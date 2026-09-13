#!/usr/bin/env python3
r"""Ask a vision model to judge capture frames the way the human labeller did, and grade it.

The in-loop judge on the capture host is deliberately cheap: numpy tile maths and a
SegFormer pass, about a second a frame. It is a good veto -- against the 47 hand labels
of era11-refine-r1 every BAD class sits at the bottom -- and a poor critic, because
liveTileShare * gradMean is one-dimensional and its maximum is whatever fills the most
tiles. Fixing that needs labels, and the only labelled set is 47 frames that pre-date
half the moves the fan now makes.

So: put a real vision model in the labelling seat. NOT in the capture loop -- it is a
cloud call taking seconds, and this project has twice been burned by trusting a model
that had never been measured on this world (SegFormer's ADE20K structure mask, the LAION
aesthetic head). It labels offline, and it earns the seat first:

    python oracle_label.py label  --thumbs DIR --out oracle-RUN.json
    python oracle_label.py report --oracle oracle-RUN.json --labels eye-labels.json

report prints the confusion matrix against the human labels and every disagreement by
name. The pass bar is written down in PASS_BAR and checked, so a qualification run either
qualifies the model or says plainly that it did not.

Frames go through the HEARTH door as image files (<= 256 KiB each, absolute paths).
HEARTH_KEY must be in the environment; nothing is read from a sibling checkout.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DOOR_LIMIT = 256 * 1024

# The pass bar for a qualification run, decided before the numbers came back.
PASS_BAR = {
    "goodBadAgreement": 0.90,   # of frames the human called GOOD or BAD, share the model agrees on
    "badCalledGood": 0,         # a frame the human called BAD must never come back GOOD
}

# The rollup every specific class belongs to. Keys are the human rubric's own class names.
TIERS = {
    "GOOD": "GOOD",
    "ok": "ok", "ok-texel": "ok", "ok-cropped": "ok", "dull": "ok", "dark": "ok",
    "BAD-roof": "BAD", "BAD-mist": "BAD", "BAD-skyladder": "BAD",
    "BAD-ladder": "BAD", "BAD-aim-water": "BAD", "BAD-dark-texel": "BAD",
}

# Two rubrics, both kept, because the first one FAILED and the failure is the finding.
#
# v1 asked for a verdict with no evidence step and primed positivity ("celebrates what
# players built"). gemini-3.5-flash answered GOOD to 43 of 47 frames, including all 24 the
# human called BAD -- seven fog-outs and four camera-inside-a-roof frames came back as
# "well-composed and beautifully lit". 27% GOOD/BAD agreement. The images arrive and are
# seen (every description is frame-specific); the judgement is what failed.
#
# v2 removes the priming, states that an automated shoot is mostly failures, and makes the
# model commit to observable evidence -- what is in the frame, then a fixed set of yes/no
# flags -- BEFORE it is allowed to name a class.
#
# METHOD NOTE: the 47 human labels have now been spent twice as a qualification set. Any
# further prompt revision fits the prompt to them, so whatever is fitted downstream must be
# validated against a fresh human slice, not against these 47.

SYSTEM_V1 = (
    "You are judging automated architectural photographs of player-built structures in the "
    "game Valheim. Each frame is a \"detail\" shot: the camera was solved to put a target "
    "pixels-per-metre on part of a building, so a partial view of a large build is intended, "
    "not a fault. The frames go into a public gallery that celebrates what players built. You "
    "are judging photographs of architecture, not screenshots of gameplay. Answer only with "
    "the requested JSON."
)

SYSTEM_V2 = (
    "You are a picture editor culling an automated architectural shoot in the game Valheim. "
    "An unattended camera placed these frames from solved coordinates, and most automated "
    "frames are failures: the lens ends up inside a roof or wall, inside a fog volume, aimed "
    "at empty sky, aimed at open water, or pressed so close that the texture resolution "
    "shows. Your job is to find those. Generosity is a failure of the job -- a frame you pass "
    "that should have been cut costs more than one you cut wrongly. A partial view of a large "
    "building is intended and is not a fault by itself. Answer only with the requested JSON."
)

# The class definitions are the human rubric's own, verbatim from eye-labels.json's classes
# block, so the two label spaces are identical and a disagreement is a disagreement rather
# than a translation error.
CLASSES = """GOOD: a gallery-worthy detail frame of the build
ok: usable, not the best pose of its build
ok-texel: usable but texels visible (camera too close, texture resolution showing)
ok-cropped: usable; the subject's top is cut off
dull: shaded flat wall; nothing to look at
dark: underexposed close-up
BAD-roof: camera inside a roof or wall; flat planes
BAD-mist: fog volume; the frame is fogged out
BAD-skyladder: linear build (ladder to a sky bucket); aim is empty sky
BAD-ladder: linear build (rope-ladder diagonal) in haze; aim is empty air
BAD-aim-water: aim is open water; the build is at the frame edge or absent
BAD-dark-texel: shaded close-up with texels visible"""

ROLLUP = ('Tier rollup: "GOOD" only for the GOOD class, "ok" for '
          'ok/ok-texel/ok-cropped/dull/dark, "BAD" for any BAD-* class.')

PROMPT_V1 = ("Classify this frame into exactly one class from this list. These are the "
             "classes and their definitions, verbatim from the human labeller's rubric:\n\n"
             + CLASSES + "\n\n" + ROLLUP + "\n\n"
             "Respond with exactly this JSON and nothing else:\n"
             '{"tier": "<GOOD|ok|BAD>", "class": "<one class name from the list>", '
             '"reason": "<one short sentence>"}')

PROMPT_V2 = """Look at this frame and answer in three steps. Do not name a class until step 3.

STEP 1 -- say what is actually in the frame, in one plain sentence. Name the subject and where the camera is relative to it.

STEP 2 -- answer these strictly from what you can see. Each is true or false:
  inside:      the camera is inside a structure -- a roof cavity, between walls, under a floor. Signs: large flat planes filling the frame, beams seen from underneath, no ground and no horizon, light with no visible source.
  fogged:      a fog or mist volume is washing the frame out; distant geometry dissolves into flat grey or white.
  aimSky:      the centre of the frame is empty sky, and the built structure is a thin line or absent.
  aimWater:    the centre of the frame is open water or ice, and the built structure is at the edge or absent.
  edgeSubject: the building is not what the frame is centred on -- it sits at an edge or corner.
  texels:      the camera is close enough that individual texture pixels are visible on surfaces.
  underlit:    the subject is in shadow or underexposed; detail is lost to darkness.

STEP 3 -- classify into exactly one of these, consistent with the flags you just gave:

""" + CLASSES + """

GOOD is the top tier and should be rare: reserve it for a frame you would put on the front page of the gallery. If any flag in step 2 is true, the class is the matching BAD-* or ok-* class, never GOOD.

""" + ROLLUP + """

Respond with exactly this JSON and nothing else:
{"saw": "<step 1, one sentence>", "flags": {"inside": <bool>, "fogged": <bool>, "aimSky": <bool>, "aimWater": <bool>, "edgeSubject": <bool>, "texels": <bool>, "underlit": <bool>}, "tier": "<GOOD|ok|BAD>", "class": "<one class name>", "reason": "<one short sentence>"}"""

RUBRICS = {"v1": (SYSTEM_V1, PROMPT_V1), "v2": (SYSTEM_V2, PROMPT_V2)}


class Door:
    """Minimal streamable-HTTP MCP client for one tool: local_generate, with image files."""

    _id = 0

    def __init__(self, url: str, key: str):
        self.url, self.key, self.session = url, key, None
        self._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "oracle-label", "version": "1"}})
        self._notify("notifications/initialized")

    def _headers(self):
        h = {"Content-Type": "application/json",
             "Accept": "application/json, text/event-stream",
             "X-Hearth-Key": self.key}
        if self.session:
            h["Mcp-Session-Id"] = self.session
        return h

    def _post(self, payload: dict):
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode("utf-8"),
                                     headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=600) as resp:
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self.session = sid
            body = resp.read().decode("utf-8")
            ctype = resp.headers.get("Content-Type", "")
        if "text/event-stream" in ctype:
            msgs = [json.loads(line[5:].strip()) for line in body.splitlines()
                    if line.startswith("data:")]
            return msgs[-1] if msgs else None
        return json.loads(body) if body.strip() else None

    def _rpc(self, method: str, params: dict):
        Door._id += 1
        return self._post({"jsonrpc": "2.0", "id": Door._id, "method": method, "params": params})

    def _notify(self, method: str):
        self._post({"jsonrpc": "2.0", "method": method})

    def generate(self, prompt, backend, files=None, system=None, task_id=None, model=None):
        args = {"prompt": prompt, "backend": backend}
        for key, value in (("files", files), ("system", system),
                           ("task_id", task_id), ("model", model)):
            if value:
                args[key] = value
        res = self._rpc("tools/call", {"name": "local_generate", "arguments": args})
        content = (res or {}).get("result", {}).get("content", [])
        text = "".join(c.get("text", "") for c in content if c.get("type") == "text")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"ok": False, "text": text, "error": "non-json tool result"}


def parse_verdict(text):
    """The model is asked for bare JSON and usually fences it anyway."""
    if not text:
        return None
    body = re.sub(r"^```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.S)
    start, end = body.find("{"), body.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        got = json.loads(body[start:end + 1])
    except json.JSONDecodeError:
        return None
    cls = str(got.get("class", "")).strip()
    tier = str(got.get("tier", "")).strip()
    # The rollup is derivable, so trust the class and repair a tier that disagrees with it.
    if cls in TIERS:
        tier = TIERS[cls]
    out = {"tier": tier, "class": cls, "reason": str(got.get("reason", "")).strip()}
    for key in ("saw", "flags"):          # v2's evidence step, kept as features for later
        if key in got:
            out[key] = got[key]
    return out


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def label(args):
    key = os.environ.get("HEARTH_KEY")
    if not key:
        raise SystemExit("HEARTH_KEY is not set")
    url = os.environ.get("HEARTH_URL", "http://127.0.0.1:8710/mcp")

    thumbs = sorted(p for p in Path(args.thumbs).iterdir() if p.suffix.lower() == ".webp")
    if not thumbs:
        raise SystemExit("no .webp thumbnails under " + str(args.thumbs))
    oversize = [p.name for p in thumbs if p.stat().st_size > DOOR_LIMIT]
    if oversize:
        raise SystemExit(f"{len(oversize)} thumb(s) over the door's 256 KiB limit: {oversize[:3]}")

    system, prompt = RUBRICS[args.rubric]
    doc = {"schema": "steward-oracle-labels/v1", "backend": args.backend,
           "rubric": args.rubric, "prompt": prompt, "system": system, "frames": {}}
    if Path(args.out).exists() and not args.force:
        doc = read(args.out)
        doc.setdefault("frames", {})
    todo = [p for p in thumbs
            if p.stem not in doc["frames"] or not doc["frames"][p.stem].get("ok")]
    print(f"  {len(thumbs)} thumb(s), {len(todo)} to label on {args.backend}, "
          f"{args.jobs} in flight")
    if not todo:
        return 0

    doors = [Door(url, key) for _ in range(args.jobs)]
    started = time.time()
    done = [0]

    def one(indexed):
        index, path = indexed
        door = doors[index % len(doors)]
        try:
            result = door.generate(prompt, args.backend, files=[str(path.resolve())],
                                   system=system, task_id=args.task_id, model=args.model)
        except Exception as exc:                  # a door hiccup is one frame, not the run
            result = {"ok": False, "error": str(exc)[:200]}
        verdict = parse_verdict(result.get("text", "")) if result.get("ok") else None
        row = {"ok": bool(result.get("ok")) and verdict is not None,
               "model": result.get("model"), "duration_ms": result.get("duration_ms"),
               "tokensIn": result.get("tokens_in"), "tokensOut": result.get("tokens_out")}
        if verdict:
            row.update(verdict)
        else:
            row["error"] = result.get("error") or "unparseable verdict"
            row["raw"] = (result.get("text") or "")[:400]
        done[0] += 1
        rate = done[0] / max(time.time() - started, 1e-9)
        note = row.get("class") or row.get("error")
        print(f"    {done[0]}/{len(todo)}  {path.stem:<28} {note:<16} "
              f"~{(len(todo) - done[0]) / max(rate, 1e-9) / 60:.1f} min left", flush=True)
        return path.stem, row

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for stem, row in pool.map(one, list(enumerate(todo))):
            doc["frames"][stem] = row

    doc["model"] = next((r.get("model") for r in doc["frames"].values() if r.get("model")), None)
    doc["generatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    doc["counts"] = {"frames": len(doc["frames"]),
                     "failed": sum(1 for r in doc["frames"].values() if not r.get("ok"))}
    write(args.out, doc)
    print(f"  wrote {args.out}: {doc['counts']['frames']} frame(s), "
          f"{doc['counts']['failed']} failed, {time.time() - started:.0f}s")
    return 1 if doc["counts"]["failed"] else 0


def report(args):
    doc = read(args.oracle)
    oracle = doc["frames"]
    human = read(args.labels)["labels"]
    pairs = [(stem, lab, oracle[stem]) for stem, lab in sorted(human.items())
             if stem in oracle and oracle[stem].get("ok") and lab in TIERS]
    skipped = [s for s in human if s not in oracle or not oracle.get(s, {}).get("ok")]
    unlabelled = [s for s, lab in human.items() if lab not in TIERS]
    if not pairs:
        raise SystemExit("no frame is both human-labelled and oracle-labelled")

    tiers = ["GOOD", "ok", "BAD"]
    matrix = {h: {o: 0 for o in tiers} for h in tiers}
    for _, lab, row in pairs:
        got = row.get("tier") if row.get("tier") in tiers else "ok"
        matrix[TIERS[lab]][got] += 1

    extra = ""
    if skipped or unlabelled:
        extra = (f"  ({len(skipped)} not oracle-labelled, "
                 f"{len(unlabelled)} human class outside the rubric)")
    print(f"oracle {doc.get('model')} rubric {doc.get('rubric', 'v1')} vs "
          f"{len(pairs)} human-labelled frames{extra}")
    print("\n  " + "human \\ oracle".ljust(16) + "".join(f"{t:>7}" for t in tiers) + f"{'n':>7}")
    for h in tiers:
        n = sum(matrix[h].values())
        print(f"  {h:<16}" + "".join(f"{matrix[h][o]:>7}" for o in tiers) + f"{n:>7}")

    decisive = [(s, lab, r) for s, lab, r in pairs if TIERS[lab] in ("GOOD", "BAD")]
    agreed = [t for t in decisive if t[2].get("tier") == TIERS[t[1]]]
    bad_called_good = [t for t in decisive
                       if TIERS[t[1]] == "BAD" and t[2].get("tier") == "GOOD"]
    good_called_bad = [t for t in decisive
                       if TIERS[t[1]] == "GOOD" and t[2].get("tier") == "BAD"]
    rate = len(agreed) / float(len(decisive)) if decisive else 0.0

    print(f"\n  GOOD/BAD agreement   {len(agreed)}/{len(decisive)} = {rate:.1%}"
          f"   (bar {PASS_BAR['goodBadAgreement']:.0%})")
    print(f"  BAD called GOOD      {len(bad_called_good)}   (bar {PASS_BAR['badCalledGood']})")
    print(f"  GOOD called BAD      {len(good_called_bad)}")

    disagreements = [(s, lab, r) for s, lab, r in pairs if r.get("tier") != TIERS[lab]]
    if disagreements:
        print(f"\n  every disagreement ({len(disagreements)} of {len(pairs)}):")
        for stem, lab, row in disagreements:
            print(f"    {stem:<28} human {lab:<15} oracle {row.get('class', '?'):<15} "
                  f"{row.get('reason', '')[:70]}")

    exact = sum(1 for _, lab, r in pairs if r.get("class") == lab)
    print(f"\n  exact class match    {exact}/{len(pairs)} = {exact / len(pairs):.1%}  "
          f"(not a bar; the tier rollup is what the loop needs)")

    passed = (rate >= PASS_BAR["goodBadAgreement"]
              and len(bad_called_good) <= PASS_BAR["badCalledGood"])
    print(f"\n  QUALIFIED: {'yes' if passed else 'NO'}")
    if args.out:
        write(args.out, {
            "schema": "steward-oracle-qualification/v1",
            "oracle": str(args.oracle), "labels": str(args.labels),
            "model": doc.get("model"), "rubric": doc.get("rubric", "v1"),
            "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "passBar": PASS_BAR, "n": len(pairs), "matrix": matrix,
            "goodBadAgreement": round(rate, 4),
            "badCalledGood": [s for s, _, _ in bad_called_good],
            "goodCalledBad": [s for s, _, _ in good_called_bad],
            "exactClassMatch": round(exact / len(pairs), 4),
            "disagreements": [{"frame": s, "human": lab, "oracle": r.get("class"),
                               "reason": r.get("reason")} for s, lab, r in disagreements],
            "qualified": passed,
        })
        print(f"  wrote {args.out}")
    return 0 if passed else 1


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    lab = sub.add_parser("label", help="send every thumbnail through the door and record the verdict")
    lab.add_argument("--thumbs", required=True, help="directory of .webp thumbnails, <= 256 KiB each")
    lab.add_argument("--out", required=True)
    lab.add_argument("--backend", default="gcp-gemini")
    lab.add_argument("--rubric", default="v2", choices=sorted(RUBRICS),
                     help="v1 failed qualification (27%% agreement, every BAD called GOOD); "
                          "v2 is evidence-first and is the default")
    lab.add_argument("--model", default=None, help="pin a model within the backend")
    lab.add_argument("--task-id", default=None, help="HEARTH ledger attribution")
    lab.add_argument("--jobs", type=int, default=4)
    lab.add_argument("--force", action="store_true", help="re-label frames already recorded")
    lab.set_defaults(func=label)

    rep = sub.add_parser("report", help="grade the oracle against the human labels")
    rep.add_argument("--oracle", required=True)
    rep.add_argument("--labels", required=True, help="eye-labels.json")
    rep.add_argument("--out", default=None, help="write the qualification receipt here")
    rep.set_defaults(func=report)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""VLM tiebreak pass: qwen2.5vl judges the top frames of each interior cell.

Selection: interior variants only (hall_/toproom_/seat_/gate_/court_*). Within
each (variant) cell, frames pass the depth veto (center_block <= 0.45), rank by
aesthetic, and the top K go to the judge. Writes judge.json {id: {score, reason}}.

Plain python3 (urllib + PIL; sends the 1600px webp re-encoded as JPEG at 1280).

Known limit, measured on the first full run: qwen2.5vl at temperature 0 scored
all 80 pre-filtered frames exactly 8.0 -- absolute scales compress on small
VLMs. The useful next step is pairwise ranking (show two frames, ask which is
the better gallery shot), not a bigger rubric. Until then the judge column is
a reason-generator and the aesthetic score is the effective tiebreak.
"""
import base64
import io
import json
import os
import sys
import time
import urllib.request

HERE = r"C:\work\baseline\tools\selfie-stick"
LARGE = os.path.join(HERE, "out", "gallery", "large")
OLLAMA = "http://127.0.0.1:11434"
VLM = "qwen2.5vl:7b"
TOP_K = 4
CROP_FRAC = (0.0, 40 / 900, 1550 / 1600, 1.0)
INTERIOR_PREFIXES = ("hall_", "toproom_", "seat_", "gate_", "court_")

JUDGE_PROMPT = """You are judging a screenshot from the game Valheim for a public gallery of
player-built structures. The gallery wants frames that feel like you are IN the scene:
epic, atmospheric, readable. Penalize frames that are too dark to read, that are a
close-up of a wall or object filling the frame, or that have no clear subject.
Reward depth, dramatic light (sunrise, sunset, stars, storms, firelight), and a
clear sense of place.

Reply with ONLY a JSON object: {"score": <1-10>, "reason": "<one short sentence>"}"""


def judge(path):
    from PIL import Image
    img = Image.open(path).convert("RGB")
    w, h = img.size
    l, t, r, b = CROP_FRAC
    img = img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    if img.size[0] > 1280:
        img = img.resize((1280, int(img.size[1] * 1280 / img.size[0])))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    payload = {"model": VLM, "prompt": JUDGE_PROMPT,
               "images": [base64.b64encode(buf.getvalue()).decode()],
               "stream": False, "options": {"temperature": 0}}
    req = urllib.request.Request(f"{OLLAMA}/api/generate",
                                 json.dumps(payload).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        text = json.loads(resp.read())["response"]
    frag = text[text.find("{"): text.rfind("}") + 1]
    d = json.loads(frag)
    return float(d["score"]), str(d.get("reason", ""))[:140]


def main():
    with open(os.path.join(HERE, "out", "gallery", "index.json"), encoding="utf-8") as fh:
        idx = json.load(fh)
    aesthetic = {}
    ap = os.path.join(HERE, "out", "aesthetic.json")
    if os.path.exists(ap):
        with open(ap, encoding="utf-8") as fh:
            aesthetic = {k: v.get("aesthetic") for k, v in json.load(fh).items()}
    depth = {}
    dp = os.path.join(HERE, "out", "depth.json")
    if os.path.exists(dp):
        with open(dp, encoding="utf-8") as fh:
            depth = json.load(fh)

    out_path = os.path.join(HERE, "out", "judge.json")
    done = {}
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as fh:
            done = json.load(fh)

    cells = {}
    for r in idx["images"]:
        v = r.get("variant") or ""
        if not v.startswith(INTERIOR_PREFIXES):
            continue
        d = depth.get(r["id"], {})
        if d.get("center_block", 0) > 0.45:
            continue                      # geometric veto: camera against a wall
        a = aesthetic.get(r["id"])
        if a is None:
            continue
        cells.setdefault(v, []).append((a, r["id"]))

    todo = []
    for v, rows in sorted(cells.items()):
        rows.sort(reverse=True)
        todo += [i for _a, i in rows[:TOP_K] if i not in done]
    print(f"{len(cells)} cells, {len(todo)} frames to judge (top {TOP_K} each, "
          f"{len(done)} already done)")

    t0 = time.time()
    for n, image_id in enumerate(todo, 1):
        path = os.path.join(LARGE, image_id + ".webp")
        if not os.path.exists(path):
            continue
        try:
            score, reason = judge(path)
        except Exception as exc:
            print(f"  ! {image_id}: {exc}")
            continue
        done[image_id] = {"score": score, "reason": reason}
        rate = n / max(time.time() - t0, 0.001)
        print(f"  [{n}/{len(todo)}] {image_id}: {score}  {reason[:60]}"
              f"   (~{(len(todo)-n)/max(rate,0.001)/60:.0f} min left)")

    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(done, fh, indent=1)
    os.replace(tmp, out_path)
    print(f"wrote {out_path} ({len(done)} judged)")


if __name__ == "__main__":
    main()

r"""Extract closed-vocabulary attributes for each concept from its generation prompt.

    python tools/portrait-corpus/extract_attributes.py prepare --concepts docs/.../concepts.json --out <dir>
        writes <dir>/batch-N.prompt.txt (the instruction + N prompts) for an operator or agent to
        send through the HEARTH door, and <dir>/batches.json listing the concept ids per batch.
    python tools/portrait-corpus/extract_attributes.py call --concepts ... --out <dir> [--backend gcp-gemini]
        does the same and then sends each batch itself over the door's HTTP MCP transport, when
        HEARTH_URL and HEARTH_KEY are in the environment (never read from a sibling checkout).
        Each result lands as <dir>/batch-N.result.json with the door's ok/backend/model metadata.
    python tools/portrait-corpus/extract_attributes.py ingest --concepts ... --out <dir> --write attributes.json
        validates every returned value against vocab.json, writes attributes.json for
        build_catalog.py --attributes, and lists what is off-vocabulary under "review".

The prompt is the ground truth for what the painter was asked for; the picker filters on what
was asked for because that is stable across all takes of a concept. What was actually painted
is the human pass's business (picks.json). A value the model cannot support from the prompt
text is to be "unspecified", which the ingest step maps to the axis default.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
VOCAB = json.loads((HERE / "vocab.json").read_text(encoding="utf-8"))

AXES = {
    "age": ("adult", VOCAB["age"]),
    "hair": ("brown", VOCAB["hair"]),
    "hair_style": ("loose", VOCAB["hair_style"]),
    "beard": ("none", VOCAB["beard"]),
    "mood": ("calm", VOCAB["mood"]),
    "setting": (None, VOCAB["setting"]),
    "palette": ("daylight", VOCAB["palette"]),
    "kit": ("civilian", VOCAB["kit"]),
    "companion": ("none", VOCAB["companion"]),
    "headwear": ("none", VOCAB["headwear"]),
}
BOOLS = ("magic", "face_paint")

INSTRUCTION = """You classify painted Viking character portraits from the text prompt that produced each one.
For every prompt below return one JSON object. Answer ONLY from what the prompt says; if an axis is not stated, use "unspecified".
Closed vocabularies -- use these exact lowercase tokens and nothing else:
  age:        {age}
  hair:       {hair}   (hair = colour; when only a beard colour is stated, use the beard colour; "hidden" only when a hood/helmet covers all hair and no colour is stated; grey covers white and silver; auburn/copper/ginger = red; light-brown/chestnut = brown; black/raven = dark; flaxen/golden/honey = blonde)
  hair_style: {hair_style}
  beard:      {beard}   (women: "none" unless stated)
  mood:       {mood}   (warm = smiling/kind/friendly; calm = serene/thoughtful/wise; proud = confident/determined; stern = grim/serious/intense; fierce = rage/snarl/menace)
  setting:    {setting}   (the dominant background place; "sacred" = runestones, shrine, ritual site; "market" = trading post)
  palette:    {palette}   (ember = fire/forge/hearth/torch/lantern glow; golden = sunset/dawn/warm sun; daylight = plain day; cool = overcast/snow/blue; storm = lightning/rain/dark sky; aurora = northern lights; night = moon/stars)
  kit:        {kit}   (armoured = mail/plate/lamellar/helmet/shield; robed = robes/cloak-dominant ritual dress; otherwise civilian)
  companion:  {companion}   (a live animal in frame; "other" for anything not listed)
  headwear:   {headwear}
  magic:      true/false  (glowing runes, spectral light, visible sorcery)
  face_paint: true/false  (war paint, kohl, painted runes on the face)
  props:      list of 1-4 short lowercase noun phrases for objects held or worn that identify the trade (e.g. "adze", "try-square", "drinking horn")
Return a JSON array, one object per prompt, in the same order, each with keys:
  concept_id, age, hair, hair_style, beard, mood, setting, palette, kit, companion, headwear, magic, face_paint, props
No prose, no code fences.
"""


def batches_of(concepts: list[dict], size: int) -> list[list[dict]]:
    return [concepts[i:i + size] for i in range(0, len(concepts), size)]


def build_prompt(batch: list[dict]) -> str:
    head = INSTRUCTION.format(**{k: " | ".join(v[1]) for k, v in AXES.items()})
    body = "\n\n".join(f"[{i + 1}] concept_id: {c['concept_id']}\n{c['prompt']}" for i, c in enumerate(batch))
    return head + "\nPROMPTS:\n\n" + body


def prepare(concepts: list[dict], out: Path, size: int) -> list[list[str]]:
    out.mkdir(parents=True, exist_ok=True)
    ids = []
    for n, batch in enumerate(batches_of(concepts, size), 1):
        (out / f"batch-{n}.prompt.txt").write_text(build_prompt(batch), encoding="utf-8")
        ids.append([c["concept_id"] for c in batch])
    (out / "batches.json").write_text(json.dumps({"batches": ids}, indent=1), encoding="utf-8")
    print(f"prepared {len(ids)} batches under {out}")
    return ids


class Door:
    """Minimal streamable-HTTP MCP client for one tool: local_generate."""

    def __init__(self, url: str, key: str):
        self.url, self.key, self.session = url, key, None
        self._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "portrait-corpus", "version": "1"}})
        self._notify("notifications/initialized")

    def _headers(self):
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "X-Hearth-Key": self.key}
        if self.session:
            h["Mcp-Session-Id"] = self.session
        return h

    def _post(self, payload: dict):
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode("utf-8"), headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=1500) as resp:
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self.session = sid
            body = resp.read().decode("utf-8")
            ctype = resp.headers.get("Content-Type", "")
        if "text/event-stream" in ctype:
            msgs = [json.loads(line[5:].strip()) for line in body.splitlines() if line.startswith("data:")]
            return msgs[-1] if msgs else None
        return json.loads(body) if body.strip() else None

    def _rpc(self, method: str, params: dict):
        Door._id = getattr(Door, "_id", 0) + 1
        return self._post({"jsonrpc": "2.0", "id": Door._id, "method": method, "params": params})

    def _notify(self, method: str):
        self._post({"jsonrpc": "2.0", "method": method})

    def generate(self, prompt: str, backend: str, task_id: str | None) -> dict:
        args = {"prompt": prompt, "backend": backend}
        if task_id:
            args["task_id"] = task_id
        res = self._rpc("tools/call", {"name": "local_generate", "arguments": args})
        content = (res or {}).get("result", {}).get("content", [])
        text = "".join(c.get("text", "") for c in content if c.get("type") == "text")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"ok": False, "text": text, "error": "non-json tool result"}


def call(concepts: list[dict], out: Path, size: int, backend: str, task_id: str | None, only: list[int] | None = None) -> int:
    url, key = os.environ.get("HEARTH_URL", "http://127.0.0.1:8710/mcp"), os.environ.get("HEARTH_KEY")
    if not key:
        raise SystemExit("HEARTH_KEY is not set; use `prepare` and send the batches by hand")
    if not only:
        prepare(concepts, out, size)
    door = Door(url, key)
    bad = 0
    for n in (only or range(1, len(batches_of(concepts, size)) + 1)):
        prompt = (out / f"batch-{n}.prompt.txt").read_text(encoding="utf-8")
        result = door.generate(prompt, backend, task_id)
        keep = {k: result.get(k) for k in ("ok", "text", "backend", "model", "routed_by", "tokens_in", "tokens_out", "duration_ms", "error", "error_code")}
        keep["execution"] = (result.get("execution") or {}).get("job_id")
        (out / f"batch-{n}.result.json").write_text(json.dumps(keep, indent=1, ensure_ascii=False), encoding="utf-8")
        ok = bool(keep.get("ok"))
        bad += 0 if ok else 1
        print(f"batch {n}: ok={ok} backend={keep.get('backend')} model={keep.get('model')} out={keep.get('tokens_out')}")
    return 1 if bad else 0


def parse_array(text: str) -> tuple[list[dict], bool]:
    """Parse the JSON array; when the door truncated the reply mid-array, salvage every complete
    object before the cut and say so. Returns (items, truncated)."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    start = text.find("[")
    try:
        return json.loads(text[start:text.rfind("]") + 1]), False
    except json.JSONDecodeError:
        pass
    items, depth, obj_start = [], 0, None
    for i, ch in enumerate(text[start + 1:], start + 1):
        if ch == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and obj_start is not None:
                try:
                    items.append(json.loads(text[obj_start:i + 1]))
                except json.JSONDecodeError:
                    break
                obj_start = None
    return items, True


def ingest(concepts: list[dict], out: Path, write: Path) -> int:
    ids = json.loads((out / "batches.json").read_text(encoding="utf-8"))["batches"]
    by_id = {c["concept_id"]: c for c in concepts}
    rows, review, meta = {}, [], []
    for n, expected in enumerate(ids, 1):
        r = json.loads((out / f"batch-{n}.result.json").read_text(encoding="utf-8"))
        meta.append({"batch": n, "ok": r.get("ok"), "backend": r.get("backend"), "model": r.get("model"),
                     "routed_by": r.get("routed_by"), "job_id": r.get("execution")})
        if not r.get("ok"):
            review.append({"batch": n, "problem": "door returned ok:false", "error": r.get("error")})
            continue
        try:
            items, truncated = parse_array(r["text"])
        except Exception as e:
            review.append({"batch": n, "problem": f"unparseable: {e}"})
            continue
        got = [it.get("concept_id") for it in items]
        if truncated:
            review.append({"batch": n, "problem": f"reply truncated by the door after {len(items)} of {len(expected)} objects; re-run this batch"})
        elif got != expected:
            review.append({"batch": n, "problem": "order/ids differ", "expected": expected, "got": got})
        for it in items:
            cid = it.get("concept_id")
            if cid not in by_id:
                review.append({"batch": n, "problem": f"unknown concept_id {cid!r}"})
                continue
            row = {"concept_id": cid}
            for axis, (default, vocab) in AXES.items():
                v = str(it.get(axis, "unspecified")).strip().lower()
                if v in vocab:
                    row[axis] = v
                elif v in ("unspecified", "", "none") and default is not None and axis not in ("companion", "headwear", "beard"):
                    row[axis] = default
                    row.setdefault("defaulted", []).append(axis)
                elif v in ("unspecified", "") and axis in ("companion", "headwear", "beard"):
                    row[axis] = "none"
                    row.setdefault("defaulted", []).append(axis)
                else:
                    row[axis] = default
                    review.append({"concept_id": cid, "axis": axis, "value": it.get(axis), "problem": "off-vocabulary"})
            for b in BOOLS:
                v = it.get(b)
                row[b] = v if isinstance(v, bool) else str(v).lower() == "true"
            props = it.get("props") or []
            row["props"] = [str(p).strip().lower() for p in props][:4] if isinstance(props, list) else []
            rows[cid] = row
    missing = [cid for cid in by_id if cid not in rows]
    for cid in missing:
        review.append({"concept_id": cid, "problem": "no row returned"})
    doc = {"schema": "portrait-corpus-attributes/1", "source": "generation prompt per concept, classified through the HEARTH door",
           "batches": meta, "n": len(rows), "review": review, "concepts": [rows[c["concept_id"]] for c in concepts if c["concept_id"] in rows]}
    write.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"attributes {len(rows)}/{len(by_id)} | review items {len(review)} -> {write}")
    return 0 if not review else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["prepare", "call", "ingest"])
    ap.add_argument("--concepts", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="working directory for batch prompts/results")
    ap.add_argument("--batch-size", type=int, default=24)
    ap.add_argument("--backend", default="gcp-gemini")
    ap.add_argument("--task-id", default=os.environ.get("HEARTH_TASK_ID"))
    ap.add_argument("--write", type=Path, default=None, help="ingest: attributes.json path")
    ap.add_argument("--only", type=int, nargs="*", default=None, help="call: re-run only these batch numbers")
    a = ap.parse_args()
    concepts = json.loads(a.concepts.read_text(encoding="utf-8"))["concepts"]
    if a.mode == "prepare":
        prepare(concepts, a.out, a.batch_size)
        return 0
    if a.mode == "call":
        return call(concepts, a.out, a.batch_size, a.backend, a.task_id, a.only)
    return ingest(concepts, a.out, a.write or (a.out / "attributes.json"))


if __name__ == "__main__":
    sys.exit(main())

r"""Build the portrait catalog from a corpus's receipts.ndjson.

    python tools/portrait-corpus/build_catalog.py --corpus E:\omen\DMos\artifacts\corpus-viking-profiles-20260910
        [--out-catalog <corpus>\catalog.json] [--out-concepts docs/design/valheim-portrait-picker-2026-09/concepts.json]
        [--attributes <attributes.json>] [--face-qa <face_qa.json>] [--picks <picks.json>]

One row per asset (everything a picker or a publish step needs to decide whether and how
to serve it) and one row per concept (the 96 named characters, each with one prompt).
The corpus itself never moves: the catalog lives beside it, the concept file is small
enough for the repo. Receipts are read, never rewritten. (Names with `ð` render as `?` on a
cp1252 console; the receipts hold the right code point -- check bytes before "repairing".)

Auto-QA per asset:
  corrupt      the PNG does not decode (the 2026-09-10 job collision wrote one broken blob to two paths)
  size         not 1024 square
  bg_dropped   the frame has far more near-white than the concept's other takes (whole-frame
               near-white fraction exceeds the concept median by > 0.08) -- the model
               occasionally paints a blank white studio, or leaves an unfinished white patch,
               instead of the prompted background. Two of the fifteen shared seeds (s5, s11)
               account for every case in this corpus. Per-concept, not an absolute bar, so snow
               and ice concepts with legitimately pale frames are not flagged. The four-corner
               luminance z-score is kept as a secondary field (border_z).
Advisory signals per asset (never a reject; they order takes): face confidence 0-3 and the
face_none / face_small / face_off_centre flags from face_qa.py, when its output is supplied.
Every detector tried was unreliable on this art (see face_qa.py), so the human contact-sheet
pass in picks.json is the gate, as it is for the slate48 library.

The border statistic is the four-64px-corner luminance/saturation used by the slate48
library's postprocess step (ComfyStewardView tools/chronicles/portraits/postprocess.py),
re-implemented here so this script reads nothing from a sibling checkout.

Variance per concept is the mean absolute deviation of 48px greyscale thumbnails from the
concept mean, and the largest pairwise deviation. It is the number behind the finding that
seeds are takes, not a dimension.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
VOCAB = json.loads((HERE / "vocab.json").read_text(encoding="utf-8"))

def parse_slug(concept_id: str) -> dict:
    # viking_<archetype>_<f|m>_<variant>
    parts = concept_id.split("_")
    if len(parts) != 4 or parts[0] != "viking" or parts[2] not in ("f", "m"):
        raise ValueError(f"unexpected concept id {concept_id!r}")
    return {"archetype": parts[1], "gender_code": parts[2], "variant": parts[3]}


def theme_for(batch: str) -> str:
    for tag, row in VOCAB["theme"].items():
        if row["receipt_batch"] == batch:
            return tag
    raise ValueError(f"batch {batch!r} is not in vocab.json themes")


def corner_stats(img: Image.Image, size: int = 64) -> tuple[float, float]:
    """Mean luminance (0-255) and mean HSV saturation (0-1) of the four corner patches."""
    w, h = img.size
    boxes = [(0, 0, size, size), (w - size, 0, w, size), (0, h - size, size, h), (w - size, h - size, w, h)]
    lum, sat = [], []
    for b in boxes:
        patch = img.crop(b)
        lum.append(float(np.asarray(patch.convert("L"), dtype=np.float32).mean()))
        hsv = np.asarray(patch.convert("HSV"), dtype=np.float32)
        sat.append(float(hsv[..., 1].mean()) / 255.0)
    return sum(lum) / 4, sum(sat) / 4


def load_receipts(corpus: Path) -> list[dict]:
    rows = []
    with (corpus / "receipts.ndjson").open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"receipts.ndjson line {n}: {e}")
    return rows


def analyse_asset(r: dict, corpus: Path) -> tuple[dict, np.ndarray | None]:
    path = corpus / "assets" / f"{r['asset_id']}.png"
    row = {
        "asset_id": r["asset_id"],
        "concept_id": r["concept_id"],
        "seed_idx": r["seed_idx"],
        "seed": r["seed"],
        "sha256": r["sha256"],
        "job_id": r["job_id"],
        "lane": r["lane"],
        "duration_s": round(float(r["duration_seconds"]), 3),
        "created_at": r["created_at"],
        "file": path.name,
        "bytes": None,
        "sha256_verified": None,
        "decode_ok": False,
        "size_ok": False,
        "border_lum": None,
        "border_sat": None,
        "border_z": None,
        "white_frac": None,
        "white_excess": None,
        "reject": [],
        "advisory": [],
    }
    if not path.exists():
        row["reject"].append("missing")
        return row, None
    data = path.read_bytes()
    row["bytes"] = len(data)
    row["sha256_verified"] = hashlib.sha256(data).hexdigest() == r["sha256"]
    try:
        img = Image.open(path)
        img.load()
    except Exception:
        row["reject"].append("corrupt")
        return row, None
    row["decode_ok"] = True
    row["size_ok"] = img.size == (1024, 1024)
    if not row["size_ok"]:
        row["reject"].append("size")
    lum, sat = corner_stats(img.convert("RGB"))
    row["border_lum"] = round(lum, 1)
    row["border_sat"] = round(sat, 3)
    rgb96 = np.asarray(img.convert("RGB").resize((96, 96), Image.BILINEAR), dtype=np.float32)
    row["white_frac"] = round(float((rgb96.min(axis=2) > 225).mean()), 4)
    thumb = np.asarray(img.convert("L").resize((48, 48), Image.BILINEAR), dtype=np.float32) / 255.0
    return row, thumb


def rank_takes(ok_rows: list[dict], n: int) -> list[str]:
    """Gates already applied. Order: detector consensus (3 votes before 2 before 1), then face
    height inside the window that survives a 128px tile, then most centred, then least
    white excess; alternate facing so a strip of four is not four copies of one pose."""
    def key(x):
        f = x.get("face") or {}
        frac = f.get("frac") or 0.0
        in_window = 0 if 0.12 <= frac <= 0.35 else 1
        return (-(f.get("confidence") or 0), in_window, abs(f.get("cx_offset") or 0.0), abs(x["white_excess"] or 0.0))
    ranked = sorted(ok_rows, key=key)
    auto: list[str] = []
    used: collections.Counter = collections.Counter()
    for x in ranked:
        facing = (x.get("face") or {}).get("facing")
        if auto and facing and used[facing] >= max(1, n // 2):
            continue
        auto.append(x["asset_id"])
        if facing:
            used[facing] += 1
        if len(auto) >= n:
            return auto
    for x in ranked:
        if len(auto) >= n:
            break
        if x["asset_id"] not in auto:
            auto.append(x["asset_id"])
    return auto


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out-catalog", type=Path, default=None)
    ap.add_argument("--out-concepts", type=Path,
                    default=REPO / "docs/design/valheim-portrait-picker-2026-09/concepts.json")
    ap.add_argument("--attributes", type=Path, default=None, help="attributes.json from extract_attributes.py")
    ap.add_argument("--face-qa", type=Path, default=None, help="face_qa.json from face_qa.py")
    ap.add_argument("--picks", type=Path, default=None, help="picks.json: {concept_id: {pick:[...], reject:[...]}}")
    ap.add_argument("--auto-picks", type=int, default=4, help="takes auto-picked per concept")
    a = ap.parse_args()

    corpus = a.corpus.resolve()
    out_catalog = a.out_catalog or (corpus / "catalog.json")
    receipts = load_receipts(corpus)
    print(f"receipts {len(receipts)}", file=sys.stderr)

    assets: list[dict] = []
    thumbs: dict[str, list[np.ndarray]] = collections.defaultdict(list)
    for i, r in enumerate(receipts, 1):
        row, thumb = analyse_asset(r, corpus)
        assets.append(row)
        if thumb is not None:
            thumbs[r["concept_id"]].append(thumb)
        if i % 200 == 0:
            print(f"  {i}/{len(receipts)}", file=sys.stderr)

    by_concept: dict[str, list[dict]] = collections.defaultdict(list)
    for row in assets:
        by_concept[row["concept_id"]].append(row)

    # Per-concept: whole-frame white excess -> bg_dropped; corner-luminance robust z kept as a field
    for cid, rows in by_concept.items():
        ok = [x for x in rows if x["border_lum"] is not None]
        if len(ok) < 3:
            continue
        med_white = statistics.median(x["white_frac"] for x in ok)
        lums = [x["border_lum"] for x in ok]
        med = statistics.median(lums)
        mad = statistics.median(abs(v - med) for v in lums) or 1.0
        for x in ok:
            x["border_z"] = round(0.6745 * (x["border_lum"] - med) / mad, 2)
            x["white_excess"] = round(x["white_frac"] - med_white, 4)
            if x["white_excess"] > 0.08:
                x["reject"].append("bg_dropped")

    if a.face_qa:
        fq = json.loads(a.face_qa.read_text(encoding="utf-8"))
        fq_by_id = {x["asset_id"]: x for x in fq["assets"]}
        for x in assets:
            f = fq_by_id.get(x["asset_id"])
            if not f:
                continue
            x["face"] = {k: f[k] for k in ("confidence", "detectors", "box", "frac", "cx_offset", "cy_offset", "facing", "bust_crop") if k in f}
            x["advisory"] = [fl for fl in f.get("flags", []) if fl not in ("skipped",)]

    picks = json.loads(a.picks.read_text(encoding="utf-8")) if a.picks else {}
    picks = {k: v for k, v in picks.items() if isinstance(v, dict)}   # drop schema/note/reviewed_by
    for cid, p in picks.items():
        for aid in p.get("reject", []):
            for x in by_concept.get(cid, []):
                if x["asset_id"] == aid and "rejected_by_eye" not in x["reject"]:
                    x["reject"].append("rejected_by_eye")

    attrs = {}
    if a.attributes:
        attrs = {x["concept_id"]: x for x in json.loads(a.attributes.read_text(encoding="utf-8"))["concepts"]}

    first: dict[str, dict] = {}
    for r in receipts:
        first.setdefault(r["concept_id"], r)
    name_seen = collections.Counter(r["character_name"].split(" ")[0] for r in first.values())

    concepts = []
    for cid, r in first.items():
        slug = parse_slug(cid)
        rows = by_concept[cid]
        ok_rows = [x for x in rows if not x["reject"]]
        tl = thumbs.get(cid, [])
        var_mean = var_max = None
        if len(tl) >= 2:
            T = np.stack(tl)
            var_mean = round(float(np.abs(T - T.mean(0)).mean()), 4)
            var_max = round(max(float(np.abs(T[i] - T[j]).mean())
                                 for i in range(len(T)) for j in range(i + 1, len(T))), 4)
        auto = rank_takes(ok_rows, a.auto_picks)
        manual = picks.get(cid, {})
        usable_ids = {x["asset_id"] for x in ok_rows}
        picked = [p for p in (manual.get("pick") or auto) if p in usable_ids]
        name = r["character_name"]
        concept = {
            "concept_id": cid,
            "role": slug["archetype"],
            "role_label": VOCAB["role"][slug["archetype"]]["label"],
            "receipt_discipline": r["discipline"],
            "presentation": "woman" if slug["gender_code"] == "f" else "man",
            "variant": slug["variant"],
            "theme": theme_for(r["batch"]),
            "character_name": name,
            "first_name_shared": name_seen[r["character_name"].split(" ")[0]] > 1,
            "n_takes": len(rows),
            "n_usable": len(ok_rows),
            "variance_mean_dev": var_mean,
            "variance_max_pair": var_max,
            "takes": {
                "auto": auto,
                "picked": picked,
                "rejected": [{"asset_id": x["asset_id"], "why": x["reject"]} for x in rows if x["reject"]],
                "source": "manual" if manual.get("pick") else "auto",
            },
            "prompt": r["prompt"],
        }
        if cid in attrs:
            concept["attributes"] = {k: v for k, v in attrs[cid].items() if k != "concept_id"}
        concepts.append(concept)
    concepts.sort(key=lambda c: (c["theme"], c["role"], c["presentation"], c["variant"]))

    n_ok = sum(1 for x in assets if not x["reject"])
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    receipts_path = corpus / "receipts.ndjson"
    catalog = {
        "schema": "portrait-corpus-catalog/1",
        "generated_at": generated,
        "corpus": str(corpus),
        "receipts_sha256": hashlib.sha256(receipts_path.read_bytes()).hexdigest(),
        "receipts_bytes": receipts_path.stat().st_size,
        "n_assets": len(assets),
        "n_usable": n_ok,
        "n_concepts": len(concepts),
        "reject_counts": dict(collections.Counter(why for x in assets for why in x["reject"])),
        "assets": assets,
    }
    out_catalog.write_text(json.dumps(catalog, indent=1, ensure_ascii=False), encoding="utf-8")
    concepts_doc = {
        "schema": "portrait-corpus-concepts/1",
        "generated_at": generated,
        "corpus": corpus.name,
        "catalog_sha256": hashlib.sha256(out_catalog.read_bytes()).hexdigest(),
        "n_concepts": len(concepts),
        "n_assets": len(assets),
        "n_usable": n_ok,
        "concepts": concepts,
    }
    a.out_concepts.parent.mkdir(parents=True, exist_ok=True)
    a.out_concepts.write_text(json.dumps(concepts_doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"assets {len(assets)} | usable {n_ok} | concepts {len(concepts)} | rejects {catalog['reject_counts']}")
    print(f"catalog  {out_catalog}")
    print(f"concepts {a.out_concepts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

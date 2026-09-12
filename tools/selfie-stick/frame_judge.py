#!/usr/bin/env python3
"""Judge one master against another, on the capture host's CPU, while the camera is still there.

The publication pipeline measures frames days later on another machine: derivatives,
shuttle, frame_geometry on a B70, a paired table by hand. That is fine for a corpus and
useless for a loop. This module is the same two measurements -- master_detail's tile
math on the native 4K luma and frame_geometry's SegFormer mask metrics on the 1600 px
plane -- packaged so a worker can call them on AM4 about a second after the shutter
and decide whether to move the camera.

What it is good for, measured (see selfie-stick-scoring-bench and gallery-detail-scale-
not-fill): the mask metrics failed as an absolute ranker (domain gap, corr +0.077 with
px/m) but were decisive as a PAIRED judge of the same build (13.9x structure, orbit vs
detail). A refine loop only ever compares candidates of one build from one session, so
it lives entirely in the regime that works. Everything measured is journalled; the
decision rule is a first cut in one dict, meant to be re-litigated from the receipts.

CPU only, deliberately: the GPU is rendering the next frame, the sample is tiny, and
b0 on eight threads is ~0.4 s per frame. Weights come from the local HF cache
(HF_HUB_OFFLINE); nothing is downloaded on the capture host.

    ~/venvs/torch-xpu/bin/python frame_judge.py --images <root>/images --limit 3
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
for key, value in (("HF_HUB_OFFLINE", "1"), ("TRANSFORMERS_OFFLINE", "1"),
                   ("TOKENIZERS_PARALLELISM", "false")):
    os.environ.setdefault(key, value)

import frame_geometry   # noqa: E402  (no torch at import time)
import master_detail    # noqa: E402  (numpy/PIL only, inside functions)

# The whole decision rule. Change here, never inline.
THRESHOLDS = {
    "lumaDead": 0.05,        # mean luma below this: black frame (inside a wall, night)
    "lumaWhite": 0.95,       # mean luma above this: whiteout (fog, sky-only)
    "structureMin": 0.05,    # less structure than this in the mask: no subject in frame
    "structureGuard": 0.8,   # a candidate may not drop structureFraction below this x incumbent
    "wallStructure": 0.8,    # structure above this AND edge below wallEdge = camera inside/against geometry;
    "wallEdge": 0.003,       # measured 2026-09-12: four wall frames 0.0007-0.0015, every real frame >= 0.0048
    "deadPx": 0.02,          # per-pixel floors, reported only
    "whitePx": 0.98,
}
GEOMETRY_WIDTH = 1600        # the corpus plane frame_geometry measures on (make_derivatives' large/)


def score(metrics):
    """Higher is better, within one build only. Edge density inside the mask, tempered by how
    much of the frame the mask covers, so a sliver of sharp wall does not beat a full facade."""
    g = metrics["geometry"]
    return round(float(g["subjectEdgeDensity"]) * math.sqrt(max(0.0, float(g["structureFraction"]))), 6)


def veto(receipt, metrics):
    """Reasons a frame is disqualified outright. Receipt reasons need no image."""
    reasons = []
    if receipt is None:
        return ["no-receipt"]
    if receipt.get("skipped"):
        reasons.append("skipped:" + str(receipt["skipped"]))
    if receipt.get("occluded") is True:
        reasons.append("occluded")
    if receipt.get("clearance") == "still_blocked":
        reasons.append("still-blocked")
    if receipt.get("pieces_near_aim") is not None and receipt["pieces_near_aim"] <= 0:
        reasons.append("no-pieces")
    if metrics is None:
        if not reasons:
            reasons.append("no-image")
        return reasons
    m = metrics["master"]
    if m["lumaMean"] < THRESHOLDS["lumaDead"]:
        reasons.append("dead-frame")
    if m["lumaMean"] > THRESHOLDS["lumaWhite"]:
        reasons.append("whiteout")
    g = metrics["geometry"]
    if g["structureFraction"] < THRESHOLDS["structureMin"]:
        reasons.append("no-structure")
    # A camera inside a roof reads as ~90% "structure" with no edges at all. Without this veto
    # the structure guard protects exactly the worst frame in the set (era11 a3e3c1fa, 09-12).
    if g["structureFraction"] > THRESHOLDS["wallStructure"] and g["subjectEdgeDensity"] < THRESHOLDS["wallEdge"]:
        reasons.append("wall")
    return reasons


def compare(incumbent, candidates):
    """incumbent/candidates: dicts with name, metrics (or None), vetoes (list), score (or None).
    Returns {"winner": name, "reason": str, "rows": [...]} -- the rows are the journal."""
    inc_ok = not incumbent["vetoes"] and incumbent["metrics"] is not None
    inc_struct = (incumbent["metrics"]["geometry"]["structureFraction"] if inc_ok else 0.0)
    inc_score = incumbent["score"] if inc_ok else None
    rows = []
    best = None
    for c in candidates:
        row = {"name": c["name"], "score": c["score"], "vetoes": list(c["vetoes"]),
               "delta": None, "guard_ok": None, "eligible": False}
        if c["vetoes"] or c["metrics"] is None:
            rows.append(row)
            continue
        row["guard_ok"] = (not inc_ok) or (
            c["metrics"]["geometry"]["structureFraction"] >= THRESHOLDS["structureGuard"] * inc_struct)
        row["delta"] = None if inc_score is None else round(c["score"] - inc_score, 6)
        row["eligible"] = bool(row["guard_ok"])
        if row["eligible"] and (best is None or c["score"] > best["score"]):
            best = c
        rows.append(row)
    if best is None:
        return {"winner": incumbent["name"],
                "reason": "no eligible candidate" if inc_ok else "incumbent vetoed and no eligible candidate",
                "rows": rows}
    if not inc_ok:
        return {"winner": best["name"], "reason": "incumbent vetoed; best eligible candidate", "rows": rows}
    if best["score"] > inc_score:
        return {"winner": best["name"],
                "reason": f"score {best['score']:.5f} > incumbent {inc_score:.5f}", "rows": rows}
    return {"winner": incumbent["name"], "reason": "no candidate beat the incumbent (ties keep it)", "rows": rows}


class Judge:
    def __init__(self, model=frame_geometry.MODEL, threads=8, device="cpu"):
        for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ.setdefault(key, str(threads))
        t0 = time.time()
        import numpy as np
        import torch
        from transformers import AutoImageProcessor, SegformerForSemanticSegmentation
        self.np, self.torch = np, torch
        torch.set_num_threads(threads)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass    # already started parallel work in this process; keep its setting
        self.device, self.threads, self.model_name = device, threads, model
        self.processor = AutoImageProcessor.from_pretrained(model)
        self.model = SegformerForSemanticSegmentation.from_pretrained(model).to(device).eval()
        self.group_ids = frame_geometry.build_group_ids(self.model.config.id2label)
        self.load_s = round(time.time() - t0, 2)

    def segment(self, img):
        """PIL RGB -> HxW ADE20K class ids at the image's own size."""
        torch = self.torch
        inputs = self.processor(images=img, return_tensors="pt").to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits
        up = torch.nn.functional.interpolate(
            logits, size=(img.size[1], img.size[0]), mode="bilinear", align_corners=False)
        return up.argmax(dim=1)[0].to("cpu").numpy()

    def measure(self, png_path):
        np = self.np
        from PIL import Image
        t0 = time.time()
        rgb = Image.open(png_path).convert("RGB")
        w, h = rgb.size
        decode_ms = round((time.time() - t0) * 1000)

        # Master plane: master_detail's tile math on the native luma, HUD cropped.
        t1 = time.time()
        l, t, r, b = master_detail.CROP_FRAC
        grey_img = rgb.convert("L").crop((int(l * w), int(t * h), int(r * w), int(b * h)))
        full = np.asarray(grey_img, dtype="float32") / 255.0
        gy, gx = np.gradient(full)
        grad = np.hypot(gx, gy)
        H, W = grad.shape
        tiles = []
        for j in range(master_detail.GRID_Y):
            for i in range(master_detail.GRID_X):
                tile = grad[j * H // master_detail.GRID_Y:(j + 1) * H // master_detail.GRID_Y,
                            i * W // master_detail.GRID_X:(i + 1) * W // master_detail.GRID_X]
                tiles.append(float(tile.mean()))
        tiles_sorted = sorted(tiles, reverse=True)
        top = max(1, len(tiles) // 10)
        total = sum(tiles) or 1e-9
        master = {
            "width": w, "height": h,
            "gradMean": round(float(grad.mean()), 5),
            "detailTop10": round(sum(tiles_sorted[:top]) / total, 4),
            "liveTileShare": round(sum(1 for x in tiles if x >= master_detail.LIVE_FLOOR) / float(len(tiles)), 4),
            "lumaMean": round(float(full.mean()), 4),
            "lumaStd": round(float(full.std()), 4),
            "deadFrac": round(float((full < THRESHOLDS["deadPx"]).mean()), 4),
            "whiteFrac": round(float((full > THRESHOLDS["whitePx"]).mean()), 4),
        }
        master_ms = round((time.time() - t1) * 1000)

        # Geometry plane: the 1600 px derivative the corpus was measured on, made the same way.
        t2 = time.time()
        dw = GEOMETRY_WIDTH
        dh = int(round(h * dw / float(w)))
        large = frame_geometry.crop_hud(rgb.resize((dw, dh), Image.LANCZOS))
        labels = self.segment(large)
        grey1600 = np.asarray(large.convert("L"), dtype="float32") / 255.0
        geometry = frame_geometry.measure(labels, grey1600, self.group_ids, np)
        model_ms = round((time.time() - t2) * 1000)

        return {"master": master, "geometry": geometry,
                "measuredOn": {"master": "master-native", "geometry": f"large-{dw}px"},
                "device": self.device, "threads": self.threads, "model": self.model_name,
                "timings": {"decode_ms": decode_ms, "master_ms": master_ms, "model_ms": model_ms,
                            "total_ms": round((time.time() - t0) * 1000)}}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--images", required=True, help="directory (recursed) of PNG masters")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--out", default="")
    args = p.parse_args()
    files = sorted(os.path.join(d, f) for d, _, fs in os.walk(args.images) for f in fs if f.lower().endswith(".png"))
    if args.limit:
        files = files[:args.limit]
    judge = Judge(threads=args.threads)
    print(f"model {judge.model_name} loaded in {judge.load_s}s on {judge.device} x{judge.threads}")
    out = {}
    for path in files:
        m = judge.measure(path)
        m["score"] = score(m)
        out[os.path.basename(path)] = m
        g, t = m["geometry"], m["timings"]
        print(f"{os.path.basename(path)}: score {m['score']:.5f} struct {g['structureFraction']:.3f} "
              f"edge {g['subjectEdgeDensity']:.4f} bbox {g['subjectBBoxFill']:.3f} sky {g['skyFraction']:.3f} "
              f"live {m['master']['liveTileShare']:.3f} luma {m['master']['lumaMean']:.3f} | "
              f"decode {t['decode_ms']} master {t['master_ms']} model {t['model_ms']} total {t['total_ms']} ms")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"schema": "steward-frame-judge/v1", "thresholds": THRESHOLDS, "frames": out}, fh, indent=1)


if __name__ == "__main__":
    main()

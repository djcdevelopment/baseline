#!/usr/bin/env python3
"""Judge one master against another, on the capture host's CPU, while the camera is still there.

The publication pipeline measures frames days later on another machine: derivatives,
shuttle, frame_geometry on a B70, a paired table by hand. That is fine for a corpus and
useless for a loop. This module packages the measurements so a worker can call them on
AM4 about a second after the shutter and decide whether to move the camera.

v2 (2026-09-12, after reading all 47 frames of era11-refine-r1 against the journal):
the decision is CLASS-FREE. SegFormer's ADE20K "structure" mask is wrong on this world
about as often as it is right -- 0 % on a dark twisted tower, 3.7 % on a stone tower,
8.7 % on snow-covered ice shrines, 88 % on the inside of a roof, 58 % "foliage" on
gold-veined marble -- and as a veto/guard it killed three of the best frames of the run
and protected the worst. It is kept for sky and water fractions only. What separated
good from bad, in the numbers already journalled: live-tile share (master_detail's tile
math on the native luma), mean luma, luma contrast, sky fraction, and the receipt's
pieces_near_aim (61 for a beam whose aim sat over open water; >= 515 for every other
build). The 47 eye labels live beside the journal (eye-labels.json) and --replay tests
any threshold change against them without a reshoot.

CPU only, deliberately: the GPU is rendering the next frame, the sample is tiny, and
b0 on eight threads is ~0.5 s per frame. Weights come from the local HF cache
(HF_HUB_OFFLINE); nothing is downloaded on the capture host.

    ~/venvs/torch-xpu/bin/python frame_judge.py --images <root>/images --limit 3
    python frame_judge.py --replay <root>/refine-journal.jsonl --labels eye-labels.json
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

# The whole decision rule. Change here, never inline; then run --replay.
THRESHOLDS = {
    "piecesMin": 200,        # receipt pieces_near_aim below this: the aim is off the build's mass
    "flatStd": 0.08,         # luma contrast below this: mist, whiteout, or the inside of a roof
    "lumaDark": 0.15,        # mean luma below this: shaded close-up, texels, black frame
    "skyMax": 0.75,          # sky fraction above this: aiming at air (linear builds, sky-chained mass)
    "liveMin": 0.10,         # live-tile share below this: nothing textured in frame
    "deadPx": 0.02,          # per-pixel floors, reported only
    "whitePx": 0.98,
}
GEOMETRY_WIDTH = 1600        # the corpus plane frame_geometry measures on (make_derivatives' large/)
# The aim is always at frame centre (the camera looks at it), so the middle window is the subject's.
CENTRAL_COLS = range(master_detail.GRID_X // 4, 3 * master_detail.GRID_X // 4)     # 4..11 of 16
CENTRAL_ROWS = range(master_detail.GRID_Y // 4, master_detail.GRID_Y - master_detail.GRID_Y // 4)  # 2..6 of 9


def score(metrics):
    """Higher is better, within one build only: how much of the frame is textured, times how
    strongly. Class-free on purpose -- see the module docstring.

    NOT a between-pose ranker. On the 77 blind pairs of 2026-09-12 the pose with the higher
    score was the one the eye kept 18 times against 25 (42 %); the eye rewards sky and light,
    this rewards texture fill, and they oppose. It remains the tie-break inside a gated pose's
    forced fan, nothing more. Any rule offered as a ranker must beat replay_pairs' 25.
    See docs/evidence/2026-09-12-refine-loop-calibration/."""
    m = metrics["master"]
    return round(float(m["liveTileShare"]) * float(m["gradMean"]), 7)


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
    pieces = receipt.get("pieces_near_aim")
    if pieces is not None and pieces < THRESHOLDS["piecesMin"]:
        reasons.append("aim-off-mass")
    if metrics is None:
        if not reasons:
            reasons.append("no-image")
        return reasons
    m = metrics["master"]
    g = metrics.get("geometry") or {}
    if m["lumaStd"] < THRESHOLDS["flatStd"]:
        reasons.append("flat")
    if m["lumaMean"] < THRESHOLDS["lumaDark"]:
        reasons.append("dark")
    if g.get("skyFraction") is not None and g["skyFraction"] > THRESHOLDS["skyMax"]:
        reasons.append("sky")
    if m["liveTileShare"] < THRESHOLDS["liveMin"]:
        reasons.append("no-texture")
    return reasons


def compare(incumbent, candidates):
    """incumbent/candidates: dicts with name, metrics (or None), vetoes (list), score (or None).
    Returns {"winner": name, "reason": str, "rows": [...]} -- the rows are the journal."""
    inc_ok = not incumbent["vetoes"] and incumbent["metrics"] is not None
    inc_score = incumbent["score"] if inc_ok else None
    rows, best = [], None
    for c in candidates:
        row = {"name": c["name"], "score": c["score"], "vetoes": list(c["vetoes"]), "delta": None, "eligible": False}
        if c["vetoes"] or c["metrics"] is None or c["score"] is None:
            rows.append(row)
            continue
        row["delta"] = None if inc_score is None else round(c["score"] - inc_score, 7)
        row["eligible"] = True
        if best is None or c["score"] > best["score"]:
            best = c
        rows.append(row)
    if best is None:
        return {"winner": incumbent["name"],
                "reason": "no eligible candidate" if inc_ok else "incumbent vetoed and no eligible candidate",
                "rows": rows}
    if not inc_ok:
        return {"winner": best["name"], "reason": "incumbent vetoed; best eligible candidate", "rows": rows}
    if best["score"] > inc_score:
        return {"winner": best["name"], "reason": f"score {best['score']:.6f} > incumbent {inc_score:.6f}", "rows": rows}
    return {"winner": incumbent["name"], "reason": "no candidate beat the incumbent (ties keep it)", "rows": rows}


def tile_metrics(grad, np):
    """master_detail's 16x9 tile pass plus the central window and the live-tile centroid."""
    H, W = grad.shape
    GX, GY = master_detail.GRID_X, master_detail.GRID_Y
    tiles = []
    for j in range(GY):
        row = []
        for i in range(GX):
            row.append(float(grad[j * H // GY:(j + 1) * H // GY, i * W // GX:(i + 1) * W // GX].mean()))
        tiles.append(row)
    flat = [t for row in tiles for t in row]
    tiles_sorted = sorted(flat, reverse=True)
    top = max(1, len(flat) // 10)
    total = sum(flat) or 1e-9
    live = [(i, j, tiles[j][i]) for j in range(GY) for i in range(GX) if tiles[j][i] >= master_detail.LIVE_FLOOR]
    central = [tiles[j][i] for j in CENTRAL_ROWS for i in CENTRAL_COLS]
    out = {
        "detailTop10": round(sum(tiles_sorted[:top]) / total, 4),
        "liveTileShare": round(len(live) / float(len(flat)), 4),
        "centralLiveShare": round(sum(1 for t in central if t >= master_detail.LIVE_FLOOR) / float(len(central)), 4),
        "centralGradMean": round(sum(central) / float(len(central)), 5),
        "liveCentroidX": None, "liveCentroidY": None,
    }
    if live:
        w = sum(t for _, _, t in live) or 1e-9
        out["liveCentroidX"] = round(sum((i + 0.5) / GX * t for i, _, t in live) / w, 4)
        out["liveCentroidY"] = round(sum((j + 0.5) / GY * t for _, j, t in live) / w, 4)
    return out


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
            pass
        self.device, self.threads, self.model_name = device, threads, model
        self.processor = AutoImageProcessor.from_pretrained(model)
        self.model = SegformerForSemanticSegmentation.from_pretrained(model).to(device).eval()
        self.group_ids = frame_geometry.build_group_ids(self.model.config.id2label)
        self.load_s = round(time.time() - t0, 2)

    def segment(self, img):
        torch = self.torch
        inputs = self.processor(images=img, return_tensors="pt").to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits
        up = torch.nn.functional.interpolate(logits, size=(img.size[1], img.size[0]), mode="bilinear", align_corners=False)
        return up.argmax(dim=1)[0].to("cpu").numpy()

    def measure(self, png_path):
        np = self.np
        from PIL import Image
        t0 = time.time()
        rgb = Image.open(png_path).convert("RGB")
        w, h = rgb.size
        decode_ms = round((time.time() - t0) * 1000)

        # Master plane: master_detail's tile math on the native luma, HUD cropped. This is the judge.
        t1 = time.time()
        l, t, r, b = master_detail.CROP_FRAC
        grey_img = rgb.convert("L").crop((int(l * w), int(t * h), int(r * w), int(b * h)))
        full = np.asarray(grey_img, dtype="float32") / 255.0
        gy, gx = np.gradient(full)
        grad = np.hypot(gx, gy)
        master = {"width": w, "height": h, "gradMean": round(float(grad.mean()), 5),
                  "lumaMean": round(float(full.mean()), 4), "lumaStd": round(float(full.std()), 4),
                  "deadFrac": round(float((full < THRESHOLDS["deadPx"]).mean()), 4),
                  "whiteFrac": round(float((full > THRESHOLDS["whitePx"]).mean()), 4)}
        master.update(tile_metrics(grad, np))
        master_ms = round((time.time() - t1) * 1000)

        # Geometry plane: SegFormer on the corpus' 1600 px plane. Kept for sky/water; the rest is logged.
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


# ---- offline replay against a journal and the eye labels
def replay(journal_path, labels_path=None):
    labels = json.load(open(labels_path, encoding="utf-8"))["labels"] if labels_path else {}
    build, judged, decisions = None, {}, []
    for line in open(journal_path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d["event"] == "plan_fed":
            build = d["name"].split("-")[1]
        elif d["event"] == "judged":
            m = {"master": d["master"], "geometry": d["geometry"]} if d.get("master") else None
            if m and "lumaStd" not in m["master"]:
                continue
            v = veto(d["receipt"], m)
            stem = os.path.basename(d["file"])[:-4] if d.get("file") else d["name"]
            judged[(build, d["name"])] = {"name": d["name"], "stem": stem, "metrics": m, "vetoes": v,
                                          "score": score(m) if m and not v else None, "old": d.get("vetoes")}
        elif d["event"] == "decision" and d.get("candidates"):
            decisions.append((build, d))
    by_class = {}
    for e in judged.values():
        lab = labels.get(e["stem"], "unlabelled")
        by_class.setdefault(lab, []).append(e)
    print("vetoes by eye label:")
    for lab in sorted(by_class):
        es = by_class[lab]
        vetoed = [e for e in es if e["vetoes"]]
        reasons = {}
        for e in vetoed:
            for r in e["vetoes"]:
                reasons[r] = reasons.get(r, 0) + 1
        flag = "  <-- GOOD frames vetoed" if lab == "GOOD" and vetoed else ""
        print(f"  {lab:16} {len(vetoed):2}/{len(es):<2} vetoed  {reasons}{flag}")
        for e in es:
            if (lab == "GOOD" and e["vetoes"]) or (lab.startswith("BAD") and not e["vetoes"]):
                print(f"      {e['stem']:<26} vetoes={e['vetoes']} score={e['score']}")
    print("\nround-1 decisions under the current rule:")
    for b, d in decisions:
        if d["round"] != 1:
            continue
        inc = judged.get((b, d["incumbent"]))
        cands = [judged[(b, c["name"])] for c in d["candidates"] if (b, c["name"]) in judged]
        if inc is None:
            continue
        v = compare(inc, cands)
        wl = labels.get(next((e["stem"] for e in [inc] + cands if e["name"] == v["winner"]), ""), "?")
        flag = "" if v["winner"] == d["winner"] else "  (was " + d["winner"] + ")"
        print(f"  {b} inc={d['incumbent']:<8} -> {v['winner']:<18} [{wl}] {v['reason']}{flag}")


# ---- offline replay of a between-pose rule against the eye's pair verdicts
def keep_planned(incumbent, fan):
    """The rule that won: never move off a pose that passed."""
    return "incumbent"


def higher_score(incumbent, fan):
    """The loop's rule: liveTileShare x gradMean, higher wins (the measured regression)."""
    a, b = (incumbent or {}).get("score"), (fan or {}).get("score")
    if a is None and b is None:
        return "incumbent"
    if b is None:
        return "incumbent"
    if a is None:
        return "winner"
    return "winner" if b > a else "incumbent"


RULES = {"keep-planned": keep_planned, "higher-score": higher_score}


def replay_pairs(verdicts, rule=keep_planned):
    """Score a between-pose rule against the pair verdicts (steward-pair-verdicts/v1).

    Only decided pairs count -- the ones where the eye chose the incumbent or the fan's pick;
    `neither` and `both` say nothing about which pose was better. Returns hits, decided, and
    the per-build calls so a new rule can be inspected, not just scored."""
    decided = [v for v in verdicts if v.get("chose") in ("incumbent", "winner")]
    calls = [(v["build"], rule(v.get("incMetrics"), v.get("fanMetrics")), v["chose"]) for v in decided]
    hits = sum(1 for _, call, chose in calls if call == chose)
    return {"rule": getattr(rule, "__name__", str(rule)), "hits": hits, "decided": len(decided),
            "rate": round(hits / len(decided), 3) if decided else None, "calls": calls}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pairs", help="pair-verdicts.json to score the built-in rules against (the 25-vs-18 bar)")
    p.add_argument("--images", help="directory (recursed) of PNG masters to measure")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--out", default="")
    p.add_argument("--replay", help="refine-journal.jsonl to re-decide offline under the current THRESHOLDS")
    p.add_argument("--labels", help="eye-labels.json to grade the replay against")
    args = p.parse_args()
    if args.pairs:
        verdicts = json.load(open(args.pairs, encoding="utf-8"))["verdicts"]
        for name, rule in RULES.items():
            r = replay_pairs(verdicts, rule)
            print(f"{name:14} {r['hits']:2}/{r['decided']} decided pairs ({r['rate']:.0%})")
        return
    if args.replay:
        replay(args.replay, args.labels)
        return
    if not args.images:
        p.error("--images, --replay or --pairs")
    files = sorted(os.path.join(d, f) for d, _, fs in os.walk(args.images) for f in fs if f.lower().endswith(".png"))
    if args.limit:
        files = files[:args.limit]
    judge = Judge(threads=args.threads)
    print(f"model {judge.model_name} loaded in {judge.load_s}s on {judge.device} x{judge.threads}")
    out = {}
    for path in files:
        m = judge.measure(path)
        m["score"] = score(m)
        m["vetoes"] = veto({}, m)
        out[os.path.basename(path)] = m
        mm, g, t = m["master"], m["geometry"], m["timings"]
        print(f"{os.path.basename(path)}: score {m['score']:.6f} live {mm['liveTileShare']:.2f} central {mm['centralLiveShare']:.2f} "
              f"grad {mm['gradMean']:.4f} luma {mm['lumaMean']:.2f} std {mm['lumaStd']:.3f} sky {g['skyFraction']:.2f} "
              f"cx {mm['liveCentroidX']} vetoes {m['vetoes']} | total {t['total_ms']} ms")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"schema": "steward-frame-judge/v2", "thresholds": THRESHOLDS, "frames": out}, fh, indent=1)


if __name__ == "__main__":
    main()

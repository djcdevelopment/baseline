r"""Per-asset face and framing signals for a waist-up portrait corpus.

    <venv>\python tools/portrait-corpus/face_qa.py --corpus E:\omen\DMos\artifacts\corpus-viking-profiles-20260910
        [--out <corpus>\face_qa.json] [--catalog <corpus>\catalog.json]

    venv: opencv-python-headless<5 (the 5.x wheels dropped the Haar XMLs) and mediapipe==0.10.14
    (the last release that bundles the BlazeFace models in the wheel; later ones need a download).

The slate48 library is bust-framed on a flat background, so a 128px tile is the face. This
corpus is waist-up on busy backgrounds: shown at 128px the face is a few dozen pixels unless
the tile is cut around it. So every asset gets a face box, a derived square bust crop, and
a confidence that a human face is where a head should be.

These are RANKING signals, not a gate. On 2026-09-11 every detector tried was wrong on the
one concept that matters most -- the berserker whose wolf pelt is painted as a wolf's head in
8 of 15 takes: Haar found a "face" in all 15; BlazeFace full-range found none, even where the
human face is plain; BlazeFace short-range found faces on rune-tattooed chests; gemini-3.5-flash
misread 5 of 15 on a 15-up sheet and 2 of 4 on a 4-up sheet; gemini-3.1-pro 1 of 4. Painted
fantasy portraits are outside what photo-trained detectors and vision models call a face
with any reliability. So: the numbers below order takes; the contact sheet and picks.json
decide, as they do for the slate48 library.

Signals per asset:
  detectors     which of {blaze_full, blaze_short, haar} put a box in the head zone (upper 55%
                of the frame, x within the middle 80%). Boxes outside the zone are discarded --
                that is where the false positives on chests and props live.
  confidence    0-3, number of detectors agreeing
  box, frac, cx_offset, cy_offset, facing   from the highest-scoring in-zone box
  bust_crop     square, side = 3.2 x face height, face centre 38% down; clamped. When no box
                exists the crop is the composition default [192, 0, 640] -- the head sits there
                in every take of every concept seen, wolf or human.
Flags (advisory): face_none (confidence 0), face_small (face height < 10% of frame),
face_off_centre (|cx_offset| > 0.30). Detections run on a 512px downscale; units are 1024.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("GLOG_minloglevel", "2")
warnings.filterwarnings("ignore")

import cv2  # noqa: E402
import mediapipe as mp  # noqa: E402
import numpy as np  # noqa: E402

DETECT_SIDE = 512
HEAD_ZONE_Y = 0.55
HEAD_ZONE_X = (0.10, 0.90)
MIN_FACE_HAAR = 28
SMALL_FRAC = 0.10
OFF_CENTRE = 0.30
CROP_FACTOR = 3.2
CROP_FACE_Y = 0.38
DEFAULT_CROP = [192, 0, 640]


def haar_cascades():
    root = Path(cv2.data.haarcascades)
    out = []
    for n in ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt2.xml", "haarcascade_profileface.xml"):
        c = cv2.CascadeClassifier(str(root / n))
        if c.empty():
            raise SystemExit(f"cascade missing: {root / n} (need opencv-python-headless<5)")
        out.append((n, c))
    return out


def in_zone(box_rel: tuple[float, float, float, float]) -> bool:
    x, y, w, h = box_rel
    cx, cy = x + w / 2, y + h / 2
    return cy < HEAD_ZONE_Y and HEAD_ZONE_X[0] < cx < HEAD_ZONE_X[1]


def haar_boxes(gray: np.ndarray, cascades) -> list[tuple[float, float, float, float, float]]:
    out = []
    s = gray.shape[0]
    for name, c in cascades:
        for flip in ((False,) if "profile" not in name else (False, True)):
            g = cv2.flip(gray, 1) if flip else gray
            for (x, y, w, h) in c.detectMultiScale(g, scaleFactor=1.08, minNeighbors=5, minSize=(MIN_FACE_HAAR, MIN_FACE_HAAR)):
                if flip:
                    x = s - x - w
                out.append((x / s, y / s, w / s, h / s, 0.5))
    return out


def blaze_boxes(det, rgb: np.ndarray) -> list[tuple[float, float, float, float, float]]:
    res = det.process(rgb)
    out = []
    for d in res.detections or []:
        bb = d.location_data.relative_bounding_box
        out.append((bb.xmin, bb.ymin, bb.width, bb.height, float(d.score[0])))
    return out


def best_in_zone(boxes):
    z = [b for b in boxes if in_zone(b[:4])]
    return max(z, key=lambda b: (b[4], b[2] * b[3])) if z else None


def bust_crop(box_px: tuple[int, int, int, int], frame: int) -> list[int]:
    x, y, w, h = box_px
    side = min(frame, int(round(h * CROP_FACTOR)))
    cx, cy = x + w / 2, y + h / 2
    x0 = max(0, min(frame - side, int(round(cx - side / 2))))
    y0 = max(0, min(frame - side, int(round(cy - side * CROP_FACE_Y))))
    return [x0, y0, side]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--catalog", type=Path, default=None)
    a = ap.parse_args()
    corpus = a.corpus.resolve()
    out = a.out or (corpus / "face_qa.json")
    skip = set()
    if a.catalog:
        cat = json.loads(a.catalog.read_text(encoding="utf-8"))
        skip = {x["asset_id"] for x in cat["assets"] if not x["decode_ok"]}
    ids = sorted(p.stem for p in (corpus / "assets").glob("*.png"))
    cascades = haar_cascades()
    fd = mp.solutions.face_detection
    rows = []
    counts = {"confidence_3": 0, "confidence_2": 0, "confidence_1": 0, "face_none": 0, "face_small": 0, "face_off_centre": 0}
    with fd.FaceDetection(model_selection=1, min_detection_confidence=0.3) as blaze_full, \
         fd.FaceDetection(model_selection=0, min_detection_confidence=0.3) as blaze_short:
        for i, aid in enumerate(ids, 1):
            if aid in skip:
                rows.append({"asset_id": aid, "confidence": 0, "detectors": [], "flags": ["skipped"], "bust_crop": DEFAULT_CROP})
                continue
            img = cv2.imread(str(corpus / "assets" / f"{aid}.png"), cv2.IMREAD_COLOR)
            if img is None:
                rows.append({"asset_id": aid, "confidence": 0, "detectors": [], "flags": ["unreadable"], "bust_crop": DEFAULT_CROP})
                continue
            frame = img.shape[0]
            small = cv2.resize(img, (DETECT_SIDE, DETECT_SIDE), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            gray = cv2.equalizeHist(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
            found = {
                "blaze_full": best_in_zone(blaze_boxes(blaze_full, rgb)),
                "blaze_short": best_in_zone(blaze_boxes(blaze_short, rgb)),
                "haar": best_in_zone(haar_boxes(gray, cascades)),
            }
            detectors = [k for k, v in found.items() if v]
            row = {"asset_id": aid, "confidence": len(detectors), "detectors": detectors, "flags": []}
            if detectors:
                # prefer the learned detectors' box; haar only when it is the sole vote
                order = [k for k in ("blaze_full", "blaze_short", "haar") if found[k]]
                x, y, w, h, score = found[order[0]]
                bx = (int(round(x * frame)), int(round(y * frame)), int(round(w * frame)), int(round(h * frame)))
                frac = h
                cx_off = (x + w / 2) - 0.5
                cy_off = (y + h / 2) - 0.5
                row.update({
                    "box": list(bx), "score": round(score, 3), "frac": round(frac, 4),
                    "cx_offset": round(cx_off, 4), "cy_offset": round(cy_off, 4),
                    "facing": "left" if cx_off < -0.06 else "right" if cx_off > 0.06 else "centre",
                    "bust_crop": bust_crop(bx, frame),
                })
                counts[f"confidence_{len(detectors)}"] += 1
                if frac < SMALL_FRAC:
                    row["flags"].append("face_small"); counts["face_small"] += 1
                if abs(cx_off) > OFF_CENTRE:
                    row["flags"].append("face_off_centre"); counts["face_off_centre"] += 1
            else:
                row.update({"bust_crop": DEFAULT_CROP, "facing": None})
                row["flags"].append("face_none"); counts["face_none"] += 1
            rows.append(row)
            if i % 200 == 0:
                print(f"  {i}/{len(ids)} {counts}", file=sys.stderr)
    doc = {
        "schema": "portrait-corpus-face-qa/2",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "corpus": corpus.name,
        "opencv": cv2.__version__, "mediapipe": mp.__version__,
        "params": {"detect_side": DETECT_SIDE, "head_zone_y": HEAD_ZONE_Y, "head_zone_x": HEAD_ZONE_X,
                   "small_frac": SMALL_FRAC, "off_centre": OFF_CENTRE, "crop_factor": CROP_FACTOR,
                   "crop_face_y": CROP_FACE_Y, "default_crop": DEFAULT_CROP},
        "advisory": "signals rank takes; they do not reject them -- see module docstring",
        "counts": counts,
        "assets": rows,
    }
    out.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"assets {len(rows)} | {counts}")
    print(f"face_qa {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

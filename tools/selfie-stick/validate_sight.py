#!/usr/bin/env python3
"""Retrodict run 20260827-165844: does sight.py flag the frames that were ruined?

The 16-frame roof-end run is a labelled test set that cost a capture slot already.
Six of the thirteen examined frames were lost to vegetation and boulders while the
terrain-only preflight reported 24-44 m of clearance, and the in-game probe recorded
occluded=false on every single one. If sight.py cannot separate those from the frames
that worked, it is not ready to gate a capture.

Labels are what the frames actually show, judged by eye and recorded in EXPERIMENT.md
lap 8. Poses come from the receipts, not from the plan: 1775_roofend2 was lifted 8 m
by the runtime, so the planned pose is not the geometry that produced the frame.

Usage: python validate_sight.py [--corridor 0.75] [--min-terrain 2.0]
"""
import argparse
import json
import os

import numpy as np

import sight
from terrain import TerrainEdits, TerrainGrid

HERE = os.path.dirname(os.path.abspath(__file__))
ERA = os.path.join(HERE, "out", "era17")
ARCH = os.path.join(ERA, "arch")
RECEIPTS = os.path.join(ARCH, "roofends-receipts.jsonl")

# What the frames show. See EXPERIMENT.md, lap 8.
LABELS = {
    "0310_roofend1.png": ("blocked", "camera inside a tree, full-frame foliage"),
    "0372_roofend1.png": ("blocked", "camera inside a boulder, build a distant speck"),
    "1775_roofend2.png": ("blocked", "trees fill the frame"),
    "0916_roofend2.png": ("blocked", "camera against a trunk, build behind foliage"),
    "0042_roofend2.png": ("blocked", "boulder gap, subject out of frame"),
    "1820_roofend1.png": ("clear", "hipped end, clean"),
    "1820_roofend2.png": ("clear", "gable end, clean"),
    "0042_roofend1.png": ("clear", "gable apex visible between birches"),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=sight.DEFAULT_DB)
    ap.add_argument("--occluders", default="",
                    help="parquet of a direct world export; when set, occluders come "
                         "from the world the camera actually flew through rather than "
                         "from the analytics cache snapshot")
    ap.add_argument("--snapshot-id", type=int, default=107)
    ap.add_argument("--corridor", type=float, default=0.75)
    ap.add_argument("--min-terrain", type=float, default=2.0)
    ap.add_argument("--subject-frac", type=float, default=0.8)
    ap.add_argument("--out", default=os.path.join(ARCH, "sight-validation.json"))
    args = ap.parse_args()

    receipts = {}
    with open(RECEIPTS, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            receipts[r["file"]] = r

    terrain = TerrainGrid.load()
    edits = os.path.join(ERA, "terrain-edits.npz")
    if os.path.exists(edits):
        terrain.edits = TerrainEdits.load(edits)
        terrain.source = "worldgen-cache+edits"

    results, tp, tn, fp, fn = [], 0, 0, 0, 0
    print("%-22s %-8s %-8s %s" % ("frame", "truth", "probe", "reason"))
    for fname, (truth, note) in LABELS.items():
        r = receipts[fname]
        cam = (r["placed"]["x"], r["placed"]["y"], r["placed"]["z"])
        aim = (r["aim"]["x"], r["aim"]["y"], r["aim"]["z"])
        lo = r.get("lens_offset_m", sight.LENS_OFFSET_M)
        bbox = (min(cam[0], aim[0]), max(cam[0], aim[0]),
                min(cam[2], aim[2]), max(cam[2], aim[2]))
        if args.occluders:
            idx = sight.OccluderIndex.from_parquet(args.occluders, bbox)
        else:
            idx = sight.OccluderIndex.from_cache(args.db, args.snapshot_id, bbox)
        v = sight.ray_clearance(idx, terrain, cam, aim, lens_offset=lo,
                                corridor_extra_m=args.corridor,
                                subject_frac=args.subject_frac,
                                min_terrain_m=args.min_terrain)
        probe = "clear" if v["clear"] else "blocked"
        if truth == "blocked" and probe == "blocked":
            tp += 1
        elif truth == "clear" and probe == "clear":
            tn += 1
        elif truth == "clear" and probe == "blocked":
            fp += 1
        else:
            fn += 1
        mark = "ok " if truth == probe else "MISS"
        print("%-22s %-8s %-8s %s %s" % (fname, truth, probe, mark,
                                         v["reason"] or "(%d occluders, terrain %.1f m)" %
                                         (v["occluders_considered"],
                                          v["min_terrain_clearance_m"] or -1)))
        results.append({"frame": fname, "truth": truth, "probe": probe,
                        "note": note, "verdict": v})

    n_blocked = sum(1 for t, _ in LABELS.values() if t == "blocked")
    n_clear = len(LABELS) - n_blocked
    print("\ncaught %d/%d blocked, passed %d/%d clear "
          "(false alarms %d, misses %d)" % (tp, n_blocked, tn, n_clear, fp, fn))
    gate = (tp == n_blocked and fp == 0)
    print("GATE: %s" % ("PASS" if gate else "FAIL - not ready to gate a capture"))

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"run": "20260827-165844",
                   "occluder_source": args.occluders or ("cache snapshot %d" % args.snapshot_id),
                   "settings": {"corridor_extra_m": args.corridor,
                                "min_terrain_m": args.min_terrain,
                                "subject_frac": args.subject_frac},
                   "caught_blocked": tp, "blocked_total": n_blocked,
                   "passed_clear": tn, "clear_total": n_clear,
                   "false_alarms": fp, "misses": fn, "gate": gate,
                   "frames": results}, fh, indent=1)
    print("wrote %s" % args.out)


if __name__ == "__main__":
    main()

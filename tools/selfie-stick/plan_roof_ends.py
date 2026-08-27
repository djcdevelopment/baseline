#!/usr/bin/env python3
"""Plan end-on roof elevations — the one view that can falsify a roof class.

plan_shots.orbit_azimuths offsets every orbit bearing 45 degrees off the long axis
on purpose: "dead-on the narrow face of a long building is the least informative
angle there is." That is correct for photographs and fatal for adjudication, because
the end is exactly where gable, hip and half-hip differ:

  gable      vertical wall triangle at BOTH ends, no roof plane
  hip        sloping roof plane at BOTH ends, no triangle
  half-hip   roof plane at ONE end, triangle at the other

So this plans the shot the gallery deliberately never takes: camera along the ridge
axis, low elevation (an architectural elevation, not a drone view), aimed high on the
structure so the roof fills the frame rather than the foundations.

Predictions are pre-registered in out/era17/arch/roof-end-predictions.json BEFORE the
capture, because the half-hip term was fitted post-hoc and a label invented after
seeing the frame proves nothing.

Terrain preflight is not optional here: occlusion is what made all three existing
exterior end-views of cluster 372 unusable, and the runtime silently lifts and
repitches a blocked camera, which would destroy the comparison. Each bearing escalates
elevation until the line of sight clears, and records what it had to do.

Usage: python plan_roof_ends.py [--cluster-ids ...]
"""
import argparse
import json
import math
import os

import duckdb
import numpy as np

from plan_shots import camera_for, validate_tsv
from terrain import TerrainEdits, TerrainGrid
from verify_rotation import HYPOTHESES
from reconstruct_cluster import ARCH, load_geometry
from segment_buildings import load_pieces, segment
from roof_sections import local_slope, sections, classify

HERE = os.path.dirname(os.path.abspath(__file__))
ERA = os.path.join(HERE, "out", "era17")
OUT = os.path.join(ARCH, "roof-end-predictions.json")
TSV = os.path.join(ARCH, "roof-ends.tsv")

LENS_OFFSET_M = 1.721          # measured on the 1820 control receipt
MIN_LOS_CLEARANCE_M = 2.0
ELEVATION_LADDER = [10.0, 14.0, 18.0, 24.0, 30.0]


def ang(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def roof_of_cluster(con, cid, geom, slope, to_rad, compose):
    pieces = load_pieces(con, cid, geom, to_rad, compose)
    comps = [c for c in segment(pieces) if len(c) >= 20]
    main = comps[0] if comps else range(len(pieces))
    roofs = []
    for i in main:
        p = pieces[i]
        if p["family"] != "roof":
            continue
        sl = slope.get(p["name"])
        if not sl:
            continue
        h, n_loc, pitch = sl
        n_w = p["R"] @ n_loc
        roofs.append({"center": p["center"], "n_w": n_w,
                      "offset": float(n_w @ p["center"]),
                      "bearing": float(np.degrees(np.arctan2(*(p["R"] @ h)[[0, 2]])) % 360),
                      "pitch": pitch, "y": float(p["center"][1])})
    if not roofs:
        return None, []
    secs = sections(roofs, 15.0, 0.75, 4.0)
    stats = []
    for g in secs:
        a = np.radians([roofs[i]["bearing"] for i in g])
        mb = float(np.degrees(np.arctan2(np.sin(a).mean(), np.cos(a).mean())) % 360)
        stats.append({"pieces": len(g), "bearing": round(mb, 1),
                      "pitch": round(float(np.mean([roofs[i]["pitch"] for i in g])), 1)})
    return classify(stats), stats


def end_bearings(shape, bearings, stats):
    """The two directions the ridge runs toward — where the classes differ."""
    weight = {}
    for s in stats:
        for b in bearings:
            if ang(s["bearing"], b) <= 25:
                weight[b] = weight.get(b, 0) + s["pieces"]
    pairs = [(a, b) for i, a in enumerate(bearings) for b in bearings[i + 1:]
             if abs(ang(a, b) - 180) <= 25]
    if not pairs:                                   # shed / single plane
        b = bearings[0]
        return [(b + 90) % 360, (b + 270) % 360], "profile of a single slope"
    dom = max(pairs, key=lambda p: weight.get(p[0], 0) + weight.get(p[1], 0))
    rest = [b for b in bearings if b not in dom]
    if rest:                                        # hip or half-hip
        ends = [rest[0], (rest[0] + 180) % 360]
        if len(rest) >= 2 and ang(rest[1], ends[1]) > 25:
            ends = [rest[0], rest[1]]
        return ends, "ends carry their own roof planes"
    return [(dom[0] + 90) % 360, (dom[0] + 270) % 360], "ends perpendicular to the pair"


def expectation(shape):
    if shape == "gable":
        return "vertical wall TRIANGLE at both ends, no roof plane"
    if shape == "hip":
        return "sloping roof PLANE at both ends, no triangle"
    if shape.startswith("half-hip"):
        return "roof PLANE at the first end, TRIANGLE at the second"
    if shape == "shed":
        return "asymmetric right-triangle profile, one slope only"
    return "unclassified"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster-ids", default="1820,1775,916,372,310,729,42,195")
    ap.add_argument("--margin", type=float, default=1.15)
    ap.add_argument("--max-distance", type=float, default=140.0)
    ap.add_argument("--aim-height", type=float, default=0.85)
    args = ap.parse_args()

    with open(os.path.join(ARCH, "rotation-verify.json"), encoding="utf-8") as fh:
        v = json.load(fh)
    to_rad, compose = HYPOTHESES[v["winner"]]
    geom = load_geometry(os.path.join(ARCH, "piece-geometry.json"))
    slope = {n: local_slope(e) for n, e in geom.items()
             if e["family"] == "roof" and e["snap_points"]}
    with open(os.path.join(ERA, "clusters.json"), encoding="utf-8") as fh:
        doc = json.load(fh)
    clusters = {c["cluster_id"]: c for c in doc["clusters"]}

    terrain = TerrainGrid.load()
    edits = os.path.join(ERA, "terrain-edits.npz")
    if os.path.exists(edits):
        terrain.edits = TerrainEdits.load(edits)
        terrain.source = "worldgen-cache+edits"

    con = duckdb.connect()
    shots, preds = [], {}
    for cid in [int(s) for s in args.cluster_ids.split(",") if s.strip()]:
        cluster = clusters[cid]
        (shape, bearings), stats = roof_of_cluster(con, cid, geom, slope, to_rad, compose)
        if not shape or shape == "unknown":
            print("  %-6d no classifiable roof, skipped" % cid)
            continue
        ends, why = end_bearings(shape, bearings, stats)
        preds[str(cid)] = {"class": shape, "plane_bearings": bearings,
                           "end_bearings": [round(e, 1) for e in ends],
                           "end_rule": why, "expect": expectation(shape),
                           "roof_sections": stats[:6]}
        print("  %-6d %-32s planes=%s ends=%s" %
              (cid, shape, [round(b, 1) for b in bearings], [round(e, 1) for e in ends]))
        for k, e in enumerate(ends):
            chosen = None
            for elev in ELEVATION_LADDER:
                cam = camera_for(cluster, e, elev, args.margin, args.max_distance,
                                 3.0, args.aim_height)
                c, aim = cam["camera"], cam["aim"]
                lens_y = c["y"] + LENS_OFFSET_M
                cl = []
                for i in range(41):
                    t = i / 50.0
                    x = c["x"] + (aim["x"] - c["x"]) * t
                    z = c["z"] + (aim["z"] - c["z"]) * t
                    ray = lens_y + (aim["y"] - lens_y) * t
                    cl.append(ray - terrain.ground_y_detail(x, z)[0])
                gy = terrain.ground_y_detail(c["x"], c["z"])[0]
                chosen = (cam, elev, min(cl), lens_y - gy)
                if min(cl) >= MIN_LOS_CLEARANCE_M:
                    break
            cam, elev, minc, lensc = chosen
            shots.append({
                "cluster_id": cid, "shot": "roofend%d" % (k + 1),
                "label": "cluster %d roof end %d" % (cid, k + 1),
                "predicted_class": shape, "end_bearing": round(e, 1),
                "expect": expectation(shape), **cam,
                "environment": "Clear", "time_of_day": 0.35,
                "terrain_preflight": {"elevation_used_deg": elev,
                                      "min_los_clearance_m": round(minc, 2),
                                      "lens_clearance_m": round(lensc, 2),
                                      "cleared": bool(minc >= MIN_LOS_CLEARANCE_M),
                                      "source": terrain.source}})
            print("      end%d bearing %6.1f -> elev %4.1f  LOS clearance %6.2f m %s"
                  % (k + 1, e, elev, minc, "" if minc >= MIN_LOS_CLEARANCE_M else "BLOCKED"))

    out = {"generated_from": "plan_roof_ends.py", "world": doc.get("world"),
           "decode": v["winner"], "pre_registered": True,
           "discriminator": {"gable": expectation("gable"), "hip": expectation("hip"),
                             "half-hip": expectation("half-hip"), "shed": expectation("shed")},
           "predictions": preds, "shots": shots,
           "limitations": [
               "Terrain preflight covers ground, not building self-occlusion or vegetation.",
               "Predictions are pre-registered; frames must be judged against them, not fitted to them.",
               "Elevation escalates until the ground line of sight clears, so some ends are less side-on than planned."]}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    with open(TSV, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\ttime\t"
                 "aim_x\taim_y\taim_z\tlabel\tmode\tfires\tflash\n")
        for s in shots:
            c, aim = s["camera"], s["aim"]
            fh.write("%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\t0\t\n" % (
                s["cluster_id"], s["shot"], c["x"], c["y"], c["z"],
                s["yaw_deg"], s["pitch_deg"], s["environment"], s["time_of_day"],
                aim["x"], aim["y"], aim["z"], s["label"]))
    ok, bad = validate_tsv(TSV)
    blocked = [s["cluster_id"] for s in shots if not s["terrain_preflight"]["cleared"]]
    print("\n%d shots, TSV rows ok=%d dropped=%d" % (len(shots), ok, bad))
    print("still blocked after escalation: %s" % (sorted(set(blocked)) or "none"))
    print("wrote %s\n      %s" % (OUT, TSV))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""R&D probe: is the roof PLANE the right unit, where the building was too coarse?

The prior lap recovered each roof piece's true slope (intrinsic to the prefab mesh,
derived from its snap points) but a whole-building bearing histogram still called
cluster 1820 "complex": its main gable pair (157.5 deg / 337.5 deg) was diluted by a
rooftop pavilion carrying its own roof at a different orientation.

A roof is properly a set of planar faces. This groups roof pieces into coplanar,
co-oriented, spatially adjacent sections, then asks whether the MAIN mass — the largest
roof body — classifies correctly on its own.

Section membership: two roof pieces join when their surface normals agree within
--normal-deg, their plane offsets agree within --offset-m, and their centres are within
--link-m of each other.

Usage: python roof_sections.py --cluster-ids 1820,1775,916
"""
import argparse
import json
import os
from collections import Counter

import duckdb
import numpy as np
from scipy.spatial import cKDTree

from verify_rotation import HYPOTHESES
from reconstruct_cluster import ARCH, load_geometry
from segment_buildings import UF, load_pieces, segment


def local_slope(entry):
    """Downhill unit vector, surface normal and pitch, from the prefab's snap geometry."""
    s = np.asarray(entry["snap_points"], dtype=float)
    if len(s) < 3:
        return None
    ys = s[:, 1]
    if ys.max() - ys.min() < 0.25:
        return None
    hi = s[ys >= ys.max() - 1e-6].mean(0)
    lo = s[ys <= ys.min() + 1e-6].mean(0)
    d = lo - hi
    horiz = np.array([d[0], 0.0, d[2]])
    run = np.linalg.norm(horiz)
    if run < 0.25:
        return None
    h = horiz / run
    pitch = float(np.arctan2(hi[1] - lo[1], run))
    n = h * np.sin(pitch) + np.array([0.0, 1.0, 0.0]) * np.cos(pitch)
    return h, n / np.linalg.norm(n), float(np.degrees(pitch))


def sections(roofs, normal_deg, offset_m, link_m):
    n = len(roofs)
    uf = UF(n)
    centers = np.array([r["center"] for r in roofs])
    tree = cKDTree(centers)
    cos_tol = np.cos(np.radians(normal_deg))
    for i in range(n):
        for j in tree.query_ball_point(centers[i], link_m):
            if j <= i:
                continue
            if float(roofs[i]["n_w"] @ roofs[j]["n_w"]) < cos_tol:
                continue
            if abs(roofs[i]["offset"] - roofs[j]["offset"]) > offset_m:
                continue
            uf.union(i, j)
    groups = {}
    for i in range(n):
        groups.setdefault(uf.find(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)


def classify(sec_stats, min_share=0.30):
    """Roof class from the section bearings that actually carry the roof.

    Share is measured against the LARGEST section, not the total. Measuring against
    the total is wrong on fragmented roofs: a long tail of small sections inflates the
    denominator until only the single biggest plane clears the bar, which reported
    cluster 916's four-plane roof as a "shed"."""
    if not sec_stats:
        return "unknown", []
    biggest = max(s["pieces"] for s in sec_stats)
    strong = [s for s in sec_stats if s["pieces"] >= min_share * biggest]
    if not strong:
        return "unknown", []
    # Distinct plane ORIENTATIONS: two disconnected patches of one plane are one
    # orientation, not two. Merge strong sections whose bearings agree within 25 deg.
    dirs = []
    for s in sorted(strong, key=lambda s: -s["pieces"]):
        for d in dirs:
            gap = abs(d["bearing"] - s["bearing"]) % 360
            if min(gap, 360 - gap) <= 25:
                d["pieces"] += s["pieces"]
                break
        else:
            dirs.append({"bearing": s["bearing"], "pieces": s["pieces"]})
    bearings = [round(d["bearing"], 1) for d in dirs]
    if len(dirs) == 1:
        return "shed", bearings
    if len(dirs) == 2:
        gap = abs(dirs[0]["bearing"] - dirs[1]["bearing"]) % 360
        gap = min(gap, 360 - gap)
        return ("gable" if abs(gap - 180) <= 25 else "cross-gable/L"), bearings
    if len(dirs) == 3:
        # two opposing planes plus one end slope is a gable with a hipped end
        for i in range(3):
            a, b = dirs[i]["bearing"], dirs[(i + 1) % 3]["bearing"]
            gap = abs(a - b) % 360
            if abs(min(gap, 360 - gap) - 180) <= 25:
                return "half-hip (gable + one hipped end)", bearings
        return "hip", bearings
    if len(dirs) == 4:
        return "hip", bearings
    return "complex", bearings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster-ids", default="1820,1775,916")
    ap.add_argument("--normal-deg", type=float, default=15.0)
    ap.add_argument("--offset-m", type=float, default=0.75)
    ap.add_argument("--link-m", type=float, default=4.0)
    ap.add_argument("--out", default=os.path.join(ARCH, "roof-sections.json"))
    args = ap.parse_args()

    with open(os.path.join(ARCH, "rotation-verify.json"), encoding="utf-8") as fh:
        v = json.load(fh)
    assert v["verdict"] == "PASS", v["verdict"]
    to_rad, compose = HYPOTHESES[v["winner"]]
    geom = load_geometry(os.path.join(ARCH, "piece-geometry.json"))
    slope = {n: local_slope(e) for n, e in geom.items()
             if e["family"] == "roof" and e["snap_points"]}
    con = duckdb.connect()
    report = {"clusters": {}}

    for cid in [int(s) for s in args.cluster_ids.split(",") if s.strip()]:
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
                          "pitch": pitch, "y": float(p["center"][1]), "name": p["name"]})
        print("\n=== cluster %d: main structure %d pieces, %d sloped roof pieces"
              % (cid, len(main), len(roofs)))
        if not roofs:
            print("   no sloped roof pieces")
            continue
        secs = sections(roofs, args.normal_deg, args.offset_m, args.link_m)
        stats = []
        for g in secs:
            b = np.array([roofs[i]["bearing"] for i in g])
            ang = np.radians(b)
            mb = float(np.degrees(np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())) % 360)
            ys = np.array([roofs[i]["y"] for i in g])
            stats.append({"pieces": len(g), "bearing": round(mb, 1),
                          "pitch": round(float(np.mean([roofs[i]["pitch"] for i in g])), 1),
                          "y_mean": round(float(ys.mean()), 1),
                          "y_span": round(float(ys.max() - ys.min()), 1)})
        for k, s in enumerate(stats[:8]):
            print("   sec#%d: %4d pieces  bearing=%6.1f  pitch=%4.1f  y=%.1f (span %.1f)"
                  % (k, s["pieces"], s["bearing"], s["pitch"], s["y_mean"], s["y_span"]))
        if len(stats) > 8:
            print("   ... %d more sections, %d pieces"
                  % (len(stats) - 8, sum(s["pieces"] for s in stats[8:])))

        shape, bearings = classify(stats)
        print("   ALL SECTIONS      -> %s  %s" % (shape, [round(b, 1) for b in bearings]))

        # Main mass = sections sharing the dominant roof height band (drop rooftop
        # structures sitting above it, which is what diluted the whole-building label).
        top = stats[0]
        band = [s for s in stats if abs(s["y_mean"] - top["y_mean"]) <= 4.0]
        shape_m, bearings_m = classify(band)
        print("   MAIN MASS (%d of %d sections, y within 4 m of largest) -> %s  %s"
              % (len(band), len(stats), shape_m, [round(b, 1) for b in bearings_m]))
        above = [s for s in stats if s["y_mean"] - top["y_mean"] > 4.0]
        if above:
            print("   above main mass: %d sections, %d pieces (rooftop structures)"
                  % (len(above), sum(s["pieces"] for s in above)))
        report["clusters"][str(cid)] = {
            "main_structure_pieces": len(main), "sloped_roof_pieces": len(roofs),
            "sections": stats, "all_sections_class": shape,
            "main_mass_class": shape_m, "main_mass_bearings": bearings_m,
            "sections_above_main_mass": len(above)}

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print("\nwrote %s" % args.out)


if __name__ == "__main__":
    main()

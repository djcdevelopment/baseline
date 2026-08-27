#!/usr/bin/env python3
"""R&D probe: is the frozen cluster the wrong unit of architectural analysis?

L3 scored storey count, roof class and openings at 5/10, and the named failures all
smell the same way: cluster 916 six "storeys" are elevation bands across a low
COMPOUND, not one stack. A 16 m occupancy cluster with 3-D connectivity happily merges
a longhouse, its outbuilding and a wall 4 m away into one "structure", and every
semantic label is then computed over that union.

This segments a cluster into physically connected structures and recomputes the same
facts per structure. Contact = snap-point coincidence (5 cm) OR oriented-box overlap
(separating-axis test, 5 cm inflation). Membership comes from the verified frozen
artifact cluster-zdos.parquet, joined to the rotation export by zdo_index.

Usage: python segment_buildings.py --cluster-ids 916,1820,1775
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

HERE = os.path.dirname(os.path.abspath(__file__))
CP = r"E:\omen\steward-era17-arch\cluster-zdos.parquet"
BG = r"E:\omen\steward-era17-arch\building-geometry.parquet"


class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def load_pieces(con, cid, geom_by_name, to_rad, compose):
    rows = con.execute("""
        SELECT c.zdo_index, c.prefab_name, c.x, c.y, c.z,
               b.has_rot, b.rot_x, b.rot_y, b.rot_z, c.creator_id
        FROM read_parquet(?) c JOIN read_parquet(?) b USING (zdo_index)
        WHERE c.cluster_id = ? ORDER BY c.zdo_index""", [CP, BG, cid]).fetchall()
    out = []
    for zi, name, x, y, z, has_rot, rx, ry, rz, creator in rows:
        g = geom_by_name.get(name)
        if not g:
            continue
        if has_rot:
            ax, ay, az = (np.asarray([v * to_rad]) for v in (rx, ry, rz))
            R = compose(ax, ay, az)[0]
        else:
            R = np.eye(3)
        pivot = np.array([x, y, z])
        center = pivot + R @ np.asarray(g["center_offset"])
        out.append({"zdo": zi, "name": name, "family": g["family"], "creator": creator,
                    "pivot": pivot, "R": R, "half": np.asarray(g["extents"]) / 2.0,
                    "center": center, "snaps": g["snap_points"]})
    return out


def obb_overlap(a, b, infl=0.05):
    """Separating-axis test on two oriented boxes, each inflated by infl metres."""
    Ra, Rb = a["R"], b["R"]
    ha, hb = a["half"] + infl, b["half"] + infl
    t = b["center"] - a["center"]
    Rab = Ra.T @ Rb
    absR = np.abs(Rab) + 1e-9
    ta = Ra.T @ t
    for i in range(3):
        if abs(ta[i]) > ha[i] + float(hb @ absR[i]):
            return False
    tb = Rb.T @ t
    for j in range(3):
        if abs(tb[j]) > hb[j] + float(ha @ absR[:, j]):
            return False
    for i in range(3):
        for j in range(3):
            i1, i2 = (i + 1) % 3, (i + 2) % 3
            j1, j2 = (j + 1) % 3, (j + 2) % 3
            ra = ha[i1] * absR[i2, j] + ha[i2] * absR[i1, j]
            rb = hb[j1] * absR[i, j2] + hb[j2] * absR[i, j1]
            if abs(ta[i2] * Rab[i1, j] - ta[i1] * Rab[i2, j]) > ra + rb:
                return False
    return True


def segment(pieces, eps=0.05):
    n = len(pieces)
    uf = UF(n)
    pts, owner = [], []
    for i, p in enumerate(pieces):
        if not p["snaps"]:
            continue
        w = np.asarray(p["snaps"]) @ p["R"].T + p["pivot"]
        pts.append(w)
        owner.extend([i] * len(w))
    if pts:
        pts = np.vstack(pts)
        owner = np.asarray(owner)
        for a, b in cKDTree(pts).query_pairs(eps, output_type="ndarray"):
            if owner[a] != owner[b]:
                uf.union(int(owner[a]), int(owner[b]))

    centers = np.array([p["center"] for p in pieces])
    radii = np.array([np.linalg.norm(p["half"]) for p in pieces])
    tree = cKDTree(centers)
    rmax = float(radii.max())
    for i, p in enumerate(pieces):
        for j in tree.query_ball_point(centers[i], radii[i] + rmax + 0.1):
            if j <= i:
                continue
            if np.linalg.norm(centers[i] - centers[j]) > radii[i] + radii[j] + 0.1:
                continue
            if uf.find(i) == uf.find(j):
                continue
            if obb_overlap(p, pieces[j]):
                uf.union(i, j)

    comps = {}
    for i in range(n):
        comps.setdefault(uf.find(i), []).append(i)
    return sorted(comps.values(), key=len, reverse=True)


def storeys_of(members, pieces):
    fy = np.array([pieces[i]["pivot"][1] for i in members
                   if pieces[i]["family"] == "floor"])
    if fy.size == 0:
        return []
    lo, hi = fy.min(), fy.max()
    hist, edges = np.histogram(fy, bins=np.arange(lo - .125, hi + .375, .25))
    out = []
    for bi in np.argsort(hist)[::-1]:
        if hist[bi] < max(3, int(.02 * fy.size)):
            break
        lvl = float((edges[bi] + edges[bi + 1]) / 2)
        if all(abs(lvl - s) >= 2.0 for s in out):
            out.append(round(lvl, 2))
    return sorted(out)


def roof_of(members, pieces):
    rr = [pieces[i] for i in members if pieces[i]["family"] == "roof"]
    if not rr:
        return None, 0
    yaws = Counter()
    for p in rr:
        yaw = np.degrees(np.arctan2(p["R"][0, 2], p["R"][2, 2])) % 180.0
        yaws[round(yaw / 22.5) * 22.5 % 180.0] += 1
    strong = [y for y, c in yaws.items() if c >= max(3, .1 * len(rr))]
    shape = ("flat" if not yaws else "gable" if len(strong) <= 2
             else "hip" if len(strong) <= 4 else "complex")
    return shape, len(rr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster-ids", default="916,1820,1775")
    ap.add_argument("--min-pieces", type=int, default=20)
    ap.add_argument("--out", default=os.path.join(ARCH, "segmentation.json"))
    args = ap.parse_args()

    with open(os.path.join(ARCH, "rotation-verify.json"), encoding="utf-8") as fh:
        v = json.load(fh)
    assert v["verdict"] == "PASS", v["verdict"]
    to_rad, compose = HYPOTHESES[v["winner"]]
    geom = load_geometry(os.path.join(ARCH, "piece-geometry.json"))
    con = duckdb.connect()
    report = {"decode": v["winner"], "clusters": {}}

    for cid in [int(s) for s in args.cluster_ids.split(",") if s.strip()]:
        pieces = load_pieces(con, cid, geom, to_rad, compose)
        comps = segment(pieces)
        big = [c for c in comps if len(c) >= args.min_pieces]
        whole = storeys_of(range(len(pieces)), pieces)
        wshape, wroof = roof_of(range(len(pieces)), pieces)
        print("\n=== cluster %d: %d pieces -> %d components (%d >= %d pieces)"
              % (cid, len(pieces), len(comps), len(big), args.min_pieces))
        print("  WHOLE-CLUSTER (what L3 judged): storeys=%d %s roof=%s"
              % (len(whole), whole, wshape))
        structs = []
        for k, c in enumerate(big[:8]):
            ys = np.array([pieces[i]["pivot"][1] for i in c])
            st = storeys_of(c, pieces)
            shape, nroof = roof_of(c, pieces)
            fams = Counter(pieces[i]["family"] for i in c)
            structs.append({"rank": k, "pieces": len(c),
                            "height_m": round(float(ys.max() - ys.min()), 1),
                            "storeys": st, "roof": shape, "roof_pieces": nroof,
                            "top_families": dict(fams.most_common(4))})
            print("   #%d: %5d pieces  h=%5.1fm  storeys=%d %s  roof=%s(%d)"
                  % (k, len(c), ys.max() - ys.min(), len(st), st, shape, nroof))
        tail = sum(len(c) for c in comps if len(c) < args.min_pieces)
        print("   tail: %d components < %d pieces (%d pieces, %.1f%%)"
              % (len(comps) - len(big), args.min_pieces, tail,
                 100 * tail / max(len(pieces), 1)))
        report["clusters"][str(cid)] = {
            "pieces": len(pieces), "components": len(comps), "structures": structs,
            "whole_cluster": {"storeys": whole, "roof": wshape, "roof_pieces": wroof},
            "tail_components": len(comps) - len(big), "tail_pieces": tail}

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print("\nwrote %s" % args.out)


if __name__ == "__main__":
    main()

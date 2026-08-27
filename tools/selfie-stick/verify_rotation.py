#!/usr/bin/env python3
"""Discriminate the ZDO rotation encoding, using the buildings themselves as the oracle.

The save stores 12 rotation bytes (3 floats) per rotated ZDO. The export's range scan
already settled units — every component lives in [0, 360) — but axis ORDER and SIGN
still have to be proven, and a wrong guess yields walls that face plausible-but-wrong
ways, which no eyeball catches reliably.

The oracle: snapped construction. Almost every placed piece is snapped to a neighbour,
and snap points live in pivot-local space (piece-geometry.json). Under the CORRECT
rotation hypothesis, transforming each piece's snap points to world space makes snapped
neighbours' points coincide within centimetres; under a wrong axis order they coincide
only for unrotated or symmetric pieces. So: transform under each hypothesis, count
coincidences, and the hypothesis with the highest alignment rate — by a wide margin,
on every pilot cluster — is the decode. No photographs needed.

Pieces without the rotation flag (6% of the export) are assumed identity; their
alignment rate is reported separately, which doubles as the test of that assumption.

Writes out/era17/arch/rotation-verify.json; downstream tools import the winner from
there rather than hardcoding it.

Usage:
  python verify_rotation.py [--parquet PATH] [--geometry PATH] [--clusters PATH]
                            [--cluster-ids 1,2,3] [--epsilon 0.05] [--pad 8]
"""
import argparse
import json
import math
import os
import sys

import duckdb
import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PARQUET = r"E:\omen\steward-era17-arch\building-geometry.parquet"
DEFAULT_GEOMETRY = os.path.join(HERE, "out", "era17", "arch", "piece-geometry.json")
DEFAULT_CLUSTERS = os.path.join(HERE, "out", "era17", "clusters.json")
DEFAULT_OUT = os.path.join(HERE, "out", "era17", "arch", "rotation-verify.json")


def rx(a):
    c, s = np.cos(a), np.sin(a)
    m = np.zeros(a.shape + (3, 3)); m[..., 0, 0] = 1
    m[..., 1, 1] = c; m[..., 1, 2] = -s; m[..., 2, 1] = s; m[..., 2, 2] = c
    return m


def ry(a):
    c, s = np.cos(a), np.sin(a)
    m = np.zeros(a.shape + (3, 3)); m[..., 1, 1] = 1
    m[..., 0, 0] = c; m[..., 0, 2] = s; m[..., 2, 0] = -s; m[..., 2, 2] = c
    return m


def rz(a):
    c, s = np.cos(a), np.sin(a)
    m = np.zeros(a.shape + (3, 3)); m[..., 2, 2] = 1
    m[..., 0, 0] = c; m[..., 0, 1] = -s; m[..., 1, 0] = s; m[..., 1, 1] = c
    return m


# name -> (to_radians, compose). Unity's euler is applied Z, then X, then Y, which as a
# column-vector matrix product is Ry @ Rx @ Rz. The rest are the plausible wrong answers,
# kept so the report SHOWS the discrimination instead of asserting it. rad_unity is the
# control the range test already killed.
HYPOTHESES = {
    "deg_unity":     (math.radians(1.0), lambda x, y, z: ry(y) @ rx(x) @ rz(z)),
    "deg_unity_neg": (math.radians(-1.0), lambda x, y, z: ry(y) @ rx(x) @ rz(z)),
    "deg_xyz":       (math.radians(1.0), lambda x, y, z: rx(x) @ ry(y) @ rz(z)),
    "deg_zxy":       (math.radians(1.0), lambda x, y, z: rz(z) @ rx(x) @ ry(y)),
    "rad_unity":     (1.0, lambda x, y, z: ry(y) @ rx(x) @ rz(z)),
}


def quantization_pretest(con, parquet):
    """Players snap-rotate in 22.5-degree steps; the true unit shows a sharp peak at 0."""
    row = con.execute(f"""
        SELECT
          count(*),
          avg(CASE WHEN least(m_deg, 22.5 - m_deg) < 0.5 THEN 1.0 ELSE 0.0 END),
          avg(CASE WHEN least(m_rad, 0.3927 - m_rad) < 0.0087 THEN 1.0 ELSE 0.0 END)
        FROM (
          SELECT abs(rot_y) % 22.5 AS m_deg, abs(rot_y) % 0.3927 AS m_rad
          FROM read_parquet('{parquet}') WHERE has_rot = 1 AND category = 'BUILDING'
        )""").fetchone()
    return {"rows": row[0],
            "yaw_on_22p5_deg_grid_pct": round(100.0 * row[1], 2),
            "yaw_on_22p5_rad_grid_pct": round(100.0 * row[2], 2)}


def load_cluster_pieces(con, parquet, bbox, pad, snap_by_name):
    min_x, max_x, min_y, max_y, min_z, max_z = bbox
    rows = con.execute(f"""
        SELECT prefab_name, x, y, z, has_rot, rot_x, rot_y, rot_z
        FROM read_parquet('{parquet}')
        WHERE x BETWEEN ? AND ? AND z BETWEEN ? AND ? AND y BETWEEN ? AND ?
          AND prefab_name IS NOT NULL
        """, [min_x - pad, max_x + pad, min_z - pad, max_z + pad,
              min_y - pad, max_y + pad]).fetchall()
    return [r for r in rows if snap_by_name.get(r[0])]


def sig_angle(v):
    """Distance from the nearest full turn, degrees-as-stored."""
    m = abs(v) % 360.0
    return min(m, 360.0 - m)


def alignment(pieces, snap_by_name, to_rad, compose, epsilon):
    """Match stats for one hypothesis.

    The aggregate rate cannot separate axis ORDERS: composition order only matters
    for pieces with two or more non-zero euler components, and pure-yaw pieces (the
    overwhelming majority of any build) transform identically under every order. So
    the discriminating number is multiaxis_rate — the match rate over snap points of
    multi-axis pieces — and the aggregate is the health check."""
    pts, piece_ids, flagless_mask, multi_mask = [], [], [], []
    for pid, (name, x, y, z, has_rot, rot_xv, rot_yv, rot_zv) in enumerate(pieces):
        snaps = np.asarray(snap_by_name[name], dtype=np.float64)
        multi = False
        if has_rot:
            ax = np.asarray([rot_xv * to_rad]); ay = np.asarray([rot_yv * to_rad])
            az = np.asarray([rot_zv * to_rad])
            rot = compose(ax, ay, az)[0]
            world = snaps @ rot.T + np.array([x, y, z])
            multi = sum(1 for v in (rot_xv, rot_yv, rot_zv) if sig_angle(v) > 1.0) >= 2
        else:
            world = snaps + np.array([x, y, z])
        pts.append(world)
        piece_ids.extend([pid] * len(snaps))
        flagless_mask.extend([not has_rot] * len(snaps))
        multi_mask.extend([multi] * len(snaps))
    if not pts:
        return None
    pts = np.vstack(pts)
    piece_ids = np.asarray(piece_ids)
    flagless_mask = np.asarray(flagless_mask)
    multi_mask = np.asarray(multi_mask)

    tree = cKDTree(pts)
    k = min(12, len(pts))
    dist, idx = tree.query(pts, k=k)
    other = piece_ids[idx] != piece_ids[:, None]
    dist_other = np.where(other, dist, np.inf)
    nn_other = dist_other.min(axis=1)
    matched = nn_other < epsilon
    flagless_rate = (float(matched[flagless_mask].mean())
                     if flagless_mask.any() else None)
    multi_rate = float(matched[multi_mask].mean()) if multi_mask.any() else None
    finite = nn_other[np.isfinite(nn_other)]
    return {
        "match_rate": round(float(matched.mean()), 4),
        "multiaxis_match_rate": (round(multi_rate, 4) if multi_rate is not None else None),
        "n_multiaxis_snap_points": int(multi_mask.sum()),
        "median_nn_other_m": round(float(np.median(finite)), 4) if finite.size else None,
        "n_snap_points": int(len(pts)),
        "flagless_match_rate": (round(flagless_rate, 4)
                                if flagless_rate is not None else None),
    }


def pick_pilots(clusters, con, parquet, snap_by_name, pad, want=5):
    """Pilot criteria: in-world, mid-sized, one dominant creator, enough snap-bearing
    pieces including genuinely pitched/rolled ones (pure yaw cannot discriminate sign)."""
    cands = [c for c in clusters
             if c.get("region") == "in-world" and not c.get("sky")
             and 100 <= c["pieces"] <= 1500
             and (c.get("top_creator_share") or 0) >= 0.7]
    cands.sort(key=lambda c: -c.get("distinct_prefabs", 0))
    picked = []
    for c in cands:
        bbox = (c["min_x"], c["max_x"], c["min_y"], c["max_y"], c["min_z"], c["max_z"])
        pieces = load_cluster_pieces(con, parquet, bbox, pad, snap_by_name)
        multi = sum(1 for p in pieces if p[4] and
                    sum(1 for v in (p[5], p[6], p[7]) if sig_angle(v) > 1.0) >= 2)
        if len(pieces) >= 50 and multi >= 10:
            picked.append((c, pieces))
            print(f"  pilot {c['cluster_id']}: {c['pieces']} pieces, "
                  f"{len(pieces)} snap-bearing, {multi} multi-axis", flush=True)
        if len(picked) >= want:
            break
    return picked


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--parquet", default=DEFAULT_PARQUET)
    p.add_argument("--geometry", default=DEFAULT_GEOMETRY)
    p.add_argument("--clusters", default=DEFAULT_CLUSTERS)
    p.add_argument("--cluster-ids", default="",
                   help="explicit pilot cluster ids (default: auto-pick 5)")
    p.add_argument("--epsilon", type=float, default=0.05)
    p.add_argument("--pad", type=float, default=8.0)
    p.add_argument("--out", default=DEFAULT_OUT)
    args = p.parse_args()

    with open(args.geometry, encoding="utf-8") as fh:
        geometry = json.load(fh)
    snap_by_name = {e["name"]: e["snap_points"]
                    for e in geometry["pieces"] if e["snap_points"]}
    with open(args.clusters, encoding="utf-8") as fh:
        clusters = json.load(fh)["clusters"]

    parquet = args.parquet.replace("'", "''").replace("\\", "/")
    con = duckdb.connect()

    print("quantization pre-test (whole parquet):", flush=True)
    pre = quantization_pretest(con, parquet)
    print(f"  BUILDING rows with rotation: {pre['rows']:,}")
    print(f"  yaw on 22.5-DEGREE grid (+-0.5 deg): {pre['yaw_on_22p5_deg_grid_pct']}%")
    print(f"  yaw on 22.5-deg-as-RADIAN grid:      {pre['yaw_on_22p5_rad_grid_pct']}%")

    if args.cluster_ids:
        ids = {int(s) for s in args.cluster_ids.split(",") if s.strip()}
        chosen = [c for c in clusters if c["cluster_id"] in ids]
        pilots = []
        for c in chosen:
            bbox = (c["min_x"], c["max_x"], c["min_y"], c["max_y"], c["min_z"], c["max_z"])
            pilots.append((c, load_cluster_pieces(con, parquet, bbox, args.pad, snap_by_name)))
    else:
        print("\npicking pilot clusters:", flush=True)
        pilots = pick_pilots(clusters, con, parquet, snap_by_name, args.pad)
    if not pilots:
        sys.exit("no pilot clusters matched the criteria")

    results = {name: {} for name in HYPOTHESES}
    for c, pieces in pilots:
        cid = c["cluster_id"]
        for name, (to_rad, compose) in HYPOTHESES.items():
            r = alignment(pieces, snap_by_name, to_rad, compose, args.epsilon)
            results[name][str(cid)] = r

    def mean_of(metric, name):
        vals = [results[name][str(c['cluster_id'])].get(metric) for c, _ in pilots]
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else 0.0

    print(f"\nsnap alignment (epsilon {args.epsilon} m) — "
          f"aggregate | multi-axis subset (the order discriminator):")
    header = "  {:<14}".format("hypothesis") + "".join(
        f"{str(c['cluster_id']):>16}" for c, _ in pilots) + "  mean(all)  mean(multi)"
    print(header)
    means, multi_means = {}, {}
    for name in HYPOTHESES:
        means[name] = mean_of("match_rate", name)
        multi_means[name] = mean_of("multiaxis_match_rate", name)
        cells = []
        for c, _ in pilots:
            r = results[name][str(c['cluster_id'])]
            mr = r.get("multiaxis_match_rate")
            cells.append(f"{r['match_rate']:.3f}|" +
                         (f"{mr:.3f}" if mr is not None else "  -  "))
        print("  {:<14}".format(name) + "".join(f"{cell:>16}" for cell in cells)
              + f"{means[name]:>11.3f}{multi_means[name]:>13.3f}")

    # Winner by the discriminating subset; the aggregate is the per-cluster health gate.
    ranked = sorted(multi_means, key=multi_means.get, reverse=True)
    winner, runner = ranked[0], ranked[1]
    margin = multi_means[winner] - multi_means[runner]
    per_cluster_ok = all(
        results[winner][str(c['cluster_id'])]["match_rate"] >= 0.70 for c, _ in pilots)
    verdict = "PASS" if (per_cluster_ok and margin >= 0.20) else "INCONCLUSIVE"
    print(f"\nwinner: {winner} (multi-axis mean {multi_means[winner]:.3f}, margin over "
          f"{runner} {margin:+.3f}; aggregate mean {means[winner]:.3f}) -> {verdict}")
    fl = [results[winner][str(c['cluster_id'])]["flagless_match_rate"] for c, _ in pilots]
    fl = [v for v in fl if v is not None]
    if fl:
        print(f"flagless-pieces-as-identity alignment under winner: "
              f"mean {sum(fl)/len(fl):.3f} (tests the missing-flag=identity assumption)")

    out = {
        "parquet": args.parquet,
        "epsilon_m": args.epsilon,
        "pretest": pre,
        "pilot_cluster_ids": [c["cluster_id"] for c, _ in pilots],
        "results": results,
        "means": {k: round(v, 4) for k, v in means.items()},
        "multiaxis_means": {k: round(v, 4) for k, v in multi_means.items()},
        "winner": winner,
        "margin_over_runner_up_multiaxis": round(margin, 4),
        "verdict": verdict,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

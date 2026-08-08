#!/usr/bin/env python3
"""Find the rooms, seats, gates, windows and courtyards inside each photographed
structure, so a camera can be planned *inside* the build rather than orbiting it.

The orbit planner needs only a bounding box. An interior planner needs to know
where the furniture is: which floor level is the main hall, which chair faces a
table, which wall opening is a window and which is the front gate. All of that
is in the world save — the StewardView DuckDB cache stores every ZDO with its
prefab name and position — it has just never been pulled out per structure.

Names, not categories. The viewer's own category census calls a hearth INTERIOR
and a chair FURNITURE-ish depending on its classification file; this scan
matches on prefab_name directly (the cache resolves 99.6% of rows using the
same committed prefab dump this repo carries), so a chair is a chair no matter
how the viewer filed it.

Cluster identity is frozen. out/clusters.json is the gallery's join key —
cluster ids come from union-find ordering and a re-scan can renumber them — so
this scan NEVER re-clusters. Features are assigned to the existing clusters by
padded bounding-box containment (nearest centre wins a tie), and the per-cluster
piece recount doubles as a drift report against the frozen scan.

No rotation. The cache does not store ZDO orientation, so a chair's facing is
unknowable here. The planner compensates by aiming at nearby features (the
table, the fire, the window) instead of down the chair's axis — which is the
better photograph anyway.

Outputs out/features.json (gitignored — real coordinates) for plan_interiors.py.

Usage:
  python scan_features.py [--db PATH] [--clusters out/clusters.json]
                          [--prefab-dump ../component-packets/samples/prefab-dump.json]
                          [--top 80] [--cluster-ids 439,71,407] [--pad 8]
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

import duckdb

DEFAULT_DB = r"C:\work\ComfyStewardView\viewer\target\ComfyEra16.duckdb"

# ---------------------------------------------------------------------------
# Feature vocabulary. One place, data-driven; weights say "prefer this one when
# choosing a subject" (a throne shot beats a bench shot, a 4x2 window gathers
# more light than a 1x1). Pattern sets (floors/roofs/walls/doors) are expanded
# against the committed prefab dump at startup so drift in the dump is visible.
# ---------------------------------------------------------------------------
SEATS = {
    "piece_throne01": 3, "piece_throne02": 3,
    "piece_blackmarble_throne": 3, "piece_bone_throne": 3,
    "piece_chair": 2, "piece_chair02": 2, "piece_chair03": 2,
    "piece_bench01": 1, "piece_blackmarble_bench": 1,
    "piece_blackwood_bench": 1, "piece_blackwood_bench01": 1,
    "piece_logbench01": 1,
}
TABLES = {"piece_table", "piece_table_oak", "piece_table_round", "piece_blackmarble_table"}
BEDS = {"bed", "piece_bed02", "goblin_bed", "ashwood_bed"}
GATES = {"wood_gate", "darkwood_gate", "flametal_gate"}
# wood_wall_half deliberately excluded in v1: it reads as a parapet far more
# often than as a window sill.
WINDOWS = {
    "wood_window": 1,
    "crystal_wall_1x1": 1,
    "Piece_grausten_window_2x2": 4,
    "Piece_grausten_window_4x2": 8,
}
FIRES_EXACT = {"hearth", "fire_pit", "bonfire", "piece_walltorch"}
FIRES_PREFIX = ("piece_brazier", "piece_groundtorch")


def expand_pattern_sets(dump_path):
    """Concrete name sets for the pattern-defined kinds, from the prefab dump.

    Only names the dump marks piece:true are considered, which keeps creature
    and effect prefabs with 'wall' in their names out of the wall set.
    """
    with open(dump_path, encoding="utf-8") as fh:
        dump = json.load(fh)
    piece_names = [p["name"] for p in dump["prefabs"] if p.get("piece")]

    fixed = set(SEATS) | TABLES | BEDS | GATES | set(WINDOWS) | FIRES_EXACT
    doors, roofs, floors, walls = set(), set(), set(), set()
    for name in piece_names:
        if name in fixed or name.startswith(FIRES_PREFIX):
            continue
        low = name.lower()
        if "_door" in low:
            doors.add(name)
        elif "roof" in low:            # before walls: wood_wall_roof is cover
            roofs.add(name)
        elif "_floor" in low:
            floors.add(name)
        elif "wall" in low:
            walls.add(name)
    return doors, roofs, floors, walls


def feature_rows(fixed_and_expanded):
    """(name, kind, weight) rows for the temp lookup table."""
    doors, roofs, floors, walls = fixed_and_expanded
    rows = []
    rows += [(n, "seat", w) for n, w in SEATS.items()]
    rows += [(n, "table", 1) for n in TABLES]
    rows += [(n, "bed", 1) for n in BEDS]
    rows += [(n, "gate", 1) for n in GATES]
    rows += [(n, "window", w) for n, w in WINDOWS.items()]
    rows += [(n, "fire", 1) for n in FIRES_EXACT]
    rows += [(n, "door", 1) for n in doors]
    rows += [(n, "roof", 1) for n in roofs]
    rows += [(n, "floor", 1) for n in floors]
    rows += [(n, "wall", 1) for n in walls]
    return rows


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=DEFAULT_DB, help="ComfyStewardView DuckDB cache")
    p.add_argument("--clusters", default=os.path.join(here, "out", "clusters.json"))
    p.add_argument("--prefab-dump",
                   default=os.path.normpath(os.path.join(
                       here, "..", "component-packets", "samples", "prefab-dump.json")))
    p.add_argument("--out", default=os.path.join(here, "out", "features.json"))
    p.add_argument("--top", type=int, default=80,
                   help="scan the top N clusters by score (0 = all; default 80)")
    p.add_argument("--cluster-ids", default="",
                   help="comma-separated cluster ids to include regardless of --top")
    p.add_argument("--region", default="in-world", choices=["all", "in-world", "outland"])
    p.add_argument("--pad", type=float, default=8.0,
                   help="metres of x/z slack around each frozen bounding box (default 8)")
    p.add_argument("--y-pad", type=float, default=4.0)
    return p.parse_args()


def pick_targets(doc, args):
    clusters = [c for c in doc["clusters"]
                if args.region == "all" or c["region"] == args.region]
    clusters.sort(key=lambda c: -c["score"])
    want = {int(s) for s in args.cluster_ids.split(",") if s.strip()}
    targets = clusters[: args.top] if args.top else list(clusters)
    have = {c["cluster_id"] for c in targets}
    by_id = {c["cluster_id"]: c for c in doc["clusters"]}
    for cid in sorted(want - have):
        if cid not in by_id:
            sys.exit(f"--cluster-ids {cid} not present in {len(by_id)} known clusters")
        targets.append(by_id[cid])
    return targets


# ---------------------------------------------------------------------------
# Geometry digests
# ---------------------------------------------------------------------------

def floor_bands(floors, min_keep):
    """Group floor pieces into horizontal bands — one band per storey, roughly.

    y is quantised to 0.5 m bins; occupied bins within 1.0 m of each other merge
    into one band, which absorbs the half-metre offsets of mixed slab pivots.
    Tiny bands (a lone balcony plank) are dropped: a camera needs a room.
    """
    if not floors:
        return []
    bins = defaultdict(list)
    for x, y, z in floors:
        bins[round(y * 2.0) / 2.0].append((x, y, z))
    bands, current = [], []
    for level in sorted(bins):
        if current and level - current[-1][0] > 1.0:
            bands.append(current)
            current = []
        current.append((level, bins[level]))
    if current:
        bands.append(current)

    out = []
    for group in bands:
        pts = [p for _lvl, members in group for p in members]
        if len(pts) < min_keep:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        zs = [p[2] for p in pts]
        out.append({
            "y": round(sum(ys) / len(ys), 2),
            "count": len(pts),
            "min_x": round(min(xs), 1), "max_x": round(max(xs), 1),
            "min_z": round(min(zs), 1), "max_z": round(max(zs), 1),
            "cx": round(sum(xs) / len(xs), 1),
            "cz": round(sum(zs) / len(zs), 1),
        })
    return out


def roof_grid(roofs, floors, bands, cluster, cell=2.0):
    """Which 2 m cells of the footprint have something overhead.

    Cover is a roof piece, or a floor piece sitting well above the lowest band
    (an upper storey is a ceiling to whoever stands under it). Open cells are
    courtyard candidates for the planner.
    """
    min_x, min_z = cluster["min_x"], cluster["min_z"]
    nx = max(1, int(math.ceil((cluster["max_x"] - min_x) / cell)))
    nz = max(1, int(math.ceil((cluster["max_z"] - min_z) / cell)))
    ground_y = bands[0]["y"] if bands else cluster["min_y"]
    covered = set()
    for x, _y, z in roofs:
        covered.add((int((x - min_x) // cell), int((z - min_z) // cell)))
    for x, y, z in floors:
        if y > ground_y + 2.0:
            covered.add((int((x - min_x) // cell), int((z - min_z) // cell)))
    covered = [[ix, iz] for ix, iz in sorted(covered)
               if 0 <= ix < nx and 0 <= iz < nz]
    return {"origin": [round(min_x, 1), round(min_z, 1)], "cell": cell,
            "nx": nx, "nz": nz, "covered": covered}


def thin(points, xz_res=1.0, y_res=2.0):
    """One representative point per (1 m x, 1 m z, 2 m y) cell — enough spatial
    truth for line-of-sight sampling and enclosure tests at a fraction of the
    bytes."""
    seen = {}
    for x, y, z in points:
        key = (round(x / xz_res), round(z / xz_res), round(y / y_res))
        if key not in seen:
            seen[key] = [round(x, 1), round(y, 1), round(z, 1)]
    return list(seen.values())


def main():
    args = parse_args()
    if not os.path.exists(args.db):
        sys.exit(f"DuckDB cache not found: {args.db} — rebuild it with the "
                 "StewardView viewer (--build-cache --batch-only)")
    if not os.path.exists(args.clusters):
        sys.exit(f"no clusters at {args.clusters} — the frozen cluster ids are "
                 "the gallery's join key; this scan never regenerates them")

    with open(args.clusters, encoding="utf-8") as fh:
        doc = json.load(fh)
    targets = pick_targets(doc, args)
    print(f"scanning features for {len(targets)} cluster(s)")

    expanded = expand_pattern_sets(args.prefab_dump)
    doors, roofs_set, floors_set, walls_set = expanded
    print(f"  vocabulary: {len(SEATS)} seats, {len(TABLES)} tables, {len(GATES)} gates, "
          f"{len(WINDOWS)} windows, {len(doors)} doors, {len(roofs_set)} roofs, "
          f"{len(floors_set)} floors, {len(walls_set)} walls (patterns expanded "
          f"against the prefab dump)")

    con = duckdb.connect(args.db, read_only=True)
    snap = con.execute(
        "SELECT source_path, parsed_at FROM world_snapshot LIMIT 1").fetchone()

    con.execute("CREATE OR REPLACE TEMP TABLE feature_name "
                "(name VARCHAR, kind VARCHAR, w INTEGER)")
    con.executemany("INSERT INTO feature_name VALUES (?, ?, ?)",
                    feature_rows(expanded))

    con.execute("CREATE OR REPLACE TEMP TABLE cluster_box "
                "(cid BIGINT, minx DOUBLE, maxx DOUBLE, miny DOUBLE, maxy DOUBLE, "
                "minz DOUBLE, maxz DOUBLE)")
    con.executemany(
        "INSERT INTO cluster_box VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(c["cluster_id"],
          c["min_x"] - args.pad, c["max_x"] + args.pad,
          c["min_y"] - args.y_pad, c["max_y"] + args.y_pad,
          c["min_z"] - args.pad, c["max_z"] + args.pad) for c in targets])

    print("  pulling classified pieces inside the frozen boxes ...", flush=True)
    rows = con.execute(
        """
        SELECT b.cid, f.kind, z.prefab_name, f.w, z.x, z.y, z.z
        FROM zdo z
        JOIN feature_name f ON f.name = z.prefab_name
        JOIN cluster_box b
          ON z.x BETWEEN b.minx AND b.maxx
         AND z.z BETWEEN b.minz AND b.maxz
         AND z.y BETWEEN b.miny AND b.maxy
        """).fetchall()
    print(f"  {len(rows):,} feature piece(s) matched")

    counts = {cid: (n_all, n_unres) for cid, n_all, n_unres in con.execute(
        """
        SELECT b.cid, count(*),
               count(*) FILTER (WHERE z.prefab_name LIKE 'hash:%')
        FROM zdo z
        JOIN cluster_box b
          ON z.x BETWEEN b.minx AND b.maxx
         AND z.z BETWEEN b.minz AND b.maxz
         AND z.y BETWEEN b.miny AND b.maxy
        WHERE z.category = 'BUILDING'
        GROUP BY b.cid
        """).fetchall()}

    total, unresolved = con.execute(
        "SELECT count(*), count(*) FILTER (WHERE prefab_name LIKE 'hash:%') "
        "FROM zdo WHERE category='BUILDING'").fetchone()

    # A padded box can claim a neighbour's edge pieces; the nearest centre keeps
    # each piece with the structure it belongs to.
    centers = {c["cluster_id"]: (c["center_x"], c["center_z"]) for c in targets}
    best = {}
    for cid, kind, name, w, x, y, z in rows:
        key = (kind, name, round(x, 2), round(y, 2), round(z, 2))
        cx, cz = centers[cid]
        d2 = (x - cx) ** 2 + (z - cz) ** 2
        if key not in best or d2 < best[key][0]:
            best[key] = (d2, cid)
    per_cluster = defaultdict(lambda: defaultdict(list))
    for (kind, name, x, y, z), (_d2, cid) in best.items():
        per_cluster[cid][kind].append((name, x, y, z))

    features = {}
    print()
    print(f"  {'cid':>5} {'drift':>7} {'seats':>5} {'tables':>6} {'gates':>5} "
          f"{'windows':>7} {'fires':>5} {'doors':>5} {'bands':>5} {'open%':>5}")
    for c in sorted(targets, key=lambda c: c.get("rank") or 0):
        cid = c["cluster_id"]
        kinds = per_cluster.get(cid, {})
        floors = [(x, y, z) for _n, x, y, z in kinds.get("floor", [])]
        walls = [(x, y, z) for _n, x, y, z in kinds.get("wall", [])]
        roofs = [(x, y, z) for _n, x, y, z in kinds.get("roof", [])]
        bands = floor_bands(floors, min_keep=max(8, int(0.02 * len(floors))))
        grid = roof_grid(roofs, floors, bands, c)

        def named(kind, weights=None):
            out = []
            for name, x, y, z in kinds.get(kind, []):
                rec = {"name": name, "x": round(x, 1), "y": round(y, 2), "z": round(z, 1)}
                if weights:
                    rec["w"] = weights.get(name, 1)
                out.append(rec)
            return out

        n_now, n_unres = counts.get(cid, (0, 0))
        drift = (n_now - c["pieces"]) / c["pieces"] * 100 if c["pieces"] else 0.0
        entry = {
            "label": None,          # planner joins cluster-names.json itself
            "rank": c.get("rank"),
            "pieces_frozen": c["pieces"],
            "pieces_in_box": n_now,
            "drift_pct": round(drift, 1),
            "unresolved_rows": n_unres,
            "seats": named("seat", SEATS),
            "tables": named("table"),
            "beds": named("bed"),
            "gates": named("gate"),
            "doors": named("door"),
            "windows": named("window", WINDOWS),
            "fires": named("fire"),
            "floor_bands": bands,
            "roof_grid": grid,
            "walls": thin(walls),
            "floors_thin": thin(floors),
        }
        features[str(cid)] = entry

        open_cells = grid["nx"] * grid["nz"] - len(grid["covered"])
        open_pct = 100.0 * open_cells / max(grid["nx"] * grid["nz"], 1)
        flag = "  DRIFT" if abs(drift) > 15 else ""
        print(f"  {cid:>5} {drift:>+6.1f}% {len(entry['seats']):>5} "
              f"{len(entry['tables']):>6} {len(entry['gates']):>5} "
              f"{len(entry['windows']):>7} {len(entry['fires']):>5} "
              f"{len(entry['doors']):>5} {len(bands):>5} {open_pct:>4.0f}%{flag}")

    out_doc = {
        "generated_from": "scan_features.py",
        "world": os.path.basename(snap[0]) if snap else None,
        "snapshot_parsed_at": str(snap[1]) if snap else None,
        "clusters_parsed_at": doc.get("parsed_at"),
        "building_rows": total,
        "building_rows_unresolved": unresolved,
        "resolved_pct": round(100.0 * (total - unresolved) / max(total, 1), 2),
        "pad_m": args.pad,
        "count": len(features),
        "clusters": features,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out_doc, fh, separators=(",", ":"))
    os.replace(tmp, args.out)

    print()
    print(f"  prefab resolution: {total - unresolved:,}/{total:,} building rows "
          f"({out_doc['resolved_pct']}%) named by the dump dictionary")
    print(f"  wrote {args.out}")


if __name__ == "__main__":
    main()

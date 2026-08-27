#!/usr/bin/env python3
"""Build the piece-geometry lexicon: per-prefab box extents, pivot offset estimate,
snap points and family, joined against what Era 17 actually placed.

The committed prefab dump (Mono.Cecil over assembly_valheim.dll) carries two fields
no code has ever read: meshBoundsApprox (AABB extents, 1,915 prefabs) and snapPoints
(build-connection points in local pivot space, 209 prefabs). Position + rotation +
extents is an oriented-box massing model; snap points are the connectivity graph and
the rotation-decode oracle (snapped pieces' snap points must coincide in world space).

Vocabulary discipline, learned three times in this project: the lexicon is keyed to
the prefabs THIS world placed (counts from the cache), never to the dump alone. The
dump only supplies geometry for names the world already voted for.

Pivot problem: a ZDO position is the piece PIVOT, and the dump gives extents with no
pivot-to-center offset. Estimate priority:
  1. snap-centroid  — snap points sit on the piece boundary in pivot space, so their
     centroid approximates the box center (exact for the classic 2x2 wall);
  2. family default — walls/poles/furniture raised by half height, floors/roofs at 0.
Both are recorded with center_source so verify_rotation.py / render_compare.py can
calibrate them instead of trusting them.

Outputs out/era17/arch/piece-geometry.json (gitignored — derived artifact).

Usage:
  python extract_geometry_lexicon.py [--db PATH] [--world-id ComfyEra17]
                                     [--snapshot-id N] [--prefab-dump PATH] [--out PATH]
"""
import argparse
import json
import os
import statistics
import sys

import duckdb

from scan_clusters import select_snapshot, table_columns
from scan_features import SEATS, TABLES, BEDS, GATES, WINDOWS, LIGHTS

DEFAULT_DB = r"E:\omen\steward-era17\out\world-cache.duckdb"
DEFAULT_DUMP = r"C:\work\ComfyStewardView\viewer\src\main\resources\prefab-dump.json"

# Categories that reach the reconstruction (mirrors BuildingGeometryExporter.wants()).
ARCH_CATEGORIES = ("BUILDING", "ITEM_STAND", "CONTAINER", "PORTAL", "BED", "SIGN", "BALLISTA")

# Cache-category families for the piece kinds that classified out of BUILDING before
# the building branch ever saw them. Name patterns below only run inside BUILDING.
CATEGORY_FAMILY = {
    "PORTAL": "portal", "CONTAINER": "container", "BED": "bed",
    "SIGN": "sign", "ITEM_STAND": "item_stand", "BALLISTA": "ballista",
}

# Snap-extent vs meshBounds disagreement threshold (fraction of the larger value).
DISAGREE_FRAC = 0.30
# Snap extents below this are degenerate on that axis (all snaps coplanar) — no signal.
DEGENERATE_M = 0.1

# meshBoundsApprox is unreliable wherever a prefab scales a unit mesh: the dump reads
# sharedMesh bounds without the transform, so blackmarble_2x2x2 (snaps at all eight
# +-1 corners — a true 2x2x2) reports ~[1,1,1], and wood_floor/wood_beam/wood_door
# carry a literal [1,1,1] placeholder. Snap points ARE the connection span in pivot
# space, so on snap-bearing axes they win; bounds are used only when they agree with
# the snaps, and a degenerate axis with distrusted bounds falls back to a family
# thickness (a wall is ~0.35 m deep, a floor ~0.1 m thick).
FAMILY_THICKNESS = {"floor": 0.1, "roof": 0.15, "door": 0.15, "gate": 0.2,
                    "window": 0.35, "wall": 0.35, "beam": 0.2, "pole": 0.2,
                    "fence": 0.2, "sign": 0.1}


def resolve_extents(bounds, snaps, family):
    """(extents, source_tag, disagree) from mesh bounds + snap span."""
    if not snaps:
        if bounds:
            return [round(v, 4) for v in bounds], "mesh", False
        return None, "family_median", False
    se = snap_extent(snaps)
    nondeg = [i for i in range(3) if se[i] > DEGENERATE_M]
    if not nondeg:
        if bounds:
            return [round(v, 4) for v in bounds], "mesh", False
        return None, "family_median", False
    bounds_ok = bounds is not None and all(
        abs(se[i] - bounds[i]) <= DISAGREE_FRAC * max(bounds[i], se[i]) for i in nondeg)
    ext = []
    for i in range(3):
        if se[i] > DEGENERATE_M:
            ext.append(max(se[i], bounds[i]) if bounds_ok else se[i])
        elif bounds_ok:
            ext.append(bounds[i])
        else:
            ext.append(FAMILY_THICKNESS.get(family, 0.2))
    tag = "snap+mesh" if bounds_ok else "snap"
    return [round(v, 4) for v in ext], tag, (bounds is not None and not bounds_ok)


def classify_family(name, category):
    """One family per prefab. Fixed vocabularies first (a window is not a wall),
    then cache category, then name patterns in scan_features order — door before
    roof before floor before wall, roof before wall because wood_wall_roof is cover."""
    if name in SEATS:
        return "seat"
    if name in TABLES:
        return "table"
    if name in BEDS:
        return "bed"
    if name in GATES:
        return "gate"
    if name in WINDOWS:
        return "window"
    if name in LIGHTS:
        return "light"
    fam = CATEGORY_FAMILY.get(category)
    if fam:
        return fam
    low = name.lower()
    if "_door" in low:
        return "door"
    if "gate" in low:
        return "gate"
    if "roof" in low:
        return "roof"
    if "stair" in low or "ladder" in low or "steepstair" in low:
        return "stair"
    if "_floor" in low or low.endswith("floor"):
        return "floor"
    if "window" in low:
        return "window"
    if "wall" in low:
        return "wall"
    if "beam" in low:
        return "beam"
    if "pole" in low:
        return "pole"
    if "fence" in low:
        return "fence"
    return "misc"


# Families whose pivot sits at the bottom face: box center is half a height up.
RAISED_FAMILIES = {
    "wall", "door", "gate", "window", "pole", "beam", "fence", "seat", "table",
    "bed", "light", "container", "portal", "sign", "item_stand", "ballista",
    "stair", "misc",
}


def default_center_offset(family, extents):
    if family in RAISED_FAMILIES:
        return [0.0, round(extents[1] / 2.0, 4), 0.0]
    # floor / roof: pivot at the surface plane
    return [0.0, 0.0, 0.0]


def snap_centroid(snaps):
    n = float(len(snaps))
    return [round(sum(p[i] for p in snaps) / n, 4) for i in range(3)]


def snap_extent(snaps):
    return [round(max(p[i] for p in snaps) - min(p[i] for p in snaps), 4) for i in range(3)]


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=DEFAULT_DB, help="ComfyStewardView DuckDB cache")
    p.add_argument("--world-id", default="ComfyEra17",
                   help="pick the newest snapshot of this world id (multi-era caches)")
    p.add_argument("--snapshot-id", type=int, default=None)
    p.add_argument("--prefab-dump", default=DEFAULT_DUMP)
    p.add_argument("--out", default=os.path.join(here, "out", "era17", "arch",
                                                 "piece-geometry.json"))
    return p.parse_args()


def main():
    args = parse_args()

    with open(args.prefab_dump, encoding="utf-8") as fh:
        dump = json.load(fh)
    by_name = {p["name"]: p for p in dump["prefabs"]}
    print(f"dump: {len(by_name):,} prefabs, schema {dump.get('schema')}, "
          f"game {dump.get('gameVersion')}", flush=True)

    print(f"opening {args.db} (read-only)", flush=True)
    con = duckdb.connect(args.db, read_only=True)
    try:
        snap = select_snapshot(con, args.world_id, args.snapshot_id)
    except ValueError as exc:
        sys.exit(str(exc))
    snapshot_id, source_path, parsed_at, world_id, world_name = snap
    zdo_columns = table_columns(con, "zdo")
    if snapshot_id is not None and "snapshot_id" in zdo_columns:
        con.execute(f"CREATE TEMP VIEW selected_zdo AS "
                    f"SELECT * FROM zdo WHERE snapshot_id = {int(snapshot_id)}")
    else:
        con.execute("CREATE TEMP VIEW selected_zdo AS SELECT * FROM zdo")
    print(f"  snapshot {snapshot_id}: {world_name or world_id}", flush=True)

    placeholders = ", ".join("?" for _ in ARCH_CATEGORIES)
    vocab = con.execute(
        f"SELECT prefab_name, first(category), count(*) FROM selected_zdo "
        f"WHERE category IN ({placeholders}) "
        f"AND prefab_name IS NOT NULL AND prefab_name NOT LIKE 'hash:%' "
        f"GROUP BY prefab_name ORDER BY count(*) DESC",
        list(ARCH_CATEGORIES)).fetchall()
    total_placed = sum(r[2] for r in vocab)
    print(f"  vocabulary: {len(vocab):,} distinct prefabs, "
          f"{total_placed:,} placed pieces", flush=True)
    con.close()

    entries, flagged = [], []
    for name, category, count in vocab:
        d = by_name.get(name, {})
        bounds = d.get("meshBoundsApprox")
        snaps = d.get("snapPoints") or []
        family = classify_family(name, category)
        extents, source, disagree = resolve_extents(bounds, snaps, family)
        entry = {
            "name": name,
            "hash": d.get("hash"),
            "family": family,
            "category": category,
            "count_era17": count,
            "snap_points": snaps,
            "extents": extents,
            "source": source,
        }
        if snaps:
            entry["center_offset"] = snap_centroid(snaps)
            entry["center_source"] = "snap_centroid"
            entry["snap_extent"] = snap_extent(snaps)
        else:
            entry["center_offset"] = None    # needs extents; filled below
            entry["center_source"] = "family_default"
        if disagree:
            entry["bounds_disagree"] = True
            flagged.append(name)
        entries.append(entry)

    # Family medians from entries with real geometry, then fill the gaps.
    REAL_SOURCES = ("mesh", "snap+mesh", "snap")
    fam_extents = {}
    for e in entries:
        if e["source"] in REAL_SOURCES:
            fam_extents.setdefault(e["family"], []).append(e["extents"])
    fam_median = {
        fam: [round(statistics.median(v[i] for v in vals), 4) for i in range(3)]
        for fam, vals in fam_extents.items()
    }
    for e in entries:
        if e["extents"] is None:
            med = fam_median.get(e["family"])
            if med:
                e["extents"] = med
            else:
                e["extents"] = [1.0, 1.0, 1.0]
                e["source"] = "cube"
        if e["center_offset"] is None:
            e["center_offset"] = default_center_offset(e["family"], e["extents"])

    covered = [e for e in entries if e["source"] in REAL_SOURCES]
    with_snaps = [e for e in entries if e["snap_points"]]
    weighted_real = sum(e["count_era17"] for e in covered)
    weighted_snap = sum(e["count_era17"] for e in with_snaps)
    coverage = {
        "distinct_prefabs": len(entries),
        "distinct_with_real_geometry": len(covered),
        "distinct_with_snap_points": len(with_snaps),
        "placed_total": total_placed,
        "placed_with_real_geometry": weighted_real,
        "placed_with_real_geometry_pct": round(100.0 * weighted_real / total_placed, 2),
        "placed_with_snap_points": weighted_snap,
        "placed_with_snap_points_pct": round(100.0 * weighted_snap / total_placed, 2),
        "bounds_disagree_flagged": len(flagged),
    }

    out = {
        "generated_from": {"dump": args.prefab_dump, "db": args.db,
                           "snapshot_id": snapshot_id, "world_id": world_id,
                           "parsed_at": parsed_at},
        "dump_schema": dump.get("schema"),
        "game_version": dump.get("gameVersion"),
        "coverage": coverage,
        "family_median_extents": fam_median,
        "pieces": entries,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)

    print(f"\ncoverage: real geometry {coverage['distinct_with_real_geometry']}/{coverage['distinct_prefabs']} "
          f"prefabs = {coverage['placed_with_real_geometry_pct']}% of placed pieces; "
          f"snap points {coverage['distinct_with_snap_points']} prefabs = "
          f"{coverage['placed_with_snap_points_pct']}% of placed pieces", flush=True)
    if flagged:
        print(f"bounds distrusted, snap extents used ({len(flagged)} prefabs): "
              f"{', '.join(flagged[:12])}{' ...' if len(flagged) > 12 else ''}")

    fam_counts = {}
    for e in entries:
        fam_counts[e["family"]] = fam_counts.get(e["family"], 0) + e["count_era17"]
    print("families by placed count: " + ", ".join(
        f"{k}={v:,}" for k, v in sorted(fam_counts.items(), key=lambda kv: -kv[1])))

    uncovered = [e for e in entries if e["source"] not in REAL_SOURCES][:20]
    if uncovered:
        print("\ntop uncovered prefabs (fallback boxes):")
        for e in uncovered:
            print(f"  {e['name']:<44} {e['family']:<10} {e['count_era17']:>9,}  {e['source']}")

    print("\nspot checks (known in-game sizes):")
    for probe in ("woodwall", "wood_floor", "wood_roof_45", "wood_door", "wood_beam",
                  "stone_wall_2x1", "blackmarble_2x2x2"):
        e = next((x for x in entries if x["name"] == probe), None)
        if e:
            print(f"  {probe:<14} extents={e['extents']} center={e['center_offset']} "
                  f"({e['center_source']}, snaps={len(e['snap_points'])})")
        else:
            print(f"  {probe:<14} not placed in this world")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()

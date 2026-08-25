#!/usr/bin/env python3
"""Find the high ground of each build, and how lit it is after dark.

Two questions this answers, both of which a night pass needs and nothing in the
pipeline could answer before:

  where do you STAND?   Every camera in this project so far has been outside the
                        build looking down at it. To photograph the sky from a
                        roof you need a flat piece of that roof, its height, and
                        how far the drop is in each direction -- because the
                        distance to the parapet is what decides how far the
                        camera can tilt up before the roofline leaves the frame.

  how LIT is it?        A night frame pays off in proportion to the lights the
                        builder placed. Measured across 268 builds, no structural
                        attribute predicts photo quality -- height r = -0.189, the
                        ranking score itself r = -0.136. Light count is not one of
                        those attributes; it is a statement about what is in the
                        photograph rather than about the building, which is why it
                        is worth targeting on.

Reads the same DuckDB cache and the same frozen clusters.json as everything else,
and borrows the audited light vocabulary from scan_features.py rather than keeping
a second copy of it.

Usage:
  python scan_rooftops.py --db E:\\omen\\steward-era17\\out\\world-cache.duckdb
      --world-id ComfyEra17 --clusters out/era17/clusters.json
      --out out/era17/rooftops.json --top 40
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

import duckdb

from scan_clusters import select_snapshot
from scan_features import LIGHTS

DEFAULT_DB = r"C:\work\ComfyStewardView\viewer\target\ComfyEra16.duckdb"

# A 2 m grid is the coarsest bin that still resolves a Valheim floor tile, and
# the finest that does not shatter a terrace into single planks.
CELL = 2.0
# Flatness: a 6x6 m block whose column tops sit within this of each other. A 45
# degree roof climbs 2 m per cell, so it fails on the first comparison; a
# terrace, a tower top and a walled courtyard all pass.
FLAT_TOLERANCE_M = 1.0
# A neighbour column this far below the platform is a drop you can see over --
# which is what puts a near layer against the frame border, the thing
# depth_layers.py calls edge_frame and rewards.
DROP_M = 1.5
# A ZDO's position is the piece's PIVOT, not the top of its mesh. A 2 m wall
# whose pivot sits at 67 reaches 69, and a column-top model that reads 67 puts
# the camera's eye inside masonry and calls it sky. Measured on cluster 182:
# grausten pillar arches pivoting 1.35 m BELOW the lens are what filled the frame.
PIECE_TOP_M = 2.0
# The skyline cannot be one ray. The frame is 97 degrees wide, and a single ray
# through a pillared hall threads the gaps between columns and reports open sky
# from inside a tower -- which is exactly what happened on the first run. Guard
# the central fan, where the moon and the sky band live, and tolerate the edges:
# a wall at the frame border is a near layer, a wall up the middle is a wall.
SKYLINE_FAN_DEG = 15.0
SKYLINE_FAN_STEP_DEG = 5.0


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--clusters", default=os.path.join(here, "out", "clusters.json"))
    p.add_argument("--out", default=os.path.join(here, "out", "rooftops.json"))
    p.add_argument("--world-id", default=None,
                   help="pick the newest snapshot of this world id (multi-era caches)")
    p.add_argument("--snapshot-id", type=int, default=None)
    p.add_argument("--region", default="in-world", choices=["all", "in-world", "outland"])
    p.add_argument("--top", type=int, default=40,
                   help="how many builds to find a stance on, in light order (0 = all)")
    p.add_argument("--min-lights", type=int, default=1,
                   help="skip builds with fewer weighted lights than this")
    p.add_argument("--cluster-ids", default="",
                   help="comma-separated ids to include regardless of --top")
    p.add_argument("--max-height-m", type=float, default=300.0,
                   help="same guard plan_shots.py carries: union-find chains a sky "
                        "platform to the ground through a vertical column and calls "
                        "the result one structure. The tallest real build is 177.9 m")
    p.add_argument("--exclude-sky", action="store_true", default=True,
                   help="drop clusters marked sky=true; they have no terrain, no "
                        "treetops and no horizon, which is three of the four bands "
                        "this composition is built from")
    p.add_argument("--include-sky", dest="exclude_sky", action="store_false")
    p.add_argument("--h-eye", type=float, default=1.65,
                   help="lens height above the roof, for the skyline angles "
                        "(measured: the mod places the player and the lens ends "
                        "up 1.65 m above that point)")
    p.add_argument("--platforms", type=int, default=5,
                   help="how many candidate stances to emit per build. The "
                        "highest flat block is not always the one with sky over "
                        "it, so the planner needs a choice rather than a verdict")
    p.add_argument("--pad", type=float, default=4.0,
                   help="metres of x/z slack around each frozen bounding box")
    return p.parse_args()


def light_census(con, clusters, pad):
    """Weighted light count per cluster.

    Same box-then-nearest-centre assignment scan_features.py uses, for the same
    reason: a padded box claims a neighbour's edge pieces, and the nearest centre
    puts each piece back with the structure it belongs to.
    """
    con.execute("CREATE OR REPLACE TEMP TABLE light_name (name VARCHAR, w INTEGER)")
    con.executemany("INSERT INTO light_name VALUES (?, ?)", list(LIGHTS.items()))
    con.execute("CREATE OR REPLACE TEMP TABLE cluster_box "
                "(cid BIGINT, minx DOUBLE, maxx DOUBLE, miny DOUBLE, maxy DOUBLE, "
                "minz DOUBLE, maxz DOUBLE)")
    con.executemany(
        "INSERT INTO cluster_box VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(c["cluster_id"], c["min_x"] - pad, c["max_x"] + pad,
          c["min_y"] - pad, c["max_y"] + pad,
          c["min_z"] - pad, c["max_z"] + pad) for c in clusters])

    rows = con.execute(
        """
        SELECT b.cid, l.w, z.x, z.z
        FROM selected_zdo z
        JOIN light_name l ON l.name = z.prefab_name
        JOIN cluster_box b
          ON z.x BETWEEN b.minx AND b.maxx
         AND z.z BETWEEN b.minz AND b.maxz
         AND z.y BETWEEN b.miny AND b.maxy
        WHERE z.category = 'BUILDING'
        """).fetchall()

    centers = {c["cluster_id"]: (c["center_x"], c["center_z"]) for c in clusters}
    best = {}
    for cid, w, x, z in rows:
        key = (round(x, 2), round(z, 2), w)
        cx, cz = centers[cid]
        d2 = (x - cx) ** 2 + (z - cz) ** 2
        if key not in best or d2 < best[key][0]:
            best[key] = (d2, cid, w)
    lit = defaultdict(int)
    n = defaultdict(int)
    for _d2, cid, w in best.values():
        lit[cid] += w
        n[cid] += 1
    return lit, n


def column_tops(pieces):
    """Highest piece in each 2 m x 2 m column. An empty column is open air."""
    tops = {}
    for x, y, z in pieces:
        key = (math.floor(x / CELL), math.floor(z / CELL))
        if key not in tops or y > tops[key]:
            tops[key] = y
    return tops


def platforms(tops):
    """Every 3x3 block of columns flat enough to stand on, best first.

    Flatness is the whole test. A sloped roof cannot pass it and a terrace
    cannot fail it, which beats guessing at a floor-prefab vocabulary -- the
    seats and the lights were both written from the crafting UI against a world
    built from the prefab table, and both were wrong.

    Note there is no "is the sky above it" test here, because a column's top IS
    its highest piece: nothing can be over it in its own column. What CAN be over
    it is the rest of the build, one column across -- see skyline(), which is the
    test that actually matters and the one the first capture run lacked.
    """
    out = []
    for (ix, iz), _top in tops.items():
        block = [tops.get((ix + dx, iz + dz))
                 for dx in (-1, 0, 1) for dz in (-1, 0, 1)]
        if any(v is None for v in block):
            continue                      # a hole in the floor is not a platform
        if max(block) - min(block) > FLAT_TOLERANCE_M:
            continue
        level = sum(block) / 9.0
        # Edge exposure: the ring outside the block that is a drop or open air.
        # This is the parapet the camera stands behind, and the reason the frame
        # gets a near layer along its border instead of a flat middle.
        ring = [(ix + dx, iz + dz)
                for dx in range(-2, 3) for dz in range(-2, 3)
                if max(abs(dx), abs(dz)) == 2]
        exposure = sum(1 for k in ring
                       if tops.get(k) is None or tops[k] < level - DROP_M)
        out.append({"ix": ix, "iz": iz, "level": level,
                    "exposure": exposure, "ring": len(ring)})
    # Height first -- the ask is the high ground -- then how much of the world
    # you can see over the edge from it.
    out.sort(key=lambda p: (-p["level"], -p["exposure"]))
    return out


def skyline(tops, x0, z0, eye_y, bearing_deg, limit_m=80.0):
    """The highest thing in the way, as an angle above the lens, along a bearing.

    This is the guard the first run needed and did not have. All 16 frames came
    back clearance="planned" and occluded=false, and not one of them had sky in
    it: the camera was looking straight into the build's own lattice or into a
    tree canopy. The mod's raycast could not see either -- IsOccluded masks
    "terrain", "static_solid" and "Default" and player pieces are on the "piece"
    layer, so for a camera standing inside its own build the check is blind.

    So do it here, from the world's own positions, the same way plan_interiors.py
    settled the identical problem indoors: guard the plan, not the pixels. Uses
    EVERY category rather than just BUILDING, because the thing that filled the
    top of the best frame in that run was a tree.

    Terrain is still not covered -- Valheim generates it from the seed and no
    heightmap exists offline -- but terrain IS in the mod's raycast mask, so the
    two checks cover each other.
    """
    worst = 0.0
    offset = -SKYLINE_FAN_DEG
    while offset <= SKYLINE_FAN_DEG + 1e-9:
        az = math.radians(bearing_deg + offset)
        sx, sz = math.sin(az), math.cos(az)
        d = CELL
        while d <= limit_m:
            key = (math.floor((x0 + sx * d) / CELL),
                   math.floor((z0 + sz * d) / CELL))
            top = tops.get(key)
            if top is not None:
                angle = math.degrees(math.atan2(top + PIECE_TOP_M - eye_y, d))
                if angle > worst:
                    worst = angle
            d += CELL
        offset += SKYLINE_FAN_STEP_DEG
    return round(worst, 1)


def reach(tops, ix, iz, level, bearing_deg, limit_m=40.0):
    """How far the roof runs before it drops away, along one bearing.

    This is R in the framing constraint: the camera can only tilt up to
    fov/2 - atan(h_eye / R) before the roofline leaves the bottom of the frame,
    so a wide terrace buys tilt and a narrow tower top does not.
    """
    az = math.radians(bearing_deg)
    sx, sz = math.sin(az), math.cos(az)
    x0, z0 = (ix + 0.5) * CELL, (iz + 0.5) * CELL
    d = CELL
    while d <= limit_m:
        k = (math.floor((x0 + sx * d) / CELL), math.floor((z0 + sz * d) / CELL))
        t = tops.get(k)
        if t is None or t < level - DROP_M:
            return round(d, 1)
        d += CELL
    return limit_m


def main():
    args = parse_args()
    if not os.path.exists(args.clusters):
        sys.exit(f"no clusters at {args.clusters} - run scan_clusters.py first")
    with open(args.clusters, encoding="utf-8") as fh:
        doc = json.load(fh)
    clusters = doc["clusters"]

    con = duckdb.connect(args.db, read_only=True)
    snap = select_snapshot(con, world_id=args.world_id, snapshot_id=args.snapshot_id)
    snapshot_id = snap[0] if snap else None
    if snapshot_id is not None:
        con.execute("CREATE OR REPLACE TEMP VIEW selected_zdo AS "
                    f"SELECT * FROM zdo WHERE snapshot_id = {int(snapshot_id)}")
        print(f"  snapshot {snapshot_id}: {snap[3] or snap[1]}")
    else:
        con.execute("CREATE OR REPLACE TEMP VIEW selected_zdo AS SELECT * FROM zdo")

    print(f"  {len(LIGHTS)} light prefabs in the vocabulary; counting them "
          f"across {len(clusters):,} structures ...", flush=True)
    lit, n_lights = light_census(con, clusters, args.pad)
    dark = sum(1 for c in clusters if lit.get(c["cluster_id"], 0) == 0)
    print(f"  {sum(n_lights.values()):,} placed light(s) assigned; "
          f"{dark:,} structure(s) have none")

    want = {int(i) for i in args.cluster_ids.split(",") if i.strip()}
    pool = [c for c in clusters
            if (args.region == "all" or c["region"] == args.region)
            and c["size_y"] <= args.max_height_m
            and not (args.exclude_sky and c.get("sky"))]
    pool.sort(key=lambda c: (-lit.get(c["cluster_id"], 0), -c["score"]))
    targets = [c for c in pool if lit.get(c["cluster_id"], 0) >= args.min_lights]
    if args.top:
        targets = targets[: args.top]
    by_id = {c["cluster_id"]: c for c in clusters}
    have = {c["cluster_id"] for c in targets}
    for cid in sorted(want - have):
        if cid not in by_id:
            sys.exit(f"--cluster-ids {cid} is not a known cluster")
        targets.append(by_id[cid])

    print(f"  finding a stance on {len(targets)} build(s) ...", flush=True)
    con.execute("DELETE FROM cluster_box")
    con.executemany(
        "INSERT INTO cluster_box VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(c["cluster_id"], c["min_x"] - args.pad, c["max_x"] + args.pad,
          c["min_y"] - args.pad, c["max_y"] + args.pad,
          c["min_z"] - args.pad, c["max_z"] + args.pad) for c in targets])
    rows = con.execute(
        """
        SELECT b.cid, z.category, z.x, z.y, z.z
        FROM selected_zdo z
        JOIN cluster_box b
          ON z.x BETWEEN b.minx AND b.maxx
         AND z.z BETWEEN b.minz AND b.maxz
         AND z.y BETWEEN b.miny AND b.maxy
        """).fetchall()
    per_cluster = defaultdict(list)
    per_cluster_all = defaultdict(list)
    for cid, category, x, y, z in rows:
        per_cluster_all[cid].append((x, y, z))
        if category == "BUILDING":
            per_cluster[cid].append((x, y, z))

    bearings = list(range(0, 360, 30))
    out, skipped = [], []
    print()
    print(f"  {'cid':>6} {'lights':>6} {'pieces':>7} {'stance_y':>8} "
          f"{'above':>6} {'exposure':>9} {'reach_m':>9} {'plat':>3} {'sky_deg':>7}")
    for c in sorted(targets, key=lambda c: -lit.get(c["cluster_id"], 0)):
        cid = c["cluster_id"]
        pieces = per_cluster.get(cid, [])
        if not pieces:
            skipped.append((cid, "no pieces in the frozen box"))
            continue
        tops = column_tops(pieces)
        tops_all = column_tops(per_cluster_all.get(cid, pieces))
        found = platforms(tops)
        if not found:
            # Not a failure to report quietly: a build with no flat 6x6 m
            # anywhere is a roof you cannot stand on, and the honest answer is
            # that this composition has nowhere to put the camera.
            skipped.append((cid, "no flat 6x6 m platform"))
            continue

        # Several candidates, not one verdict. The highest flat block is not
        # reliably the one with sky over it: on the first run the tallest block
        # of the most-lit build in the world sat under its own lattice, and all
        # four frames are a photograph of that lattice.
        candidates = []
        for block in found:
            if any(max(abs(block["ix"] - c["ix"]), abs(block["iz"] - c["iz"])) < 3
                   for c in candidates):
                continue                  # same spot on the roof, one shot
            candidates.append(block)
            if len(candidates) >= args.platforms:
                break

        detail = []
        for block in candidates:
            bx = (block["ix"] + 0.5) * CELL
            bz = (block["iz"] + 0.5) * CELL
            by = block["level"]
            eye = by + args.h_eye
            detail.append({
                "stance": {"x": round(bx, 1), "y": round(by, 2), "z": round(bz, 1)},
                "above_base_m": round(by - c["min_y"], 1),
                "exposure": block["exposure"], "exposure_of": block["ring"],
                "reach_m": {b: reach(tops, block["ix"], block["iz"], by, b)
                            for b in bearings},
                "skyline_deg": {b: skyline(tops_all, bx, bz, eye, b)
                                for b in bearings},
            })

        best = candidates[0]
        sx = (best["ix"] + 0.5) * CELL
        sz = (best["iz"] + 0.5) * CELL
        sy = best["level"]
        reaches = detail[0]["reach_m"]
        open_sky = min(min(d["skyline_deg"].values()) for d in detail)
        out.append({
            "platforms_detail": detail,
            "clearest_skyline_deg": open_sky,
            "cluster_id": cid,
            "lights": lit.get(cid, 0),
            "light_pieces": n_lights.get(cid, 0),
            "pieces": c["pieces"],
            "height_m": c["size_y"],
            "region": c["region"],
            "stance": {"x": round(sx, 1), "y": round(sy, 2), "z": round(sz, 1)},
            "above_base_m": round(sy - c["min_y"], 1),
            "exposure": best["exposure"],
            "exposure_of": best["ring"],
            "platforms": len(found),
            "reach_m": reaches,
        })
        print(f"  {cid:>6} {lit.get(cid, 0):>6} {c['pieces']:>7,} {sy:>8.1f} "
              f"{sy - c['min_y']:>6.1f} {best['exposure']:>4}/{best['ring']:<4} "
              f"{min(reaches.values()):>4.0f}-{max(reaches.values()):<4.0f} "
              f"{len(detail):>3} {open_sky:>7.1f}")

    doc_out = {
        "generated_from": "scan_rooftops.py",
        "world": doc.get("world"),
        "snapshot_id": snapshot_id,
        "settings": {"cell_m": CELL, "flat_tolerance_m": FLAT_TOLERANCE_M,
                     "drop_m": DROP_M, "bearings": bearings,
                     "h_eye_m": args.h_eye, "platforms_per_build": args.platforms,
                     "min_lights": args.min_lights, "pad_m": args.pad},
        "light_census": {str(c["cluster_id"]): lit.get(c["cluster_id"], 0)
                         for c in clusters if lit.get(c["cluster_id"], 0)},
        "structures": out,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc_out, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, args.out)

    print()
    print(f"  {len(out)} stance(s) -> {args.out}")
    if skipped:
        print(f"  {len(skipped)} build(s) have no stance:")
        for cid, why in skipped[:10]:
            print(f"    cluster {cid}: {why}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Where a build can actually see OUT: canopy gaps, and how far down them you see.

The night lane aims the camera AT the moon. That composes the moon as the subject
and it is the least interesting thing a night frame can do -- the moon is a light,
and a light is worth more raking across a scene from off-axis than sitting in the
middle of it. What earns the frame is a CHANNEL: a bearing where the canopy opens
and the eye runs a long way out, ideally over water, with a band of stars across
the top sixth to third.

This measures the channel. It does not choose the shot; plan_channel.py does.

Per (stance, bearing):

  canopy_deg     The angle of the highest tall tree above the LENS. This is the
                 measurement that matters and the one a gap distance cannot give:
                 from cluster 26's 68 m roof a 20 m fir standing on 30 m ground
                 tops out at 50 m and is not in the picture at all, while the same
                 fir closes the view completely from a 12 m roof. Negative means
                 the canopy is below the lens and the bearing is open.

                 A ZDO carries the tree's PIVOT -- the trunk base, which is real
                 ground elevation at that point -- and nothing about the crown.
                 So one constant, --tree-height, is assumed and everything else is
                 measured. That isolation is deliberate: a wrong H moves every
                 canopy angle in the same direction by the same amount, so a
                 single frame with a visible treeline recalibrates it, and no
                 conclusion here rests on having guessed a prefab's size right.
                 Guessing prefab properties from names is how the seat and light
                 vocabularies were both wrong in this world.

  first_tree_m   Distance to the first tall tree inside a corridor of --corridor
                 half-width, and trees_near the count of them within --near. A
                 single trunk at 250 m is a subject; forty of them is a wall.

  sea_at_m       Distance along the bearing to the first ocean pixel, and
  sea_run_m      how much open water the ray then crosses. This is the depth the
                 coastal shots are built around: ground construction in the near
                 field, then terrain, then water running out to the horizon.

The ocean comes from the world's own minimap cache, NOT from the DuckDB analytics
cache. The colour lane recorded that "seaward direction is not derivable from the
DuckDB cache (no terrain); the cheap proxy is radially outward from world centre,
which is wrong on lakes, inlets and the inside of a bay". That is true of the
cache and false of the machine: Valheim writes <World>_mapTexCache next to the
save as a 2048x2048 PNG of biome colours, ocean included, and it costs nothing to
read.

The world-to-pixel mapping is solved, not assumed:

    col = x / 10 + 1024        row = z / 10 + 1024

10 m/px comes from the non-Ashlands disc measuring 1005 px in half-width against
an in-world build radius of 10,383 m, and from the disc being centred on column
1023.0 -- half a pixel off 2048/2, which a wrong scale does not produce. The row
direction (+z downward, i.e. no vertical flip) is fixed by a physical prior
rather than a convention: under it, pixels the map calls Mountain carry a mean
build min_y of 127.9 m against 64.8 m on ordinary land. Flipped, mountains come
out LOWEST, which terrain cannot do. Ocean pixels read 91.2 m because the builds
standing on them are this world's floating forts and sky islands.

Usage:
  python scan_channels.py --rooftops out/era17/rooftops.json \
      --out out/era17/channels.json
"""
import argparse
import json
import math
import os
import sys

# Tall enough that the canopy closes overhead. Small firs, bushes, stumps and
# logs are deliberately absent: they block a walking eye and not a rooftop one.
# Chosen by placement count off the cache, then read back for obvious mistakes --
# a pattern sweep for "tree" would also collect FirTree_small_dead and stubbe.
TALL_TREES = (
    "Pinetree_01", "FirTree", "Beech1", "Birch1", "Birch2", "Birch1_aut",
    "Birch2_aut", "SwampTree1", "SwampTree2", "Oak1", "FirTree_oldLog",
    "AshlandsTree1", "AshlandsTree2", "AshlandsTree3", "YggdrasilRoot",
)

OCEAN_RGB = (0x33, 0x33, 0x33)
PIXEL_SIZE_M = 10.0


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rooftops", default=os.path.join(here, "out", "era17", "rooftops.json"))
    p.add_argument("--db", default=r"E:\omen\steward-era17\out\world-cache.duckdb")
    p.add_argument("--world", default="ComfyEra17")
    p.add_argument("--worlds-dir", default=os.path.expandvars(
        r"%USERPROFILE%\AppData\LocalLow\IronGate\Valheim\worlds_local"))
    p.add_argument("--out", default=os.path.join(here, "out", "era17", "channels.json"))
    p.add_argument("--bearings", type=int, default=24,
                   help="how many bearings to sweep (24 = every 15 degrees)")
    p.add_argument("--corridor", type=float, default=20.0,
                   help="half-width of the sight corridor in metres")
    p.add_argument("--near", type=float, default=300.0,
                   help="a tree inside this counts toward trees_near")
    p.add_argument("--reach", type=float, default=1500.0,
                   help="how far to look for the first tree")
    p.add_argument("--sea-reach", type=float, default=4000.0,
                   help="how far to look for open water")
    p.add_argument("--tree-height", type=float, default=20.0,
                   help="assumed canopy height above a tall tree's ZDO pivot. THE ONE "
                        "guessed number here, and it is isolated on purpose: the pivot "
                        "elevation is real data, so a wrong H shifts every canopy angle "
                        "the same way and a single measured frame recalibrates it")
    p.add_argument("--cluster-ids", default="")
    return p.parse_args()


def load_ocean(worlds_dir, world):
    """The biome raster, as a boolean ocean mask."""
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        sys.exit("scan_channels needs numpy and Pillow")
    path = os.path.join(worlds_dir, f"{world}_mapTexCache")
    if not os.path.exists(path):
        sys.exit(f"no minimap cache at {path}.\n"
                 f"       Valheim writes it beside the save; open the world once if it is missing.")
    arr = np.asarray(Image.open(path).convert("RGB"))
    return np.all(arr == OCEAN_RGB, axis=2), arr.shape[0]


def sea_along(ocean, n, x0, z0, bearing_deg, reach_m, step_m=10.0):
    """(distance to first open water, metres of water crossed) along a bearing."""
    br = math.radians(bearing_deg)
    dx, dz = math.sin(br), math.cos(br)
    half = n / 2.0
    first, run, d = None, 0.0, 0.0
    while d < reach_m:
        col = int(x0 / PIXEL_SIZE_M + dx * d / PIXEL_SIZE_M + half)
        row = int(z0 / PIXEL_SIZE_M + dz * d / PIXEL_SIZE_M + half)
        if not (0 <= col < n and 0 <= row < n):
            break
        if ocean[row, col]:
            if first is None:
                first = d
            run += step_m
        d += step_m
    return first, run


def main():
    args = parse_args()
    try:
        import duckdb
        import numpy as np
    except ImportError:
        sys.exit("scan_channels needs duckdb and numpy")

    ocean, n = load_ocean(args.worlds_dir, args.world)
    print(f"  ocean mask {n}x{n} at {PIXEL_SIZE_M:g} m/px "
          f"({100.0 * ocean.mean():.1f}% water)")

    with open(args.rooftops, encoding="utf-8-sig") as fh:
        roof = json.load(fh)
    builds = roof["structures"]
    if args.cluster_ids:
        want = {int(c) for c in args.cluster_ids.split(",") if c.strip()}
        builds = [b for b in builds if b["cluster_id"] in want]
    print(f"  {len(builds)} build(s)")

    con = duckdb.connect(args.db, read_only=True)
    names = ",".join("'%s'" % t for t in TALL_TREES)
    step = 360.0 / args.bearings
    out = []

    for b in builds:
        st = b["stance"]
        x0, z0 = st["x"], st["z"]
        rows = con.execute(f"""
            SELECT x, y, z FROM zdo
            WHERE prefab_name IN ({names})
              AND x BETWEEN {x0 - args.reach} AND {x0 + args.reach}
              AND z BETWEEN {z0 - args.reach} AND {z0 + args.reach}
        """).fetchall()
        tx = np.array([r[0] for r in rows], dtype=float)
        ty = np.array([r[1] for r in rows], dtype=float)
        tz = np.array([r[2] for r in rows], dtype=float)
        # The lens rides 1.65 m above the stance the mod places the player on.
        eye_y = st["y"] + 1.65

        bearings = {}
        for i in range(args.bearings):
            bng = i * step
            br = math.radians(bng)
            dx, dz = math.sin(br), math.cos(br)
            if len(tx):
                along = (tx - x0) * dx + (tz - z0) * dz
                cross = np.abs(-(tx - x0) * dz + (tz - z0) * dx)
                # 5 m floor: a trunk closer than that is part of the build's own
                # planting, not the treeline that closes the view.
                inside = (along > 5.0) & (cross < args.corridor) & (along < args.reach)
                first = float(along[inside].min()) if inside.any() else None
                near = int((inside & (along < args.near)).sum())
                # A tree only closes the view if its CANOPY reaches above the lens.
                # From a 68 m roof a 20 m fir standing on 30 m ground tops out at
                # 50 m and is not in the picture at all, which is why a gap
                # distance alone says nothing about whether you can see out.
                if inside.any():
                    rise = ty[inside] + args.tree_height - eye_y
                    canopy = float(np.degrees(np.arctan2(rise, along[inside])).max())
                else:
                    canopy = None
            else:
                first, near, canopy = None, 0, None
            sea_at, sea_run = sea_along(ocean, n, x0, z0, bng, args.sea_reach)
            bearings[str(int(round(bng)))] = {
                "first_tree_m": None if first is None else round(first, 1),
                "trees_near": near,
                "sea_at_m": None if sea_at is None else round(sea_at, 1),
                "sea_run_m": round(sea_run, 1),
                "canopy_deg": None if canopy is None else round(canopy, 2),
            }

        out.append({
            "cluster_id": b["cluster_id"],
            "stance": st,
            "reach_m": b.get("reach_m"),
            "skyline_deg": b.get("skyline_deg"),
            "lights": b.get("lights"),
            "tall_trees_in_range": int(len(tx)),
            "bearings": bearings,
        })
        opens = [k for k, v in bearings.items()
                 if v["canopy_deg"] is None or v["canopy_deg"] <= 0.0]
        seas = [k for k, v in bearings.items() if v["sea_at_m"] is not None]
        print(f"    cluster {b['cluster_id']:>5}: {len(tx):>6} tall trees, "
              f"{len(opens)} bearing(s) with canopy below the lens, "
              f"{len(seas)} with water")

    doc = {
        "generated_from": "scan_channels.py",
        "world": args.world,
        "settings": {
            "bearings": args.bearings, "corridor_m": args.corridor,
            "near_m": args.near, "reach_m": args.reach,
            "sea_reach_m": args.sea_reach, "pixel_size_m": PIXEL_SIZE_M,
            "tree_height_m_ASSUMED": args.tree_height,
            "tall_trees": list(TALL_TREES),
        },
        "structures": out,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    print(f"  {args.out}")


if __name__ == "__main__":
    main()

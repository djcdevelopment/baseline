#!/usr/bin/env python3
"""Can the camera actually see the subject? One shared answer, from ZDOs.

Three partial probes existed and none of them answered this question:

  scan_channels.py    vectorised tree corridor, but a horizontal ray from a fixed
                      eye, no subject exclusion -- it asks "how closed is the view",
                      not "is this shot blocked"
  scan_rooftops.py    skyline fan over a 2 m column-top hash, build-local, returns a
                      max elevation angle rather than a verdict
  probe_facade_orbit  terrain ray clearance, duplicated verbatim in plan_roof_ends,
  + plan_roof_ends    ground-only and advisory

and plan_shots.py, which produces most of the corpus, has no visibility model at all.
The in-game probe cannot cover for it: Plugin.cs IsOccluded excludes the `piece`
layer on purpose, and on run 20260827-165844 it reported occluded=false for all 16
frames including the ones whose camera was standing inside a tree.

That run cost 6 of 13 examined frames to vegetation and boulders while the terrain
preflight reported 24-44 m of clearance, because terrain is the one thing that was
never the problem.

Occluders come from the DuckDB cache, not from building-geometry.parquet -- that
export filters to BUILDING plus architectural categories. Vegetation and rock are
category UNKNOWN (NATURE is empty in Era17): Rock_4 298k, cliff_mistlands2 186k,
Pinetree_01 117k, FirTree 66k.

Heights: the audited TALL_TREES vocabulary WINS over meshBoundsApprox, because the
dump reads sharedMesh bounds without the transform and so reports FirTree and
FirTree_small as the same 5.45 m when the real fir is 18 m. That is the same
unit-mesh scaling bug that made blackmarble_2x2x2 measure 1x1x1. Bounds are trusted
for rock, which does not scale a unit mesh.

Usage as a library:
    idx = OccluderIndex.from_cache(db, 107, bbox)
    verdict = ray_clearance(idx, terrain, cam, aim)

Or audit the vocabulary it would use:
    python sight.py --audit --db <cache> --snapshot-id 107
"""
import argparse
import json
import math
import os

import numpy as np

from scan_channels import TALL_TREES

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DUMP = r"C:\work\ComfyStewardView\viewer\src\main\resources\prefab-dump.json"
DEFAULT_DB = r"E:\omen\steward-era17\out\world-cache.duckdb"

# Measured on the 20260827-165844 receipts; earlier probes hardcoded 1.721 from the
# 1820 control. Receipts carry the real value per shot -- pass it when you have it.
LENS_OFFSET_M = 1.79

OCCLUDER_CATEGORIES = ("UNKNOWN", "NATURE")

# Not physical geometry. Each of these is placed in quantity and would otherwise be
# treated as something a camera cannot see through.
NON_OCCLUDER_SUBSTRINGS = (
    "_zonectrl", "vfx_", "sfx_", "spawner_", "mistarea", "mistvolume", "flies",
    "waterliquid", "locationproxy", "pickable_", "fireflies", "smoke", "_trigger",
    "musiclocation", "raise_", "particle", "_terraincompiler", "music_", "dg_",
)

# An occluder shorter than this cannot get between a lens and a building.
MIN_OCCLUDER_HEIGHT_M = 1.0
# Anything with no bounds and no vocabulary entry. Deliberately small: guessing big
# would refuse good shots, and unknown-prefab misses are logged rather than assumed.
DEFAULT_HEIGHT_M = 0.0
MIN_RADIUS_M = 0.35


def is_occluder_name(name):
    low = name.lower()
    return not any(s in low for s in NON_OCCLUDER_SUBSTRINGS)


# Vegetation is not reliably category UNKNOWN: 13,641 trees in Era17 are category
# BUILDING because players plant them, and one of those (a Pinetree_01 2.7 m from the
# camera) is in the corridor of a frame this probe has to catch. Match by name across
# every category rather than trusting the classifier.
VEGETATION_SUBSTRINGS = (
    "tree", "beech", "birch", "oak", "pine", "fir", "shoot", "bush", "shrub",
    "yggdrasil", "vines", "sapling",
)


def looks_like_vegetation(name):
    low = name.lower()
    if not is_occluder_name(name):
        return False
    if any(bad in low for bad in ("_log", "_stub", "stump", "decowall", "xmas")):
        return False        # felled, stumps, and a decorative WALL named tree
    return name in TALL_TREES or any(s in low for s in VEGETATION_SUBSTRINGS)


def occluder_height(name, bounds):
    """Audited vocabulary first for trees, mesh bounds otherwise.

    meshBoundsApprox is unreliable for vegetation in BOTH directions and cannot be
    repaired by taking a max. It reads sharedMesh bounds without the transform, so
    FirTree measures 5.45 m when the real fir is 18 m -- the unit-mesh bug that made
    blackmarble_2x2x2 report 1x1x1 -- while Oak1 and Beech1 come back at 25-30 m tall
    and ~36 m WIDE, which is a sway/LOD volume, not a tree. A max() rule fixes the
    first case and makes the second worse: it gave Oak1 a 17.9 m radius and refused
    1820_roofend2, a frame that plainly shows the building.

    The repair is to treat HEIGHT and RADIUS separately rather than picking one source
    for both -- the mistake that made this probe oscillate between 2/5 and 4/5:

      height  max(vocabulary, bounds). Conservative, and it has to be: a Beech1 whose
              pivot sits 26 m below a camera tops out at 56 m under the 14 m vocabulary
              (clear) and 72 m under its 30.5 m bounds (lens inside the canopy). The
              native-resolution frame of 0310_roofend1 shows leaves at the lens, so the
              taller reading is the true one and the vocabulary -- calibrated for canopy
              ANGLE from a rooftop, not for blocking -- understates it.
      radius  never from bounds, always derived from height below. Bounds widths are
              sway/LOD volumes: Oak1 reads 36 m across, and using that refused
              1820_roofend2, a frame that plainly shows the building.

    Rock keeps its bounds outright, which are trustworthy -- rock does not scale a unit
    mesh, and cliff_mistlands2 at 63 m tall and 23 m across is a real cliff.
    """
    vocab = TALL_TREES.get(name)
    mesh = float(bounds[1]) if bounds else None
    if vocab is not None and mesh is not None:
        return max(vocab, mesh), "max(vocabulary,meshBounds)"
    if vocab is not None:
        return vocab, "vocabulary"
    if mesh is not None:
        return mesh, "meshBounds"
    return DEFAULT_HEIGHT_M, "unknown"


# Canopy radius is derived from height, because no audited width vocabulary exists and
# the dump's widths are sway/LOD volumes (Oak1 comes back 36 m across). One ratio for
# every tree was still wrong in both directions: a conifer is a narrow spire and a
# broadleaf is a wide dome, and at 14-16 m tall that is the difference between a 3 m
# and an 8 m radius -- which is exactly the difference between catching the beech the
# camera was standing in on 0310 and refusing the oak that 1820_roofend2 sees past.
CONIFER_RADIUS_RATIO = 0.22
BROADLEAF_RADIUS_RATIO = 0.50
MAX_CANOPY_RADIUS_M = 9.0
CONIFER_SUBSTRINGS = ("pine", "fir", "spruce")


def occluder_radius(name, bounds, height, is_veg):
    if is_veg:
        low = name.lower()
        ratio = (CONIFER_RADIUS_RATIO if any(s in low for s in CONIFER_SUBSTRINGS)
                 else BROADLEAF_RADIUS_RATIO)
        return max(MIN_RADIUS_M, min(height * ratio, MAX_CANOPY_RADIUS_M))
    if not bounds:
        return MIN_RADIUS_M
    return max(MIN_RADIUS_M, max(float(bounds[0]), float(bounds[2])) / 2.0)


def load_bounds(dump_path=DEFAULT_DUMP):
    with open(dump_path, encoding="utf-8") as fh:
        dump = json.load(fh)
    return {p["name"]: p.get("meshBoundsApprox") for p in dump["prefabs"]}


# A tree is not a solid cylinder. Its canopy occupies the upper part of its height at
# full width; below that there is only a trunk, and a camera set low for an
# architectural elevation routinely sees straight under it. Modelling trees as solid
# from the ground up made this probe refuse 1820_roofend2 -- a frame that plainly shows
# the building -- because an Oak1 stood 14 m away with its canopy well above the ray.
CANOPY_BASE_FRAC = 0.35
TRUNK_RADIUS_M = 0.6


class OccluderIndex:
    """Vegetation and rock near a corridor: rock is solid, trees are trunk + canopy."""

    def __init__(self, x, y, z, h, r, names, is_veg, unresolved):
        self.x, self.y, self.z, self.h, self.r = x, y, z, h, r
        self.names = names
        self.is_veg = is_veg
        self.unresolved = unresolved      # {prefab: count} with no height source

    def __len__(self):
        return len(self.x)

    def radius_at(self, height):
        """Effective horizontal radius where the sight ray passes, per occluder."""
        canopy_base = self.y + self.h * CANOPY_BASE_FRAC
        trunk = np.minimum(self.r, TRUNK_RADIUS_M)
        wide = (~self.is_veg) | (height >= canopy_base)
        return np.where(wide, self.r, trunk)

    @classmethod
    def from_parquet(cls, path, bbox, dump_path=DEFAULT_DUMP, pad=40.0):
        """Occluders from a direct world export rather than the analytics cache.

        The cache describes a snapshot; a capture host's world drifts away from it.
        Reading the same file the camera flew through is the only way to ask whether a
        frame was blocked by something that is actually there.
        """
        import duckdb
        min_x, max_x, min_z, max_z = bbox
        con = duckdb.connect()
        rows = con.execute("""
            SELECT prefab_name, category, x, y, z FROM read_parquet(?)
            WHERE prefab_name IS NOT NULL
              AND x BETWEEN ? AND ? AND z BETWEEN ? AND ?
            """, [path.replace("\\", "/"), min_x - pad, max_x + pad,
                  min_z - pad, max_z + pad]).fetchall()
        con.close()
        return cls._build(rows, dump_path)

    @classmethod
    def from_cache(cls, db, snapshot_id, bbox, dump_path=DEFAULT_DUMP, pad=40.0):
        import duckdb
        min_x, max_x, min_z, max_z = bbox
        bounds = load_bounds(dump_path)
        con = duckdb.connect(db, read_only=True)
        # Every category, not just UNKNOWN/NATURE -- planted trees classify as BUILDING.
        # Non-vegetation BUILDING rows are dropped below so the subject's own walls do
        # not blockade every shot of it.
        rows = con.execute("""
            SELECT prefab_name, category, x, y, z FROM zdo
            WHERE snapshot_id = ? AND prefab_name IS NOT NULL
              AND x BETWEEN ? AND ? AND z BETWEEN ? AND ?
            """, [snapshot_id, min_x - pad, max_x + pad,
                  min_z - pad, max_z + pad]).fetchall()
        con.close()
        return cls._build(rows, dump_path)

    @classmethod
    def _build(cls, rows, dump_path):
        bounds = load_bounds(dump_path)
        X, Y, Z, H, R, N, V = [], [], [], [], [], [], []
        unresolved = {}
        for name, category, x, y, z in rows:
            veg = looks_like_vegetation(name)
            if not (category in OCCLUDER_CATEGORIES or veg):
                continue
            if not is_occluder_name(name):
                continue
            b = bounds.get(name)
            h, src = occluder_height(name, b)
            if src == "unknown":
                unresolved[name] = unresolved.get(name, 0) + 1
            if h < MIN_OCCLUDER_HEIGHT_M:
                continue
            X.append(x); Y.append(y); Z.append(z)
            H.append(h); R.append(occluder_radius(name, b, h, veg)); N.append(name); V.append(veg)
        return cls(np.asarray(X, float), np.asarray(Y, float), np.asarray(Z, float),
                   np.asarray(H, float), np.asarray(R, float), N,
                   np.asarray(V, bool), unresolved)


def terrain_clearance(terrain, lens, aim, samples=41, subject_frac=0.8):
    """Minimum height of the sight ray above ground over its first 80%.

    The last fifth is supposed to intersect the subject and is not an obstruction --
    the convention probe_facade_orbit and plan_roof_ends already share, and the same
    one the in-game raycast uses at 0.85.
    """
    worst = math.inf
    for i in range(samples):
        t = (i / max(samples - 1, 1)) * subject_frac
        x = lens[0] + (aim[0] - lens[0]) * t
        z = lens[2] + (aim[2] - lens[2]) * t
        ray_y = lens[1] + (aim[1] - lens[1]) * t
        worst = min(worst, ray_y - terrain.ground_y_detail(x, z)[0])
    return worst


def ray_clearance(index, terrain, cam, aim, lens_offset=LENS_OFFSET_M,
                  corridor_extra_m=0.75, subject_frac=0.8, min_terrain_m=2.0,
                  vertical_margin_m=0.0):
    """Is the line from this camera to this aim point actually open?

    cam/aim are (x, y, z); cam is the placement, the lens rides lens_offset above it.
    Returns a verdict dict; `clear` False always carries a `reason`.
    """
    lens = (cam[0], cam[1] + lens_offset, cam[2])
    dx, dz = aim[0] - lens[0], aim[2] - lens[2]
    total = math.hypot(dx, dz)
    out = {"clear": True, "reason": None, "lens_y": lens[1],
           "distance_m": round(total, 2), "occluders_considered": len(index),
           "min_terrain_clearance_m": None, "first_blocker": None, "blockers": 0}
    if total < 1e-6:
        out.update(clear=False, reason="degenerate ray")
        return out

    if terrain is not None:
        tc = terrain_clearance(terrain, lens, aim, subject_frac=subject_frac)
        out["min_terrain_clearance_m"] = round(tc, 2)
        if tc < min_terrain_m:
            out.update(clear=False, reason="terrain within %.2f m of the sight line" % tc)

    if len(index) == 0:
        return out

    ux, uz = dx / total, dz / total
    px, pz = index.x - lens[0], index.z - lens[2]
    along = px * ux + pz * uz
    cross = np.abs(-px * uz + pz * ux)
    top = index.y + index.h

    # The camera standing inside a canopy, a trunk or a rock: horizontally within the
    # body at the lens height, and vertically inside its column. This is the failure
    # that ruined 310, 372 and 916, and an `along > 5 m` floor of the kind
    # scan_channels uses would hide it entirely.
    r_lens = index.radius_at(np.full(len(index), lens[1]))
    inside_cyl = (np.abs(along) <= r_lens) & (cross <= r_lens) & \
                 (lens[1] >= index.y) & (lens[1] <= top)
    if inside_cyl.any():
        j = int(np.argmax(inside_cyl))
        out.update(clear=False,
                   reason="camera is inside %s" % index.names[j],
                   first_blocker={"prefab": index.names[j], "along_m": round(float(along[j]), 2),
                                  "over_ray_m": round(float(top[j] - lens[1]), 2)},
                   blockers=int(inside_cyl.sum()))
        return out

    ray_y = lens[1] + (aim[1] - lens[1]) * np.clip(along / total, 0.0, 1.0)
    # Width is evaluated where the ray actually passes, so a low elevation sees under
    # a canopy instead of being refused by it.
    r_ray = index.radius_at(ray_y)
    in_corridor = (along > 0.0) & (along < subject_frac * total) & \
                  (cross < r_ray + corridor_extra_m)
    blocked = in_corridor & (top > ray_y + vertical_margin_m) & (index.y < ray_y + index.h)
    n = int(blocked.sum())
    out["blockers"] = n
    if n:
        idx = np.where(blocked)[0]
        j = int(idx[np.argmin(along[idx])])
        out.update(clear=False,
                   reason="%s blocks the sight line at %.1f m" % (index.names[j], along[j]),
                   first_blocker={"prefab": index.names[j],
                                  "along_m": round(float(along[j]), 2),
                                  "over_ray_m": round(float(top[j] - ray_y[j]), 2)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audit", action="store_true",
                    help="print the occluder vocabulary this world would use")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--snapshot-id", type=int, default=107)
    ap.add_argument("--limit", type=int, default=30)
    args = ap.parse_args()
    if not args.audit:
        ap.error("nothing to do; pass --audit")

    import duckdb
    bounds = load_bounds()
    con = duckdb.connect(args.db, read_only=True)
    cats = ", ".join("'%s'" % c for c in OCCLUDER_CATEGORIES)
    rows = con.execute(f"""
        SELECT prefab_name, count(*) c FROM zdo
        WHERE snapshot_id = ? AND category IN ({cats}) AND prefab_name IS NOT NULL
        GROUP BY 1 ORDER BY c DESC LIMIT 400""", [args.snapshot_id]).fetchall()
    con.close()

    kept, dropped, unresolved = [], [], []
    for name, c in rows:
        if not is_occluder_name(name):
            dropped.append((name, c, "not physical"))
            continue
        b = bounds.get(name)
        h, src = occluder_height(name, b)
        if src == "unknown":
            unresolved.append((name, c))
        if h < MIN_OCCLUDER_HEIGHT_M:
            dropped.append((name, c, "%.2f m, too short" % h))
            continue
        kept.append((name, c, h, occluder_radius(name, b, h, looks_like_vegetation(name)), src))

    print("OCCLUDERS (%d prefabs, %d placements)" %
          (len(kept), sum(k[1] for k in kept)))
    print("%-34s %9s %7s %7s  %s" % ("prefab", "count", "height", "radius", "source"))
    for name, c, h, r, src in kept[:args.limit]:
        print("%-34s %9d %7.1f %7.2f  %s" % (name, c, h, r, src))
    print("\nDROPPED (%d prefabs, %d placements)" %
          (len(dropped), sum(d[1] for d in dropped)))
    for name, c, why in dropped[:args.limit]:
        print("  %-32s %9d  %s" % (name, c, why))
    if unresolved:
        print("\nNO HEIGHT SOURCE (%d prefabs, %d placements) -- these are invisible "
              "to the probe:" % (len(unresolved), sum(u[1] for u in unresolved)))
        for name, c in unresolved[:args.limit]:
            print("  %-32s %9d" % (name, c))


if __name__ == "__main__":
    main()

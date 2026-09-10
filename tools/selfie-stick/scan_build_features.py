#!/usr/bin/env python3
"""Say what each build IS, so the gallery can offer a filter and the planner a target.

The era-archive index ships kinds, regions, areas and flashes as hardcoded empty
lists (build_era_index.py:138-141) and perspective as the constant "orbit". The
viewer drops any facet with one value, so eras 7-14 render almost no chip row at
all -- not because the data is missing, but because nothing ever computed it.
Era 17, on the Gen-1 path, carries twelve kinds and four perspectives.

Everything needed is already in the zdo parquet, but it arrives in two different
ways, and conflating them silently returns zero:

  * **membership.parquet holds BUILDING rows and nothing else.** Measured on era11:
    3,008,433 rows, every one category='BUILDING'. So a build "owns" only its
    construction pieces. Counting beds or signs by joining membership to a category
    returns 0 for every build in the era -- the furniture is not a member of
    anything. What IS reachable this way, by prefab name, is whatever was placed as
    a construction piece: lights, seats, tables, workbenches, and the `portal`
    prefab.
  * **beds, signs, item stands, containers and `portal_wood` are separate ZDOs**
    (BED 2,516; SIGN 72,956; ITEM_STAND 61,693; PORTAL 11,189 in era11) and can only
    be attributed geometrically, by asking which build's box they stand inside.
    That is what scan_features.py means by "pulling classified pieces inside the
    frozen boxes". Those counts are reported under `contained`, because containment
    is a weaker claim than ownership: two builds whose boxes overlap both count the
    same bed.

Light sources need their own vocabulary either way: there is no LIGHT category, and
the lights that actually dominate a world are groundtorches and braziers, not the
campfire a hand-written vocabulary reaches for first. Measured on era11:
groundtorch_wood 18,483, groundtorch_mist 14,816, CastleKit/MountainKit braziers
~20,000. A vocabulary that misses those undercounts by two orders of magnitude.

The light count is the targeting signal for a twilight second frame: a base whose
builder placed real light sources has a night composition worth photographing, and
one that did not does not. See the daylight-leads note -- twilight earns its place
on builds that lit themselves, and never replaces the golden frame.

  python scan_build_features.py --root E:\\omen\\steward-multi-era --era era11 \\
      --out features-era11.json
"""
import argparse
import json
import math
import os
import sys

import duckdb

# Grounded in the era11 census, not guessed. Ordered so the comment above stays
# checkable: anything that emits light at night and is placed by a player.
LIGHT_PATTERNS = ("torch", "brazier", "candle", "fire_pit", "bonfire", "hearth",
                  "lantern", "sconce", "firepit", "fireplace")

# Placed as construction pieces, so they live in membership and are genuinely owned.
SEAT_PATTERNS = ("chair", "throne", "bench", "stool")
TABLE_PATTERNS = ("table",)
CRAFT_PATTERNS = ("workbench", "forge", "magetable", "artisan", "stonecutter",
                  "blackforge", "piece_cauldron", "smelter", "kiln", "windmill",
                  "spinningwheel")

# Attributed by containment, not ownership -- these are their own categories and
# belong to no build's membership.
CONTAINED_CATEGORIES = ("BED", "SIGN", "ITEM_STAND", "CONTAINER", "PORTAL")

# Vertical slack on the containment test. A sign hung under an eave or a bed on a
# floor whose pieces sit slightly above it should still count as inside.
CONTAIN_PAD_Y = 2.0

# A build is one thing only if its pieces touch. The archive clusters at 16 m
# cells, which chains neighbouring structures into a single "build" -- that is what
# makes a compound. Re-running the same union-find at a tighter cell splits the
# compound back into the masses a camera can actually frame one at a time.
SUBCLUSTER_CELL = 8.0
SUBCLUSTER_MIN_SHARE = 0.02


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", required=True)
    p.add_argument("--era", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--subclusters", action="store_true",
                   help="also decompose each build into shootable sub-masses. Needs "
                        "the point cloud, so it is slower and off by default")
    p.add_argument("--build-keys", default="",
                   help="comma-separated buildKeys to restrict to (default: every "
                        "build in the era)")
    p.add_argument("--min-pieces", type=int, default=200,
                   help="skip builds smaller than this (default 200). Era 11 holds "
                        "47,758 clustered builds and almost all of them are a "
                        "handful of pieces; a kind census over those says nothing, "
                        "and the containment join over them is most of the cost")
    return p.parse_args()


def load(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def artifacts(root, era):
    catalog = load(os.path.join(root, "catalog.json"))
    analysis = load(os.path.join(root, "analysis", "catalog.json"))
    era_row = next(e for e in catalog["eras"] if e["slug"] == era)
    ana_row = next(e for e in analysis["eras"] if e["slug"] == era)
    if ana_row["sourceKey"] != era_row["sourceKey"]:
        sys.exit(f"membership source mismatch for {era}")
    membership = os.path.join(root, ana_row["membership"]["path"]).replace("\\", "/")
    zdo = os.path.join(root, era_row["ingestion"]["artifacts"]["zdo"]["path"]).replace("\\", "/")
    for path in (membership, zdo):
        if not os.path.exists(path):
            sys.exit(f"missing artifact: {path}")
    return era_row, membership, zdo


def describe(f):
    """A readable name for a structure, since Valheim gives builds no names.

    Same ladder as build_valheim_index.describe(), which was tuned on era 17: lead
    with the most characterising trait, because a 66-portal hub reads as a hub first
    and a big build second. Kept in this order deliberately so a kind means the same
    thing on both the Gen-1 and Gen-2 paths.
    """
    if f["portals"] >= 30:
        return "major hub"
    if f["heightM"] >= 90:
        return "tower"
    if f["itemStands"] >= 200:
        return "museum"
    if f["signs"] >= 800:
        return "sign-covered"
    if f["portals"] >= 10:
        return "hub"
    if f["beds"] >= 10:
        return "settlement"
    if f["footprintM2"] >= 50000:
        return "sprawl"
    if f["heightM"] >= 60:
        return "tall hall"
    if f["builders"] >= 8:
        return "shared build"
    return "build"


def subclusters(points):
    """Split a build into the masses a camera can frame one at a time.

    Grid-snap to SUBCLUSTER_CELL and union-find touching cells, then keep components
    holding at least SUBCLUSTER_MIN_SHARE of the pieces. A single coherent longhouse
    comes back as one component; a settlement of six outbuildings comes back as six,
    and each one is a detail shot the orbit planner never offered.
    """
    cells = {}
    for i, (x, y, z) in enumerate(points):
        key = (int(math.floor(x / SUBCLUSTER_CELL)),
               int(math.floor(y / SUBCLUSTER_CELL)),
               int(math.floor(z / SUBCLUSTER_CELL)))
        cells.setdefault(key, []).append(i)

    parent = {k: k for k in cells}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for (cx, cy, cz) in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    other = (cx + dx, cy + dy, cz + dz)
                    if other in cells:
                        union((cx, cy, cz), other)

    groups = {}
    for key, members in cells.items():
        groups.setdefault(find(key), []).extend(members)

    total = float(len(points))
    out = []
    for members in groups.values():
        if len(members) / total < SUBCLUSTER_MIN_SHARE:
            continue
        pts = [points[i] for i in members]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        zs = [p[2] for p in pts]
        cx, cz = sum(xs) / len(pts), sum(zs) / len(pts)
        out.append({
            "pieces": len(pts),
            "share": round(len(pts) / total, 4),
            "centerX": round(cx, 1), "centerZ": round(cz, 1),
            "minY": round(min(ys), 1), "maxY": round(max(ys), 1),
            "sizeX": round(max(xs) - min(xs), 1),
            "sizeY": round(max(ys) - min(ys), 1),
            "sizeZ": round(max(zs) - min(zs), 1),
            "radiusM": round(max(math.hypot(p[0] - cx, p[2] - cz) for p in pts), 1),
        })
    out.sort(key=lambda g: -g["pieces"])
    return out


def main():
    args = parse_args()
    era_row, membership, zdo = artifacts(args.root, args.era)
    snapshot = era_row["snapshotId"]
    wanted = [k for k in args.build_keys.split(",") if k] if args.build_keys else None

    def name_filter(patterns):
        return " OR ".join(f"lower(z.prefab_name) LIKE '%{p}%'" for p in patterns)

    restrict = "AND m.build_key IN ?" if wanted else ""
    params = [snapshot] + ([wanted] if wanted else [])

    con = duckdb.connect(":memory:")
    con.execute("SET threads=2; SET memory_limit='2GB'")

    sys.stderr.write("aggregating owned pieces...\n")
    con.execute(f"""
        CREATE TABLE owned AS
        SELECT m.build_key,
               count(*) AS pieces,
               min(z.x) AS min_x, max(z.x) AS max_x,
               min(z.y) AS min_y, max(z.y) AS max_y,
               min(z.z) AS min_z, max(z.z) AS max_z,
               count(DISTINCT z.creator_id) FILTER (WHERE z.creator_id IS NOT NULL
                                                      AND z.creator_id <> 0) AS builders,
               count(*) FILTER (WHERE {name_filter(LIGHT_PATTERNS)}) AS lights,
               count(*) FILTER (WHERE {name_filter(SEAT_PATTERNS)}) AS seats,
               count(*) FILTER (WHERE {name_filter(TABLE_PATTERNS)}) AS tables,
               count(*) FILTER (WHERE {name_filter(CRAFT_PATTERNS)}) AS crafting,
               count(*) FILTER (WHERE lower(z.prefab_name) LIKE '%portal%') AS portals_owned
        FROM read_parquet('{membership}') m
        JOIN read_parquet('{zdo}') z USING (snapshot_id, zdo_index)
        WHERE m.snapshot_id = ? {restrict}
        GROUP BY m.build_key
        HAVING count(*) >= {args.min_pieces}""", params)

    kept = con.execute("SELECT count(*) FROM owned").fetchone()[0]
    sys.stderr.write(f"  {kept} builds at >= {args.min_pieces} pieces\n")

    # Containment, not ownership: these categories are members of nothing, so the
    # only available question is which build's box they stand inside. Boxes can
    # overlap, so an object may be counted by more than one build -- that is why
    # these live under their own key rather than being summed into the owned counts.
    sys.stderr.write("attributing contained furniture by bounding box...\n")
    cats = ", ".join(f"'{c}'" for c in CONTAINED_CATEGORIES)
    con.execute(f"""
        CREATE TABLE contained AS
        SELECT o.build_key,
               count(*) FILTER (WHERE z.category = 'BED') AS beds,
               count(*) FILTER (WHERE z.category = 'SIGN') AS signs,
               count(*) FILTER (WHERE z.category = 'ITEM_STAND') AS item_stands,
               count(*) FILTER (WHERE z.category = 'CONTAINER') AS containers,
               count(*) FILTER (WHERE z.category = 'PORTAL') AS portals
        FROM owned o
        JOIN read_parquet('{zdo}') z
          ON z.snapshot_id = {snapshot} AND z.category IN ({cats})
         AND z.x BETWEEN o.min_x AND o.max_x
         AND z.z BETWEEN o.min_z AND o.max_z
         AND z.y BETWEEN o.min_y - {CONTAIN_PAD_Y} AND o.max_y + {CONTAIN_PAD_Y}
        GROUP BY o.build_key""")

    rows = con.execute("""
        SELECT o.*, coalesce(c.beds,0), coalesce(c.signs,0), coalesce(c.item_stands,0),
               coalesce(c.containers,0), coalesce(c.portals,0)
        FROM owned o LEFT JOIN contained c USING (build_key)""").fetchall()

    features = {}
    for r in rows:
        (key, pieces, min_x, max_x, min_y, max_y, min_z, max_z, builders,
         lights, seats, tables, crafting, portals_owned,
         beds, signs, stands, containers, portals_contained) = r
        cx, cz = (min_x + max_x) / 2.0, (min_z + max_z) / 2.0
        f = {
            "pieces": int(pieces),
            "heightM": round(float(max_y - min_y), 1),
            "footprintM2": round(float((max_x - min_x) * (max_z - min_z)), 1),
            "builders": int(builders),
            "lights": int(lights), "seats": int(seats), "tables": int(tables),
            "crafting": int(crafting),
            # Lights per 1000 pieces. The raw count follows build size, so a big
            # hall always wins it; the density is what says somebody lit the place
            # on purpose -- which is what earns a build its twilight frame.
            "lightDensity": round(1000.0 * lights / max(1, pieces), 1),
            "contained": {"beds": int(beds), "signs": int(signs),
                          "itemStands": int(stands), "containers": int(containers),
                          "portals": int(portals_contained)},
            "region": "outland" if math.hypot(cx, cz) > 10500 else "in-world",
        }
        # describe() reads the era-17 ladder's names; portals count either way they
        # arrive, since a portal placed as a piece and one standing in the hall are
        # the same fact about the place.
        f["beds"] = f["contained"]["beds"]
        f["signs"] = f["contained"]["signs"]
        f["itemStands"] = f["contained"]["itemStands"]
        f["portals"] = int(portals_owned) + int(portals_contained)
        f["kind"] = describe(f)
        features[key] = f

    if args.subclusters:
        sys.stderr.write("decomposing builds into sub-masses...\n")
        cursor = con.execute(f"""
            SELECT m.build_key, z.x, z.y, z.z
            FROM read_parquet('{membership}') m
            JOIN owned o USING (build_key)
            JOIN read_parquet('{zdo}') z USING (snapshot_id, zdo_index)
            WHERE m.snapshot_id = ? {restrict}
            ORDER BY m.build_key""", params)
        import itertools
        while True:
            chunk = cursor.fetchmany(200000)
            if not chunk:
                break
            for key, group in itertools.groupby(chunk, key=lambda r: r[0]):
                pts = [(float(r[1]), float(r[2]), float(r[3])) for r in group]
                # groupby can split one build across fetch boundaries; accumulate.
                features[key].setdefault("_pts", []).extend(pts)
        for key, f in features.items():
            pts = f.pop("_pts", [])
            if pts:
                groups = subclusters(pts)
                f["subClusters"] = groups
                f["subClusterCount"] = len(groups)
    con.close()

    kinds = {}
    for f in features.values():
        kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
    doc = {
        "schema": "steward-build-features/v1",
        "era": args.era,
        "sourceKey": era_row["sourceKey"],
        "snapshotId": snapshot,
        "minPieces": args.min_pieces,
        "vocabularies": {"light": list(LIGHT_PATTERNS), "seat": list(SEAT_PATTERNS),
                         "table": list(TABLE_PATTERNS), "crafting": list(CRAFT_PATTERNS)},
        "containedCategories": list(CONTAINED_CATEGORIES),
        "counts": {"builds": len(features), "kinds": kinds},
        "builds": features,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    sys.stderr.write(f"wrote {args.out}: {len(features)} builds\n")
    for kind, n in sorted(kinds.items(), key=lambda kv: -kv[1]):
        sys.stderr.write(f"  {kind:<14}{n:>6}\n")


if __name__ == "__main__":
    main()

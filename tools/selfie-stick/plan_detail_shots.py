#!/usr/bin/env python3
"""Shoot the parts of a build the orbit planner is too far away to show.

frame_forecast measured the whole problem: framing to fit the bounding volume
holds frame FILL roughly constant across build size while detail scale collapses.
Median pixels-per-metre by build radius, over 3,300 era11/era14 shots:

    0-15 m   91.1        40-70 m   16.4
    15-25 m  35.3        70 m +     9.1
    25-40 m  22.9

corr(log distance, log px/m) = -1.000 -- the orbit planner is doing exactly what
it was built to do, and that is the problem. 35% of the corpus sits under 20 px/m,
where a one-metre plank is twenty pixels.

Reframing does not rescue this. Trimming the outliers to a 90th-percentile mass
moves a 70 m+ build from 9.1 to 10.7 px/m: still unreadable. A hundred-metre
longhouse and its shingles do not fit in one frame, and no framing rule makes them.
That is geometry, not a bug, and the answer is a second kind of shot.

So: solve the camera for a DETAIL SCALE instead of for an extent. Pick the distance
that puts --target-px-per-m on the subject, and accept that the frame shows part of
the build. Where a build decomposes into separate masses, shoot each one -- the
settlement that reads as a smudge at 180 m is six legible buildings up close.

The distance rule needs no new maths. camera_for already returns
min(ideal, max_distance), so passing the target distance as max_distance yields
exactly min(fit, target): a small mass is framed whole because fitting it already
beats the target, and a large one is framed partial but legible. It also sets
frames_whole_build correctly, so a partial frame is recorded as intended rather
than as a failure.

  python plan_detail_shots.py --root E:\\omen\\steward-multi-era --era era11 \\
      --campaign .../campaign.json --out-tsv detail-era11.tsv --out-json detail-era11.json
"""
import argparse
import itertools
import json
import math
import os
import sys

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from plan_shots import (FOV_V_DEG, camera_for, elevation_for,  # noqa: E402
                        orbit_azimuths, validate_tsv)
from scan_build_features import subclusters  # noqa: E402

TAN_V = math.tan(math.radians(FOV_V_DEG / 2.0))

HEADER = ("# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\ttime"
          "\taim_x\taim_y\taim_z\tlabel\tmode\tfires\tflash\n")

# campaign.py's own values, so a detail frame is lit and cleared like its orbits.
MARGIN = 1.2
CLEARANCE = 3
ENVIRONMENT = "Clear"
TIME_OF_DAY = 0.64

# Detail shots sit closer, so the steep look-down that keeps a whole compound in
# frame becomes a roof survey. Coming down to 28 degrees puts walls in the picture.
DETAIL_ELEVATION = 28.0


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", required=True)
    p.add_argument("--era", required=True)
    p.add_argument("--campaign", required=True,
                   help="campaign.json naming the builds and their cluster ids")
    p.add_argument("--out-tsv", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--target-px-per-m", type=float, default=40.0,
                   help="detail scale to solve for (default 40). Checked by eye "
                        "against era11: 38 px/m reads window mullions and roof "
                        "shingles, 9.8 px/m is a silhouette in haze")
    p.add_argument("--below-px-per-m", type=float, default=25.0,
                   help="only plan detail for builds whose orbit shots already sit "
                        "below this (default 25). Above it the wide frame is "
                        "already legible and a detail shot is a luxury")
    p.add_argument("--forecast", default="",
                   help="forecast-<era>.json. Without it every build is measured "
                        "from its own geometry instead of its shot record")
    p.add_argument("--max-per-build", type=int, default=4,
                   help="cap on detail frames per build, largest masses first")
    p.add_argument("--height", type=int, default=2160)
    p.add_argument("--limit", type=int, default=0)
    return p.parse_args()


def load(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def artifacts(root, era):
    catalog = load(os.path.join(root, "catalog.json"))
    analysis = load(os.path.join(root, "analysis", "catalog.json"))
    era_row = next(e for e in catalog["eras"] if e["slug"] == era)
    ana_row = next(e for e in analysis["eras"] if e["slug"] == era)
    membership = os.path.join(root, ana_row["membership"]["path"]).replace("\\", "/")
    zdo = os.path.join(root, era_row["ingestion"]["artifacts"]["zdo"]["path"]).replace("\\", "/")
    return era_row, membership, zdo


def distance_for_scale(px_per_m, height_px):
    """Camera distance that puts px_per_m on a subject at the aim plane."""
    return height_px / (2.0 * px_per_m * TAN_V)


def cluster_from_mass(mass, points):
    """A sub-mass in the shape camera_for expects, so the same solver applies."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return {"center_x": (min(xs) + max(xs)) / 2.0,
            "center_z": (min(zs) + max(zs)) / 2.0,
            "min_y": min(ys), "max_y": max(ys),
            "size_x": max(xs) - min(xs),
            "size_y": max(ys) - min(ys),
            "size_z": max(zs) - min(zs)}


def mass_points(mass, points):
    """Recover the points of one sub-mass by its own box, which is how it was cut."""
    half_x, half_z = mass["sizeX"] / 2.0 + 0.5, mass["sizeZ"] / 2.0 + 0.5
    return [p for p in points
            if abs(p[0] - mass["centerX"]) <= half_x
            and abs(p[2] - mass["centerZ"]) <= half_z
            and mass["minY"] - 0.5 <= p[1] <= mass["maxY"] + 0.5]


def read_points(root, era, build_keys):
    era_row, membership, zdo = artifacts(root, era)
    points = {}
    with duckdb.connect(":memory:") as con:
        con.execute("SET threads=2; SET memory_limit='768MB'")
        con.execute("CREATE TABLE wanted(build_key VARCHAR PRIMARY KEY)")
        con.executemany("INSERT INTO wanted VALUES (?)", [(k,) for k in build_keys])
        cursor = con.execute(f"""
            SELECT m.build_key, z.x, z.y, z.z
            FROM read_parquet('{membership}') m JOIN wanted USING(build_key)
            JOIN read_parquet('{zdo}') z USING(snapshot_id, zdo_index)
            WHERE m.snapshot_id = ? ORDER BY m.build_key, z.zdo_index""",
            [era_row["snapshotId"]])

        def rows():
            while True:
                chunk = cursor.fetchmany(8192)
                if not chunk:
                    break
                yield from chunk

        for key, group in itertools.groupby(rows(), key=lambda r: r[0]):
            points.setdefault(key, []).extend(
                (float(r[1]), float(r[2]), float(r[3])) for r in group)
    return points, era_row


def main():
    args = parse_args()
    campaign = load(args.campaign)
    builds = campaign["builds"]
    if args.limit:
        builds = builds[:args.limit]
    height = args.height or campaign.get("height") or 2160
    target_distance = distance_for_scale(args.target_px_per_m, height)

    forecast = load(args.forecast)["builds"] if args.forecast else {}

    keys = [b["buildKey"] for b in builds]
    sys.stderr.write(f"reading points for {len(keys)} builds...\n")
    points, era_row = read_points(args.root, args.era, keys)

    rows, plan, skipped = [], {}, 0
    for build in builds:
        key = build["buildKey"]
        pts = points.get(key)
        if not pts:
            continue

        # Which builds need this. With a forecast, ask what the orbits actually
        # delivered; without one, ask the geometry the same question directly.
        if forecast.get(key):
            # The best of the four orbits, not the worst: if any one of them is
            # already legible the build has been served and a detail pass is extra.
            worst = max(s["predictedPxPerM"] for s in forecast[key]["shots"].values())
        else:
            # No shot record, so ask the geometry what the orbit planner would do:
            # frame the whole mass, then read the scale off that distance.
            cx = sum(p[0] for p in pts) / len(pts)
            cz = sum(p[2] for p in pts) / len(pts)
            radius = max(math.hypot(p[0] - cx, p[2] - cz) for p in pts)
            fit = max(radius, 4.0) / TAN_V * MARGIN
            worst = height / (2.0 * fit * TAN_V)
        if worst >= args.below_px_per_m:
            skipped += 1
            continue

        masses = subclusters(pts)[:args.max_per_build]
        cid = build.get("localClusterId", 0)
        entries = []
        for n, mass in enumerate(masses, 1):
            mpts = mass_points(mass, pts)
            if len(mpts) < 8:
                continue
            cluster = cluster_from_mass(mass, mpts)
            azimuth = orbit_azimuths(cluster["size_x"], cluster["size_z"])[0][0]
            elevation = elevation_for(cluster, DETAIL_ELEVATION)
            # max_distance=target_distance is the whole trick: camera_for returns
            # min(ideal, max_distance), so a small mass is framed whole and a large
            # one is framed at the target scale.
            cam = camera_for(cluster, azimuth, elevation, MARGIN,
                             target_distance, CLEARANCE, points=mpts)
            c, a = cam["camera"], cam["aim"]
            name = f"detail{n}"
            rows.append("\t".join(map(str, [
                cid, name, c["x"], c["y"], c["z"], cam["yaw_deg"], cam["pitch_deg"],
                ENVIRONMENT, TIME_OF_DAY, a["x"], a["y"], a["z"],
                f"Build {key[:8]}", "", 0, ""])))
            entries.append({
                "shot": name,
                "massPieces": mass["pieces"], "massShare": mass["share"],
                "massRadiusM": mass["radiusM"],
                "distanceM": cam["distance_m"],
                "pxPerM": round(height / (2.0 * cam["distance_m"] * TAN_V), 1),
                "framesWholeMass": cam["frames_whole_build"],
            })
        if entries:
            plan[key] = {"localClusterId": cid, "orbitWorstPxPerM": round(worst, 1),
                         "subMasses": len(masses), "shots": entries}

    os.makedirs(os.path.dirname(os.path.abspath(args.out_tsv)), exist_ok=True)
    with open(args.out_tsv, "w", encoding="utf-8", newline="") as fh:
        fh.write(HEADER + "".join(r + "\n" for r in rows))
    ok, bad = validate_tsv(args.out_tsv)
    if bad or ok != len(rows):
        sys.exit(f"detail TSV contract failed: {ok} ok, {bad} bad, {len(rows)} written")

    doc = {
        "schema": "steward-detail-plan/v1",
        "era": args.era,
        "sourceKey": era_row["sourceKey"],
        "snapshotId": era_row["snapshotId"],
        "targetPxPerM": args.target_px_per_m,
        "targetDistanceM": round(target_distance, 1),
        "belowPxPerM": args.below_px_per_m,
        "elevationDeg": DETAIL_ELEVATION,
        "counts": {"builds": len(plan), "shots": len(rows),
                   "skippedAlreadyLegible": skipped},
        "builds": plan,
    }
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)

    sys.stderr.write(
        f"wrote {args.out_tsv}: {len(rows)} detail shots over {len(plan)} builds "
        f"({skipped} already at or above {args.below_px_per_m} px/m)\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Measure how much frame each shot actually gave the build, from geometry alone.

No images, no GPU, no re-render. Everything here is recoverable from the parquet
the campaign was planned against plus the pose it recorded, so the whole back
catalogue can be scored before a single accelerator wakes up.

The failure this exists to name: plan_shots.framing_from_points solves the camera
distance so that EVERY building ZDO fits in frame -- it is a max over points. A
compound settlement with one outlying pier drags the camera back far enough to
include the pier, and the built mass then occupies a few percent of the picture.
The frame looks fine to every existing metric (exposure is correct and the
surrounding forest supplies plenty of whole-frame edge energy) and is useless to a
reader who does not already know what they are looking at.

So: reproject the build's points through the camera that was actually used, and
report what share of the frame they landed on. Then do it again against a
percentile-trimmed point set -- the framing the fixed planner would have chosen --
and report the difference. That difference, fillDeficit, is what the outliers cost.

  python frame_forecast.py --root E:\\omen\\steward-multi-era --era era11 \\
      --campaign E:\\omen\\steward-multi-era\\omen-capture-era11\\campaign.json \\
      --out forecast-era11.json

Reads the same membership/zdo parquet pair campaign.py plans from, so the point
set is identical by construction rather than by agreement.
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
from plan_shots import FOV_V_DEG, FOV_H_DEG, framing_from_points  # noqa: E402

TAN_V = math.tan(math.radians(FOV_V_DEG / 2.0))
TAN_H = math.tan(math.radians(FOV_H_DEG / 2.0))

# The occupancy grid is 16:9 like the frame, so a cell is square on screen. 64x36
# puts a cell at 60x60 px of a 3840x2160 master -- fine enough that a longhouse
# spans many cells, coarse enough that one lonely ZDO does not read as coverage.
GRID_X, GRID_Y = 64, 36

# campaign.py's call: camera_for(cluster, azimuth, elevation, 1.2, 200, 3, points).
CAMPAIGN_MARGIN = 1.2
CAMPAIGN_MAX_DISTANCE = 200.0


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", required=True,
                   help="archive root holding catalog.json, analysis/ and packages/")
    p.add_argument("--era", required=True, help="era slug, e.g. era11")
    p.add_argument("--campaign", required=True,
                   help="campaign.json for the run whose shots are being scored")
    p.add_argument("--out", required=True)
    p.add_argument("--percentile", type=float, default=90.0,
                   help="counterfactual framing percentile (default 90). The "
                        "trimmed set drops the outlying pieces that dictate the "
                        "current framing")
    p.add_argument("--width", type=int, default=0,
                   help="frame width px; defaults to the campaign's own value")
    p.add_argument("--height", type=int, default=0)
    p.add_argument("--limit", type=int, default=0, help="first N builds only")
    return p.parse_args()


def load(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return (v[0] / n, v[1] / n, v[2] / n) if n else (0.0, 0.0, 1.0)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def camera_basis(cam, aim):
    """Orthonormal basis from the pose as actually flown, not from a replanned angle.

    Deriving this from cam->aim rather than from the azimuth the planner intended
    means a shot whose camera was nudged (clearance clamp, ground query) is measured
    where it really stood.
    """
    forward = norm((aim[0] - cam[0], aim[1] - cam[1], aim[2] - cam[2]))
    right = cross(forward, (0.0, 1.0, 0.0))
    if not any(right):                      # looking straight down
        right = cross(forward, (0.0, 0.0, 1.0))
    right = norm(right)
    up = norm(cross(right, forward))
    return forward, right, up


def project(points, cam, aim):
    """Perspective-project into normalised screen coords; |sx|,|sy| <= 1 is in frame."""
    forward, right, up = camera_basis(cam, aim)
    out = []
    for x, y, z in points:
        rel = (x - cam[0], y - cam[1], z - cam[2])
        depth = dot(rel, forward)
        if depth <= 1e-6:                   # behind the lens
            continue
        out.append((dot(rel, right) / (depth * TAN_H),
                    dot(rel, up) / (depth * TAN_V),
                    depth))
    return out


def coverage(projected, total):
    """What share of the frame the build's pieces actually touch.

    Two numbers, because they fail in opposite directions. bboxFill is the outer
    bound -- a build with a courtyard claims the courtyard. occupancyFill bins the
    points onto a grid and counts live cells, so a sprawl with gaps reads as the
    sum of its parts.

    Both count PIECES, not pixels: a single large roof panel is one ZDO and covers
    little grid, so occupancyFill under-reads solid mass. It is a spread measure.
    The pixel-true version needs the image and lives in frame_geometry.py.
    """
    if not projected:
        return {"bboxFill": 0.0, "occupancyFill": 0.0, "inFrameFraction": 0.0}
    inside = [(sx, sy) for sx, sy, _ in projected if abs(sx) <= 1.0 and abs(sy) <= 1.0]
    if not inside:
        return {"bboxFill": 0.0, "occupancyFill": 0.0, "inFrameFraction": 0.0}

    xs = [p[0] for p in inside]
    ys = [p[1] for p in inside]
    # Clip the bbox to the frame: the visible share is what a reader gets.
    bbox = ((min(1.0, max(xs)) - max(-1.0, min(xs))) / 2.0
            * (min(1.0, max(ys)) - max(-1.0, min(ys))) / 2.0)

    cells = set()
    for sx, sy in inside:
        gx = min(GRID_X - 1, int((sx + 1.0) / 2.0 * GRID_X))
        gy = min(GRID_Y - 1, int((sy + 1.0) / 2.0 * GRID_Y))
        cells.add((gx, gy))
    return {
        "bboxFill": round(max(0.0, bbox), 5),
        "occupancyFill": round(len(cells) / float(GRID_X * GRID_Y), 5),
        "inFrameFraction": round(len(inside) / float(total), 4),
    }


def percentile(values, pct):
    if not values:
        return 0.0
    ordered = sorted(values)
    if pct >= 100.0:
        return ordered[-1]
    idx = (len(ordered) - 1) * (pct / 100.0)
    lo = int(math.floor(idx))
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def mass_radii(points):
    """Radii about the horizontal centroid containing 50/90/100% of the pieces.

    sprawlRatio = P100/P90 is the compound detector. Near 1.0 the build is one
    coherent mass and the bounding volume is honest. Large, and a handful of pieces
    sit far outside everything else -- which is exactly the set the max-over-points
    framing obeys.
    """
    n = float(len(points))
    cx = sum(p[0] for p in points) / n
    cz = sum(p[2] for p in points) / n
    radii = [math.hypot(p[0] - cx, p[2] - cz) for p in points]
    p50, p90, p100 = (percentile(radii, 50.0), percentile(radii, 90.0),
                      percentile(radii, 100.0))
    return (cx, cz), radii, p50, p90, p100


def pose_from_tsv(tsv):
    f = tsv.split("\t")
    return ((float(f[2]), float(f[3]), float(f[4])),      # camera xyz
            (float(f[9]), float(f[10]), float(f[11])))    # aim xyz


def counterfactual(points, radii, keep_radius, cam, aim, height_px):
    """Reframe on the trimmed mass and report what the reader would have got.

    The aim moves with the trimmed set, because a planner that ignores the outliers
    would also centre on what is left. Elevation and bearing are held at what was
    flown, so the only variable is the framing decision itself.
    """
    kept = [p for p, r in zip(points, radii) if r <= keep_radius]
    if len(kept) < 8:                       # too little left to reframe honestly
        return None

    xs = [p[0] for p in kept]
    ys = [p[1] for p in kept]
    zs = [p[2] for p in kept]
    new_aim = ((min(xs) + max(xs)) / 2.0,
               (min(ys) + max(ys)) / 2.0,
               (min(zs) + max(zs)) / 2.0)

    dx, dy, dz = cam[0] - aim[0], cam[1] - aim[1], cam[2] - aim[2]
    horiz = math.hypot(dx, dz)
    az = math.degrees(math.atan2(dx, dz))
    el = math.degrees(math.atan2(dy, horiz)) if horiz else 90.0

    geom = framing_from_points(kept, new_aim, az, el, CAMPAIGN_MARGIN)
    distance = min(geom["ideal_distance_m"], CAMPAIGN_MAX_DISTANCE)
    ar, er = math.radians(az), math.radians(el)
    new_cam = (new_aim[0] + distance * math.cos(er) * math.sin(ar),
               new_aim[1] + distance * math.sin(er),
               new_aim[2] + distance * math.cos(er) * math.cos(ar))

    cov = coverage(project(kept, new_cam, new_aim), len(kept))
    cov["distanceM"] = round(distance, 1)
    cov["predictedPxPerM"] = round(height_px / (2.0 * distance * TAN_V), 2)
    return cov


def read_points(root, era, build_keys):
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

    points = {}
    with duckdb.connect(":memory:") as con:
        con.execute("SET threads=2; SET memory_limit='768MB'")
        con.execute("CREATE TABLE wanted(build_key VARCHAR PRIMARY KEY)")
        con.executemany("INSERT INTO wanted VALUES (?)", [(k,) for k in build_keys])
        cursor = con.execute(f"""
            SELECT m.build_key, z.zdo_index, z.x, z.y, z.z
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
            points[key] = [(float(r[2]), float(r[3]), float(r[4])) for r in group]
    return points, era_row


def main():
    args = parse_args()
    campaign = load(args.campaign)
    builds = campaign["builds"]
    if args.limit:
        builds = builds[:args.limit]
    width = args.width or campaign.get("width") or 3840
    height = args.height or campaign.get("height") or 2160

    keys = [b["buildKey"] for b in builds]
    sys.stderr.write(f"reading points for {len(keys)} builds...\n")
    points, era_row = read_points(args.root, args.era, keys)

    missing = [k for k in keys if k not in points]
    if missing:
        sys.exit(f"{len(missing)} build(s) have no geometry; first {missing[0]}")

    out_builds, shot_rows = {}, 0
    for build in builds:
        key = build["buildKey"]
        pts = points[key]
        (cx, cz), radii, p50, p90, p100 = mass_radii(pts)
        keep_radius = percentile(radii, args.percentile)

        shots = {}
        for shot in build["shots"]:
            cam, aim = pose_from_tsv(shot["tsv"])
            distance = math.dist(cam, aim)
            cov = coverage(project(pts, cam, aim), len(pts))
            row = {
                "shot": shot["shot"],
                "distanceM": round(distance, 1),
                "predictedPxPerM": round(height / (2.0 * distance * TAN_V), 2),
                "framesWholeBuild": shot.get("framesWholeBuild"),
                **cov,
            }
            alt = counterfactual(pts, radii, keep_radius, cam, aim, height)
            if alt:
                row["counterfactual"] = alt
                row["fillDeficit"] = round(alt["occupancyFill"] - cov["occupancyFill"], 5)
                row["pxPerMGain"] = (round(alt["predictedPxPerM"] / row["predictedPxPerM"], 3)
                                     if row["predictedPxPerM"] else None)
            shots[shot["shot"]] = row
            shot_rows += 1

        out_builds[key] = {
            "localClusterId": build.get("localClusterId"),
            "pieces": len(pts),
            "massRadiusP50": round(p50, 2),
            "massRadiusP90": round(p90, 2),
            "massRadiusP100": round(p100, 2),
            "sprawlRatio": round(p100 / p90, 3) if p90 > 0.01 else None,
            "shots": shots,
        }

    doc = {
        "schema": "steward-frame-forecast/v1",
        "era": args.era,
        "sourceKey": era_row["sourceKey"],
        "snapshotId": era_row["snapshotId"],
        "campaign": os.path.abspath(args.campaign),
        "measuredOn": "geometry",
        "frame": {"width": width, "height": height,
                  "fovVDeg": FOV_V_DEG, "grid": [GRID_X, GRID_Y]},
        "counterfactualPercentile": args.percentile,
        "counts": {"builds": len(out_builds), "shots": shot_rows},
        "builds": out_builds,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    sys.stderr.write(f"wrote {args.out}: {len(out_builds)} builds, {shot_rows} shots\n")


if __name__ == "__main__":
    main()

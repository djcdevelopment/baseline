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
import hashlib
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
from frame_forecast import project  # noqa: E402
import pose_forecast  # noqa: E402

TAN_V = math.tan(math.radians(FOV_V_DEG / 2.0))

# The aim rule, settled by two re-shoots of the same 131 shots on AM4 (2026-09-11),
# paired frame-for-frame through frame_geometry.
#
# v1, box centre: 2x the px/m of the orbits, but subject edge density rose in only
# 44 of 77 -- the box centre of a flat platform is a point on the floor.
#
# v2, "dense": aim at the densest, highest 4 m cell. It did NOT work. On the 53 shots
# where the aim moved >= 5 m, subject edge density was 1.01x (26/53) and
# structureFraction HALVED (0.53x). Banded by how far the aim lifted:
#
#     lift        n   edge   structure   sky
#     down >5 m  14   1.18     1.09      0.76     <- centre was in empty air
#     ~0         32   1.10     1.16      0.53     <- run-to-run noise, ~15%
#     up 1-3     16   0.87     0.70      1.15
#     up 6-12    18   0.84     0.37      0.40
#     up >12     15   1.82     0.86      4.04     <- tower crowns against sky
#
# Any upward lift trades floor for sky, and there is no sweet spot. Moving DOWN
# helps: those are the sky-chained and tall builds whose box centre sat in a void
# between platforms (v1 structure 0.000, 0.004, 0.025 on three of them).
#
# So "grounded": the box centre, unless nothing is near it -- then drop to the
# densest cell at or below that height. It is v1 everywhere v1 had a subject, and
# the fix only where v1 aimed at nothing. Never lift. "dense" and "center" stay
# available and all three are scored per shot as centralShare.
AIM_CELL_M = 4.0
AIM_RADIUS_M = 5.0
# The trigger. A first cut used "fewer than 8 pieces within 5 m of the box centre"
# and redirected 67 of 131 shots, several for the worse -- a courtyard's centre
# trivially has few pieces near it. The honest signal is the one already computed
# for every shot: if box-centre framing puts less than this share of the pieces in
# the middle quarter of the frame, it aimed at nothing. Under that, the grounded
# aim is tried and kept only if it clears the same bar -- a descent that finds
# nothing either (a tall build whose mass is all above the centre) stays as v1,
# because that case needs a different elevation, not a different aim.
AIM_EMPTY_SHARE = 0.15
# The central region of the frame used to score the rule: the middle half on each
# axis, a quarter of the picture. A detail frame should have its subject there.
CENTRAL_HALF = 0.5


def dense_aim(points):
    """Where to look: the densest, highest cell of the mass, not its box centre."""
    ys = [p[1] for p in points]
    min_y, span_y = min(ys), max(max(ys) - min(ys), 1.0)
    cells = {}
    for x, y, z in points:
        key = (math.floor(x / AIM_CELL_M), math.floor(y / AIM_CELL_M),
               math.floor(z / AIM_CELL_M))
        cells[key] = cells.get(key, 0) + 1
    best, best_score = None, -1.0
    for (gx, gy, gz), n in cells.items():
        h_rel = ((gy + 0.5) * AIM_CELL_M - min_y) / span_y
        score = n * (0.5 + max(0.0, min(1.0, h_rel)))
        if score > best_score:
            best, best_score = (gx, gy, gz), score
    ctr = tuple((g + 0.5) * AIM_CELL_M for g in best)
    near = [p for p in points if math.dist(p, ctr) <= AIM_RADIUS_M] or [ctr]
    return (sum(p[0] for p in near) / len(near),
            sum(p[1] for p in near) / len(near),
            sum(p[2] for p in near) / len(near))


def grounded_aim(points, cluster):
    """The densest mass at or below the box centre's height. Never lifts.

    The candidate for a centre that aimed at nothing -- a void between chained
    platforms, the hollow of a tall hall. Whether it is used is decided by the
    caller from centralShare, so the common case stays byte-identical to v1.
    """
    cy = cluster["min_y"] + (cluster["max_y"] - cluster["min_y"]) * 0.5
    cells = {}
    for x, y, z in points:
        if y > cy + AIM_CELL_M / 2.0:
            continue                          # never lift
        key = (math.floor(x / AIM_CELL_M), math.floor(y / AIM_CELL_M),
               math.floor(z / AIM_CELL_M))
        cells[key] = cells.get(key, 0) + 1
    if not cells:
        return None
    best = max(cells, key=cells.get)
    bctr = tuple((g + 0.5) * AIM_CELL_M for g in best)
    near = [p for p in points if math.dist(p, bctr) <= AIM_RADIUS_M] or [bctr]
    return (sum(p[0] for p in near) / len(near),
            min(cy, sum(p[1] for p in near) / len(near)),
            sum(p[2] for p in near) / len(near))


def central_share(points, cam, aim):
    """Share of the in-frame pieces that land in the middle quarter of the picture.

    The geometry-side score for the aim rule: the same projection frame_forecast
    uses, asked a narrower question. Reported per shot so the two rules can be
    compared on every build without re-shooting.
    """
    proj = [(sx, sy) for sx, sy, _ in project(points, cam, aim)
            if abs(sx) <= 1.0 and abs(sy) <= 1.0]
    if not proj:
        return 0.0
    inner = sum(1 for sx, sy in proj
                if abs(sx) <= CENTRAL_HALF and abs(sy) <= CENTRAL_HALF)
    return round(inner / float(len(proj)), 4)

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
RANK_FLOOR_RATIO = 0.1      # a candidate below this share of the build's best forecast is not worth a frame


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", required=True)
    p.add_argument("--era", required=True)
    p.add_argument("--campaign", required=True,
                   help="campaign.json naming the builds and their cluster ids")
    p.add_argument("--out-tsv", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-campaign", default="",
                   help="also write a steward-local-campaign/v1 campaign.json, so the "
                        "detail tier runs through install_capture_worker.py and "
                        "capture_worker.py like any other campaign instead of down a "
                        "side channel. Write it into its own immutable directory "
                        "beside the TSV")
    p.add_argument("--batch-size", type=int, default=100)
    p.add_argument("--min-free-bytes", type=int, default=20 * 1024 ** 3)
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
                   help="cap on masses considered per build, largest first")
    p.add_argument("--frames-per-build", type=int, default=5,
                   help="candidate poses kept per build after the pre-shutter forecast, "
                        "round-robin across masses so every mass gets its best pose first "
                        "(2026-09-12: 33 of 77 builds lost both frames to aim, not angle)")
    p.add_argument("--aim-rule", choices=("grounded", "center", "dense"),
                   default="grounded",
                   help="grounded (default): box centre unless nothing is near it, "
                        "then the densest mass at or below that height -- never "
                        "lifts. center: the box centre always (the v1 era11 run). "
                        "dense: the densest, highest cell (the v2 run; it halved "
                        "structureFraction and is kept only for comparison). All "
                        "three are scored per shot as centralShare")
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


# A build made mostly of prefabs the name dictionary cannot resolve ("hash:NNNN")
# is made of mod prefabs the capture client does not have. It arrives as an empty
# zone -- "world never arrived (0 pieces)" -- on every attempt, and costs a game
# relaunch on the miss and another on the retry before the worker gives up. era11's
# bad2c07d (289 pieces, five prefabs, all hash:) did exactly that on three separate
# campaigns. Six such builds exist across every campaign; skip them at plan time.
UNRESOLVABLE_SHARE = 0.5


def read_points(root, era, build_keys):
    era_row, membership, zdo = artifacts(root, era)
    points, unresolvable = {}, set()
    with duckdb.connect(":memory:") as con:
        con.execute("SET threads=2; SET memory_limit='768MB'")
        con.execute("CREATE TABLE wanted(build_key VARCHAR PRIMARY KEY)")
        con.executemany("INSERT INTO wanted VALUES (?)", [(k,) for k in build_keys])
        for key, n, u in con.execute(f"""
            SELECT m.build_key, count(*),
                   count(*) FILTER (WHERE z.prefab_name IS NULL
                                       OR z.prefab_name LIKE 'hash:%')
            FROM read_parquet('{membership}') m JOIN wanted USING(build_key)
            JOIN read_parquet('{zdo}') z USING(snapshot_id, zdo_index)
            WHERE m.snapshot_id = ? GROUP BY 1""", [era_row["snapshotId"]]).fetchall():
            if u / float(n) > UNRESOLVABLE_SHARE:
                unresolvable.add(key)
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
    return points, era_row, unresolvable


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
    points, era_row, unresolvable = read_points(args.root, args.era, keys)
    if unresolvable:
        names = ", ".join(k[:8] for k in sorted(unresolvable))
        sys.stderr.write(f"skipping {len(unresolvable)} build(s) the client cannot "
                         f"render (majority hash: prefabs): {names}\n")

    rows, plan, campaign_builds, skipped = [], {}, [], 0
    for build in builds:
        key = build["buildKey"]
        pts = points.get(key)
        if not pts or key in unresolvable:
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
        per_mass = []
        for n, mass in enumerate(masses, 1):
            mpts = mass_points(mass, pts)
            if len(mpts) < 8:
                continue
            cluster = cluster_from_mass(mass, mpts)
            # Where the mass actually faces, and what kind of thing it is: the prior the
            # 33 lost builds were missing. A longhouse is shot from its facade corners,
            # not from the axis-aligned bearing the orbit planner defaults to; a tower
            # from low, a compound from high.
            orientation = pose_forecast.pca_orientation(mpts)
            kind = pose_forecast.typology(cluster["size_x"], cluster["size_y"], cluster["size_z"],
                                          mass["pieces"], cluster["min_y"])
            profile = pose_forecast.PROFILES[kind]
            azimuths = pose_forecast.bearings(orientation,
                                              extra=[orbit_azimuths(cluster["size_x"], cluster["size_z"])[0][0]])
            elevations = sorted({round(elevation_for(cluster, DETAIL_ELEVATION), 1),
                                 round(elevation_for(cluster, profile["elevationDeg"]), 1)})
            candidates = []
            for azimuth in azimuths:
                for elevation in elevations:
                    # max_distance=target_distance is the whole trick: camera_for returns
                    # min(ideal, max_distance), so a small mass is framed whole and a large
                    # one is framed at the target scale. Every aim rule is solved so the
                    # record carries the comparison; the chosen one is what gets forecast.
                    solved = {}
                    for rule in ("center", "dense", "grounded"):
                        aim = {"center": None, "dense": dense_aim(mpts),
                               "grounded": grounded_aim(mpts, cluster)}[rule]
                        solved[rule] = camera_for(cluster, azimuth, elevation, MARGIN,
                                                  target_distance, CLEARANCE,
                                                  points=mpts, aim=aim)
                    shares = {rule: central_share(
                        mpts, (s["camera"]["x"], s["camera"]["y"], s["camera"]["z"]),
                        (s["aim"]["x"], s["aim"]["y"], s["aim"]["z"]))
                        for rule, s in solved.items()}
                    # grounded is box-centre unless box-centre aimed at nothing AND the
                    # descent actually helps; then and only then it moves.
                    if (args.aim_rule == "grounded"
                            and not (shares["center"] < AIM_EMPTY_SHARE
                                     and shares["grounded"] >= AIM_EMPTY_SHARE)):
                        solved["grounded"] = solved["center"]
                        shares["grounded"] = shares["center"]
                    cam = solved[args.aim_rule]
                    c, a = cam["camera"], cam["aim"]
                    fc = pose_forecast.forecast(mpts, (c["x"], c["y"], c["z"]), (a["x"], a["y"], a["z"]))
                    candidates.append({
                        "name": f"detail{n}-{int(round(azimuth)) % 360:03d}-{int(round(elevation)):02d}",
                        "cam": cam, "forecast": fc, "shares": shares, "solved": solved,
                        "azimuthDeg": round(azimuth, 1), "elevationDeg": elevation})
            candidates.sort(key=lambda cand: -cand["forecast"]["rank"])
            per_mass.append((n, mass, orientation, kind, candidates))
        # Every mass gets its best pose before any mass gets a second: the first pass is
        # the survey, the rest are variants for the light table to choose between. A
        # candidate the forecast ranks below a tenth of the build's best is not a variant
        # worth a frame -- typically a mass the target scale cannot frame at all.
        best = max((c[4][0]["forecast"]["rank"] for c in per_mass if c[4]), default=0.0)
        per_mass = [(n, mass, orientation, kind,
                     [cand for cand in candidates if cand["forecast"]["rank"] >= RANK_FLOOR_RATIO * best])
                    for n, mass, orientation, kind, candidates in per_mass]
        chosen = []
        for depth in range(max((len(c[4]) for c in per_mass), default=0)):
            for n, mass, orientation, kind, candidates in per_mass:
                if depth < len(candidates) and len(chosen) < args.frames_per_build:
                    chosen.append((n, mass, orientation, kind, candidates[depth]))
        entries, campaign_shots = [], []
        for n, mass, orientation, kind, cand in chosen:
            cam, shares, solved, name = cand["cam"], cand["shares"], cand["solved"], cand["name"]
            c, a = cam["camera"], cam["aim"]
            tsv = "\t".join(map(str, [
                cid, name, c["x"], c["y"], c["z"], cam["yaw_deg"], cam["pitch_deg"],
                ENVIRONMENT, TIME_OF_DAY, a["x"], a["y"], a["z"],
                f"Build {key[:8]}", "", 0, ""]))
            rows.append(tsv)
            campaign_shots.append({
                "shotKey": hashlib.sha256(
                    f"{era_row['sourceKey']}:{key}:{name}".encode()).hexdigest(),
                "shot": name, "tsv": tsv,
                "framesWholeBuild": cam["frames_whole_build"],
                "mass": n, "typology": kind, "forecast": cand["forecast"]})
            entries.append({
                "shot": name, "mass": n, "typology": kind,
                "azimuthDeg": cand["azimuthDeg"], "elevationDeg": cand["elevationDeg"],
                "principalAngleDeg": orientation["principalAngleDeg"],
                "massPieces": mass["pieces"], "massShare": mass["share"],
                "massRadiusM": mass["radiusM"],
                "distanceM": cam["distance_m"],
                "pxPerM": round(height / (2.0 * cam["distance_m"] * TAN_V), 1),
                "framesWholeMass": cam["frames_whole_build"],
                "aimRule": args.aim_rule,
                "aimLiftM": round(solved["dense"]["aim"]["y"]
                                  - solved["center"]["aim"]["y"], 1),
                "centralShare": shares[args.aim_rule],
                "centralShareCenter": shares["center"],
                "centralShareDense": shares["dense"],
                "centralShareGrounded": shares["grounded"],
                "groundedMoved": solved["grounded"]["aim"] != solved["center"]["aim"],
                "forecast": cand["forecast"],
            })
        if entries:
            plan[key] = {"localClusterId": cid, "orbitWorstPxPerM": round(worst, 1),
                         "subMasses": len(masses), "shots": entries}
            campaign_builds.append({
                "buildKey": key, "localClusterId": cid,
                "membershipSha256": build.get("membershipSha256"),
                "pieces": len(pts), "shots": campaign_shots})

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
        "aimRule": args.aim_rule,
        "framesPerBuild": args.frames_per_build,
        "counts": {"builds": len(plan), "shots": len(rows),
                   "skippedAlreadyLegible": skipped,
                   "skippedUnrenderable": sorted(k[:12] for k in unresolvable)},
        "builds": plan,
    }
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)

    if args.out_campaign:
        # Same shape campaign.py writes, so install_capture_worker.py stamps it and
        # capture_worker.py runs it with no special case. batchSize matters: a game
        # launch costs ~233 s, and a detail pass is small enough to fit one launch.
        import datetime
        campaign_doc = {
            "schema": "steward-local-campaign/v1",
            "createdAt": datetime.datetime.now(datetime.timezone.utc)
                                 .strftime("%Y-%m-%dT%H:%M:%SZ"),
            "era": args.era,
            "sourceKey": era_row["sourceKey"],
            "snapshotId": era_row["snapshotId"],
            "world": era_row["worldId"],
            "sourceFiles": {k: {p: era_row[k][p] for p in ("bytes", "sha256")}
                            for k in ("db", "fwl")},
            "runtimeMode": "current-client",
            "width": campaign.get("width", 3840), "height": height,
            "batchSize": args.batch_size,
            "maxOutputBytes": 32 * 1024 ** 3,
            "minFreeBytes": args.min_free_bytes,
            "stallSeconds": 900, "maxAttempts": 2,
            "excludedCompleted": [],
            "builds": campaign_builds,
        }
        os.makedirs(os.path.dirname(os.path.abspath(args.out_campaign)), exist_ok=True)
        with open(args.out_campaign, "w", encoding="utf-8") as fh:
            json.dump(campaign_doc, fh, indent=2, sort_keys=True)
        # capture_worker reads all-shots.tsv from the campaign directory by name.
        beside = os.path.join(os.path.dirname(os.path.abspath(args.out_campaign)),
                              "all-shots.tsv")
        with open(beside, "w", encoding="utf-8", newline="") as fh:
            fh.write(HEADER + "".join(r + "\n" for r in rows))
        sys.stderr.write(f"wrote {args.out_campaign} and all-shots.tsv beside it\n")

    sys.stderr.write(
        f"wrote {args.out_tsv}: {len(rows)} detail shots over {len(plan)} builds "
        f"({skipped} already at or above {args.below_px_per_m} px/m)\n")


if __name__ == "__main__":
    main()

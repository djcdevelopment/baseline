#!/usr/bin/env python3
"""Probe whether rotated prefab envelopes materially improve 3-D shot framing.

This is an R&D instrument, not a planner.  The production planner currently solves
camera distance against exact BUILDING ZDO pivots.  This probe joins those frozen
members to the independently verified rotation export, expands each architectural
piece to its eight oriented-box corners, and asks whether the physical envelope would
have changed any of the already captured exact-XYZ frames.

Vegetation is deliberately not part of the subject envelope.  Player-planted trees
classify as BUILDING in the world cache, while their mesh bounds are often sway/LOD
volumes rather than photographic widths.  They remain reported as context and belong
to the separate sight/occlusion instrument.

If the recorded material-edge gate passes, the probe emits a six-row paired-shot TSV
for another capture agent.  It never fires AM4 and never edits plan_shots.py.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from collections import defaultdict

import duckdb
import numpy as np
from PIL import Image, ImageDraw

from plan_shots import ASPECT, FOV_H_DEG, FOV_V_DEG, framing_from_points, validate_tsv
from sight import looks_like_vegetation
from verify_rotation import HYPOTHESES


HERE = os.path.dirname(os.path.abspath(__file__))
ERA = os.path.join(HERE, "out", "era17")
DEFAULT_RECEIPTS = (r"C:\Program Files (x86)\Steam\steamapps\common\Valheim"
                    r"\BepInEx\config\shotplan-receipts.jsonl")
DEFAULT_CAPTURES = (r"C:\Program Files (x86)\Steam\steamapps\common\Valheim"
                    r"\BepInEx\config\comfy-orbit-captures")

BOX_CORNERS = np.asarray([[x, y, z] for x in (-0.5, 0.5)
                          for y in (-0.5, 0.5) for z in (-0.5, 0.5)], dtype=float)
BOX_EDGES = (
    (0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
    (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7),
)
NEAR_M = 0.05
HANDOFF_ROUNDING_PAD_M = 0.25


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--plan", action="append", required=True,
                   help="exact-XYZ plan JSON; repeat once per capture run")
    p.add_argument("--run-id", action="append", required=True,
                   help="capture run corresponding positionally to --plan")
    p.add_argument("--clusters", default=os.path.join(ERA, "clusters.json"))
    p.add_argument("--cluster-points", required=True)
    p.add_argument("--building-geometry", required=True)
    p.add_argument("--piece-geometry",
                   default=os.path.join(ERA, "arch", "piece-geometry.json"))
    p.add_argument("--rotation-verify",
                   default=os.path.join(ERA, "arch", "rotation-verify.json"))
    p.add_argument("--receipts", default=DEFAULT_RECEIPTS)
    p.add_argument("--capture-root", default=DEFAULT_CAPTURES)
    p.add_argument("--out", default=os.path.join(ERA, "framing-envelope-probe"))
    p.add_argument("--trusted-coverage", type=float, default=0.95)
    p.add_argument("--min-distance-delta-m", type=float, default=2.0)
    p.add_argument("--min-distance-delta-pct", type=float, default=5.0)
    p.add_argument("--min-material-clusters", type=int, default=3)
    p.add_argument("--control-cluster", type=int,
                   help="prefer this visually adjudicated cluster for the paired control")
    return p.parse_args()


def fail(message):
    raise SystemExit(message)


def escaped(path):
    return os.path.abspath(path).replace("\\", "/").replace("'", "''")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(value, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def load_plans(paths, run_ids):
    if len(paths) != len(run_ids):
        fail(f"--plan count ({len(paths)}) must equal --run-id count ({len(run_ids)})")
    loaded, rows = [], []
    expected_world = None
    for path, run_id in zip(paths, run_ids):
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        settings = doc.get("settings", {})
        if settings.get("cluster_points") and \
                os.path.abspath(settings["cluster_points"]) != os.path.abspath(args.cluster_points):
            fail(f"{path} used {settings['cluster_points']}, not {args.cluster_points}")
        if expected_world is None:
            expected_world = doc.get("world")
        elif doc.get("world") != expected_world:
            fail(f"plan worlds disagree: {expected_world!r} vs {doc.get('world')!r}")
        margin = float(settings.get("margin", 1.15))
        if not math.isclose(float(settings.get("fov_v_deg", FOV_V_DEG)),
                            FOV_V_DEG, abs_tol=1e-9):
            fail(f"{path} was not planned at the supported {FOV_V_DEG:g}-degree FOV")
        for row in doc.get("plan", []):
            if row.get("geometry_source") != "zdo_xyz":
                fail(f"{path} contains a non-ZDO geometry row: "
                     f"{row.get('cluster_id')} {row.get('shot')}")
            item = dict(row)
            item["_run_id"] = run_id
            item["_plan_path"] = os.path.abspath(path)
            item["_margin"] = margin
            rows.append(item)
        loaded.append({"path": os.path.abspath(path), "run_id": run_id,
                       "sha256": sha256(path), "rows": len(doc.get("plan", [])),
                       "margin": margin})
    return loaded, rows


def load_receipts(path, run_ids):
    wanted = set(run_ids)
    receipts = {}
    with open(path, encoding="utf-8-sig") as fh:
        for line_no, raw in enumerate(fh, 1):
            raw = raw.strip().lstrip("\ufeff")
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                fail(f"receipt line {line_no} is unreadable: {exc}")
            run = str(row.get("run", ""))
            if run not in wanted:
                continue
            key = (run, int(row["cluster_id"]), str(row["shot"]))
            if key in receipts:
                fail(f"duplicate receipt identity {key}")
            receipts[key] = row
    return receipts


def load_geometry(path):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc, {row["name"]: row for row in doc["pieces"]}


def load_rotation(path):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if doc.get("verdict") != "PASS":
        fail(f"rotation receipt is not PASS: {doc.get('verdict')!r}")
    winner = doc.get("winner")
    if winner not in HYPOTHESES:
        fail(f"unknown rotation winner {winner!r}")
    return doc, HYPOTHESES[winner]


def load_members(cluster_doc, cluster_ids, points_path, geometry_path):
    points_sql, geometry_sql = escaped(points_path), escaped(geometry_path)
    con = duckdb.connect()
    con.execute(f"CREATE TEMP VIEW point_source AS SELECT * FROM read_parquet('{points_sql}')")
    con.execute(f"CREATE TEMP VIEW rotation_source AS SELECT * FROM read_parquet('{geometry_sql}')")
    point_columns = {row[1] for row in con.execute(
        "PRAGMA table_info('point_source')").fetchall()}
    rotation_columns = {row[1] for row in con.execute(
        "PRAGMA table_info('rotation_source')").fetchall()}
    point_required = {"snapshot_id", "world_id", "cluster_id", "zdo_index",
                      "prefab_name", "x", "y", "z"}
    rotation_required = {"zdo_index", "prefab_name", "x", "y", "z",
                         "has_rot", "rot_x", "rot_y", "rot_z"}
    if point_required - point_columns:
        fail("cluster point artifact is missing: " +
             ", ".join(sorted(point_required - point_columns)))
    if rotation_required - rotation_columns:
        fail("building geometry artifact is missing: " +
             ", ".join(sorted(rotation_required - rotation_columns)))

    metadata = con.execute(
        "SELECT DISTINCT snapshot_id, world_id FROM point_source "
        "ORDER BY snapshot_id, world_id").fetchall()
    expected = (cluster_doc.get("snapshot_id"), cluster_doc.get("world_id"))
    if len(metadata) != 1 or metadata[0] != expected:
        fail(f"cluster point artifact belongs to {metadata}, clusters.json is {expected}")

    by_id = {int(c["cluster_id"]): c for c in cluster_doc["clusters"]}
    unknown = sorted(set(cluster_ids) - set(by_id))
    if unknown:
        fail(f"plans refer to unknown frozen cluster ids: {unknown}")
    con.execute("CREATE TEMP TABLE wanted_cluster(cluster_id BIGINT, pieces BIGINT)")
    con.executemany("INSERT INTO wanted_cluster VALUES (?, ?)",
                    [(cid, int(by_id[cid]["pieces"])) for cid in cluster_ids])
    membership_mismatch = con.execute("""
        SELECT w.cluster_id, w.pieces, count(p.zdo_index) actual
        FROM wanted_cluster w LEFT JOIN point_source p USING (cluster_id)
        GROUP BY w.cluster_id, w.pieces
        HAVING count(p.zdo_index) != w.pieces
        ORDER BY w.cluster_id
        """).fetchall()
    if membership_mismatch:
        fail(f"frozen membership mismatch: {membership_mismatch[:5]}")

    duplicate_points = con.execute("""
        SELECT count(*) - count(DISTINCT p.zdo_index)
        FROM point_source p JOIN wanted_cluster w USING (cluster_id)
        """).fetchone()[0]
    if duplicate_points:
        fail(f"selected cluster artifact repeats {duplicate_points} zdo_index value(s)")

    checks = con.execute("""
        SELECT
          count(*) AS total_rows,
          count(g.zdo_index) joined,
          sum(CASE WHEN g.zdo_index IS NOT NULL AND
                    (p.prefab_name IS DISTINCT FROM g.prefab_name OR
                     abs(p.x-g.x) > 1e-9 OR abs(p.y-g.y) > 1e-9 OR abs(p.z-g.z) > 1e-9)
              THEN 1 ELSE 0 END) mismatched
        FROM point_source p
        JOIN wanted_cluster w USING (cluster_id)
        LEFT JOIN rotation_source g USING (zdo_index)
        """).fetchone()
    if checks[0] != checks[1] or checks[2]:
        fail(f"point/rotation join failed: rows={checks[0]}, joined={checks[1]}, "
             f"identity_or_xyz_mismatches={checks[2]}")

    rows = con.execute("""
        SELECT p.cluster_id, p.zdo_index, p.prefab_name, p.x, p.y, p.z,
               g.has_rot, g.rot_x, g.rot_y, g.rot_z
        FROM point_source p
        JOIN wanted_cluster w USING (cluster_id)
        JOIN rotation_source g USING (zdo_index)
        ORDER BY p.cluster_id, p.zdo_index
        """).fetchall()
    con.close()
    grouped = defaultdict(list)
    for row in rows:
        grouped[int(row[0])].append(row)
    return grouped, {
        "selected_rows": int(checks[0]),
        "rotation_rows_joined": int(checks[1]),
        "identity_or_xyz_mismatches": int(checks[2]),
        "duplicate_zdo_indices": int(duplicate_points),
        "snapshot_id": expected[0],
        "world_id": expected[1],
    }


def rotation_matrix(has_rot, rx, ry, rz, hypothesis):
    if not has_rot:
        return np.eye(3)
    to_rad, compose = hypothesis
    ax = np.asarray([float(rx) * to_rad])
    ay = np.asarray([float(ry) * to_rad])
    az = np.asarray([float(rz) * to_rad])
    return compose(ax, ay, az)[0]


def build_cluster_geometry(rows, geometry, hypothesis):
    points = []
    subject_points = []
    all_corners, all_meta = [], []
    trusted_corners, trusted_meta = [], []
    piece_corners = {}
    source_counts = defaultdict(int)
    vegetation_counts = defaultdict(int)
    missing_counts = defaultdict(int)
    subject_rows = 0
    for row in rows:
        _, zdo_index, name, x, y, z, has_rot, rx, ry, rz = row
        pivot = np.asarray([float(x), float(y), float(z)])
        points.append(pivot)
        if looks_like_vegetation(name):
            vegetation_counts[name] += 1
            continue
        subject_rows += 1
        subject_points.append(pivot)
        geom = geometry.get(name)
        if not geom:
            missing_counts[name] += 1
            continue
        extents = np.asarray(geom["extents"], dtype=float)
        offset = np.asarray(geom["center_offset"], dtype=float)
        if not np.isfinite(extents).all() or (extents < 0).any() or \
                not np.isfinite(offset).all():
            fail(f"non-finite or negative geometry for {name}")
        rot = rotation_matrix(has_rot, rx, ry, rz, hypothesis)
        center = pivot + rot @ offset
        corners = (BOX_CORNERS * extents) @ rot.T + center
        source = str(geom.get("source", "unknown"))
        source_counts[source] += 1
        meta = [{"zdo_index": int(zdo_index), "prefab": name,
                 "family": str(geom.get("family", "unknown")),
                 "geometry_source": source, "corner": i}
                for i in range(8)]
        all_corners.append(corners)
        all_meta.extend(meta)
        piece_corners[int(zdo_index)] = corners
        if source != "family_median":
            trusted_corners.append(corners)
            trusted_meta.extend(meta)

    if not points or not subject_points or not trusted_corners:
        fail("a selected cluster has no usable architectural geometry")
    all_box_rows = len(all_corners)
    trusted_box_rows = len(trusted_corners)
    return {
        "points": np.vstack(points),
        "subject_points": np.vstack(subject_points),
        "all_corners": np.vstack(all_corners),
        "all_meta": all_meta,
        "trusted_corners": np.vstack(trusted_corners),
        "trusted_meta": trusted_meta,
        "piece_corners": piece_corners,
        "counts": {
            "zdo_rows": len(points),
            "subject_rows": subject_rows,
            "vegetation_rows": sum(vegetation_counts.values()),
            "all_box_rows": all_box_rows,
            "trusted_box_rows": trusted_box_rows,
            "missing_geometry_rows": sum(missing_counts.values()),
            "all_geometry_coverage": round(all_box_rows / subject_rows, 6),
            "trusted_geometry_coverage": round(trusted_box_rows / subject_rows, 6),
            "geometry_sources": dict(sorted(source_counts.items())),
            "vegetation_prefabs": dict(sorted(vegetation_counts.items(),
                                                key=lambda item: (-item[1], item[0]))),
            "missing_prefabs": dict(sorted(missing_counts.items(),
                                             key=lambda item: (-item[1], item[0]))),
        },
    }


def planner_axes(azimuth_deg, elevation_deg):
    az = math.radians(float(azimuth_deg))
    el = math.radians(float(elevation_deg))
    back = np.asarray([math.sin(az) * math.cos(el), math.sin(el),
                       math.cos(az) * math.cos(el)])
    right = np.asarray([math.cos(az), 0.0, -math.sin(az)])
    up = np.cross(back, right)
    return back, right, up


def camera_basis(yaw_deg, pitch_deg):
    yaw, pitch = math.radians(float(yaw_deg)), math.radians(float(pitch_deg))
    forward = np.asarray([math.cos(pitch) * math.sin(yaw), -math.sin(pitch),
                          math.cos(pitch) * math.cos(yaw)])
    right = np.asarray([math.cos(yaw), 0.0, -math.sin(yaw)])
    up = np.asarray([math.sin(yaw) * math.sin(pitch), math.cos(pitch),
                     math.cos(yaw) * math.sin(pitch)])
    return forward, right, up


def required_distance(vertices, aim, axes, margin, metadata=None):
    back, right, up = axes
    relative = vertices - aim
    image_x = relative @ right
    image_y = relative @ up
    depth = relative @ back
    horizontal = depth + margin * np.abs(image_x) / math.tan(math.radians(FOV_H_DEG / 2))
    vertical = depth + margin * np.abs(image_y) / math.tan(math.radians(FOV_V_DEG / 2))
    combined = np.maximum(horizontal, vertical)
    idx = int(np.argmax(combined))
    ideal = max(float(combined[idx]), margin * 4.0 /
                math.tan(math.radians(FOV_V_DEG / 2)))
    axis = "horizontal" if horizontal[idx] >= vertical[idx] else "vertical"
    limiter = dict(metadata[idx]) if metadata is not None and ideal == combined[idx] else None
    if limiter is not None:
        limiter.update({"axis": axis, "required_distance_m": round(float(combined[idx]), 3),
                        "camera_depth_m": round(float(depth[idx]), 3)})
    return {
        "required_distance_m": round(ideal, 6),
        "projected_width_m": round(float(np.ptp(image_x)), 6),
        "projected_height_m": round(float(np.ptp(image_y)), 6),
        "camera_depth_m": round(float(np.ptp(depth)), 6),
        "world_height_m": round(float(np.ptp(vertices[:, 1])), 6),
        "limiter": limiter,
    }


def frame_utilization(vertices, metadata, camera, yaw, pitch, margin):
    forward, right, up = camera_basis(yaw, pitch)
    relative = vertices - camera
    depth = relative @ forward
    behind = depth <= NEAR_M
    safe_depth = np.maximum(depth, NEAR_M)
    x_ndc = (relative @ right) / (safe_depth * math.tan(math.radians(FOV_H_DEG / 2)))
    y_ndc = (relative @ up) / (safe_depth * math.tan(math.radians(FOV_V_DEG / 2)))
    utilization = np.maximum(np.abs(x_ndc), np.abs(y_ndc))
    utilization[behind] = np.inf
    idx = int(np.argmax(utilization))
    axis = "horizontal" if abs(x_ndc[idx]) >= abs(y_ndc[idx]) else "vertical"
    limiter = dict(metadata[idx])
    limiter.update({"axis": axis, "x_ndc": round(float(x_ndc[idx]), 6),
                    "y_ndc": round(float(y_ndc[idx]), 6),
                    "camera_depth_m": round(float(depth[idx]), 6)})
    maximum = float(utilization[idx])
    return {
        "max_utilization": None if not math.isfinite(maximum) else round(maximum, 6),
        "intended_margin_limit": round(1.0 / margin, 6),
        "margin_violated": bool(maximum > 1.0 / margin),
        "clipped": bool(maximum > 1.0),
        "behind_camera": int(np.count_nonzero(behind)),
        "limiter": limiter,
    }


def vector(mapping):
    return np.asarray([float(mapping["x"]), float(mapping["y"]), float(mapping["z"])])


def pct_delta(new, old):
    return 100.0 * (new - old) / old if old else 0.0


def convex_hull(points):
    unique = sorted(set((int(round(x)), int(round(y))) for x, y in points))
    if len(unique) <= 1:
        return unique

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def project_pixels(vertices, camera, yaw, pitch, width, height):
    forward, right, up = camera_basis(yaw, pitch)
    relative = vertices - camera
    depth = relative @ forward
    visible = depth > NEAR_M
    x_ndc = (relative[visible] @ right) / (depth[visible] *
            math.tan(math.radians(FOV_H_DEG / 2)))
    y_ndc = (relative[visible] @ up) / (depth[visible] *
            math.tan(math.radians(FOV_V_DEG / 2)))
    pixels = np.column_stack(((1.0 + x_ndc) * width / 2.0,
                              (1.0 - y_ndc) * height / 2.0))
    return pixels, visible


def save_overlay(capture_root, output, cluster, frame, role):
    receipt = frame["_receipt"]
    image_path = os.path.join(capture_root, receipt["run"], receipt["file"])
    if not os.path.isfile(image_path):
        return None
    image = Image.open(image_path).convert("RGB")
    original_w, original_h = image.size
    camera = vector(receipt.get("lens") or receipt.get("placed") or receipt["planned"])
    pixels, _ = project_pixels(cluster["trusted_corners"], camera,
                               receipt["yaw"], receipt["pitch"], original_w, original_h)
    hull = convex_hull(pixels)
    max_w = 1920
    scale = min(1.0, max_w / original_w)
    if scale < 1.0:
        image = image.resize((round(original_w * scale), round(original_h * scale)),
                             Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    margin = frame["_plan"]["_margin"]
    safe = 1.0 / margin
    left = (1.0 - safe) * image.width / 2.0
    right = (1.0 + safe) * image.width / 2.0
    top = (1.0 - safe) * image.height / 2.0
    bottom = (1.0 + safe) * image.height / 2.0
    draw.rectangle((left, top, right, bottom), outline=(0, 220, 255), width=3)
    if len(hull) >= 3:
        draw.line([(x * scale, y * scale) for x, y in hull + [hull[0]]],
                  fill=(255, 40, 220), width=4)
    limiter = frame["trusted_required"].get("limiter")
    if limiter and limiter["zdo_index"] in cluster["piece_corners"]:
        box = cluster["piece_corners"][limiter["zdo_index"]]
        box_pixels, visible = project_pixels(box, camera, receipt["yaw"], receipt["pitch"],
                                             original_w, original_h)
        projected = {}
        cursor = 0
        for index, is_visible in enumerate(visible):
            if is_visible:
                projected[index] = tuple(box_pixels[cursor] * scale)
                cursor += 1
        for a, b in BOX_EDGES:
            if a in projected and b in projected:
                draw.line((projected[a], projected[b]), fill=(255, 186, 48), width=4)
    text = (f"{role}: cluster {frame['cluster_id']} {frame['shot']} | "
            f"point {frame['point_required_m']:.1f} m -> box "
            f"{frame['trusted_required_m']:.1f} m | "
            f"actual util {frame['actual_trusted']['max_utilization']}")
    draw.rectangle((12, 12, min(image.width - 12, 14 + 8 * len(text)), 42),
                   fill=(18, 18, 18))
    draw.text((18, 18), text, fill=(245, 245, 245))
    os.makedirs(os.path.dirname(output), exist_ok=True)
    image.save(output)
    return output


def choose_cases(frames, trusted_coverage):
    candidates = [f for f in frames if f["shot"].startswith("orbit") and
                  f["cluster_counts"]["trusted_geometry_coverage"] >= trusted_coverage and
                  f["trusted_required"].get("limiter")]
    material = [f for f in candidates if f["actual_trusted"]["clipped"] or
                (f["distance_delta_m"] >= args.min_distance_delta_m and
                 f["distance_delta_pct"] >= args.min_distance_delta_pct)]
    chosen, used = [], set()

    vertical = [f for f in material if
                f["trusted_required"]["limiter"]["axis"] == "vertical" and
                f["trusted_required"]["limiter"].get("family") != "misc"]
    if vertical:
        row = max(vertical, key=lambda f: (f["distance_delta_m"],
                                           f["actual_trusted"]["max_utilization"] or 0))
        chosen.append(("vertical", row)); used.add(row["cluster_id"])

    depth = [f for f in material if f["cluster_id"] not in used and
             f["trusted_required"]["limiter"].get("family") != "misc"]
    if depth:
        row = max(depth, key=lambda f: (f["depth_added_m"], f["distance_delta_m"]))
        chosen.append(("depth", row)); used.add(row["cluster_id"])

    controls = [f for f in candidates if f["cluster_id"] not in used and
                not f["actual_trusted"]["clipped"]]
    if args.control_cluster is not None:
        preferred = [f for f in controls if f["cluster_id"] == args.control_cluster]
        if not preferred:
            fail(f"preferred control cluster {args.control_cluster} has no eligible orbit")
        controls = preferred
    if controls:
        row = min(controls, key=lambda f: (abs(f["distance_delta_pct"]),
                                           abs(f["distance_delta_m"])))
        chosen.append(("control", row)); used.add(row["cluster_id"])
    return chosen


def handoff_row(source, shot, camera, distance, role, variant):
    row = {
        "cluster_id": source["cluster_id"],
        "label": f"framing envelope {role} {variant}",
        "pieces": source.get("pieces"),
        "height_m": source.get("height_m"),
        "region": source.get("region"),
        "shot": shot,
        "azimuth_deg": source.get("azimuth_deg"),
        "camera": {axis: round(float(camera[i]), 1)
                   for i, axis in enumerate(("x", "y", "z"))},
        "aim": dict(source["aim"]),
        "yaw_deg": source["yaw_deg"],
        "pitch_deg": source["pitch_deg"],
        "distance_m": round(float(distance), 1),
        "elevation_deg": source.get("elevation_deg"),
        "frames_whole_build": True,
        "geometry_source": "zdo_oriented_box" if variant == "box" else "zdo_xyz",
        "environment": source["environment"],
        "time_of_day": source["time_of_day"],
        "fires": bool(source.get("fires")),
        "flash": source.get("flash"),
    }
    return row


def write_handoff(chosen, out_dir, inputs, cluster_geometry):
    if len(chosen) != 3 or {role for role, _ in chosen} != {"vertical", "depth", "control"}:
        return {"generated": False,
                "reason": "could not select distinct vertical, depth, and control cases"}
    rows, pairs = [], []
    for role, frame in chosen:
        source = frame["_plan"]
        aim = vector(source["aim"])
        point_camera = vector(source["camera"])
        ray = point_camera - aim
        point_ray_distance = float(np.linalg.norm(ray))
        if point_ray_distance <= 0:
            fail(f"zero camera ray for {frame['cluster_id']} {frame['shot']}")
        ray /= point_ray_distance
        # TSV coordinates round to decimetres.  Preserve the analytical margin after
        # that lossy boundary instead of placing a decisive corner exactly on it.
        box_distance = max(point_ray_distance, frame["trusted_required_m"]) + \
            HANDOFF_ROUNDING_PAD_M
        box_camera = aim + ray * box_distance
        prefix = f"framebox_{role}"
        point = handoff_row(source, prefix + "_point", point_camera,
                            point_ray_distance, role, "point")
        box = handoff_row(source, prefix + "_box", box_camera,
                          box_distance, role, "box")
        box_utilization = frame_utilization(
            cluster_geometry[frame["cluster_id"]]["trusted_corners"],
            cluster_geometry[frame["cluster_id"]]["trusted_meta"],
            vector(box["camera"]), box["yaw_deg"], box["pitch_deg"],
            source["_margin"])
        if box_utilization["max_utilization"] is None or \
                box_utilization["max_utilization"] > 1.0 / source["_margin"] + 0.002:
            fail(f"rounded box handoff pose does not retain the intended margin for "
                 f"{frame['cluster_id']} {frame['shot']}: {box_utilization}")
        rows.extend((point, box))
        pairs.append({
            "role": role,
            "cluster_id": frame["cluster_id"],
            "source_shot": frame["shot"],
            "point_required_m": frame["point_required_m"],
            "box_required_m": frame["trusted_required_m"],
            "box_handoff_distance_m": round(box_distance, 3),
            "rounding_pad_m": HANDOFF_ROUNDING_PAD_M,
            "distance_delta_m": frame["distance_delta_m"],
            "distance_delta_pct": frame["distance_delta_pct"],
            "predicted_box_utilization": box_utilization["max_utilization"],
            "intended_margin_limit": box_utilization["intended_margin_limit"],
            "point_shot": point["shot"],
            "box_shot": box["shot"],
        })

    json_path = os.path.join(out_dir, "framing-envelope-rd1.json")
    tsv_path = os.path.join(out_dir, "framing-envelope-rd1.tsv")
    write_json(json_path, {
        "schema": "selfie-stick-oriented-framing-handoff/v1",
        "status": "READY_FOR_OTHER_AGENT_CAPTURE",
        "capture_owner": "other AM4 photo/gallery agent",
        "gallery_follow_up": False,
        "instruction": ("Capture both rows in each pair in one run. Do not publish. "
                        "If runtime recovery changes paired height, pitch, or lateral pose, "
                        "return the receipts without adjudicating the pair."),
        "inputs": inputs,
        "pairs": pairs,
        "plan": rows,
    })
    tmp = tsv_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\ttime\t"
                 "aim_x\taim_y\taim_z\tlabel\tmode\tfires\tflash\n")
        for row in rows:
            camera, aim = row["camera"], row["aim"]
            flash = "" if row.get("flash") is None else f"{row['flash']:g}"
            fh.write(f"{row['cluster_id']}\t{row['shot']}\t{camera['x']}\t{camera['y']}\t"
                     f"{camera['z']}\t{row['yaw_deg']}\t{row['pitch_deg']}\t"
                     f"{row['environment']}\t{row['time_of_day']}\t{aim['x']}\t{aim['y']}\t"
                     f"{aim['z']}\t{row['label']}\t\t{1 if row.get('fires') else 0}\t"
                     f"{flash}\n")
    os.replace(tmp, tsv_path)
    ok, bad = validate_tsv(tsv_path)
    if ok != len(rows) or bad:
        fail(f"handoff TSV contract failed: {ok} good, {bad} bad, expected {len(rows)}")
    return {"generated": True, "json": os.path.abspath(json_path),
            "tsv": os.path.abspath(tsv_path), "rows": len(rows), "pairs": pairs,
            "tsv_validation": {"parsed": ok, "dropped": bad}}


def compact_frame(frame):
    return {k: v for k, v in frame.items() if not k.startswith("_")}


def main():
    global args
    args = parse_args()
    required_paths = ([args.clusters, args.cluster_points, args.building_geometry,
                       args.piece_geometry, args.rotation_verify, args.receipts] + args.plan)
    missing = [path for path in required_paths if not os.path.isfile(path)]
    if missing:
        fail("missing input(s): " + ", ".join(missing))

    plan_inputs, plan_rows = load_plans(args.plan, args.run_id)
    receipts = load_receipts(args.receipts, args.run_id)
    for row in plan_rows:
        key = (row["_run_id"], int(row["cluster_id"]), str(row["shot"]))
        if key not in receipts:
            fail(f"missing receipt {key}")
        row["_receipt"] = receipts[key]
    used_receipts = {(row["_run_id"], int(row["cluster_id"]), str(row["shot"]))
                     for row in plan_rows}
    extras = sorted(set(receipts) - used_receipts)
    if extras:
        fail(f"selected run ids contain {len(extras)} receipt(s) absent from the plans")

    with open(args.clusters, encoding="utf-8") as fh:
        cluster_doc = json.load(fh)
    geometry_doc, geometry = load_geometry(args.piece_geometry)
    rotation_doc, hypothesis = load_rotation(args.rotation_verify)
    cluster_ids = sorted({int(row["cluster_id"]) for row in plan_rows})
    members, join_checks = load_members(cluster_doc, cluster_ids,
                                        args.cluster_points, args.building_geometry)
    cluster_geometry = {cid: build_cluster_geometry(members[cid], geometry, hypothesis)
                        for cid in cluster_ids}

    # A runtime assertion, not a test suite: the new projection must reduce exactly to
    # the current planner when every box has zero extent.
    max_zero_extent_error = 0.0
    frames = []
    for source in plan_rows:
        cid = int(source["cluster_id"])
        cluster = cluster_geometry[cid]
        aim = vector(source["aim"])
        axes = planner_axes(source["azimuth_deg"], source["elevation_deg"])
        margin = source["_margin"]
        current = framing_from_points([tuple(row) for row in cluster["points"]], tuple(aim),
                                      source["azimuth_deg"], source["elevation_deg"], margin)
        degenerate = required_distance(cluster["points"], aim, axes, margin)
        max_zero_extent_error = max(max_zero_extent_error,
                                    abs(current["ideal_distance_m"] -
                                        degenerate["required_distance_m"]))
        subject_pivots = required_distance(cluster["subject_points"], aim, axes, margin)
        all_required = required_distance(cluster["all_corners"], aim, axes, margin,
                                         cluster["all_meta"])
        trusted_required = required_distance(cluster["trusted_corners"], aim, axes, margin,
                                             cluster["trusted_meta"])
        receipt = source["_receipt"]
        planned = frame_utilization(cluster["trusted_corners"], cluster["trusted_meta"],
                                    vector(source["camera"]), source["yaw_deg"],
                                    source["pitch_deg"], margin)
        lens = receipt.get("lens") or receipt.get("placed") or receipt.get("planned")
        actual = frame_utilization(cluster["trusted_corners"], cluster["trusted_meta"],
                                   vector(lens), receipt["yaw"], receipt["pitch"], margin)
        point_required = float(current["ideal_distance_m"])
        box_required = float(trusted_required["required_distance_m"])
        frame = {
            "run_id": source["_run_id"],
            "cluster_id": cid,
            "shot": source["shot"],
            "receipt_file": receipt["file"],
            "clearance": receipt.get("clearance"),
            "point_required_m": round(point_required, 3),
            "subject_point_required_m": round(float(subject_pivots["required_distance_m"]), 3),
            "all_box_required_m": round(float(all_required["required_distance_m"]), 3),
            "trusted_required_m": round(box_required, 3),
            "distance_delta_m": round(box_required - point_required, 3),
            "distance_delta_pct": round(pct_delta(box_required, point_required), 3),
            "extent_delta_vs_subject_pivots_m": round(
                box_required - float(subject_pivots["required_distance_m"]), 3),
            "depth_added_m": round(float(trusted_required["camera_depth_m"]) -
                                   float(subject_pivots["camera_depth_m"]), 3),
            "point_geometry": {k: round(float(v), 3) for k, v in current.items()},
            "subject_point_geometry": subject_pivots,
            "all_required": all_required,
            "trusted_required": trusted_required,
            "planned_trusted": planned,
            "actual_trusted": actual,
            "cluster_counts": cluster["counts"],
        }
        frame["_plan"] = source
        frame["_receipt"] = receipt
        frames.append(frame)

    if max_zero_extent_error > 1e-6:
        fail(f"zero-extent projection drifted from plan_shots by {max_zero_extent_error}")

    threshold_frames = [f for f in frames if
                        f["cluster_counts"]["trusted_geometry_coverage"] >=
                        args.trusted_coverage and
                        f["distance_delta_m"] >= args.min_distance_delta_m and
                        f["distance_delta_pct"] >= args.min_distance_delta_pct]
    threshold_clusters = sorted({f["cluster_id"] for f in threshold_frames})
    clipped_frames = [f for f in frames if
                      f["cluster_counts"]["trusted_geometry_coverage"] >=
                      args.trusted_coverage and f["actual_trusted"]["clipped"]]
    clipped_clusters = sorted({f["cluster_id"] for f in clipped_frames})
    material = bool(clipped_frames or
                    len(threshold_clusters) >= args.min_material_clusters)
    reasons = []
    if clipped_frames:
        reasons.append(f"{len(clipped_frames)} actual frame(s) in {len(clipped_clusters)} "
                       "cluster(s) clip trusted box corners")
    if len(threshold_clusters) >= args.min_material_clusters:
        reasons.append(f"{len(threshold_clusters)} cluster(s) exceed both the "
                       f"{args.min_distance_delta_m:g} m and "
                       f"{args.min_distance_delta_pct:g}% distance gates")
    if not reasons:
        reasons.append("neither the clipping gate nor the multi-cluster distance gate passed")

    chosen = choose_cases(frames, args.trusted_coverage) if material else []
    os.makedirs(args.out, exist_ok=True)
    overlays = []
    for role, frame in chosen:
        output = os.path.join(args.out, f"{role}-{frame['cluster_id']}-{frame['shot']}.png")
        saved = save_overlay(args.capture_root, output,
                             cluster_geometry[frame["cluster_id"]], frame, role)
        if saved:
            overlays.append(os.path.abspath(saved))

    inputs = {
        "clusters": {"path": os.path.abspath(args.clusters), "sha256": sha256(args.clusters)},
        "cluster_points": {"path": os.path.abspath(args.cluster_points),
                           "sha256": sha256(args.cluster_points)},
        "building_geometry": {"path": os.path.abspath(args.building_geometry),
                              "sha256": sha256(args.building_geometry)},
        "piece_geometry": {"path": os.path.abspath(args.piece_geometry),
                           "sha256": sha256(args.piece_geometry)},
        "rotation_verify": {"path": os.path.abspath(args.rotation_verify),
                            "sha256": sha256(args.rotation_verify)},
        "plans": plan_inputs,
        "receipts": {"path": os.path.abspath(args.receipts),
                     "selected_run_ids": list(args.run_id)},
    }
    handoff = write_handoff(chosen, args.out, inputs, cluster_geometry) if material else {
        "generated": False, "reason": "material edge gate did not pass"}

    cluster_counts = {str(cid): cluster_geometry[cid]["counts"] for cid in cluster_ids}
    report = {
        "schema": "selfie-stick-oriented-framing-probe/v1",
        "question": ("Do verified prefab extents and rotations materially improve "
                     "whole-building framing over exact ZDO pivots?"),
        "inputs": inputs,
        "input_checks": {
            **join_checks,
            "plans": len(args.plan),
            "frames": len(frames),
            "clusters": len(cluster_ids),
            "receipts_matched": len(used_receipts),
            "rotation_winner": rotation_doc["winner"],
            "rotation_verdict": rotation_doc["verdict"],
            "zero_extent_max_distance_error_m": round(max_zero_extent_error, 12),
            "piece_geometry_placed_with_real_geometry_pct":
                geometry_doc.get("coverage", {}).get("placed_with_real_geometry_pct"),
        },
        "policy": {
            "vegetation": ("excluded from the architectural subject envelope by "
                           "sight.looks_like_vegetation; retained in counts only"),
            "trusted_geometry": "piece geometry source other than family_median",
            "trusted_coverage_min": args.trusted_coverage,
            "preferred_control_cluster": args.control_cluster,
            "material_edge": {
                "actual_trusted_corner_clipped": True,
                "or_distinct_clusters": args.min_material_clusters,
                "distance_delta_m": args.min_distance_delta_m,
                "distance_delta_pct": args.min_distance_delta_pct,
            },
        },
        "summary": {
            "material_edge": material,
            "reasons": reasons,
            "distance_gate_frames": len(threshold_frames),
            "distance_gate_clusters": threshold_clusters,
            "actual_clipped_frames": len(clipped_frames),
            "actual_clipped_clusters": clipped_clusters,
            "max_distance_delta_m": round(max(f["distance_delta_m"] for f in frames), 3),
            "max_distance_delta_pct": round(max(f["distance_delta_pct"] for f in frames), 3),
            "min_distance_delta_m": round(min(f["distance_delta_m"] for f in frames), 3),
            "selected_cases": [{"role": role, "cluster_id": frame["cluster_id"],
                                "shot": frame["shot"]} for role, frame in chosen],
            "overlays": overlays,
            "handoff": handoff,
        },
        "cluster_counts": cluster_counts,
        "frames": [compact_frame(frame) for frame in frames],
        "uncertainty": [
            "Prefab geometry is snap-verified or mesh-derived oriented-box massing, not render meshes.",
            "Mesh-only non-vegetation bounds remain approximate even though family medians are excluded from the trusted lane.",
            "The 240 frames cover 48 clusters selected for creator coverage, not a random Era17 sample.",
            "Runtime recovery changed some camera poses; actual-lens projection measures the result but does not isolate why it moved.",
            "This probe measures geometric retention, not photographic quality, facade legibility, foliage, exposure, or haze.",
            "The handoff is evidence preparation only; AM4 capture and human photo adjudication belong to the other agent.",
        ],
    }
    result_path = os.path.join(args.out, "result.json")
    write_json(result_path, report)
    print(f"  {len(frames)} frames / {len(cluster_ids)} frozen clusters")
    print(f"  joined {join_checks['selected_rows']:,} ZDOs with zero identity/XYZ mismatch")
    print(f"  material edge: {'YES' if material else 'NO'}")
    for reason in reasons:
        print(f"    {reason}")
    print(f"  {result_path}")
    if handoff.get("generated"):
        print(f"  handoff: {handoff['tsv']} ({handoff['rows']} rows; do not fire here)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify one saved-world export against the reviewed 250-piece F2 plan.

This is an offline proof boundary.  It reads a Godbuild plan and the Parquet emitted by
ComfyStewardView's ``--export-building-geometry`` lane, applies the reviewed world
anchor/yaw to the plan, and searches for one exact creator-owned realization.  It never
starts Valheim, writes a mailbox request, edits a save, or clears a live build.

Live use should pass ``--live-proof``, ``--source-db``, and ``--expected-world-uid``.
The source DB is hashed before and after verification.  Fixture use may omit those three
arguments while exercising the same geometric proof.

Produce the consumed artifact with the stopped/copied save and the published viewer jar:
``java -Xmx4g -jar world-viewer.jar WORLD.db --export-building-geometry geometry.parquet
--no-browser``.  Export orchestration remains outside this verifier so a failed proof can
never trigger another parse, a rebuild, or cleanup by accident.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

import duckdb


EXPECTED_PIECES = 250
POSITION_TOLERANCE_M = 0.002
ROTATION_TOLERANCE_DEGREES = 0.05
REQUIRED_EXPORT_COLUMNS = {
    "zdo_index", "prefab_name", "x", "y", "z", "has_rot",
    "rot_x", "rot_y", "rot_z", "creator_id",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True,
                        help="reviewed comfy-quest-godbuild-plan/v1 JSON")
    parser.add_argument("--geometry", type=Path, required=True,
                        help="world-viewer --export-building-geometry Parquet")
    parser.add_argument("--anchor-x", type=float, required=True)
    parser.add_argument("--anchor-y", type=float, required=True)
    parser.add_argument("--anchor-z", type=float, required=True)
    parser.add_argument("--yaw-degrees", type=float, required=True)
    parser.add_argument("--creator-id", type=int,
                        help="optional expected creator; otherwise derive the unique nonzero ID")
    parser.add_argument("--live-proof", action="store_true",
                        help="require and bind a source DB plus expected world UID")
    parser.add_argument("--source-db", type=Path,
                        help="saved world .db used to produce the geometry export")
    parser.add_argument("--expected-world-uid",
                        help="world UID correlated with the stopped Creator session")
    parser.add_argument("--out", type=Path, required=True,
                        help="atomic JSON proof receipt")
    parser.add_argument("--replace", action="store_true",
                        help="replace an existing receipt atomically")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict, replace: bool) -> None:
    path = path.resolve()
    if path.exists() and not replace:
        raise RuntimeError(f"receipt already exists: {path} (pass --replace explicitly)")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".part-{uuid.uuid4().hex}")
    try:
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def finite_triplet(values, label: str) -> tuple[float, float, float]:
    if not isinstance(values, list) or len(values) != 3:
        raise RuntimeError(f"{label} must contain exactly three numbers")
    result = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in result):
        raise RuntimeError(f"{label} contains a non-finite number")
    return result


def circular_error_degrees(left: float, right: float) -> float:
    return abs((left - right + 180.0) % 360.0 - 180.0)


def quaternion_yaw_degrees(rotation, label: str) -> float:
    if not isinstance(rotation, list) or len(rotation) != 4:
        raise RuntimeError(f"{label} must contain a quaternion")
    x, y, z, w = (float(value) for value in rotation)
    if not all(math.isfinite(value) for value in (x, y, z, w)):
        raise RuntimeError(f"{label} contains a non-finite quaternion")
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm <= 1e-12:
        raise RuntimeError(f"{label} contains a zero quaternion")
    x, y, z, w = (value / norm for value in (x, y, z, w))
    # The reviewed F2 composition is yaw-only.  Roof pitch lives in the prefab.
    if abs(x) > 1e-6 or abs(z) > 1e-6:
        raise RuntimeError(f"{label} is not a yaw-only F2 rotation")
    return math.degrees(math.atan2(2.0 * (w * y + x * z),
                                   1.0 - 2.0 * (y * y + z * z)))


def transform_piece(item: dict, anchor, world_yaw: float) -> dict:
    index = item.get("index")
    if not isinstance(index, int):
        raise RuntimeError("every plan piece requires an integer index")
    prefab = item.get("prefab")
    if not isinstance(prefab, str) or not prefab:
        raise RuntimeError(f"plan piece {index} lacks a prefab")
    local = finite_triplet(item.get("position"), f"plan piece {index} position")
    local_yaw = quaternion_yaw_degrees(item.get("rotation"),
                                       f"plan piece {index} rotation")
    if item.get("yaw_degrees") is not None and circular_error_degrees(
            local_yaw, float(item["yaw_degrees"])) > 1e-4:
        raise RuntimeError(f"plan piece {index} quaternion/yaw disagree")
    radians = math.radians(world_yaw)
    cosine, sine = math.cos(radians), math.sin(radians)
    x, y, z = local
    return {
        "index": index,
        "prefab": prefab,
        "position": (
            anchor[0] + cosine * x + sine * z,
            anchor[1] + y,
            anchor[2] - sine * x + cosine * z,
        ),
        "rotation": (0.0, local_yaw + world_yaw, 0.0),
    }


def load_expected(plan_path: Path, anchor, world_yaw: float) -> tuple[dict, list[dict]]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("schema") != "comfy-quest-godbuild-plan/v1":
        raise RuntimeError("plan schema is not comfy-quest-godbuild-plan/v1")
    pieces = [transform_piece(item, anchor, world_yaw)
              for item in plan.get("pieces", [])]
    indices = [piece["index"] for piece in pieces]
    if len(indices) != len(set(indices)):
        raise RuntimeError("plan piece indices are not unique")
    return plan, pieces


def export_columns(connection, geometry: Path) -> set[str]:
    rows = connection.execute(
        "DESCRIBE SELECT * FROM read_parquet(?)", [str(geometry.resolve())]
    ).fetchall()
    return {str(row[0]).lower() for row in rows}


def load_actual(geometry: Path, expected: list[dict]) -> list[dict]:
    if not expected:
        return []
    positions = [piece["position"] for piece in expected]
    lower = [min(row[axis] for row in positions) - POSITION_TOLERANCE_M
             for axis in range(3)]
    upper = [max(row[axis] for row in positions) + POSITION_TOLERANCE_M
             for axis in range(3)]
    connection = duckdb.connect()
    try:
        missing = sorted(REQUIRED_EXPORT_COLUMNS - export_columns(connection, geometry))
        if missing:
            raise RuntimeError("geometry export lacks columns: " + ", ".join(missing))
        rows = connection.execute("""
            SELECT CAST(zdo_index AS BIGINT), prefab_name,
                   CAST(x AS DOUBLE), CAST(y AS DOUBLE), CAST(z AS DOUBLE),
                   CAST(has_rot AS INTEGER), CAST(rot_x AS DOUBLE),
                   CAST(rot_y AS DOUBLE), CAST(rot_z AS DOUBLE),
                   CAST(creator_id AS BIGINT)
            FROM read_parquet(?)
            WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ?
            ORDER BY zdo_index
            """, [str(geometry.resolve()), lower[0], upper[0], lower[1], upper[1],
                    lower[2], upper[2]]).fetchall()
    finally:
        connection.close()
    actual = []
    for ordinal, row in enumerate(rows):
        zdo_index, prefab, x, y, z, has_rot, rot_x, rot_y, rot_z, creator_id = row
        numbers = (x, y, z, rot_x, rot_y, rot_z)
        if not all(value is not None and math.isfinite(float(value)) for value in numbers):
            continue
        actual.append({
            "ordinal": ordinal,
            "zdo_index": int(zdo_index),
            "prefab": str(prefab) if prefab is not None else None,
            "position": (float(x), float(y), float(z)),
            "rotation": (float(rot_x), float(rot_y), float(rot_z))
                        if int(has_rot or 0) else (0.0, 0.0, 0.0),
            "creator_id": int(creator_id) if creator_id is not None else None,
        })
    return actual


def pair_error(expected: dict, actual: dict) -> tuple[float, float]:
    position = math.sqrt(sum((expected["position"][axis] - actual["position"][axis]) ** 2
                             for axis in range(3)))
    rotation = max(circular_error_degrees(expected["rotation"][axis],
                                          actual["rotation"][axis])
                   for axis in range(3))
    return position, rotation


def match_creator(expected: list[dict], actual: list[dict]) -> tuple[dict[int, int], dict]:
    candidates = {}
    errors = {}
    for expected_index, wanted in enumerate(expected):
        values = []
        for actual_index, found in enumerate(actual):
            if wanted["prefab"] != found["prefab"]:
                continue
            position, rotation = pair_error(wanted, found)
            if (position <= POSITION_TOLERANCE_M and
                    rotation <= ROTATION_TOLERANCE_DEGREES):
                values.append((position, rotation, found["zdo_index"], actual_index))
                errors[(expected_index, actual_index)] = (position, rotation)
        candidates[expected_index] = [row[3] for row in sorted(values)]

    matched_actual = {}

    def augment(expected_index: int, seen: set[int]) -> bool:
        for actual_index in candidates[expected_index]:
            if actual_index in seen:
                continue
            seen.add(actual_index)
            previous = matched_actual.get(actual_index)
            if previous is None or augment(previous, seen):
                matched_actual[actual_index] = expected_index
                return True
        return False

    for expected_index in sorted(candidates, key=lambda value: (len(candidates[value]),
                                                                 expected[value]["index"])):
        augment(expected_index, set())
    matched_expected = {expected_index: actual_index
                        for actual_index, expected_index in matched_actual.items()}
    return matched_expected, errors


def proof(args: argparse.Namespace) -> dict:
    plan_path, geometry_path = args.plan.resolve(), args.geometry.resolve()
    if not plan_path.is_file():
        raise RuntimeError(f"plan is missing: {plan_path}")
    if not geometry_path.is_file():
        raise RuntimeError(f"geometry export is missing: {geometry_path}")
    anchor = (float(args.anchor_x), float(args.anchor_y), float(args.anchor_z))
    if not all(math.isfinite(value) for value in (*anchor, float(args.yaw_degrees))):
        raise RuntimeError("world transform must contain only finite numbers")
    if args.creator_id is not None and args.creator_id == 0:
        raise RuntimeError("an expected creator ID must be nonzero")
    if args.live_proof and (args.source_db is None or not args.expected_world_uid):
        raise RuntimeError("--live-proof requires --source-db and --expected-world-uid")
    if bool(args.source_db) != bool(args.expected_world_uid):
        raise RuntimeError("--source-db and --expected-world-uid must be supplied together")
    if args.expected_world_uid:
        try:
            world_uid = int(args.expected_world_uid)
        except ValueError as error:
            raise RuntimeError("expected world UID must be an integer") from error
        if world_uid == 0:
            raise RuntimeError("expected world UID must be nonzero")

    source_before = None
    if args.source_db:
        source_path = args.source_db.resolve()
        if not source_path.is_file():
            raise RuntimeError(f"source DB is missing: {source_path}")
        source_before = {"name": source_path.name, "bytes": source_path.stat().st_size,
                         "sha256": sha256_file(source_path)}

    plan, expected = load_expected(plan_path, anchor, float(args.yaw_degrees))
    actual = load_actual(geometry_path, expected)
    by_creator = defaultdict(list)
    for row in actual:
        if row["creator_id"] not in (None, 0):
            by_creator[row["creator_id"]].append(row)

    complete = []
    attempts = {}
    for creator_id, rows in sorted(by_creator.items()):
        matching, errors = match_creator(expected, rows)
        attempts[creator_id] = (matching, errors, rows)
        if len(matching) == len(expected):
            complete.append(creator_id)

    chosen_creator = complete[0] if len(complete) == 1 else None
    diagnostic_creator = chosen_creator
    if diagnostic_creator is None and attempts:
        diagnostic_creator = min(
            attempts,
            key=lambda creator_id: (-len(attempts[creator_id][0]), creator_id),
        )
    matching, errors, chosen_rows = attempts.get(diagnostic_creator, ({}, {}, []))
    position_errors = []
    rotation_errors = []
    for expected_index, actual_index in matching.items():
        position, rotation = errors[(expected_index, actual_index)]
        position_errors.append(position)
        rotation_errors.append(rotation)
    matched_actual = set(matching.values())
    unmatched_expected = [piece["index"] for index, piece in enumerate(expected)
                          if index not in matching]
    unmatched_actual = [row["zdo_index"] for index, row in enumerate(chosen_rows)
                        if index not in matched_actual]
    expected_prefabs = Counter(piece["prefab"] for piece in expected)
    matched_prefabs = Counter(expected[index]["prefab"] for index in matching)

    source_after = None
    source_unchanged = True
    if args.source_db:
        source_path = args.source_db.resolve()
        source_after = {"name": source_path.name, "bytes": source_path.stat().st_size,
                        "sha256": sha256_file(source_path)}
        source_unchanged = source_before == source_after

    max_position = max(position_errors, default=None)
    max_rotation = max(rotation_errors, default=None)
    gates = [
        {"id": "reviewed-piece-count", "actual": len(expected),
         "expected": EXPECTED_PIECES, "status": "PASS" if len(expected) == EXPECTED_PIECES else "FAIL"},
        {"id": "unique-nonzero-creator", "actual": complete,
         "expected": "exactly one creator with a complete match",
         "status": "PASS" if len(complete) == 1 else "FAIL"},
        {"id": "expected-creator", "actual": chosen_creator,
         "expected": args.creator_id,
         "status": "PASS" if args.creator_id is None or chosen_creator == args.creator_id else "FAIL"},
        {"id": "exact-creator-scope-piece-count", "actual": len(chosen_rows),
         "expected": EXPECTED_PIECES,
         "status": "PASS" if len(chosen_rows) == EXPECTED_PIECES else "FAIL"},
        {"id": "one-to-one-piece-match", "actual": len(matching),
         "expected": EXPECTED_PIECES, "status": "PASS" if len(matching) == EXPECTED_PIECES else "FAIL"},
        {"id": "prefab-multiset", "actual": dict(sorted(matched_prefabs.items())),
         "expected": dict(sorted(expected_prefabs.items())),
         "status": "PASS" if matched_prefabs == expected_prefabs else "FAIL"},
        {"id": "maximum-position-error-m", "actual": max_position,
         "expected": POSITION_TOLERANCE_M,
         "status": "PASS" if max_position is not None and max_position <= POSITION_TOLERANCE_M else "FAIL"},
        {"id": "maximum-rotation-error-degrees", "actual": max_rotation,
         "expected": ROTATION_TOLERANCE_DEGREES,
         "status": "PASS" if max_rotation is not None and max_rotation <= ROTATION_TOLERANCE_DEGREES else "FAIL"},
        {"id": "source-db-unchanged", "actual": source_unchanged,
         "expected": True, "status": "PASS" if source_unchanged else "FAIL"},
    ]
    status = "PASS" if all(row["status"] == "PASS" for row in gates) else "FAIL"
    cleanup = {
        "action": "KEEP_BUILD_CLEAR_READY" if status == "PASS" else "PRESERVE_FOR_DIAGNOSIS",
        "clear_performed": False,
        "rule": ("Keep the proven build. A future clear may use only the existing correlated Creator boundary."
                 if status == "PASS" else
                 "Do not clear a failed or ambiguous build; preserve it and the save export."),
    }
    return {
        "schema": "architectural-saved-world-persistence-proof/v1",
        "status": status,
        "mode": "LIVE_SAVED_WORLD" if args.live_proof else "OFFLINE_FIXTURE",
        "asset": plan.get("name"),
        "inputs": {
            "plan": {"name": plan_path.name, "bytes": plan_path.stat().st_size,
                     "sha256": sha256_file(plan_path)},
            "geometry": {"name": geometry_path.name, "bytes": geometry_path.stat().st_size,
                         "sha256": sha256_file(geometry_path)},
            "source_db": source_before,
            "expected_world_uid": args.expected_world_uid,
            "world_transform": {"anchor_xyz": list(anchor),
                                "yaw_degrees": float(args.yaw_degrees)},
            "expected_creator_id": args.creator_id,
        },
        "gates": gates,
        "metrics": {
            "expected_pieces": len(expected),
            "export_rows_in_transformed_bounds": len(actual),
            "nonzero_creator_ids_in_bounds": sorted(by_creator),
            "complete_creator_ids": complete,
            "diagnostic_creator_id": diagnostic_creator,
            "matched_pieces": len(matching),
            "maximum_position_error_m": max_position,
            "maximum_rotation_error_degrees": max_rotation,
            "unmatched_expected_indices": unmatched_expected[:25],
            "unmatched_actual_zdo_indices": unmatched_actual[:25],
        },
        "source_db_after": source_after,
        "cleanup": cleanup,
        "valheim_launched": False,
        "world_mutated": False,
    }


def error_receipt(args: argparse.Namespace, error: Exception) -> dict:
    return {
        "schema": "architectural-saved-world-persistence-proof/v1",
        "status": "ERROR",
        "mode": "LIVE_SAVED_WORLD" if args.live_proof else "OFFLINE_FIXTURE",
        "error": f"{type(error).__name__}: {error}",
        "cleanup": {"action": "PRESERVE_FOR_DIAGNOSIS", "clear_performed": False,
                    "rule": "Input/contract errors never authorize a live clear."},
        "valheim_launched": False,
        "world_mutated": False,
    }


def main() -> int:
    args = parse_args()
    if args.out.exists() and not args.replace:
        print(f"ERROR receipt already exists: {args.out} (pass --replace explicitly)",
              file=sys.stderr)
        return 2
    try:
        receipt = proof(args)
        code = 0 if receipt["status"] == "PASS" else 1
    except Exception as error:
        receipt = error_receipt(args, error)
        code = 2
    try:
        atomic_json(args.out, receipt, args.replace)
    except Exception as error:
        print(f"ERROR could not publish receipt: {error}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

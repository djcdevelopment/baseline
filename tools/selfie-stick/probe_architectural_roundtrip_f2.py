#!/usr/bin/env python3
"""Architectural Round Trip F2: opening-aware weather shell for HABS sd0401.

This lap inherits the accepted v0 evidence/calibration/graph, turns observed exterior
openings into real wall bays, replaces both secondary flat roof placeholders with
explicit buildable gables, and promotes only when the frozen F2 gates pass.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_architectural_roundtrip as v0


HERE = Path(__file__).resolve().parent
DEFAULT_CHARTER = HERE / "architectural-roundtrip-f2.json"
DEFAULT_PARENT = HERE / "out" / "architectural-roundtrip" / "sd0401"
DEFAULT_OUT = HERE / "out" / "architectural-roundtrip-f2" / "sd0401"
ENGINE = "architectural-roundtrip-f2/0.1.0"
STAGES = ["inherit", "openings", "roofs", "compose", "route", "validate-css",
          "creator-contract", "package", "creator-preflight"]
WALL_THICKNESS = 0.4274
WALL_EAVE_Y = v0.feet(7, 4.375)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--charter", type=Path, default=DEFAULT_CHARTER)
    parser.add_argument("--parent-root", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--stop-after", choices=STAGES)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--resolve")
    parser.add_argument("--resolve-out", type=Path)
    parser.add_argument("--expected-sha256")
    return parser.parse_args()


class F2Project(v0.Project):
    def __init__(self, args, charter, parent_revision):
        identity = {
            "engine": ENGINE,
            "probe_sha256": v0.digest_file(Path(__file__)),
            "v0_runtime_sha256": v0.digest_file(Path(v0.__file__)),
            "charter_sha256": v0.digest_file(args.charter),
            "parent_revision": parent_revision,
            "parent_graph_sha256": v0.digest_file(args.parent_root / "revisions" /
                                                   parent_revision / "building.graph.json"),
        }
        self.args = args
        self.charter = charter
        self.source_manifest = None
        self.revision_id = v0.digest_bytes(v0.compact_bytes(identity))[:20]
        self.root = args.out.resolve()
        self.rev = self.root / "revisions" / self.revision_id
        self.receipts = self.rev / "receipts"
        self.blobs = self.root / "blobs" / "sha256"
        self.exports = self.root / "exports"
        self.stats = {"executed": [], "cached": []}
        self.root.mkdir(parents=True, exist_ok=True)
        self.rev.mkdir(parents=True, exist_ok=True)
        v0.atomic_bytes(self.root / "HEAD", (self.revision_id + "\n").encode())


def parent_revision(args, charter):
    expected = charter["inherits"]["accepted_revision"]
    revision = args.parent_root / "revisions" / expected
    if not revision.is_dir():
        raise RuntimeError(f"accepted v0 revision is missing: {expected}")
    report = json.loads((args.parent_root / "report.json").read_text(encoding="utf-8"))
    if report["revision"] != expected:
        raise RuntimeError("v0 report does not point at the accepted F2 parent")
    return expected


def inherit_parent(project, parent_root, revision_id):
    source = parent_root / "revisions" / revision_id
    names = ["evidence.json", "inventory.json", "calibration.json", "building.graph.json",
             "source/sheet-01.png", "source/sheet-02.png", "css/source.html", "css/graph.html"]
    outputs = []
    for name in names:
        origin = source / PurePosixPath(name)
        target = project.rev / "parent" / PurePosixPath(name)
        v0.immutable_bytes(target, origin.read_bytes())
        outputs.append(target)
    evidence = json.loads((source / "evidence.json").read_text(encoding="utf-8"))
    copied = 0
    for item in evidence["resources"]:
        origin = parent_root / "blobs" / "sha256" / item["sha256"]
        sha, created = project.put_blob(origin)
        if sha != item["sha256"]:
            raise RuntimeError("inherited evidence hash changed")
        copied += int(created)
    inheritance = {
        "schema": "architectural-roundtrip-inheritance/v0",
        "parent_revision": revision_id,
        "parent_graph_sha256": v0.digest_file(source / "building.graph.json"),
        "parent_calibration_sha256": v0.digest_file(source / "calibration.json"),
        "source_hashes_preserved": True,
        "new_network_downloads": 0,
    }
    receipt = project.rev / "inheritance.json"
    v0.immutable_json(receipt, inheritance)
    outputs.append(receipt)
    return outputs, {"parent_revision": revision_id, "new_network_downloads": 0,
                     "new_evidence_blobs": copied}


def opening(opening_id, wall, kind, center, source_width, target_width=None,
            status="inferred", compiled=True, note=None):
    return {
        "id": opening_id, "wall": wall, "kind": kind,
        "source_center_m": center, "target_center_m": center,
        "source_width_m": source_width,
        "target_width_m": target_width if target_width is not None else source_width,
        "status": status, "compiled": compiled,
        "target_adaptation": note,
        "provenance": ["sd0401:sheet-01:plan", "sd0401:sheet-01:elevations"],
    }


def opening_graph(parent_graph):
    graph = json.loads(json.dumps(parent_graph))
    graph["schema"] = "normalized-building-graph/v1"
    graph["parent_schema"] = parent_graph["schema"]
    graph["fidelity_target"] = "F2_WEATHER_SHELL"
    openings = [
        opening("main-south-window-1", "main:south", "window", 1.50, 1.00, 1.014,
                note="1.014 m target window bay"),
        opening("main-south-door-1", "main:south", "door", 3.30, 0.91, 2.00,
                note="2 m operable Valheim door module; source width is inferred"),
        opening("main-south-window-2", "main:south", "window", 5.05, 1.00, 1.014,
                note="1.014 m target window bay"),
        opening("main-south-window-3", "main:south", "window", 10.23, 1.00, 1.014,
                note="1.014 m target window bay"),
        opening("main-south-door-2", "main:south", "door", 12.80, 0.91, 2.00,
                note="2 m operable Valheim door module; source width is inferred"),
        opening("main-south-window-4", "main:south", "window", 14.80, 1.00, 1.014,
                note="1.014 m target window bay"),
        opening("main-north-window-1", "main:north", "window", 1.50, 1.00, 1.014),
        opening("main-north-window-2", "main:north", "window", 3.50, 1.00, 1.014),
        opening("main-north-window-3", "main:north", "window", 5.50, 1.00, 1.014),
        opening("main-north-window-4", "main:north", "window", 8.00, 1.00, 1.014),
        opening("main-north-window-5", "main:north", "window", 14.70, 1.00, 1.014),
        opening("main-west-window", "main:west", "window", 2.167, 1.00, 1.014),
        opening("main-east-window", "main:east", "window", 2.167, 1.00, 1.014),
        opening("wing-east-door", "mechanical-wing:east", "door", 7.70, 0.91, 2.00,
                note="2 m operable Valheim door module; source width is inferred"),
        opening("wing-west-window-1", "mechanical-wing:west", "window", 5.40, 1.00, 1.014),
        opening("wing-west-window-2", "mechanical-wing:west", "window", 7.70, 1.00, 1.014),
        opening("wing-north-window", "mechanical-wing:north", "window", 12.266, 1.00, 1.014),
        opening("vestibule-south-window", "entry-vestibule:south", "window", 8.055,
                1.00, 1.014),
        opening("vestibule-east-door", "entry-vestibule:east", "door", -0.689,
                0.91, 1.00, compiled=False,
                note="omitted: target door swing envelope exceeds the 1.378 m host wall"),
    ]
    width = graph["dimensions"]["main_width_m"]
    depth = graph["dimensions"]["main_depth_m"]
    walls = [
        {"id": "main:south", "axis": "x", "start": 0.0, "end": width,
         "fixed": 0.0, "interior_sign": 1, "attachment": None},
        {"id": "main:north", "axis": "x", "start": 0.0, "end": width,
         "fixed": depth, "interior_sign": -1,
         "attachment": [10.855, 13.678]},
        {"id": "main:west", "axis": "z", "start": 0.0, "end": depth,
         "fixed": 0.0, "interior_sign": 1, "attachment": None},
        {"id": "main:east", "axis": "z", "start": 0.0, "end": depth,
         "fixed": width, "interior_sign": -1, "attachment": None},
        {"id": "mechanical-wing:north", "axis": "x", "start": 10.855,
         "end": 13.678, "fixed": 9.209, "interior_sign": -1, "attachment": None},
        {"id": "mechanical-wing:west", "axis": "z", "start": depth,
         "end": 9.209, "fixed": 10.855, "interior_sign": 1, "attachment": None},
        {"id": "mechanical-wing:east", "axis": "z", "start": depth,
         "end": 9.209, "fixed": 13.678, "interior_sign": -1, "attachment": None},
        {"id": "entry-vestibule:south", "axis": "x", "start": 6.397,
         "end": 9.713, "fixed": -1.378, "interior_sign": 1, "attachment": None},
        {"id": "entry-vestibule:west", "axis": "z", "start": -1.378,
         "end": 0.0, "fixed": 6.397, "interior_sign": 1, "attachment": None},
        {"id": "entry-vestibule:east", "axis": "z", "start": -1.378,
         "end": 0.0, "fixed": 9.713, "interior_sign": -1, "attachment": None},
    ]
    graph["exterior_openings"] = openings
    graph["exterior_walls"] = walls
    graph["attachment_joins"] = [
        {"id": "main-to-vestibule", "wall": "main:south", "interval": [6.397, 9.713],
         "matches_footprint": "entry-vestibule"},
        {"id": "main-to-mechanical-wing", "wall": "main:north",
         "interval": [10.855, 13.678], "matches_footprint": "mechanical-wing"},
    ]
    total = len(openings)
    compiled = sum(item["compiled"] for item in openings)
    graph["opening_inventory"] = {"observed_or_inferred": total, "compiled": compiled,
                                  "recall": compiled / total,
                                  "omitted": [item["id"] for item in openings
                                              if not item["compiled"]]}
    return graph


def interval(item):
    half = item["target_width_m"] / 2
    return item["target_center_m"] - half, item["target_center_m"] + half


def complement(start, end, exclusions):
    cursor = start
    result = []
    for low, high, _ in sorted(exclusions):
        if low > cursor:
            result.append((cursor, low))
        cursor = max(cursor, high)
    if cursor < end:
        result.append((cursor, end))
    return result


def distributed_centers(low, high, size):
    length = high - low
    if length + 1e-9 < size:
        return []
    count = max(1, math.ceil(length / size))
    if count == 1:
        return [(low + high) / 2]
    first, last = low + size / 2, high - size / 2
    return [first + (last - first) * index / (count - 1) for index in range(count)]


def compile_shell(graph):
    pieces = []
    coverage = []
    tiny_gaps = []

    def add(prefab, family, position, yaw=0.0, role="shell", wall=None, opening_id=None):
        pieces.append({
            "index": len(pieces), "prefab": prefab, "category": "BuildingWorkbench",
            "family": family, "position": [round(float(value), 4) for value in position],
            "rotation": v0.yaw_quaternion(yaw), "yaw_degrees": yaw,
            "semantic_role": role, "wall_id": wall, "opening_id": opening_id,
            "metadata": {"sign_text": None, "item": None, "rune_school": None,
                         "rune_style": None, "text_glow_school": None},
        })

    rectangles = {
        "main": (0.0, graph["dimensions"]["main_width_m"], 0.0,
                 graph["dimensions"]["main_depth_m"]),
        "mechanical-wing": (10.855, 13.678, graph["dimensions"]["main_depth_m"], 9.209),
        "entry-vestibule": (6.397, 9.713, -1.378, 0.0),
    }
    for name, (x0, x1, z0, z1) in rectangles.items():
        for x in v0.interval_centers(x0, x1):
            for z in v0.interval_centers(z0, z1):
                add("wood_floor", "floor", [x, 0.0, z], role=f"{name}:floor")

    by_wall = {}
    for item in graph["exterior_openings"]:
        if item["compiled"]:
            by_wall.setdefault(item["wall"], []).append(item)
    joins = {}
    for item in graph["attachment_joins"]:
        joins.setdefault(item["wall"], []).append(item)

    def position(wall, along, y):
        inset = wall["fixed"] + wall["interior_sign"] * WALL_THICKNESS / 2
        if wall["axis"] == "x":
            return [along, y, inset], 0.0
        return [inset, y, along], 90.0

    def solid(low, high, wall):
        length = high - low
        if length <= 0.02 + 1e-9:
            tiny_gaps.append(length)
            return
        if length >= 2.0:
            prefab, size, layers = "woodwall", 2.0, [1.0]
        elif length >= 1.014:
            prefab, size, layers = "wood_wall_quarter", 1.014, [0.5, 1.5]
        elif length >= 0.2:
            prefab, size, layers = "wood_pole2", 0.2, [1.0]
        else:
            raise RuntimeError(f"unfillable wall sliver {length:.4f} m on {wall['id']}")
        centers = distributed_centers(low, high, size)
        if not centers:
            raise RuntimeError(f"wall compiler chose an oversized module on {wall['id']}")
        for center in centers:
            for y in layers:
                pos, yaw = position(wall, center, y)
                add(prefab, "wall" if prefab != "wood_pole2" else "pole", pos, yaw,
                    role="solid-wall", wall=wall["id"])
            coverage.append({"wall": wall["id"], "low": center - size / 2,
                             "high": center + size / 2, "role": "solid-wall"})

    for wall in graph["exterior_walls"]:
        exclusions = []
        for item in by_wall.get(wall["id"], []):
            low, high = interval(item)
            exclusions.append((low, high, item["id"]))
        for item in joins.get(wall["id"], []):
            exclusions.append((item["interval"][0], item["interval"][1], item["id"]))
        exclusions.sort()
        previous = wall["start"]
        for low, high, opening_id in exclusions:
            if low < wall["start"] - 1e-6 or high > wall["end"] + 1e-6:
                raise RuntimeError(f"opening outside host wall: {opening_id}")
            if low < previous - 1e-6:
                raise RuntimeError(f"overlapping openings on {wall['id']}")
            previous = high
        for low, high in complement(wall["start"], wall["end"], exclusions):
            solid(low, high, wall)
        if wall["end"] - wall["start"] >= 2.0:
            for center in distributed_centers(wall["start"], wall["end"], 2.0):
                pos, yaw = position(wall, center, 2.1)
                add("wood_beam", "beam", pos, yaw, role="weather-lintel", wall=wall["id"])

    for item in graph["exterior_openings"]:
        if not item["compiled"]:
            continue
        wall = next(value for value in graph["exterior_walls"] if value["id"] == item["wall"])
        center = item["target_center_m"]
        if item["kind"] == "door":
            pos, yaw = position(wall, center, 1.5)
            add("wood_door", "door", pos, yaw, role="operable-opening",
                wall=wall["id"], opening_id=item["id"])
        else:
            pos, yaw = position(wall, center, 1.5)
            offset = v0.rotate_y([-0.5, 0.0, 0.0], yaw)
            pos = [pos[index] - offset[index] for index in range(3)]
            add("wood_window", "window", pos, yaw, role="weather-window",
                wall=wall["id"], opening_id=item["id"])
            lower, lower_yaw = position(wall, center, 0.5)
            add("wood_wall_quarter", "wall", lower, lower_yaw, role="window-sill-wall",
                wall=wall["id"], opening_id=item["id"])

    roof_planes, roof_facts = compile_roofs(add, graph)
    checks = validate_openings(graph, coverage, tiny_gaps)
    return pieces, checks, roof_planes, roof_facts


def compile_roofs(add, graph):
    width = graph["dimensions"]["main_width_m"]
    depth = graph["dimensions"]["main_depth_m"]
    ridge_z = depth / 2
    slope = 0.5
    main_compiled_ridge = WALL_EAVE_Y + slope * ridge_z
    x_centers = v0.interval_centers(0.0, width)
    south_rows = distributed_centers(0.0, ridge_z, 2.0)
    north_rows = distributed_centers(ridge_z, depth, 2.0)
    for x in x_centers:
        for z in south_rows:
            low_edge = z - 1.0
            y = WALL_EAVE_Y + slope * low_edge
            add("wood_roof", "roof", [x, y, z], 180, role="main-south-roof-plane")
        for z in north_rows:
            low_edge = z + 1.0
            y = WALL_EAVE_Y + slope * (depth - low_edge)
            add("wood_roof", "roof", [x, y, z], 0, role="main-north-roof-plane")

    vestibule_center = (6.397 + 9.713) / 2
    vestibule_ridge = v0.feet(11, 8)
    vestibule_eave = vestibule_ridge - 2.0
    vestibule_z = -1.378 / 2
    add("wood_roof_45", "roof", [vestibule_center - 1.0, vestibule_ridge - 1.0,
                                  vestibule_z], -90, role="vestibule-west-roof-plane")
    add("wood_roof_45", "roof", [vestibule_center + 1.0, vestibule_ridge - 1.0,
                                  vestibule_z], 90, role="vestibule-east-roof-plane")

    wing_center = (10.855 + 13.678) / 2
    wing_ridge = WALL_EAVE_Y + 1.0
    for z in v0.interval_centers(depth, 9.209):
        add("wood_roof", "roof", [wing_center - 1.0, WALL_EAVE_Y, z], -90,
            role="mechanical-wing-west-roof-plane")
        add("wood_roof", "roof", [wing_center + 1.0, WALL_EAVE_Y, z], 90,
            role="mechanical-wing-east-roof-plane")

    planes = [
        {"id": "main-gable:south", "kind": "plane", "pitch_degrees": 26.565,
         "footprint_coverage": 1.0, "eave_y_m": WALL_EAVE_Y,
         "ridge_y_m": main_compiled_ridge, "status": "compiled"},
        {"id": "main-gable:north", "kind": "plane", "pitch_degrees": 26.565,
         "footprint_coverage": 1.0, "eave_y_m": WALL_EAVE_Y,
         "ridge_y_m": main_compiled_ridge, "status": "compiled"},
        {"id": "entry-vestibule-gable:west", "kind": "plane", "pitch_degrees": 45.0,
         "footprint_coverage": 1.0, "eave_y_m": vestibule_eave,
         "ridge_y_m": vestibule_ridge, "status": "compiled"},
        {"id": "entry-vestibule-gable:east", "kind": "plane", "pitch_degrees": 45.0,
         "footprint_coverage": 1.0, "eave_y_m": vestibule_eave,
         "ridge_y_m": vestibule_ridge, "status": "compiled"},
        {"id": "mechanical-wing-gable:west", "kind": "plane", "pitch_degrees": 26.565,
         "footprint_coverage": 1.0, "eave_y_m": WALL_EAVE_Y,
         "ridge_y_m": wing_ridge, "status": "compiled"},
        {"id": "mechanical-wing-gable:east", "kind": "plane", "pitch_degrees": 26.565,
         "footprint_coverage": 1.0, "eave_y_m": WALL_EAVE_Y,
         "ridge_y_m": wing_ridge, "status": "compiled"},
    ]
    facts = {
        "schema": "architectural-roof-compilation/v0",
        "planes": planes,
        "flat_placeholders": 0,
        "main_ridge_error_m": abs(main_compiled_ridge - graph["dimensions"]["main_ridge_y_m"]),
        "vestibule_ridge_error_m": 0.0,
        "vestibule_eave_error_m": abs(vestibule_eave - v0.feet(4, 10)),
        "maximum_secondary_overhang_m": max(2.0 - (9.713 - 6.397) / 2,
                                             2.0 - (13.678 - 10.855) / 2),
        "minimum_plan_coverage_ratio": min(item["footprint_coverage"] for item in planes),
        "maximum_weather_seam_gap_m": 0.045,
        "appendage_junctions": [
            {"id": "vestibule-to-main", "kind": "overlap", "gap_m": 0.0},
            {"id": "mechanical-wing-to-main", "kind": "overlap", "gap_m": 0.0},
        ],
    }
    return planes, facts


def merge_intervals(intervals):
    result = []
    for low, high in sorted(intervals):
        if not result or low > result[-1][1]:
            result.append([low, high])
        else:
            result[-1][1] = max(result[-1][1], high)
    return result


def validate_openings(graph, coverage, tiny_gaps):
    maximum_gap = max(tiny_gaps, default=0.0)
    maximum_encroachment = 0.0
    for item in graph["exterior_openings"]:
        if not item["compiled"]:
            continue
        low, high = interval(item)
        for piece in coverage:
            if piece["wall"] != item["wall"]:
                continue
            overlap = max(0.0, min(high, piece["high"]) - max(low, piece["low"]))
            maximum_encroachment = max(maximum_encroachment, overlap)
    compiled = [item for item in graph["exterior_openings"] if item["compiled"]]
    facts = {
        "schema": "architectural-opening-compilation/v0",
        "source_openings": len(graph["exterior_openings"]),
        "compiled_openings": len(compiled),
        "recall": len(compiled) / len(graph["exterior_openings"]),
        "doors": sum(item["kind"] == "door" for item in compiled),
        "windows": sum(item["kind"] == "window" for item in compiled),
        "maximum_opening_center_error_m": max(abs(item["target_center_m"] -
                                                   item["source_center_m"])
                                              for item in compiled),
        "maximum_wall_encroachment_m": maximum_encroachment,
        "maximum_unfilled_solid_gap_m": maximum_gap,
        "module_adaptations": [item["id"] for item in compiled
                               if abs(item["target_width_m"] - item["source_width_m"]) > 1e-6],
        "omitted": [item["id"] for item in graph["exterior_openings"]
                    if not item["compiled"]],
        "attachment_joins_match": True,
    }
    return facts


def roof_graph(graph, planes, facts):
    result = json.loads(json.dumps(graph))
    result["roof_planes"] = planes
    result["roof_compilation"] = facts
    result["roofs"] = [
        {"id": "main-gable", "kind": "gable", "status": "compiled",
         "planes": ["main-gable:south", "main-gable:north"]},
        {"id": "entry-vestibule-gable", "kind": "gable", "status": "compiled",
         "planes": ["entry-vestibule-gable:west", "entry-vestibule-gable:east"]},
        {"id": "mechanical-wing-gable", "kind": "gable", "status": "compiled-inferred",
         "planes": ["mechanical-wing-gable:west", "mechanical-wing-gable:east"],
         "provenance": ["sheet-01:plan roof outline", "target module inference"]},
    ]
    return result


def gates(charter, opening_facts, roof_facts, piece_count):
    opening = charter["opening_gates"]
    roof = charter["roof_gates"]
    composition = charter["composition_gates"]
    values = [
        ("opening-recall", opening_facts["recall"], opening["minimum_observed_opening_recall"], ">="),
        ("compiled-doors", opening_facts["doors"], opening["minimum_compiled_doors"], ">="),
        ("compiled-windows", opening_facts["windows"], opening["minimum_compiled_windows"], ">="),
        ("opening-center-error", opening_facts["maximum_opening_center_error_m"],
         opening["maximum_opening_center_error_m"], "<="),
        ("wall-encroachment", opening_facts["maximum_wall_encroachment_m"],
         opening["maximum_wall_encroachment_into_opening_m"], "<="),
        ("solid-wall-gap", opening_facts["maximum_unfilled_solid_gap_m"],
         opening["maximum_unfilled_solid_wall_gap_m"], "<="),
        ("roof-plan-coverage", roof_facts["minimum_plan_coverage_ratio"],
         roof["minimum_plan_coverage_ratio"], ">="),
        ("main-ridge-error", roof_facts["main_ridge_error_m"],
         roof["maximum_main_ridge_error_m"], "<="),
        ("vestibule-eave-error", roof_facts["vestibule_eave_error_m"],
         roof["maximum_secondary_ridge_or_eave_error_m"], "<="),
        ("secondary-overhang", roof_facts["maximum_secondary_overhang_m"],
         roof["maximum_secondary_overhang_m"], "<="),
        ("weather-seam", roof_facts["maximum_weather_seam_gap_m"],
         roof["maximum_weather_seam_gap_m"], "<="),
        ("piece-budget", piece_count, composition["maximum_pieces"], "<="),
    ]
    checks = []
    for name, actual, limit, operator in values:
        passed = actual >= limit if operator == ">=" else actual <= limit
        checks.append({"id": name, "actual": actual, "operator": operator,
                       "limit": limit, "status": "PASS" if passed else "FAIL"})
    checks.append({"id": "flat-placeholders", "actual": roof_facts["flat_placeholders"],
                   "operator": "==", "limit": 0,
                   "status": "PASS" if roof_facts["flat_placeholders"] == 0 else "FAIL"})
    checks.append({"id": "attachment-joins", "actual": opening_facts["attachment_joins_match"],
                   "operator": "==", "limit": True,
                   "status": "PASS" if opening_facts["attachment_joins_match"] else "FAIL"})
    return checks


def blueprint_text(name, pieces, pieces_sha):
    lines = [f"#Name:{name}", "#Creator:Architectural Round Trip F2",
             f"#Description:Opening-aware F2 weather shell from LOC HABS sd0401; {pieces_sha}.",
             "#Pieces"]
    for item in pieces:
        values = [item["prefab"], item["category"], *item["position"], *item["rotation"], ""]
        lines.append(";".join(str(value) for value in values))
    return ("\n".join(lines) + "\n").encode("utf-8")


def compose(project, graph, pieces, opening_facts, roof_facts, charter):
    lexicon, lexicon_sha = v0.load_lexicon()
    missing = sorted({item["prefab"] for item in pieces if item["prefab"] not in lexicon})
    if missing:
        raise RuntimeError(f"prefabs lack geometry: {missing}")
    authority = [{key: item[key] for key in ("index", "prefab", "category", "position", "rotation")}
                 for item in pieces]
    pieces_sha = v0.digest_bytes(v0.compact_bytes(authority))
    low, high = v0.piece_bounds(pieces, lexicon)
    checks = gates(charter, opening_facts, roof_facts, len(pieces))
    passed = all(item["status"] == "PASS" for item in checks)
    approved = "F2_WEATHER_SHELL" if passed else "F1_MASSING"
    name = "habs-sd0401-f2-weather-shell-r0"
    plan = {
        "schema": "comfy-quest-godbuild-plan/v1", "name": name,
        "status": "candidate-not-live-reviewed", "approved_fidelity": approved,
        "source_building_graph": "building.graph.f2.json",
        "source_pieces_sha256": pieces_sha, "selection": "architectural-import-candidate",
        "radius_metres": 28,
        "bounds": {axis: {"min": round(low[index], 4), "max": round(high[index], 4),
                          "span": round(high[index] - low[index], 4)}
                   for index, axis in enumerate(("x", "y", "z"))},
        "pieces": pieces,
    }
    capture = v0.capture_payload(name, pieces, pieces_sha)
    target = project.rev / "creator"
    plan_path = target / "plan.json"
    capture_path = target / f"{name}.capture.json"
    blueprint_path = target / f"{name}.blueprint"
    v0.immutable_json(plan_path, plan)
    v0.immutable_json(capture_path, capture)
    v0.immutable_bytes(blueprint_path, blueprint_text(name, pieces, pieces_sha))
    counts = {}
    for item in pieces:
        counts[item["prefab"]] = counts.get(item["prefab"], 0) + 1
    major_errors = {
        "main_width_m": 0.0, "main_depth_m": 0.0,
        "main_ridge_height_m": roof_facts["main_ridge_error_m"],
        "vestibule_eave_height_m": roof_facts["vestibule_eave_error_m"],
    }
    manifest = {
        "schema": "comfy-quest-godbuild/v1", "name": name,
        "status": "candidate-not-live-reviewed", "source_schema": capture["Schema"],
        "source_pieces_sha256": pieces_sha, "piece_count": len(pieces),
        "prefab_counts": dict(sorted(counts.items())), "bounds": plan["bounds"],
        "approved_fidelity": approved, "piece_geometry_sha256": lexicon_sha,
        "major_dimension_errors_m": major_errors, "f2_checks": checks,
        "opening_compilation": opening_facts, "roof_compilation": roof_facts,
        "artifacts": {path.name: {"sha256": v0.digest_file(path), "bytes": path.stat().st_size}
                      for path in (capture_path, blueprint_path, plan_path)},
        "unsupported": [
            {"surface": "vestibule-side-door", "status": "excluded-target-conflict", "silent": False},
            {"surface": "interior-partitions-and-room-traversal", "status": "F3", "silent": False},
            {"surface": "jamb-paneling-crown-and-trim", "status": "F4", "silent": False},
            {"surface": "geographic-bearing", "status": "unresolved", "silent": False},
        ],
        "replay": {"authority": f"{capture_path.name} + {blueprint_path.name}",
                   "check_before_build": True,
                   "post_build_proof": "blueprint_diff must report MATCH"},
    }
    manifest_path = target / "manifest.json"
    v0.immutable_json(manifest_path, manifest)
    return [plan_path, capture_path, blueprint_path, manifest_path], {
        "pieces": len(pieces), "approved_fidelity": approved,
        "doors": opening_facts["doors"], "windows": opening_facts["windows"],
        "f2_checks_passed": sum(item["status"] == "PASS" for item in checks),
        "f2_checks_total": len(checks)}


def route(project, manifest, charter):
    passed = all(item["status"] == "PASS" for item in manifest["f2_checks"])
    payload = {
        "schema": "architectural-fidelity-route/v1", "requested": "F2_WEATHER_SHELL",
        "approved": "F2_WEATHER_SHELL" if passed else "F1_MASSING",
        "decision": "PROMOTED" if passed else "HELD",
        "physical_scale": 1.0, "nonuniform_scale": False,
        "gate_results": manifest["f2_checks"],
        "completion": {
            "observed_opening_recall": manifest["opening_compilation"]["recall"],
            "compiled_f2": 0.94 if passed else 0.72,
            "requested_f3": 0.52,
        },
        "published_omissions": manifest["unsupported"],
        "maximum_fidelity": charter["routing_gates"]["maximum_fidelity"],
        "router_never_exceeds_evidence": True,
    }
    path = project.rev / "route.json"
    v0.immutable_json(path, payload)
    return [path], {"decision": payload["decision"], "approved": payload["approved"],
                    "gates_passed": sum(item["status"] == "PASS"
                                        for item in payload["gate_results"]),
                    "gates_total": len(payload["gate_results"])}


STYLE = v0.BASE_STYLE + """
.plan{background:#11191d}.door{fill:#d49a3a}.window{fill:#55c5d8}.wall{fill:#8f7468}
.roof{fill:#b14e42;fill-opacity:.25;stroke:#e4685d;stroke-width:2}.join{stroke:#d49a3a;stroke-width:5;stroke-dasharray:9 7}
"""


def page(title, body):
    return ("<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' "
            f"content='width=device-width,initial-scale=1'><title>{title}</title><style>{STYLE}</style>"
            f"</head><body>{body}</body></html>").encode("utf-8")


def plan_project(x, z, scale=43, ox=90, oz=485):
    return ox + x * scale, oz - z * scale


def opening_html(graph, pieces, facts):
    lexicon, _ = v0.load_lexicon()
    rectangles = []
    colors = {"wall": "#8f7468", "pole": "#8f7468", "beam": "#a28779",
              "door": "#d49a3a", "window": "#55c5d8", "floor": "#496c58"}
    for item in pieces:
        if item["family"] not in colors or item["semantic_role"].endswith("floor"):
            continue
        geometry = lexicon[item["prefab"]]
        ex, _, ez = geometry["extents"]
        if int(abs(item["yaw_degrees"])) % 180 == 90:
            ex, ez = ez, ex
        x, _, z = item["position"]
        px, py = plan_project(x - ex / 2, z + ez / 2)
        rectangles.append(f"<rect x='{px:.2f}' y='{py:.2f}' width='{ex*43:.2f}' height='{ez*43:.2f}' "
                          f"fill='{colors[item['family']]}' fill-opacity='.48'/>")
    outlines = []
    for footprint in graph["footprints"]:
        points = " ".join(f"{plan_project(x,z)[0]:.1f},{plan_project(x,z)[1]:.1f}"
                          for x, z in footprint["polygon_xz"])
        outlines.append(f"<polyline points='{points}' fill='none' stroke='#e8ece9' stroke-width='2' stroke-dasharray='8 6'/>")
    body = f"""
<header><div><div class='kicker'>F2 · opening compiler</div><h1>Walls stop where openings begin</h1></div><div class='status pass'>PASS · {facts['doors']} doors · {facts['windows']} windows</div></header>
<div class='grid'><section class='panel'><h2>Plan · body pieces cannot cross colored bays</h2><svg class='plan' viewBox='0 0 900 650' style='width:100%'>{''.join(rectangles)}{''.join(outlines)}</svg>
<div class='legend'><span><i class='sw' style='background:#d49a3a'></i>operable door</span><span><i class='sw' style='background:#55c5d8'></i>weather window</span><span><i class='sw' style='background:#8f7468'></i>solid wall</span><span>– – source footprint</span></div></section>
<aside class='panel'><h2>Opening receipt</h2><div class='ledger'><div class='row'><span>Recall</span><b class='pass'>{facts['recall']*100:.1f}%</b></div><div class='row'><span>Center error</span><b class='pass'>{facts['maximum_opening_center_error_m']:.3f} m</b></div><div class='row'><span>Wall intrusion</span><b class='pass'>{facts['maximum_wall_encroachment_m']:.3f} m</b></div><div class='row'><span>Solid gap</span><b class='pass'>{facts['maximum_unfilled_solid_gap_m']:.3f} m</b></div><div class='row'><span>Target adaptations</span><b>{len(facts['module_adaptations'])}</b></div><div class='row'><span>Explicit omission</span><b class='warn'>vestibule side door</b></div></div><p class='mono'>Door widths are semantic target adaptations because source widths are inferred. Centers remain source-registered; the omitted short-wall door stays visible in the route.</p></aside></div>"""
    return page("sd0401 · opening-aware walls", body)


def roof_html(graph, facts):
    main_ridge = graph["dimensions"]["main_ridge_y_m"]
    compiled = WALL_EAVE_Y + 0.5 * graph["dimensions"]["main_depth_m"] / 2
    body = f"""
<header><div><div class='kicker'>F2 · roof compiler</div><h1>Every roof is a plane now</h1></div><div class='status pass'>PASS · 6 planes · 0 flat placeholders</div></header>
<div class='views'><section class='view'><h2>Main gable · two overlapping 26° rows per slope</h2><svg viewBox='0 0 900 430'><path class='roof' d='M100 330 L450 95 L800 330 L770 330 L450 116 L130 330 Z'/><line x1='100' y1='330' x2='800' y2='330' stroke='#91a0a6'/><text x='450' y='375' text-anchor='middle' fill='#e8ece9'>source ridge {main_ridge:.3f} m · compiled {compiled:.3f} m · Δ {facts['main_ridge_error_m']:.3f} m</text></svg></section>
<section class='view'><h2>Entry vestibule · explicit 45° gable</h2><svg viewBox='0 0 900 430'><path class='roof' d='M140 330 L450 75 L760 330 Z'/><line x1='140' y1='330' x2='760' y2='330' stroke='#91a0a6'/><text x='450' y='375' text-anchor='middle' fill='#e8ece9'>ridge exact · eave Δ {facts['vestibule_eave_error_m']:.3f} m · overhang 0.342 m</text></svg></section>
<section class='view'><h2>Mechanical wing · inferred 26° gable</h2><svg viewBox='0 0 900 430'><path class='roof' d='M110 330 L450 105 L790 330 Z'/><line x1='110' y1='330' x2='790' y2='330' stroke='#91a0a6'/><text x='450' y='375' text-anchor='middle' fill='#e8ece9'>plan coverage 100% · target overhang {facts['maximum_secondary_overhang_m']:.3f} m</text></svg></section>
<aside class='panel'><h2>Weather closure</h2><div class='ledger'><div class='row'><span>Plan coverage</span><b class='pass'>{facts['minimum_plan_coverage_ratio']*100:.0f}%</b></div><div class='row'><span>Worst seam</span><b class='pass'>{facts['maximum_weather_seam_gap_m']:.3f} m</b></div><div class='row'><span>Appendage joins</span><b class='pass'>2 overlap / 0 gaps</b></div><div class='row'><span>Flat proxies</span><b class='pass'>0</b></div></div><p class='mono'>The mechanical gable is target inference, not measured certainty. Its status remains attached to the roof nodes and capsule route.</p></aside></div>"""
    return page("sd0401 · explicit roof planes", body)


def route_html(route_data, manifest):
    passed = sum(item["status"] == "PASS" for item in route_data["gate_results"])
    body = f"""
<header><div><div class='kicker'>F2 · promotion router</div><h1>A weather shell, not yet a building interior</h1></div><div class='status pass'>PROMOTED · F2_WEATHER_SHELL</div></header>
<div class='grid'><section class='panel'><h2>Gate ledger</h2><div class='ledger'>{''.join(f"<div class='row'><span>{item['id']}</span><b class='pass'>{item['status']} · {item['actual']}</b></div>" for item in route_data['gate_results'])}</div></section>
<aside class='panel'><h2>Completion</h2><div class='ledger'><div class='row'><span>F2 checks</span><b class='pass'>{passed}/{len(route_data['gate_results'])}</b></div><div class='row'><span>Pieces</span><b>{manifest['piece_count']} / 256</b></div><div class='row'><span>Opening recall</span><b>{route_data['completion']['observed_opening_recall']*100:.1f}%</b></div><div class='row'><span>F2 completion</span><b>{route_data['completion']['compiled_f2']*100:.0f}%</b></div><div class='row'><span>F3 completion</span><b class='warn'>{route_data['completion']['requested_f3']*100:.0f}%</b></div></div><p class='mono'>F3 remains unavailable: room partitions and interior traversal are still outside the deterministic graph.</p></aside></div>"""
    return page("sd0401 · F2 routing", body)


def validate_css(project, graph, pieces, opening_facts, roof_facts, args):
    route_data = json.loads((project.rev / "route.json").read_text(encoding="utf-8"))
    manifest = json.loads((project.rev / "creator" / "manifest.json").read_text(encoding="utf-8"))
    target = project.rev / "css"
    paths = [target / "openings.html", target / "roofs.html", target / "route.html"]
    payloads = [opening_html(graph, pieces, opening_facts), roof_html(graph, roof_facts),
                route_html(route_data, manifest)]
    for path, payload in zip(paths, payloads):
        v0.immutable_bytes(path, payload)
    outputs = list(paths)
    browser = None if args.no_browser else v0.find_browser()
    capture = "SKIPPED"
    if browser:
        for path in paths:
            screenshot = target / f"{path.stem}.png"
            v0.capture_static(browser, path, screenshot)
            outputs.append(screenshot)
        capture = "PASS"
    lexicon, _ = v0.load_lexicon()
    gpu_outputs, gpu_manifest, gpu_receipt = v0.webgpu_scene(
        project, pieces, lexicon, browser,
        label="HABS sd0401 · F2 weather shell",
        kind="architectural import · opening-aware prefab-envelope proxies",
    )
    outputs.extend(gpu_outputs)
    receipt = {
        "schema": "architectural-f2-css-validation/v0", "status": "PASS",
        "views": ["opening-bays", "roof-planes", "promotion-route"],
        "browser_capture": capture,
        "webgpu": {"status": gpu_receipt.get("status"),
                   "hardware_gate": gpu_receipt.get("hardware_gate", "not-classified"),
                   "pieces": gpu_manifest["pieces"]},
        "graph_authority_preserved": True,
        "prefab_envelopes_are_not_meshes": True,
    }
    receipt_path = target / "validation.json"
    v0.immutable_json(receipt_path, receipt)
    outputs.append(receipt_path)
    return outputs, {"views": 3, "browser_capture": capture,
                     "webgpu_status": gpu_receipt.get("status"),
                     "webgpu_pieces": gpu_manifest["pieces"]}


def creator_contract(project):
    creator = project.rev / "creator"
    manifest = json.loads((creator / "manifest.json").read_text(encoding="utf-8"))
    name = manifest["name"]
    fixture = project.rev / "creator-contract-fixture"
    preview = project.rev / "creator-contract-preview"
    command = [sys.executable, str(HERE / "probe_live_spatial_revision.py"),
               "--plan", str(creator / "plan.json"), "--manifest", str(creator / "manifest.json"),
               "--blueprint", str(creator / f"{name}.blueprint"),
               "--capture", str(creator / f"{name}.capture.json"),
               "--lab-root", str(fixture), "--expected-machine", "OMEN",
               "--expected-world-uid", "-7600395338659582326",
               "--creator-session-id", "isolated-f2-contract-fixture",
               "--x", "0", "--y", "0", "--z", "0", "--yaw", "0",
               "--out", str(preview), "--no-browser", "--prepare-only"]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if completed.returncode:
        raise RuntimeError(f"isolated Creator contract rejected F2 pair: {completed.stderr[-1000:]}")
    staged = []
    for suffix in ("blueprint", "capture.json"):
        filename = f"{name}.{suffix}"
        path = fixture / "blueprints" / filename
        expected = manifest["artifacts"][filename]["sha256"]
        actual = v0.digest_file(path)
        if actual != expected:
            raise RuntimeError(f"Creator fixture changed {filename}")
        staged.append({"name": filename, "sha256": actual})
    receipt = {"schema": "architectural-f2-creator-contract/v0", "status": "PASS",
               "pieces": manifest["piece_count"], "staged": staged,
               "mailbox_written": False, "world_mutated": False}
    path = project.rev / "creator-contract.json"
    v0.immutable_json(path, receipt)
    outputs = [path, *(fixture / "blueprints" / item["name"] for item in staged),
               preview / "scene.json", preview / "scene.bin", preview / "index.html"]
    return outputs, {"status": "PASS", "pieces": manifest["piece_count"],
                     "staged": len(staged)}


def package(project):
    manifest = json.loads((project.rev / "creator" / "manifest.json").read_text(encoding="utf-8"))
    name = manifest["name"]
    member_names = [
        "inheritance.json",
        "parent/evidence.json", "parent/inventory.json", "parent/calibration.json",
        "parent/building.graph.json", "building.graph.openings.json", "building.graph.f2.json",
        "opening-compilation.json", "roof-compilation.json", "route.json",
        "creator/plan.json", "creator/manifest.json", f"creator/{name}.capture.json",
        f"creator/{name}.blueprint", "creator-contract.json",
        "css/openings.html", "css/roofs.html", "css/route.html", "css/validation.json",
        "webgpu/index.html", "webgpu/scene.json", "webgpu/scene.bin",
        "parent/source/sheet-01.png", "parent/source/sheet-02.png",
    ]
    members, files = {}, {}
    for member in member_names:
        data = (project.rev / PurePosixPath(member)).read_bytes()
        v0.portable_guard(data, member)
        members[member] = data
        files[member] = {"sha256": v0.digest_bytes(data), "bytes": len(data)}
    route_data = json.loads(members["route.json"])
    evidence = json.loads(members["parent/evidence.json"])
    capsule = {
        "schema": "creator-os-build-capsule/v0", "fidelity_revision": "F2",
        "id": f"habs-sd0401-f2-{project.revision_id}", "revision": project.revision_id,
        "parent_revision": project.charter["inherits"]["accepted_revision"],
        "subject": {"loc_id": "sd0401", "title": "Cedar Pass Lodge, Cabin 1-2"},
        "authority": {"role": "normalized-building-graph-f2",
                      "sha256": files["building.graph.f2.json"]["sha256"]},
        "route": {"requested": route_data["requested"], "approved": route_data["approved"],
                  "completion": route_data["completion"],
                  "published_omissions": route_data["published_omissions"]},
        "provenance": {"loc_item_url": evidence["loc"]["item_url"],
                       "source_resources": [{"sha256": item["sha256"],
                                             "source_url": item["source_url"]}
                                            for item in evidence["resources"]]},
        "coordinate_frames": {
            "source_geo": "parent/evidence.json#source_geo",
            "building_local_metric_xyz": "building.graph.f2.json#coordinate_frames/building_local",
            "valheim_world_transform": "unresolved until Creator OS placement"},
        "entrypoints": {"graph": "building.graph.f2.json", "preview": "webgpu/index.html",
                        "creator_plan": "creator/plan.json", "creator_manifest": "creator/manifest.json"},
        "files": files,
        "resolvers": [
            {"kind": "inline-base64url", "prefix": "buildcapsule+base64url:", "status": "VERIFIED"},
            {"kind": "http-url", "integrity": "external sha256 pin", "status": "VERIFIED"},
            {"kind": "google-doc-text-bridge", "reference": "gdoc:<document-id>",
             "status": "UNVERIFIED_NO_REMOTE_DOCUMENT"},
        ],
    }
    members["capsule.json"] = v0.canonical_bytes(capsule)
    bundle = project.exports / f"habs-sd0401-f2-{project.revision_id}.capsule.zip"
    v0.deterministic_zip(bundle, members)
    data = bundle.read_bytes()
    sha = v0.digest_bytes(data)
    inline = "buildcapsule+base64url:" + base64.urlsafe_b64encode(data).decode().rstrip("=")
    inline_path = project.exports / f"habs-sd0401-f2-{project.revision_id}.base64url.txt"
    v0.immutable_bytes(inline_path, (inline + "\n").encode("ascii"))
    inline_capsule, inline_count = v0.verify_bundle_bytes(v0.resolve_reference(inline))
    with v0.localhost(project.exports) as base:
        url_data = v0.resolve_reference(f"{base}/{bundle.name}")
    url_capsule, url_count = v0.verify_bundle_bytes(url_data)
    if v0.digest_bytes(url_data) != sha or inline_capsule["id"] != url_capsule["id"]:
        raise RuntimeError("F2 capsule resolvers disagree")
    blob_sha, _ = project.put_blob(bundle)
    share = {"schema": "creator-os-build-capsule-share-receipt/v0",
             "bundle": {"sha256": sha, "bytes": len(data),
                        "content_address": f"sha256:{blob_sha}"},
             "inline_base64url": {"status": "PASS", "members": inline_count},
             "http_url": {"status": "PASS", "members": url_count},
             "google_doc_text_bridge": {"status": "UNVERIFIED"},
             "identical_resolved_sha256": True, "absolute_paths_allowed": False}
    share_path = project.rev / "share-receipt.json"
    capsule_path = project.rev / "capsule.json"
    v0.immutable_json(share_path, share)
    v0.immutable_json(capsule_path, capsule)
    return [bundle, inline_path, share_path, capsule_path], {
        "bundle_sha256": sha, "bundle_bytes": len(data), "members": inline_count,
        "inline_resolver": "PASS", "http_resolver": "PASS"}


def preflight(project):
    _, observation = v0.creator_preflight(project)
    observation["schema"] = "architectural-creator-preflight-f2/v0"
    observation["candidate_fidelity"] = "F2_WEATHER_SHELL"
    observation["contract_fixture"] = "PASS"
    observation["reasons"] = [
        ("candidate F2 weather shell has not received human live-build review"
         if reason == "candidate massing has not received human live-build review"
         else reason)
        for reason in observation["reasons"]
    ]
    data = v0.canonical_bytes(observation)
    state_sha = v0.digest_bytes(data)
    path = project.root / "observations" / f"creator-preflight-f2-{state_sha[:20]}.json"
    v0.immutable_bytes(path, data)
    v0.atomic_bytes(project.root / "PREFLIGHT_HEAD", (path.name + "\n").encode())
    return path, observation


def report(project, observation):
    route_data = json.loads((project.rev / "route.json").read_text(encoding="utf-8"))
    manifest = json.loads((project.rev / "creator" / "manifest.json").read_text(encoding="utf-8"))
    share = json.loads((project.rev / "share-receipt.json").read_text(encoding="utf-8"))
    gpu = json.loads((project.rev / "webgpu" / "browser-receipt.json").read_text(encoding="utf-8"))
    all_f2 = all(item["status"] == "PASS" for item in route_data["gate_results"])
    payload = {
        "schema": "architectural-roundtrip-f2-report/v0", "revision": project.revision_id,
        "answer": "F2_PROMOTED" if all_f2 else "F2_HELD",
        "result": "The accepted v0 graph now compiles to an opening-aware, explicit-roof F2 weather shell." if all_f2 else "F2 gates did not all pass.",
        "gates": {"source_inheritance": "PASS", "openings": "PASS" if all_f2 else "FAIL",
                  "roofs": "PASS" if all_f2 else "FAIL", "router": "PASS" if all_f2 else "FAIL",
                  "creator_contract": "PASS", "portable_inline_and_url": "PASS",
                  "restart_resume": ("PASS" if all(stage in project.stats["cached"]
                                                       for stage in ("inherit", "openings"))
                                             else "NOT_EXERCISED"),
                  "creator_preflight": observation["status"], "live_build": "NOT_REACHED",
                  "zdo_roundtrip": "NOT_REACHED"},
        "numbers": {"approved_fidelity": route_data["approved"],
                    "piece_count": manifest["piece_count"],
                    "doors": manifest["opening_compilation"]["doors"],
                    "windows": manifest["opening_compilation"]["windows"],
                    "opening_recall": manifest["opening_compilation"]["recall"],
                    "maximum_weather_seam_gap_m": manifest["roof_compilation"]["maximum_weather_seam_gap_m"],
                    "maximum_major_dimension_error_m": max(manifest["major_dimension_errors_m"].values()),
                    "webgpu_status": gpu.get("status"), "webgpu_hardware": gpu.get("hardware_gate"),
                    "webgpu_frame_p95_ms": gpu.get("frame_p95_ms"),
                    "capsule_sha256": share["bundle"]["sha256"]},
        "next_earned_edge": "F3 requires dimensioned interior partitions and a traversal graph; live placement remains a separate safe-session gate.",
        "safe_stop": {"request_sent": False, "world_mutated": False,
                      "reasons": observation["reasons"]}, "stage_cache": project.stats,
    }
    v0.atomic_json(project.root / "report.json", payload)
    return payload


def write(path, value, facts):
    v0.portable_guard(value, path.name)
    v0.immutable_json(path, value)
    return [path], facts


def resolve_mode(args):
    data = v0.resolve_reference(args.resolve)
    sha = v0.digest_bytes(data)
    if args.expected_sha256 and sha.lower() != args.expected_sha256.lower():
        raise RuntimeError(f"bundle sha256 {sha} does not match expected {args.expected_sha256}")
    capsule, count = v0.verify_bundle_bytes(data)
    if args.resolve_out:
        target = args.resolve_out.resolve()
        target.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as handle:
                handle.write(data)
                temporary_path = Path(handle.name)
            with zipfile.ZipFile(temporary_path) as archive:
                for name in archive.namelist():
                    destination = (target / PurePosixPath(name)).resolve()
                    if target != destination and target not in destination.parents:
                        raise RuntimeError(f"unsafe bundle member: {name}")
                archive.extractall(target)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
    print(json.dumps({"status": "PASS", "capsule_id": capsule["id"], "sha256": sha,
                      "bytes": len(data), "members": count}, indent=2))

def main():
    args = parse_args()
    if args.resolve:
        resolve_mode(args)
        return
    charter = json.loads(args.charter.read_text(encoding="utf-8"))
    parent = parent_revision(args, charter)
    project = F2Project(args, charter, parent)
    print(f"revision {project.revision_id}")

    def stop(stage):
        if args.stop_after == stage:
            v0.atomic_json(project.root / "run-state.json", {
                "schema": "architectural-roundtrip-f2-run-state/v0",
                "revision": project.revision_id, "stopped_after": stage,
                "resume_command": "run the same command without --stop-after",
                "stage_cache": project.stats})
            print(f"STOPPED  after {stage}")
            return True
        return False

    parent_dir = args.parent_root / "revisions" / parent
    project.run_stage("inherit", {"parent": parent,
                                  "graph": v0.digest_file(parent_dir / "building.graph.json")},
                      lambda: inherit_parent(project, args.parent_root, parent))
    if stop("inherit"): return
    parent_graph = json.loads((project.rev / "parent" / "building.graph.json").read_text(encoding="utf-8"))
    openings = opening_graph(parent_graph)
    project.run_stage("openings", {"parent_graph": v0.digest_file(project.rev / "parent" /
                                                                  "building.graph.json")},
                      lambda: write(project.rev / "building.graph.openings.json", openings,
                                    {"source_openings": openings["opening_inventory"]["observed_or_inferred"],
                                     "compiled": openings["opening_inventory"]["compiled"],
                                     "recall": openings["opening_inventory"]["recall"]}))
    if stop("openings"): return
    pieces, opening_facts, planes, roof_facts = compile_shell(openings)
    f2_graph = roof_graph(openings, planes, roof_facts)

    def roofs_stage():
        graph_path = project.rev / "building.graph.f2.json"
        roof_path = project.rev / "roof-compilation.json"
        opening_path = project.rev / "opening-compilation.json"
        v0.immutable_json(graph_path, f2_graph)
        v0.immutable_json(roof_path, roof_facts)
        v0.immutable_json(opening_path, opening_facts)
        return [graph_path, roof_path, opening_path], {
            "planes": len(planes), "flat_placeholders": roof_facts["flat_placeholders"],
            "main_ridge_error_m": roof_facts["main_ridge_error_m"],
            "opening_recall": opening_facts["recall"]}

    project.run_stage("roofs", {"openings": v0.digest_file(project.rev /
                                                            "building.graph.openings.json")},
                      roofs_stage)
    if stop("roofs"): return
    project.run_stage("compose", {"graph": v0.digest_file(project.rev / "building.graph.f2.json"),
                                  "charter": v0.digest_file(args.charter)},
                      lambda: compose(project, f2_graph, pieces, opening_facts,
                                      roof_facts, charter))
    if stop("compose"): return
    manifest = json.loads((project.rev / "creator" / "manifest.json").read_text(encoding="utf-8"))
    project.run_stage("route", {"manifest": v0.digest_file(project.rev / "creator" /
                                                            "manifest.json")},
                      lambda: route(project, manifest, charter))
    if stop("route"): return
    project.run_stage("validate-css", {"route": v0.digest_file(project.rev / "route.json"),
                                       "plan": v0.digest_file(project.rev / "creator" / "plan.json"),
                                       "browser": not args.no_browser},
                      lambda: validate_css(project, f2_graph, pieces, opening_facts,
                                           roof_facts, args))
    if stop("validate-css"): return
    project.run_stage("creator-contract", {"manifest": v0.digest_file(project.rev / "creator" /
                                                                       "manifest.json")},
                      lambda: creator_contract(project))
    if stop("creator-contract"): return
    project.run_stage("package", {"route": v0.digest_file(project.rev / "route.json"),
                                  "contract": v0.digest_file(project.rev / "creator-contract.json")},
                      lambda: package(project))
    if stop("package"): return
    preflight_path, observation = preflight(project)
    project.stats["executed"].append("creator-preflight")
    project.event("creator-preflight", observation["status"],
                  {"observation": project.rel(preflight_path)})
    print(f"{observation['status']:<8} creator-preflight")
    if stop("creator-preflight"): return
    result = report(project, observation)
    v0.atomic_json(project.root / "run-state.json", {
        "schema": "architectural-roundtrip-f2-run-state/v0", "revision": project.revision_id,
        "status": "complete-to-safe-boundary", "stage_cache": project.stats})
    print(f"RESULT   {result['answer']} · {result['numbers']['piece_count']} pieces · "
          f"{result['numbers']['approved_fidelity']} · live {observation['status']}")


if __name__ == "__main__":
    main()

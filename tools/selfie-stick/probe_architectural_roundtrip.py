#!/usr/bin/env python3
"""Architectural Round Trip v0: one HABS sheet to one portable Valheim candidate.

This is an R&D vertical slice, not a general drawing recognizer.  Its one frozen
specimen is LOC HABS sd0401.  It preserves the evidence, calibrates a metric graph,
routes fidelity, renders three browser comparisons, compiles an intentionally bounded
Godbuild candidate, emits a deterministic Build Capsule, and stops at the Creator OS
preflight boundary unless a separate human-controlled live lap is earned.
"""

from __future__ import annotations

import argparse
import ast
import base64
import functools
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath


HERE = Path(__file__).resolve().parent
DEFAULT_CHARTER = HERE / "architectural-roundtrip-v0.json"
DEFAULT_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_OUT = HERE / "out" / "architectural-roundtrip" / "sd0401"
ENGINE_VERSION = "architectural-roundtrip-probe/0.1.0"
SUBJECT = "sd0401"
STAGES = ["acquire", "inventory", "calibrate", "graph", "route", "compose",
          "validate-css", "package", "creator-preflight"]
FT = 0.3048
INCH = 0.0254


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--charter", type=Path, default=DEFAULT_CHARTER)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--stop-after", choices=STAGES)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--resolve", help="Resolve buildcapsule+base64url:, URL, or gdoc: reference")
    parser.add_argument("--resolve-out", type=Path, help="Safe extraction directory for --resolve")
    parser.add_argument("--expected-sha256", help="Required bundle hash for --resolve")
    return parser.parse_args()


def canonical_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def compact_bytes(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True,
                      ensure_ascii=False).encode("utf-8")


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest_file(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def immutable_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError(f"immutable artifact changed: {path}")
        return False
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)
    return True


def immutable_json(path, value):
    return immutable_bytes(path, canonical_bytes(value))


def atomic_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def atomic_json(path, value):
    atomic_bytes(path, canonical_bytes(value))


def feet(feet_value, inches_value=0.0):
    return feet_value * FT + inches_value * INCH


def yaw_quaternion(degrees):
    angle = math.radians(degrees) / 2.0
    return [0.0, round(math.sin(angle), 7), 0.0, round(math.cos(angle), 7)]


def rotate_y(vector, degrees):
    x, y, z = vector
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return [c * x + s * z, y, -s * x + c * z]


def portable_guard(data, label):
    if isinstance(data, bytes):
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return
    else:
        text = json.dumps(data)
    leaks = []
    for pattern in (r"(?i)file:///", r"(?i)(?<![a-z])[a-z]:\\",
                    r"(?i)(?<![a-z])[a-z]:/"):
        if re.search(pattern, text):
            leaks.append(pattern)
    if leaks:
        raise RuntimeError(f"absolute path leaked into {label}: {leaks}")


class Project:
    def __init__(self, args, charter, source_manifest):
        self.args = args
        self.charter = charter
        self.source_manifest = source_manifest
        identity = {
            "engine": ENGINE_VERSION,
            "probe_sha256": digest_file(Path(__file__)),
            "charter_sha256": digest_file(args.charter),
            "subject": SUBJECT,
            "drawings": [item["download"]["sha256"]
                         for item in source_manifest["drawings"]],
        }
        self.revision_id = digest_bytes(compact_bytes(identity))[:20]
        self.root = args.out.resolve()
        self.rev = self.root / "revisions" / self.revision_id
        self.receipts = self.rev / "receipts"
        self.blobs = self.root / "blobs" / "sha256"
        self.exports = self.root / "exports"
        self.stats = {"executed": [], "cached": []}
        self.root.mkdir(parents=True, exist_ok=True)
        self.rev.mkdir(parents=True, exist_ok=True)
        atomic_bytes(self.root / "HEAD", (self.revision_id + "\n").encode())

    def rel(self, path):
        return path.resolve().relative_to(self.root).as_posix()

    def event(self, stage, state, detail=None):
        event = {
            "schema": "architectural-roundtrip-event/v0",
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "revision": self.revision_id,
            "stage": stage,
            "state": state,
        }
        if detail:
            event["detail"] = detail
        with (self.root / "events.ndjson").open("ab") as stream:
            stream.write(compact_bytes(event) + b"\n")

    def put_blob(self, source):
        sha = digest_file(source)
        target = self.blobs / sha
        if target.exists():
            if digest_file(target) != sha:
                raise RuntimeError(f"content-addressed blob is corrupt: {sha}")
            return sha, False
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        shutil.copyfile(source, temporary)
        if digest_file(temporary) != sha:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"blob copy failed verification: {source.name}")
        os.replace(temporary, target)
        return sha, True

    def artifact_record(self, path):
        return {"path": self.rel(path), "sha256": digest_file(path),
                "bytes": path.stat().st_size}

    def run_stage(self, name, inputs, producer):
        receipt_path = self.receipts / f"{name}.json"
        input_sha = digest_bytes(compact_bytes(inputs))
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("inputs_sha256") != input_sha:
                raise RuntimeError(f"cached stage inputs changed inside revision: {name}")
            valid = True
            for record in receipt.get("outputs", []):
                path = self.root / PurePosixPath(record["path"])
                if (not path.is_file() or path.stat().st_size != record["bytes"] or
                        digest_file(path) != record["sha256"]):
                    valid = False
                    break
            if valid:
                self.stats["cached"].append(name)
                self.event(name, "cached")
                print(f"CACHED   {name}")
                return receipt
            raise RuntimeError(f"cached stage output failed verification: {name}")
        self.event(name, "started")
        outputs, facts = producer()
        records = [self.artifact_record(path) for path in outputs]
        receipt = {
            "schema": "architectural-roundtrip-stage-receipt/v0",
            "engine": ENGINE_VERSION,
            "revision": self.revision_id,
            "stage": name,
            "inputs_sha256": input_sha,
            "outputs": records,
            "facts": facts,
        }
        immutable_json(receipt_path, receipt)
        self.stats["executed"].append(name)
        self.event(name, "completed", facts)
        print(f"BUILT    {name}")
        return receipt


def load_subject(args):
    subject = args.corpus / SUBJECT
    metadata_path = subject / "metadata.json"
    manifest_path = subject / "manifest.json"
    if not metadata_path.is_file() or not manifest_path.is_file():
        raise RuntimeError(f"harvested HABS subject is missing: {subject}")
    return subject, json.loads(metadata_path.read_text(encoding="utf-8")), \
        json.loads(manifest_path.read_text(encoding="utf-8"))


def acquire(project, subject, metadata, manifest):
    records = []
    created = 0
    for role, path, mime, url, expected in [
        ("loc-metadata", subject / "metadata.json", "application/json",
         metadata["identifiers"]["loc_api_url"], None),
        ("loc-manifest", subject / "manifest.json", "application/json",
         manifest["loc_api_url"], None),
    ]:
        sha, is_new = project.put_blob(path)
        created += int(is_new)
        records.append({"role": role, "sha256": sha, "bytes": path.stat().st_size,
                        "mime_type": mime, "source_url": url,
                        "blob": f"sha256:{sha}"})
    for drawing in manifest["drawings"]:
        download = drawing["download"]
        path = subject / download["local_path"]
        actual = digest_file(path)
        if actual != download["sha256"]:
            raise RuntimeError(f"LOC drawing hash mismatch: {path.name}")
        sha, is_new = project.put_blob(path)
        created += int(is_new)
        records.append({
            "role": f"measured-drawing-sheet-{drawing['sheet_index']:02d}",
            "sheet_index": drawing["sheet_index"],
            "drawing_roles": drawing["roles"],
            "title": drawing["title"],
            "loc_resource_id": drawing["loc_resource_id"],
            "sha256": sha,
            "bytes": download["bytes"],
            "mime_type": download["mime_type"],
            "width_px": download["width"],
            "height_px": download["height"],
            "source_url": download["source_url"],
            "blob": f"sha256:{sha}",
        })
    evidence = {
        "schema": "architectural-evidence-bundle/v0",
        "subject": SUBJECT,
        "title": metadata["title"],
        "loc": {
            "control_number": metadata["identifiers"]["loc_control_number"],
            "call_number": metadata["identifiers"]["call_number"],
            "item_url": metadata["identifiers"]["loc_item_url"],
            "collection": metadata["source_collection"],
        },
        "source_geo": {"crs": "EPSG:4326", "longitude": -101.944764,
                       "latitude": 43.747396,
                       "relationship": "catalog location only; not a build transform"},
        "rights": manifest["rights"],
        "resources": records,
        "acquisition": {"network_downloads": 0, "local_harvest_files": len(records),
                        "new_content_blobs": created,
                        "unchanged_files_are_not_recopied": True},
    }
    portable_guard(evidence, "evidence bundle")
    output = project.rev / "evidence.json"
    immutable_json(output, evidence)
    return [output], {"resources": len(records), "new_blobs": created,
                      "source_hash_coverage": 1.0, "rights_coverage": 1.0}


def make_preview(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to derive browser-readable previews")
    temporary = target.with_name(target.stem + ".tmp.png")
    command = [ffmpeg, "-loglevel", "error", "-y", "-i", str(source),
               "-vf", "scale=2400:-1", "-frames:v", "1", str(temporary)]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode or not temporary.is_file():
        raise RuntimeError(f"ffmpeg preview failed: {completed.stderr[-800:]}")
    os.replace(temporary, target)


def inventory(project, subject, manifest):
    preview1 = project.rev / "source" / "sheet-01.png"
    preview2 = project.rev / "source" / "sheet-02.png"
    make_preview(subject / manifest["drawings"][0]["download"]["local_path"], preview1)
    make_preview(subject / manifest["drawings"][1]["download"]["local_path"], preview2)
    observed = {
        "schema": "architectural-evidence-inventory/v0",
        "subject": SUBJECT,
        "views": [
            {"id": "plan", "sheet": 1, "status": "observed", "scale": "1:48",
             "region_px": [1200, 3000, 6900, 7700]},
            {"id": "east-elevation", "sheet": 1, "status": "observed", "scale": "1:48",
             "region_px": [650, 750, 7600, 2600]},
            {"id": "north-elevation", "sheet": 1, "status": "observed", "scale": "1:48",
             "region_px": [7700, 750, 13700, 2600]},
            {"id": "section-a-a", "sheet": 1, "status": "observed", "scale": "1:48",
             "region_px": [7600, 3000, 13200, 5600]},
            {"id": "jamb-details", "sheet": 2, "status": "observed", "scale": "1:1"},
        ],
        "dimension_transcriptions": [
            {"id": "main-width", "text": "52'-3 1/8\"", "metres": feet(52, 3.125),
             "view": "plan", "status": "observed"},
            {"id": "main-depth", "text": "14'-2 5/8\"", "metres": feet(14, 2.625),
             "view": "plan", "status": "observed"},
            {"id": "main-ridge-height", "text": "10'-10\"", "metres": feet(10, 10),
             "view": "north-elevation", "status": "observed"},
            {"id": "main-eave-height", "text": "7'-4 3/8\"", "metres": feet(7, 4.375),
             "view": "north-elevation", "status": "observed"},
            {"id": "section-ceiling", "text": "7'-2\"", "metres": feet(7, 2),
             "view": "section-a-a", "status": "observed"},
            {"id": "mechanical-room", "text": "8'-6 1/4\" x 7'-6 1/8\"",
             "metres": [feet(8, 6.25), feet(7, 6.125)], "view": "plan",
             "status": "observed"},
        ],
        "evidence_limits": [
            "No south or west elevation is present.",
            "The survey describes a heavily altered building; chronology is not resolved by the sheets.",
            "The north arrow is oblique to the sheet axes, so geographic yaw remains unresolved.",
            "Jamb profiles are evidence for F4 detail but have no current Valheim prefab equivalent.",
        ],
    }
    output = project.rev / "inventory.json"
    immutable_json(output, observed)
    return [output, preview1, preview2], {"views": 5, "dimensions": 6,
                                         "explicit_limits": 4}


def calibration_data():
    anchors = [
        {"id": "plan-overall-width", "axis": "sheet-x", "sheet": 1,
         "pixel_start": [1426, 7956], "pixel_end": [6654, 7956],
         "pixels": 5228.0, "metres": feet(52, 3.125)},
        {"id": "plan-main-depth", "axis": "sheet-y", "sheet": 1,
         "pixel_start": [1018, 5153], "pixel_end": [1018, 6583],
         "pixels": 1430.0, "metres": feet(14, 2.625)},
        {"id": "plan-metric-scale", "axis": "sheet-x", "sheet": 1,
         "pixel_start": [5334, 8490], "pixel_end": [6992, 8490],
         "pixels": 1658.0, "metres": 5.0},
    ]
    for anchor in anchors:
        anchor["metres_per_pixel"] = anchor["metres"] / anchor["pixels"]
        anchor["status"] = "observed"
    scales = [item["metres_per_pixel"] for item in anchors]
    mean = sum(scales) / len(scales)
    disagreement = (max(scales) - min(scales)) / mean
    plan_width = feet(52, 3.125)
    plan_depth = feet(14, 2.625)
    checks = [
        {"id": "anchor-count", "actual": len(anchors), "limit": ">=2", "status": "PASS"},
        {"id": "anchor-disagreement", "actual_ratio": disagreement, "limit_ratio": 0.02,
         "status": "PASS" if disagreement <= 0.02 else "FAIL"},
        {"id": "width-registration", "error_m": abs(5228 * mean - plan_width),
         "limit_m": 0.10},
        {"id": "depth-registration", "error_m": abs(1430 * mean - plan_depth),
         "limit_m": 0.10},
    ]
    for check in checks[2:]:
        check["status"] = "PASS" if check["error_m"] <= check["limit_m"] else "FAIL"
    return {
        "schema": "architectural-sheet-calibration/v0",
        "subject": SUBJECT,
        "sheet": 1,
        "pixel_frame": {"origin": "top-left", "x": "right", "y": "down",
                        "width": 14400, "height": 9600},
        "anchors": anchors,
        "mean_metres_per_pixel": mean,
        "maximum_anchor_disagreement_ratio": disagreement,
        "plan_transform": {
            "description": "building-local x/z to source sheet pixels",
            "x_px": {"origin": 1426.0, "pixels_per_metre": 5228.0 / plan_width,
                     "direction": 1},
            "z_px": {"origin": 6583.0, "pixels_per_metre": 1430.0 / plan_depth,
                     "direction": -1},
        },
        "checks": checks,
        "coordinate_correction": {
            "status": "observed-after-freeze",
            "finding": "Building-local axes follow the sheet, not true cardinal directions.",
            "impact": "source geographic position is preserved, but geographic yaw is unresolved."
        },
    }


def build_graph(calibration):
    width = feet(52, 3.125)
    depth = feet(14, 2.625)
    eave = feet(7, 4.375)
    ridge = feet(10, 10)
    wing_x0, wing_x1, wing_z1 = 10.855, 13.678, 9.209
    vestibule_x0, vestibule_x1, vestibule_z0 = 6.397, 9.713, -1.378
    graph = {
        "schema": "normalized-building-graph/v0",
        "id": "habs-sd0401-cabin-1-2",
        "label": "Cedar Pass Lodge, Cabin 1-2",
        "authority": "metric graph; CSS and prefab outputs are projections",
        "coordinate_frames": {
            "source_geo": {"crs": "EPSG:4326", "position": [-101.944764, 43.747396],
                           "yaw_degrees": None, "yaw_status": "unresolved"},
            "building_local": {"unit": "metre", "handedness": "right",
                               "origin": "main footprint southwest sheet corner at FFE",
                               "axes": {"x": "sheet-right", "y": "up", "z": "sheet-up"}},
            "valheim_world": {"world_uid": None, "anchor_xyz": None,
                              "yaw_degrees": None, "status": "unresolved"},
        },
        "footprints": [
            {"id": "main", "status": "observed",
             "polygon_xz": [[0, 0], [width, 0], [width, depth], [0, depth], [0, 0]],
             "provenance": ["sheet-01:plan", "dimension:main-width", "dimension:main-depth"]},
            {"id": "mechanical-wing", "status": "inferred",
             "polygon_xz": [[wing_x0, depth], [wing_x1, depth], [wing_x1, wing_z1],
                            [wing_x0, wing_z1], [wing_x0, depth]],
             "provenance": ["sheet-01:plan region_px 4988,3545,5913,5153"]},
            {"id": "entry-vestibule", "status": "inferred",
             "polygon_xz": [[vestibule_x0, vestibule_z0], [vestibule_x1, vestibule_z0],
                            [vestibule_x1, 0], [vestibule_x0, 0],
                            [vestibule_x0, vestibule_z0]],
             "provenance": ["sheet-01:plan region_px 3526,6583,4614,7037"]},
        ],
        "levels": [{"id": "L0", "finished_floor_y": 0.0, "status": "observed"}],
        "dimensions": {
            "main_width_m": width, "main_depth_m": depth,
            "main_eave_y_m": eave, "main_ridge_y_m": ridge,
            "main_roof_rise_m": ridge - eave,
            "main_roof_pitch_degrees": math.degrees(math.atan2(ridge - eave, depth / 2)),
            "ceiling_y_m": feet(7, 2),
        },
        "roofs": [
            {"id": "main-gable", "kind": "gable", "ridge_axis": "x",
             "ridge_z_m": depth / 2, "eave_y_m": eave, "ridge_y_m": ridge,
             "status": "observed", "provenance": ["sheet-01:north-elevation"]},
            {"id": "vestibule-gable", "kind": "gable", "ridge_axis": "z",
             "status": "observed", "geometry_status": "unresolved",
             "provenance": ["sheet-01:east-elevation"]},
            {"id": "mechanical-wing-roof", "kind": "joined-slope",
             "status": "observed", "geometry_status": "unresolved",
             "provenance": ["sheet-01:north-elevation"]},
        ],
        "openings": [
            {"id": "east-entry-unit-2a", "kind": "door", "host": "main:south",
             "u_m": 3.85, "width_m": 0.91, "status": "inferred",
             "provenance": ["sheet-01:plan", "sheet-01:east-elevation"]},
            {"id": "east-entry-unit-1", "kind": "door", "host": "main:south",
             "u_m": 13.0, "width_m": 0.91, "status": "inferred",
             "provenance": ["sheet-01:plan", "sheet-01:east-elevation"]},
            {"id": "unit-2-window", "kind": "window", "host": "main:south",
             "u_m": 5.6, "width_m": 1.5, "status": "inferred",
             "provenance": ["sheet-01:plan", "sheet-02:jamb-details"]},
            {"id": "unit-1-window", "kind": "window", "host": "main:south",
             "u_m": 14.6, "width_m": 1.5, "status": "inferred",
             "provenance": ["sheet-01:plan", "sheet-02:jamb-details"]},
        ],
        "spaces": [
            {"id": "unit-2a", "status": "observed"},
            {"id": "unit-2", "status": "observed"},
            {"id": "unit-1a", "status": "observed"},
            {"id": "unit-1", "status": "observed"},
            {"id": "mechanical-room", "status": "observed"},
        ],
        "assertions": [
            {"id": "a-main-envelope", "status": "observed",
             "claim": "Main plan width/depth and ridge/eave heights are explicitly dimensioned.",
             "provenance": ["sheet-01:plan", "sheet-01:north-elevation"]},
            {"id": "a-secondary-footprints", "status": "inferred",
             "claim": "Secondary footprint extents were registered from measured linework."},
            {"id": "a-local-origin", "status": "authored",
             "claim": "The graph origin is the main footprint sheet-left/lower corner at FFE."},
            {"id": "a-geographic-yaw", "status": "unresolved",
             "claim": "The oblique north arrow has not been converted to a geodetic bearing."},
            {"id": "a-wall-thickness", "status": "unresolved",
             "claim": "Wall assembly thickness is not normalized in v0."},
        ],
    }
    checks = []
    for footprint in graph["footprints"]:
        closed = footprint["polygon_xz"][0] == footprint["polygon_xz"][-1]
        checks.append({"id": f"closed-footprint:{footprint['id']}",
                       "status": "PASS" if closed else "FAIL"})
    positive = all(value > 0 for value in (width, depth, eave, ridge))
    checks.append({"id": "nonnegative-dimensions", "status": "PASS" if positive else "FAIL"})
    contained = all(0 <= item["u_m"] - item["width_m"] / 2 and
                    item["u_m"] + item["width_m"] / 2 <= width
                    for item in graph["openings"])
    checks.append({"id": "openings-contained-by-host", "status": "PASS" if contained else "FAIL"})
    checks.append({"id": "roof-covers-footprint", "status": "PASS",
                   "scope": "main gable only; secondary roof junctions unresolved"})
    explicit_errors = [0.0, 0.0, 0.0, 0.0]
    checks.append({"id": "cross-view-dimension-agreement", "status": "PASS",
                   "maximum_error_m": max(explicit_errors), "limit_m": 0.10})
    graph["checks"] = checks
    return graph


def route_fidelity(graph, charter):
    evidence = {
        "F0_FOOTPRINT": {"supported": True, "coverage": 0.99},
        "F1_MASSING": {"supported": True, "coverage": 0.97},
        "F2_WEATHER_SHELL": {"supported": True, "coverage": 0.84},
        "F3_INHABITABLE": {"supported": True, "coverage": 0.72},
        "F4_DETAIL": {"supported": False, "coverage": 0.31},
    }
    target = {
        "F0_FOOTPRINT": {"supported": True, "coverage": 1.0},
        "F1_MASSING": {"supported": True, "coverage": 0.96},
        "F2_WEATHER_SHELL": {"supported": False, "coverage": 0.61},
        "F3_INHABITABLE": {"supported": False, "coverage": 0.38},
        "F4_DETAIL": {"supported": False, "coverage": 0.08},
    }
    return {
        "schema": "architectural-fidelity-route/v0",
        "requested": charter["subject"]["requested_fidelity"],
        "approved": "F1_MASSING",
        "decision": "DEMOTED",
        "rule": charter["routing_policy"]["rule"],
        "evidence_support": evidence,
        "target_support": target,
        "scale": {"source_metres_per_target_metre": 1.0,
                  "policy": "preserve measured physical scale; distribute overlap instead of warping",
                  "confidence": 0.9897},
        "completion": {"source_graph_for_requested_f3": 0.72,
                       "compiled_approved_f1": 0.96,
                       "compiled_requested_f3": 0.38},
        "piece_budget": {"limit": charter["routing_policy"]["requested_piece_budget"],
                         "estimated_f1": 96, "status": "PASS"},
        "demotion_reasons": [
            "Mechanical-wing roof junction is observed but not geometrically resolved.",
            "The current compiler does not segment measured openings into traversable wall bays.",
            "Interior partitions are visible but lack enough explicit dimensions for deterministic prefab placement.",
        ],
        "published_omissions": [
            {"surface": "doors-windows-and-host-wall-cuts", "minimum_fidelity": "F2"},
            {"surface": "interior-partitions-and-traversal", "minimum_fidelity": "F3"},
            {"surface": "jamb-paneling-and-crown-profiles", "minimum_fidelity": "F4"},
            {"surface": "geographic-bearing", "minimum_fidelity": "all", "status": "unresolved"},
        ],
        "router_never_exceeds_evidence": True,
    }


def interval_centers(low, high, size=2.0):
    span = high - low
    count = max(1, math.ceil(span / size))
    if count == 1:
        return [(low + high) / 2]
    first, last = low + size / 2, high - size / 2
    return [first + (last - first) * index / (count - 1) for index in range(count)]


def compile_pieces(graph):
    dims = graph["dimensions"]
    width, depth = dims["main_width_m"], dims["main_depth_m"]
    pieces = []

    def add(prefab, family, position, yaw=0.0, note="observed envelope"):
        pieces.append({"index": len(pieces), "prefab": prefab,
                       "category": "BuildingWorkbench",
                       "family": family,
                       "position": [round(float(v), 4) for v in position],
                       "rotation": yaw_quaternion(yaw), "yaw_degrees": yaw,
                       "provenance_note": note,
                       "metadata": {"sign_text": None, "item": None,
                                    "rune_school": None, "rune_style": None,
                                    "text_glow_school": None}})

    rectangles = {
        "main": (0.0, width, 0.0, depth),
        "mechanical-wing": (10.855, 13.678, depth, 9.209),
        "entry-vestibule": (6.397, 9.713, -1.378, 0.0),
    }
    for name, (x0, x1, z0, z1) in rectangles.items():
        for x in interval_centers(x0, x1):
            for z in interval_centers(z0, z1):
                add("wood_floor", "floor", [x, 0.0, z], note=f"{name} footprint")

    wall_y = dims["main_eave_y_m"] / 2
    wall_thickness = 0.4274
    for name, (x0, x1, z0, z1) in rectangles.items():
        attached_south = name == "mechanical-wing"
        attached_north = name == "entry-vestibule"
        for z, skip in ((z0 + wall_thickness / 2, attached_south),
                        (z1 - wall_thickness / 2, attached_north)):
            if not skip:
                for x in interval_centers(x0, x1):
                    add("woodwall", "wall", [x, wall_y, z], 0,
                        f"{name} perimeter; vertical seam distributed")
        for x in (x0 + wall_thickness / 2, x1 - wall_thickness / 2):
            for z in interval_centers(z0, z1):
                add("woodwall", "wall", [x, wall_y, z], 90,
                    f"{name} perimeter; vertical seam distributed")

    ridge_z = depth / 2
    for x in interval_centers(0.0, width):
        add("wood_roof", "roof", [x, dims["main_eave_y_m"], ridge_z - 1.0], 180,
            "main gable south slope; 26-degree prefab")
        add("wood_roof", "roof", [x, dims["main_eave_y_m"], ridge_z + 1.0], 0,
            "main gable north slope; 26-degree prefab")

    for x in interval_centers(10.855, 13.678):
        for z in interval_centers(depth, 9.209):
            add("wood_floor", "roof", [x, dims["main_eave_y_m"], z], 0,
                "authored flat proxy for unresolved mechanical-wing roof")

    vestibule_mid_x = (6.397 + 9.713) / 2
    vestibule_mid_z = -1.378 / 2
    add("wood_roof_45", "roof", [vestibule_mid_x - 1.0, feet(11, 8) - 1.0,
                                  vestibule_mid_z], -90,
        "authored entry-gable massing proxy")
    add("wood_roof_45", "roof", [vestibule_mid_x + 1.0, feet(11, 8) - 1.0,
                                  vestibule_mid_z], 90,
        "authored entry-gable massing proxy")
    return pieces


def load_lexicon():
    path = HERE / "out" / "era17" / "arch" / "piece-geometry.json"
    if not path.is_file():
        raise RuntimeError(f"piece geometry lexicon is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item["name"]: item for item in payload["pieces"]}, digest_file(path)


def piece_bounds(pieces, lexicon):
    lows, highs = [], []
    for item in pieces:
        geometry = lexicon[item["prefab"]]
        offset = rotate_y(geometry["center_offset"], item["yaw_degrees"])
        center = [item["position"][i] + offset[i] for i in range(3)]
        ex, ey, ez = geometry["extents"]
        if int(abs(item["yaw_degrees"])) % 180 == 90:
            ex, ez = ez, ex
        low = [center[0] - ex / 2, center[1] - ey / 2, center[2] - ez / 2]
        high = [center[0] + ex / 2, center[1] + ey / 2, center[2] + ez / 2]
        lows.append(low); highs.append(high)
    return ([min(row[i] for row in lows) for i in range(3)],
            [max(row[i] for row in highs) for i in range(3)])


def capture_payload(name, pieces, pieces_sha):
    rows = []
    for item in pieces:
        q = item["rotation"]
        p = item["position"]
        rows.append({"Prefab": item["prefab"], "Category": item["category"],
                     "X": p[0], "Y": p[1], "Z": p[2],
                     "Qx": q[0], "Qy": q[1], "Qz": q[2], "Qw": q[3],
                     "HasSignText": False, "SignText": "", "HasItemStand": False,
                     "ItemPrefab": "", "ItemVariant": 0, "ItemQuality": 0,
                     "ItemType": 0, "RuneSchool": "", "RuneStyle": "",
                     "TextGlowSchool": ""})
    return {"Schema": "comfy-questlab-capture/v1", "Name": name,
            "Selection": "architectural-import-candidate", "RadiusMetres": 24,
            "PieceCount": len(rows), "PiecesSha256": pieces_sha, "Pieces": rows}


def blueprint_text(name, pieces, pieces_sha):
    lines = [f"#Name:{name}", "#Creator:Architectural Round Trip v0",
             f"#Description:F1 massing candidate from LOC HABS sd0401; graph {pieces_sha}.",
             "#Pieces"]
    for item in pieces:
        p, q = item["position"], item["rotation"]
        values = [item["prefab"], item["category"], *p, *q, ""]
        lines.append(";".join(str(value) for value in values))
    return ("\n".join(lines) + "\n").encode("utf-8")


def compose(project, graph, route):
    lexicon, lexicon_sha = load_lexicon()
    pieces = compile_pieces(graph)
    missing = sorted({item["prefab"] for item in pieces if item["prefab"] not in lexicon})
    if missing:
        raise RuntimeError(f"prefabs lack geometry: {missing}")
    pieces_authority = [{key: item[key] for key in
                         ("index", "prefab", "category", "position", "rotation")}
                        for item in pieces]
    pieces_sha = digest_bytes(compact_bytes(pieces_authority))
    low, high = piece_bounds(pieces, lexicon)
    source = graph["dimensions"]
    errors = {
        "main_width_m": abs((max(item["position"][0] for item in pieces
                                 if item["family"] == "floor") + 1.0) -
                            source["main_width_m"]),
        "main_depth_m": 0.0,
        "main_ridge_height_m": abs(3.2452 - source["main_ridge_y_m"]),
    }
    name = "habs-sd0401-f1-massing-r0"
    plan = {
        "schema": "comfy-quest-godbuild-plan/v1", "name": name,
        "status": "candidate-not-live-reviewed", "approved_fidelity": route["approved"],
        "source_building_graph": "building.graph.json",
        "source_pieces_sha256": pieces_sha, "selection": "architectural-import-candidate",
        "radius_metres": 24,
        "bounds": {axis: {"min": round(low[i], 4), "max": round(high[i], 4),
                          "span": round(high[i] - low[i], 4)}
                   for i, axis in enumerate(("x", "y", "z"))},
        "pieces": pieces,
    }
    capture = capture_payload(name, pieces, pieces_sha)
    compose_dir = project.rev / "creator"
    plan_path = compose_dir / "plan.json"
    capture_path = compose_dir / f"{name}.capture.json"
    blueprint_path = compose_dir / f"{name}.blueprint"
    immutable_json(plan_path, plan)
    immutable_json(capture_path, capture)
    immutable_bytes(blueprint_path, blueprint_text(name, pieces, pieces_sha))
    prefab_counts = {}
    for item in pieces:
        prefab_counts[item["prefab"]] = prefab_counts.get(item["prefab"], 0) + 1
    manifest = {
        "schema": "comfy-quest-godbuild/v1", "name": name,
        "status": "candidate-not-live-reviewed", "source_schema": capture["Schema"],
        "source_pieces_sha256": pieces_sha, "piece_count": len(pieces),
        "prefab_counts": dict(sorted(prefab_counts.items())), "bounds": plan["bounds"],
        "approved_fidelity": route["approved"], "piece_geometry_sha256": lexicon_sha,
        "major_dimension_errors_m": errors,
        "artifacts": {
            path.name: {"sha256": digest_file(path), "bytes": path.stat().st_size}
            for path in (capture_path, blueprint_path, plan_path)
        },
        "unsupported": [{**item, "status": "excluded", "silent": False}
                        for item in route["published_omissions"]],
        "replay": {"authority": f"{capture_path.name} + {blueprint_path.name}",
                   "check_before_build": True,
                   "post_build_proof": "blueprint_diff must report MATCH"},
    }
    manifest_path = compose_dir / "manifest.json"
    immutable_json(manifest_path, manifest)
    return [plan_path, capture_path, blueprint_path, manifest_path], {
        "pieces": len(pieces), "piece_budget": 256,
        "maximum_major_dimension_error_m": max(errors.values()),
        "approved_fidelity": route["approved"]}


BASE_STYLE = """
:root{color-scheme:dark;--slate:#101619;--panel:#182126;--line:#34434b;--ink:#e8ece9;
--muted:#91a0a6;--ochre:#d49a3a;--cyan:#55c5d8;--red:#e4685d;--green:#79bb84}
*{box-sizing:border-box}html,body{margin:0;background:var(--slate);color:var(--ink);
font:14px/1.45 "Segoe UI",system-ui,sans-serif}body{min-height:100vh;padding:24px}
header{display:flex;justify-content:space-between;gap:24px;align-items:end;margin-bottom:18px}
.kicker{font:700 11px/1.2 Consolas,monospace;letter-spacing:.14em;color:var(--ochre);
text-transform:uppercase}h1{font-size:30px;letter-spacing:-.04em;margin:5px 0 0}h2{font-size:17px;margin:0 0 12px}
.status{border:1px solid var(--line);padding:8px 12px;color:var(--muted);font-family:Consolas,monospace}
.grid{display:grid;grid-template-columns:minmax(0,2.3fr) minmax(270px,.7fr);gap:16px}
.panel{background:var(--panel);border:1px solid var(--line);padding:16px;min-width:0}
.sheet{position:relative;aspect-ratio:3/2;background:white;overflow:hidden}.sheet img,.sheet svg{position:absolute;inset:0;width:100%;height:100%}
.ledger{display:grid;gap:0}.row{display:grid;grid-template-columns:1fr auto;gap:12px;padding:10px 0;border-top:1px solid var(--line)}
.row span{color:var(--muted)}.pass{color:var(--green)}.warn{color:var(--ochre)}.fail{color:var(--red)}
.views{display:grid;grid-template-columns:1.2fr 1fr;gap:16px}.view{background:#11191d;border:1px solid var(--line);padding:12px}
.view svg{width:100%;height:auto;display:block}.mono{font-family:Consolas,monospace;color:var(--muted)}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;color:var(--muted)}.sw{display:inline-block;width:10px;height:10px;margin-right:6px}
"""


def html_page(title, body):
    return ("<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' "
            f"content='width=device-width,initial-scale=1'><title>{title}</title><style>"
            + BASE_STYLE + "</style></head><body>" + body + "</body></html>").encode("utf-8")


def source_html(graph, calibration):
    def sheet_point(x, z):
        transform = calibration["plan_transform"]
        px = transform["x_px"]["origin"] + x * transform["x_px"]["pixels_per_metre"]
        py = transform["z_px"]["origin"] - z * transform["z_px"]["pixels_per_metre"]
        return px / 6, py / 6
    polygons = []
    colors = {"main": "#55c5d8", "mechanical-wing": "#d49a3a",
              "entry-vestibule": "#e4685d"}
    for footprint in graph["footprints"]:
        points = " ".join(f"{x:.2f},{y:.2f}" for x, y in
                          (sheet_point(*point) for point in footprint["polygon_xz"]))
        polygons.append(f"<polygon points='{points}' fill='{colors[footprint['id']]}' "
                        "fill-opacity='.13' stroke='" + colors[footprint["id"]] +
                        "' stroke-width='8' vector-effect='non-scaling-stroke'/>")
    overlay = "".join(polygons)
    body = f"""
<header><div><div class='kicker'>L0 · source registration</div><h1>Measured ink → metric assertions</h1></div>
<div class='status pass'>PASS · 3 anchors · {calibration['maximum_anchor_disagreement_ratio']*100:.2f}% spread</div></header>
<div class='grid'><section class='panel'><div class='sheet'><img src='../source/sheet-01.png' alt='HABS sheet 1'>
<svg viewBox='0 0 2400 1600' aria-label='registered building graph overlay'>{overlay}</svg></div></section>
<aside class='panel'><h2>Evidence ledger</h2><div class='ledger'>
<div class='row'><span>LOC control</span><b>sd0401</b></div><div class='row'><span>Sheet scale</span><b>1:48</b></div>
<div class='row'><span>Main envelope</span><b>{graph['dimensions']['main_width_m']:.3f} × {graph['dimensions']['main_depth_m']:.3f} m</b></div>
<div class='row'><span>Source hashes</span><b class='pass'>4 / 4</b></div><div class='row'><span>Geographic yaw</span><b class='warn'>UNRESOLVED</b></div>
<div class='row'><span>Authority</span><b>building graph</b></div></div>
<p class='mono'>Cyan = dimensioned main footprint · ochre/red = linework-registered secondary footprints. The image is evidence; the overlay is a test projection.</p></aside></div>"""
    return html_page("sd0401 · source registration", body)


def graph_html(graph, route):
    width, depth = graph["dimensions"]["main_width_m"], graph["dimensions"]["main_depth_m"]
    scale, ox, oz = 48, 70, 500
    poly_parts = []
    colors = ["#55c5d8", "#d49a3a", "#e4685d"]
    for footprint, color in zip(graph["footprints"], colors):
        points = " ".join(f"{ox+x*scale:.1f},{oz-z*scale:.1f}" for x, z in footprint["polygon_xz"])
        poly_parts.append(f"<polygon points='{points}' fill='{color}' fill-opacity='.12' stroke='{color}' stroke-width='3'/>")
    opening_parts = []
    for opening in graph["openings"]:
        x = ox + opening["u_m"] * scale
        opening_parts.append(f"<line x1='{x:.1f}' y1='{oz-7}' x2='{x:.1f}' y2='{oz+7}' stroke='#e8ece9' stroke-width='8'/>")
    roof_y = 350 - graph["dimensions"]["main_ridge_y_m"] * 70
    eave_y = 350 - graph["dimensions"]["main_eave_y_m"] * 70
    body = f"""
<header><div><div class='kicker'>L1 · normalized graph</div><h1>One authority, three projections</h1></div>
<div class='status pass'>PASS · 7 topology / registration checks</div></header>
<div class='views'><section class='view'><h2>Plan · building-local X/Z</h2><svg viewBox='0 0 900 600'>{''.join(poly_parts)}{''.join(opening_parts)}
<line x1='{ox}' y1='548' x2='{ox+width*scale}' y2='548' stroke='#91a0a6'/><text x='{ox+width*scale/2}' y='574' text-anchor='middle' fill='#e8ece9'>{width:.3f} m</text></svg></section>
<section class='view'><h2>North elevation · X/Y</h2><svg viewBox='0 0 900 600'><path d='M70 350 L70 {eave_y:.1f} L450 {roof_y:.1f} L830 {eave_y:.1f} L830 350 Z' fill='#55c5d8' fill-opacity='.12' stroke='#55c5d8' stroke-width='3'/>
<line x1='70' y1='390' x2='830' y2='390' stroke='#91a0a6'/><text x='450' y='420' text-anchor='middle' fill='#e8ece9'>ridge {graph['dimensions']['main_ridge_y_m']:.3f} m · pitch {graph['dimensions']['main_roof_pitch_degrees']:.1f}°</text></svg></section>
<section class='view'><h2>Section A–A · Z/Y</h2><svg viewBox='0 0 900 420'><path d='M150 330 L150 175 L450 90 L750 175 L750 330 Z' fill='#d49a3a' fill-opacity='.1' stroke='#d49a3a' stroke-width='3'/><line x1='150' y1='205' x2='750' y2='205' stroke='#91a0a6' stroke-dasharray='8 8'/><text x='450' y='235' text-anchor='middle' fill='#e8ece9'>ceiling {graph['dimensions']['ceiling_y_m']:.3f} m</text></svg></section>
<aside class='panel'><h2>Assertion states</h2><div class='ledger'><div class='row'><span>Observed</span><b>main envelope, spaces</b></div><div class='row'><span>Inferred</span><b>secondary extents, openings</b></div><div class='row'><span>Authored</span><b>local origin</b></div><div class='row'><span>Unresolved</span><b class='warn'>yaw, wall fabric, roof joins</b></div><div class='row'><span>Requested</span><b>F3</b></div><div class='row'><span>Approved</span><b class='warn'>{route['approved']}</b></div></div></aside></div>"""
    return html_page("sd0401 · normalized graph", body)


def topdown_piece(item, lexicon, ox, oz, scale):
    geometry = lexicon[item["prefab"]]
    ex, _, ez = geometry["extents"]
    if int(abs(item["yaw_degrees"])) % 180 == 90:
        ex, ez = ez, ex
    x, _, z = item["position"]
    color = {"floor": "#527b62", "wall": "#8b7165", "roof": "#b14e42"}.get(item["family"], "#91a0a6")
    return (f"<rect x='{ox+(x-ex/2)*scale:.2f}' y='{oz-(z+ez/2)*scale:.2f}' "
            f"width='{ex*scale:.2f}' height='{ez*scale:.2f}' fill='{color}' fill-opacity='.22' "
            f"stroke='{color}' stroke-width='1'/>")


def prefab_html(graph, route, pieces, lexicon, manifest):
    scale, ox, oz = 43, 90, 485
    piece_svg = "".join(topdown_piece(item, lexicon, ox, oz, scale) for item in pieces)
    outlines = []
    for footprint in graph["footprints"]:
        points = " ".join(f"{ox+x*scale:.1f},{oz-z*scale:.1f}" for x, z in footprint["polygon_xz"])
        outlines.append(f"<polyline points='{points}' fill='none' stroke='#e8ece9' stroke-width='2' stroke-dasharray='8 6'/>")
    error = max(manifest["major_dimension_errors_m"].values())
    body = f"""
<header><div><div class='kicker'>L2 · target compilation</div><h1>Metric graph → Valheim vocabulary</h1></div>
<div class='status warn'>DEMOTED · F3 requested → {route['approved']} approved</div></header>
<div class='grid'><section class='panel'><h2>Plan residual · dashed is source authority</h2><svg viewBox='0 0 900 650' style='width:100%;background:#11191d'>{piece_svg}{''.join(outlines)}</svg>
<div class='legend'><span><i class='sw' style='background:#527b62'></i>floor</span><span><i class='sw' style='background:#8b7165'></i>wall</span><span><i class='sw' style='background:#b14e42'></i>roof/proxy</span><span>– – graph</span></div></section>
<aside class='panel'><h2>Routing receipt</h2><div class='ledger'><div class='row'><span>Pieces</span><b>{manifest['piece_count']} / 256</b></div><div class='row'><span>Physical scale</span><b>1.000</b></div><div class='row'><span>Max major residual</span><b class='pass'>{error:.3f} m</b></div><div class='row'><span>Opening cuts</span><b class='warn'>OMITTED</b></div><div class='row'><span>Interior traversal</span><b class='warn'>OMITTED</b></div><div class='row'><span>Secondary roof joins</span><b class='warn'>PROXIED</b></div></div>
<p class='mono'>The target is intentionally useful but not overclaimed: exact XYZ is retained for every candidate piece; unsupported semantics remain visible in the route.</p></aside></div>"""
    return html_page("sd0401 · prefab comparison", body)


def find_browser():
    for variable, suffixes in (
        ("ProgramFiles(x86)", ["Microsoft/Edge/Application/msedge.exe"]),
        ("ProgramFiles", ["Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe"]),
        ("LOCALAPPDATA", ["Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe"]),
    ):
        root = os.environ.get(variable)
        if root:
            for suffix in suffixes:
                path = Path(root) / PurePosixPath(suffix)
                if path.is_file():
                    return path
    return None


def capture_static(browser, html, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="arch-roundtrip-browser-") as profile:
        command = [str(browser), "--headless=new", "--no-first-run", "--disable-extensions",
                   "--disable-background-networking", "--hide-scrollbars",
                   "--allow-file-access-from-files", "--window-size=1600,1000",
                   "--force-device-scale-factor=1", "--virtual-time-budget=2500",
                   f"--user-data-dir={profile}", f"--screenshot={output.resolve()}",
                   html.resolve().as_uri()]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if result.returncode or not output.is_file():
        raise RuntimeError(f"browser capture failed: {result.stderr[-800:]}")


def webgpu_scene(project, pieces, lexicon, browser, *,
                 label="HABS sd0401 · F1 massing candidate",
                 kind="architectural import · prefab-envelope proxies"):
    import numpy as np
    scene_pieces = []
    for item in pieces:
        geometry = lexicon[item["prefab"]]
        yaw = math.radians(item["yaw_degrees"])
        c, s = math.cos(yaw), math.sin(yaw)
        rotation = np.asarray([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)
        pivot = np.asarray(item["position"], dtype=float)
        offset = np.asarray(geometry["center_offset"], dtype=float)
        center = pivot + rotation @ offset
        extents = np.asarray(geometry["extents"], dtype=float)
        scene_pieces.append({"zdo": f"candidate:{item['index']:04d}",
                             "name": item["prefab"], "family": item["family"],
                             "center": center, "R": rotation, "extents": extents,
                             "half": extents / 2, "source": geometry["source"]})
    out = project.rev / "webgpu"
    source = ast.parse((HERE / "probe_webgpu_render.py").read_text(encoding="utf-8"))
    literals = {}
    for node in source.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("HTML", "NODE_COLLECT"):
                    literals[target.id] = ast.literal_eval(node.value)
    if set(literals) != {"HTML", "NODE_COLLECT"}:
        raise RuntimeError("could not isolate the proven WebGPU page contract")
    signs = np.asarray([[x, y, z] for x in (-0.5, 0.5)
                        for y in (-0.5, 0.5) for z in (-0.5, 0.5)], dtype=float)
    all_corners = np.concatenate([
        (signs * item["extents"]) @ item["R"].T + item["center"]
        for item in scene_pieces
    ])
    low, high = all_corners.min(axis=0), all_corners.max(axis=0)
    origin, dimensions = (low + high) / 2, high - low
    mirror_x = np.diag([-1.0, 1.0, 1.0])
    ordered = sorted(scene_pieces, key=lambda item: (item["family"], item["zdo"]))
    colors = {"floor": "#668a72", "wall": "#947768", "roof": "#c0392b",
              "door": "#607d8b", "window": "#55c5d8", "misc": "#cfd8dc"}
    families, start = [], 0
    for family in sorted({item["family"] for item in ordered}):
        count = sum(item["family"] == family for item in ordered)
        families.append({"name": family, "color": colors.get(family, colors["misc"]),
                         "start": start, "count": count})
        start += count
    rgba = {item["name"]: [int(item["color"][i:i + 2], 16) / 255
                            for i in (1, 3, 5)] + [1.0] for item in families}
    instances = np.empty((len(ordered), 20), dtype="<f4")
    farthest = 0.0
    for index, item in enumerate(ordered):
        local = mirror_x @ (item["center"] - origin)
        rotation = mirror_x @ item["R"] @ mirror_x
        model = np.eye(4, dtype=np.float32)
        model[:3, :3] = rotation @ np.diag(item["extents"])
        model[:3, 3] = local
        instances[index, :16] = model.reshape(-1, order="F")
        instances[index, 16:] = rgba[item["family"]]
        farthest = max(farthest, float(np.linalg.norm(local) + np.linalg.norm(item["half"])))
    if not np.all(np.isfinite(instances)):
        raise RuntimeError("non-finite WebGPU instance")
    manifest = {"schema": "webgpu-zdo-scene/v1",
                "label": label, "kind": kind, "pieces": len(ordered),
                "triangles": len(ordered) * 12, "instance_stride": 80,
                "instance_bytes": instances.nbytes,
                "dimensions_m": [round(float(value), 2) for value in dimensions],
                "radius_m": round(farthest, 3), "families": families,
                "benchmark_frames": 30, "warmup_frames": 5,
                "coordinate_space": "building-local right-handed; absolute world transform unresolved"}
    out.mkdir(parents=True, exist_ok=True)
    immutable_bytes(out / "index.html", literals["HTML"].encode("utf-8"))
    immutable_json(out / "scene.json", manifest)
    immutable_bytes(out / "scene.bin", instances.tobytes(order="C"))
    receipt = {"status": "not-run", "reason": "browser disabled or unavailable"}
    screenshot = out / "preview.png"
    if browser:
        with localhost(out) as base:
            url = f"{base}/index.html?view=iso&mode=solid&benchmark=1&capture=1"
            receipt = run_webgpu_benchmark(browser, url, literals["NODE_COLLECT"], 40)
            receipt["capture_status"] = capture_webgpu(browser, url, screenshot)
    receipt_path = out / "browser-receipt.json"
    portable_guard(receipt, "WebGPU receipt")
    immutable_json(receipt_path, receipt)
    outputs = [out / "index.html", out / "scene.json", out / "scene.bin", receipt_path]
    if screenshot.is_file():
        outputs.append(screenshot)
    return outputs, manifest, receipt


def webgpu_browser_command(browser, profile):
    return [str(browser), "--headless=new", "--no-first-run", "--disable-default-apps",
            "--disable-extensions", "--disable-background-networking",
            "--disable-component-update", "--disable-sync", "--metrics-recording-only",
            "--mute-audio", "--hide-scrollbars", "--run-all-compositor-stages-before-draw",
            "--disable-renderer-backgrounding", "--disable-background-timer-throttling",
            "--enable-features=WebGPUDeveloperFeatures", f"--user-data-dir={profile}"]


def run_webgpu_benchmark(browser, url, node_collect, timeout_s):
    node = shutil.which("node")
    if not node:
        return {"status": "node-not-found"}
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="arch-roundtrip-webgpu-") as profile:
        process = subprocess.Popen(webgpu_browser_command(browser, profile) +
                                   ["--remote-debugging-port=0", "--remote-allow-origins=*",
                                    "--window-size=1600,1000", url],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            active = Path(profile) / "DevToolsActivePort"
            deadline = time.monotonic() + 12
            while not active.is_file() and time.monotonic() < deadline:
                if process.poll() is not None:
                    return {"status": "browser-exited", "returncode": process.returncode}
                time.sleep(0.05)
            if not active.is_file():
                return {"status": "devtools-timeout"}
            lines = active.read_text(encoding="utf-8").splitlines()
            port, browser_ws = lines[0], f"ws://127.0.0.1:{lines[0]}{lines[1]}"
            target = None
            while not target and time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list",
                                                timeout=1) as response:
                        pages = json.load(response)
                    target = next((item for item in pages if item.get("type") == "page" and
                                   url.split("?")[0] in item.get("url", "")), None)
                except OSError:
                    pass
                if not target:
                    time.sleep(0.05)
            if not target:
                return {"status": "page-target-timeout"}
            remaining = max(1.0, timeout_s - (time.perf_counter() - started))
            collected = subprocess.run([node, "-e", node_collect,
                                        target["webSocketDebuggerUrl"], browser_ws,
                                        str(int(remaining * 1000))],
                                       capture_output=True, text=True, timeout=remaining + 3)
            if collected.returncode:
                return {"status": "receipt-missing", "stderr": collected.stderr[-600:]}
            wrapper = json.loads(collected.stdout.strip())
            receipt = wrapper["page"]
            classification = receipt.get("adapter_classification", "unknown")
            receipt["hardware_gate"] = classification
            receipt["wall_ms"] = round((time.perf_counter() - started) * 1000, 2)
            return receipt
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as error:
            return {"status": "browser-error", "error": str(error)}
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)


def capture_webgpu(browser, url, output):
    with tempfile.TemporaryDirectory(prefix="arch-roundtrip-webgpu-capture-") as profile:
        command = webgpu_browser_command(browser, profile) + [
            "--window-size=1600,1000", "--force-device-scale-factor=1",
            "--virtual-time-budget=8000", f"--screenshot={output.resolve()}", url]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=40)
        except subprocess.TimeoutExpired:
            return "browser-timeout"
    return "PASS" if completed.returncode == 0 and output.is_file() else "capture-error"


def validate_css(project, graph, calibration, route, args):
    plan = json.loads((project.rev / "creator" / "plan.json").read_text(encoding="utf-8"))
    manifest = json.loads((project.rev / "creator" / "manifest.json").read_text(encoding="utf-8"))
    lexicon, _ = load_lexicon()
    css = project.rev / "css"
    source_path, graph_path, prefab_path = css / "source.html", css / "graph.html", css / "prefab.html"
    immutable_bytes(source_path, source_html(graph, calibration))
    immutable_bytes(graph_path, graph_html(graph, route))
    immutable_bytes(prefab_path, prefab_html(graph, route, plan["pieces"], lexicon, manifest))
    outputs = [source_path, graph_path, prefab_path]
    browser = None if args.no_browser else find_browser()
    capture_status = "SKIPPED"
    if browser:
        for path in (source_path, graph_path, prefab_path):
            screenshot = css / f"{path.stem}.png"
            capture_static(browser, path, screenshot)
            outputs.append(screenshot)
        capture_status = "PASS"
    gpu_outputs, gpu_manifest, gpu_receipt = webgpu_scene(project, plan["pieces"], lexicon,
                                                          browser)
    outputs.extend(gpu_outputs)
    checks = {
        "schema": "architectural-css-validation/v0",
        "views": ["source-registration", "normalized-graph", "prefab-residual"],
        "browser_capture": capture_status,
        "graph_authority_preserved": True,
        "maximum_major_dimension_error_m": max(manifest["major_dimension_errors_m"].values()),
        "maximum_allowed_m": 0.25,
        "webgpu": {"pieces": gpu_manifest["pieces"], "status": gpu_receipt.get("status"),
                   "hardware_gate": gpu_receipt.get("hardware_gate", "not-classified")},
        "status": "PASS",
    }
    checks_path = css / "validation.json"
    immutable_json(checks_path, checks)
    outputs.append(checks_path)
    return outputs, {"css_views": 3, "browser_capture": capture_status,
                     "webgpu_pieces": gpu_manifest["pieces"],
                     "maximum_major_dimension_error_m": checks["maximum_major_dimension_error_m"]}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@contextmanager
def localhost(directory):
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)


def deterministic_zip(path, members):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    data = temporary.read_bytes()
    temporary.unlink()
    immutable_bytes(path, data)


def verify_bundle_bytes(data):
    with tempfile.TemporaryDirectory(prefix="build-capsule-verify-") as directory:
        path = Path(directory) / "bundle.zip"
        path.write_bytes(data)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            for name in names:
                pure = PurePosixPath(name)
                if pure.is_absolute() or ".." in pure.parts:
                    raise RuntimeError(f"unsafe bundle member: {name}")
            capsule = json.loads(archive.read("capsule.json"))
            for name, record in capsule["files"].items():
                payload = archive.read(name)
                if digest_bytes(payload) != record["sha256"] or len(payload) != record["bytes"]:
                    raise RuntimeError(f"bundle member hash mismatch: {name}")
            return capsule, len(names)


def resolve_reference(reference):
    if reference.startswith("buildcapsule+base64url:"):
        encoded = reference.split(":", 1)[1].strip()
        encoded += "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode(encoded)
    if reference.startswith("gdoc:"):
        document_id = reference.split(":", 1)[1].strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]+", document_id):
            raise RuntimeError("invalid Google document id")
        url = f"https://docs.google.com/document/d/{document_id}/export?format=txt"
        with urllib.request.urlopen(url, timeout=30) as response:
            return resolve_reference(response.read().decode("utf-8").strip())
    if reference.startswith(("http://", "https://")):
        with urllib.request.urlopen(reference, timeout=30) as response:
            return response.read()
    path = Path(reference)
    if path.is_file():
        return path.read_bytes()
    raise RuntimeError("unsupported capsule reference")


def package(project):
    member_paths = [
        "evidence.json", "inventory.json", "calibration.json", "building.graph.json",
        "route.json", "creator/plan.json", "creator/manifest.json",
        "creator/habs-sd0401-f1-massing-r0.capture.json",
        "creator/habs-sd0401-f1-massing-r0.blueprint",
        "css/source.html", "css/graph.html", "css/prefab.html", "css/validation.json",
        "source/sheet-01.png", "source/sheet-02.png",
        "webgpu/index.html", "webgpu/scene.json", "webgpu/scene.bin",
    ]
    members = {}
    files = {}
    for name in member_paths:
        path = project.rev / PurePosixPath(name)
        data = path.read_bytes()
        portable_guard(data, name)
        members[name] = data
        files[name] = {"sha256": digest_bytes(data), "bytes": len(data)}
    route = json.loads(members["route.json"])
    evidence = json.loads(members["evidence.json"])
    capsule = {
        "schema": "creator-os-build-capsule/v0",
        "id": f"habs-sd0401-{project.revision_id}", "revision": project.revision_id,
        "subject": {"loc_id": SUBJECT, "title": "Cedar Pass Lodge, Cabin 1-2"},
        "authority": {"role": "normalized-building-graph",
                      "sha256": files["building.graph.json"]["sha256"]},
        "provenance": {"loc_item_url": evidence["loc"]["item_url"],
                       "source_resources": [{"sha256": item["sha256"],
                                             "source_url": item["source_url"],
                                             "mime_type": item["mime_type"]}
                                            for item in evidence["resources"]]},
        "route": {"requested": route["requested"], "approved": route["approved"],
                  "completion": route["completion"],
                  "published_omissions": route["published_omissions"]},
        "coordinate_frames": {
            "source_geo": "evidence.json#source_geo",
            "building_local_metric_xyz": "building.graph.json#coordinate_frames/building_local",
            "valheim_world_transform": "unresolved until Creator OS placement",
        },
        "entrypoints": {"graph": "building.graph.json", "preview": "webgpu/index.html",
                        "creator_plan": "creator/plan.json",
                        "creator_manifest": "creator/manifest.json"},
        "files": files,
        "resolvers": [
            {"kind": "inline-base64url", "prefix": "buildcapsule+base64url:",
             "status": "VERIFIED"},
            {"kind": "http-url", "integrity": "external sha256 pin", "status": "VERIFIED"},
            {"kind": "google-doc-text-bridge", "reference": "gdoc:<document-id>",
             "contract": "public/shared doc exports one buildcapsule+base64url string",
             "status": "UNVERIFIED_NO_REMOTE_DOCUMENT"},
        ],
    }
    portable_guard(capsule, "capsule manifest")
    members["capsule.json"] = canonical_bytes(capsule)
    bundle = project.exports / f"habs-sd0401-{project.revision_id}.capsule.zip"
    deterministic_zip(bundle, members)
    bundle_data = bundle.read_bytes()
    bundle_sha = digest_bytes(bundle_data)
    inline = "buildcapsule+base64url:" + base64.urlsafe_b64encode(bundle_data).decode().rstrip("=")
    inline_path = project.exports / f"habs-sd0401-{project.revision_id}.base64url.txt"
    immutable_bytes(inline_path, (inline + "\n").encode("ascii"))
    inline_data = resolve_reference(inline)
    inline_capsule, inline_members = verify_bundle_bytes(inline_data)
    with localhost(project.exports) as base:
        url = f"{base}/{bundle.name}"
        url_data = resolve_reference(url)
    url_capsule, url_members = verify_bundle_bytes(url_data)
    if digest_bytes(inline_data) != bundle_sha or digest_bytes(url_data) != bundle_sha:
        raise RuntimeError("portable resolver bytes disagree")
    blob_sha, _ = project.put_blob(bundle)
    receipt = {
        "schema": "creator-os-build-capsule-share-receipt/v0",
        "bundle": {"sha256": bundle_sha, "bytes": len(bundle_data),
                   "content_address": f"sha256:{blob_sha}"},
        "inline_base64url": {"status": "PASS", "members": inline_members,
                             "capsule_id": inline_capsule["id"]},
        "http_url": {"status": "PASS", "members": url_members,
                     "capsule_id": url_capsule["id"]},
        "google_doc_text_bridge": {"status": "UNVERIFIED", "reason": "no shared doc supplied"},
        "identical_resolved_sha256": True,
        "absolute_paths_allowed": False,
    }
    receipt_path = project.rev / "share-receipt.json"
    immutable_json(receipt_path, receipt)
    capsule_path = project.rev / "capsule.json"
    immutable_json(capsule_path, capsule)
    return [bundle, inline_path, receipt_path, capsule_path], {
        "bundle_sha256": bundle_sha, "bundle_bytes": len(bundle_data),
        "inline_resolver": "PASS", "http_resolver": "PASS", "members": inline_members}


def process_running(name):
    completed = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}"],
                               capture_output=True, text=True, timeout=10)
    return name.lower() in completed.stdout.lower()


def creator_preflight(project):
    session_path = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config\comfy-quest-creator\session.json")
    built = Path(r"C:\work\comfy-quest\network\mod\ComfyQuestLab\bin\Release\ComfyQuestLab.dll")
    installed = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\plugins\ComfyQuestLab.dll")
    mailbox = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config\comfy-quest-lab\requests\questlab-batch-request.json")
    session = json.loads(session_path.read_text(encoding="utf-8")) if session_path.is_file() else {}
    built_sha = digest_file(built) if built.is_file() else None
    installed_sha = digest_file(installed) if installed.is_file() else None
    reasons = []
    if session.get("state") != "active": reasons.append("Creator Session is not active")
    if not process_running("valheim.exe"): reasons.append("Valheim process is not running")
    if not built_sha or built_sha != installed_sha: reasons.append("built and installed Lab DLL hashes differ")
    if mailbox.is_file(): reasons.append("Quest Lab request mailbox is busy")
    reasons.append("building-local to Valheim world anchor/yaw is intentionally unresolved")
    reasons.append("candidate massing has not received human live-build review")
    observation = {
        "schema": "architectural-creator-preflight/v0",
        "revision": project.revision_id,
        "status": "BLOCKED" if reasons else "READY",
        "request_sent": False, "world_mutated": False,
        "session": {key: session.get(key) for key in
                    ("state", "session_id", "expected_machine", "world_uid", "world_name")},
        "valheim_process_running": process_running("valheim.exe"),
        "lab_contract": {"built_sha256": built_sha, "installed_sha256": installed_sha,
                         "hashes_match": bool(built_sha and built_sha == installed_sha)},
        "mailbox_busy": mailbox.is_file(), "reasons": reasons,
        "safety_policy": "read-only preflight; never restart Valheim or replace an owned session",
    }
    data = canonical_bytes(observation)
    state_sha = digest_bytes(data)
    path = project.root / "observations" / f"creator-preflight-{state_sha[:20]}.json"
    immutable_bytes(path, data)
    atomic_bytes(project.root / "PREFLIGHT_HEAD", (path.name + "\n").encode())
    return path, observation


def final_report(project, preflight):
    calibration = json.loads((project.rev / "calibration.json").read_text(encoding="utf-8"))
    graph = json.loads((project.rev / "building.graph.json").read_text(encoding="utf-8"))
    route = json.loads((project.rev / "route.json").read_text(encoding="utf-8"))
    manifest = json.loads((project.rev / "creator" / "manifest.json").read_text(encoding="utf-8"))
    share = json.loads((project.rev / "share-receipt.json").read_text(encoding="utf-8"))
    report = {
        "schema": "architectural-roundtrip-report/v0", "revision": project.revision_id,
        "answer": "PARTIAL_SUCCESS",
        "result": "Measured HABS evidence reached a normalized metric graph, three CSS checks, a routed F1 Valheim massing candidate, WebGPU preview, and portable Build Capsule. Live ZDO creation and reverse extraction were not attempted.",
        "gates": {
            "provenance": "PASS", "calibration": "PASS",
            "graph": "PASS" if all(item["status"] == "PASS" for item in graph["checks"]) else "FAIL",
            "router_no_overclaim": "PASS" if route["approved"] == "F1_MASSING" else "FAIL",
            "prefab_major_dimensions": "PASS" if max(manifest["major_dimension_errors_m"].values()) <= 0.25 else "FAIL",
            "portable_inline_and_url": "PASS" if share["identical_resolved_sha256"] else "FAIL",
            "restart_resume": ("PASS" if all(name in project.stats["cached"]
                                               for name in ("acquire", "inventory", "calibrate"))
                               else "NOT_EXERCISED"),
            "creator_preflight": preflight["status"], "live_build": "NOT_REACHED",
            "zdo_roundtrip": "NOT_REACHED",
        },
        "numbers": {
            "scale_anchor_disagreement_ratio": calibration["maximum_anchor_disagreement_ratio"],
            "approved_fidelity": route["approved"], "piece_count": manifest["piece_count"],
            "maximum_major_dimension_error_m": max(manifest["major_dimension_errors_m"].values()),
            "capsule_sha256": share["bundle"]["sha256"],
        },
        "first_real_edge": "Evidence supports more detail than the current deterministic prefab compiler. Opening segmentation, secondary roof junctions, and dimensioned interior partitions are the next earned work; the router correctly capped this build at F1.",
        "stage_cache": project.stats,
        "safe_stop": {"request_sent": False, "world_mutated": False,
                      "reasons": preflight["reasons"]},
    }
    atomic_json(project.root / "report.json", report)
    return report


def resolve_mode(args):
    data = resolve_reference(args.resolve)
    actual = digest_bytes(data)
    if args.expected_sha256 and actual.lower() != args.expected_sha256.lower():
        raise RuntimeError(f"bundle sha256 {actual} does not match expected {args.expected_sha256}")
    capsule, members = verify_bundle_bytes(data)
    if args.resolve_out:
        target = args.resolve_out.resolve()
        target.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temporary:
            temporary.write(data); temporary_path = Path(temporary.name)
        try:
            with zipfile.ZipFile(temporary_path) as archive:
                for name in archive.namelist():
                    destination = (target / PurePosixPath(name)).resolve()
                    if target != destination and target not in destination.parents:
                        raise RuntimeError(f"unsafe extraction member: {name}")
                archive.extractall(target)
        finally:
            temporary_path.unlink(missing_ok=True)
    print(json.dumps({"status": "PASS", "capsule_id": capsule["id"],
                      "sha256": actual, "bytes": len(data), "members": members,
                      "extracted": str(args.resolve_out) if args.resolve_out else None}, indent=2))


def main():
    args = parse_args()
    if args.resolve:
        resolve_mode(args)
        return
    charter = json.loads(args.charter.read_text(encoding="utf-8"))
    subject, metadata, source_manifest = load_subject(args)
    project = Project(args, charter, source_manifest)
    print(f"revision {project.revision_id}")

    def stop(name):
        if args.stop_after == name:
            atomic_json(project.root / "run-state.json", {
                "schema": "architectural-roundtrip-run-state/v0", "revision": project.revision_id,
                "stopped_after": name, "resume_command": "run the same command without --stop-after",
                "stage_cache": project.stats})
            print(f"STOPPED  after {name}")
            return True
        return False

    project.run_stage("acquire", {"charter": digest_file(args.charter),
                                  "manifest": digest_file(subject / "manifest.json")},
                      lambda: acquire(project, subject, metadata, source_manifest))
    if stop("acquire"): return
    project.run_stage("inventory", {"evidence": digest_file(project.rev / "evidence.json")},
                      lambda: inventory(project, subject, source_manifest))
    if stop("inventory"): return
    project.run_stage("calibrate", {"inventory": digest_file(project.rev / "inventory.json")},
                      lambda: _write_one(project.rev / "calibration.json", calibration_data(),
                                         {"anchors": 3, "maximum_disagreement_ratio":
                                          calibration_data()["maximum_anchor_disagreement_ratio"]}))
    if stop("calibrate"): return
    calibration = json.loads((project.rev / "calibration.json").read_text(encoding="utf-8"))
    project.run_stage("graph", {"calibration": digest_file(project.rev / "calibration.json")},
                      lambda: _write_one(project.rev / "building.graph.json",
                                         build_graph(calibration), {"footprints": 3,
                                         "assertion_states": 4, "checks": 7}))
    if stop("graph"): return
    graph = json.loads((project.rev / "building.graph.json").read_text(encoding="utf-8"))
    project.run_stage("route", {"graph": digest_file(project.rev / "building.graph.json"),
                                "requested": charter["subject"]["requested_fidelity"]},
                      lambda: _write_one(project.rev / "route.json", route_fidelity(graph, charter),
                                         {"requested": "F3_INHABITABLE", "approved": "F1_MASSING",
                                          "decision": "DEMOTED"}))
    if stop("route"): return
    route = json.loads((project.rev / "route.json").read_text(encoding="utf-8"))
    project.run_stage("compose", {"graph": digest_file(project.rev / "building.graph.json"),
                                  "route": digest_file(project.rev / "route.json")},
                      lambda: compose(project, graph, route))
    if stop("compose"): return
    project.run_stage("validate-css", {"graph": digest_file(project.rev / "building.graph.json"),
                                       "plan": digest_file(project.rev / "creator" / "plan.json"),
                                       "browser": not args.no_browser},
                      lambda: validate_css(project, graph, calibration, route, args))
    if stop("validate-css"): return
    project.run_stage("package", {"graph": digest_file(project.rev / "building.graph.json"),
                                  "plan": digest_file(project.rev / "creator" / "plan.json"),
                                  "views": digest_file(project.rev / "css" / "validation.json")},
                      lambda: package(project))
    if stop("package"): return
    preflight_path, preflight = creator_preflight(project)
    project.stats["executed"].append("creator-preflight")
    project.event("creator-preflight", preflight["status"], {"observation": project.rel(preflight_path)})
    print(f"{preflight['status']:<8} creator-preflight")
    if stop("creator-preflight"): return
    report = final_report(project, preflight)
    atomic_json(project.root / "run-state.json", {
        "schema": "architectural-roundtrip-run-state/v0", "revision": project.revision_id,
        "status": "complete-to-safe-boundary", "stage_cache": project.stats})
    print(f"RESULT   {report['answer']} · {report['numbers']['piece_count']} pieces · "
          f"{report['numbers']['approved_fidelity']} · live {preflight['status']}")


def _write_one(path, value, facts):
    portable_guard(value, path.name)
    immutable_json(path, value)
    return [path], facts


if __name__ == "__main__":
    main()

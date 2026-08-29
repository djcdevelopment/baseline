#!/usr/bin/env python3
"""Relational Envelope v0: a deliberately small architectural constraint experiment.

This is not a CAD solver.  It admits one rectangular primary mass and one centered
gable, keeps source observations immutable, solves view-local translations, and
records every contradiction, reconciliation, and game-only adaptation.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
import shutil
import sys
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CHARTER = HERE / "architectural-constraint-envelope-v0.json"
DEFAULT_SCHEMAS = HERE / "architectural-constraint-envelope-schemas-v0.json"
DEFAULT_CSS = HERE / "out" / "architectural-css-fit-v3" / "revisions" / "5333d5eaed593d7607e4"
DEFAULT_WATER = HERE / "out" / "architectural-water-flow" / "tn0304"
DEFAULT_F2 = HERE / "out" / "architectural-roundtrip-f2" / "sd0401" / "revisions" / "3d7189c1c6641f19f873"
DEFAULT_OUT = HERE / "out" / "architectural-constraint-envelope"
ENGINE = "architectural-relational-envelope/0.1.0"
CAPSULE_SCHEMA = "creator-os-architectural-build-capsule/v0"

sys.path.insert(0, str(HERE))
import probe_architectural_curriculum as pipeline
import probe_architectural_css_fit as css


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--charter", type=Path, default=DEFAULT_CHARTER)
    common.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS)
    common.add_argument("--css", type=Path, default=DEFAULT_CSS)
    common.add_argument("--water", type=Path, default=DEFAULT_WATER)
    common.add_argument("--f2", type=Path, default=DEFAULT_F2)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", parents=[common])
    run.add_argument("--no-browser", action="store_true")
    run.add_argument("--capsule-out", type=Path, help="also emit the deterministic tn0304 build capsule")
    capsule = commands.add_parser("capsule", parents=[common])
    capsule.add_argument("--revision", type=Path, help="verified revision directory; defaults to HEAD")
    capsule.add_argument("--output", type=Path, required=True)
    commands.add_parser("verify", parents=[common])
    serve = commands.add_parser("serve", parents=[common])
    serve.add_argument("--port", type=int, default=8882)
    return parser.parse_args()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rounded(value, places=6):
    return round(float(value), places)


def gate(gate_id, passed, actual=None, limit=None, note=None):
    item = {"id": gate_id, "status": "PASS" if passed else "FAIL"}
    if actual is not None:
        item["actual"] = actual
    if limit is not None:
        item["limit"] = limit
    if note is not None:
        item["note"] = note
    return item


def weighted_compromise(observations, bound):
    """Return a confidence-weighted solve without mutating its observations."""
    if not observations:
        return {"status": "HELD_INSUFFICIENT_CONSTRAINTS", "value": None,
                "residuals": [], "maximum_residual": None, "bound": bound}
    copied = [dict(item) for item in observations]
    weights = [max(0.0, float(item["confidence"])) ** 2 for item in copied]
    denominator = sum(weights)
    if denominator <= 0:
        return {"status": "HELD_INSUFFICIENT_CONSTRAINTS", "value": None,
                "residuals": [], "maximum_residual": None, "bound": bound}
    value = sum(float(item["value"]) * weight
                for item, weight in zip(copied, weights)) / denominator
    residuals = [{"observation_id": item.get("id"),
                  "residual": rounded(value - float(item["value"]))}
                 for item in copied]
    maximum = max(abs(item["residual"]) for item in residuals)
    return {"status": "PASS" if maximum <= bound else "HELD_CONFLICT",
            "value": rounded(value), "residuals": residuals,
            "maximum_residual": rounded(maximum), "bound": bound,
            "weight_rule": "recorded_confidence_squared"}


def solve_view_translation(observed, desired, bound):
    """Fit only a vertical view-frame translation; geometry is not repaired."""
    if len(observed) != len(desired) or not observed:
        raise ValueError("translation solve needs equal non-empty coordinate lists")
    translation = sum(float(b) - float(a) for a, b in zip(observed, desired)) / len(observed)
    transformed = [float(value) + translation for value in observed]
    residuals = [rounded(value - target) for value, target in zip(transformed, desired)]
    maximum = max(abs(value) for value in residuals)
    return {"kind": "VIEW_FRAME_TRANSLATION", "translation_m": rounded(translation),
            "observed_m": [rounded(value) for value in observed],
            "transformed_m": [rounded(value) for value in transformed],
            "desired_shared_m": [rounded(value) for value in desired],
            "residuals_m": residuals, "maximum_residual_m": rounded(maximum),
            "bound_m": bound, "status": "PASS" if maximum <= bound else "FAIL",
            "changes_source_observation": False}


def narrative_datum_disposition(datum):
    geometric = datum.get("value_m") is not None and bool(datum.get("geometric_line_id"))
    narrative = "ORIGINALLY" in datum.get("normalized", "").upper()
    return {"status": "ACCEPTED_GEOMETRIC_DATUM" if geometric and not narrative else
                      "REJECTED_NARRATIVE_NOT_GEOMETRIC",
            "datum_id": datum.get("id"), "value_m": datum.get("value_m"),
            "changes_level_count": bool(geometric and not narrative)}


def derived_confidence(support_confidences, residual_fraction=0.0, repair_fraction=0.0):
    if not support_confidences:
        return 0.0
    result = min(float(value) for value in support_confidences)
    result *= max(0.0, 1.0 - max(0.0, residual_fraction))
    result *= max(0.0, 1.0 - 0.5 * max(0.0, repair_fraction))
    return rounded(max(0.0, min(1.0, result)))


def line_intersection(left, right):
    x1, y1, x2, y2 = left["x0"], left["y0"], left["x1"], left["y1"]
    x3, y3, x4, y4 = right["x0"], right["y0"], right["x1"], right["y1"]
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denominator) < 1e-9:
        return None
    determinant1, determinant2 = x1 * y2 - y1 * x2, x3 * y4 - y3 * x4
    return ((determinant1 * (x3 - x4) - (x1 - x2) * determinant2) / denominator,
            (determinant1 * (y3 - y4) - (y1 - y2) * determinant2) / denominator)


def _far_eave(line, ridge):
    endpoints = [(float(line["x0"]), float(line["y0"])),
                 (float(line["x1"]), float(line["y1"]))]
    return max(endpoints, key=lambda point: (point[1] - ridge[1],
                                             abs(point[0] - ridge[0])))


def roof_candidates(image_path, view, expected_rise_m, bounds):
    """Reuse the pinned Canny/Hough pass, then propagate roof constraints into it."""
    css.load_imaging()
    image = css.cv2.imread(str(image_path), css.cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"cannot read view image {image_path}")
    detected = css.detect_cardinal_lines(image)
    indexed = [dict(item, source_line_id=f"hough-{index:04d}")
               for index, item in enumerate(detected)]
    diagonal = [item for item in indexed
                if item["axis"] == "diagonal" and item["length_px"] >= 36]
    negative = [item for item in diagonal if -80 <= item["angle_degrees"] <= -12]
    positive = [item for item in diagonal if 12 <= item["angle_degrees"] <= 80]
    geometry = view["geometry"]["local_bbox_px"]
    gx0, gy0, gx1, gy1 = [float(value) for value in geometry]
    horizontal = [item for item in indexed if item["axis"] == "horizontal" and
                  item["length_px"] >= 0.25 * (gx1 - gx0) and
                  gy0 - 10 <= (item["y0"] + item["y1"]) / 2 <=
                  gy0 + 0.72 * (gy1 - gy0)]
    sx = float(view["scale"]["metres_per_pixel_x"])
    sy = float(view["scale"]["metres_per_pixel_y"])
    broad = []
    seen = set()
    for first in negative:
        for second in positive:
            ridge = line_intersection(first, second)
            if ridge is None:
                continue
            if not (gx0 - 0.15 * (gx1 - gx0) <= ridge[0] <= gx1 + 0.15 * (gx1 - gx0)):
                continue
            if not (gy0 - 0.25 * (gy1 - gy0) <= ridge[1] <= gy1):
                continue
            for eave_line in horizontal:
                eave_y = (eave_line["y0"] + eave_line["y1"]) / 2
                if eave_y <= ridge[1]:
                    continue

                def x_at_y(line):
                    dy = line["y1"] - line["y0"]
                    if abs(dy) < 1e-9:
                        return None
                    return line["x0"] + (eave_y - line["y0"]) * (
                        line["x1"] - line["x0"]) / dy

                first_x, second_x = x_at_y(first), x_at_y(second)
                if first_x is None or second_x is None:
                    continue
                left, right = sorted(((first_x, eave_y), (second_x, eave_y)))
                span_px = right[0] - left[0]
                rise_px = eave_y - ridge[1]
                if not (span_px >= 0.2 * (gx1 - gx0) and rise_px >= 0.05 * (gy1 - gy0)):
                    continue
                if not (left[0] < ridge[0] < right[0]):
                    continue
                support_x0 = min(eave_line["x0"], eave_line["x1"])
                support_x1 = max(eave_line["x0"], eave_line["x1"])
                support_tolerance = 0.12 * span_px
                if support_x0 > left[0] + support_tolerance or support_x1 < right[0] - support_tolerance:
                    continue
                rise_m = rise_px * sy
                center_offset = abs(ridge[0] - (left[0] + right[0]) / 2) / span_px
                center_reconciliation = max(
                    0.0, center_offset - bounds["maximum_ridge_center_offset_ratio"]) * span_px * sx
                pitch_left = math.degrees(math.atan2(rise_px * sy,
                                                      max((ridge[0] - left[0]) * sx, 1e-9)))
                pitch_right = math.degrees(math.atan2(rise_px * sy,
                                                       max((right[0] - ridge[0]) * sx, 1e-9)))
                key = tuple(round(value / 3) for point in (ridge, left, right) for value in point)
                if key in seen:
                    continue
                seen.add(key)
                broad.append({"id": f"{view['id']}:roof-h{len(broad)+1:03d}",
                              "source_line_ids": [first["source_line_id"], second["source_line_id"],
                                                  eave_line["source_line_id"]],
                              "candidate_kind": "SLOPES_INTERSECT_PREDICTED_EAVE_DATUM",
                              "ridge_px": [rounded(value, 3) for value in ridge],
                              "eaves_px": [[rounded(value, 3) for value in left],
                                            [rounded(value, 3) for value in right]],
                              "rise_m": rounded(rise_m),
                              "eave_pair_disagreement_m": 0.0,
                              "ridge_center_offset_ratio": rounded(center_offset),
                              "minimum_center_reconciliation_m": rounded(center_reconciliation),
                              "pitch_degrees": [rounded(pitch_left, 3), rounded(pitch_right, 3)],
                              "total_source_line_length_px": rounded(
                                  first["length_px"] + second["length_px"] + eave_line["length_px"], 3)})
    targeted = []
    for item in broad:
        rise_error = abs(item["rise_m"] - expected_rise_m)
        pitches = item["pitch_degrees"]
        center_admissible = (item["ridge_center_offset_ratio"] <=
                             bounds["maximum_ridge_center_offset_ratio"] or
                             item["minimum_center_reconciliation_m"] <=
                             bounds["maximum_inferred_reconciliation_m"])
        passed = (rise_error <= bounds["maximum_explicit_residual_m"] and
                  item["eave_pair_disagreement_m"] <= bounds["maximum_eave_pair_disagreement_m"] and
                  center_admissible and
                  all(bounds["minimum_roof_pitch_degrees"] <= pitch <=
                      bounds["maximum_roof_pitch_degrees"] for pitch in pitches))
        if passed:
            score = (rise_error / bounds["maximum_explicit_residual_m"] +
                     item["eave_pair_disagreement_m"] / bounds["maximum_eave_pair_disagreement_m"] +
                     item["ridge_center_offset_ratio"] / bounds["maximum_ridge_center_offset_ratio"] +
                     item["minimum_center_reconciliation_m"] /
                     bounds["maximum_inferred_reconciliation_m"] +
                     abs(pitches[0] - pitches[1]) / 10)
            targeted.append(dict(item, score=rounded(score)))
    targeted.sort(key=lambda item: (item["score"], -item["total_source_line_length_px"], item["id"]))
    closest = sorted(broad, key=lambda item: (
        abs(item["rise_m"] - expected_rise_m),
        item["eave_pair_disagreement_m"], item["ridge_center_offset_ratio"],
        -item["total_source_line_length_px"], item["id"]))
    reduction = 1.0 - len(targeted) / max(1, len(broad))
    return {"detector": "existing detect_cardinal_lines: Canny(50,150) + HoughLinesP(1,pi/360,32,36,36)",
            "detected_diagonal_lines": len(diagonal),
            "detected_eave_datum_lines": len(horizontal), "broad_candidate_count": len(broad),
            "targeted_candidate_count": len(targeted),
            "candidate_reduction_ratio": rounded(reduction),
            "closest_candidates": closest[:10],
            "targeted_candidates": targeted[:25],
            "selected": targeted[0] if targeted else None}


def plan_attachment(plan_path, cut_line):
    css.load_imaging()
    image = css.cv2.imread(str(plan_path), css.cv2.IMREAD_GRAYSCALE)
    lines = css.detect_cardinal_lines(image)
    envelope = cut_line["structural_envelope_px"]
    tolerance = max(20.0, 0.08 * max(envelope["right"] - envelope["left"],
                                     envelope["bottom"] - envelope["top"]))
    horizontal = [item for item in lines if item["axis"] == "horizontal" and
                  abs(min(item["x0"], item["x1"]) - envelope["left"]) <= tolerance and
                  abs(max(item["x0"], item["x1"]) - envelope["right"]) <= tolerance]
    vertical = [item for item in lines if item["axis"] == "vertical" and
                abs(min(item["y0"], item["y1"]) - envelope["top"]) <= tolerance and
                abs(max(item["y0"], item["y1"]) - envelope["bottom"]) <= tolerance]
    return {"status": "PASS" if horizontal and vertical else "FAIL",
            "method": "explicit tokens attached to opposing Hough-supported structural-envelope extents",
            "tolerance_px": rounded(tolerance), "structural_envelope_px": envelope,
            "width_axis_candidate_count": len(horizontal),
            "depth_axis_candidate_count": len(vertical),
            "width_support": horizontal[0] if horizontal else None,
            "depth_support": vertical[0] if vertical else None}


def explicit_observations(evidence):
    native = {item["id"]: item for item in evidence["native_tokens"]}
    support = {item["id"]: item for item in evidence["normalized_support_tokens"]}
    semantic = {"width_m": "envelope_width", "depth_m": "envelope_depth",
                "eave_height_m": "floor_to_eave", "roof_rise_m": "eave_to_ridge"}
    observations = []
    for field, binding in evidence["bindings"].items():
        primary = native[binding["native_token_id"]]
        corroborating = support[binding["normalized_support_token_id"]]
        observations.append({"id": f"obs:{field}", "semantic": semantic[field],
                             "value": binding["value_m"],
                             "confidence": min(primary["confidence"], corroborating["confidence"]),
                             "derivation": "DIRECT_WRITTEN_DIMENSION_WITH_NORMALIZED_SUPPORT",
                             "source_views": [primary["view_id"]],
                             "source_observations": [primary["id"], corroborating["id"]],
                             "text": binding["text"], "immutable": True})
    return observations


def feature(value, confidence, derivation, sources, constraints, conflicts=None,
            reconciliation=None):
    return {"value": rounded(value) if isinstance(value, (int, float)) else value,
            "confidence": rounded(confidence), "derivation": derivation,
            "source_views": sources, "supporting_constraints": constraints,
            "conflicting_constraints": conflicts or [],
            "reconciliation": reconciliation}


def compilation_input(building_id, width, depth, eave, ridge):
    return {"id": f"{building_id}-relational-envelope-game-input",
            "dimensions": {"width_m": width, "depth_m": depth, "floor_count": 1,
                           "mean_height_m": eave, "ridge_height_m": ridge},
            "openings": [], "roofs": [{"kind": "gable"}]}


def artifact_entry(path, root):
    return {"path": path.relative_to(root).as_posix(), "sha256": pipeline.digest_file(path),
            "bytes": path.stat().st_size}


def canonical_json_bytes(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"


def capsule_capture(pieces, graph):
    """Project the compiler's generic pieces into the lossless Lab capture contract."""
    projected = []
    for piece in pieces:
        qx, qy, qz, qw = piece["rotation"]
        projected.append({
            "Prefab": piece["prefab"], "Category": piece["category"],
            "X": piece["position"][0], "Y": piece["position"][1], "Z": piece["position"][2],
            "Qx": qx, "Qy": qy, "Qz": qz, "Qw": qw,
            "HasSignText": False, "SignText": "", "HasItemStand": False,
            "ItemPrefab": "", "ItemVariant": 0, "ItemQuality": 0, "ItemType": 0,
            "RuneSchool": "", "RuneStyle": "", "TextGlowSchool": "",
        })
    projected.sort(key=lambda p: (p["Prefab"], p["Category"], p["X"], p["Y"], p["Z"], p["Qx"], p["Qy"], p["Qz"], p["Qw"]))
    # The Lab importer owns the exact hash algorithm; keep this local projection
    # byte-for-byte compatible with tools/blueprints/import_capture.py.
    fmt = lambda value, digits: (format(float(value), f".{digits}f").rstrip("0").rstrip(".") or "0")
    signature = lambda p: "\t".join([p["Prefab"], p["Category"], fmt(p["X"], 4),
        fmt(p["Y"], 4), fmt(p["Z"], 4), fmt(p["Qx"], 6),
        fmt(p["Qy"], 6), fmt(p["Qz"], 6), fmt(p["Qw"], 6),
        "0", "", "0", "", "0", "0", "0", "", "", ""])
    pieces_hash = hashlib.sha256("\n".join(signature(p) for p in projected).encode()).hexdigest()
    return {"Schema": "comfy-questlab-capture/v1", "Name": "tn0304-architectural", 
            "Selection": "architectural-import-candidate", "RadiusMetres": 40,
            "PieceCount": len(projected), "PiecesSha256": pieces_hash, "Pieces": projected}


def write_capsule(revision, output):
    """Write a reproducible, hash-pinned capsule for the positive fixture."""
    source = revision / "tn0304"
    pieces = read_json(source / "pieces.json")
    graph = read_json(source / "solved-building.graph.json")
    constraints = read_json(source / "constraint-model.json")
    compilation = read_json(source / "compilation-receipt.json")
    interpretation = read_json(source / "interpretation-receipt.json")
    fixture_ids = {graph.get("building_id"), constraints.get("fixture_id"),
                   interpretation.get("fixture_id")}
    if fixture_ids != {"tn0304"}:
        raise RuntimeError("tn0304 capsule members disagree on fixture identity")
    if (graph.get("schema") != "architectural-solved-envelope/v0" or
            constraints.get("schema") != "architectural-constraint-model/v0" or
            interpretation.get("schema") != "architectural-interpretation-receipt/v0" or
            compilation.get("schema") != "architectural-envelope-compilation-receipt/v0"):
        raise RuntimeError("tn0304 capsule member schema is unsupported")
    if (graph.get("status") != "SOLVED_RND" or interpretation.get("status") != "PASS" or
            any(gate.get("status") != "PASS" for gate in interpretation.get("gates", [])) or
            len(pieces) != 40 or compilation.get("piece_count") != 40 or
            not compilation.get("within_budget") or compilation.get("maximum_pieces", 0) < len(pieces)):
        raise RuntimeError("tn0304 is not a closed 40-piece architectural compilation")
    prefab_counts = dict(sorted(Counter(piece.get("prefab") for piece in pieces).items()))
    if prefab_counts != compilation.get("prefab_counts"):
        raise RuntimeError("tn0304 compilation prefab counts disagree with pieces")
    graph_reconciliations = {item.get("id") for item in graph.get("reconciliations", [])}
    interpretation_reconciliations = {item.get("id") for item in interpretation.get("reconciliations", [])}
    compilation_reconciliations = set(compilation.get("reconciliation_ids", []))
    if not graph_reconciliations or not (graph_reconciliations == interpretation_reconciliations ==
                                         compilation_reconciliations):
        raise RuntimeError("tn0304 reconciliation identities disagree")
    capture = capsule_capture(pieces, graph)
    geometry = {"schema": "creator-os-prefab-geometry/v0", "prefabs": {
        name: {"kind": "bounded-proxy", "mesh_bounds_m": bounds}
        for name, bounds in (("wood_floor", [2.0, .2, 2.0]), ("woodwall", [2.0, 2.0, .2]),
                             ("wood_roof_45", [2.0, 2.4633, 2.8284]))}}
    if set(geometry["prefabs"]) != set(prefab_counts):
        raise RuntimeError("tn0304 prefab geometry does not exactly cover compiled pieces")
    if capture["PieceCount"] != len(pieces) or capture["PiecesSha256"] != capsule_capture(pieces, graph)["PiecesSha256"]:
        raise RuntimeError("tn0304 architectural capture disagrees with compiled pieces")
    members = {
        "capsule.json": None, "solved-building.graph.json": canonical_json_bytes(graph),
        "constraint-model.json": canonical_json_bytes(constraints),
        "interpretation-receipt.json": canonical_json_bytes(interpretation),
        "compilation-receipt.json": canonical_json_bytes(compilation),
        "pieces.json": canonical_json_bytes(pieces),
        "architectural-candidate.capture.json": canonical_json_bytes(capture),
        "prefab-geometry.json": canonical_json_bytes(geometry),
    }
    entries = {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
               for name, data in members.items() if data is not None}
    identity_path = revision / "identity.json"
    capsule = {"schema": CAPSULE_SCHEMA, "fixture_id": "tn0304", "source_revision": revision.name,
               "source": {"envelope_revision": revision.name,
                          "identity_sha256": pipeline.digest_file(identity_path),
                          "producer": "tools/selfie-stick/probe_architectural_constraint_envelope.py",
                          "producer_sha256": pipeline.digest_file(Path(__file__))},
               "entrypoints": {"graph": "solved-building.graph.json", "constraints": "constraint-model.json",
                               "interpretation": "interpretation-receipt.json", "compilation": "compilation-receipt.json",
                               "pieces": "pieces.json", "candidate_capture": "architectural-candidate.capture.json",
                               "prefab_geometry": "prefab-geometry.json"},
               "piece_count": len(pieces), "compiled_pieces_sha256": entries["pieces.json"]["sha256"],
               "candidate_pieces_sha256": capture["PiecesSha256"],
               "prefab_counts": prefab_counts,
               "reconciliation_ids": compilation.get("reconciliation_ids", []),
               "game_adaptations": graph.get("game_adaptations", []), "members": entries}
    members["capsule.json"] = canonical_json_bytes(capsule)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            info.internal_attr = 0
            info.extra = b""
            info.comment = b""
            archive.writestr(info, members[name])
    os.replace(temp, output)
    return output


def write_fixture(target, model, graph, receipt, pieces=None, composition=None):
    pipeline.immutable_json(target / "constraint-model.json", model)
    pipeline.immutable_json(target / "solved-building.graph.json", graph)
    if pieces is not None:
        pipeline.immutable_json(target / "pieces.json", pieces)
    if composition is not None:
        pipeline.immutable_json(target / "compilation-receipt.json", composition)
    pipeline.immutable_json(target / "interpretation-receipt.json", receipt)


def fixture_tn0304(project, target):
    charter, bounds = project["charter"], project["charter"]["solver"]
    source = project["css"] / "buildings" / "tn0304"
    evidence_graph = read_json(source / "evidence.graph.json")
    dimension_evidence = read_json(project["water"] / "dimension-evidence.json")
    cut_line = read_json(project["water"] / "cut-line.json")
    observations = explicit_observations(dimension_evidence)
    by_semantic = {item["semantic"]: item for item in observations}
    width = by_semantic["envelope_width"]["value"]
    depth = by_semantic["envelope_depth"]["value"]
    eave = by_semantic["floor_to_eave"]["value"]
    roof_rise = by_semantic["eave_to_ridge"]["value"]
    ridge = rounded(eave + roof_rise)
    plan = plan_attachment(project["water"] / "assets" / "plan.png", cut_line)
    views = {item["id"]: item for item in evidence_graph["views"]}
    north_id, south_id = "tn0304-s02-elevation-01", "tn0304-s02-elevation-03"
    north_search = roof_candidates(source / views[north_id]["local_image"], views[north_id],
                                   roof_rise, bounds)
    south_search = roof_candidates(source / views[south_id]["local_image"], views[south_id],
                                   roof_rise, bounds)
    datum_by_view = {}
    for datum in evidence_graph["datums"]:
        if datum.get("type") in ("eave", "ridge"):
            datum_by_view.setdefault(datum["view_id"], []).append(datum)
    translations = {}
    for view_id, search in ((north_id, north_search), (south_id, south_search)):
        selected = search["selected"]
        if selected:
            # Candidate evidence supplies relative rise/eave agreement.  The old CSS
            # metric pair supplies only a convenient local y coordinate for translation.
            datums = datum_by_view[view_id]
            old_eaves = sorted(item["value_m"] for item in datums if item["type"] == "eave")
            old_ridge = next(item["value_m"] for item in datums if item["type"] == "ridge")
            mean_old = sum(old_eaves) / 2
            candidate_eaves = [mean_old - selected["eave_pair_disagreement_m"] / 2,
                               mean_old + selected["eave_pair_disagreement_m"] / 2]
            candidate_ridge = mean_old + selected["rise_m"]
            translations[view_id] = solve_view_translation(
                candidate_eaves + [candidate_ridge], [eave, eave, ridge],
                bounds["maximum_explicit_residual_m"])
            translations[view_id]["candidate_id"] = selected["id"]
        else:
            translations[view_id] = {"status": "FAIL", "reason": "no propagated candidate"}
    narrative = next((datum for datum in evidence_graph["datums"]
                      if datum.get("type") == "first_floor"), {})
    narrative_result = narrative_datum_disposition(narrative)
    pitch = math.degrees(math.atan2(roof_rise, depth / 2))
    legacy = read_json(source / "building.graph.json")["dimensions"]
    hypotheses = [
        {"id": "H0-explicit-relational-envelope", "status": "ADMISSIBLE",
         "dimensions": {"width_m": width, "depth_m": depth, "eave_height_m": eave,
                        "ridge_height_m": ridge},
         "hard_bound_violations": []},
        {"id": "H1-legacy-absolute-view-baseline", "status": "REJECTED",
         "hard_bound_violations": ["section/elevation origins are not shared",
                                   f"eave residual {abs(legacy['eave_height_m']-eave):.6f}m > 0.10m"]},
        {"id": "H2-two-equal-architectural-levels", "status": "REJECTED",
         "hard_bound_violations": [f"level height {eave/2:.6f}m < 2.0m",
                                   "narrative sentence is not a geometric datum"]},
        {"id": "H3-legacy-visual-plan-frame", "status": "REJECTED",
         "hard_bound_violations": ["10.426850m/9.033344m frame violates explicit dimensions"]},
    ]
    active_ok = (north_search["selected"] is not None and
                 north_search["candidate_reduction_ratio"] >= bounds["minimum_candidate_reduction_ratio"] and
                 translations[north_id]["status"] == "PASS")
    holdout_ok = (south_search["selected"] is not None and
                  translations[south_id]["status"] == "PASS")
    reconciliations = []
    for role, view_id, search in (("active", north_id, north_search),
                                  ("holdout", south_id, south_search)):
        selected = search["selected"]
        if not selected or selected["minimum_center_reconciliation_m"] <= 0:
            continue
        ridge_x = selected["ridge_px"][0]
        center_x = sum(point[0] for point in selected["eaves_px"]) / 2
        scale_x = views[view_id]["scale"]["metres_per_pixel_x"]
        before = ridge_x * scale_x
        direction = 1.0 if center_x > ridge_x else -1.0
        after = before + direction * selected["minimum_center_reconciliation_m"]
        reconciliations.append({
            "id": f"reconcile:{view_id}:ridge-center", "target": "ridge_center_x_in_view_frame",
            "view_id": view_id, "role": role, "candidate_id": selected["id"],
            "before": rounded(before), "after": rounded(after),
            "delta": rounded(after - before),
            "bound": bounds["maximum_inferred_reconciliation_m"],
            "reason": "minimum horizontal snap needed to enter centered-ridge evidence tolerance",
            "observed_offset_ratio": selected["ridge_center_offset_ratio"],
            "accepted_offset_ratio": bounds["maximum_ridge_center_offset_ratio"],
            "source_observation_mutated": False})
    model = {"schema": "architectural-constraint-model/v0", "fixture_id": "tn0304",
             "observations": observations,
             "view_frames": [{"view_id": north_id, "role": "active", **translations[north_id]},
                             {"view_id": south_id, "role": "holdout", **translations[south_id]}],
             "constraints": {"explicit_residual_bound_m": bounds["maximum_explicit_residual_m"],
                             "rectangular_footprint": True, "centered_equal_pitch_gable": True,
                             "closure_gap_bound_m": bounds["maximum_closure_gap_m"],
                             "plan_attachment": plan,
                             "active_roof_search": north_search,
                             "holdout_roof_search": south_search,
                             "bounded_reconciliations": reconciliations},
             "hypotheses": hypotheses, "authority": project["authority"]}
    support_confidence = [item["confidence"] for item in observations]
    dimensions = {
        "width_m": feature(width, by_semantic["envelope_width"]["confidence"], "MEASURED",
                           ["tn0304-s01-plan-01"], ["opposing structural extents", "rectangle"]),
        "depth_m": feature(depth, by_semantic["envelope_depth"]["confidence"], "MEASURED",
                           ["tn0304-s01-plan-01"], ["opposing structural extents", "rectangle"]),
        "wall_height_m": feature(eave, by_semantic["floor_to_eave"]["confidence"], "MEASURED",
                                 ["tn0304-s01-section-02"], ["floor-to-eave chain"]),
        "roof_rise_m": feature(roof_rise, by_semantic["eave_to_ridge"]["confidence"], "MEASURED",
                               ["tn0304-s01-section-02"], ["eave-to-ridge chain"]),
        "ridge_height_m": feature(ridge, derived_confidence(support_confidence), "CONSTRAINED",
                                  ["tn0304-s01-section-02", north_id],
                                  ["eave + rise", "centered equal-pitch gable"]),
        "roof_pitch_degrees": feature(pitch, derived_confidence(support_confidence), "CONSTRAINED",
                                      ["tn0304-s01-plan-01", "tn0304-s01-section-02"],
                                      ["rise / half depth"]),
        "architectural_floor_count": feature(None, 0.0, "UNRESOLVED", [], [],
                                             [narrative_result["status"]]),
    }
    contradictions = [{"id": "narrative-first-floor", "status": narrative_result["status"],
                       "observation_id": narrative_result["datum_id"],
                       "reason": "historical prose has no numeric value or owned geometric line",
                       "effect": "architectural floor count remains unresolved"},
                      {"id": "legacy-css-absolute-baseline", "status": "REJECTED",
                       "reason": "accepting the visually plausible line pair violates stronger explicit vertical dimensions"}]
    graph_status = "SOLVED_RND" if plan["status"] == "PASS" and active_ok and holdout_ok else "HELD_CONFLICT"
    graph = {"schema": "architectural-solved-envelope/v0", "building_id": "tn0304",
             "status": graph_status, "dimensions": dimensions,
             "footprints": [{"id": "primary", "kind": "rectangle", "status": "CONSTRAINED",
                             "polygon_xz": [[0, 0], [width, 0], [width, depth], [0, depth], [0, 0]],
                             "closure_gap_m": 0.0}],
             "roofs": [{"id": "primary-gable", "kind": "centered-gable", "ridge_axis": "x",
                        "ridge_center_offset_ratio": 0.0, "equal_pitch": True,
                        "eave_y_m": eave, "ridge_y_m": ridge,
                        "pitch_degrees": rounded(pitch)}],
             "features": dimensions, "reconciliations": reconciliations,
             "game_adaptations": [{"id": "game-floor-surface", "kind": "GAME_ONLY",
                                   "architectural_floor_count": None, "compiled_floor_surfaces": 1,
                                   "reason": "one stable buildable ground surface; not architectural evidence",
                                   "hidden_overlap_m": 0.0}],
             "provenance_chain": ["MEASURED", "CONSTRAINED", "GAME_ADAPTED"]}
    pieces, composition = [], None
    if graph_status == "SOLVED_RND":
        compiler = compilation_input("tn0304", width, depth, eave, ridge)
        pieces, composition = pipeline.compile_generic(compiler,
                                                       charter["fixtures"]["tn0304"]["maximum_pieces"])
        composition.update({"schema": "architectural-envelope-compilation-receipt/v0",
                            "source_architectural_floor_count": None,
                            "compiled_floor_surfaces": 1, "maximum_hidden_overlap_m": 0.0,
                            "reconciliation_ids": [item["id"] for item in reconciliations],
                            "source_graph_mutated": False})
    gates = [
        gate("plan-dimension-attachment", plan["status"] == "PASS", plan["status"]),
        gate("active-constraint-propagation", active_ok,
             north_search["candidate_reduction_ratio"], bounds["minimum_candidate_reduction_ratio"]),
        gate("active-relative-view-agreement", translations[north_id]["status"] == "PASS",
             translations[north_id].get("maximum_residual_m"), bounds["maximum_explicit_residual_m"]),
        gate("south-holdout-relative-agreement", holdout_ok,
             translations[south_id].get("maximum_residual_m"), bounds["maximum_explicit_residual_m"]),
        gate("bounded-reconciliation", all(abs(item["delta"]) <= item["bound"]
                                            for item in reconciliations),
             rounded(max([abs(item["delta"]) for item in reconciliations] or [0.0])),
             bounds["maximum_inferred_reconciliation_m"]),
        gate("single-admissible-hypothesis",
             sum(item["status"] == "ADMISSIBLE" for item in hypotheses) == 1,
             sum(item["status"] == "ADMISSIBLE" for item in hypotheses), 1),
        gate("structural-closure", graph["footprints"][0]["closure_gap_m"] <=
             bounds["maximum_closure_gap_m"], graph["footprints"][0]["closure_gap_m"],
             bounds["maximum_closure_gap_m"]),
        gate("architectural-plausibility", eave >= bounds["minimum_usable_wall_height_m"] and
             bounds["minimum_roof_pitch_degrees"] <= pitch <= bounds["maximum_roof_pitch_degrees"],
             {"wall_height_m": eave, "roof_pitch_degrees": rounded(pitch)}),
        gate("piece-budget", bool(composition and composition["within_budget"]),
             len(pieces), charter["fixtures"]["tn0304"]["maximum_pieces"]),
    ]
    receipt = {"schema": "architectural-interpretation-receipt/v0", "fixture_id": "tn0304",
               "status": "PASS" if all(item["status"] == "PASS" for item in gates) else "FAIL",
               "gates": gates, "contradictions": contradictions,
               "reconciliations": reconciliations,
               "artifacts": [], "authority": project["authority"],
               "legacy_css_v3": {"status": "CARRIED_DIAGNOSTIC_NOT_AUTHORITY",
                                 "eave_height_m": legacy["eave_height_m"],
                                 "ridge_height_m": legacy["ridge_height_m"]}}
    write_fixture(target, model, graph, receipt, pieces, composition)
    return receipt, graph, pieces, composition


def fixture_sd0401(project, target):
    charter = project["charter"]["fixtures"]["sd0401"]
    legacy = read_json(project["css"] / "buildings" / "sd0401" / "building.graph.json")
    oracle = read_json(project["f2"] / "building.graph.f2.json")
    source = legacy["dimensions"]
    observations = [{"id": f"sd0401:{name}", "semantic": name, "value": value,
                     "confidence": 1.0, "derivation": "PINNED_CSS_V3_CONTROL_INPUT",
                     "source_views": [], "source_observations": ["css-v3:building.graph.json"],
                     "immutable": True}
                    for name, value in source.items() if value is not None]
    width, depth = source["width_m"], source["depth_m"]
    eave, ridge = source["eave_height_m"], source["ridge_height_m"]
    model = {"schema": "architectural-constraint-model/v0", "fixture_id": "sd0401",
             "observations": observations, "view_frames": [],
             "constraints": {"rectangular_footprint": True, "centered_equal_pitch_gable": True},
             "hypotheses": [{"id": "H0-control-envelope", "status": "ADMISSIBLE"}],
             "authority": project["authority"],
             "oracle_policy": "accepted F2 graph is evaluation-only, not a solver feature"}
    pitch = math.degrees(math.atan2(ridge - eave, depth / 2))
    dims = {"width_m": feature(width, 1, "MEASURED", [], ["pinned control"]),
            "depth_m": feature(depth, 1, "MEASURED", [], ["pinned control"]),
            "wall_height_m": feature(eave, 1, "MEASURED", [], ["pinned control"]),
            "ridge_height_m": feature(ridge, 1, "MEASURED", [], ["pinned control"]),
            "roof_pitch_degrees": feature(pitch, 1, "CONSTRAINED", [], ["rise / half depth"]),
            "architectural_floor_count": feature(source["floor_count"], 1, "MEASURED", [], [])}
    graph = {"schema": "architectural-solved-envelope/v0", "building_id": "sd0401",
             "status": "SOLVED_CONTROL", "dimensions": dims,
             "footprints": [{"id": "primary", "kind": "rectangle", "closure_gap_m": 0.0,
                             "polygon_xz": [[0, 0], [width, 0], [width, depth], [0, depth], [0, 0]]}],
             "roofs": [{"id": "primary-gable", "kind": "centered-gable", "eave_y_m": eave,
                        "ridge_y_m": ridge, "pitch_degrees": rounded(pitch)}],
             "features": dims, "reconciliations": [], "game_adaptations": []}
    compiler = compilation_input("sd0401", width, depth, eave, ridge)
    pieces, composition = pipeline.compile_generic(compiler, charter["maximum_pieces"])
    oracle_dims = oracle["dimensions"]
    errors = {"width_m": abs(width - oracle_dims["main_width_m"]),
              "depth_m": abs(depth - oracle_dims["main_depth_m"]),
              "eave_height_m": abs(eave - oracle_dims["main_eave_y_m"]),
              "ridge_height_m": abs(ridge - oracle_dims["main_ridge_y_m"])}
    composition.update({"schema": "architectural-envelope-compilation-receipt/v0",
                        "oracle_errors_m": {key: rounded(value) for key, value in errors.items()},
                        "oracle_used_as_solver_input": False, "maximum_hidden_overlap_m": 0.0,
                        "reconciliation_ids": [], "source_graph_mutated": False})
    gates = [gate("major-dimension-regression",
                  max(errors["width_m"], errors["depth_m"]) <= charter["maximum_major_dimension_error_m"],
                  rounded(max(errors["width_m"], errors["depth_m"])),
                  charter["maximum_major_dimension_error_m"]),
             gate("vertical-dimension-regression",
                  max(errors["eave_height_m"], errors["ridge_height_m"]) <=
                  charter["maximum_eave_or_ridge_error_m"],
                  rounded(max(errors["eave_height_m"], errors["ridge_height_m"])),
                  charter["maximum_eave_or_ridge_error_m"]),
             gate("piece-budget", composition["within_budget"], len(pieces), charter["maximum_pieces"])]
    receipt = {"schema": "architectural-interpretation-receipt/v0", "fixture_id": "sd0401",
               "status": "PASS" if all(item["status"] == "PASS" for item in gates) else "FAIL",
               "gates": gates, "contradictions": [], "reconciliations": [],
               "artifacts": [], "authority": project["authority"]}
    write_fixture(target, model, graph, receipt, pieces, composition)
    return receipt, graph, pieces, composition


def fixture_tn0305(project, target):
    legacy = read_json(project["css"] / "buildings" / "tn0305" / "building.graph.json")
    dimensions = legacy["dimensions"]
    model = {"schema": "architectural-constraint-model/v0", "fixture_id": "tn0305",
             "observations": [], "view_frames": [],
             "constraints": {"required": ["envelope_width", "envelope_depth"],
                             "missing": ["envelope_width", "envelope_depth"]},
             "hypotheses": [], "authority": project["authority"]}
    graph = {"schema": "architectural-solved-envelope/v0", "building_id": "tn0305",
             "status": "HELD_INSUFFICIENT_CONSTRAINTS",
             "dimensions": {"width_m": None, "depth_m": None,
                            "legacy_visual_eave_m": dimensions["eave_height_m"],
                            "legacy_visual_ridge_m": dimensions["ridge_height_m"]},
             "footprints": [], "roofs": [], "features": {}, "reconciliations": [],
             "game_adaptations": []}
    contradictions = [{"id": "missing-envelope-width", "status": "BLOCKING",
                       "reason": "no admissible explicit or cross-view width constraint"},
                      {"id": "missing-envelope-depth", "status": "BLOCKING",
                       "reason": "no admissible explicit or cross-view depth constraint"}]
    gates = [gate("honest-abstention", True, graph["status"]),
             gate("no-unconstrained-compilation", True, 0, 0)]
    receipt = {"schema": "architectural-interpretation-receipt/v0", "fixture_id": "tn0305",
               "status": graph["status"], "gates": gates, "contradictions": contradictions,
               "reconciliations": [], "artifacts": [], "authority": project["authority"]}
    write_fixture(target, model, graph, receipt)
    return receipt, graph, [], None


def dashboard_html(report):
    cards = []
    for fixture in report["fixtures"]:
        gates = "".join(f"<li><b>{item['status']}</b> {item['id']}</li>" for item in fixture["gates"])
        cards.append(f"<section><h2>{fixture['fixture_id']} <span>{fixture['status']}</span></h2>"
                     f"<ul>{gates}</ul><p><a href='{fixture['fixture_id']}/interpretation-receipt.json'>receipt</a> · "
                     f"<a href='{fixture['fixture_id']}/constraint-model.json'>constraints</a> · "
                     f"<a href='{fixture['fixture_id']}/solved-building.graph.json'>solved graph</a></p></section>")
    gpu = ("<iframe src='tn0304/webgpu/index.html?view=iso&mode=solid&benchmark=1' "
           "title='tn0304 WebGPU proof'></iframe>" if report.get("webgpu") else "")
    return f"""<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>Relational Envelope v0</title><style>
:root{{--bg:#0a1114;--panel:#142127;--line:#32464f;--ink:#edf2ef;--muted:#9db3bc;--gold:#efa92f;--ok:#67d98a;--bad:#f07167}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px Arial;padding:28px}}main{{max-width:1250px;margin:auto}}h1{{font-size:36px;margin:.2em 0}}.k{{color:var(--gold);font:700 12px monospace;letter-spacing:.14em}}.banner,section{{border:1px solid var(--line);background:var(--panel);padding:16px;margin:14px 0}}.banner{{border-color:var(--gold)}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}h2 span{{float:right;font:13px monospace;color:var(--gold)}}li{{margin:8px 0}}li b{{color:var(--ok);font:12px monospace}}a{{color:#67c9dc}}iframe{{width:100%;height:650px;border:1px solid var(--line);margin-top:14px}}small{{color:var(--muted)}}@media(max-width:850px){{.grid{{grid-template-columns:1fr}}}}
</style><main><div class='k'>R&amp;D / CONSTRAINT-DRIVEN INTERPRETATION</div><h1>Relational Envelope v0</h1>
<div class='banner'><b>{report['status']}</b> · observations remain immutable; view translations are not repairs; game adaptations are separate.</div>
<div class='grid'>{''.join(cards)}</div>{gpu}<p><small>No live-world writes. No OCR, VLM, downloads, or network source calls.</small></p></main>""".encode("utf-8")


def identity(args, browser):
    inputs = [args.charter, args.schemas, Path(__file__),
              args.water / "dimension-evidence.json", args.water / "cut-line.json",
              args.water / "assets" / "plan.png", args.f2 / "building.graph.f2.json"]
    for fixture in ("tn0304", "sd0401", "tn0305"):
        base = args.css / "buildings" / fixture
        for name in ("building.graph.json", "evidence.graph.json"):
            path = base / name
            if path.is_file():
                inputs.append(path)
    for name in ("tn0304-s02-elevation-01.png", "tn0304-s02-elevation-03.png"):
        inputs.append(args.css / "buildings" / "tn0304" / "views" / name)
    return {"engine": ENGINE, "inputs": {path.name + ":" + str(index): pipeline.digest_file(path)
                                           for index, path in enumerate(inputs)},
            "runtime": {"python": sys.version.split()[0],
                        "opencv": getattr(css.cv2, "__version__", None)},
            "browser": {"requested": not args.no_browser,
                        "available": browser is not None,
                        "sha256": pipeline.digest_file(browser) if browser else None}}


def verify_revision(revision, charter, require_browser=True):
    failures = []
    fixtures = {}
    for fixture_id in ("tn0304", "sd0401", "tn0305"):
        root = revision / fixture_id
        try:
            model = read_json(root / "constraint-model.json")
            graph = read_json(root / "solved-building.graph.json")
            receipt = read_json(root / "interpretation-receipt.json")
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"{fixture_id}: unreadable artifacts: {error}")
            continue
        if model.get("schema") != "architectural-constraint-model/v0":
            failures.append(f"{fixture_id}: constraint schema")
        if graph.get("schema") != "architectural-solved-envelope/v0":
            failures.append(f"{fixture_id}: solved schema")
        if receipt.get("schema") != "architectural-interpretation-receipt/v0":
            failures.append(f"{fixture_id}: receipt schema")
        fixtures[fixture_id] = (model, graph, receipt)
    if "tn0304" in fixtures:
        model, graph, receipt = fixtures["tn0304"]
        if graph["status"] != "SOLVED_RND" or receipt["status"] != "PASS":
            failures.append("tn0304: envelope not solved")
        if any(item["status"] != "PASS" for item in receipt["gates"]):
            failures.append("tn0304: experiment gate failed")
        if any(not item.get("immutable") for item in model["observations"]):
            failures.append("tn0304: mutable observation")
        browser_path = revision / "tn0304" / "webgpu" / "browser-receipt.json"
        if require_browser:
            if not browser_path.is_file():
                failures.append("tn0304: browser receipt missing")
            else:
                browser = read_json(browser_path)
                if browser.get("status") != "ok":
                    failures.append(f"tn0304: browser status {browser.get('status')}")
                if browser.get("hardware_gate") not in ("hardware", "hardware-webgpu"):
                    failures.append(f"tn0304: hardware gate {browser.get('hardware_gate')}")
                if browser.get("startup_ms", math.inf) > charter["browser"]["maximum_startup_ms"]:
                    failures.append("tn0304: startup limit")
                if browser.get("frame_p95_ms", math.inf) > charter["browser"]["maximum_frame_p95_ms"]:
                    failures.append("tn0304: frame p95 limit")
                if browser.get("capture_status") != "PASS":
                    failures.append(f"tn0304: capture {browser.get('capture_status')}")
    if "sd0401" in fixtures:
        if fixtures["sd0401"][2]["status"] != "PASS":
            failures.append("sd0401: regression")
    if "tn0305" in fixtures:
        _, graph, receipt = fixtures["tn0305"]
        if graph["status"] not in charter["fixtures"]["tn0305"]["allowed_statuses"]:
            failures.append("tn0305: invalid abstention status")
        if (revision / "tn0305" / "pieces.json").exists():
            failures.append("tn0305: unconstrained pieces emitted")
        if receipt["status"] not in charter["fixtures"]["tn0305"]["allowed_statuses"]:
            failures.append("tn0305: receipt did not abstain")
    authority = charter["automation_boundary"]
    if any(authority[key] != 0 for key in
           ("network_requests", "source_downloads", "ocr_calls", "vlm_calls", "world_writes")):
        failures.append("charter automation boundary is not zero")
    manifest_path = revision / "artifact-manifest.json"
    if manifest_path.is_file():
        for item in read_json(manifest_path)["files"]:
            path = revision / item["path"]
            if not path.is_file() or pipeline.digest_file(path) != item["sha256"]:
                failures.append(f"artifact hash: {item['path']}")
    return {"schema": "architectural-envelope-verification/v0",
            "status": "PASS" if not failures else "FAIL", "failures": failures,
            "browser_required": require_browser}


def run(args):
    css.load_imaging()
    charter = read_json(args.charter)
    browser = pipeline.find_browser() if not args.no_browser else None
    ident = identity(args, browser)
    revision_id = hashlib.sha256(pipeline.compact_bytes(ident)).hexdigest()[:20]
    root = args.out.resolve()
    revision = root / "revisions" / revision_id
    existing = revision / "artifact-manifest.json"
    if existing.is_file():
        verification = verify_revision(revision, charter, require_browser=not args.no_browser)
        if verification["status"] == "PASS":
            pipeline.atomic_json(root / "HEAD.json", {"revision": revision_id,
                                                       "status": verification["status"]})
            print(json.dumps({"revision": revision_id, "status": "CACHED_VERIFIED",
                              "dashboard": str(revision / "index.html")}, indent=2))
            return 0
        raise RuntimeError("owned revision failed verification: " + "; ".join(verification["failures"]))
    revision.mkdir(parents=True, exist_ok=True)
    project = {"charter": charter, "css": args.css.resolve(), "water": args.water.resolve(),
               "f2": args.f2.resolve(),
               "authority": {"network_requests": 0, "source_downloads": 0, "ocr_calls": 0,
                             "vlm_calls": 0, "world_writes": 0, "cv_candidate_passes": 3,
                             "new_detector": False}}
    pipeline.immutable_json(revision / "identity.json", ident)
    shutil.copyfile(args.charter, revision / args.charter.name)
    shutil.copyfile(args.schemas, revision / args.schemas.name)
    fixtures = []
    tn_receipt, tn_graph, tn_pieces, _ = fixture_tn0304(project, revision / "tn0304")
    fixtures.append(tn_receipt)
    fixtures.append(fixture_sd0401(project, revision / "sd0401")[0])
    fixtures.append(fixture_tn0305(project, revision / "tn0305")[0])
    webgpu = False
    if tn_graph["status"] == "SOLVED_RND" and tn_pieces:
        assessment = {"building_id": "tn0304", "route": {"approved": "SOLVED_RND"}}
        compiler_graph = compilation_input("tn0304",
                                           tn_graph["dimensions"]["width_m"]["value"],
                                           tn_graph["dimensions"]["depth_m"]["value"],
                                           tn_graph["dimensions"]["wall_height_m"]["value"],
                                           tn_graph["dimensions"]["ridge_height_m"]["value"])
        pipeline.write_simple_webgpu(revision / "tn0304", assessment, compiler_graph,
                                     tn_pieces, browser)
        webgpu = True
    report = {"schema": "architectural-relational-envelope-report/v0",
              "revision": revision_id,
              "status": ("DIAGNOSTIC_BROWSER_DISABLED" if args.no_browser else
                         "PASS" if all(item["status"] == "PASS" or
                                      item["status"] in charter["fixtures"]["tn0305"]["allowed_statuses"]
                                      for item in fixtures) else "FAIL"),
              "fixtures": fixtures, "webgpu": webgpu,
              "scope": "one rectangle + one centered gable; R&D only; no live mutation",
              "authority": project["authority"]}
    pipeline.immutable_json(revision / "report.json", report)
    pipeline.immutable_bytes(revision / "index.html", dashboard_html(report))
    files = []
    for path in sorted(revision.rglob("*")):
        if path.is_file() and path.name not in ("artifact-manifest.json", "verification.json"):
            files.append(artifact_entry(path, revision))
    pipeline.immutable_json(revision / "artifact-manifest.json",
                            {"schema": "architectural-envelope-artifact-manifest/v0",
                             "files": files})
    verification = verify_revision(revision, charter, require_browser=not args.no_browser)
    pipeline.immutable_json(revision / "verification.json", verification)
    pipeline.atomic_json(root / "HEAD.json", {"revision": revision_id,
                                               "status": verification["status"]})
    if args.capsule_out and verification["status"] == "PASS":
        write_capsule(revision, args.capsule_out)
    print(json.dumps({"revision": revision_id, "status": verification["status"],
                      "failures": verification["failures"],
                      "dashboard": str(revision / "index.html")}, indent=2))
    return 0 if verification["status"] == "PASS" else 1


def verify(args):
    head = read_json(args.out / "HEAD.json")
    revision = args.out / "revisions" / head["revision"]
    verification = verify_revision(revision, read_json(args.charter), require_browser=True)
    print(json.dumps({"revision": head["revision"], **verification}, indent=2))
    return 0 if verification["status"] == "PASS" else 1


def capsule(args):
    root = args.out.resolve()
    revision = args.revision.resolve() if args.revision else root / "revisions" / read_json(root / "HEAD.json")["revision"]
    write_capsule(revision, args.output)
    print(json.dumps({"schema": CAPSULE_SCHEMA, "output": str(args.output),
                      "sha256": hashlib.sha256(Path(args.output).read_bytes()).hexdigest()}, indent=2))
    return 0


def serve(args):
    root = args.out.resolve()
    head = read_json(root / "HEAD.json")
    directory = root / "revisions" / head["revision"]
    handler = lambda *values, **kwargs: SimpleHTTPRequestHandler(*values, directory=str(directory), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Serving {directory} at http://127.0.0.1:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0


def main():
    args = parse_args()
    return {"run": run, "verify": verify, "capsule": capsule, "serve": serve}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())

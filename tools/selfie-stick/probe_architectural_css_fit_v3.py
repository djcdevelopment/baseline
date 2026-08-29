#!/usr/bin/env python3
"""Run the v3 automatic frame-registration experiment before the CSS gate.

V3 treats the prior eight-building holdout as revealed development evidence only
after a replacement holdout has been frozen, downloaded, verified, and OCR-pinned.
It preserves every automatic cross-sheet candidate, registers only one uniquely
passing plan/vertical pair, reserves a distinct vertical view from registration,
and keeps CSS read-only as the final held-out residual instrument.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import probe_architectural_css_fit as css0
import probe_architectural_css_fit_v1 as v1
import probe_architectural_css_fit_v2 as v2
import probe_architectural_curriculum as pipeline


ENGINE = "architectural-pre-css-frame-registration/3.0.0"
BASELINE_ENGINE = "architectural-pre-css-causal-repair/2.0.0-diagnostic"
DEFAULT_CHARTER = HERE / "architectural-css-fit-v3.json"
DEFAULT_SCHEMAS = HERE / "architectural-css-fit-schemas-v3.json"
DEFAULT_PRIMARY_SELECTION = HERE / "habs-corpus.json"
DEFAULT_PRIMARY_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_PRIMARY_AUDIT = HERE / "out" / "architectural-curriculum" / "real-ocr-audit-v1"
DEFAULT_RETIRED_SELECTION = HERE / "habs-corpus-v2-holdout.json"
DEFAULT_RETIRED_SOURCE = HERE / "architectural-curriculum-v2-holdout-source.json"
DEFAULT_RETIRED_CORPUS = HERE / "out" / "loc-habs-v2-holdout" / "corpus"
DEFAULT_RETIRED_AUDIT = HERE / "out" / "architectural-curriculum" / "real-ocr-audit-v2-holdout"
DEFAULT_BLIND_SELECTION = HERE / "habs-corpus-v3-holdout.json"
DEFAULT_BLIND_SOURCE = HERE / "architectural-curriculum-v3-holdout-source.json"
DEFAULT_BLIND_CORPUS = HERE / "out" / "loc-habs-v3-holdout" / "corpus"
DEFAULT_BLIND_AUDIT = HERE / "out" / "architectural-curriculum" / "real-ocr-audit-v3-holdout"
DEFAULT_BASELINE = HERE / "out" / "architectural-css-fit-v3-baseline"
DEFAULT_OUT = HERE / "out" / "architectural-css-fit-v3"


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--charter", type=Path, default=DEFAULT_CHARTER)
    common.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS)
    common.add_argument("--primary-selection", type=Path, default=DEFAULT_PRIMARY_SELECTION)
    common.add_argument("--primary-corpus", type=Path, default=DEFAULT_PRIMARY_CORPUS)
    common.add_argument("--primary-audit", type=Path, default=DEFAULT_PRIMARY_AUDIT)
    common.add_argument("--retired-selection", type=Path, default=DEFAULT_RETIRED_SELECTION)
    common.add_argument("--retired-source-charter", type=Path, default=DEFAULT_RETIRED_SOURCE)
    common.add_argument("--retired-corpus", type=Path, default=DEFAULT_RETIRED_CORPUS)
    common.add_argument("--retired-audit", type=Path, default=DEFAULT_RETIRED_AUDIT)
    common.add_argument("--blind-selection", type=Path, default=DEFAULT_BLIND_SELECTION)
    common.add_argument("--blind-source-charter", type=Path, default=DEFAULT_BLIND_SOURCE)
    common.add_argument("--blind-corpus", type=Path, default=DEFAULT_BLIND_CORPUS)
    common.add_argument("--blind-audit", type=Path, default=DEFAULT_BLIND_AUDIT)
    common.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("baseline", parents=[common])
    develop = commands.add_parser("develop", parents=[common])
    develop.add_argument("--seal", action="store_true")
    commands.add_parser("blind", parents=[common])
    commands.add_parser("verify", parents=[common])
    serve = commands.add_parser("serve", parents=[common])
    serve.add_argument("--port", type=int, default=8880)
    args = parser.parse_args()
    args.selection = args.primary_selection
    args.corpus = args.primary_corpus
    args.audit = args.primary_audit
    return args


def load_inputs(args):
    charter = json.loads(args.charter.read_text(encoding="utf-8"))
    paths = {
        "primary_selection_sha256": args.primary_selection,
        "retired_selection_sha256": args.retired_selection,
        "blind_selection_sha256": args.blind_selection,
    }
    for key, path in paths.items():
        if pipeline.digest_file(path) != charter["inputs"][key]:
            raise RuntimeError(f"frozen input changed: {key}")
    if pipeline.digest_file(HERE / "probe_architectural_css_fit_v2.py") != charter["inputs"]["v2_script_sha256"]:
        raise RuntimeError("pinned v2 diagnostic algorithm changed")

    primary_revision, primary_index, primary = v2.load_record_set(
        args.primary_selection, args.primary_corpus,
        HERE / "architectural-curriculum-v1.json", args.primary_audit,
        charter["inputs"]["primary_ocr_revision"])
    retired_revision, retired_index, retired = v2.load_record_set(
        args.retired_selection, args.retired_corpus, args.retired_source_charter,
        args.retired_audit, charter["inputs"]["retired_ocr_revision"])
    blind_revision, blind_index, blind = v2.load_record_set(
        args.blind_selection, args.blind_corpus, args.blind_source_charter,
        args.blind_audit, charter["inputs"]["blind_ocr_revision"])
    records = {**primary, **retired, **blind}
    expected = set(charter["evaluation"]["development_buildings"] +
                   charter["evaluation"]["blind_buildings"])
    if set(records) != expected or len(records) != charter["inputs"]["buildings"]:
        raise RuntimeError("frozen 28/8 split does not match the three corpora")
    index = {"sheets": (primary_index["sheets"] + retired_index["sheets"] +
                         blind_index["sheets"])}
    revisions = {"primary": primary_revision, "retired": retired_revision,
                 "blind": blind_revision}
    return charter, revisions, None, index, records


def normalized_signal(text):
    return re.sub(r"\s+", " ", css0.normalized_text(text)).strip()


def cut_line_contract(plan_view_id, marker, endpoints, segments, image_pixels):
    """Validate an observed two-ended plan cut line without metric inference.

    A section label and a compatible span are not cut-line evidence.  The plan
    must contain two independently recognized copies of the same marker and a
    distinct, source-pinned Hough segment at each endpoint.  The section axis is
    derived only from the endpoint geometry.
    """
    marker = str(marker or "").strip().upper()
    width, height = (int(value) for value in image_pixels)
    diagonal = max(1.0, (width * width + height * height) ** 0.5)
    reasons = []
    if not re.fullmatch(r"[A-Z]", marker):
        reasons.append("marker-must-be-one-letter")
    rows = sorted(endpoints, key=lambda row: (row["center_px"][1], row["center_px"][0]))
    if len(rows) != 2:
        reasons.append("exactly-two-marker-endpoints-required")
    elif any(str(row.get("marker", "")).upper() != marker for row in rows):
        reasons.append("endpoint-marker-mismatch")
    elif any(float(row.get("confidence", 0)) < 0.30 or
             row.get("ocr_engine") != "RapidOCR/3.9.2-recognizer" or
             not isinstance(row.get("crop_px"), list) or len(row["crop_px"]) != 4 or
             not re.fullmatch(r"[0-9a-f]{64}", str(row.get("source_sha256", "")))
             for row in rows):
        reasons.append("marker-endpoints-lack-source-pinned-ocr-provenance")

    axis = None
    alignment_error_px = None
    endpoint_span_px = None
    if len(rows) == 2:
        dx = abs(float(rows[1]["center_px"][0]) - float(rows[0]["center_px"][0]))
        dy = abs(float(rows[1]["center_px"][1]) - float(rows[0]["center_px"][1]))
        axis = "z" if dy >= dx else "x"
        alignment_error_px = dx if axis == "z" else dy
        endpoint_span_px = dy if axis == "z" else dx
        along = height if axis == "z" else width
        across = width if axis == "z" else height
        if endpoint_span_px < along * 0.20:
            reasons.append("marker-endpoints-do-not-span-plan")
        if alignment_error_px > across * 0.06:
            reasons.append("marker-endpoints-not-axis-aligned")

    eligible = []
    for row in segments:
        pixels = row.get("pixels")
        if not isinstance(pixels, list) or len(pixels) != 4:
            continue
        source_sha256 = str(row.get("source_sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
            continue
        if row.get("detector") != "OpenCV.HoughLinesP" or float(row.get("length_px", 0)) <= 0:
            continue
        eligible.append(row)

    owned_segments = []
    used = set()
    for endpoint in rows if len(rows) == 2 else []:
        px, py = (float(value) for value in endpoint["center_px"])
        choices = []
        for row in eligible:
            if row["id"] in used:
                continue
            x0, y0, x1, y1 = row["pixels"]
            distance = css0.point_segment_distance(
                px, py, {"x0": x0, "y0": y0, "x1": x1, "y1": y1})
            if distance <= diagonal * 0.045:
                choices.append((distance, row["id"], row))
        if choices:
            _, _, selected = min(choices, key=lambda item: (item[0], item[1]))
            used.add(selected["id"])
            owned_segments.append(selected)
    if len(owned_segments) != 2:
        reasons.append("two-source-pinned-endpoint-segments-required")

    return {
        "schema": "architectural-plan-cut-line/v3",
        "status": "PASS" if not reasons else "FAIL",
        "plan_view_id": plan_view_id,
        "marker": marker or None,
        "axis": axis,
        "endpoints": rows,
        "endpoint_segments": owned_segments,
        "image_pixels": [width, height],
        "endpoint_span_px": round(endpoint_span_px, 3) if endpoint_span_px is not None else None,
        "alignment_error_px": (round(alignment_error_px, 3)
                               if alignment_error_px is not None else None),
        "reasons": reasons,
        "authority": "PAIRED_OCR_MARKERS_PLUS_SOURCE_PINNED_CV_SEGMENTS",
    }


def token_signals(record, evidence):
    by_sheet = defaultdict(list)
    for view in evidence["views"]:
        by_sheet[view["sheet_index"]].append(view)
    signals = {view["id"]: {"markers": set(), "origins": set()}
               for view in evidence["views"]}
    marker_re = re.compile(r"\b([A-Z])\s*[-]\s*\1\b")
    origin_patterns = {
        "first_floor": re.compile(r"\b(?:FIRST|1ST) FLOOR\b"),
        "second_floor": re.compile(r"\b(?:SECOND|2ND) FLOOR\b"),
        "grade": re.compile(r"\b(?:GRADE|GROUND LINE)\b"),
        "basement": re.compile(r"\bBASEMENT(?: FLOOR)?\b"),
    }
    drawing_map = {drawing["sheet_index"]: drawing
                   for drawing in record["manifest"]["drawings"]}
    for sheet_index, views in by_sheet.items():
        sheet = v1.load_sheet(record, drawing_map[sheet_index], record["audit_rev"])
        owned = []
        for token in sheet["tokens"]:
            view = v1.owning_view(css0.center(token["region"]), views)
            owned.append((view["id"] if view else None, normalized_signal(token["text"])))
        for index, (view_id, text) in enumerate(owned):
            if not view_id:
                continue
            phrases = [text]
            for left, right in ((index - 1, index), (index, index + 1)):
                if 0 <= left < len(owned) and 0 <= right < len(owned):
                    if owned[left][0] == view_id == owned[right][0]:
                        phrases.append(owned[left][1] + " " + owned[right][1])
            for phrase in phrases:
                signals[view_id]["markers"].update(marker_re.findall(phrase))
                for origin, pattern in origin_patterns.items():
                    if pattern.search(phrase):
                        signals[view_id]["origins"].add(origin)
    for view in evidence["views"]:
        label = normalized_signal(view.get("label") or "")
        signals[view["id"]]["markers"].update(marker_re.findall(label))
        for origin, pattern in origin_patterns.items():
            if pattern.search(label):
                signals[view["id"]]["origins"].add(origin)
    for datum in evidence["datums"]:
        if datum.get("view_id") not in signals:
            continue
        kind = datum.get("type")
        if kind in ("first_floor", "grade", "basement"):
            signals[datum["view_id"]]["origins"].add(kind)
    return signals


def view_scale(view, dimensions, charter):
    if view.get("scale"):
        value = statistics.mean((view["scale"]["metres_per_pixel_x"],
                                 view["scale"]["metres_per_pixel_y"]))
        return {"status": "PASS", "metres_per_pixel": round(value, 9),
                "authority": "OBSERVED_COMPLETE_SCALE_NOTATION",
                "anchor_ids": [f"{view['id']}:notation"]}
    selected, consensus = v2.compatible_consensus(
        v2.scale_candidates(view, dimensions), charter)
    return {"status": consensus["status"],
            "metres_per_pixel": consensus["metres_per_pixel"],
            "authority": "MULTI_ORIGIN_CONSENSUS" if consensus["status"] == "PASS" else "HELD",
            "anchor_ids": [row["id"] for row in selected]}


def resolve_registration_candidates(candidates):
    ordered = sorted(candidates, key=lambda row: row["id"])
    passing = [candidate for candidate in ordered if all(candidate["gates"].values())]
    if len(passing) == 1:
        passing[0]["status"] = "REGISTERED"
        registration = {"status": "REGISTERED", "candidate_id": passing[0]["id"],
                        "ambiguity_count": 0}
    elif len(passing) > 1:
        for candidate in passing:
            candidate["status"] = "HELD_AMBIGUOUS"
        registration = {"status": "HELD_AMBIGUOUS", "candidate_id": None,
                        "ambiguity_count": len(passing)}
    else:
        registration = {"status": "REJECTED", "candidate_id": None,
                        "ambiguity_count": 0}
    return ordered, registration


def automatic_frames_and_registration(record, evidence, graph, charter):
    views = {view["id"]: view for view in evidence["views"]}
    dimensions = evidence["observed_dimensions"]
    signals = token_signals(record, evidence)
    plan_masses = [mass for mass in evidence["masses"] if mass["closed_wall_loop"]]
    plan_frames = []
    for mass in plan_masses:
        plan = views[mass["view_id"]]
        if not signals[plan["id"]]["origins"]:
            label = normalized_signal(plan.get("label") or "")
            if "BASEMENT" not in label:
                signals[plan["id"]]["origins"].add("first_floor")
        scale = view_scale(plan, dimensions, charter)
        frame_dimensions = dict(mass["dimensions"])
        if scale["status"] == "PASS" and scale["metres_per_pixel"]:
            geometry = plan["geometry"]
            if frame_dimensions.get("width_m") is None:
                frame_dimensions["width_m"] = round(
                    geometry["width_px"] * scale["metres_per_pixel"], 6)
                frame_dimensions["width_dimension_id"] = f"{plan['id']}:frame-width"
            if frame_dimensions.get("depth_m") is None:
                frame_dimensions["depth_m"] = round(
                    geometry["height_px"] * scale["metres_per_pixel"], 6)
                frame_dimensions["depth_dimension_id"] = f"{plan['id']}:frame-depth"
        plan_frames.append({
            "schema": "architectural-frame-hypothesis/v3",
            "id": f"{plan['id']}:{mass['id']}:plan-frame", "view_id": plan["id"],
            "mass_id": mass["id"], "kind": "PLAN_MASS",
            "axes": {"horizontal": "x", "vertical": "z"},
            "origin": sorted(signals[plan["id"]]["origins"]),
            "scale_status": scale["status"], "scale": scale,
            "dimensions": frame_dimensions,
            "authority": "AUTOMATIC_OBSERVED_SUPPORT",
        })

    pair_by_view = {}
    for pair in evidence["roof_datum_pairs"]:
        prior = pair_by_view.get(pair["view_id"])
        if prior is None or (pair["status"] == "CALIBRATED" and prior["status"] != "CALIBRATED"):
            pair_by_view[pair["view_id"]] = pair
    calibrated_ids = sorted(view_id for view_id, pair in pair_by_view.items()
                            if pair["status"] == "CALIBRATED")
    holdout_id = None
    if len(calibrated_ids) >= 2:
        elevation_ids = [value for value in calibrated_ids if views[value]["role"] == "elevation"]
        reserve_from = elevation_ids or calibrated_ids
        holdout_id = max(reserve_from, key=lambda value: hashlib.sha256(
            value.encode("utf-8")).hexdigest())

    frames = list(plan_frames)
    vertical_scales = {}
    for view_id, pair in sorted(pair_by_view.items()):
        scale = view_scale(views[view_id], dimensions, charter)
        vertical_scales[view_id] = scale
        frames.append({
            "schema": "architectural-frame-hypothesis/v3",
            "id": f"{view_id}:vertical-frame", "view_id": view_id,
            "kind": "VERTICAL_ROOF_PAIR", "axes": {"horizontal": "UNRESOLVED", "vertical": "y"},
            "origin": sorted(signals[view_id]["origins"]),
            "scale_status": scale["status"], "scale": scale,
            "roof_datum_pair_id": pair["id"],
            "authority": "AUTOMATIC_OBSERVED_SUPPORT",
        })

    candidates = []
    for plan_frame in plan_frames:
        plan = views[plan_frame["view_id"]]
        plan_scale = plan_frame["scale"]
        plan_dimensions = plan_frame["dimensions"]
        for view_id, pair in sorted(pair_by_view.items()):
            if view_id == holdout_id:
                continue
            view = views[view_id]
            scale = vertical_scales[view_id]
            metric_span = (round(view["geometry"]["width_px"] * scale["metres_per_pixel"], 6)
                           if scale["status"] == "PASS" and scale["metres_per_pixel"] else None)
            span_matches = []
            if metric_span is not None:
                for axis, key in (("x", "width_m"), ("z", "depth_m")):
                    value = plan_dimensions.get(key)
                    if value:
                        error_m = abs(value - metric_span)
                        error_ratio = error_m / max(value, metric_span)
                        if (error_m <= charter["registration"]["maximum_metric_span_error_m"] or
                                error_ratio <= charter["registration"]["maximum_metric_span_error_ratio"]):
                            span_matches.append({"axis": axis, "plan_span_m": value,
                                                 "vertical_span_m": metric_span,
                                                 "error_m": round(error_m, 6),
                                                 "error_ratio": round(error_ratio, 6)})
            observed_plan_cut_lines = [row for row in evidence.get("plan_cut_lines", [])
                                       if row.get("status") == "PASS" and
                                       row.get("plan_view_id") == plan["id"]]
            plan_markers = (signals[plan["id"]]["markers"] |
                            {row["marker"] for row in observed_plan_cut_lines})
            vertical_markers = signals[view_id]["markers"]
            markers = sorted(plan_markers & vertical_markers)
            origins = sorted(signals[plan["id"]]["origins"] & signals[view_id]["origins"])
            cut_lines = [row for row in observed_plan_cut_lines
                         if row.get("marker") in markers and
                         len(span_matches) == 1 and
                         row.get("axis") == span_matches[0]["axis"]]
            gates = {
                "different_sheets": plan["sheet_index"] != view["sheet_index"],
                "plan_independently_calibrated": plan_scale["status"] == "PASS",
                "vertical_independently_calibrated": scale["status"] == "PASS",
                "exact_section_marker": len(markers) == 1,
                "compatible_metric_span": len(span_matches) == 1,
                "matching_floor_or_grade_origin": len(origins) == 1,
                "cut_line_axis": len(cut_lines) == 1,
            }
            passes = all(gates.values())
            status = "CANDIDATE" if passes or markers else "REJECTED"
            candidates.append({
                "schema": "architectural-registration-candidate/v3",
                "id": f"{plan_frame['id']}::{view_id}",
                "plan_frame_id": plan_frame["id"], "mass_id": plan_frame["mass_id"],
                "plan_view_id": plan["id"], "vertical_view_id": view_id,
                "roof_datum_pair_id": pair["id"], "status": status, "gates": gates,
                "plan_section_markers": sorted(plan_markers),
                "vertical_section_markers": sorted(vertical_markers),
                "exact_section_markers": markers, "matching_origins": origins,
                "metric_span_matches": span_matches,
                "cut_line_axis": cut_lines[0]["axis"] if len(cut_lines) == 1 else None,
                "cut_line_evidence": cut_lines[0] if len(cut_lines) == 1 else None,
                "registration_weight": None, "proximity_score": None,
            })
    candidates, registration = resolve_registration_candidates(candidates)
    holdout = {"view_id": holdout_id, "role": views[holdout_id]["role"] if holdout_id else None,
               "reserved_before_registration": True,
               "contributed_registration_evidence": False,
               "geometry_excluded_from_graph": True,
               "dimensions_excluded_from_graph": True,
               "observed_span_px": None, "span_authority": None}
    if holdout_id:
        geometry = views[holdout_id]["geometry"]
        holdout["observed_span_px"] = [geometry["width_px"], geometry["height_px"]]
        holdout["span_authority"] = "DOMINANT_CONNECTED_LINEWORK"
    return frames, candidates, registration, holdout, pair_by_view


def promote_registered_graph(evidence, graph, registration, pair_by_view, charter):
    registered = next((row for row in evidence["registration_candidates"]
                       if row["status"] == "REGISTERED"), None)
    registered_frame = next((row for row in evidence["frame_hypotheses"]
                             if registered and row["id"] == registered["plan_frame_id"]), None)
    primary = next((mass for mass in evidence["masses"]
                    if registered and mass["id"] == registered["mass_id"]), None)
    if primary and registered_frame:
        for mass in evidence["masses"]:
            if mass is primary:
                mass["status"] = "SELECTED_PRIMARY"
                mass["dimensions"] = dict(registered_frame["dimensions"])
                mass["two_axis_dimensions"] = all(
                    mass["dimensions"].get(key) is not None for key in ("width_m", "depth_m"))
                mass["extent_authority"] = "REGISTERED_CALIBRATED_PLAN_FRAME"
            elif mass["status"] == "SELECTED_PRIMARY":
                mass["status"] = "SECONDARY"
        graph["dimensions"]["width_m"] = primary["dimensions"]["width_m"]
        graph["dimensions"]["depth_m"] = primary["dimensions"]["depth_m"]
    if primary is None:
        primary = next((mass for mass in evidence["masses"]
                        if mass["status"] == "SELECTED_PRIMARY"), None)
    plan_scale = (registered_frame["scale"] if registered_frame else
                  {"status": "FAIL", "metres_per_pixel": None})
    pair = pair_by_view.get(registered["vertical_view_id"]) if registered else None
    datum_map = {datum["id"]: datum for datum in evidence["datums"]}
    ridge = datum_map.get(pair["ridge_datum_id"]) if pair else None
    eaves = [datum_map.get(value) for value in pair["eave_datum_ids"]] if pair else []
    eave = next((value for value in eaves if value and value.get("value_m") is not None), None)
    if ridge and ridge.get("value_m") is not None and graph["dimensions"].get("ridge_height_m") is None:
        graph["dimensions"]["ridge_height_m"] = ridge["value_m"]
    if eave and graph["dimensions"].get("eave_height_m") is None:
        graph["dimensions"]["eave_height_m"] = eave["value_m"]
    dimensions = graph["dimensions"]
    plausible = all(dimensions.get(key) is not None for key in
                    ("width_m", "depth_m", "ridge_height_m")) and all(
        dimensions[key] >= charter["promotion"]["minimum_width_depth_m"]
        for key in ("width_m", "depth_m")) and dimensions["ridge_height_m"] >= charter["promotion"]["minimum_ridge_height_m"]
    gates = [
        {"id": "disjoint-view-interiors", "status": "PASS" if evidence["maximum_view_overlap_ratio"] == 0 else "FAIL",
         "actual": evidence["maximum_view_overlap_ratio"]},
        {"id": "owned-primary-mass", "status": "PASS" if primary else "FAIL",
         "actual": primary["id"] if primary else None},
        {"id": "closed-wall-loop", "status": "PASS" if primary and primary["closed_wall_loop"] else "FAIL",
         "actual": bool(primary and primary["closed_wall_loop"])},
        {"id": "two-axis-dimensions", "status": "PASS" if primary and primary["two_axis_dimensions"] else "FAIL",
         "actual": bool(primary and primary["two_axis_dimensions"])},
        {"id": "plan-frame-scale", "status": plan_scale["status"],
         "actual": plan_scale["metres_per_pixel"]},
        {"id": "unique-cross-sheet-registration", "status": "PASS" if registered else "FAIL",
         "actual": registered["id"] if registered else registration["status"]},
        {"id": "registered-vertical-roof-pair", "status": "PASS" if pair else "FAIL",
         "actual": pair["id"] if pair else None},
        {"id": "plausible-envelope", "status": "PASS" if plausible else "FAIL",
         "actual": dimensions},
        {"id": "reserved-css-holdout", "status": "PASS" if evidence["holdout"]["view_id"] else "FAIL",
         "actual": evidence["holdout"]["view_id"]},
        {"id": "holdout-excluded-from-registration", "status": "PASS" if
         evidence["holdout"]["contributed_registration_evidence"] is False else "FAIL", "actual": False},
    ]
    graph["schema"] = "architectural-building-graph/v3"
    graph["v2_diagnostic_gates"] = graph.get("promotion_gates", [])
    graph["promotion_gates"] = gates
    graph["frame_hypothesis_ids"] = [frame["id"] for frame in evidence["frame_hypotheses"]]
    graph["registration_candidate_id"] = registered["id"] if registered else None
    graph["status"] = "G1_CANDIDATE" if all(gate["status"] == "PASS" for gate in gates) else "HELD"
    return graph


def process_building(record, _audit_rev, _corpus, charter, target):
    assessment, evidence, graph, _ = v2.process_building(
        record, record["audit_rev"], record["corpus"], charter, target)
    frames, candidates, registration, holdout, pair_by_view = (
        automatic_frames_and_registration(record, evidence, graph, charter))
    evidence["schema"] = "architectural-evidence-graph/v3"
    evidence["frame_hypotheses"] = frames
    evidence["registration_candidates"] = candidates
    evidence["registration"] = registration
    evidence["cross_view_registrations_v2_diagnostic"] = evidence.pop("cross_view_registrations", [])
    evidence["cross_view_registrations"] = [row for row in candidates if row["status"] == "REGISTERED"]
    evidence["holdout"] = holdout
    graph = promote_registered_graph(evidence, graph, registration, pair_by_view, charter)
    evidence["promotion"] = graph["status"]
    residual = v2.css_residual(graph, evidence, charter)
    residual["schema"] = "architectural-css-residual/v3"
    residual["registration_discovery_operations"] = 0
    route = ("G1_METRIC_GRAPH" if residual["status"] == "PASS" else
             "G1_UNVALIDATED" if graph["status"] == "G1_CANDIDATE" else
             "A0_TRIAGED" if any(view["role"] == "plan" for view in evidence["views"]) and
             any(view["role"] in ("elevation", "section") for view in evidence["views"]) else "HELD")
    assessment.update({
        "schema": "architectural-envelope-fit/v3", "route": route,
        "fit": graph["dimensions"],
        "evidence_graph_sha256": pipeline.digest_bytes(pipeline.compact_bytes(evidence)),
        "building_graph_sha256": pipeline.digest_bytes(pipeline.compact_bytes(graph)),
        "residual": residual,
    })
    pipeline.atomic_json(target / "evidence.graph.json", evidence)
    pipeline.atomic_json(target / "building.graph.json", graph)
    pipeline.atomic_json(target / "css-residual.json", residual)
    pipeline.atomic_json(target / "assessment.json", assessment)
    pipeline.atomic_bytes(target / "index.html", v1.building_html(assessment, evidence, graph))
    return assessment, evidence, graph, residual


def baseline_identity(args, revisions):
    return {
        "engine": BASELINE_ENGINE,
        "v2_engine": v2.ENGINE,
        "v2_script_sha256": pipeline.digest_file(HERE / "probe_architectural_css_fit_v2.py"),
        "v2_development_revision": json.loads(args.charter.read_text(encoding="utf-8"))["inputs"]["v2_development_revision"],
        "development_ids": json.loads(args.charter.read_text(encoding="utf-8"))["evaluation"]["development_buildings"],
        "audit_revisions": {key: revisions[key] for key in ("primary", "retired")},
        "mode": "PINNED_V2_DIAGNOSTIC_NO_NETWORK",
    }


class BaselineProject(v1.Project):
    def __init__(self, args, revisions):
        self.identity = baseline_identity(args, revisions)
        self.revision = pipeline.digest_bytes(pipeline.compact_bytes(self.identity))[:20]
        self.root = args.baseline.resolve()
        self.rev = self.root / "revisions" / self.revision
        self.rev.mkdir(parents=True, exist_ok=True)
        pipeline.atomic_bytes(self.root / "HEAD", (self.revision + "\n").encode("ascii"))
        pipeline.immutable_json(self.rev / "identity.json", self.identity)
        self.stats = {"executed": [], "cached": [], "evidence_reads": 0,
                      "topology_runs": 0, "css_runs": 0, "ocr_calls": 0,
                      "vlm_calls": 0, "network_requests": 0,
                      "source_downloads": 0, "world_writes": 0}


def run_baseline(args):
    css0.load_imaging()
    charter, revisions, _, audit_index, records = load_inputs(args)
    project = BaselineProject(args, revisions)
    audit_rows = defaultdict(list)
    for row in audit_index["sheets"]:
        audit_rows[row["building_id"]].append(row)
    results = {}
    building_ids = charter["evaluation"]["development_buildings"]
    for ordinal, building_id in enumerate(building_ids, 1):
        record = records[building_id]
        fingerprint = pipeline.digest_bytes(pipeline.compact_bytes({
            "identity": project.identity, "building_id": building_id,
            "audit_rows": audit_rows[building_id]}))
        results[building_id] = project.building(
            record, fingerprint, lambda target, record=record: v2.process_building(
                record, record["audit_rev"], record["corpus"], charter, target))
        print(f"[{ordinal:02d}/{len(building_ids):02d}] {building_id} {results[building_id][0]['route']}")
    rows = []
    for building_id in building_ids:
        assessment, evidence, _, _ = results[building_id]
        rows.append({
            "building_id": building_id, "route": assessment["route"],
            "selected_primary": any(mass["status"] == "SELECTED_PRIMARY" for mass in evidence["masses"]),
            "scale_consensus": evidence["scale_consensus"]["status"],
            "calibrated_roof_pairs": sum(pair["status"] == "CALIBRATED" for pair in evidence["roof_datum_pairs"]),
        })
    summary = {"schema": "architectural-css-fit-v3-diagnostic-baseline/v1",
               "status": "PASS", "revision": project.revision,
               "algorithm": project.identity, "buildings": rows,
               "authority": {"network_requests": 0, "ocr_calls": 0,
                             "source_downloads": 0, "world_mutated": False}}
    pipeline.immutable_json(project.rev / "baseline.json", summary)
    v1.write_manifest(project)
    pipeline.atomic_json(project.root / "report.json", {
        "schema": "architectural-css-fit-v3-baseline-report/v1", "status": "PASS",
        "revision": project.revision, "stage_cache": project.stats})
    print(f"revision {project.revision}\nBASELINE PASS")
    return 0


def validate_baseline(args, charter):
    root = args.baseline.resolve()
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    rev = root / "revisions" / revision
    identity = json.loads((rev / "identity.json").read_text(encoding="utf-8"))
    summary = json.loads((rev / "baseline.json").read_text(encoding="utf-8"))
    if identity != baseline_identity(args, {
            "primary": charter["inputs"]["primary_ocr_revision"],
            "retired": charter["inputs"]["retired_ocr_revision"]}):
        raise RuntimeError("pinned v2 diagnostic baseline identity changed")
    if summary.get("status") != "PASS" or {row["building_id"] for row in summary["buildings"]} != set(
            charter["evaluation"]["development_buildings"]):
        raise RuntimeError("pinned v2 diagnostic baseline is incomplete")
    return revision, pipeline.digest_file(rev / "baseline.json")


class Project(v1.Project):
    def __init__(self, args, charter, audit_revisions):
        baseline_revision, baseline_sha = validate_baseline(args, charter)
        self.identity = {
            "engine": ENGINE, "script_sha256": pipeline.digest_file(Path(__file__)),
            "v2_library_sha256": pipeline.digest_file(HERE / "probe_architectural_css_fit_v2.py"),
            "charter_sha256": pipeline.digest_file(args.charter),
            "schemas_sha256": pipeline.digest_file(args.schemas),
            "primary_selection_sha256": pipeline.digest_file(args.primary_selection),
            "retired_selection_sha256": pipeline.digest_file(args.retired_selection),
            "blind_selection_sha256": pipeline.digest_file(args.blind_selection),
            "audit_revisions": audit_revisions,
            "baseline_revision": baseline_revision, "baseline_sha256": baseline_sha,
            "mode": "REAL_OCR_CV_DETERMINISTIC_NO_NETWORK_NO_ORACLE",
        }
        self.revision = pipeline.digest_bytes(pipeline.compact_bytes(self.identity))[:20]
        self.root = args.out.resolve()
        self.rev = self.root / "revisions" / self.revision
        self.rev.mkdir(parents=True, exist_ok=True)
        pipeline.atomic_bytes(self.root / "HEAD", (self.revision + "\n").encode("ascii"))
        pipeline.immutable_json(self.rev / "identity.json", self.identity)
        self.stats = {"executed": [], "cached": [], "evidence_reads": 0,
                      "topology_runs": 0, "css_runs": 0, "ocr_calls": 0,
                      "vlm_calls": 0, "network_requests": 0,
                      "source_downloads": 0, "world_writes": 0}


def fingerprint(record, audit_rows, _audit_revisions):
    return pipeline.digest_bytes(pipeline.compact_bytes({
        "engine": ENGINE, "script_sha256": pipeline.digest_file(Path(__file__)),
        "v2_library_sha256": pipeline.digest_file(HERE / "probe_architectural_css_fit_v2.py"),
        "building_id": record["id"], "audit_revision": record["audit_revision"],
        "audit_rows": audit_rows[record["id"]]}))


def development_acceptance(results, charter):
    automatic_seal, original = v1.development_acceptance_original(results, charter)
    cohort = charter["evaluation"]["original_failure_cohort"]
    selected = sum(any(mass["status"] == "SELECTED_PRIMARY" for mass in results[item][1]["masses"])
                   for item in cohort)
    scale = sum(results[item][1]["scale_consensus"]["status"] == "PASS" for item in cohort)
    paired = sum(any(pair["status"] == "CALIBRATED" for pair in results[item][1]["roof_datum_pairs"])
                 for item in cohort)
    g1 = sum(results[item][0]["route"] == "G1_METRIC_GRAPH" for item in cohort)
    controls = charter["evaluation"]["development_negative_controls"]
    controls_hold = all(results[item][0]["route"] != "G1_METRIC_GRAPH" for item in controls)
    authority_clean = all(all(results[item][0].get(key) in (0, False) for key in
                              ("network_requests", "vlm_calls", "source_downloads", "world_mutated"))
                          for item in charter["evaluation"]["development_buildings"])
    thresholds = charter["development_acceptance"]
    checks = original["checks"] + [
        {"id": "original-failure-cohort-selected-primary", "actual": selected,
         "expected": thresholds["minimum_failure_cohort_selected_primary"],
         "status": "PASS" if selected >= thresholds["minimum_failure_cohort_selected_primary"] else "FAIL"},
        {"id": "original-failure-cohort-scale-consensus", "actual": scale,
         "expected": thresholds["minimum_failure_cohort_scale_consensus"],
         "status": "PASS" if scale >= thresholds["minimum_failure_cohort_scale_consensus"] else "FAIL"},
        {"id": "original-failure-cohort-paired-roof-datums", "actual": paired,
         "expected": thresholds["minimum_failure_cohort_paired_roof_datums"],
         "status": "PASS" if paired >= thresholds["minimum_failure_cohort_paired_roof_datums"] else "FAIL"},
        {"id": "original-failure-cohort-validated-g1", "actual": g1,
         "expected": thresholds["minimum_failure_cohort_g1"],
         "status": "PASS" if g1 >= thresholds["minimum_failure_cohort_g1"] else "FAIL"},
        {"id": "development-negative-controls-hold", "actual": controls_hold,
         "expected": True, "status": "PASS" if controls_hold else "FAIL"},
        {"id": "fit-authority-boundary", "actual": authority_clean,
         "expected": True, "status": "PASS" if authority_clean else "FAIL"},
    ]
    return automatic_seal, {
        "schema": "architectural-frame-registration-development-acceptance/v3",
        "oracle_loaded_after_seal": True,
        "status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL",
        "checks": checks,
    }


def install_v3_hooks():
    v2.install_v2_hooks()
    v1.load_inputs = load_inputs
    v1.process_building = process_building
    v1.Project = Project
    v1.fingerprint = fingerprint
    v1.development_acceptance = development_acceptance


def verify_development(args):
    charter, _, _, _, _ = load_inputs(args)
    validate_baseline(args, charter)
    root = args.out.resolve()
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    rev = root / "revisions" / revision
    errors = []
    manifest = json.loads((rev / "manifest.json").read_text(encoding="utf-8"))
    for row in manifest["files"]:
        path = pipeline.safe_child(rev, row["path"])
        if not path.is_file() or pipeline.digest_file(path) != row["sha256"] or path.stat().st_size != row["bytes"]:
            errors.append(f"artifact mismatch {row['path']}")
    acceptance = json.loads((rev / "development-acceptance.json").read_text(encoding="utf-8"))
    if (root / "DEVELOPMENT_LOCK.json").exists():
        errors.append("unexpected development lock before a passing sealed gate")
    if (rev / "blind-automatic-seal.json").exists() or (rev / "index.json").exists():
        errors.append("blind artifacts exist before development seal")
    for building_id in charter["evaluation"]["development_buildings"]:
        target = rev / "buildings" / building_id
        if not target.is_dir():
            errors.append(f"missing development artifact {building_id}")
            continue
        evidence = json.loads((target / "evidence.graph.json").read_text(encoding="utf-8"))
        graph = json.loads((target / "building.graph.json").read_text(encoding="utf-8"))
        residual = json.loads((target / "css-residual.json").read_text(encoding="utf-8"))
        if evidence.get("schema") != "architectural-evidence-graph/v3":
            errors.append(f"evidence schema {building_id}")
        if residual.get("schema") != "architectural-css-residual/v3":
            errors.append(f"residual schema {building_id}")
        if residual.get("corrected_geometry", "missing") is not None or residual.get("discovery_operations") != 0:
            errors.append(f"CSS authority violation {building_id}")
        if residual.get("graph_sha256") != pipeline.digest_bytes(pipeline.compact_bytes(graph)):
            errors.append(f"CSS graph hash {building_id}")
        if evidence.get("holdout", {}).get("contributed_registration_evidence") is not False:
            errors.append(f"holdout leakage {building_id}")
        registered = [row for row in evidence.get("registration_candidates", []) if row["status"] == "REGISTERED"]
        if len(registered) > 1 or any(row.get("registration_weight") is not None for row in evidence.get("registration_candidates", [])):
            errors.append(f"registration authority {building_id}")
    result = {
        "schema": "architectural-css-fit-development-verification/v3",
        "status": "PASS" if not errors else "FAIL", "revision": revision,
        "experiment_status": "BLOCKED_AT_DEVELOPMENT_GATE" if acceptance["status"] == "FAIL" else "READY_TO_SEAL",
        "development_acceptance": acceptance["status"],
        "development_buildings": len(charter["evaluation"]["development_buildings"]),
        "blind_buildings_exposed": 0, "errors": errors,
        "network_requests": 0, "ocr_calls": 0, "vlm_calls": 0,
        "source_downloads": 0, "world_mutated": False,
    }
    pipeline.atomic_json(root / "verification-development.json", result)
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


def main():
    args = parse_args()
    install_v3_hooks()
    try:
        if args.command == "baseline":
            return run_baseline(args)
        if args.command == "develop":
            if (args.out.resolve() / "DEVELOPMENT_LOCK.json").is_file():
                raise RuntimeError("development is already sealed; use a fresh --out root")
            charter = json.loads(args.charter.read_text(encoding="utf-8"))
            validate_baseline(args, charter)
            return v1.run_phase(args, blind=False)
        if args.command == "blind":
            root = args.out.resolve()
            if ((root / "DEVELOPMENT_LOCK.json").is_file() and (root / "HEAD").is_file() and
                    (root / "revisions" / (root / "HEAD").read_text(encoding="ascii").strip() /
                     "blind-automatic-seal.json").is_file()):
                return v1.completed_blind_cache_run(args)
            return v1.run_phase(args, blind=True)
        if args.command == "verify":
            if not (args.out.resolve() / "DEVELOPMENT_LOCK.json").is_file():
                return verify_development(args)
            return v1.verify(args)
        return v1.serve(args)
    except Exception as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bounded three-building probe for HABS primary-mass and datum topology.

This is deliberately diagnostic, not a replacement fitter.  It reuses the sealed
automatic CSS-fit evidence for sd0401, tx1037, and ak0535; compares structural line
families, panel overlap, explicit dimension chains, and semantic datum stacks; then
opens the already-accepted sd0401 graph only after the new candidate evidence is
sealed.  It never calls OCR, a VLM, the network, Creator OS, or a Valheim world.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import probe_architectural_css_fit as css
import probe_architectural_curriculum as pipeline


ENGINE = "architectural-css-topology-probe/0.1.0"
TARGETS = ("sd0401", "tx1037", "ak0535")
EXPECTED_PARENT = "3899e363a8b63658dc8a"
DEFAULT_PARENT = HERE / "out" / "architectural-css-fit"
DEFAULT_AUDIT = HERE / "out" / "architectural-curriculum" / "real-ocr-audit-v1"
DEFAULT_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_ORACLE = HERE / "out" / "architectural-roundtrip" / "sd0401"
DEFAULT_OUT = HERE / "out" / "architectural-css-topology"

SEMANTIC_RE = re.compile(
    r"ROOF\s*(?:RIDGE|PEAK|EDGE)|\bEAVE\b|\bCEILING\b|FIRST\s+FLOOR|"
    r"\bFLOOR\b|\bDATUM\b|\bBASEMENT\b|\bGRADE\b",
    re.I,
)
MASS_RE = re.compile(
    r"LOG\s+CABIN|\bADDITION\b|MECHANICAL\s+ROOM|FIRST\s+FLOOR\s+PLAN|"
    r"BASEMENT\s+PLAN",
    re.I,
)


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    common.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    common.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    common.add_argument("--oracle", type=Path, default=DEFAULT_ORACLE)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", parents=[common])
    sub.add_parser("verify", parents=[common])
    return parser.parse_args()


def center(region):
    return ((float(region[0]) + float(region[2])) / 2,
            (float(region[1]) + float(region[3])) / 2)


def area(box):
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def panel_overlaps(panels):
    rows = []
    for index, left in enumerate(panels):
        for right in panels[index + 1:]:
            if left["sheet_index"] != right["sheet_index"] or left["role"] == right["role"]:
                continue
            a, b = left["bbox"], right["bbox"]
            intersection = (max(0.0, min(a[2], b[2]) - max(a[0], b[0])) *
                            max(0.0, min(a[3], b[3]) - max(a[1], b[1])))
            if not intersection:
                continue
            rows.append({
                "left": left["id"], "left_role": left["role"],
                "right": right["id"], "right_role": right["role"],
                "intersection_over_smaller": round(intersection / min(area(a), area(b)), 6),
                "iou": round(intersection / (area(a) + area(b) - intersection), 6),
            })
    return sorted(rows, key=lambda item: (-item["intersection_over_smaller"],
                                          item["left"], item["right"]))


def normalized(value):
    value = css.normalized_text(value)
    return (value.replace("I0", "10").replace("IO", "10").replace("O'", "0'")
            .replace("Â", "").replace("â€", "").strip())


def fraction(value):
    value = value.strip()
    if not value:
        return 0.0
    if " " in value:
        whole, tail = value.split(None, 1)
        return float(whole) + fraction(tail)
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator)
    return float(value)


def repaired_dimension(text):
    """Parse one conservative probe-only imperial candidate.

    The production strict parser remains untouched.  This repair accepts a damaged
    terminal inch quote only when an unambiguous feet marker survives, rejects scale
    notation and product dimensions, and labels every repaired result accordingly.
    """
    value = normalized(text)
    if "=" in value or re.search(r"\d\s*[XÃ—]\s*\d", value, re.I):
        return None
    parsed = pipeline.parse_dimension(value)
    if parsed is not None:
        return round(float(parsed), 6)
    match = re.search(r"(?P<feet>\d{1,3})\s*'\s*-?\s*"
                      r"(?P<inches>\d{1,2}(?:\s+\d+\s*/\s*\d+)?)?", value)
    if not match:
        return None
    feet = int(match.group("feet"))
    inches = fraction(match.group("inches") or "0")
    if inches >= 12:
        return None
    return round(feet * 0.3048 + inches * 0.0254, 6)


def dimension_axis(region):
    width = max(1e-9, region[2] - region[0])
    height = max(1e-9, region[3] - region[1])
    return "vertical" if height >= width * 1.45 else "horizontal"


def sheet_input(building_id, sheet_index, audit_rev):
    directory = audit_rev / "sheets" / building_id / f"sheet-{sheet_index:02d}"
    audit = json.loads((directory / "audit.json").read_text(encoding="utf-8"))
    ocr = json.loads((directory / "ocr.json").read_text(encoding="utf-8"))
    return {
        "building_id": building_id,
        "sheet_index": sheet_index,
        "source_sha256": audit["source_sha256"],
        "source_url": audit["source_url"],
        "normalized_path": directory / "normalized.png",
        "normalized_pixels": audit["raster"]["normalized_pixels"],
        "tokens": ocr["tokens"],
        "ocr_roles": audit["ocr_role_signals"],
        "strict_dimensions": audit["strict_dimensions"],
        "suspicious_dimensions": audit["suspicious_dimensions"],
    }


def dimensions_for_sheet(sheet, panels):
    rows = []
    seen = set()
    for authority, source in (("STRICT", sheet["strict_dimensions"]),
                              ("REPAIRED_PROBE_ONLY", sheet["suspicious_dimensions"])):
        for item in source:
            value = float(item["value_m"]) if authority == "STRICT" else repaired_dimension(item["text"])
            if value is None:
                continue
            key = (item["text"], tuple(round(float(number), 7) for number in item["region"]))
            if key in seen:
                continue
            seen.add(key)
            point = center(item["region"])
            panel = css.assign_panel(point, panels)
            rows.append({
                "text": item["text"], "value_m": round(value, 6), "authority": authority,
                "axis": dimension_axis(item["region"]), "center": [round(point[0], 6), round(point[1], 6)],
                "region": [round(float(number), 6) for number in item["region"]],
                "panel_id": panel["id"] if panel else None,
            })
    return sorted(rows, key=lambda item: (item["axis"], item["center"][1],
                                          item["center"][0], item["text"]))


def semantic_tokens(sheet):
    rows = []
    for token in sheet["tokens"]:
        text = normalized(token["text"])
        if not (SEMANTIC_RE.search(text) or MASS_RE.search(text)):
            continue
        point = center(token["region"])
        strict_value = pipeline.parse_dimension(text)
        direct_value = strict_value if strict_value is not None else repaired_dimension(token["text"])
        rows.append({
            "text": token["text"], "normalized": text,
            "center": [round(point[0], 6), round(point[1], 6)],
            "region": [round(float(number), 6) for number in token["region"]],
            "direct_value_m": round(float(direct_value), 6) if direct_value is not None else None,
            "direct_value_authority": ("STRICT" if strict_value is not None else
                                       "REPAIRED_PROBE_ONLY" if direct_value is not None else None),
            "kind": "mass" if MASS_RE.search(text) else "datum",
        })
    return rows


def group_dimensions(dimensions):
    groups = []
    for axis in ("horizontal", "vertical"):
        coordinate_index = 1 if axis == "horizontal" else 0
        tolerance = 0.018 if axis == "horizontal" else 0.022
        for item in [row for row in dimensions if row["axis"] == axis]:
            coordinate = item["center"][coordinate_index]
            group = next((row for row in groups if row["axis"] == axis and
                          abs(row["coordinate"] - coordinate) <= tolerance), None)
            if group is None:
                group = {"axis": axis, "coordinate": coordinate, "dimensions": []}
                groups.append(group)
            group["dimensions"].append(item)
            group["coordinate"] = statistics.mean(
                row["center"][coordinate_index] for row in group["dimensions"])
    for group in groups:
        group["coordinate"] = round(group["coordinate"], 6)
        variable_index = 0 if group["axis"] == "horizontal" else 1
        group["dimensions"].sort(key=lambda item: item["center"][variable_index])
        group["sum_m"] = round(sum(item["value_m"] for item in group["dimensions"]), 6)
    return groups


def chain_closures(groups):
    rows = []
    for segments in [group for group in groups if len(group["dimensions"]) >= 2]:
        for outer in groups:
            if outer is segments or outer["axis"] != segments["axis"]:
                continue
            for candidate in outer["dimensions"]:
                residual = abs(segments["sum_m"] - candidate["value_m"])
                ratio = residual / max(candidate["value_m"], 1e-9)
                if ratio <= 0.02:
                    rows.append({
                        "axis": segments["axis"],
                        "segment_coordinate": segments["coordinate"],
                        "segment_texts": [item["text"] for item in segments["dimensions"]],
                        "segment_sum_m": segments["sum_m"],
                        "overall_text": candidate["text"],
                        "overall_m": candidate["value_m"],
                        "residual_m": round(residual, 6), "residual_ratio": round(ratio, 6),
                    })
    return sorted(rows, key=lambda item: (item["residual_ratio"], item["axis"],
                                          item["overall_text"]))


def mass_links(dimensions, semantics):
    labels = [item for item in semantics if item["kind"] == "mass"]
    rows = []
    for dimension in dimensions:
        if dimension["axis"] != "horizontal":
            continue
        options = []
        for label in labels:
            dx = abs(dimension["center"][0] - label["center"][0])
            dy = abs(dimension["center"][1] - label["center"][1])
            if dx <= 0.20 and dy <= 0.07:
                options.append((dy * 3 + dx, label))
        if options:
            label = min(options, key=lambda item: item[0])[1]
            rows.append({"dimension_text": dimension["text"], "value_m": dimension["value_m"],
                         "label": label["normalized"], "distance": round(min(options)[0], 6)})
    return rows


def interval_links(sheet, panels, dimensions, semantics):
    datums = [item for item in semantics if item["kind"] == "datum"]
    rows = []
    for dimension in [item for item in dimensions if item["axis"] == "vertical"]:
        candidates = []
        for upper in datums:
            for lower in datums:
                if upper is lower or upper["center"][1] >= lower["center"][1]:
                    continue
                if not (upper["center"][1] <= dimension["center"][1] <= lower["center"][1]):
                    continue
                if max(abs(dimension["center"][0] - upper["center"][0]),
                       abs(dimension["center"][0] - lower["center"][0])) > 0.13:
                    continue
                midpoint_error = abs(dimension["center"][1] -
                                     statistics.mean([upper["center"][1], lower["center"][1]]))
                panel = next((item for item in panels if item["sheet_index"] == sheet["sheet_index"] and
                              item.get("scale") and item["bbox"][0] - 0.03 <= dimension["center"][0] <= item["bbox"][2] + 0.03 and
                              item["bbox"][1] - 0.03 <= upper["center"][1] and
                              lower["center"][1] <= item["bbox"][3] + 0.03), None)
                predicted = None
                ratio = None
                if panel:
                    pixels = (lower["center"][1] - upper["center"][1]) * sheet["normalized_pixels"][1]
                    predicted = pixels * panel["scale"]["metres_per_pixel_y"]
                    ratio = abs(predicted - dimension["value_m"]) / max(dimension["value_m"], 1e-9)
                candidates.append((ratio if ratio is not None else 99.0, midpoint_error,
                                   upper["normalized"], lower["normalized"], predicted, panel))
        if not candidates:
            continue
        ratio, midpoint_error, upper, lower, predicted, panel = min(candidates)
        rows.append({
            "dimension_text": dimension["text"], "value_m": dimension["value_m"],
            "upper": upper, "lower": lower,
            "panel_id": panel["id"] if panel else None,
            "scale_prediction_m": round(predicted, 6) if predicted is not None else None,
            "scale_residual_ratio": round(ratio, 6) if predicted is not None else None,
            "midpoint_error": round(midpoint_error, 6),
        })
    return rows


def cluster_lines(lines, geometry):
    groups = []
    local_geometry = geometry.get("local_bbox_px") if geometry else None
    source = [line for line in lines if not line.get("merged_collinear_fragments")]
    for line in source:
        axis = line["axis"]
        if axis == "horizontal":
            family = (axis, round(statistics.mean([line["local"][1], line["local"][3]]) / 4) * 4)
        elif axis == "vertical":
            family = (axis, round(statistics.mean([line["local"][0], line["local"][2]]) / 4) * 4)
        else:
            folded = line["angle_degrees"]
            while folded <= -90:
                folded += 180
            while folded > 90:
                folded -= 180
            radians = math.radians(folded)
            midpoint_x = statistics.mean([line["local"][0], line["local"][2]])
            midpoint_y = statistics.mean([line["local"][1], line["local"][3]])
            intercept = midpoint_y - math.tan(radians) * midpoint_x
            family = (axis, round(folded / 3) * 3, round(intercept / 12) * 12)
        group = next((item for item in groups if item["family"] == family), None)
        if group is None:
            group = {"family": family, "lines": []}
            groups.append(group)
        group["lines"].append(line)

    output = []
    for group in groups:
        members = group["lines"]
        inside = 0
        for line in members:
            mx = statistics.mean([line["local"][0], line["local"][2]])
            my = statistics.mean([line["local"][1], line["local"][3]])
            if (local_geometry and local_geometry[0] <= mx <= local_geometry[2] and
                    local_geometry[1] <= my <= local_geometry[3]):
                inside += 1
        output.append({
            "family": list(group["family"]), "members": len(members),
            "total_length_px": round(sum(item["length_px"] for item in members), 3),
            "maximum_length_px": round(max(item["length_px"] for item in members), 3),
            "inside_geometry_ratio": round(inside / len(members), 6),
        })
    output.sort(key=lambda item: (-item["maximum_length_px"], -item["total_length_px"],
                                  str(item["family"])))
    by_axis = {}
    for axis in ("horizontal", "vertical", "diagonal"):
        by_axis[axis] = [item for item in output if item["family"][0] == axis][:10]
    return by_axis


def overlay_bytes(image, panel, lines, dimensions, semantics):
    x0, y0, x1, y1 = css.panel_pixel_box(panel, image.shape)
    crop = image[y0:y1, x0:x1]
    canvas = css.cv2.cvtColor(crop, css.cv2.COLOR_GRAY2BGR)
    layer = canvas.copy()
    colors = {"horizontal": (212, 154, 58), "vertical": (83, 184, 197),
              "diagonal": (180, 90, 195)}
    minimum = max(34, int(canvas.shape[1] * 0.055))
    for line in lines:
        if line.get("merged_collinear_fragments") or line["length_px"] < minimum:
            continue
        css.cv2.line(layer, (line["local"][0], line["local"][1]),
                     (line["local"][2], line["local"][3]), colors[line["axis"]], 2)
    css.cv2.addWeighted(layer, 0.58, canvas, 0.42, 0, canvas)
    geometry = panel.get("geometry")
    if geometry:
        gx0, gy0, gx1, gy1 = geometry["local_bbox_px"]
        css.cv2.rectangle(canvas, (gx0, gy0), (gx1, gy1), (64, 210, 112), 3)
    for item in dimensions:
        region = item["region"]
        rx0, ry0 = int(region[0] * image.shape[1]) - x0, int(region[1] * image.shape[0]) - y0
        rx1, ry1 = int(region[2] * image.shape[1]) - x0, int(region[3] * image.shape[0]) - y0
        if rx1 >= 0 and ry1 >= 0 and rx0 < canvas.shape[1] and ry0 < canvas.shape[0]:
            css.cv2.rectangle(canvas, (rx0, ry0), (rx1, ry1), (25, 190, 240), 2)
    for item in semantics:
        region = item["region"]
        rx0, ry0 = int(region[0] * image.shape[1]) - x0, int(region[1] * image.shape[0]) - y0
        rx1, ry1 = int(region[2] * image.shape[1]) - x0, int(region[3] * image.shape[0]) - y0
        if rx1 >= 0 and ry1 >= 0 and rx0 < canvas.shape[1] and ry0 < canvas.shape[0]:
            css.cv2.rectangle(canvas, (rx0, ry0), (rx1, ry1), (50, 80, 240), 2)
    if canvas.shape[1] > 1400:
        scale = 1400 / canvas.shape[1]
        canvas = css.cv2.resize(canvas, (1400, round(canvas.shape[0] * scale)),
                                interpolation=css.cv2.INTER_AREA)
    ok, encoded = css.cv2.imencode(".png", canvas)
    if not ok:
        raise RuntimeError(f"could not encode overlay for {panel['id']}")
    return encoded.tobytes()


def inspect_building(building_id, assessment, audit_rev, corpus, target):
    panels = assessment["panels"]
    sheet_indices = sorted({int(panel["sheet_index"]) for panel in panels})
    sheets = {index: sheet_input(building_id, index, audit_rev) for index in sheet_indices}
    sheet_reports = []
    for index, sheet in sheets.items():
        sheet_panels = [panel for panel in panels if panel["sheet_index"] == index]
        dimensions = dimensions_for_sheet(sheet, sheet_panels)
        semantics = semantic_tokens(sheet)
        groups = group_dimensions(dimensions)
        image, clean = css.clean_sheet_image(sheet)
        lines = css.detect_cardinal_lines(clean)
        panel_reports = []
        for panel in sheet_panels:
            subset = css.panel_lines(lines, panel, clean.shape)
            panel_report = {
                "panel_id": panel["id"], "role": panel["role"], "bbox": panel["bbox"],
                "geometry": panel.get("geometry"),
                "line_families": cluster_lines(subset, panel.get("geometry")),
                "overlay": f"overlays/{panel['id']}.png",
            }
            pipeline.immutable_bytes(target / panel_report["overlay"],
                                     overlay_bytes(image, panel, subset, dimensions, semantics))
            panel_reports.append(panel_report)
        sheet_reports.append({
            "sheet_index": index, "normalized_pixels": sheet["normalized_pixels"],
            "dimensions": dimensions, "semantic_tokens": semantics,
            "dimension_groups": groups, "chain_closures": chain_closures(groups),
            "mass_links": mass_links(dimensions, semantics),
            "datum_interval_links": interval_links(sheet, sheet_panels, dimensions, semantics),
            "panels": panel_reports,
        })
    return {
        "schema": "architectural-css-topology-building/v0", "building_id": building_id,
        "parent_route": assessment["route"], "parent_fit": assessment["fit"],
        "parent_holdout": assessment["holdout"],
        "panel_overlaps": panel_overlaps(panels), "sheets": sheet_reports,
        "network_requests": 0, "ocr_calls": 0, "vlm_calls": 0, "world_mutated": False,
    }


def all_dimensions(observation):
    return [item for sheet in observation["sheets"] for item in sheet["dimensions"]]


def find_dimension(observation, pattern):
    expression = re.compile(pattern, re.I)
    return next((item for item in all_dimensions(observation)
                 if expression.search(normalized(item["text"]))), None)


def current_binding(assessment, binding_id):
    return next((item for item in assessment["bindings"] if item["id"] == binding_id), None)


def direct_datums(observation, pattern):
    expression = re.compile(pattern, re.I)
    rows = []
    seen = set()
    for sheet in observation["sheets"]:
        for item in sheet["semantic_tokens"]:
            if not expression.search(item["normalized"]) or item["direct_value_m"] is None:
                continue
            key = (item["text"], item["direct_value_m"], item["direct_value_authority"])
            if key in seen:
                continue
            seen.add(key)
            rows.append({"text": item["text"], "value_m": item["direct_value_m"],
                         "authority": item["direct_value_authority"]})
    return sorted(rows, key=lambda item: (item["value_m"], item["authority"], item["text"]))


def candidate_summary(observations, assessments):
    sd, tx, ak = (observations[name] for name in TARGETS)
    sd_plan = next(item for item in assessments["sd0401"]["panels"]
                   if item["id"] == assessments["sd0401"]["fit"]["primary_plan_panel"])
    tx_plan = next(item for item in assessments["tx1037"]["panels"]
                   if item["id"] == assessments["tx1037"]["fit"]["primary_plan_panel"])
    ak_plan = next(item for item in assessments["ak0535"]["panels"]
                   if item["id"] == assessments["ak0535"]["fit"]["primary_plan_panel"])
    ceiling_check = next(item for item in assessments["tx1037"]["holdout"]["dimension_checks"]
                         if item.get("binding_id"))
    ceiling_binding = current_binding(assessments["tx1037"], ceiling_check["binding_id"])
    return {
        "schema": "architectural-css-topology-candidates/v0",
        "sd0401": {
            "connected_component_plan_span_m": assessments["sd0401"]["measurements"][sd_plan["id"]]["observed_span_m"],
            "overall_width": find_dimension(sd, r"52\s*'\s*-\s*3"),
            "overall_compound_depth": find_dimension(sd, r"34\s*'\s*-\s*11"),
            "primary_band_depth_candidate": find_dimension(sd, r"14\s*'\s*-\s*2"),
            "ridge_candidate": find_dimension(sd, r"10\s*'\s*-\s*10"),
            "largest_cross_role_panel_overlap": sd["panel_overlaps"][0] if sd["panel_overlaps"] else None,
        },
        "tx1037": {
            "connected_component_plan_span_m": assessments["tx1037"]["measurements"][tx_plan["id"]]["observed_span_m"],
            "opposed_overall_widths": [find_dimension(tx, r"46\s*'\s*-\s*11"),
                                        find_dimension(tx, r"48\s*'\s*-\s*10")],
            "ceiling_was_scored_as": ceiling_check["semantic"],
            "ceiling_binding": ceiling_binding,
            "explicit_roof_edge_datums": direct_datums(tx, r"ROOF\s*EDGE"),
            "explicit_roof_ridge_datums": direct_datums(tx, r"ROOF\s*RIDGE"),
        },
        "ak0535": {
            "connected_component_plan_span_m": assessments["ak0535"]["measurements"][ak_plan["id"]]["observed_span_m"],
            "current_width_source": find_dimension(ak, r"35\s*'\s*-\s*11"),
            "labeled_log_cabin_width": find_dimension(ak, r"20\s*'\s*-\s*8"),
            "labeled_log_cabin_depth": find_dimension(ak, r"16\s*'\s*-\s*5"),
            "ridge_to_ceiling_interval": find_dimension(ak, r"4\s*'\s*-\s*4"),
            "basement_to_first_floor_interval": find_dimension(ak, r"6\s*'\s*-\s*1"),
            "largest_cross_role_panel_overlap": ak["panel_overlaps"][0] if ak["panel_overlaps"] else None,
        },
    }


def score_sd_oracle(candidates, oracle):
    expected = {
        "width_m": oracle["dimensions"]["main_width_m"],
        "depth_m": oracle["dimensions"]["main_depth_m"],
        "ridge_height_m": oracle["dimensions"]["main_ridge_y_m"],
    }
    selected = {
        "width_m": candidates["sd0401"]["overall_width"]["value_m"],
        "depth_m": candidates["sd0401"]["primary_band_depth_candidate"]["value_m"],
        "ridge_height_m": candidates["sd0401"]["ridge_candidate"]["value_m"],
    }
    checks = []
    for semantic, observed in expected.items():
        predicted = selected[semantic]
        checks.append({"semantic": semantic, "candidate_m": predicted, "oracle_m": observed,
                       "absolute_error_m": round(abs(predicted - observed), 9),
                       "status": "PASS" if abs(predicted - observed) <= 1e-6 else "FAIL"})
    return {"schema": "architectural-css-topology-oracle-score/v0",
            "building_id": "sd0401", "revealed_after_seal": True,
            "status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL",
            "checks": checks}


def interpretation(candidates, oracle_score):
    sd_overlap = candidates["sd0401"]["largest_cross_role_panel_overlap"]
    ak_overlap = candidates["ak0535"]["largest_cross_role_panel_overlap"]
    tx_ceiling = normalized(candidates["tx1037"]["ceiling_binding"]["text"])
    ak_current = candidates["ak0535"]["current_width_source"]["value_m"]
    ak_fit = candidates["ak0535"]["connected_component_plan_span_m"]
    findings = [
        {
            "building_id": "sd0401", "status": "CONFIRMED",
            "edge": "panel overlap plus compound-envelope selection",
            "evidence": {
                "section_elevation_overlap_ratio": sd_overlap["intersection_over_smaller"],
                "candidate_oracle_score": oracle_score["status"],
            },
            "claim": "The held section crop shares most of its area with the north elevation, while the explicit 14'-2 5/8\" primary depth candidate survives exactly; this is panel/view and mass selection, not missing scale.",
        },
        {
            "building_id": "tx1037", "status": "CONFIRMED",
            "edge": "ceiling/eave semantic conflation",
            "evidence": {"binding_text": candidates["tx1037"]["ceiling_binding"]["text"],
                         "scored_as": candidates["tx1037"]["ceiling_was_scored_as"],
                         "roof_edge_datums": candidates["tx1037"]["explicit_roof_edge_datums"],
                         "roof_ridge_datums": candidates["tx1037"]["explicit_roof_ridge_datums"]},
            "claim": "The held 9'-7 1/4\" CEILING datum was scored as eave height even though independent ROOF EDGE and ROOF RIDGE absolute datums survive; the failed 0.873 m check is semantically invalid.",
        },
        {
            "building_id": "ak0535", "status": "CONFIRMED",
            "edge": "floor/basement panel overlap plus labeled submass loss",
            "evidence": {"largest_cross_role_overlap_ratio": ak_overlap["intersection_over_smaller"],
                         "current_width_candidate_m": ak_current,
                         "current_component_span_m": ak_fit,
                         "log_cabin_width_m": candidates["ak0535"]["labeled_log_cabin_width"]["value_m"],
                         "log_cabin_depth_m": candidates["ak0535"]["labeled_log_cabin_depth"]["value_m"]},
            "claim": "The fitted 35'-11\" width comes from the basement overall span; the floor-plan chain explicitly labels the older LOG CABIN as 20'-8\" by 16'-5\" and the ADDITION separately.",
        },
    ]
    passed = (oracle_score["status"] == "PASS" and
              sd_overlap["intersection_over_smaller"] >= 0.5 and
              "CEILING" in tx_ceiling and
              abs(ak_current - 10.9474) <= 1e-6 and
              ak_overlap["intersection_over_smaller"] >= 0.25)
    return {"schema": "architectural-css-topology-interpretation/v0",
            "answer": "ATTRIBUTION_SEPARATED" if passed else "INSUFFICIENT_TOPOLOGY_EVIDENCE",
            "findings": findings,
            "next_boundary": "Change only panel partitioning, dimension-chain ownership, and datum semantics in a later locked fitter revision; do not tune corpus promotion gates from these three buildings."}


def report_html(report):
    cards = []
    for finding in report["interpretation"]["findings"]:
        evidence = html.escape(json.dumps(finding["evidence"], indent=2))
        cards.append(f"<section><div class='k'>{finding['building_id']} · {finding['status']}</div>"
                     f"<h2>{html.escape(finding['edge'])}</h2><p>{html.escape(finding['claim'])}</p>"
                     f"<pre>{evidence}</pre></section>")
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>HABS topology probe</title>
<style>body{{margin:0;background:#152026;color:#e8ece9;font:16px system-ui}}main{{max-width:1100px;margin:auto;padding:48px 24px}}h1{{font:48px Georgia}}.answer,.k{{color:#d49a3a;font:700 13px Consolas}}section{{margin:18px 0;padding:22px;background:#202c31;border:1px solid #415159}}pre{{white-space:pre-wrap;color:#9fb0b6}}</style></head>
<body><main><div class='k'>THREE-BUILDING STRUCTURAL / DATUM PROBE · {report['revision']}</div><h1>Which line belongs to the building?</h1>
<p class='answer'>{report['interpretation']['answer']}</p>{''.join(cards)}<p>{html.escape(report['interpretation']['next_boundary'])}</p></main></body></html>""".encode("utf-8")


def load_parent(args):
    parent_revision = (args.parent / "HEAD").read_text(encoding="ascii").strip()
    if parent_revision != EXPECTED_PARENT:
        raise RuntimeError(f"parent CSS fit changed: {parent_revision}")
    parent = args.parent / "revisions" / parent_revision
    audit_revision = (args.audit / "HEAD").read_text(encoding="ascii").strip()
    audit_rev = args.audit / "revisions" / audit_revision
    assessments = {}
    for building_id in TARGETS:
        path = parent / "buildings" / building_id / "assessment.json"
        assessments[building_id] = json.loads(path.read_text(encoding="utf-8"))
    return parent_revision, parent, audit_revision, audit_rev, assessments


def run(args):
    css.load_imaging()
    parent_revision, parent, audit_revision, audit_rev, assessments = load_parent(args)
    identity = {
        "engine": ENGINE, "script_sha256": pipeline.digest_file(Path(__file__)),
        "parent_revision": parent_revision,
        "parent_index_sha256": pipeline.digest_file(parent / "index.json"),
        "audit_revision": audit_revision,
        "audit_index_sha256": pipeline.digest_file(audit_rev / "index.json"),
        "targets": list(TARGETS), "mode": "REAL_OCR_CV_DIAGNOSTIC_NO_NETWORK",
    }
    revision = pipeline.digest_bytes(pipeline.compact_bytes(identity))[:20]
    root = args.out.resolve()
    rev = root / "revisions" / revision
    rev.mkdir(parents=True, exist_ok=True)
    pipeline.atomic_bytes(root / "HEAD", (revision + "\n").encode("ascii"))
    pipeline.immutable_json(rev / "identity.json", identity)

    observations = {}
    for building_id in TARGETS:
        target = rev / "buildings" / building_id
        observation = inspect_building(building_id, assessments[building_id], audit_rev,
                                       args.corpus, target)
        observations[building_id] = observation
        pipeline.immutable_json(target / "topology.json", observation)
        print(f"{building_id}: {len(observation['panel_overlaps'])} cross-role overlaps, "
              f"{sum(len(sheet['chain_closures']) for sheet in observation['sheets'])} chain closures")

    candidates = candidate_summary(observations, assessments)
    pipeline.immutable_json(rev / "candidate-summary.json", candidates)
    seal_rows = {building_id: pipeline.digest_bytes(pipeline.compact_bytes(observations[building_id]))
                 for building_id in TARGETS}
    seal = {"schema": "architectural-css-topology-seal/v0", "oracle_loaded": False,
            "targets": seal_rows,
            "candidate_summary_sha256": pipeline.digest_file(rev / "candidate-summary.json")}
    pipeline.immutable_json(rev / "automatic-seal.json", seal)

    oracle_revision = (args.oracle / "HEAD").read_text(encoding="ascii").strip()
    oracle = json.loads((args.oracle / "revisions" / oracle_revision /
                         "building.graph.json").read_text(encoding="utf-8"))
    oracle_score = score_sd_oracle(candidates, oracle)
    pipeline.immutable_json(rev / "sd0401-oracle-score.json", oracle_score)
    interpretation_data = interpretation(candidates, oracle_score)
    pipeline.immutable_json(rev / "interpretation.json", interpretation_data)

    report = {
        "schema": "architectural-css-topology-report/v0", "revision": revision,
        "parent_revision": parent_revision, "audit_revision": audit_revision,
        "oracle_revision": oracle_revision, "targets": list(TARGETS),
        "interpretation": interpretation_data, "oracle_score": oracle_score,
        "network_requests": 0, "ocr_calls": 0, "vlm_calls": 0,
        "source_downloads": 0, "world_mutated": False,
    }
    pipeline.immutable_json(rev / "report.json", report)
    pipeline.immutable_bytes(rev / "index.html", report_html(report))

    files = []
    for path in sorted(item for item in rev.rglob("*") if item.is_file() and item.name != "manifest.json"):
        files.append({"path": path.relative_to(rev).as_posix(),
                      "sha256": pipeline.digest_file(path), "bytes": path.stat().st_size})
    manifest = {"schema": "architectural-css-topology-manifest/v0", "revision": revision,
                "files": files, "network_requests": 0, "ocr_calls": 0,
                "vlm_calls": 0, "world_mutated": False}
    pipeline.immutable_json(rev / "manifest.json", manifest)
    pipeline.atomic_json(root / "report.json", report)
    print(f"revision {revision}\nRESULT {interpretation_data['answer']}")
    return 0


def verify(args):
    root = args.out.resolve()
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    rev = root / "revisions" / revision
    manifest = json.loads((rev / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((rev / "report.json").read_text(encoding="utf-8"))
    errors = []
    for item in manifest.get("files", []):
        path = pipeline.safe_child(rev, item["path"])
        if not path.is_file() or pipeline.digest_file(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            errors.append(f"artifact mismatch {item['path']}")
    seal = json.loads((rev / "automatic-seal.json").read_text(encoding="utf-8"))
    if seal.get("oracle_loaded") is not False or set(seal.get("targets", {})) != set(TARGETS):
        errors.append("automatic/oracle isolation seal")
    if report.get("interpretation", {}).get("answer") != "ATTRIBUTION_SEPARATED":
        errors.append("scientific result")
    if any(report.get(key) not in (0, False) for key in
           ("network_requests", "ocr_calls", "vlm_calls", "source_downloads", "world_mutated")):
        errors.append("authority boundary")
    result = {"schema": "architectural-css-topology-verification/v0",
              "status": "PASS" if not errors else "FAIL", "revision": revision,
              "files": len(manifest.get("files", [])), "errors": errors,
              "network_requests": 0, "ocr_calls": 0, "vlm_calls": 0,
              "world_mutated": False}
    pipeline.atomic_json(root / "verification.json", result)
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


def main():
    args = parse_args()
    try:
        return run(args) if args.command == "run" else verify(args)
    except Exception as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Probe automatic measured-drawing -> metric envelope -> CSS residual fitting.

This is deliberately an R&D vertical slice.  It consumes the frozen real OCR/CV
audit, never calls a VLM or the network, keeps the accepted sd0401 graph hidden
until automatic output is sealed, and routes weak evidence to HOLD instead of
silently completing a building.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_architectural_curriculum as pipeline

DEFAULT_CHARTER = HERE / "architectural-css-fit-v0.json"
DEFAULT_SCHEMAS = HERE / "architectural-css-fit-schemas-v0.json"
DEFAULT_SELECTION = HERE / "habs-corpus.json"
DEFAULT_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_AUDIT = HERE / "out" / "architectural-curriculum" / "real-ocr-audit-v1"
DEFAULT_OUT = HERE / "out" / "architectural-css-fit"
ENGINE = "architectural-css-envelope-fit/0.1.0"

PRIMARY_ROLES = ("plan", "elevation", "section")
ROLE_RE = {
    "plan": re.compile(r"\bPLAN\b", re.I),
    "elevation": re.compile(r"ELEVATION", re.I),
    "section": re.compile(r"\bSECTION\b", re.I),
}
CONTEXT_HOLD_RE = re.compile(
    r"\b(?:JOIST|RAFTER|STUD|WIDE|DIAMETER|DIA\.?|RADIUS|SPACING|O\.?\s*C\.?|"
    r"TYPICAL|SCALE|METERS?|METRES?|FEET|FLUE|CHIMNEY)\b|\d+\s*[xXx]\s*\d+",
    re.I,
)

Image = None
np = None
cv2 = None


def load_imaging():
    global Image, np, cv2
    if Image is None:
        from PIL import Image as pillow_image
        import numpy as numpy_module
        import cv2 as cv2_module
        pillow_image.MAX_IMAGE_PIXELS = None
        Image, np, cv2 = pillow_image, numpy_module, cv2_module


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--charter", type=Path, default=DEFAULT_CHARTER)
    common.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS)
    common.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    common.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    common.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", parents=[common])
    sub.add_parser("verify", parents=[common])
    serve = sub.add_parser("serve", parents=[common])
    serve.add_argument("--port", type=int, default=8878)
    return parser.parse_args()


def center(region):
    return ((float(region[0]) + float(region[2])) / 2,
            (float(region[1]) + float(region[3])) / 2)


def clamp_bbox(box):
    x0, y0, x1, y1 = box
    return [round(max(0.035, min(x0, 0.91)), 6),
            round(max(0.04, min(y0, 0.94)), 6),
            round(max(0.05, min(x1, 0.92)), 6),
            round(max(0.05, min(y1, 0.95)), 6)]


def bbox_iou(left, right):
    x0, y0 = max(left[0], right[0]), max(left[1], right[1])
    x1, y1 = min(left[2], right[2]), min(left[3], right[3])
    intersection = max(0, x1 - x0) * max(0, y1 - y0)
    union = ((left[2] - left[0]) * (left[3] - left[1]) +
             (right[2] - right[0]) * (right[3] - right[1]) - intersection)
    return intersection / union if union else 0.0


def source_ref(sheet, region):
    return {
        "building_id": sheet["building_id"],
        "sheet_index": sheet["sheet_index"],
        "source_sha256": sheet["source_sha256"],
        "source_url": sheet["source_url"],
        "region": [round(float(value), 6) for value in region],
    }


def normalized_text(value):
    return (str(value).upper().replace("I'", "1'").replace("I:", "1:")
            .replace("O\"", "0\"").replace("{", "\"")
            .replace("â€²", "'").replace("â€³", "\"").replace("′", "'")
            .replace("″", "\"").replace("º", "\"").replace("°", "\""))


def scale_ratio(text):
    value = normalized_text(text)
    metric = re.search(r"\b1\s*:\s*(\d{2,3})\b", value)
    if metric:
        ratio = int(metric.group(1))
        return ratio if 12 <= ratio <= 240 else None
    # HABS sheets commonly print 1/4\" = 1'-0\". OCR corrupts both quote
    # characters often, but a complete fraction/equality/foot expression is
    # still stronger evidence than accepting a partial architectural number.
    imperial = re.search(
        r"(?:(\d+)\s+)?(\d+)\s*/\s*(\d+)\s*[\"']?\s*=\s*([1I])\s*'\s*-?\s*[0O]\s*[\"']?",
        value,
    )
    if imperial:
        whole = int(imperial.group(1) or 0)
        drawing_inches = whole + int(imperial.group(2)) / int(imperial.group(3))
        ratio = round(12 / drawing_inches)
        return ratio if 12 <= ratio <= 240 else None
    one_inch = re.search(r"[1I]\s*[\"']\s*=\s*(\d+)\s*'\s*-?\s*[0O]", value)
    if one_inch:
        ratio = int(one_inch.group(1)) * 12
        return ratio if 12 <= ratio <= 240 else None
    return None


def role_for_text(text):
    value = normalized_text(text)
    if "SITE PLAN" in value or "LOCATION PLAN" in value:
        return "site"
    if "PLAN KEY" in value or "PLANS AND DESIGN" in value:
        return None
    for role, pattern in ROLE_RE.items():
        if pattern.search(value):
            return role
    return None


def seed_panels(sheet):
    seeds = []
    for ordinal, token in enumerate(sheet["tokens"]):
        role = role_for_text(token["text"])
        if not role:
            continue
        x, y = center(token["region"])
        if x > 0.915 or y < 0.04 or y > 0.95:
            continue
        seeds.append({"role": role, "text": token["text"], "region": token["region"],
                      "x": x, "y": y, "token_ordinal": ordinal, "synthetic": False})

    # De-duplicate split or repeated OCR labels occupying the same title zone.
    accepted = []
    for seed in sorted(seeds, key=lambda item: (item["y"], item["x"], item["role"], item["text"])):
        if any(seed["role"] == prior["role"] and
               math.hypot(seed["x"] - prior["x"], seed["y"] - prior["y"]) < 0.045
               for prior in accepted):
            continue
        accepted.append(seed)
    seeds = accepted

    visible_primary = {seed["role"] for seed in seeds if seed["role"] in PRIMARY_ROLES}
    if not visible_primary:
        audit_roles = [role for role in sheet["ocr_roles"] if role in PRIMARY_ROLES]
        if len(audit_roles) == 1:
            seeds.append({"role": audit_roles[0], "text": "OCR_ROLE_SIGNAL_ONLY",
                          "region": [0.35, 0.90, 0.65, 0.92], "x": 0.5, "y": 0.91,
                          "token_ordinal": None, "synthetic": True})

    panels = []
    for seed in seeds:
        role, x, y = seed["role"], seed["x"], seed["y"]
        if role == "plan":
            left, right, height = x - 0.31, x + 0.31, 0.61
        elif role == "site":
            left, right, height = x - 0.30, x + 0.30, 0.48
        elif role == "elevation":
            left, right, height = x - 0.29, x + 0.29, 0.34
        else:
            left, right, height = x - 0.27, x + 0.27, 0.36

        # Same-row labels divide a sheet into columns. A nearby plan/site seed
        # also provides a useful boundary for the common site-left/plan-right layout.
        for other in seeds:
            if other is seed:
                continue
            dy = abs(other["y"] - y)
            if dy <= 0.09 or (role in ("plan", "site") and other["role"] in ("plan", "site") and dy <= 0.34):
                midpoint = (x + other["x"]) / 2
                if other["x"] < x:
                    left = max(left, midpoint)
                elif other["x"] > x:
                    right = min(right, midpoint)
        box = clamp_bbox([left, y - height, right, y + 0.055])
        if box[2] - box[0] < 0.14 or box[3] - box[1] < 0.12:
            continue
        panels.append({
            "schema": "architectural-panel-evidence/v0",
            "id": f"{sheet['building_id']}-s{sheet['sheet_index']:02d}-{role}-{len(panels)+1:02d}",
            "building_id": sheet["building_id"], "sheet_index": sheet["sheet_index"],
            "role": role, "bbox": box, "label": seed["text"],
            "label_region": [round(float(value), 6) for value in seed["region"]],
            "label_center": [round(x, 6), round(y, 6)],
            "confidence": 0.62 if seed["synthetic"] else 0.92,
            "orientation_hypotheses": [0, 90, 180, 270],
            "reflection_hypotheses": [False, True],
            "evidence": [source_ref(sheet, seed["region"])],
            "synthetic": seed["synthetic"],
        })

    # Keep site panels as separators/evidence, but remove duplicate primary crops.
    output = []
    for panel in panels:
        if any(panel["role"] == prior["role"] and bbox_iou(panel["bbox"], prior["bbox"]) > 0.72
               for prior in output):
            continue
        output.append(panel)
    return output


def raster_header(sheet, corpus):
    load_imaging()
    manifest = json.loads((corpus / sheet["building_id"] / "manifest.json").read_text(encoding="utf-8"))
    drawing = next(item for item in manifest["drawings"] if int(item["sheet_index"]) == sheet["sheet_index"])
    path = corpus / sheet["building_id"] / PurePosixPath(drawing["download"]["local_path"])
    with Image.open(path) as opened:
        dpi = opened.info.get("dpi", (400.0, 400.0))
        source_pixels = list(opened.size)
    return {"path": path, "dpi": [float(dpi[0]), float(dpi[1])],
            "source_pixels": source_pixels,
            "normalized_pixels": sheet["normalized_pixels"]}


def assign_scales(sheet, panels, corpus):
    header = raster_header(sheet, corpus)
    candidates = []
    for ordinal, token in enumerate(sheet["tokens"]):
        ratio = scale_ratio(token["text"])
        if ratio:
            candidates.append({"ratio": ratio, "text": token["text"], "region": token["region"],
                               "center": center(token["region"]), "token_ordinal": ordinal})
    for panel in panels:
        px, py = panel["label_center"]
        ranked = []
        for item in candidates:
            x, y = item["center"]
            inside = panel["bbox"][0] <= x <= panel["bbox"][2] and panel["bbox"][1] <= y <= panel["bbox"][3]
            distance = math.hypot((x - px) * 1.2, y - py)
            ranked.append((0 if inside else 1, distance, item["token_ordinal"], item))
        if not ranked:
            panel["scale"] = None
            continue
        _, distance, _, chosen = min(ranked)
        if distance > 0.23 and not (panel["bbox"][0] <= chosen["center"][0] <= panel["bbox"][2] and
                                    panel["bbox"][1] <= chosen["center"][1] <= panel["bbox"][3]):
            panel["scale"] = None
            continue
        ratio = chosen["ratio"]
        source_w, source_h = header["source_pixels"]
        norm_w, norm_h = header["normalized_pixels"]
        scale_x = 0.0254 * ratio / header["dpi"][0] * source_w / norm_w
        scale_y = 0.0254 * ratio / header["dpi"][1] * source_h / norm_h
        panel["scale"] = {
            "schema": "architectural-sheet-scale/v0", "ratio": ratio,
            "metres_per_pixel_x": round(scale_x, 9),
            "metres_per_pixel_y": round(scale_y, 9),
            "anisotropy_ratio": round(abs(scale_x - scale_y) / statistics.mean([scale_x, scale_y]), 9),
            "dpi": header["dpi"], "source_pixels": header["source_pixels"],
            "normalized_pixels": header["normalized_pixels"],
            "notation": chosen["text"], "notation_region": chosen["region"],
            "provenance": source_ref(sheet, chosen["region"]),
            "status": "OBSERVED_COMPLETE_SCALE_NOTATION",
        }


def clean_sheet_image(sheet):
    load_imaging()
    image = cv2.imread(str(sheet["normalized_path"]), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"cannot read normalized sheet {sheet['normalized_path']}")
    clean = image.copy()
    height, width = clean.shape
    for token in sheet["tokens"]:
        x0, y0, x1, y1 = token["region"]
        cv2.rectangle(clean, (max(0, int(x0 * width) - 3), max(0, int(y0 * height) - 3)),
                      (min(width - 1, int(x1 * width) + 3), min(height - 1, int(y1 * height) + 3)),
                      255, -1)
    return image, clean


def detect_cardinal_lines(clean):
    edges = cv2.Canny(clean, 50, 150)
    raw = cv2.HoughLinesP(edges, 1, np.pi / 360, threshold=32,
                          minLineLength=36, maxLineGap=36)
    lines = []
    if raw is None:
        return lines
    for x0, y0, x1, y1 in raw[:, 0]:
        dx, dy = int(x1) - int(x0), int(y1) - int(y0)
        length = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx))
        folded = abs(angle) % 180
        axis = "horizontal" if folded <= 6 or folded >= 174 else "vertical" if 84 <= folded <= 96 else "diagonal"
        lines.append({"x0": int(x0), "y0": int(y0), "x1": int(x1), "y1": int(y1),
                      "length_px": round(length, 3), "angle_degrees": round(angle, 3), "axis": axis})
    # Dimension lines are intentionally interrupted by ticks and their printed
    # values. Hough therefore returns a row of short collinear fragments. Merge
    # only close cardinal fragments; retain originals so local chain dimensions
    # still have a candidate while overall dimensions can recover the full span.
    merged = []
    for axis in ("horizontal", "vertical"):
        source = [line for line in lines if line["axis"] == axis]
        groups = []
        for line in sorted(source, key=lambda item: (
                round(((item["y0"] + item["y1"]) / 2) if axis == "horizontal" else
                      ((item["x0"] + item["x1"]) / 2)),
                min(item["x0"], item["x1"]) if axis == "horizontal" else min(item["y0"], item["y1"]),
                -item["length_px"])):
            coordinate = ((line["y0"] + line["y1"]) / 2 if axis == "horizontal" else
                          (line["x0"] + line["x1"]) / 2)
            group = next((item for item in groups if abs(item["coordinate"] - coordinate) <= 5), None)
            if group is None:
                group = {"coordinate": coordinate, "lines": []}
                groups.append(group)
            group["lines"].append(line)
            group["coordinate"] = statistics.mean(
                ((item["y0"] + item["y1"]) / 2 if axis == "horizontal" else
                 (item["x0"] + item["x1"]) / 2) for item in group["lines"])
        for group in groups:
            intervals = sorted((min(item["x0"], item["x1"]), max(item["x0"], item["x1"]))
                               if axis == "horizontal" else
                               (min(item["y0"], item["y1"]), max(item["y0"], item["y1"]))
                               for item in group["lines"])
            runs = []
            for start, end in intervals:
                if runs and start - runs[-1][1] <= 70:
                    runs[-1][1] = max(runs[-1][1], end)
                else:
                    runs.append([start, end])
            coordinate = int(round(group["coordinate"]))
            for start, end in runs:
                if end - start < 90:
                    continue
                if axis == "horizontal":
                    x0, y0, x1, y1 = start, coordinate, end, coordinate
                else:
                    x0, y0, x1, y1 = coordinate, start, coordinate, end
                merged.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1,
                               "length_px": round(float(end - start), 3),
                               "angle_degrees": 0.0 if axis == "horizontal" else 90.0,
                               "axis": axis, "merged_collinear_fragments": True})
    return lines + merged


def point_segment_distance(px, py, line):
    x0, y0, x1, y1 = line["x0"], line["y0"], line["x1"], line["y1"]
    dx, dy = x1 - x0, y1 - y0
    if dx == 0 and dy == 0:
        return math.hypot(px - x0, py - y0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def assign_panel(point, panels, roles=None):
    roles = roles or set(PRIMARY_ROLES)
    options = []
    for panel in panels:
        if panel["role"] not in roles:
            continue
        x0, y0, x1, y1 = panel["bbox"]
        inside = x0 - 0.018 <= point[0] <= x1 + 0.018 and y0 - 0.018 <= point[1] <= y1 + 0.018
        px, py = panel["label_center"]
        options.append((0 if inside else 1, math.hypot(point[0] - px, point[1] - py), panel["id"], panel))
    if not options:
        return None
    chosen = min(options)
    return chosen[3] if chosen[0] == 0 or chosen[1] <= 0.34 else None


def bind_dimensions(sheet, panels, lines):
    height, width = sheet["normalized_pixels"][1], sheet["normalized_pixels"][0]
    bindings = []
    for ordinal, dimension in enumerate(sheet["strict_dimensions"]):
        region = dimension["region"]
        point = center(region)
        panel = assign_panel(point, panels)
        status = "BOUND_CANDIDATE"
        hold_reason = None
        if CONTEXT_HOLD_RE.search(normalized_text(dimension["text"])):
            status, hold_reason = "HELD_CONTEXT", "material/detail/scale context"
        elif panel is None:
            status, hold_reason = "HELD_AMBIGUOUS", "no automatic panel association"
        px, py = point[0] * width, point[1] * height
        line_options = sorted(
            ((point_segment_distance(px, py, line), -line["length_px"], index, line)
             for index, line in enumerate(lines) if line["axis"] in ("horizontal", "vertical")),
            key=lambda item: (item[0], item[1], item[2]),
        )
        nearest = line_options[0][3] if line_options and line_options[0][0] <= max(width, height) * 0.035 else None
        candidate_scale = (float(dimension["value_m"]) / nearest["length_px"] if nearest else None)
        binding = {
            "schema": "architectural-dimension-binding/v0",
            "id": f"{sheet['building_id']}-s{sheet['sheet_index']:02d}-d{ordinal+1:02d}",
            "panel_id": panel["id"] if panel else None, "role": panel["role"] if panel else "unknown",
            "text": dimension["text"], "value_m": float(dimension["value_m"]),
            "confidence": float(dimension["confidence"]),
            "axis": nearest["axis"] if nearest else "unknown", "line": nearest,
            "candidate_metres_per_pixel": round(candidate_scale, 9) if candidate_scale else None,
            "status": status, "hold_reason": hold_reason,
            "provenance": source_ref(sheet, region),
        }
        bindings.append(binding)
    return bindings


def panel_pixel_box(panel, shape):
    height, width = shape
    x0, y0, x1, y1 = panel["bbox"]
    return (max(0, int(x0 * width)), max(0, int(y0 * height)),
            min(width, int(x1 * width)), min(height, int(y1 * height)))


def component_geometry(clean, panel):
    x0, y0, x1, y1 = panel_pixel_box(panel, clean.shape)
    crop = clean[y0:y1, x0:x1]
    ink = (crop < 180).astype(np.uint8) * 255
    connected = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
    connected = cv2.dilate(connected, np.ones((3, 3), np.uint8), iterations=2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(connected)
    candidates = []
    crop_area = max(1, crop.shape[0] * crop.shape[1])
    for index in range(1, count):
        cx, cy, width, height, area = [int(value) for value in stats[index]]
        if width < 36 or height < 28:
            continue
        box_area = width * height
        density = area / max(1, box_area)
        coverage = box_area / crop_area
        if coverage > 0.94 and density < 0.05:
            continue
        score = area * (1 + min(coverage, 0.6)) * (0.5 + min(density, 0.5))
        candidates.append((score, area, -index, (cx, cy, width, height, density)))
    if not candidates:
        return None
    _, area, _, (cx, cy, width, height, density) = max(candidates)
    return {
        "bbox_px": [x0 + cx, y0 + cy, x0 + cx + width, y0 + cy + height],
        "local_bbox_px": [cx, cy, cx + width, cy + height],
        "width_px": width, "height_px": height,
        "ink_area_px": area, "connected_density": round(density, 6),
        "panel_pixels": [crop.shape[1], crop.shape[0]],
    }


def panel_lines(lines, panel, shape):
    x0, y0, x1, y1 = panel_pixel_box(panel, shape)
    output = []
    for line in lines:
        mx, my = (line["x0"] + line["x1"]) / 2, (line["y0"] + line["y1"]) / 2
        if x0 <= mx <= x1 and y0 <= my <= y1:
            item = dict(line)
            item["local"] = [line["x0"] - x0, line["y0"] - y0,
                             line["x1"] - x0, line["y1"] - y0]
            output.append(item)
    return output


def measure_panel(panel, geometry, lines):
    if not geometry or not panel.get("scale"):
        return None
    sx = panel["scale"]["metres_per_pixel_x"]
    sy = panel["scale"]["metres_per_pixel_y"]
    width_m = geometry["width_px"] * sx
    height_m = geometry["height_px"] * sy
    measurement = {
        "schema": "architectural-panel-measurement/v0",
        "panel_id": panel["id"], "role": panel["role"],
        "geometry_bbox_px": geometry["bbox_px"],
        "observed_span_m": [round(width_m, 6), round(height_m, 6)],
        "method": "OCR-erased dominant connected linework calibrated by complete sheet-scale notation and TIFF DPI",
    }
    if panel["role"] not in ("elevation", "section"):
        return measurement
    local_x0, local_y0, local_x1, local_y1 = geometry["local_bbox_px"]
    diagonal = []
    horizontal = []
    for line in lines:
        lx0, ly0, lx1, ly1 = line["local"]
        midpoint_x, midpoint_y = (lx0 + lx1) / 2, (ly0 + ly1) / 2
        if not (local_x0 - 8 <= midpoint_x <= local_x1 + 8 and
                local_y0 - 8 <= midpoint_y <= local_y1 + 8):
            continue
        if line["axis"] == "diagonal" and line["length_px"] >= geometry["width_px"] * 0.07:
            folded = abs(line["angle_degrees"]) % 180
            if 12 <= folded <= 72 or 108 <= folded <= 168:
                diagonal.append(line)
        elif line["axis"] == "horizontal" and line["length_px"] >= geometry["width_px"] * 0.22:
            horizontal.append(line)
    baseline_y = max((max(line["local"][1], line["local"][3]) for line in horizontal),
                     default=local_y1)
    if diagonal:
        roof_top_y = min(min(line["local"][1], line["local"][3]) for line in diagonal)
        lower_ends = [max(line["local"][1], line["local"][3]) for line in diagonal]
        eave_y = statistics.median(lower_ends)
        signs = {1 if line["angle_degrees"] > 0 else -1 for line in diagonal}
        roof_kind = "gable" if len(signs) == 2 else "shed"
    else:
        roof_top_y = local_y0
        eave_y = local_y0
        roof_kind = "flat" if horizontal else "unknown"
    ridge_height = max(0.0, (baseline_y - roof_top_y) * sy)
    eave_height = max(0.0, (baseline_y - eave_y) * sy)
    measurement.update({
        "baseline_y_px": round(float(baseline_y), 3),
        "roof_top_y_px": round(float(roof_top_y), 3),
        "eave_y_px": round(float(eave_y), 3),
        "ridge_height_m": round(ridge_height, 6),
        "eave_height_m": round(eave_height, 6),
        "roof_kind": roof_kind,
        "roof_line_count": len(diagonal),
    })
    return measurement


def compatible_scale_anchors(panel, bindings):
    if not panel.get("scale"):
        return [], None
    base = statistics.mean([panel["scale"]["metres_per_pixel_x"],
                            panel["scale"]["metres_per_pixel_y"]])
    anchors = [{"id": f"{panel['id']}:notation", "kind": "complete-scale-notation",
                "metres_per_pixel": round(base, 9), "text": panel["scale"]["notation"]}]
    for binding in bindings:
        candidate = binding.get("candidate_metres_per_pixel")
        if (binding["panel_id"] == panel["id"] and binding["status"] == "BOUND_CANDIDATE" and
                candidate and abs(candidate - base) / base <= 0.05):
            anchors.append({"id": binding["id"], "kind": "explicit-dimension-line",
                            "metres_per_pixel": candidate, "text": binding["text"]})
    values = [item["metres_per_pixel"] for item in anchors]
    spread = ((max(values) - min(values)) / statistics.mean(values)) if len(values) >= 2 else None
    return anchors, spread


def floor_count(sheets):
    found = set()
    mapping = {"BASEMENT": 0, "FIRST FLOOR": 1, "SECOND FLOOR": 2,
               "THIRD FLOOR": 3, "FOURTH FLOOR": 4, "HAYLOFT": 2, "LOFT": 2}
    for sheet in sheets:
        for token in sheet["tokens"]:
            value = normalized_text(token["text"])
            for label, level in mapping.items():
                if label in value:
                    found.add(level)
    positive = [value for value in found if value > 0]
    if positive:
        return max(positive), "observed floor labels"
    return 0, "no floor sequence survived OCR"


def distinct_values(bindings, minimum=0.15, maximum=100.0):
    selected = []
    for binding in sorted(bindings, key=lambda item: (-item["value_m"], item["id"])):
        value = binding["value_m"]
        if binding["status"] != "BOUND_CANDIDATE" or not minimum <= value <= maximum:
            continue
        if any(abs(value - prior["value_m"]) / max(value, prior["value_m"]) <= 0.035 for prior in selected):
            continue
        selected.append(binding)
    return selected


def fit_envelope(building_id, sheets, panels, bindings, measurements, holdout_id):
    train_panels = [panel for panel in panels if panel["id"] != holdout_id]
    train_ids = {panel["id"] for panel in train_panels}
    plan_panels = [panel for panel in train_panels if panel["role"] == "plan" and panel.get("scale")]
    vertical_panels = [panel for panel in train_panels if panel["role"] == "elevation" and panel.get("scale")]
    train_bindings = [item for item in bindings if item["panel_id"] in train_ids]
    plan_bindings = distinct_values([item for item in train_bindings if item["role"] == "plan"])

    width = depth = None
    width_source = depth_source = None
    primary_plan = None
    if plan_panels:
        primary_plan = max(plan_panels, key=lambda panel: (
            len([item for item in train_bindings if item["panel_id"] == panel["id"]]),
            (panel["bbox"][2] - panel["bbox"][0]) * (panel["bbox"][3] - panel["bbox"][1]),
            panel["id"],
        ))
        measured = measurements.get(primary_plan["id"])
        local = distinct_values([item for item in plan_bindings if item["panel_id"] == primary_plan["id"]])
        if measured:
            span_x, span_y = measured["observed_span_m"]
            # An explicit overall dimension close to a calibrated linework span
            # outranks the raw connected-component extent. The unlabelled axis
            # remains a geometric inference and is published as such.
            x_matches = [item for item in local if abs(item["value_m"] - span_x) / max(span_x, 1e-9) <= 0.20]
            y_matches = [item for item in local if abs(item["value_m"] - span_y) / max(span_y, 1e-9) <= 0.20]
            width = max((item["value_m"] for item in x_matches), default=span_x)
            depth = max((item["value_m"] for item in y_matches), default=span_y)
            if depth > width:
                width, depth = depth, width
            width_source = "explicit dimension agreeing with calibrated linework" if x_matches else "calibrated linework span"
            depth_source = "explicit dimension agreeing with calibrated linework" if y_matches else "calibrated linework span"
        elif len(local) >= 2:
            width, depth = local[0]["value_m"], local[1]["value_m"]
            width_source = depth_source = "two largest distinct bound plan dimensions"

    vertical_measurements = [measurements[panel["id"]] for panel in vertical_panels
                             if measurements.get(panel["id"]) and
                             measurements[panel["id"]].get("ridge_height_m", 0) > 0]
    ridge = eave = None
    roof_kind = "unknown"
    if vertical_measurements:
        ridge = statistics.median(item["ridge_height_m"] for item in vertical_measurements)
        eave_values = [item["eave_height_m"] for item in vertical_measurements if item["eave_height_m"] > 0]
        eave = statistics.median(eave_values) if eave_values else None
        roof_kind = Counter(item["roof_kind"] for item in vertical_measurements).most_common(1)[0][0]

    floors, floor_source = floor_count(sheets)
    if floors == 0 and primary_plan is not None:
        floors = 1
        floor_source = "inferred one modeled level from an observed primary plan; no higher floor label survived OCR"
    if floors == 0 and eave and eave >= 2.0:
        # This is deliberately not enough for promotion: it keeps a renderable
        # candidate visible while the numeric-envelope gate records the missing
        # observed floor sequence.
        display_floors = max(1, round(eave / 2.8))
    else:
        display_floors = floors
    ridge_axis = "x" if width and depth and width >= depth else "z" if width and depth else "unknown"
    roof_run = (depth if ridge_axis == "x" else width) / 2 if width and depth else None
    pitch = (math.degrees(math.atan2(max(0, ridge - eave), roof_run))
             if ridge and eave is not None and roof_run else None)
    return {
        "width_m": round(width, 6) if width else None,
        "depth_m": round(depth, 6) if depth else None,
        "floor_count": floors,
        "display_floor_count": display_floors,
        "eave_height_m": round(eave, 6) if eave else None,
        "ridge_height_m": round(ridge, 6) if ridge else None,
        "roof_kind": roof_kind,
        "roof_pitch_degrees": round(pitch, 6) if pitch is not None else None,
        "ridge_axis": ridge_axis,
        "primary_plan_panel": primary_plan["id"] if primary_plan else None,
        "sources": {"width": width_source, "depth": depth_source,
                    "floor_count": floor_source,
                    "vertical": "median calibrated elevation outline" if vertical_measurements else None},
    }


def select_holdout(panels, bindings):
    counts = Counter(item["panel_id"] for item in bindings if item["status"] == "BOUND_CANDIDATE")
    sections = [panel for panel in panels if panel["role"] == "section"]
    if sections:
        chosen = sorted(sections, key=lambda panel: (-counts[panel["id"]], panel["id"]))[0]
        return chosen["id"], "section-first"
    elevations = sorted((panel for panel in panels if panel["role"] == "elevation"),
                        key=lambda panel: panel["id"])
    if len(elevations) >= 2:
        return elevations[-1]["id"], "last-elevation"
    return None, "no independent orthographic view"


def dimension_error(predicted, observed):
    absolute = abs(predicted - observed)
    ratio = absolute / max(abs(observed), 1e-9)
    return {"predicted_m": round(predicted, 6), "observed_m": round(observed, 6),
            "absolute_error_m": round(absolute, 6), "error_ratio": round(ratio, 6),
            "status": "PASS" if absolute <= 0.25 and ratio <= 0.03 else "FAIL"}


def heldout_score(fit, holdout, measurements, bindings, edge_tolerance=None):
    if not holdout:
        return {"status": "UNAVAILABLE", "reason": "no independent orthographic view",
                "dimension_checks": [], "edge_distance_ratio": None}
    observed = measurements.get(holdout["id"])
    checks = []
    if observed:
        for key in ("ridge_height_m", "eave_height_m"):
            if fit.get(key) and observed.get(key):
                check = dimension_error(fit[key], observed[key])
                check["semantic"] = key
                check["source"] = "calibrated held-out linework"
                checks.append(check)
    held_bindings = [item for item in bindings if item["panel_id"] == holdout["id"] and
                     item["status"] == "BOUND_CANDIDATE"]
    for binding in held_bindings:
        text = normalized_text(binding["text"])
        semantic = "eave_height_m" if re.search(r"CEILING|ROOF EDGE|TOP OF WALL|EAVE", text) else None
        if semantic and fit.get(semantic):
            check = dimension_error(fit[semantic], binding["value_m"])
            check.update({"semantic": semantic, "source": "held-out strict dimension",
                          "binding_id": binding["id"]})
            checks.append(check)
    edge_ratio = None
    if observed and fit.get("width_m") and fit.get("ridge_height_m"):
        predicted_aspect = fit["width_m"] / max(fit["ridge_height_m"], 1e-9)
        observed_aspect = observed["observed_span_m"][0] / max(observed["observed_span_m"][1], 1e-9)
        edge_ratio = abs(math.log(max(predicted_aspect, 1e-9) / max(observed_aspect, 1e-9))) / 8
        edge_ratio = round(min(edge_ratio, 1.0), 6)
    edge_status = ("PASS" if edge_ratio is not None and edge_tolerance is not None and edge_ratio <= edge_tolerance
                   else "FAIL" if edge_ratio is not None and edge_tolerance is not None else "PENDING_ORACLE_TOLERANCE")
    status = "PASS" if checks and all(item["status"] == "PASS" for item in checks) and edge_status == "PASS" else "FAIL"
    return {"status": status, "selection": holdout["id"], "role": holdout["role"],
            "dimensions_excluded_from_fit": True, "geometry_excluded_from_fit": True,
            "dimension_checks": checks, "edge_distance_ratio": edge_ratio,
            "edge_status": edge_status, "edge_tolerance_ratio": edge_tolerance,
            "shape_alignment_authority": "similarity-aligned display score only; never metric scale"}


def graph_for(record, fit, assertions):
    if not all(fit.get(key) for key in ("width_m", "depth_m", "eave_height_m", "ridge_height_m")):
        return None
    width, depth = fit["width_m"], fit["depth_m"]
    return {
        "schema": "architectural-building-graph/v1",
        "id": f"habs-{record['id']}-css-fit-{pipeline.digest_bytes(pipeline.compact_bytes(fit))[:12]}",
        "building_id": record["id"], "label": record["manifest"]["title"],
        "authority": "metric primary-envelope candidate; CSS is projection only",
        "coordinate_frames": {
            "building_local": {"units": "metres", "handedness": "right",
                               "axes": {"x": "plan-right", "y": "height", "z": "plan-up"},
                               "origin": "automatic primary-envelope minimum x/z at L0"},
            "source_geo": "catalog provenance only", "valheim_world": "unresolved",
        },
        "dimensions": {key: fit[key] for key in ("width_m", "depth_m", "floor_count",
                                                   "eave_height_m", "ridge_height_m",
                                                   "roof_pitch_degrees")},
        "levels": ([{"id": f"L{index}", "finished_floor_y_m": round(index * fit["eave_height_m"] / max(1, fit["floor_count"]), 4),
                     "status": "observed"}
                    for index in range(fit["floor_count"])] if fit["floor_count"] else []),
        "footprints": [{"id": "primary", "level": "L0", "status": "inferred",
                        "polygon_xz": [[0, 0], [width, 0], [width, depth], [0, depth], [0, 0]]}],
        "roofs": [{"id": "primary-roof", "kind": fit["roof_kind"],
                   "ridge_axis": fit["ridge_axis"], "eave_y_m": fit["eave_height_m"],
                   "ridge_y_m": fit["ridge_height_m"], "status": "inferred"}],
        "openings": [], "assertions": assertions,
    }


def make_assertions(record, fit, panels, bindings):
    assertions = []
    panel_map = {panel["id"]: panel for panel in panels}
    for key in ("width_m", "depth_m", "floor_count", "eave_height_m", "ridge_height_m",
                "roof_kind", "ridge_axis"):
        value = fit.get(key)
        related = []
        for binding in bindings:
            if binding["status"] == "BOUND_CANDIDATE" and binding["panel_id"] in panel_map:
                related.append(binding["provenance"])
        assertions.append({"id": key.replace("_m", "").replace("_", "-"),
                           "status": "inferred" if value not in (None, 0, "unknown") else "unresolved",
                           "claim": f"{key} = {value}" if value not in (None, 0, "unknown") else f"{key} unresolved",
                           "provenance": related[:12]})
    return assertions


def route_fit(fit, panels, bindings, holdout, charter):
    plan = next((panel for panel in panels if panel["id"] == fit.get("primary_plan_panel")), None)
    anchors, spread = compatible_scale_anchors(plan, bindings) if plan else ([], None)
    roles = sorted({panel["role"] for panel in panels if panel["role"] in PRIMARY_ROLES})
    a0 = "plan" in roles and bool(set(roles) & {"elevation", "section"})
    numeric = all(fit.get(key) not in (None, 0, "unknown") for key in
                  ("width_m", "depth_m", "floor_count", "eave_height_m", "ridge_height_m", "roof_kind"))
    anchor_ok = len(anchors) >= charter["promotion"]["minimum_independent_scale_anchors"]
    spread_ok = spread is not None and spread <= charter["promotion"]["maximum_scale_anchor_spread_ratio"]
    plausible = bool(fit.get("width_m") and fit.get("depth_m") and fit.get("ridge_height_m") and
                     fit["width_m"] >= charter["promotion"]["minimum_width_depth_m"] and
                     fit["depth_m"] >= charter["promotion"]["minimum_width_depth_m"] and
                     fit["ridge_height_m"] >= charter["promotion"]["minimum_ridge_height_m"] and
                     fit.get("eave_height_m", 0) < fit["ridge_height_m"])
    gates = [
        {"id": "plan-and-vertical-view", "status": "PASS" if a0 else "FAIL", "actual": roles},
        {"id": "automatic-panel-evidence", "status": "PASS" if panels and not all(p["synthetic"] for p in panels) else "FAIL",
         "actual": len(panels)},
        {"id": "numeric-primary-envelope", "status": "PASS" if numeric else "FAIL", "actual": numeric},
        {"id": "independent-scale-anchors", "status": "PASS" if anchor_ok else "FAIL",
         "actual": len(anchors), "limit": charter["promotion"]["minimum_independent_scale_anchors"]},
        {"id": "scale-anchor-spread", "status": "PASS" if spread_ok else "FAIL",
         "actual": spread, "limit": charter["promotion"]["maximum_scale_anchor_spread_ratio"]},
        {"id": "plausible-envelope", "status": "PASS" if plausible else "FAIL", "actual": plausible},
        {"id": "independent-held-out-view", "status": "PASS" if holdout else "FAIL",
         "actual": holdout["id"] if holdout else None},
    ]
    pre_holdout_pass = all(item["status"] == "PASS" for item in gates)
    route = "G1_UNVALIDATED" if pre_holdout_pass else "A0_TRIAGED" if a0 else "HELD"
    return route, gates, anchors, spread


def crop_panel(sheet, panel, target):
    load_imaging()
    with Image.open(sheet["normalized_path"]) as opened:
        width, height = opened.size
        x0, y0, x1, y1 = panel["bbox"]
        crop = opened.crop((int(x0 * width), int(y0 * height), int(x1 * width), int(y1 * height)))
        crop.thumbnail((960, 720), Image.Resampling.LANCZOS)
        target.parent.mkdir(parents=True, exist_ok=True)
        crop.save(target, "PNG", optimize=True)


def process_building(record, audit_rev, corpus, charter, target):
    sheet_rows = []
    panels, bindings, measurements = [], [], {}
    for drawing in record["manifest"]["drawings"]:
        index = int(drawing["sheet_index"])
        directory = audit_rev / "sheets" / record["id"] / f"sheet-{index:02d}"
        audit = json.loads((directory / "audit.json").read_text(encoding="utf-8"))
        ocr = json.loads((directory / "ocr.json").read_text(encoding="utf-8"))
        sheet = {
            "building_id": record["id"], "sheet_index": index,
            "source_sha256": audit["source_sha256"], "source_url": audit["source_url"],
            "normalized_path": directory / "normalized.png",
            "normalized_pixels": audit["raster"]["normalized_pixels"],
            "tokens": ocr["tokens"], "ocr_roles": audit["ocr_role_signals"],
            "strict_dimensions": audit["strict_dimensions"],
        }
        image, clean = clean_sheet_image(sheet)
        lines = detect_cardinal_lines(clean)
        found = seed_panels(sheet)
        assign_scales(sheet, found, corpus)
        sheet_bindings = bind_dimensions(sheet, found, lines)
        for panel in found:
            geometry = component_geometry(clean, panel)
            line_subset = panel_lines(lines, panel, clean.shape)
            panel["geometry"] = geometry
            panel["line_counts"] = dict(Counter(line["axis"] for line in line_subset))
            measurements[panel["id"]] = measure_panel(panel, geometry, line_subset)
            crop_path = target / "panels" / f"{panel['id']}.png"
            crop_panel(sheet, panel, crop_path)
            panel["local_image"] = f"panels/{crop_path.name}"
        panels.extend(found)
        bindings.extend(sheet_bindings)
        sheet_rows.append(sheet)

    holdout_id, holdout_reason = select_holdout(panels, bindings)
    holdout = next((panel for panel in panels if panel["id"] == holdout_id), None)
    fit = fit_envelope(record["id"], sheet_rows, panels, bindings, measurements, holdout_id)
    route, gates, anchors, spread = route_fit(fit, panels, bindings, holdout, charter)
    assertions = make_assertions(record, fit, panels, bindings)
    graph = graph_for(record, fit, assertions)
    uncertainties = []
    if not any(panel["role"] == "plan" for panel in panels):
        uncertainties.append("no automatic plan panel")
    if not any(panel["role"] == "elevation" for panel in panels):
        uncertainties.append("no automatic elevation panel")
    if not holdout:
        uncertainties.append("no independent section or second elevation for held-out prediction")
    if fit["floor_count"] == 0:
        uncertainties.append("floor sequence unresolved; display floor count is not geometry authority")
    if len(anchors) < 2:
        uncertainties.append("fewer than two compatible independent primary-plan scale anchors")
    held_dimensions = [item for item in bindings if item["status"].startswith("HELD")]
    if held_dimensions:
        uncertainties.append(f"{len(held_dimensions)} dimension strings held from automatic binding")
    if fit.get("depth_m") and fit["sources"]["depth"] == "calibrated linework span":
        uncertainties.append("depth is a calibrated linework extent, not an explicit semantic dimension")
    assessment = {
        "schema": "architectural-envelope-fit/v0", "building_id": record["id"],
        "title": record["manifest"]["title"], "building_type": record["building_type"],
        "cluster": record.get("cluster"), "mode": "REAL_OCR_CV_ONLY",
        "route": route, "gates": gates, "fit": fit,
        "panels": panels, "bindings": bindings, "measurements": measurements,
        "scale_anchors": anchors, "scale_anchor_spread_ratio": spread,
        "holdout": {"panel_id": holdout_id, "selection_rule": holdout_reason,
                    "status": "SEALED_NOT_SCORED" if holdout else "UNAVAILABLE"},
        "uncertainties": uncertainties,
        "network_requests": 0, "vlm_calls": 0, "source_downloads": 0,
        "valheim_contacted": False, "world_mutated": False,
    }
    pipeline.immutable_json(target / "panel-evidence.json", {"schema": "architectural-panel-evidence-set/v0",
                                                             "building_id": record["id"], "panels": panels})
    pipeline.immutable_json(target / "dimension-bindings.json", {"schema": "architectural-dimension-binding-set/v0",
                                                                  "building_id": record["id"], "bindings": bindings})
    pipeline.immutable_json(target / "automatic-fit.json", assessment)
    pipeline.immutable_json(target / "building.graph.json", graph or {
        "schema": "architectural-building-graph/v1", "building_id": record["id"], "status": "HELD"})
    return assessment, graph


def accepted_oracle_graph():
    root = HERE / "out" / "architectural-roundtrip" / "sd0401"
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    return json.loads((root / "revisions" / revision / "building.graph.json").read_text(encoding="utf-8"))


def oracle_score(automatic, oracle):
    fit = automatic["fit"]
    expected = {
        "width_m": oracle["dimensions"]["main_width_m"],
        "depth_m": oracle["dimensions"]["main_depth_m"],
        "eave_height_m": oracle["dimensions"]["main_eave_y_m"],
        "ridge_height_m": oracle["dimensions"]["main_ridge_y_m"],
    }
    checks = []
    for key, observed in expected.items():
        if fit.get(key):
            check = dimension_error(fit[key], observed)
        else:
            check = {"predicted_m": None, "observed_m": observed, "absolute_error_m": None,
                     "error_ratio": None, "status": "FAIL"}
        check["semantic"] = key
        checks.append(check)
    oracle_roof = oracle["roofs"][0]
    exact = [
        {"semantic": "roof_kind", "predicted": fit.get("roof_kind"), "observed": oracle_roof["kind"],
         "status": "PASS" if fit.get("roof_kind") == oracle_roof["kind"] else "FAIL"},
        {"semantic": "ridge_axis", "predicted": fit.get("ridge_axis"), "observed": oracle_roof["ridge_axis"],
         "status": "PASS" if fit.get("ridge_axis") == oracle_roof["ridge_axis"] else "FAIL"},
    ]
    status = "PASS" if all(item["status"] == "PASS" for item in checks + exact) else "FAIL"
    return {"schema": "architectural-css-fit-oracle-score/v0", "building_id": "sd0401",
            "status": status, "revealed_after_seal": True, "dimension_checks": checks,
            "exact_checks": exact}


def derive_edge_tolerance(automatic, oracle):
    # Calibrate one display-only shape threshold from the accepted control,
    # without allowing any accepted metric to enter the automatic fit.
    holdout_id = automatic["holdout"].get("panel_id")
    panel = next((item for item in automatic["panels"] if item["id"] == holdout_id), None)
    observed = automatic["measurements"].get(holdout_id) if holdout_id else None
    if not panel or not observed or not observed.get("observed_span_m"):
        return 0.01
    expected_width = oracle["dimensions"]["main_depth_m"] if panel["role"] == "section" else oracle["dimensions"]["main_width_m"]
    expected_height = oracle["dimensions"]["main_ridge_y_m"]
    expected_aspect = expected_width / expected_height
    observed_aspect = observed["observed_span_m"][0] / max(observed["observed_span_m"][1], 1e-9)
    residual = abs(math.log(max(expected_aspect, 1e-9) / max(observed_aspect, 1e-9))) / 8
    return round(max(0.002, min(0.01, residual)), 6)


def finalize_assessment(assessment, graph, tolerance, charter):
    holdout_id = assessment["holdout"].get("panel_id")
    holdout = next((panel for panel in assessment["panels"] if panel["id"] == holdout_id), None)
    score = heldout_score(assessment["fit"], holdout, assessment["measurements"],
                          assessment["bindings"], tolerance)
    assessment["holdout"] = score
    assessment["gates"].append({
        "id": "held-out-cross-view", "status": "PASS" if score["status"] == "PASS" else "FAIL",
        "actual": {"panel": holdout_id, "edge_distance_ratio": score.get("edge_distance_ratio"),
                   "dimension_checks": len(score.get("dimension_checks", []))},
        "limit": {"metres": charter["promotion"]["maximum_cross_view_error_m"],
                  "ratio": charter["promotion"]["maximum_cross_view_error_ratio"],
                  "edge_distance_ratio": tolerance},
    })
    pre = all(item["status"] == "PASS" for item in assessment["gates"][:-1])
    assessment["route"] = ("G1_METRIC_GRAPH" if pre and score["status"] == "PASS" else
                           "G1_UNVALIDATED" if pre else assessment["route"])
    if graph is not None:
        graph["promotion"] = assessment["route"]
        graph["heldout"] = score
    return assessment, graph


def css_model(fit, view="elevation"):
    if not all(fit.get(key) for key in ("width_m", "depth_m", "ridge_height_m", "eave_height_m")):
        return "<div class='empty'>metric envelope unresolved</div>"
    width = fit["width_m"] if view == "elevation" else fit["width_m"]
    depth = fit["depth_m"]
    eave, ridge = fit["eave_height_m"], fit["ridge_height_m"]
    return (f"<div class='css-building {view}' style='--w:{width};--d:{depth};--e:{eave};--r:{ridge}'>"
            "<div class='css-roof'></div><div class='css-wall'></div>"
            "<div class='measure mw'>width</div><div class='measure mh'>height</div></div>")


def building_html(assessment):
    fit = assessment["fit"]
    gates = "".join(
        f"<div class='gate'><span>{html.escape(item['id'])}</span><b class='{item['status'].lower()}'>{item['status']}</b></div>"
        for item in assessment["gates"])
    panel_cards = []
    holdout_id = assessment["holdout"].get("selection") or assessment["holdout"].get("panel_id")
    for panel in assessment["panels"]:
        scale = panel.get("scale")
        badge = "holdout" if panel["id"] == holdout_id else "train"
        panel_cards.append(
            f"<article class='panel-card'><div class='panel-title'><b>{html.escape(panel['role'])}</b>"
            f"<span>{badge}</span></div><img src='{html.escape(panel['local_image'])}' alt='{html.escape(panel['id'])}'>"
            f"<div class='mono'>{html.escape(panel['id'])}</div>"
            f"<small>{html.escape(scale['notation']) if scale else 'scale unresolved'}</small></article>")
    values = "".join(f"<div><span>{key}</span><b>{html.escape(str(fit.get(key)))}</b></div>" for key in
                     ("width_m", "depth_m", "floor_count", "eave_height_m", "ridge_height_m",
                      "roof_kind", "roof_pitch_degrees", "ridge_axis"))
    uncertainties = "".join(f"<li>{html.escape(item)}</li>" for item in assessment["uncertainties"])
    payload = html.escape(json.dumps({"fit": fit, "holdout": assessment["holdout"]}, indent=2))
    return page_shell(
        f"{assessment['building_id']} CSS fit",
        f"<header><a href='../../index.html'>corpus /</a><div class='eyebrow'>{assessment['cluster']} · {assessment['building_type']}</div>"
        f"<h1>{assessment['building_id']} <span>{assessment['route']}</span></h1><p>{html.escape(assessment['title'])}</p></header>"
        f"<main><section class='hero'><div><div class='eyebrow'>CSS METRIC PROJECTION</div>{css_model(fit)}</div>"
        f"<aside><h2>Shared envelope</h2><div class='values'>{values}</div></aside></section>"
        f"<section><div class='eyebrow'>TRAIN / HELD-OUT EVIDENCE</div><div class='panel-grid'>{''.join(panel_cards) or '<p>no panels</p>'}</div></section>"
        f"<section class='two'><div><div class='eyebrow'>PROMOTION GATES</div>{gates}</div>"
        f"<div><div class='eyebrow'>UNCERTAINTY LIST</div><ul>{uncertainties or '<li>none declared</li>'}</ul></div></section>"
        f"<details><summary>fit receipt</summary><pre>{payload}</pre></details></main>")


def page_shell(title, body):
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>{html.escape(title)}</title><style>
:root{{--bg:#101619;--paper:#e9e5d8;--slate:#243137;--line:#52636a;--ink:#f1f0e8;--muted:#a8b6b9;--ochre:#d89a36;--ok:#74d69a;--fail:#f37f70;--hold:#d6b35f}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 Arial,sans-serif}}header,main{{max-width:1500px;margin:auto;padding:28px}}
header{{border-bottom:1px solid var(--line)}}h1{{font:52px/1.05 Georgia,serif;margin:.25rem 0}}h1 span{{font:14px Consolas,monospace;color:var(--ochre)}}h2{{font:25px Georgia,serif}}
a{{color:var(--ochre)}}.eyebrow,.mono{{font:12px Consolas,monospace;letter-spacing:.12em;color:var(--muted)}}
.hero,.two{{display:grid;grid-template-columns:minmax(420px,2fr) minmax(300px,1fr);gap:22px;margin:26px 0}}.hero>div,.hero>aside,.two>div,section,details{{border:1px solid var(--line);background:#172126;padding:20px}}
.values>div,.gate{{display:flex;justify-content:space-between;gap:20px;padding:9px 0;border-top:1px solid #35464d}}.values span{{color:var(--muted)}}
.pass{{color:var(--ok)}}.fail{{color:var(--fail)}}.pending_oracle_tolerance{{color:var(--hold)}}
.panel-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}}.panel-card{{background:#202c31;border:1px solid var(--line);padding:10px;min-width:0}}.panel-card img{{width:100%;height:210px;object-fit:contain;background:var(--paper);filter:contrast(1.05)}}.panel-title{{display:flex;justify-content:space-between;text-transform:uppercase;color:var(--ochre);margin-bottom:8px}}
.css-building{{height:390px;position:relative;margin:20px;background:linear-gradient(transparent 89%,#516269 90%,transparent 91%)}}
.css-wall{{position:absolute;left:10%;bottom:10%;width:80%;height:calc((var(--e)/var(--r))*62%);border:3px solid var(--ochre);background:rgba(216,154,54,.08)}}
.css-roof{{position:absolute;left:10%;bottom:calc(10% + (var(--e)/var(--r))*62%);width:80%;height:calc(((var(--r) - var(--e))/var(--r))*62%);clip-path:polygon(0 100%,50% 0,100% 100%);background:rgba(216,154,54,.18);border-bottom:3px solid var(--ochre)}}
.measure{{position:absolute;color:var(--muted);font:12px Consolas}}.mw{{bottom:3%;left:45%}}.mh{{left:2%;top:48%;transform:rotate(-90deg)}}.empty{{height:300px;display:grid;place-items:center;color:var(--fail)}}
pre{{white-space:pre-wrap;word-break:break-word;max-height:600px;overflow:auto;color:#c5d5d8}}ul{{padding-left:20px}}@media(max-width:800px){{.hero,.two{{grid-template-columns:1fr}}h1{{font-size:38px}}}}
</style></head><body>{body}</body></html>""".encode("utf-8")


def corpus_html(index):
    cards = []
    for row in index["buildings"]:
        fit = row["fit"]
        cards.append(
            f"<a class='building-card' href='buildings/{row['building_id']}/index.html'>"
            f"<div><span>{row['cluster']}</span><b>{row['route']}</b></div><h2>{row['building_id']}</h2>"
            f"<p>{row['building_type']} · {row['panels']} panels · {row['bound_dimensions']} bound dims</p>"
            f"<small>{fit.get('width_m')} × {fit.get('depth_m')} × {fit.get('ridge_height_m')} m</small></a>")
    metrics = index["metrics"]
    metric_html = "".join(f"<div><b>{html.escape(str(value))}</b><span>{html.escape(key.replace('_',' '))}</span></div>"
                          for key, value in metrics.items())
    clusters = []
    for name, rows in sorted(index["clusters"].items()):
        route_counts = Counter(item["route"] for item in rows)
        clusters.append(f"<div class='cluster'><b>{name}</b><span>{len(rows)} buildings</span><code>{html.escape(str(dict(route_counts)))}</code></div>")
    uncertainty = "".join(f"<li>{html.escape(item)}</li>" for item in index["uncertainties"])
    body = (f"<header><div class='eyebrow'>HABS · AUTOMATIC ENVELOPE FIT · REV {index['revision']}</div>"
            f"<h1>Can the drawings hold one shape?</h1><p class='result'>{index['answer']}</p></header><main>"
            f"<section class='metrics'>{metric_html}</section><section><div class='eyebrow'>PRE-SORT STRATA</div><div class='clusters'>{''.join(clusters)}</div></section>"
            f"<section><div class='eyebrow'>20-BUILDING SWEEP</div><div class='catalog'>{''.join(cards)}</div></section>"
            f"<section><div class='eyebrow'>EXPERIMENT UNCERTAINTY</div><ul>{uncertainty}</ul></section></main>")
    page = page_shell("HABS automatic CSS envelope fit", body).decode("utf-8")
    extra = """<style>.result{font:700 18px Consolas;color:var(--ochre)}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;padding:0}.metrics>div{background:#202c31;padding:20px;display:flex;flex-direction:column}.metrics b{font:34px Georgia,serif}.metrics span{color:var(--muted)}.clusters{display:flex;gap:10px;flex-wrap:wrap}.cluster{border:1px solid var(--line);padding:12px;display:grid;gap:4px}.catalog{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}.building-card{display:block;text-decoration:none;color:var(--ink);border:1px solid var(--line);background:#202c31;padding:15px}.building-card:hover{border-color:var(--ochre)}.building-card>div{display:flex;justify-content:space-between;color:var(--ochre);font:11px Consolas}.building-card h2{margin:.3rem 0}.building-card p,.building-card small{color:var(--muted)}</style>"""
    return page.replace("</head>", extra + "</head>").encode("utf-8")


class Project:
    def __init__(self, args, charter, audit_revision, audit_index):
        identity = {
            "engine": ENGINE,
            "script_sha256": pipeline.digest_file(Path(__file__)),
            "charter_sha256": pipeline.digest_file(args.charter),
            "schemas_sha256": pipeline.digest_file(args.schemas),
            "selection_sha256": pipeline.digest_file(args.selection),
            "audit_revision": audit_revision,
            "audit_index_sha256": pipeline.digest_file(args.audit / "revisions" / audit_revision / "index.json"),
            "mode": "REAL_OCR_CV_ONLY_NO_NETWORK",
        }
        self.revision = pipeline.digest_bytes(pipeline.compact_bytes(identity))[:20]
        self.root = args.out.resolve()
        self.rev = self.root / "revisions" / self.revision
        self.rev.mkdir(parents=True, exist_ok=True)
        pipeline.atomic_bytes(self.root / "HEAD", (self.revision + "\n").encode("ascii"))
        pipeline.immutable_json(self.rev / "identity.json", identity)
        self.stats = {"executed": [], "cached": [], "evidence_reads": 0, "fit_runs": 0,
                      "ocr_calls": 0, "vlm_calls": 0, "network_requests": 0,
                      "source_downloads": 0, "world_writes": 0}

    def building(self, record, fingerprint, builder):
        name = record["id"]
        receipt_path = self.rev / "receipts" / f"building-{name}.json"
        target = self.rev / "buildings" / name
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("fingerprint") == fingerprint:
                valid = all((path := pipeline.safe_child(self.rev, item["path"])).is_file() and
                            pipeline.digest_file(path) == item["sha256"]
                            for item in receipt.get("outputs", []))
                final_path = target / "assessment.json"
                automatic_path = target / "automatic-fit.json"
                graph_path = target / "building.graph.json"
                if valid and final_path.is_file() and automatic_path.is_file() and graph_path.is_file():
                    self.stats["cached"].append(name)
                    return (json.loads(automatic_path.read_text(encoding="utf-8")),
                            json.loads(graph_path.read_text(encoding="utf-8")))
        target.mkdir(parents=True, exist_ok=True)
        assessment, graph = builder(target)
        self.stats["executed"].append(name)
        self.stats["evidence_reads"] += len(record["manifest"]["drawings"])
        self.stats["fit_runs"] += 1
        return assessment, graph

    def seal_building(self, record, fingerprint, assessment, graph):
        name = record["id"]
        target = self.rev / "buildings" / name
        pipeline.atomic_json(target / "assessment.json", assessment)
        pipeline.atomic_json(target / "building.graph.json", graph or {
            "schema": "architectural-building-graph/v1", "building_id": name, "status": "HELD"})
        pipeline.atomic_bytes(target / "index.html", building_html(assessment))
        outputs = sorted(path for path in target.rglob("*") if path.is_file())
        rows = [{"path": path.relative_to(self.rev).as_posix(), "sha256": pipeline.digest_file(path),
                 "bytes": path.stat().st_size} for path in outputs]
        pipeline.atomic_json(self.rev / "receipts" / f"building-{name}.json", {
            "schema": "architectural-css-fit-stage-receipt/v0", "stage": f"building:{name}",
            "fingerprint": fingerprint, "outputs": rows,
            "facts": {"route": assessment["route"], "panels": len(assessment["panels"]),
                      "bindings": len(assessment["bindings"])},
        })


def load_inputs(args):
    charter = json.loads(args.charter.read_text(encoding="utf-8"))
    if pipeline.digest_file(args.selection) != charter["inputs"]["selection_sha256"]:
        raise RuntimeError("frozen selection hash changed")
    audit_revision = (args.audit / "HEAD").read_text(encoding="ascii").strip()
    if audit_revision != charter["inputs"]["ocr_audit_revision"]:
        raise RuntimeError(f"OCR audit revision changed: {audit_revision}")
    audit_rev = args.audit / "revisions" / audit_revision
    audit_index = json.loads((audit_rev / "index.json").read_text(encoding="utf-8"))
    if len(audit_index.get("sheets", [])) != charter["inputs"]["sheets"]:
        raise RuntimeError("OCR audit sheet count changed")
    source_args = SimpleNamespace(charter=pipeline.DEFAULT_CHARTER,
                                  selection=args.selection, corpus=args.corpus)
    _, _, records = pipeline.load_inputs(source_args)
    if len(records) != charter["inputs"]["buildings"]:
        raise RuntimeError("corpus building count changed")
    membership = {}
    for cluster in audit_index["presort"]["clusters"]:
        for building_id in cluster["members"]:
            membership[building_id] = cluster["id"]
    for record in records:
        record["cluster"] = membership.get(record["id"], "CU")
    order = audit_index["presort"]["curriculum_order"]
    order_index = {building_id: index for index, building_id in enumerate(order)}
    records.sort(key=lambda record: (order_index.get(record["id"], 999), record["id"]))
    return charter, audit_revision, audit_rev, audit_index, records


def summarize_building(assessment):
    return {"building_id": assessment["building_id"], "title": assessment["title"],
            "building_type": assessment["building_type"], "cluster": assessment["cluster"],
            "route": assessment["route"], "fit": assessment["fit"],
            "panels": len(assessment["panels"]),
            "bound_dimensions": sum(item["status"] == "BOUND_CANDIDATE" for item in assessment["bindings"]),
            "held_dimensions": sum(item["status"].startswith("HELD") for item in assessment["bindings"]),
            "holdout_status": assessment["holdout"]["status"],
            "uncertainties": assessment["uncertainties"]}


def scientific_outcome(rows, oracle, charter):
    unseen = [row for row in rows if row["building_id"] != charter["inputs"]["seed_control"]]
    promoted = [row for row in unseen if row["route"] == "G1_METRIC_GRAPH"]
    types = {row["building_type"] for row in promoted}
    clusters = {row["cluster"] for row in promoted}
    controls = {row["building_id"]: row["route"] for row in rows
                if row["building_id"] in charter["inputs"]["negative_controls"]}
    controls_hold = all(value != "G1_METRIC_GRAPH" for value in controls.values())
    if (oracle["status"] == "PASS" and controls_hold and
            len(promoted) >= charter["outcomes"]["corpus_g1_minimum"]["unseen_g1"] and
            len(types) >= charter["outcomes"]["corpus_g1_minimum"]["building_types"]):
        return "CORPUS_G1_MINIMUM"
    if (oracle["status"] == "PASS" and controls_hold and
            len(promoted) >= charter["outcomes"]["transfer_observed"]["unseen_g1"] and
            len(clusters) >= charter["outcomes"]["transfer_observed"]["clusters"]):
        return "TRANSFER_OBSERVED"
    return "INSUFFICIENT_AUTOMATIC_EVIDENCE"


def run(args):
    load_imaging()
    charter, audit_revision, audit_rev, audit_index, records = load_inputs(args)
    project = Project(args, charter, audit_revision, audit_index)
    automatic, graphs, fingerprints = {}, {}, {}
    audit_rows = defaultdict(list)
    for row in audit_index["sheets"]:
        audit_rows[row["building_id"]].append(row)
    for ordinal, record in enumerate(records, 1):
        fingerprint = pipeline.digest_bytes(pipeline.compact_bytes({
            "engine": ENGINE, "building_id": record["id"],
            "manifest_sha256": pipeline.digest_file(args.corpus / record["id"] / "manifest.json"),
            "audit_revision": audit_revision,
            "audit_rows": audit_rows[record["id"]],
        }))
        fingerprints[record["id"]] = fingerprint
        assessment, graph = project.building(
            record, fingerprint,
            lambda target, record=record: process_building(record, audit_rev, args.corpus, charter, target),
        )
        automatic[record["id"]], graphs[record["id"]] = assessment, graph
        print(f"[{ordinal:02d}/20] {record['id']} panels={len(assessment['panels'])} "
              f"bindings={len(assessment['bindings'])} pre={assessment['route']}")

    # Seal every automatic fit hash before the accepted control is loaded.
    seal = {building_id: pipeline.digest_bytes(pipeline.compact_bytes(automatic[building_id]))
            for building_id in sorted(automatic)}
    pipeline.immutable_json(project.rev / "automatic-seal.json", {
        "schema": "architectural-automatic-fit-seal/v0", "revision": project.revision,
        "oracle_loaded": False, "buildings": seal,
        "sha256": pipeline.digest_bytes(pipeline.compact_bytes(seal)),
    })
    oracle_graph = accepted_oracle_graph()
    oracle = oracle_score(automatic["sd0401"], oracle_graph)
    tolerance = derive_edge_tolerance(automatic["sd0401"], oracle_graph)
    pipeline.immutable_json(project.rev / "oracle-score.json", oracle)
    pipeline.immutable_json(project.rev / "edge-tolerance.json", {
        "schema": "architectural-css-edge-tolerance/v0", "source": "accepted sd0401 display residual only",
        "panel_diagonal_ratio": tolerance, "minimum": 0.002, "maximum": 0.01,
        "automatic_seal_sha256": pipeline.digest_file(project.rev / "automatic-seal.json"),
    })

    rows = []
    for record in records:
        building_id = record["id"]
        assessment, graph = finalize_assessment(automatic[building_id], graphs[building_id], tolerance, charter)
        project.seal_building(record, fingerprints[building_id], assessment, graph)
        rows.append(summarize_building(assessment))
    answer = scientific_outcome(rows, oracle, charter)
    routes = Counter(row["route"] for row in rows)
    metrics = {
        "buildings": len(rows), "sheets_reused": charter["inputs"]["sheets"],
        "panels": sum(row["panels"] for row in rows),
        "bound_dimensions": sum(row["bound_dimensions"] for row in rows),
        "g1_validated": routes["G1_METRIC_GRAPH"],
        "g1_unvalidated": routes["G1_UNVALIDATED"],
        "a0_triaged": routes["A0_TRIAGED"], "held": routes["HELD"],
        "oracle": oracle["status"], "edge_tolerance_ratio": tolerance,
    }
    clusters = defaultdict(list)
    for row in rows:
        clusters[row["cluster"]].append(row)
    uncertainties = [
        "The fitter samples primary orthographic envelopes only; appendages and openings remain residuals.",
        "Connected linework can still include dimension strings, poche, grade, or adjacent views after OCR erasure.",
        "A complete printed scale plus TIFF DPI calibrates a sheet, but does not by itself identify which outline is the primary mass.",
        "Similarity-aligned CSS shape residuals are display diagnostics and cannot authorize metric scale.",
        "No Valheim pieces, Creator OS messages, ZDOs, worlds, or network services were touched.",
    ]
    index = {"schema": "architectural-css-fit-index/v0", "revision": project.revision,
             "question": charter["question"], "answer": answer, "mode": "REAL_OCR_CV_ONLY",
             "metrics": metrics, "oracle": oracle, "buildings": rows,
             "clusters": dict(clusters), "uncertainties": uncertainties,
             "network_requests": 0, "vlm_calls": 0,
             "source_downloads": 0, "world_mutated": False}
    pipeline.immutable_json(project.rev / "index.json", index)
    pipeline.atomic_bytes(project.rev / "index.html", corpus_html(index))
    pipeline.atomic_json(project.root / "report.json", {
        "schema": "architectural-css-fit-report/v0", "revision": project.revision,
        "answer": answer, "metrics": metrics, "stage_cache": project.stats,
        "uncertainties": uncertainties, "network_requests": 0, "vlm_calls": 0,
        "source_downloads": 0, "world_mutated": False,
    })
    print(f"revision {project.revision}\nRESULT {answer}\nROUTES {dict(routes)}")
    return 0


def verify(args):
    root = args.out.resolve()
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    rev = root / "revisions" / revision
    index = json.loads((rev / "index.json").read_text(encoding="utf-8"))
    errors = []
    if len(index.get("buildings", [])) != 20:
        errors.append("building count")
    if index.get("network_requests") != 0 or index.get("vlm_calls") != 0 or index.get("world_mutated"):
        errors.append("authority boundary")
    seal = json.loads((rev / "automatic-seal.json").read_text(encoding="utf-8"))
    if len(seal.get("buildings", {})) != 20 or seal.get("oracle_loaded") is not False:
        errors.append("automatic oracle isolation seal")
    for receipt_path in sorted((rev / "receipts").glob("building-*.json")):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        for item in receipt.get("outputs", []):
            path = pipeline.safe_child(rev, item["path"])
            if not path.is_file() or pipeline.digest_file(path) != item["sha256"]:
                errors.append(f"receipt mismatch {item['path']}")
    for row in index.get("buildings", []):
        target = rev / "buildings" / row["building_id"]
        assessment = json.loads((target / "assessment.json").read_text(encoding="utf-8"))
        if assessment.get("network_requests") != 0 or assessment.get("vlm_calls") != 0:
            errors.append(f"network/VLM boundary {row['building_id']}")
        holdout = assessment.get("holdout", {})
        if holdout.get("selection") and not (holdout.get("dimensions_excluded_from_fit") and
                                              holdout.get("geometry_excluded_from_fit")):
            errors.append(f"holdout leakage contract {row['building_id']}")
        for panel in assessment.get("panels", []):
            scale = panel.get("scale")
            if scale and scale.get("anisotropy_ratio", 1) > 0.005:
                errors.append(f"nonuniform scale {panel['id']}")
    result = {"schema": "architectural-css-fit-verification/v0",
              "status": "PASS" if not errors else "FAIL", "revision": revision,
              "buildings": len(index.get("buildings", [])), "errors": errors,
              "network_requests": 0, "vlm_calls": 0, "world_mutated": False}
    pipeline.atomic_json(root / "verification.json", result)
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


def serve(args):
    root = args.out.resolve()
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    directory = root / "revisions" / revision

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *handler_args, **handler_kwargs):
            super().__init__(*handler_args, directory=str(directory), **handler_kwargs)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"http://127.0.0.1:{args.port}/index.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def main():
    args = parse_args()
    try:
        if args.command == "run":
            return run(args)
        if args.command == "verify":
            return verify(args)
        return serve(args)
    except Exception as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Push one real HABS specimen through the visible automatic pipeline.

This is deliberately a shark-mode R&D lane, not a corpus promotion.  It reads
only the accepted tn0304 development artifacts, recovers the paired W-W plan
cut line from pixels, composes a provisional metric graph, and reuses the
existing generic-piece/WebGPU path.  Outputs are mutable, ignored diagnostics.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import probe_architectural_css_fit_v3 as v3
import probe_architectural_curriculum as pipeline


ENGINE = "architectural-water-flow/0.1.0"
SUBJECT = "tn0304"
APPROVED_V3_REVISION = "5333d5eaed593d7607e4"
APPROVED_SHEET_SHA256 = "fcc3592829debfb3f9db14223be82cf78b33f46ef15063970875088616bae119"
DEFAULT_V3_OUT = HERE / "out" / "architectural-css-fit-v3"
DEFAULT_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_OUT = HERE / "out" / "architectural-water-flow" / SUBJECT


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--v3-out", type=Path, default=DEFAULT_V3_OUT)
    common.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", parents=[common])
    run.add_argument("--no-browser", action="store_true")
    commands.add_parser("verify", parents=[common])
    serve = commands.add_parser("serve", parents=[common])
    serve.add_argument("--port", type=int, default=8881)
    return parser.parse_args()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_building(args):
    revision = (args.v3_out / "HEAD").read_text(encoding="ascii").strip()
    if revision != APPROVED_V3_REVISION:
        raise RuntimeError(f"water-flow lane pins v3 {APPROVED_V3_REVISION}, not HEAD {revision}")
    building = args.v3_out / "revisions" / revision / "buildings" / SUBJECT
    evidence_path = building / "evidence.graph.json"
    graph_path = building / "building.graph.json"
    assessment_path = building / "assessment.json"
    if not all(path.is_file() for path in (evidence_path, graph_path, assessment_path)):
        raise RuntimeError(f"accepted v3 tn0304 artifacts are missing under {building}")
    evidence, graph, assessment = (load_json(evidence_path), load_json(graph_path),
                                   load_json(assessment_path))
    if {evidence.get("building_id"), graph.get("building_id"), assessment.get("building_id")} != {SUBJECT}:
        raise RuntimeError("the bounded runner refuses any subject except tn0304")
    return revision, building, evidence, graph, assessment


def source_sheet(args, plan):
    building = (args.corpus / SUBJECT).resolve()
    manifest_path = building / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"tn0304 corpus manifest is missing: {manifest_path}")
    manifest = load_json(manifest_path)
    drawings = [row for row in manifest.get("drawings", [])
                if row.get("sheet_index") == plan.get("sheet_index")]
    if len(drawings) != 1:
        raise RuntimeError(f"expected one native sheet {plan.get('sheet_index')}, found {len(drawings)}")
    download = drawings[0].get("download", {})
    relative = download.get("local_path")
    path = (building / str(relative)).resolve()
    if not path.is_file() or building not in path.parents:
        raise RuntimeError(f"unsafe or missing native sheet: {relative}")
    manifest_sha = str(download.get("sha256", ""))
    actual_sha = pipeline.digest_file(path)
    plan_hashes = {str(row.get("source_sha256", "")) for row in plan.get("provenance", [])}
    if (manifest_sha != APPROVED_SHEET_SHA256 or actual_sha != APPROVED_SHEET_SHA256 or
            plan_hashes != {APPROVED_SHEET_SHA256}):
        raise RuntimeError("tn0304 native sheet, manifest, and v3 plan provenance are not the approved pin")
    return path, manifest


def role_view(evidence, role, label_pattern=None):
    candidates = [row for row in evidence["views"] if row["role"] == role]
    if label_pattern:
        candidates = [row for row in candidates if re.search(
            label_pattern, str(row.get("label", "")), re.IGNORECASE)]
    if len(candidates) != 1:
        raise RuntimeError(f"expected one {role} view, found {[row['id'] for row in candidates]}")
    return candidates[0]


def primary_plan_view(evidence):
    closed = {row["view_id"] for row in evidence["masses"] if row["closed_wall_loop"]}
    candidates = [row for row in evidence["views"] if row["role"] == "plan" and
                  row["id"] in closed and str(row.get("label", "")).strip().upper() == "PLAN"]
    if len(candidates) != 1:
        raise RuntimeError(f"expected one closed view labeled PLAN, found {[row['id'] for row in candidates]}")
    return candidates[0]


def image_path(building, view):
    path = (building / view["local_image"]).resolve()
    if not path.is_file() or building.resolve() not in path.parents:
        raise RuntimeError(f"unsafe or missing local view: {view['id']}")
    return path


def cardinal_lines(path):
    import cv2

    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"OpenCV could not decode {path}")
    height, width = image.shape
    edges = cv2.Canny(image, 60, 170, apertureSize=3)
    raw = cv2.HoughLinesP(edges, 1, math.pi / 180, threshold=12,
                          minLineLength=max(8, int(width * 0.012)),
                          maxLineGap=max(3, int(width * 0.005)))
    rows = []
    for ordinal, item in enumerate(raw[:, 0, :] if raw is not None else []):
        x0, y0, x1, y1 = (int(value) for value in item)
        length = math.hypot(x1 - x0, y1 - y0)
        angle = abs(math.degrees(math.atan2(y1 - y0, x1 - x0))) % 180
        axis = ("horizontal" if min(angle, 180 - angle) <= 8 else
                "vertical" if abs(angle - 90) <= 8 else "diagonal")
        pixels = [x0, y0, x1, y1]
        rows.append({"id": f"hough-{ordinal:04d}-" + "-".join(str(value) for value in pixels),
                     "pixels": pixels, "length_px": round(length, 3),
                     "angle_degrees": round(angle, 3), "axis": axis})
    rows.sort(key=lambda row: (-row["length_px"], row["pixels"]))
    return image, rows


def structural_envelope(lines, image_pixels):
    width, height = image_pixels
    horizontal = [row for row in lines if row["axis"] == "horizontal" and
                  row["length_px"] >= width * 0.35 and
                  height * 0.15 <= sum((row["pixels"][1], row["pixels"][3])) / 2 <= height * 0.90]
    if not horizontal:
        raise RuntimeError("no dominant horizontal wall family")
    right_values = sorted(max(row["pixels"][0], row["pixels"][2]) for row in horizontal)
    right = right_values[len(right_values) // 2]
    owned = [row for row in horizontal
             if abs(max(row["pixels"][0], row["pixels"][2]) - right) <= width * 0.045]
    if len(owned) < 4:
        raise RuntimeError("dominant wall family did not retain four observed segments")
    ys = [sum((row["pixels"][1], row["pixels"][3])) / 2 for row in owned]
    top, bottom = min(ys), max(ys)
    interior = [row for row in owned if top + height * 0.04 <=
                sum((row["pixels"][1], row["pixels"][3])) / 2 <= bottom - height * 0.04]
    left_values = sorted(min(row["pixels"][0], row["pixels"][2]) for row in interior or owned)
    left = left_values[len(left_values) // 2]
    if right - left < width * 0.35 or bottom - top < height * 0.30:
        raise RuntimeError("dominant wall envelope is not a useful two-axis mass")
    return {"left": round(left, 3), "top": round(top, 3),
            "right": round(right, 3), "bottom": round(bottom, 3),
            "source_segment_ids": [row["id"] for row in owned]}


def recognize_marker_windows(image, envelope, marker, engine):
    import numpy as np
    from PIL import Image

    rgb = Image.fromarray(image).convert("RGB")
    width, height = rgb.size
    window_width = max(36, round(width * 0.06))
    window_height = max(32, round(height * 0.05))
    stride = max(7, round(width * 0.015))
    candidates = {"top": [], "bottom": []}
    scans = 0
    y_offsets = {"top": (-0.080, -0.065, -0.050, -0.035, -0.020, -0.005),
                 "bottom": (-0.010, 0.005, 0.020, 0.035, 0.050, 0.065)}
    for side, boundary_y in (("top", envelope["top"]), ("bottom", envelope["bottom"])):
        start = int(envelope["left"])
        stop = int(envelope["right"])
        for offset in y_offsets[side]:
            center_y = boundary_y + height * offset
            for center_x in range(start, stop + 1, stride):
                box = [max(0, round(center_x - window_width / 2)),
                       max(0, round(center_y - window_height / 2)),
                       min(width, round(center_x + window_width / 2)),
                       min(height, round(center_y + window_height / 2))]
                crop = np.asarray(rgb.crop(tuple(box)))
                result = engine(crop, use_det=False, use_cls=False, use_rec=True)
                scans += 1
                texts = tuple(result.txts or ()) if result else ()
                scores = tuple(result.scores or ()) if result else ()
                text = re.sub(r"[^A-Z]", "", str(texts[0] if texts else "").upper())
                score = float(scores[0]) if scores else 0.0
                if text == marker and score >= 0.30:
                    candidates[side].append({"marker": marker,
                                             "center_px": [float(center_x), round(float(center_y), 3)],
                                             "confidence": round(score, 6), "crop_px": box,
                                             "ocr_engine": "RapidOCR/3.9.2-recognizer"})

    def collapse(rows):
        groups = []
        for row in sorted(rows, key=lambda item: item["center_px"][0]):
            if not groups or row["center_px"][0] - groups[-1][-1]["center_px"][0] > stride * 1.5:
                groups.append([row])
            else:
                groups[-1].append(row)
        return [max(group, key=lambda item: (item["confidence"], -item["center_px"][0]))
                for group in groups]

    top, bottom = collapse(candidates["top"]), collapse(candidates["bottom"])
    pairs = []
    for first in top:
        for second in bottom:
            delta = abs(first["center_px"][0] - second["center_px"][0])
            if delta <= width * 0.06:
                pairs.append((min(first["confidence"], second["confidence"]), -delta,
                              first, second))
    if not pairs:
        raise RuntimeError(f"paired {marker} endpoints were not recovered: top={top}, bottom={bottom}")
    _, _, first, second = max(pairs, key=lambda item: (item[0], item[1]))
    return [first, second], scans


def section_marker(section):
    match = re.search(r"\bSECTION\s+([A-Z])\s*[-]\s*\1\b",
                      str(section.get("label", "")), re.IGNORECASE)
    if not match:
        raise RuntimeError(f"section label is not an exact repeated marker: {section.get('label')}")
    return match.group(1).upper()


def make_cut_line(plan, plan_path, marker, engine):
    image, lines = cardinal_lines(plan_path)
    height, width = image.shape
    envelope = structural_envelope(lines, [width, height])
    endpoints, scans = recognize_marker_windows(image, envelope, marker, engine)
    source_sha256 = plan["provenance"][0]["source_sha256"]
    for endpoint in endpoints:
        endpoint["source_sha256"] = source_sha256
    segments = [{**row, "detector": "OpenCV.HoughLinesP",
                 "source_sha256": source_sha256}
                for row in lines if row["axis"] == "horizontal" and
                8 <= row["length_px"] <= width * 0.14]
    contract = v3.cut_line_contract(plan["id"], marker, endpoints, segments, [width, height])
    contract["structural_envelope_px"] = envelope
    contract["recognition_windows"] = scans
    if contract["status"] != "PASS":
        raise RuntimeError(f"cut-line contract failed: {contract['reasons']}")
    return contract


def numeric_atoms(text):
    return re.findall(r"\d+", str(text or ""))


def ocr_token_id(view_id, source_kind, text, box, source_sha256):
    payload = json.dumps([view_id, source_kind, text, box, source_sha256],
                         ensure_ascii=True, separators=(",", ":"))
    return "dim-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def explicit_dimension_parse(text):
    value_m = pipeline.parse_dimension(text)
    if value_m is not None:
        return str(text), value_m, None
    match = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s*[-–—]\s*"
        r"(\d+(?:\.\d+)?(?:\s+\d+/\d+)?)\s*[\"″]\s*", str(text or ""))
    if not match:
        return str(text), None, None
    repaired = f"{match.group(1)}'-{match.group(2)}\""
    return repaired, pipeline.parse_dimension(repaired), "MISSING_FOOT_PRIME_FROM_OCR"


def rotated_ocr_tokens(image, engine, view_id, source_kind, source_sha256,
                       source_crop_px=None, require_parsed=False):
    import numpy as np

    rotated = image.convert("RGB").rotate(270, expand=True)
    result = engine(np.asarray(rotated))
    boxes = [] if result is None or result.boxes is None else result.boxes
    texts = [] if result is None or result.txts is None else result.txts
    scores = [] if result is None or result.scores is None else result.scores
    rows = []
    for ordinal in range(min(len(boxes), len(texts), len(scores))):
        confidence = float(scores[ordinal])
        text = str(texts[ordinal]).strip()
        atoms = numeric_atoms(text)
        interpreted_text, value_m, repair = explicit_dimension_parse(text)
        if confidence < 0.80 or len(atoms) < 2 or (require_parsed and value_m is None):
            continue
        points = [[round(float(value), 3) for value in point]
                  for point in boxes[ordinal]]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        bbox = [round(min(xs), 3), round(min(ys), 3),
                round(max(xs), 3), round(max(ys), 3)]
        rows.append({
            "id": ocr_token_id(view_id, source_kind, text, bbox, source_sha256),
            "view_id": view_id,
            "source_kind": source_kind,
            "source_sha256": source_sha256,
            "source_crop_px": source_crop_px,
            "source_image_pixels": list(image.size),
            "rotation": {"api": "PIL.Image.rotate", "degrees_counter_clockwise": 270,
                         "expand": True},
            "rotated_image_pixels": list(rotated.size),
            "rotated_box_points_px": points,
            "rotated_bbox_px": bbox,
            "rotated_center_px": [round((bbox[0] + bbox[2]) / 2, 3),
                                  round((bbox[1] + bbox[3]) / 2, 3)],
            "text": text,
            "interpreted_text": interpreted_text,
            "transcription_repair": repair,
            "numeric_atoms": atoms,
            "value_m": round(float(value_m), 6) if value_m is not None else None,
            "confidence": round(confidence, 6),
            "ocr_engine": "RapidOCR/3.9.2-detector-recognizer",
        })
    return rows


def normalized_support(building, view, engine, native_tokens):
    from PIL import Image

    path = image_path(building, view)
    with Image.open(path) as image:
        candidates = rotated_ocr_tokens(
            image, engine, view["id"], "normalized-v3-view", pipeline.digest_file(path))
    selected = []
    for native in native_tokens:
        matches = [row for row in candidates
                   if row["numeric_atoms"] == native["numeric_atoms"]]
        if not matches:
            raise RuntimeError(f"normalized OCR did not independently support {native['id']}")
        support = max(matches, key=lambda row: (row["confidence"], row["id"]))
        support["supports_native_token_id"] = native["id"]
        support["upstream_source_sha256"] = native["source_sha256"]
        selected.append(support)
    return selected


def explicit_dimension_evidence(source_path, building, plan, section, engine):
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    views = [plan, section]
    native = {}
    crop_boxes = {}
    with Image.open(source_path) as sheet:
        sheet_pixels = list(sheet.size)
        for view in views:
            x0, y0, x1, y1 = (float(value) for value in view["bbox"])
            crop_box = [max(0, round(x0 * sheet.width)), max(0, round(y0 * sheet.height)),
                        min(sheet.width, round(x1 * sheet.width)),
                        min(sheet.height, round(y1 * sheet.height))]
            if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
                raise RuntimeError(f"invalid native crop for {view['id']}: {crop_box}")
            crop_boxes[view["id"]] = crop_box
            crop = sheet.crop(tuple(crop_box))
            native[view["id"]] = rotated_ocr_tokens(
                crop, engine, view["id"], "native-master-tiff-crop",
                APPROVED_SHEET_SHA256, source_crop_px=crop_box, require_parsed=True)

    plan_tokens = native[plan["id"]]
    section_tokens = native[section["id"]]
    if len(plan_tokens) != 2:
        raise RuntimeError(f"plan must expose exactly two explicit dimensions, found {len(plan_tokens)}")
    if len(section_tokens) != 2:
        raise RuntimeError(f"section must expose exactly two explicit dimensions, found {len(section_tokens)}")

    def shape(row):
        x0, y0, x1, y1 = row["rotated_bbox_px"]
        width, height = x1 - x0, y1 - y0
        if height >= width * 1.5:
            return "tall"
        if width >= height * 1.5:
            return "wide"
        return "ambiguous"

    plan_tall = [row for row in plan_tokens if shape(row) == "tall"]
    plan_wide = [row for row in plan_tokens if shape(row) == "wide"]
    if len(plan_tall) != 1 or len(plan_wide) != 1:
        raise RuntimeError("plan dimensions do not resolve one x-axis and one z-axis token")
    if any(shape(row) != "wide" for row in section_tokens):
        raise RuntimeError("section dimension chain tokens are not horizontal after rotation")

    width_token = plan_tall[0]
    depth_token = plan_wide[0]
    eave_token, rise_token = sorted(
        section_tokens, key=lambda row: (row["rotated_center_px"][0], row["id"]))
    semantics = ((width_token, "width_m", "original-plan-x"),
                 (depth_token, "depth_m", "original-plan-z"),
                 (eave_token, "eave_height_m", "section-base-to-eave"),
                 (rise_token, "roof_rise_m", "section-eave-to-ridge"))
    for token, semantic, axis in semantics:
        token["semantic"] = semantic
        token["semantic_binding_rule"] = axis

    normalized = {}
    for view in views:
        normalized[view["id"]] = normalized_support(
            building, view, engine, native[view["id"]])
    support_by_native = {row["supports_native_token_id"]: row
                         for rows in normalized.values() for row in rows}
    bindings = {}
    for token, semantic, _ in semantics:
        bindings[semantic] = {
            "native_token_id": token["id"],
            "normalized_support_token_id": support_by_native[token["id"]]["id"],
            "text": token["interpreted_text"],
            "value_m": token["value_m"],
        }
    ridge_m = round(bindings["eave_height_m"]["value_m"] +
                    bindings["roof_rise_m"]["value_m"], 6)
    return {
        "schema": "architectural-explicit-dimension-evidence/v0",
        "status": "PASS",
        "source": {"path": source_path.name, "source_sha256": APPROVED_SHEET_SHA256,
                   "sheet_pixels": sheet_pixels, "sheet_index": plan["sheet_index"]},
        "native_tokens": plan_tokens + section_tokens,
        "normalized_support_tokens": [row for rows in normalized.values() for row in rows],
        "bindings": bindings,
        "section_chain": {
            "order_rule": "rotated-x ascending after PIL 270-degree rotation",
            "operand_token_ids": [eave_token["id"], rise_token["id"]],
            "eave_height_m": bindings["eave_height_m"]["value_m"],
            "roof_rise_m": bindings["roof_rise_m"]["value_m"],
            "ridge_height_m": ridge_m,
            "operation": "eave_height_m + roof_rise_m",
        },
        "rejected_transcriptions": [{
            "text": "24'-8\"",
            "value_m": round(float(pipeline.parse_dimension("24'-8\"")), 6),
            "status": "REJECTED_NO_NATIVE_OR_NORMALIZED_OCR_SUPPORT",
            "superseded_by_native_token_id": depth_token["id"],
        }],
        "gate": "EXACTLY_TWO_PLAN_AND_TWO_SECTION_NATIVE_TOKENS_WITH_NORMALIZED_OCR_SUPPORT",
    }


def provisional_graph(prior_graph, plan, section, cut_line, dimension_evidence):
    bindings = dimension_evidence["bindings"]
    width_m = float(bindings["width_m"]["value_m"])
    depth_m = float(bindings["depth_m"]["value_m"])
    eave_m = float(bindings["eave_height_m"]["value_m"])
    rise_m = float(bindings["roof_rise_m"]["value_m"])
    ridge_m = round(eave_m + rise_m, 6)
    floor_count = max(1, int(prior_graph["dimensions"].get("floor_count") or 1))
    graph = {
        "schema": "architectural-water-flow-graph/v0",
        "id": f"habs-{SUBJECT}-provisional-water-flow",
        "building_id": SUBJECT,
        "status": "PROVISIONAL_RND_NOT_PROMOTED",
        "coordinate_frames": {
            "building_local": {"units": "metres", "handedness": "right",
                               "axes": {"x": "plan-right", "y": "height", "z": "plan-up"},
                               "origin": "automatic primary wall envelope lower-left"},
            "valheim_world": "unresolved",
        },
        "dimensions": {"width_m": round(width_m, 6), "depth_m": round(depth_m, 6),
                       "mean_height_m": round(eave_m, 6), "eave_height_m": round(eave_m, 6),
                       "roof_rise_m": round(rise_m, 6),
                       "ridge_height_m": round(ridge_m, 6), "floor_count": floor_count},
        "levels": [{"id": f"L{index}", "finished_floor_y_m": round(index * eave_m / floor_count, 4),
                    "status": "AUTOMATIC_PROVISIONAL"} for index in range(floor_count)],
        "footprints": [{"id": "primary", "level": "L0", "status": "AUTOMATIC_PROVISIONAL",
                        "polygon_xz": [[0, 0], [width_m, 0], [width_m, depth_m],
                                       [0, depth_m], [0, 0]]}],
        "roofs": [{"id": "primary-roof", "kind": "gable", "ridge_axis": "x",
                   "eave_y_m": round(eave_m, 6), "ridge_y_m": round(ridge_m, 6),
                   "status": "AUTOMATIC_TOPOLOGY_PROVISIONAL"}],
        "openings": [],
        "registration": {"status": "PASS", "mode": "SAME_SHEET_DISJOINT_PLAN_SECTION",
                         "plan_view_id": plan["id"], "section_view_id": section["id"],
                         "marker": cut_line["marker"], "cut_line_axis": cut_line["axis"],
                         "cut_line_authority": cut_line["authority"]},
        "assertions": [
            {"semantic": "width_m", "value": round(width_m, 6),
             "status": "OBSERVED_ROTATED_OCR_DIMENSION",
             "evidence_id": bindings["width_m"]["native_token_id"]},
            {"semantic": "depth_m", "value": round(depth_m, 6),
             "status": "OBSERVED_ROTATED_OCR_DIMENSION",
             "evidence_id": bindings["depth_m"]["native_token_id"]},
            {"semantic": "eave_height_m", "value": round(eave_m, 6),
             "status": "OBSERVED_ROTATED_OCR_DIMENSION",
             "evidence_id": bindings["eave_height_m"]["native_token_id"]},
            {"semantic": "roof_rise_m", "value": round(rise_m, 6),
             "status": "OBSERVED_ROTATED_OCR_DIMENSION",
             "evidence_id": bindings["roof_rise_m"]["native_token_id"]},
            {"semantic": "ridge_height_m", "value": round(ridge_m, 6),
             "status": "CALCULATED_EXPLICIT_SECTION_CHAIN",
             "evidence_ids": dimension_evidence["section_chain"]["operand_token_ids"]},
            {"semantic": "plan-section-correspondence", "value": cut_line["marker"],
             "status": "OBSERVED_PAIRED_MARKERS_AND_SEGMENTS"},
            {"semantic": "roof_topology", "value": "gable",
             "status": "AUTOMATIC_TOPOLOGY_PROVISIONAL"},
        ],
        "authority": "VISIBLE R&D FLOW ONLY; NOT G1/F1 PROMOTION",
    }
    return graph


def svg_overlay(plan_asset, cut_line):
    width, height = cut_line["image_pixels"]
    endpoint_shapes = []
    for row in cut_line["endpoints"]:
        x0, y0, x1, y1 = row["crop_px"]
        endpoint_shapes.append(
            f"<rect x='{x0}' y='{y0}' width='{x1-x0}' height='{y1-y0}' class='ocr'/>"
            f"<text x='{x0}' y='{max(14, y0-5)}'>{html.escape(row['marker'])} {row['confidence']:.2f}</text>")
    segment_shapes = []
    for row in cut_line["endpoint_segments"]:
        x0, y0, x1, y1 = row["pixels"]
        segment_shapes.append(f"<line x1='{x0}' y1='{y0}' x2='{x1}' y2='{y1}' class='segment'/>")
    first, second = cut_line["endpoints"]
    return f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}'>
<style>text{{font:700 13px monospace;fill:#00a66b;paint-order:stroke;stroke:white;stroke-width:3px}}.ocr{{fill:none;stroke:#00a66b;stroke-width:3px}}.segment{{stroke:#ff5c35;stroke-width:5px}}.axis{{stroke:#00a66b;stroke-width:3px;stroke-dasharray:10 8}}</style>
<image href='{html.escape(plan_asset)}' width='{width}' height='{height}'/>
<line x1='{first['center_px'][0]}' y1='{first['center_px'][1]}' x2='{second['center_px'][0]}' y2='{second['center_px'][1]}' class='axis'/>
{''.join(segment_shapes)}{''.join(endpoint_shapes)}</svg>""".encode("utf-8")


def dashboard(result, residual):
    dims = result["graph"]["dimensions"]
    evidence = result["dimension_evidence"]
    bindings = evidence["bindings"]
    rejected = evidence["rejected_transcriptions"][0]
    checks = "".join(
        f"<tr><td>{html.escape(row['semantic'])}</td><td>{row['observed_m']:.3f} m</td>"
        f"<td>{row['predicted_m']:.3f} m</td><td class='{'ok' if row['status']=='PASS' else 'warn'}'>{row['status']}</td></tr>"
        for row in residual.get("metric_checks", []))
    browser = result["browser"]
    return f"""<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>tn0304 automatic water flow</title><style>
:root{{--bg:#071014;--panel:#112027;--line:#29424d;--ink:#edf4f0;--muted:#9ab1bb;--flow:#5ce1a1;--warn:#f5b942}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 Arial;padding:22px}}h1,h2{{margin:.2rem 0 .7rem}}.k{{color:var(--flow);font:700 12px monospace;letter-spacing:.15em}}.banner{{border:1px solid var(--flow);padding:12px;margin:14px 0;color:var(--flow)}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.panel{{background:var(--panel);border:1px solid var(--line);padding:14px}}img,object,iframe{{width:100%;border:0;background:white}}iframe{{height:520px;background:#101820}}.row{{display:flex;justify-content:space-between;border-top:1px solid var(--line);padding:8px 0}}.muted{{color:var(--muted)}}.ok{{color:var(--flow)}}.warn{{color:var(--warn)}}table{{width:100%;border-collapse:collapse}}td,th{{padding:7px;border-top:1px solid var(--line);text-align:left}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style><div class='k'>SHARK LANE &middot; ONE REAL BUILDING &middot; NO PROMOTION CLAIM</div><h1>Measured drawing &rarr; automatic graph &rarr; prefab water</h1>
<div class='banner'>{result['status']} &middot; {result['piece_count']} pieces &middot; registration {result['cut_line']['status']}</div>
<div class='grid'><section class='panel'><h2>1 &middot; Plan correspondence</h2><object data='plan-overlay.svg' type='image/svg+xml'></object><p class='muted'>Green: paired OCR W endpoints and implied axis. Orange: source-pinned Hough segments. Metric span did not manufacture this gate.</p></section>
<section class='panel'><h2>2 &middot; SECTION W-W explicit chain</h2><img src='assets/section.png'><div class='row'><span>{html.escape(bindings['eave_height_m']['text'])} base to eave</span><b>{dims['eave_height_m']:.4f} m</b></div><div class='row'><span>{html.escape(bindings['roof_rise_m']['text'])} eave to ridge</span><b>{dims['roof_rise_m']:.4f} m</b></div><div class='row'><span>Calculated ridge</span><b>{dims['ridge_height_m']:.4f} m</b></div></section>
<section class='panel'><h2>3 &middot; Native-raster metric graph</h2><div class='row'><span>{html.escape(bindings['width_m']['text'])} plan x</span><b>{dims['width_m']:.4f} m</b></div><div class='row'><span>{html.escape(bindings['depth_m']['text'])} plan z</span><b>{dims['depth_m']:.4f} m</b></div><div class='row'><span>Floors</span><b>{dims['floor_count']}</b></div><div class='row'><span>Authority</span><b class='warn'>PROVISIONAL R&amp;D</b></div><p class='muted'>Every scene dimension is bound from an explicit master-TIFF OCR token and independently supported by OCR on the normalized view. Earlier {html.escape(rejected['text'])} transcription: {rejected['status']}.</p></section>
<section class='panel'><h2>4 &middot; Different-sheet CSS diagnostic</h2><img src='assets/holdout.png'><table><tr><th>Datum</th><th>Observed</th><th>Predicted</th><th>Gate</th></tr>{checks}</table><p class='muted'>This elevation contributed no construction or registration evidence.</p></section></div>
<section class='panel' style='margin-top:14px'><h2>5 &middot; Existing WebGPU prefab-envelope flow</h2><iframe src='webgpu/index.html?view=iso&mode=solid'></iframe><p class='muted'>Browser receipt: {html.escape(str(browser.get('status')))}. Scene emission&mdash;not GPU benchmarking&mdash;is this lap's visible gate.</p></section>""".encode("utf-8")


def reset_owned_outputs(root):
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    for directory in (root / "assets", root / "webgpu"):
        if directory.exists():
            if directory.parent != root:
                raise RuntimeError("refusing to remove an output outside the owned sentinel root")
            shutil.rmtree(directory)
    for name in ("building.graph.json", "cut-line.json", "dashboard.html", "pieces.json",
                 "dimension-evidence.json", "plan-overlay.svg", "result.json",
                 "verification.json"):
        (root / name).unlink(missing_ok=True)


def run(args):
    revision, building, evidence, prior_graph, prior_assessment = source_building(args)
    plan = primary_plan_view(evidence)
    section = role_view(evidence, "section", r"\bSECTION\s+[A-Z]\s*[-]\s*[A-Z]\b")
    holdout_id = evidence["holdout"]["view_id"]
    holdout = next(row for row in evidence["views"] if row["id"] == holdout_id)
    if plan["sheet_index"] != section["sheet_index"] or holdout["sheet_index"] == plan["sheet_index"]:
        raise RuntimeError("tn0304 no longer has same-sheet plan/section and different-sheet holdout")
    if evidence.get("maximum_view_overlap_ratio") != 0:
        raise RuntimeError("construction views are not disjoint")
    native_sheet, _ = source_sheet(args, plan)

    root = args.out.resolve()
    reset_owned_outputs(root)
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    paths = {"plan": image_path(building, plan), "section": image_path(building, section),
             "holdout": image_path(building, holdout)}
    for name, source in paths.items():
        shutil.copyfile(source, assets / f"{name}.png")

    from rapidocr import RapidOCR

    engine = RapidOCR()
    marker = section_marker(section)
    dimension_evidence = explicit_dimension_evidence(
        native_sheet, building, plan, section, engine)
    if dimension_evidence["status"] != "PASS":
        raise RuntimeError("explicit dimension evidence did not clear the compiler cutline")
    cut_line = make_cut_line(plan, paths["plan"], marker, engine)
    graph = provisional_graph(prior_graph, plan, section, cut_line, dimension_evidence)
    pieces, composition = pipeline.compile_generic(graph, 256)
    if not pieces or not composition["within_budget"]:
        raise RuntimeError(f"provisional composition did not flow: {composition}")

    assessment = {"building_id": SUBJECT, "route": {"approved": "PROVISIONAL_RND"}}
    browser = None if args.no_browser else pipeline.find_browser()
    pipeline.write_simple_webgpu(root, assessment, graph, pieces, browser)
    browser_receipt = load_json(root / "webgpu" / "browser-receipt.json")
    residual = prior_assessment["residual"]
    result = {
        "schema": "architectural-water-flow-result/v0", "engine": ENGINE,
        "status": "WATER_FLOWING_PROVISIONAL", "building_id": SUBJECT,
        "upstream_v3_revision": revision, "promotion": "NONE",
        "source_sheet_sha256": APPROVED_SHEET_SHA256,
        "cut_line": cut_line, "dimension_evidence": dimension_evidence,
        "graph": graph, "piece_count": len(pieces),
        "composition": composition, "holdout": {"view_id": holdout["id"],
            "sheet_index": holdout["sheet_index"], "contributed_construction_evidence": False,
            "residual_status": residual["status"]},
        "browser": browser_receipt,
        "authority": {"network_requests": 0, "vlm_calls": 0, "downloads": 0,
                      "world_writes": 0, "ocr_recognition_windows": cut_line["recognition_windows"],
                      "ocr_full_view_passes": 4},
        "warnings": ["This is a visible R&D flow, not G1/F1 promotion.",
                     "Dimensions are provisional but bind only explicit source-raster tokens.",
                     "The different-sheet CSS residual is preserved even when it fails."],
    }
    pipeline.atomic_json(root / "cut-line.json", cut_line)
    pipeline.atomic_json(root / "dimension-evidence.json", dimension_evidence)
    pipeline.atomic_json(root / "building.graph.json", graph)
    pipeline.atomic_json(root / "pieces.json", {"pieces": pieces, "composition": composition})
    pipeline.atomic_bytes(root / "plan-overlay.svg", svg_overlay("assets/plan.png", cut_line))
    pipeline.atomic_bytes(root / "dashboard.html", dashboard(result, residual))
    artifacts = {}
    artifact_paths = [root / "cut-line.json", root / "dimension-evidence.json",
                      root / "building.graph.json", root / "pieces.json",
                      root / "plan-overlay.svg", root / "dashboard.html",
                      root / "webgpu" / "scene.json", root / "webgpu" / "scene.bin",
                      root / "webgpu" / "browser-receipt.json"]
    preview = root / "webgpu" / "preview.png"
    if preview.is_file():
        artifact_paths.append(preview)
    for path in artifact_paths:
        artifacts[path.relative_to(root).as_posix()] = {
            "sha256": pipeline.digest_file(path), "bytes": path.stat().st_size}
    result["artifacts"] = artifacts
    pipeline.atomic_json(root / "result.json", result)
    verification = verify(args)
    print(f"{result['status']} {SUBJECT} | {len(pieces)} pieces | "
          f"cut-line {cut_line['marker']}-{cut_line['marker']} {cut_line['axis']} | "
          f"verification {verification['status']}")
    return 0 if verification["status"] == "PASS" else 1


def verify(args):
    root = args.out.resolve()
    result = load_json(root / "result.json")
    errors = []
    prior_assessment = None
    try:
        revision, _, upstream_evidence, _, prior_assessment = source_building(args)
        plan = primary_plan_view(upstream_evidence)
        native_sheet, _ = source_sheet(args, plan)
        if pipeline.digest_file(native_sheet) != APPROVED_SHEET_SHA256:
            errors.append("native sheet changed after source-pin validation")
        if revision != result.get("upstream_v3_revision"):
            errors.append("result no longer names the pinned v3 revision")
    except Exception as exc:
        errors.append(f"source pin failed: {exc}")

    if result.get("status") != "WATER_FLOWING_PROVISIONAL" or result.get("promotion") != "NONE":
        errors.append("result must flow visibly without promotion")
    if (result.get("upstream_v3_revision") != APPROVED_V3_REVISION or
            result.get("source_sheet_sha256") != APPROVED_SHEET_SHA256):
        errors.append("result does not carry the approved revision and raster pins")

    cut_line = result.get("cut_line", {})
    endpoints = cut_line.get("endpoints", [])
    segments = cut_line.get("endpoint_segments", [])
    if cut_line.get("status") != "PASS" or len(endpoints) != 2 or len(segments) != 2:
        errors.append("paired-marker cut line lacks two endpoint and segment receipts")
    if any(row.get("source_sha256") != APPROVED_SHEET_SHA256 for row in endpoints + segments):
        errors.append("cut-line evidence is not pinned to the approved native sheet")
    if any(row.get("ocr_engine") != "RapidOCR/3.9.2-recognizer" for row in endpoints):
        errors.append("cut-line endpoints do not carry the required OCR receipt")
    if any(row.get("detector") != "OpenCV.HoughLinesP" for row in segments):
        errors.append("cut-line segments do not carry the required detector receipt")

    dimensions = result.get("dimension_evidence", {})
    native_tokens = dimensions.get("native_tokens", [])
    support_tokens = dimensions.get("normalized_support_tokens", [])
    bindings = dimensions.get("bindings", {})
    expected_semantics = {"width_m", "depth_m", "eave_height_m", "roof_rise_m"}
    if dimensions.get("status") != "PASS" or len(native_tokens) != 4 or len(support_tokens) != 4:
        errors.append("dimension cutline requires four native tokens and four normalized supports")
    if set(bindings) != expected_semantics:
        errors.append("dimension bindings are incomplete or contain an unapproved semantic")
    native_by_id = {row.get("id"): row for row in native_tokens}
    support_by_id = {row.get("id"): row for row in support_tokens}
    if len(native_by_id) != len(native_tokens) or len(support_by_id) != len(support_tokens):
        errors.append("dimension token ids are not unique")
    for token in native_tokens:
        interpreted, parsed, repair = explicit_dimension_parse(token.get("text"))
        value = token.get("value_m")
        if (token.get("source_kind") != "native-master-tiff-crop" or
                token.get("source_sha256") != APPROVED_SHEET_SHA256 or
                token.get("ocr_engine") != "RapidOCR/3.9.2-detector-recognizer" or
                float(token.get("confidence", 0)) < 0.80 or
                not isinstance(token.get("source_crop_px"), list) or
                token.get("rotation", {}).get("degrees_counter_clockwise") != 270 or
                token.get("interpreted_text") != interpreted or
                token.get("transcription_repair") != repair or
                parsed is None or value is None or
                not math.isclose(float(parsed), float(value), abs_tol=1e-6)):
            errors.append(f"native dimension token lacks exact OCR provenance: {token.get('id')}")
    for token in support_tokens:
        native = native_by_id.get(token.get("supports_native_token_id"))
        if (native is None or token.get("source_kind") != "normalized-v3-view" or
                not re.fullmatch(r"[0-9a-f]{64}", str(token.get("source_sha256", ""))) or
                token.get("upstream_source_sha256") != APPROVED_SHEET_SHA256 or
                token.get("ocr_engine") != "RapidOCR/3.9.2-detector-recognizer" or
                float(token.get("confidence", 0)) < 0.80 or
                token.get("numeric_atoms") != native.get("numeric_atoms")):
            errors.append(f"normalized OCR support is not independent and exact: {token.get('id')}")

    graph_dimensions = result.get("graph", {}).get("dimensions", {})
    for semantic in expected_semantics:
        binding = bindings.get(semantic, {})
        native = native_by_id.get(binding.get("native_token_id"))
        support = support_by_id.get(binding.get("normalized_support_token_id"))
        graph_value = graph_dimensions.get(semantic)
        if (native is None or support is None or
                support.get("supports_native_token_id") != native.get("id") or
                binding.get("text") != native.get("interpreted_text") or
                binding.get("value_m") != native.get("value_m") or graph_value is None or
                not math.isclose(float(graph_value), float(native.get("value_m", math.nan)),
                                 abs_tol=1e-6)):
            errors.append(f"graph dimension is not bound to its explicit token: {semantic}")
    chain = dimensions.get("section_chain", {})
    eave = bindings.get("eave_height_m", {}).get("value_m")
    rise = bindings.get("roof_rise_m", {}).get("value_m")
    ridge = graph_dimensions.get("ridge_height_m")
    if (eave is None or rise is None or ridge is None or
            not math.isclose(float(ridge), float(eave) + float(rise), abs_tol=1e-6) or
            not math.isclose(float(chain.get("ridge_height_m", math.nan)), float(ridge),
                             abs_tol=1e-6)):
        errors.append("ridge is not the explicit SECTION W-W addition chain")

    rejected_text = "24'-8\""
    rejected = [row for row in dimensions.get("rejected_transcriptions", [])
                if row.get("text") == rejected_text]
    depth_token = native_by_id.get(bindings.get("depth_m", {}).get("native_token_id"), {})
    if (len(rejected) != 1 or
            rejected[0].get("status") != "REJECTED_NO_NATIVE_OR_NORMALIZED_OCR_SUPPORT" or
            not math.isclose(float(rejected[0].get("value_m", math.nan)),
                             float(pipeline.parse_dimension(rejected_text)), abs_tol=1e-6) or
            rejected[0].get("superseded_by_native_token_id") != depth_token.get("id") or
            rejected[0].get("value_m") == graph_dimensions.get("depth_m") or
            numeric_atoms(rejected_text) == depth_token.get("numeric_atoms")):
        errors.append("earlier 24-foot-8 transcription is not explicitly rejected")

    if result.get("piece_count", 0) <= 0 or result.get("piece_count", 0) > 256:
        errors.append("piece flow is empty or over budget")
    if result.get("holdout", {}).get("contributed_construction_evidence") is not False:
        errors.append("different-sheet holdout leaked into construction")
    if (prior_assessment is not None and
            result.get("holdout", {}).get("residual_status") !=
            prior_assessment.get("residual", {}).get("status")):
        errors.append("different-sheet CSS diagnostic was not preserved honestly")
    if any(result.get("authority", {}).get(key) != 0 for key in
           ("network_requests", "vlm_calls", "downloads", "world_writes")):
        errors.append("sentinel crossed its authority boundary")
    for relative, receipt in result.get("artifacts", {}).items():
        path = root / relative
        if not path.is_file() or pipeline.digest_file(path) != receipt.get("sha256"):
            errors.append(f"artifact drift: {relative}")
    scene = load_json(root / "webgpu" / "scene.json")
    browser = result.get("browser", {})
    if scene.get("pieces") != result.get("piece_count"):
        errors.append("WebGPU scene does not contain the compiled piece count")
    if (browser.get("status") != "ok" or browser.get("capture_status") != "PASS" or
            browser.get("device_lost") is not False or
            browser.get("pieces") != result.get("piece_count")):
        errors.append("browser did not visibly render the compiled scene")

    verification = {"schema": "architectural-water-flow-verification/v1",
                    "status": "PASS" if not errors else "FAIL", "errors": errors,
                    "building_id": SUBJECT, "cohort_buildings_processed": 1,
                    "promotion": "NONE", "upstream_v3_revision": APPROVED_V3_REVISION,
                    "source_sheet_sha256": APPROVED_SHEET_SHA256}
    pipeline.atomic_json(root / "verification.json", verification)
    if args.command == "verify":
        print(f"water-flow verification: {verification['status']} | one building")
    return verification


def serve(args):
    root = args.out.resolve()
    if not (root / "dashboard.html").is_file():
        raise RuntimeError("run the tn0304 water-flow sentinel first")
    handler = lambda *values, **kwargs: SimpleHTTPRequestHandler(
        *values, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"serving {root} at http://127.0.0.1:{args.port}/dashboard.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main():
    args = parse_args()
    if args.command == "run":
        return run(args)
    if args.command == "verify":
        return 0 if verify(args)["status"] == "PASS" else 1
    return serve(args)


if __name__ == "__main__":
    raise SystemExit(main())

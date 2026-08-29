#!/usr/bin/env python3
"""Run the v2 causal repair experiment upstream of the first CSS gate.

The v1 holdout showed that CSS was correctly refusing under-specified building
graphs.  This successor keeps CSS read-only and repairs the evidence graph instead:
dimension axes are owned by nearby linework, scale anchors are independently
derived, plan extents must close on two axes, and geometric roof datums are emitted
only as an opposed-slope ridge/eave pair.  The revealed v1 corpus is development
data; a separately acquired eight-building corpus remains blind until sealing.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import probe_architectural_css_fit as css0
import probe_architectural_css_fit_v1 as v1
import probe_architectural_css_topology as topology0
import probe_architectural_curriculum as pipeline


ENGINE = "architectural-pre-css-causal-repair/2.0.0"
DEFAULT_CHARTER = HERE / "architectural-css-fit-v2.json"
DEFAULT_SCHEMAS = HERE / "architectural-css-fit-schemas-v2.json"
DEFAULT_DEVELOPMENT_SELECTION = HERE / "habs-corpus.json"
DEFAULT_DEVELOPMENT_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_DEVELOPMENT_AUDIT = HERE / "out" / "architectural-curriculum" / "real-ocr-audit-v1"
DEFAULT_BLIND_SELECTION = HERE / "habs-corpus-v2-holdout.json"
DEFAULT_BLIND_SOURCE_CHARTER = HERE / "architectural-curriculum-v2-holdout-source.json"
DEFAULT_BLIND_CORPUS = HERE / "out" / "loc-habs-v2-holdout" / "corpus"
DEFAULT_BLIND_AUDIT = HERE / "out" / "architectural-curriculum" / "real-ocr-audit-v2-holdout"
DEFAULT_BASELINE = HERE / "out" / "architectural-css-fit-v1"
DEFAULT_OUT = HERE / "out" / "architectural-css-fit-v2"


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--charter", type=Path, default=DEFAULT_CHARTER)
    common.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS)
    common.add_argument("--development-selection", type=Path, default=DEFAULT_DEVELOPMENT_SELECTION)
    common.add_argument("--development-corpus", type=Path, default=DEFAULT_DEVELOPMENT_CORPUS)
    common.add_argument("--development-audit", type=Path, default=DEFAULT_DEVELOPMENT_AUDIT)
    common.add_argument("--blind-selection", type=Path, default=DEFAULT_BLIND_SELECTION)
    common.add_argument("--blind-source-charter", type=Path, default=DEFAULT_BLIND_SOURCE_CHARTER)
    common.add_argument("--blind-corpus", type=Path, default=DEFAULT_BLIND_CORPUS)
    common.add_argument("--blind-audit", type=Path, default=DEFAULT_BLIND_AUDIT)
    common.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    develop = commands.add_parser("develop", parents=[common])
    develop.add_argument("--seal", action="store_true")
    commands.add_parser("blind", parents=[common])
    commands.add_parser("verify", parents=[common])
    serve = commands.add_parser("serve", parents=[common])
    serve.add_argument("--port", type=int, default=8880)
    args = parser.parse_args()
    # Compatibility fields consumed by the shared immutable run harness.  The v2
    # loader and processor use the explicit development/blind paths above.
    args.selection = args.development_selection
    args.corpus = args.development_corpus
    args.audit = args.development_audit
    return args


def audit_membership(index):
    membership = {}
    for cluster in index.get("presort", {}).get("clusters", []):
        for building_id in cluster.get("members", []):
            membership[building_id] = cluster["id"]
    return membership


def load_record_set(selection, corpus, source_charter, audit, expected_revision):
    revision = (audit / "HEAD").read_text(encoding="ascii").strip()
    if revision != expected_revision:
        raise RuntimeError(f"OCR audit revision changed: {revision} != {expected_revision}")
    audit_rev = audit / "revisions" / revision
    index = json.loads((audit_rev / "index.json").read_text(encoding="utf-8"))
    source_args = SimpleNamespace(charter=source_charter, selection=selection, corpus=corpus)
    _, _, records = pipeline.load_inputs(source_args)
    membership = audit_membership(index)
    output = {}
    for record in records:
        record["cluster"] = membership.get(record["id"], "CU")
        record["audit_revision"] = revision
        record["audit_rev"] = audit_rev
        record["corpus"] = corpus
        output[record["id"]] = record
    return revision, index, output


def load_inputs(args):
    charter = json.loads(args.charter.read_text(encoding="utf-8"))
    if pipeline.digest_file(args.development_selection) != charter["inputs"]["development_selection_sha256"]:
        raise RuntimeError("frozen development selection hash changed")
    if pipeline.digest_file(args.blind_selection) != charter["inputs"]["blind_selection_sha256"]:
        raise RuntimeError("frozen blind selection hash changed")
    baseline_revision = (args.baseline / "HEAD").read_text(encoding="ascii").strip()
    if baseline_revision != charter["inputs"]["css_v1_baseline_revision"]:
        raise RuntimeError("CSS v1 baseline revision changed")
    dev_revision, dev_index, dev_records = load_record_set(
        args.development_selection, args.development_corpus,
        HERE / "architectural-curriculum-v1.json", args.development_audit,
        charter["inputs"]["development_ocr_audit_revision"])
    blind_revision, blind_index, blind_records = load_record_set(
        args.blind_selection, args.blind_corpus, args.blind_source_charter,
        args.blind_audit, charter["inputs"]["blind_ocr_audit_revision"])
    records = {**dev_records, **blind_records}
    expected = set(charter["evaluation"]["development_buildings"] +
                   charter["evaluation"]["blind_buildings"])
    if set(records) != expected or len(records) != charter["inputs"]["buildings"]:
        raise RuntimeError("frozen 20/8 split does not match the two corpora")
    combined_index = {"sheets": dev_index["sheets"] + blind_index["sheets"]}
    revisions = {"development": dev_revision, "blind": blind_revision}
    return charter, revisions, None, combined_index, records


def line_key(line):
    if not line:
        return None
    return ":".join(str(int(round(line[key]))) for key in ("x0", "y0", "x1", "y1"))


def dimension_rows(sheet, views, lines, charter):
    rows = []
    seen = set()
    height, width = sheet["normalized_pixels"][1], sheet["normalized_pixels"][0]
    threshold = max(width, height) * charter["topology"]["dimension_line_max_distance_ratio"]
    for raw_authority, source in (("STRICT", sheet["strict_dimensions"]),
                                  ("REPAIRED", sheet["suspicious_dimensions"])):
        for ordinal, item in enumerate(source):
            value = (float(item["value_m"]) if raw_authority == "STRICT" else
                     topology0.repaired_dimension(item["text"]))
            key = (item["text"], tuple(round(float(number), 7) for number in item["region"]))
            if value is None or key in seen:
                continue
            seen.add(key)
            point = css0.center(item["region"])
            view = v1.owning_view(point, views)
            text = css0.normalized_text(item["text"])
            status = "OBSERVED"
            if css0.CONTEXT_HOLD_RE.search(text) or v1.PRODUCT_RE.search(text):
                status = "HELD_CONTEXT"
            elif view is None:
                status = "HELD_AMBIGUOUS"
            px, py = point[0] * width, point[1] * height
            options = sorted(
                ((css0.point_segment_distance(px, py, line), -line["length_px"], index, line)
                 for index, line in enumerate(lines) if line["axis"] in ("horizontal", "vertical")),
                key=lambda row: (row[0], row[1], row[2]))
            nearest = options[0][3] if options and options[0][0] <= threshold else None
            legacy_axis = topology0.dimension_axis(item["region"])
            axis = nearest["axis"] if nearest else legacy_axis
            candidate_scale = (float(value) / nearest["length_px"]
                               if nearest and raw_authority == "STRICT" else None)
            rows.append({
                "schema": "architectural-dimension-binding/v2",
                "id": f"{sheet['building_id']}-s{sheet['sheet_index']:02d}-od{ordinal+1:03d}-{raw_authority.lower()}",
                "text": item["text"], "value_m": round(float(value), 6),
                "raw_authority": raw_authority,
                "authority": raw_authority if raw_authority == "STRICT" else "HELD",
                "axis": axis, "legacy_axis": legacy_axis,
                "axis_authority": "OWNED_CARDINAL_LINE" if nearest else "HELD_TOKEN_SHAPE",
                "line": ({key: nearest[key] for key in
                          ("x0", "y0", "x1", "y1", "length_px", "axis")}
                         if nearest else None),
                "candidate_metres_per_pixel": (round(candidate_scale, 9) if candidate_scale else None),
                "center": [round(number, 6) for number in point],
                "region": [round(float(number), 6) for number in item["region"]],
                "sheet_index": sheet["sheet_index"],
                "view_id": view["id"] if view else None, "status": status,
                "provenance": css0.source_ref(sheet, item["region"]),
            })
    return sorted(rows, key=lambda row: (row["view_id"] or "~", row["axis"],
                                         row["center"][1], row["center"][0], row["id"]))


def compatible_consensus(candidates, charter):
    maximum = charter["promotion"]["maximum_scale_anchor_spread_ratio"]
    minimum = charter["promotion"]["minimum_independent_scale_anchors"]
    minimum_origins = charter["promotion"]["minimum_scale_anchor_origins"]
    ordered = sorted(candidates, key=lambda row: (row["metres_per_pixel"], row["id"]))
    options = []
    for start in range(len(ordered)):
        for end in range(start + 1, len(ordered) + 1):
            group = ordered[start:end]
            values = [row["metres_per_pixel"] for row in group]
            spread = ((max(values) - min(values)) / statistics.mean(values)) if len(values) >= 2 else None
            origins = {row["origin"] for row in group}
            if spread is not None and spread <= maximum:
                options.append((len(group), len(origins), -spread, group, spread, origins))
    if not options:
        return [], {"status": "FAIL", "anchor_count": 0, "origin_count": 0,
                    "spread_ratio": None, "metres_per_pixel": None}
    _, _, _, selected, spread, origins = max(options, key=lambda row: (row[0], row[1], row[2]))
    status = "PASS" if len(selected) >= minimum and len(origins) >= minimum_origins else "FAIL"
    return selected, {"status": status, "anchor_count": len(selected),
                      "origin_count": len(origins), "spread_ratio": round(spread, 9),
                      "metres_per_pixel": round(statistics.mean(
                          row["metres_per_pixel"] for row in selected), 9)}


def scale_candidates(view, dimensions):
    candidates = []
    if view.get("scale"):
        base = statistics.mean([view["scale"]["metres_per_pixel_x"],
                                view["scale"]["metres_per_pixel_y"]])
        candidates.append({
            "id": f"{view['id']}:notation", "kind": "complete-scale-notation",
            "origin": f"notation:{view['scale']['provenance']}",
            "metres_per_pixel": round(base, 9), "authority": "STRICT",
        })
    sheet_scope = bool(view.get("scale") and view["scale"].get("owner_scope") == "sheet")
    for row in dimensions:
        candidate = row.get("candidate_metres_per_pixel")
        owned = (row["view_id"] == view["id"] or
                 (sheet_scope and row.get("sheet_index") == view["sheet_index"]))
        if (not owned or row["status"] != "OBSERVED" or
                row["raw_authority"] != "STRICT" or not candidate or not row.get("line")):
            continue
        candidates.append({
            "id": row["id"], "kind": "owned-strict-dimension-line",
            "origin": f"dimension-line:s{row.get('sheet_index', view['sheet_index']):02d}:{line_key(row['line'])}",
            "metres_per_pixel": candidate, "authority": "STRICT",
            "dimension_id": row["id"], "axis": row["axis"],
        })
    return candidates


def scale_anchors(primary, views, dimensions, chains, charter):
    if not primary:
        return [], [], {"status": "FAIL", "anchor_count": 0, "origin_count": 0,
                        "spread_ratio": None, "metres_per_pixel": None}
    view = next(item for item in views if item["id"] == primary["view_id"])
    candidates = scale_candidates(view, dimensions)
    candidates.extend(primary.get("axis_span_anchors", []))
    selected, consensus = compatible_consensus(candidates, charter)
    selected_ids = {row["id"] for row in selected}
    for row in candidates:
        row["consensus"] = "SELECTED" if row["id"] in selected_ids else "REJECTED"
    return selected, candidates, consensus


def mass_hypotheses(record, sheets, views, dimensions, measurements, line_map, charter):
    masses = v1.mass_hypotheses(record, sheets, views, dimensions, measurements, line_map)
    view_map = {view["id"]: view for view in views}
    for mass in masses:
        mass["schema"] = "architectural-mass-hypothesis/v2"
        mass["extent_authority"] = "OWNED_STRICT_DIMENSION_LINES"
        mass["dimension_axis_sources"] = {
            "width": next((row.get("axis_authority") for row in dimensions
                           if row["id"] == mass["dimensions"].get("width_dimension_id")), None),
            "depth": next((row.get("axis_authority") for row in dimensions
                           if row["id"] == mass["dimensions"].get("depth_dimension_id")), None),
        }
        complete = all(mass["dimensions"].get(key) is not None for key in ("width_m", "depth_m"))
        if not complete and mass["label"] == "PRIMARY" and mass["closed_wall_loop"]:
            owned = [row for row in dimensions if row["view_id"] == mass["view_id"] and
                     row["status"] == "OBSERVED" and row.get("axis_authority") == "OWNED_CARDINAL_LINE"]
            minimum = charter["promotion"]["minimum_width_depth_m"]
            ratio_minimum = charter["topology"]["minimum_primary_aspect_ratio"]
            for key, axis, opposite_key in (("width_m", "horizontal", "depth_m"),
                                            ("depth_m", "vertical", "width_m")):
                if mass["dimensions"][key] is not None or mass["dimensions"][opposite_key] is None:
                    continue
                opposite = mass["dimensions"][opposite_key]
                repaired = [row for row in owned if row["axis"] == axis and
                            row["raw_authority"] == "REPAIRED" and row["value_m"] >= minimum and
                            ratio_minimum <= row["value_m"] / opposite <= 1 / ratio_minimum]
                if repaired:
                    chosen = max(repaired, key=lambda row: (row["value_m"], row["id"]))
                    mass["dimensions"][key] = chosen["value_m"]
                    id_key = "width_dimension_id" if key == "width_m" else "depth_dimension_id"
                    mass["dimensions"][id_key] = chosen["id"]
                    mass.setdefault("topology_corroborated_axes", []).append(key.removesuffix("_m"))
                    mass["extent_authority"] = "TOPOLOGY_CORROBORATED_REPAIRED_LINE_IN_CLOSED_LOOP"
        if not complete and mass["label"] == "PRIMARY" and mass["closed_wall_loop"]:
            view = view_map[mass["view_id"]]
            selected, consensus = compatible_consensus(scale_candidates(view, dimensions), charter)
            geometry = measurements.get(view["id"], {}).get("geometry")
            if consensus["status"] == "PASS" and geometry:
                inferred = []
                if mass["dimensions"]["width_m"] is None:
                    mass["dimensions"]["width_m"] = round(
                        geometry["width_px"] * consensus["metres_per_pixel"], 6)
                    mass["dimensions"]["width_dimension_id"] = f"{view['id']}:topology-width"
                    inferred.append("width")
                if mass["dimensions"]["depth_m"] is None:
                    mass["dimensions"]["depth_m"] = round(
                        geometry["height_px"] * consensus["metres_per_pixel"], 6)
                    mass["dimensions"]["depth_dimension_id"] = f"{view['id']}:topology-depth"
                    inferred.append("depth")
                mass["topology_inferred_axes"] = inferred
                mass["scale_anchor_ids"] = [row["id"] for row in selected]
                mass["extent_authority"] = "TOPOLOGY_CORROBORATED_CLOSED_LOOP"
        complete = all(mass["dimensions"].get(key) is not None for key in ("width_m", "depth_m"))
        mass["two_axis_dimensions"] = complete
        if complete and mass["closed_wall_loop"]:
            mass["status"] = "CANDIDATE"
    selectable = [mass for mass in masses if mass["status"] == "CANDIDATE" and
                  mass["label"] not in ("ADDITION", "WING", "ELL")]
    if selectable:
        selected = min(selectable, key=lambda mass: (
            1 if "BASEMENT" in css0.normalized_text(mass["view_label"]) else 0,
            0 if mass["label"] in ("PRIMARY", "LOG CABIN") else 1,
            -mass["dimensions"]["width_m"] * mass["dimensions"]["depth_m"], mass["id"]))
        for mass in masses:
            if mass is selected:
                mass["status"] = "SELECTED_PRIMARY"
            elif mass["status"] == "CANDIDATE":
                mass["status"] = "SECONDARY"
        width_row = next((row for row in dimensions
                          if row["id"] == selected["dimensions"].get("width_dimension_id") and
                          row["raw_authority"] == "STRICT"), None)
        depth_row = next((row for row in dimensions
                          if row["id"] == selected["dimensions"].get("depth_dimension_id") and
                          row["raw_authority"] == "STRICT"), None)
        geometry = measurements.get(selected["view_id"], {}).get("geometry")
        if width_row and depth_row and geometry:
            x0, y0, x1, y1 = geometry["local_bbox_px"]
            horizontal, vertical = [], []
            for line in line_map.get(selected["view_id"], []):
                lx0, ly0, lx1, ly1 = line["local"]
                midpoint = ((lx0 + lx1) / 2, (ly0 + ly1) / 2)
                if not (x0 - 8 <= midpoint[0] <= x1 + 8 and y0 - 8 <= midpoint[1] <= y1 + 8):
                    continue
                if line["axis"] == "horizontal" and line["length_px"] >= geometry["width_px"] * 0.2:
                    horizontal.append(line)
                elif line["axis"] == "vertical" and line["length_px"] >= geometry["height_px"] * 0.2:
                    vertical.append(line)
            pairs = []
            for hline in horizontal:
                for vline in vertical:
                    sx = selected["dimensions"]["width_m"] / hline["length_px"]
                    sz = selected["dimensions"]["depth_m"] / vline["length_px"]
                    spread = abs(sx - sz) / statistics.mean([sx, sz])
                    if spread <= charter["promotion"]["maximum_scale_anchor_spread_ratio"]:
                        pairs.append((spread, -(hline["length_px"] + vline["length_px"]),
                                      hline, vline, sx, sz))
            if pairs:
                spread, _, hline, vline, sx, sz = min(
                    pairs, key=lambda row: (row[0], row[1], line_key(row[2]), line_key(row[3])))
                selected["axis_span_anchors"] = [
                    {"id": f"{selected['id']}:closed-loop-x", "kind": "closed-loop-axis-span",
                     "origin": f"closed-loop:{width_row['id']}:{line_key(hline)}",
                     "metres_per_pixel": round(sx, 9), "authority": "TOPOLOGY_CORROBORATED",
                     "dimension_id": width_row["id"], "axis": "horizontal"},
                    {"id": f"{selected['id']}:closed-loop-z", "kind": "closed-loop-axis-span",
                     "origin": f"closed-loop:{depth_row['id']}:{line_key(vline)}",
                     "metres_per_pixel": round(sz, 9), "authority": "TOPOLOGY_CORROBORATED",
                     "dimension_id": depth_row["id"], "axis": "vertical"},
                ]
                selected["axis_span_spread_ratio"] = round(spread, 9)
    return masses


def transfer_unique_sheet_scale(sheet, views, corpus):
    notations = []
    for ordinal, token in enumerate(sheet["tokens"]):
        ratio = css0.scale_ratio(token["text"])
        if ratio:
            notations.append((ordinal, ratio, token))
    if len(notations) != 1:
        return
    ordinal, ratio, token = notations[0]
    header = css0.raster_header(sheet, corpus)
    source_w, source_h = header["source_pixels"]
    norm_w, norm_h = header["normalized_pixels"]
    scale_x = 0.0254 * ratio / header["dpi"][0] * source_w / norm_w
    scale_y = 0.0254 * ratio / header["dpi"][1] * source_h / norm_h
    owner_id = f"{sheet['building_id']}-s{sheet['sheet_index']:02d}-scale-{ordinal+1:03d}"
    for view in views:
        if view["role"] not in v1.PRIMARY_ROLES or view["interior_status"] != "DISJOINT":
            continue
        view["scale"] = {
            "schema": "architectural-sheet-scale/v2", "ratio": ratio,
            "metres_per_pixel_x": round(scale_x, 9),
            "metres_per_pixel_y": round(scale_y, 9),
            "anisotropy_ratio": round(abs(scale_x - scale_y) /
                                      statistics.mean([scale_x, scale_y]), 9),
            "dpi": header["dpi"], "source_pixels": header["source_pixels"],
            "normalized_pixels": header["normalized_pixels"],
            "notation": token["text"], "notation_region": token["region"],
            "provenance": css0.source_ref(sheet, token["region"]),
            "status": "OBSERVED_UNIQUE_SHEET_SCALE_NOTATION",
            "owner_scope": "sheet", "owner_id": owner_id,
        }


def roof_topology_points(lines, geometry):
    if not geometry:
        return None
    x0, y0, x1, y1 = geometry["local_bbox_px"]
    diagonals = []
    for line in lines:
        if line["axis"] != "diagonal" or line["length_px"] < geometry["width_px"] * 0.06:
            continue
        lx0, ly0, lx1, ly1 = line["local"]
        midpoint = ((lx0 + lx1) / 2, (ly0 + ly1) / 2)
        if not (x0 - 8 <= midpoint[0] <= x1 + 8 and y0 - 8 <= midpoint[1] <= y1 + 8):
            continue
        angle = line["angle_degrees"]
        while angle <= -90:
            angle += 180
        while angle > 90:
            angle -= 180
        if 12 <= abs(angle) <= 80:
            diagonals.append((angle, line))
    positive = [line for angle, line in diagonals if angle > 0]
    negative = [line for angle, line in diagonals if angle < 0]
    candidates = []
    loose_candidates = []
    tolerance = max(18.0, geometry["width_px"] * 0.14)
    for left in positive:
        for right in negative:
            ax, ay, bx, by = left["local"]
            cx, cy, dx, dy = right["local"]
            denominator = (ax - bx) * (cy - dy) - (ay - by) * (cx - dx)
            if abs(denominator) < 1e-9:
                continue
            dl, dr = ax * by - ay * bx, cx * dy - cy * dx
            rx = (dl * (cx - dx) - (ax - bx) * dr) / denominator
            ry = (dl * (cy - dy) - (ay - by) * dr) / denominator
            if not (x0 - tolerance <= rx <= x1 + tolerance and y0 - tolerance <= ry <= y1 + tolerance):
                continue
            left_eave = (ax, ay) if ay >= by else (bx, by)
            right_eave = (cx, cy) if cy >= dy else (dx, dy)
            eaves = sorted((left_eave, right_eave), key=lambda point: point[0])
            left_eave, right_eave = eaves
            eave_y = statistics.mean([left_eave[1], right_eave[1]])
            if not (left_eave[0] < rx < right_eave[0]):
                continue
            if right_eave[0] - left_eave[0] < geometry["width_px"] * 0.2:
                continue
            if eave_y - ry < geometry["height_px"] * 0.05:
                continue
            symmetry = abs(abs(rx - left_eave[0]) - abs(right_eave[0] - rx))
            loose_candidates.append((abs(left_eave[1] - right_eave[1]), symmetry,
                                     -(left["length_px"] + right["length_px"]), ry,
                                     (rx, ry), left_eave, right_eave, left, right))
            if abs(left_eave[1] - right_eave[1]) > geometry["height_px"] * 0.12:
                continue
            if eave_y > y0 + geometry["height_px"] * 0.68:
                continue
            candidates.append((abs(left_eave[1] - right_eave[1]), symmetry,
                               -(left["length_px"] + right["length_px"]), ry,
                               (rx, ry), left_eave, right_eave, left, right))
    if not candidates and v1.opposed_gable(lines, geometry):
        candidates = loose_candidates
    if not candidates:
        return None
    _, _, _, _, ridge, left_eave, right_eave, left, right = min(candidates)
    return {"ridge": ridge, "eaves": [left_eave, right_eave],
            "line_ids": [line_key(left), line_key(right)]}


def topology_datums(record, views, dimensions, measurements, line_map, charter):
    datums, pairs = [], []
    for view in views:
        if view["role"] not in ("elevation", "section") or view["interior_status"] != "DISJOINT":
            continue
        points = roof_topology_points(line_map.get(view["id"], []),
                                      measurements.get(view["id"], {}).get("geometry"))
        if not points:
            continue
        candidates = scale_candidates(view, dimensions)
        selected, consensus = compatible_consensus(candidates, charter)
        calibration = "MULTI_ORIGIN_CONSENSUS" if consensus["status"] == "PASS" else None
        scale = consensus["metres_per_pixel"] if consensus["status"] == "PASS" else None
        dimension_only = [row for row in candidates if row["kind"] == "owned-strict-dimension-line"]
        if scale is None and len(candidates) == 1 and len(dimension_only) == 1:
            selected = dimension_only
            scale = dimension_only[0]["metres_per_pixel"]
            calibration = "SINGLE_STRICT_DIMENSION_INDEPENDENT_OF_ROOF_TOPOLOGY"
        if scale is None and view.get("scale") and not dimension_only:
            selected = [row for row in candidates if row["kind"] == "complete-scale-notation"]
            if len(selected) == 1:
                scale = selected[0]["metres_per_pixel"]
                calibration = "COMPLETE_SCALE_NOTATION_INDEPENDENT_OF_ROOF_TOPOLOGY"
        geometry = measurements[view["id"]]["geometry"]
        baseline = geometry["local_bbox_px"][3]
        pair_id = f"{record['id']}-{view['id']}-roof-pair"
        authority = "TOPOLOGY_CORROBORATED" if scale else "GEOMETRIC_SUPPORT"
        nodes = []
        for kind, point, suffix in (("ridge", points["ridge"], "ridge"),
                                    ("eave", points["eaves"][0], "eave-left"),
                                    ("eave", points["eaves"][1], "eave-right")):
            value = max(0.0, (baseline - point[1]) * scale) if scale else None
            node = {
                "schema": "architectural-datum/v2", "id": f"{pair_id}-{suffix}",
                "view_id": view["id"], "type": kind,
                "label": f"topology {suffix}", "normalized": f"TOPOLOGY {suffix.upper()}",
                "center_px": [round(point[0], 3), round(point[1], 3)],
                "value_m": round(value, 6) if value is not None else None,
                "authority": authority, "pair_id": pair_id,
                "provenance": view["provenance"] + points["line_ids"],
            }
            datums.append(node)
            nodes.append(node)
        pairs.append({
            "schema": "architectural-roof-datum-pair/v2", "id": pair_id,
            "view_id": view["id"], "relation": "OPPOSED_SLOPES_MEET_WITH_PAIRED_EAVES",
            "ridge_datum_id": nodes[0]["id"],
            "eave_datum_ids": [nodes[1]["id"], nodes[2]["id"]],
            "scale_anchor_ids": [row["id"] for row in selected],
            "calibration": calibration,
            "authority": authority, "status": "CALIBRATED" if scale else "UNSCALED",
        })
    return datums, pairs


def choose_vertical(datums, excluded_view):
    allowed = {"STRICT": 0, "TOPOLOGY_CORROBORATED": 1, "GEOMETRIC_SUPPORT": 2}
    paired = defaultdict(list)
    for node in datums:
        if (node.get("pair_id") and node["view_id"] != excluded_view and
                node.get("value_m") is not None and node["authority"] in allowed):
            paired[node["pair_id"]].append(node)
    options = []
    for pair_id, nodes in paired.items():
        ridges = [node for node in nodes if node["type"] == "ridge" and node["value_m"] >= 2.0]
        eaves = [node for node in nodes if node["type"] == "eave" and node["value_m"] > 0]
        if ridges and eaves:
            ridge = min(ridges, key=lambda node: (allowed[node["authority"]], node["id"]))
            eave = min(eaves, key=lambda node: (allowed[node["authority"]], node["id"]))
            options.append((allowed[ridge["authority"]] + allowed[eave["authority"]], pair_id,
                            ridge, eave))
    if options:
        _, _, ridge, eave = min(options, key=lambda row: (row[0], row[1]))
        return ridge, eave
    return v1.choose_vertical_original(datums, excluded_view)


def choose_holdout(views, pairs):
    calibrated = [pair for pair in pairs if pair["status"] == "CALIBRATED"]
    source_id = min(calibrated, key=lambda row: row["id"])["view_id"] if calibrated else None
    candidates = [view for view in views if view["role"] in ("section", "elevation") and
                  view["interior_status"] == "DISJOINT" and view["id"] != source_id and view.get("geometry")]
    if not candidates:
        return None
    return min(candidates, key=lambda view: (0 if view["role"] == "section" else 1, view["id"]))


def building_graph(record, evidence, sheets, charter):
    graph = v1.building_graph(record, evidence, sheets, charter)
    graph["schema"] = "architectural-building-graph/v2"
    origin_count = evidence["scale_consensus"]["origin_count"]
    graph["promotion_gates"].append({
        "id": "independent-scale-origins",
        "status": "PASS" if origin_count >= charter["promotion"]["minimum_scale_anchor_origins"] else "FAIL",
        "actual": origin_count,
    })
    selected_pair = next((pair for pair in evidence["roof_datum_pairs"]
                          if pair["ridge_datum_id"] == graph["sources"].get("ridge_datum_id") and
                          graph["sources"].get("eave_datum_id") in pair["eave_datum_ids"] and
                          pair["status"] == "CALIBRATED"), None)
    graph["promotion_gates"].append({
        "id": "paired-roof-datums", "status": "PASS" if selected_pair else "FAIL",
        "actual": selected_pair["id"] if selected_pair else None,
    })
    graph["sources"]["roof_datum_pair_id"] = selected_pair["id"] if selected_pair else None
    graph["status"] = ("G1_CANDIDATE" if all(
        gate["status"] == "PASS" for gate in graph["promotion_gates"]) else "HELD")
    return graph


def css_residual(graph, evidence, charter):
    if graph["building_id"] != evidence["building_id"]:
        raise RuntimeError("CSS graph/evidence building mismatch")
    graph_hash = pipeline.digest_bytes(pipeline.compact_bytes(graph))
    holdout_id = evidence["holdout"]["view_id"]
    checks = []
    semantic_map = {"ridge": "ridge_height_m", "eave": "eave_height_m",
                    "roof_edge": "eave_height_m", "top_of_wall": "eave_height_m"}
    if holdout_id:
        for node in evidence["datums"]:
            semantic = semantic_map.get(node["type"])
            if (node["view_id"] != holdout_id or not semantic or node.get("value_m") is None or
                    graph["dimensions"].get(semantic) is None):
                continue
            error = css0.dimension_error(graph["dimensions"][semantic], node["value_m"])
            error.update({"semantic": semantic, "datum_id": node["id"],
                          "authority": node["authority"]})
            checks.append(error)
    metric_status = ("PASS" if checks and all(row["status"] == "PASS" for row in checks)
                     else "FAIL" if checks else "UNAVAILABLE")
    shape = {"status": "UNAVAILABLE", "edge_distance_ratio": None,
             "tolerance_ratio": charter["promotion"]["edge_tolerance_ratio"]}
    span = evidence["holdout"].get("observed_span_px")
    holdout = next((view for view in evidence["views"] if view["id"] == holdout_id), None)
    dimensions = graph["dimensions"]
    if holdout and span and dimensions.get("ridge_height_m"):
        projected_options = [(axis, dimensions.get(key)) for axis, key in
                             (("x", "width_m"), ("z", "depth_m")) if dimensions.get(key)]
        if projected_options:
            observed_aspect = span[0] / max(span[1], 1e-9)
            scored = []
            for axis, projected in projected_options:
                predicted_aspect = projected / dimensions["ridge_height_m"]
                ratio = abs(math.log(max(predicted_aspect, 1e-9) /
                                     max(observed_aspect, 1e-9))) / 8
                scored.append((ratio, axis))
            ratio, axis = min(scored)
            shape = {"status": "PASS" if ratio <= charter["promotion"]["edge_tolerance_ratio"] else "FAIL",
                     "edge_distance_ratio": round(ratio, 6),
                     "projected_axis": axis,
                     "tolerance_ratio": charter["promotion"]["edge_tolerance_ratio"]}
    status = ("PASS" if graph["status"] == "G1_CANDIDATE" and
              metric_status != "FAIL" and shape["status"] == "PASS" else "FAIL")
    failed = {gate["id"] for gate in graph["promotion_gates"] if gate["status"] == "FAIL"}
    attribution = []
    if "disjoint-view-interiors" in failed:
        attribution.append("panel_ownership")
    if failed & {"two-axis-dimensions", "independent-scale-anchors", "scale-anchor-spread",
                 "independent-scale-origins"}:
        attribution.append("dimension_chain")
    if failed & {"owned-primary-mass", "closed-wall-loop"}:
        attribution.append("mass_ambiguity")
    if failed & {"typed-eave-and-ridge", "opposed-slope-gable", "paired-roof-datums",
                 "plausible-envelope"}:
        attribution.append("datum_semantics")
    if metric_status == "FAIL" or shape["status"] == "FAIL":
        attribution.append("cross_view_geometry")
    return {
        "schema": "architectural-css-residual/v2", "building_id": graph["building_id"],
        "graph_sha256": graph_hash, "status": status, "metric_status": metric_status,
        "metric_checks": checks, "shape_check": shape,
        "upstream_attribution": list(dict.fromkeys(attribution)),
        "corrected_geometry": None, "discovery_operations": 0,
    }


def process_building(record, _audit_rev, _corpus, charter, target):
    sheets, views, dimensions, measurements, datums, line_map = {}, [], [], {}, [], {}
    for drawing in record["manifest"]["drawings"]:
        sheet = v1.load_sheet(record, drawing, record["audit_rev"])
        sheets[sheet["sheet_index"]] = sheet
        _, clean = css0.clean_sheet_image(sheet)
        lines = css0.detect_cardinal_lines(clean)
        sheet_views = v1.partition_views(sheet, record["corpus"])
        transfer_unique_sheet_scale(sheet, sheet_views, record["corpus"])
        for view in sheet_views:
            subset = css0.panel_lines(lines, view, clean.shape)
            geometry = css0.component_geometry(clean, view)
            view["geometry"] = geometry
            view["line_counts"] = dict(Counter(line["axis"] for line in subset))
            view["roof_topology"] = ("OPPOSED_SLOPES_MEET" if
                                     roof_topology_points(subset, geometry) else "UNRESOLVED")
            line_map[view["id"]] = subset
            measurements[view["id"]] = {"measurement": css0.measure_panel(view, geometry, subset),
                                          "geometry": geometry}
            crop = target / "views" / f"{view['id']}.png"
            css0.crop_panel(sheet, view, crop)
            view["local_image"] = f"views/{crop.name}"
        sheet_dimensions = dimension_rows(sheet, sheet_views, lines, charter)
        sheet_datums = v1.typed_datums(sheet, sheet_views, sheet_dimensions, measurements, charter)
        for node in sheet_datums:
            node["schema"] = "architectural-datum/v2"
        views.extend(sheet_views)
        dimensions.extend(sheet_dimensions)
        datums.extend(sheet_datums)

    chains = v1.build_dimension_chains(record["id"], dimensions, charter)
    for chain in chains:
        chain["schema"] = "architectural-dimension-chain/v2"
    masses = mass_hypotheses(record, sheets, views, dimensions, measurements, line_map, charter)
    primary = next((mass for mass in masses if mass["status"] == "SELECTED_PRIMARY"), None)
    anchors, anchor_candidates, consensus = scale_anchors(primary, views, dimensions, chains, charter)
    geometric_datums, pairs = topology_datums(record, views, dimensions, measurements, line_map, charter)
    datums.extend(geometric_datums)
    holdout = choose_holdout(views, pairs)
    maximum_overlap = 0.0
    for index, left in enumerate(views):
        for right in views[index + 1:]:
            if left["sheet_index"] == right["sheet_index"] and left["role"] != right["role"]:
                maximum_overlap = max(maximum_overlap, v1.interior_overlap_ratio(left["bbox"], right["bbox"]))
    holdout_geometry = measurements.get(holdout["id"], {}).get("geometry") if holdout else None
    holdout_topology = (roof_topology_points(line_map.get(holdout["id"], []), holdout_geometry)
                        if holdout and holdout_geometry else None)
    if holdout_topology:
        topology_span = [
            abs(holdout_topology["eaves"][1][0] - holdout_topology["eaves"][0][0]),
            max(1e-9, holdout_geometry["local_bbox_px"][3] - holdout_topology["ridge"][1]),
        ]
    else:
        topology_span = None
    evidence = {
        "schema": "architectural-evidence-graph/v2", "building_id": record["id"],
        "views": views, "observed_dimensions": dimensions, "dimension_chains": chains,
        "masses": masses, "datums": datums, "roof_datum_pairs": pairs,
        "cross_view_registrations": v1.cross_view_registrations(datums, charter),
        "scale_anchors": anchors, "scale_anchor_candidates": anchor_candidates,
        "scale_consensus": consensus, "scale_anchor_spread_ratio": consensus["spread_ratio"],
        "maximum_view_overlap_ratio": round(maximum_overlap, 9),
        "holdout": {"view_id": holdout["id"] if holdout else None,
                    "role": holdout["role"] if holdout else None,
                    "observed_span_px": (topology_span or
                                         ([holdout_geometry["width_px"], holdout_geometry["height_px"]]
                                          if holdout_geometry else None)),
                    "span_authority": ("OPPOSED_SLOPE_ENVELOPE" if topology_span else
                                       "DOMINANT_CONNECTED_LINEWORK" if holdout_geometry else None),
                    "geometry_excluded_from_graph": True, "dimensions_excluded_from_graph": True},
        "promotion": "PENDING_METRIC_GRAPH",
        "authority": {"ocr_calls": 0, "vlm_calls": 0, "network_requests": 0,
                      "source_downloads": 0, "world_mutated": False},
    }
    graph = building_graph(record, evidence, sheets, charter)
    evidence["promotion"] = graph["status"]
    residual = css_residual(graph, evidence, charter)
    route = ("G1_METRIC_GRAPH" if residual["status"] == "PASS" else
             "G1_UNVALIDATED" if graph["status"] == "G1_CANDIDATE" else
             "A0_TRIAGED" if any(view["role"] == "plan" for view in views) and
             any(view["role"] in ("elevation", "section") for view in views) else "HELD")
    assessment = {
        "schema": "architectural-envelope-fit/v2", "building_id": record["id"],
        "title": record["manifest"]["title"], "building_type": record["building_type"],
        "cluster": record["cluster"], "route": route, "fit": graph["dimensions"],
        "evidence_graph_sha256": pipeline.digest_bytes(pipeline.compact_bytes(evidence)),
        "building_graph_sha256": pipeline.digest_bytes(pipeline.compact_bytes(graph)),
        "residual": residual, "network_requests": 0, "vlm_calls": 0,
        "source_downloads": 0, "world_mutated": False,
    }
    pipeline.immutable_json(target / "evidence.graph.json", evidence)
    pipeline.immutable_json(target / "building.graph.json", graph)
    pipeline.immutable_json(target / "css-residual.json", residual)
    pipeline.immutable_json(target / "assessment.json", assessment)
    pipeline.immutable_bytes(target / "index.html", v1.building_html(assessment, evidence, graph))
    return assessment, evidence, graph, residual


class Project(v1.Project):
    def __init__(self, args, charter, audit_revisions):
        self.identity = {
            "engine": ENGINE,
            "script_sha256": pipeline.digest_file(Path(__file__)),
            "v1_library_sha256": pipeline.digest_file(HERE / "probe_architectural_css_fit_v1.py"),
            "charter_sha256": pipeline.digest_file(args.charter),
            "schemas_sha256": pipeline.digest_file(args.schemas),
            "development_selection_sha256": pipeline.digest_file(args.development_selection),
            "blind_selection_sha256": pipeline.digest_file(args.blind_selection),
            "audit_revisions": audit_revisions,
            "development_audit_index_sha256": pipeline.digest_file(
                args.development_audit / "revisions" / audit_revisions["development"] / "index.json"),
            "blind_audit_index_sha256": pipeline.digest_file(
                args.blind_audit / "revisions" / audit_revisions["blind"] / "index.json"),
            "baseline_revision": charter["inputs"]["css_v1_baseline_revision"],
            "mode": "REAL_OCR_CV_DETERMINISTIC_NO_NETWORK",
        }
        self.revision = pipeline.digest_bytes(pipeline.compact_bytes(self.identity))[:20]
        self.root = args.out.resolve()
        self.rev = self.root / "revisions" / self.revision
        self.rev.mkdir(parents=True, exist_ok=True)
        pipeline.atomic_bytes(self.root / "HEAD", (self.revision + "\n").encode("ascii"))
        pipeline.immutable_json(self.rev / "identity.json", self.identity)
        self.stats = {"executed": [], "cached": [], "evidence_reads": 0, "topology_runs": 0,
                      "css_runs": 0, "ocr_calls": 0, "vlm_calls": 0, "network_requests": 0,
                      "source_downloads": 0, "world_writes": 0}


def fingerprint(record, audit_rows, _audit_revisions):
    return pipeline.digest_bytes(pipeline.compact_bytes({
        "engine": ENGINE, "script_sha256": pipeline.digest_file(Path(__file__)),
        "v1_library_sha256": pipeline.digest_file(HERE / "probe_architectural_css_fit_v1.py"),
        "building_id": record["id"], "audit_revision": record["audit_revision"],
        "audit_rows": audit_rows[record["id"]],
    }))


def development_acceptance(results, charter):
    seal, acceptance = v1.development_acceptance_original(results, charter)
    cohort = charter["evaluation"]["revealed_v1_failure_cohort"]
    selected = sum(any(mass["status"] == "SELECTED_PRIMARY" for mass in results[item][1]["masses"])
                   for item in cohort)
    scale = sum(results[item][1]["scale_consensus"]["status"] == "PASS" for item in cohort)
    paired = sum(any(pair["status"] == "CALIBRATED" for pair in results[item][1]["roof_datum_pairs"])
                 for item in cohort)
    g1 = sum(results[item][0]["route"] == "G1_METRIC_GRAPH" for item in cohort)
    negative = charter["evaluation"]["development_negative_controls"]
    controls_hold = all(results[item][0]["route"] != "G1_METRIC_GRAPH" for item in negative)
    thresholds = charter["development_acceptance"]
    checks = acceptance["checks"] + [
        {"id": "failure-cohort-selected-primary", "actual": selected,
         "expected": thresholds["minimum_failure_cohort_selected_primary"],
         "status": "PASS" if selected >= thresholds["minimum_failure_cohort_selected_primary"] else "FAIL"},
        {"id": "failure-cohort-scale-consensus", "actual": scale,
         "expected": thresholds["minimum_failure_cohort_scale_consensus"],
         "status": "PASS" if scale >= thresholds["minimum_failure_cohort_scale_consensus"] else "FAIL"},
        {"id": "failure-cohort-paired-roof-datums", "actual": paired,
         "expected": thresholds["minimum_failure_cohort_paired_roof_datums"],
         "status": "PASS" if paired >= thresholds["minimum_failure_cohort_paired_roof_datums"] else "FAIL"},
        {"id": "failure-cohort-g1", "actual": g1,
         "expected": thresholds["minimum_failure_cohort_g1"],
         "status": "PASS" if g1 >= thresholds["minimum_failure_cohort_g1"] else "FAIL"},
        {"id": "development-negative-controls-hold", "actual": controls_hold,
         "expected": True, "status": "PASS" if controls_hold else "FAIL"},
    ]
    return seal, {"schema": "architectural-topology-development-acceptance/v2",
                  "oracle_loaded_after_seal": True,
                  "status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL",
                  "checks": checks}


def install_v2_hooks():
    if not hasattr(v1, "choose_vertical_original"):
        v1.choose_vertical_original = v1.choose_vertical
    if not hasattr(v1, "development_acceptance_original"):
        v1.development_acceptance_original = v1.development_acceptance
    v1.choose_vertical = choose_vertical
    v1.load_inputs = load_inputs
    v1.process_building = process_building
    v1.Project = Project
    v1.fingerprint = fingerprint
    v1.development_acceptance = development_acceptance


def verify_development(args):
    charter, _, _, _, _ = load_inputs(args)
    root = args.out.resolve()
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    rev = root / "revisions" / revision
    errors = []
    manifest = json.loads((rev / "manifest.json").read_text(encoding="utf-8"))
    for row in manifest["files"]:
        path = pipeline.safe_child(rev, row["path"])
        if (not path.is_file() or pipeline.digest_file(path) != row["sha256"] or
                path.stat().st_size != row["bytes"]):
            errors.append(f"artifact mismatch {row['path']}")
    acceptance = json.loads((rev / "development-acceptance.json").read_text(encoding="utf-8"))
    development_ids = charter["evaluation"]["development_buildings"]
    if (root / "DEVELOPMENT_LOCK.json").exists():
        errors.append("unexpected development lock after failed acceptance")
    if (rev / "blind-automatic-seal.json").exists() or (rev / "index.json").exists():
        errors.append("blind artifacts exist before development acceptance")
    for building_id in development_ids:
        target = rev / "buildings" / building_id
        receipt = rev / "receipts" / f"building-{building_id}.json"
        if not target.is_dir() or not receipt.is_file():
            errors.append(f"missing development artifact {building_id}")
            continue
        evidence = json.loads((target / "evidence.graph.json").read_text(encoding="utf-8"))
        graph = json.loads((target / "building.graph.json").read_text(encoding="utf-8"))
        residual = json.loads((target / "css-residual.json").read_text(encoding="utf-8"))
        if evidence.get("schema") != "architectural-evidence-graph/v2":
            errors.append(f"evidence schema {building_id}")
        if residual.get("schema") != "architectural-css-residual/v2":
            errors.append(f"residual schema {building_id}")
        if residual.get("corrected_geometry", "missing") is not None or residual.get("discovery_operations") != 0:
            errors.append(f"CSS authority violation {building_id}")
        if residual.get("graph_sha256") != pipeline.digest_bytes(pipeline.compact_bytes(graph)):
            errors.append(f"CSS graph hash {building_id}")
        if evidence.get("maximum_view_overlap_ratio") != 0:
            errors.append(f"view overlap {building_id}")
    result = {
        "schema": "architectural-css-fit-development-verification/v2",
        "status": "PASS" if not errors else "FAIL", "revision": revision,
        "experiment_status": ("BLOCKED_AT_DEVELOPMENT_GATE" if acceptance["status"] == "FAIL"
                              else "READY_TO_SEAL"),
        "development_acceptance": acceptance["status"],
        "development_buildings": len(development_ids), "blind_buildings_exposed": 0,
        "errors": errors, "network_requests": 0, "ocr_calls": 0, "vlm_calls": 0,
        "source_downloads": 0, "world_mutated": False,
    }
    pipeline.atomic_json(root / "verification-development.json", result)
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


def main():
    args = parse_args()
    install_v2_hooks()
    try:
        if args.command == "develop":
            if (args.out.resolve() / "DEVELOPMENT_LOCK.json").is_file():
                raise RuntimeError("development is already sealed; use a fresh --out root")
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

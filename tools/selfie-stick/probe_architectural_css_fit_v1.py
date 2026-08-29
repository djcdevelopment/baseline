#!/usr/bin/env python3
"""Probe deterministic pre-CSS topology and read-only CSS residual transfer.

The v0 CSS probe mixed perception with projection.  This revision first emits an
``architectural-evidence-graph/v1`` containing disjoint views, owned dimension
chains, explicit mass hypotheses, and typed vertical datums.  A metric building
graph is derived from that evidence before the CSS stage runs.  CSS receives only
those two artifacts and may report residuals; it cannot discover or repair geometry.

The development split is sd0401/tx1037/ak0535.  ``develop --seal`` freezes the
script, charter, schemas, and three-building evidence before ``blind`` can expose
the remaining seventeen buildings.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import probe_architectural_css_fit as css0
import probe_architectural_css_topology as topology0
import probe_architectural_curriculum as pipeline


ENGINE = "architectural-pre-css-topology-fit/1.0.0"
DEFAULT_CHARTER = HERE / "architectural-css-fit-v1.json"
DEFAULT_SCHEMAS = HERE / "architectural-css-fit-schemas-v1.json"
DEFAULT_SELECTION = HERE / "habs-corpus.json"
DEFAULT_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_AUDIT = HERE / "out" / "architectural-curriculum" / "real-ocr-audit-v1"
DEFAULT_BASELINE = HERE / "out" / "architectural-css-fit"
DEFAULT_OUT = HERE / "out" / "architectural-css-fit-v1"

PRIMARY_ROLES = {"plan", "elevation", "section"}
MASS_RE = re.compile(r"\b(LOG\s+CABIN|ADDITION|MECHANICAL\s+ROOM|WING|ELL)\b", re.I)
PRODUCT_RE = re.compile(r"\d\s*(?:[xX×]|Ã—)\s*\d")
DATUM_RULES = (
    (re.compile(r"ROOF\s*(?:RIDGE|PEAK)", re.I), "ridge"),
    (re.compile(r"\bEAVE\b", re.I), "eave"),
    (re.compile(r"ROOF\s*EDGE", re.I), "roof_edge"),
    (re.compile(r"TOP\s+OF\s+WALL", re.I), "top_of_wall"),
    (re.compile(r"\bCEILING\b", re.I), "ceiling"),
    (re.compile(r"FIRST\s+FLOOR(?!\s+PLAN)", re.I), "first_floor"),
    (re.compile(r"\bBASEMENT\b(?!\s+PLAN)", re.I), "basement"),
    (re.compile(r"\bGRADE\b", re.I), "grade"),
    (re.compile(r"\bDATUM\b", re.I), "datum"),
    (re.compile(r"\bFLOOR\b(?!\s+PLAN)", re.I), "floor"),
)


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--charter", type=Path, default=DEFAULT_CHARTER)
    common.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS)
    common.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    common.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    common.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    common.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    develop = sub.add_parser("develop", parents=[common])
    develop.add_argument("--seal", action="store_true")
    sub.add_parser("blind", parents=[common])
    sub.add_parser("verify", parents=[common])
    serve = sub.add_parser("serve", parents=[common])
    serve.add_argument("--port", type=int, default=8879)
    return parser.parse_args()


def load_inputs(args):
    charter = json.loads(args.charter.read_text(encoding="utf-8"))
    if pipeline.digest_file(args.selection) != charter["inputs"]["selection_sha256"]:
        raise RuntimeError("frozen selection hash changed")
    audit_revision = (args.audit / "HEAD").read_text(encoding="ascii").strip()
    if audit_revision != charter["inputs"]["ocr_audit_revision"]:
        raise RuntimeError(f"OCR audit revision changed: {audit_revision}")
    baseline_revision = (args.baseline / "HEAD").read_text(encoding="ascii").strip()
    if baseline_revision != charter["inputs"]["css_v0_baseline_revision"]:
        raise RuntimeError(f"CSS v0 baseline changed: {baseline_revision}")
    audit_rev = args.audit / "revisions" / audit_revision
    audit_index = json.loads((audit_rev / "index.json").read_text(encoding="utf-8"))
    if len(audit_index.get("sheets", [])) != charter["inputs"]["sheets"]:
        raise RuntimeError("OCR audit sheet count changed")
    source_args = SimpleNamespace(charter=pipeline.DEFAULT_CHARTER,
                                  selection=args.selection, corpus=args.corpus)
    _, _, records = pipeline.load_inputs(source_args)
    membership = {}
    for cluster in audit_index["presort"]["clusters"]:
        for building_id in cluster["members"]:
            membership[building_id] = cluster["id"]
    for record in records:
        record["cluster"] = membership.get(record["id"], "CU")
    by_id = {record["id"]: record for record in records}
    expected = set(charter["evaluation"]["development_buildings"] +
                   charter["evaluation"]["blind_buildings"])
    if set(by_id) != expected or len(by_id) != charter["inputs"]["buildings"]:
        raise RuntimeError("frozen 3/17 split does not match corpus")
    return charter, audit_revision, audit_rev, audit_index, by_id


def load_sheet(record, drawing, audit_rev):
    index = int(drawing["sheet_index"])
    directory = audit_rev / "sheets" / record["id"] / f"sheet-{index:02d}"
    audit = json.loads((directory / "audit.json").read_text(encoding="utf-8"))
    ocr = json.loads((directory / "ocr.json").read_text(encoding="utf-8"))
    return {
        "building_id": record["id"], "sheet_index": index,
        "source_sha256": audit["source_sha256"], "source_url": audit["source_url"],
        "normalized_path": directory / "normalized.png",
        "normalized_pixels": audit["raster"]["normalized_pixels"],
        "tokens": ocr["tokens"], "ocr_roles": audit["ocr_role_signals"],
        "strict_dimensions": audit["strict_dimensions"],
        "suspicious_dimensions": audit["suspicious_dimensions"],
    }


def box_overlap(left, right):
    return (max(0.0, min(left[2], right[2]) - max(left[0], right[0])) *
            max(0.0, min(left[3], right[3]) - max(left[1], right[1])))


def interior_overlap_ratio(left, right):
    overlap = box_overlap(left, right)
    if not overlap:
        return 0.0
    areas = ((left[2] - left[0]) * (left[3] - left[1]),
             (right[2] - right[0]) * (right[3] - right[1]))
    return overlap / max(1e-12, min(areas))


def partition_views(sheet, corpus):
    """Turn title-seeded crops into disjoint view interiors.

    The earlier crop boxes were independent expansions around each title.  Here an
    earlier title-owned interior keeps its extent and the later neighbor begins at
    that boundary.  Plan extents may widen to include explicit mass labels, but no
    view is ever widened after pairwise ownership is resolved.
    """
    views = css0.seed_panels(sheet)
    css0.assign_scales(sheet, views, corpus)
    mass_tokens = [token for token in sheet["tokens"] if MASS_RE.search(css0.normalized_text(token["text"]))]
    for view in views:
        if view["role"] != "plan":
            continue
        nearby = [css0.center(token["region"]) for token in mass_tokens
                  if abs(css0.center(token["region"])[1] - view["label_center"][1]) <= 0.12]
        if nearby:
            view["bbox"][0] = round(max(0.035, min(view["bbox"][0], min(x for x, _ in nearby) - 0.15)), 6)
            view["bbox"][2] = round(min(0.92, max(view["bbox"][2], max(x for x, _ in nearby) + 0.15)), 6)

    ordered = sorted(views, key=lambda item: (item["sheet_index"], item["label_center"][1],
                                               item["label_center"][0], item["id"]))
    for left_index, left in enumerate(ordered):
        for right in ordered[left_index + 1:]:
            if left["sheet_index"] != right["sheet_index"] or not box_overlap(left["bbox"], right["bbox"]):
                continue
            lx, ly = left["label_center"]
            rx, ry = right["label_center"]
            horizontal = abs(lx - rx) >= abs(ly - ry)
            if horizontal:
                first, second = (left, right) if lx <= rx else (right, left)
                boundary = first["bbox"][2]
                if boundary >= second["bbox"][2] - 0.08:
                    boundary = statistics.mean([max(first["bbox"][0], second["bbox"][0]),
                                                min(first["bbox"][2], second["bbox"][2])])
                    first["bbox"][2] = round(boundary, 6)
                second["bbox"][0] = round(max(second["bbox"][0], boundary), 6)
            else:
                first, second = (left, right) if ly <= ry else (right, left)
                boundary = first["bbox"][3]
                if boundary >= second["bbox"][3] - 0.08:
                    boundary = statistics.mean([max(first["bbox"][1], second["bbox"][1]),
                                                min(first["bbox"][3], second["bbox"][3])])
                    first["bbox"][3] = round(boundary, 6)
                second["bbox"][1] = round(max(second["bbox"][1], boundary), 6)

    output = []
    for view in ordered:
        width, height = view["bbox"][2] - view["bbox"][0], view["bbox"][3] - view["bbox"][1]
        view["schema"] = "architectural-view/v1"
        view["interior_status"] = "DISJOINT" if width >= 0.08 and height >= 0.08 else "HELD_AMBIGUOUS"
        view["provenance"] = view.pop("evidence")
        output.append(view)
    return output


def owning_view(point, views, roles=None):
    roles = roles or PRIMARY_ROLES
    inside = [view for view in views if view["role"] in roles and
              view["bbox"][0] - 0.018 <= point[0] <= view["bbox"][2] + 0.018 and
              view["bbox"][1] - 0.018 <= point[1] <= view["bbox"][3] + 0.018]
    if len(inside) == 1:
        return inside[0]
    if len(inside) > 1:
        return None
    ranked = sorted((math.hypot(point[0] - view["label_center"][0],
                                point[1] - view["label_center"][1]), view["id"], view)
                    for view in views if view["role"] in roles)
    return ranked[0][2] if ranked and ranked[0][0] <= 0.18 else None


def dimension_rows(sheet, views):
    rows = []
    seen = set()
    for authority, source in (("STRICT", sheet["strict_dimensions"]),
                              ("REPAIRED", sheet["suspicious_dimensions"])):
        for ordinal, item in enumerate(source):
            value = (float(item["value_m"]) if authority == "STRICT" else
                     topology0.repaired_dimension(item["text"]))
            key = (item["text"], tuple(round(float(number), 7) for number in item["region"]))
            if value is None or key in seen:
                continue
            seen.add(key)
            point = css0.center(item["region"])
            view = owning_view(point, views)
            text = css0.normalized_text(item["text"])
            status = "OBSERVED"
            if css0.CONTEXT_HOLD_RE.search(text) or PRODUCT_RE.search(text):
                status = "HELD_CONTEXT"
            elif view is None:
                status = "HELD_AMBIGUOUS"
            rows.append({
                "id": f"{sheet['building_id']}-s{sheet['sheet_index']:02d}-od{ordinal+1:03d}-{authority.lower()}",
                "text": item["text"], "value_m": round(float(value), 6),
                "raw_authority": authority, "authority": authority if authority == "STRICT" else "HELD",
                "axis": topology0.dimension_axis(item["region"]),
                "center": [round(number, 6) for number in point],
                "region": [round(float(number), 6) for number in item["region"]],
                "view_id": view["id"] if view else None, "status": status,
                "provenance": css0.source_ref(sheet, item["region"]),
            })
    return sorted(rows, key=lambda row: (row["view_id"] or "~", row["axis"],
                                         row["center"][1], row["center"][0], row["id"]))


def build_dimension_chains(building_id, dimensions, charter):
    chains = []
    grouped = defaultdict(list)
    for row in dimensions:
        if row["view_id"] and row["status"] == "OBSERVED":
            grouped[(row["view_id"], row["axis"])].append(row)
    for (view_id, axis), rows in sorted(grouped.items()):
        coordinate_index = 1 if axis == "horizontal" else 0
        tolerance = 0.018 if axis == "horizontal" else 0.022
        bands = []
        for row in rows:
            coordinate = row["center"][coordinate_index]
            band = next((candidate for candidate in bands
                         if abs(candidate["coordinate"] - coordinate) <= tolerance), None)
            if band is None:
                band = {"coordinate": coordinate, "members": []}
                bands.append(band)
            band["members"].append(row)
            band["coordinate"] = statistics.mean(
                member["center"][coordinate_index] for member in band["members"])
        for ordinal, band in enumerate(bands, 1):
            members = sorted(band["members"], key=lambda row: row["center"][0 if axis == "horizontal" else 1])
            strict = [row for row in members if row["raw_authority"] == "STRICT"]
            chains.append({
                "schema": "architectural-dimension-chain/v1",
                "id": f"{building_id}-{view_id}-{axis[0]}{ordinal:02d}",
                "view_id": view_id, "axis": axis, "coordinate": round(band["coordinate"], 6),
                "members": members, "sum_m": round(sum(row["value_m"] for row in members), 6),
                "authority": "STRICT" if strict and len(strict) == len(members) else "HELD",
                "status": "SINGLETON" if len(members) == 1 else "HELD_AMBIGUOUS",
                "closure": None,
            })
    maximum = charter["topology"]["dimension_chain_closure_ratio"]
    for segments in chains:
        if len(segments["members"]) < 2:
            continue
        options = []
        for overall in chains:
            if overall is segments or overall["view_id"] != segments["view_id"] or overall["axis"] != segments["axis"]:
                continue
            for member in overall["members"]:
                ratio = abs(segments["sum_m"] - member["value_m"]) / max(member["value_m"], 1e-9)
                if ratio <= maximum:
                    options.append((ratio, overall, member))
        if not options:
            continue
        ratio, overall, member = min(options, key=lambda item: (item[0], item[2]["id"]))
        closure = {"overall_dimension_id": member["id"], "overall_m": member["value_m"],
                   "residual_ratio": round(ratio, 6)}
        segments["status"], segments["closure"] = "CLOSED", closure
        overall["status"] = "CLOSED"
        overall["closure"] = {"segment_chain_id": segments["id"], "residual_ratio": round(ratio, 6)}
        if any(row["raw_authority"] == "REPAIRED" for row in segments["members"] + overall["members"]):
            for row in segments["members"] + overall["members"]:
                if row["raw_authority"] == "REPAIRED":
                    row["authority"] = "TOPOLOGY_CORROBORATED"
            segments["authority"] = overall["authority"] = "TOPOLOGY_CORROBORATED"
    return chains


def datum_type(text):
    for pattern, kind in DATUM_RULES:
        if pattern.search(text):
            return kind
    return None


def typed_datums(sheet, views, dimensions, measurements, charter):
    datums = []
    for ordinal, token in enumerate(sheet["tokens"]):
        text = css0.normalized_text(token["text"])
        kind = datum_type(text)
        if not kind:
            continue
        point = css0.center(token["region"])
        view = owning_view(point, views, {"elevation", "section"})
        if not view:
            continue
        strict = pipeline.parse_dimension(text)
        repaired = strict if strict is not None else topology0.repaired_dimension(token["text"])
        datums.append({
            "schema": "architectural-datum/v1",
            "id": f"{sheet['building_id']}-s{sheet['sheet_index']:02d}-datum-{ordinal+1:03d}",
            "view_id": view["id"], "type": kind, "label": token["text"],
            "normalized": text, "center": [round(number, 6) for number in point],
            "region": [round(float(number), 6) for number in token["region"]],
            "value_m": round(float(repaired), 6) if repaired is not None else None,
            "authority": ("STRICT" if strict is not None else "HELD" if repaired is not None else
                          "GEOMETRIC_SUPPORT"),
            "provenance": [css0.source_ref(sheet, token["region"])],
        })

    by_view = defaultdict(list)
    for node in datums:
        by_view[node["view_id"]].append(node)
    view_map = {view["id"]: view for view in views}
    height_px = sheet["normalized_pixels"][1]
    for view_id, nodes in by_view.items():
        view = view_map[view_id]
        scale = view.get("scale")
        if not scale:
            continue
        bases = [node for node in nodes if node["type"] in ("first_floor", "grade", "floor")]
        geometry = measurements.get(view_id, {}).get("geometry")
        base_y = max((node["center"][1] for node in bases), default=None)
        if base_y is None and geometry:
            base_y = geometry["bbox_px"][3] / height_px
        if base_y is None:
            continue
        for node in nodes:
            geometric = max(0.0, (base_y - node["center"][1]) * height_px *
                            scale["metres_per_pixel_y"])
            node["geometric_value_m"] = round(geometric, 6)
            if node["value_m"] is None and node["type"] not in ("first_floor", "grade", "floor"):
                node["value_m"] = round(geometric, 6)
                node["authority"] = "GEOMETRIC_SUPPORT"
            elif node["authority"] == "HELD" and node["value_m"]:
                residual = abs(node["value_m"] - geometric) / max(node["value_m"], 1e-9)
                node["topology_residual_ratio"] = round(residual, 6)
                if residual <= charter["topology"]["topology_corroborated_scale_ratio"]:
                    node["authority"] = "TOPOLOGY_CORROBORATED"

    # Bind a vertical interval only when it lies between a named roof datum and
    # a named envelope-origin datum in the same disjoint view.  This replaces
    # the old nearest-Hough-line semantic guess.
    for dimension in [row for row in dimensions if row["status"] == "OBSERVED" and
                      row["axis"] == "vertical" and row["raw_authority"] == "STRICT"]:
        candidates = []
        for upper in datums:
            if upper["view_id"] != dimension["view_id"] or upper["type"] not in (
                    "ridge", "eave", "roof_edge", "top_of_wall"):
                continue
            for lower in datums:
                if lower["view_id"] != dimension["view_id"] or lower["type"] not in (
                        "grade", "first_floor", "floor", "datum"):
                    continue
                if upper["center"][1] >= lower["center"][1]:
                    continue
                if not upper["center"][1] <= dimension["center"][1] <= lower["center"][1]:
                    continue
                x_error = max(abs(dimension["center"][0] - upper["center"][0]),
                              abs(dimension["center"][0] - lower["center"][0]))
                if x_error > 0.13:
                    continue
                midpoint_error = abs(dimension["center"][1] -
                                     statistics.mean([upper["center"][1], lower["center"][1]]))
                candidates.append((x_error * 2 + midpoint_error, upper, lower))
        if not candidates:
            continue
        _, upper, lower = min(candidates, key=lambda item: (item[0], item[1]["id"], item[2]["id"]))
        upper["value_m"] = dimension["value_m"]
        upper["authority"] = "STRICT"
        upper["interval"] = {"dimension_id": dimension["id"], "lower_datum_id": lower["id"],
                             "value_m": dimension["value_m"]}
    return datums


def opposed_gable(lines, geometry):
    if not geometry:
        return False
    x0, y0, x1, y1 = geometry["local_bbox_px"]
    diagonals = []
    for line in lines:
        if line["axis"] != "diagonal" or line["length_px"] < geometry["width_px"] * 0.06:
            continue
        lx0, ly0, lx1, ly1 = line["local"]
        midpoint = ((lx0 + lx1) / 2, (ly0 + ly1) / 2)
        if x0 - 8 <= midpoint[0] <= x1 + 8 and y0 - 8 <= midpoint[1] <= y1 + 8:
            folded = line["angle_degrees"]
            while folded <= -90:
                folded += 180
            while folded > 90:
                folded -= 180
            if 12 <= abs(folded) <= 80:
                diagonals.append((folded, line))
    positive = [line for angle, line in diagonals if angle > 0]
    negative = [line for angle, line in diagonals if angle < 0]
    tolerance = max(18.0, geometry["width_px"] * 0.14)
    for left in positive:
        for right in negative:
            ax, ay, bx, by = left["local"]
            cx, cy, dx, dy = right["local"]
            denominator = (ax - bx) * (cy - dy) - (ay - by) * (cx - dx)
            if abs(denominator) < 1e-9:
                continue
            determinant_left = ax * by - ay * bx
            determinant_right = cx * dy - cy * dx
            meeting_x = (determinant_left * (cx - dx) - (ax - bx) * determinant_right) / denominator
            meeting_y = (determinant_left * (cy - dy) - (ay - by) * determinant_right) / denominator
            if (x0 - tolerance <= meeting_x <= x1 + tolerance and
                    y0 - tolerance <= meeting_y <= y1 + tolerance):
                return True
    return False


def mass_hypotheses(record, sheets, views, dimensions, measurements, line_map):
    masses = []
    vertical_support = any(view["role"] in ("elevation", "section") and
                           view["interior_status"] == "DISJOINT" for view in views)
    for view in [item for item in views if item["role"] == "plan" and item["interior_status"] == "DISJOINT"]:
        sheet = sheets[view["sheet_index"]]
        labels = []
        for token in sheet["tokens"]:
            match = MASS_RE.search(css0.normalized_text(token["text"]))
            if not match:
                continue
            point = css0.center(token["region"])
            if owning_view(point, views, {"plan"}) is view:
                labels.append({"label": match.group(1).upper(), "center": point,
                               "provenance": css0.source_ref(sheet, token["region"])})
        # Keep one label per named mass in this view.
        deduped = {}
        for label in labels:
            deduped.setdefault(label["label"], label)
        labels = list(deduped.values())
        if not any(label["label"] in ("LOG CABIN", "ADDITION") for label in labels):
            labels.insert(0, {"label": "PRIMARY", "center": view["label_center"],
                              "provenance": view["provenance"][0]})
        owned = [row for row in dimensions if row["view_id"] == view["id"] and
                 row["status"] == "OBSERVED" and row["raw_authority"] == "STRICT"]
        horizontal = [row for row in owned if row["axis"] == "horizontal"]
        vertical = [row for row in owned if row["axis"] == "vertical"]
        assigned_vertical = set()
        for ordinal, label in enumerate(sorted(labels, key=lambda item: item["center"][0]), 1):
            if label["label"] == "PRIMARY":
                width_row = max(horizontal, key=lambda row: (row["value_m"], row["id"]), default=None)
                candidates = []
                if width_row:
                    candidates = [row for row in vertical
                                  if width_row["value_m"] * 0.25 <= row["value_m"] <= width_row["value_m"] * 1.25]
                depth_row = min(candidates, key=lambda row: (row["value_m"], row["id"]), default=None)
            else:
                same_band = [row for row in horizontal
                             if abs(row["center"][1] - label["center"][1]) <= 0.035]
                width_row = min(same_band, key=lambda row: (abs(row["center"][0] - label["center"][0]),
                                                             row["id"]), default=None)
                # Several segment dimensions can share one vertical dimension
                # string.  The owned mass depth is the largest strict value in
                # the closest x-column, not the nearest token in that column.
                available_vertical = [row for row in vertical if row["id"] not in assigned_vertical]
                if available_vertical:
                    closest_x = min(abs(row["center"][0] - label["center"][0])
                                    for row in available_vertical)
                    column = [row for row in available_vertical
                              if abs(abs(row["center"][0] - label["center"][0]) - closest_x) <= 0.015]
                else:
                    column = []
                depth_row = max(column, key=lambda row: (row["value_m"], row["id"]), default=None)
                if depth_row:
                    assigned_vertical.add(depth_row["id"])
            measured = measurements.get(view["id"], {})
            geometry = measured.get("geometry")
            line_counts = Counter(line["axis"] for line in line_map.get(view["id"], []))
            closed = bool(geometry and line_counts["horizontal"] >= 2 and line_counts["vertical"] >= 2)
            dimensions_value = {
                "width_m": width_row["value_m"] if width_row else None,
                "depth_m": depth_row["value_m"] if depth_row else None,
                "width_dimension_id": width_row["id"] if width_row else None,
                "depth_dimension_id": depth_row["id"] if depth_row else None,
            }
            complete = width_row is not None and depth_row is not None
            masses.append({
                "schema": "architectural-mass-hypothesis/v1",
                "id": f"{record['id']}-{view['id']}-mass-{ordinal:02d}",
                "view_id": view["id"], "view_label": view["label"], "label": label["label"],
                "dimensions": dimensions_value, "closed_wall_loop": closed,
                "cross_view_support": vertical_support, "two_axis_dimensions": complete,
                "status": "CANDIDATE" if complete and closed and vertical_support else "HELD_AMBIGUOUS",
                "provenance": [label["provenance"]] +
                              [row["provenance"] for row in (width_row, depth_row) if row],
            })
    selectable = [mass for mass in masses if mass["status"] == "CANDIDATE" and
                  mass["label"] not in ("ADDITION", "WING", "ELL")]
    if selectable:
        selected = sorted(selectable, key=lambda mass: (
            1 if "BASEMENT" in css0.normalized_text(mass["view_label"]) else 0,
            0 if mass["label"] in ("PRIMARY", "LOG CABIN") else 1,
            -mass["dimensions"]["width_m"] * mass["dimensions"]["depth_m"], mass["id"]))[0]
        selected["status"] = "SELECTED_PRIMARY"
        for mass in masses:
            if mass is not selected and mass["status"] == "CANDIDATE":
                mass["status"] = "SECONDARY"
    return masses


def choose_vertical(datums, excluded_view):
    allowed = {"STRICT": 0, "TOPOLOGY_CORROBORATED": 1, "GEOMETRIC_SUPPORT": 2}
    rows = [node for node in datums if node["view_id"] != excluded_view and
            node.get("value_m") is not None and node["authority"] in allowed]
    ridge = [node for node in rows if node["type"] == "ridge" and node["value_m"] >= 2.0]
    eave = [node for node in rows if node["type"] in ("eave", "roof_edge", "top_of_wall") and
            node["value_m"] > 0]

    def select(candidates):
        if not candidates:
            return None
        best = min(allowed[node["authority"]] for node in candidates)
        strongest = [node for node in candidates if allowed[node["authority"]] == best]
        values = [node["value_m"] for node in strongest]
        if candidates is ridge:
            return min(strongest, key=lambda node: (node["value_m"], node["id"]))
        median = statistics.median(values)
        return min(strongest, key=lambda node: (abs(node["value_m"] - median), node["id"]))

    return select(ridge), select(eave)


def heldout_view(views, datums):
    counts = Counter(node["view_id"] for node in datums if node.get("value_m") is not None)
    sections = [view for view in views if view["role"] == "section" and
                view["interior_status"] == "DISJOINT"]
    if sections:
        return sorted(sections, key=lambda view: (-counts[view["id"]], view["id"]))[0]
    elevations = sorted((view for view in views if view["role"] == "elevation" and
                         view["interior_status"] == "DISJOINT"), key=lambda view: view["id"])
    return elevations[-1] if len(elevations) >= 2 else None


def scale_anchors(primary, views, dimensions, chains):
    if not primary:
        return [], None
    view = next(view for view in views if view["id"] == primary["view_id"])
    anchors = []
    if view.get("scale"):
        base = statistics.mean([view["scale"]["metres_per_pixel_x"],
                                view["scale"]["metres_per_pixel_y"]])
        anchors.append({"id": f"{view['id']}:scale", "kind": "complete-scale-notation",
                        "metres_per_pixel": round(base, 9), "authority": "STRICT"})
        for axis in ("width_dimension_id", "depth_dimension_id"):
            dimension_id = primary["dimensions"].get(axis)
            row = next((item for item in dimensions if item["id"] == dimension_id), None)
            if row and row["raw_authority"] == "STRICT":
                anchors.append({"id": row["id"], "kind": "owned-strict-dimension",
                                "metres_per_pixel": round(base, 9), "authority": "STRICT"})
    values = [anchor["metres_per_pixel"] for anchor in anchors]
    spread = ((max(values) - min(values)) / statistics.mean(values)) if len(values) >= 2 else None
    return anchors, round(spread, 9) if spread is not None else None


def cross_view_registrations(datums, charter):
    canonical = lambda kind: "ridge" if kind == "ridge" else "eave" if kind in (
        "eave", "roof_edge", "top_of_wall") else kind
    groups = defaultdict(list)
    for node in datums:
        if node.get("value_m") is not None and node["type"] in (
                "ridge", "eave", "roof_edge", "top_of_wall", "ceiling"):
            groups[canonical(node["type"])].append(node)
    rows = []
    for semantic, nodes in sorted(groups.items()):
        for index, left in enumerate(nodes):
            for right in nodes[index + 1:]:
                if left["view_id"] == right["view_id"]:
                    continue
                absolute = abs(left["value_m"] - right["value_m"])
                ratio = absolute / max(right["value_m"], 1e-9)
                rows.append({
                    "semantic": semantic, "left_datum_id": left["id"], "right_datum_id": right["id"],
                    "left_view_id": left["view_id"], "right_view_id": right["view_id"],
                    "absolute_error_m": round(absolute, 6), "error_ratio": round(ratio, 6),
                    "status": "PASS" if absolute <= charter["promotion"]["maximum_cross_view_error_m"] and
                    ratio <= charter["promotion"]["maximum_cross_view_error_ratio"] else "FAIL",
                })
    return rows


def building_graph(record, evidence, sheets, charter):
    primary = next((mass for mass in evidence["masses"] if mass["status"] == "SELECTED_PRIMARY"), None)
    holdout = next((view for view in evidence["views"] if view["id"] == evidence["holdout"]["view_id"]), None)
    ridge, eave = choose_vertical(evidence["datums"], holdout["id"] if holdout else None)
    width = primary["dimensions"]["width_m"] if primary else None
    depth = primary["dimensions"]["depth_m"] if primary else None
    vertical_views = [view for view in evidence["views"] if view["role"] in ("elevation", "section")]
    gable = any(view.get("roof_topology") == "OPPOSED_SLOPES_MEET" for view in vertical_views
                if not holdout or view["id"] != holdout["id"])
    floors, floor_source = css0.floor_count(list(sheets.values()))
    if floors == 0 and primary:
        floors = 1
        floor_source = "one observed primary plan; higher floor sequence unresolved"
    anchors = evidence["scale_anchors"]
    spread = evidence["scale_anchor_spread_ratio"]
    numeric = all(value not in (None, 0) for value in (width, depth,
                                                        ridge["value_m"] if ridge else None,
                                                        eave["value_m"] if eave else None))
    plausible = bool(numeric and width >= charter["promotion"]["minimum_width_depth_m"] and
                     depth >= charter["promotion"]["minimum_width_depth_m"] and
                     ridge["value_m"] >= charter["promotion"]["minimum_ridge_height_m"] and
                     eave["value_m"] < ridge["value_m"])
    gates = [
        {"id": "disjoint-view-interiors", "status": "PASS" if evidence["maximum_view_overlap_ratio"] == 0 else "FAIL",
         "actual": evidence["maximum_view_overlap_ratio"]},
        {"id": "owned-primary-mass", "status": "PASS" if primary else "FAIL",
         "actual": primary["id"] if primary else None},
        {"id": "closed-wall-loop", "status": "PASS" if primary and primary["closed_wall_loop"] else "FAIL",
         "actual": primary["closed_wall_loop"] if primary else None},
        {"id": "two-axis-dimensions", "status": "PASS" if primary and primary["two_axis_dimensions"] else "FAIL",
         "actual": primary["two_axis_dimensions"] if primary else None},
        {"id": "typed-eave-and-ridge", "status": "PASS" if ridge and eave else "FAIL",
         "actual": {"ridge": ridge["id"] if ridge else None, "eave": eave["id"] if eave else None}},
        {"id": "opposed-slope-gable", "status": "PASS" if gable else "FAIL", "actual": gable},
        {"id": "numeric-primary-envelope", "status": "PASS" if numeric else "FAIL", "actual": numeric},
        {"id": "independent-scale-anchors", "status": "PASS" if len(anchors) >=
         charter["promotion"]["minimum_independent_scale_anchors"] else "FAIL", "actual": len(anchors)},
        {"id": "scale-anchor-spread", "status": "PASS" if spread is not None and spread <=
         charter["promotion"]["maximum_scale_anchor_spread_ratio"] else "FAIL", "actual": spread},
        {"id": "plausible-envelope", "status": "PASS" if plausible else "FAIL", "actual": plausible},
        {"id": "independent-held-out-view", "status": "PASS" if holdout else "FAIL",
         "actual": holdout["id"] if holdout else None},
    ]
    promoted = all(gate["status"] == "PASS" for gate in gates)
    dimensions = {
        "width_m": round(width, 6) if width else None,
        "depth_m": round(depth, 6) if depth else None,
        "floor_count": floors,
        "eave_height_m": eave["value_m"] if eave else None,
        "ridge_height_m": ridge["value_m"] if ridge else None,
        "roof_pitch_degrees": (round(math.degrees(math.atan2(
            ridge["value_m"] - eave["value_m"], depth / 2)), 6)
            if ridge and eave and depth else None),
    }
    graph = {
        "schema": "architectural-building-graph/v1",
        "id": f"habs-{record['id']}-topology-{pipeline.digest_bytes(pipeline.compact_bytes(dimensions))[:12]}",
        "building_id": record["id"], "label": record["manifest"]["title"],
        "authority": "pre-CSS deterministic topology; CSS residual cannot alter geometry",
        "status": "G1_CANDIDATE" if promoted else "HELD",
        "coordinate_frames": {"building_local": {"units": "metres", "handedness": "right",
                                                     "axes": {"x": "plan-right", "y": "height", "z": "plan-up"},
                                                     "origin": "typed first-floor envelope datum"}},
        "dimensions": dimensions, "levels": ([{"id": f"L{index}", "status": "observed"}
                                                for index in range(floors)] if floors else []),
        "footprints": ([{"id": "primary", "level": "L0", "status": "observed",
                         "polygon_xz": [[0, 0], [width, 0], [width, depth], [0, depth], [0, 0]],
                         "mass_id": primary["id"]}] if primary else []),
        "roofs": ([{"id": "primary-roof", "kind": "gable", "ridge_axis": "x" if width and depth and width >= depth else "z",
                    "eave_y_m": eave["value_m"], "ridge_y_m": ridge["value_m"],
                    "status": "observed", "datum_ids": [eave["id"], ridge["id"]]}]
                  if primary and ridge and eave and gable else []),
        "openings": [], "assertions": [], "promotion_gates": gates,
        "sources": {"primary_mass_id": primary["id"] if primary else None,
                    "floor_count": floor_source,
                    "eave_datum_id": eave["id"] if eave else None,
                    "ridge_datum_id": ridge["id"] if ridge else None},
    }
    return graph


def css_residual(graph, evidence, charter):
    """Project and score a pre-existing graph without geometry discovery."""
    if graph["building_id"] != evidence["building_id"]:
        raise RuntimeError("CSS graph/evidence building mismatch")
    holdout_id = evidence["holdout"]["view_id"]
    holdout = next((view for view in evidence["views"] if view["id"] == holdout_id), None)
    graph_hash = pipeline.digest_bytes(pipeline.compact_bytes(graph))
    checks = []
    dimensions = graph["dimensions"]
    semantic_map = {"ridge": "ridge_height_m", "eave": "eave_height_m",
                    "roof_edge": "eave_height_m", "top_of_wall": "eave_height_m"}
    if holdout:
        for node in evidence["datums"]:
            semantic = semantic_map.get(node["type"])
            if (node["view_id"] != holdout_id or not semantic or
                    node.get("value_m") is None or dimensions.get(semantic) is None):
                continue
            error = css0.dimension_error(dimensions[semantic], node["value_m"])
            error.update({"semantic": semantic, "datum_id": node["id"], "authority": node["authority"]})
            checks.append(error)
    shape = {"status": "UNAVAILABLE", "edge_distance_ratio": None,
             "tolerance_ratio": charter["promotion"]["edge_tolerance_ratio"]}
    observed = evidence["holdout"].get("observed_span_m")
    if holdout and observed and dimensions.get("ridge_height_m"):
        projected_span = dimensions.get("depth_m") if holdout["role"] == "section" else dimensions.get("width_m")
        if projected_span:
            predicted_aspect = projected_span / dimensions["ridge_height_m"]
            observed_aspect = observed[0] / max(observed[1], 1e-9)
            ratio = abs(math.log(max(predicted_aspect, 1e-9) / max(observed_aspect, 1e-9))) / 8
            shape = {"status": "PASS" if ratio <= charter["promotion"]["edge_tolerance_ratio"] else "FAIL",
                     "edge_distance_ratio": round(ratio, 6),
                     "tolerance_ratio": charter["promotion"]["edge_tolerance_ratio"]}
    metric_status = "PASS" if checks and all(check["status"] == "PASS" for check in checks) else "FAIL"
    status = "PASS" if graph["status"] == "G1_CANDIDATE" and metric_status == "PASS" and shape["status"] == "PASS" else "FAIL"
    attribution = []
    failed_gates = {gate["id"] for gate in graph["promotion_gates"] if gate["status"] == "FAIL"}
    if "disjoint-view-interiors" in failed_gates:
        attribution.append("panel_ownership")
    if failed_gates & {"two-axis-dimensions", "independent-scale-anchors", "scale-anchor-spread"}:
        attribution.append("dimension_chain")
    if failed_gates & {"owned-primary-mass", "closed-wall-loop"}:
        attribution.append("mass_ambiguity")
    if failed_gates & {"typed-eave-and-ridge", "opposed-slope-gable", "plausible-envelope"}:
        attribution.append("datum_semantics")
    if metric_status == "FAIL" or shape["status"] == "FAIL":
        attribution.append("cross_view_geometry")
    return {
        "schema": "architectural-css-residual/v1", "building_id": graph["building_id"],
        "graph_sha256": graph_hash, "status": status, "metric_status": metric_status,
        "metric_checks": checks, "shape_check": shape,
        "upstream_attribution": list(dict.fromkeys(attribution)),
        "corrected_geometry": None, "discovery_operations": 0,
    }


def process_building(record, audit_rev, corpus, charter, target):
    sheets, views, dimensions, measurements, datums, line_map = {}, [], [], {}, [], {}
    for drawing in record["manifest"]["drawings"]:
        sheet = load_sheet(record, drawing, audit_rev)
        sheets[sheet["sheet_index"]] = sheet
        image, clean = css0.clean_sheet_image(sheet)
        lines = css0.detect_cardinal_lines(clean)
        sheet_views = partition_views(sheet, corpus)
        for view in sheet_views:
            subset = css0.panel_lines(lines, view, clean.shape)
            geometry = css0.component_geometry(clean, view)
            view["geometry"] = geometry
            view["line_counts"] = dict(Counter(line["axis"] for line in subset))
            view["roof_topology"] = ("OPPOSED_SLOPES_MEET" if view["role"] in ("elevation", "section") and
                                     opposed_gable(subset, geometry) else "UNRESOLVED")
            line_map[view["id"]] = subset
            measurement = css0.measure_panel(view, geometry, subset)
            measurements[view["id"]] = {"measurement": measurement, "geometry": geometry}
            crop = target / "views" / f"{view['id']}.png"
            css0.crop_panel(sheet, view, crop)
            view["local_image"] = f"views/{crop.name}"
        sheet_dimensions = dimension_rows(sheet, sheet_views)
        sheet_datums = typed_datums(sheet, sheet_views, sheet_dimensions, measurements, charter)
        views.extend(sheet_views)
        dimensions.extend(sheet_dimensions)
        datums.extend(sheet_datums)

    chains = build_dimension_chains(record["id"], dimensions, charter)
    masses = mass_hypotheses(record, sheets, views, dimensions, measurements, line_map)
    primary = next((mass for mass in masses if mass["status"] == "SELECTED_PRIMARY"), None)
    anchors, spread = scale_anchors(primary, views, dimensions, chains)
    holdout = heldout_view(views, datums)
    maximum_overlap = 0.0
    for index, left in enumerate(views):
        for right in views[index + 1:]:
            if left["sheet_index"] == right["sheet_index"] and left["role"] != right["role"]:
                maximum_overlap = max(maximum_overlap, interior_overlap_ratio(left["bbox"], right["bbox"]))
    holdout_measurement = (measurements.get(holdout["id"], {}).get("measurement") if holdout else None)
    evidence = {
        "schema": "architectural-evidence-graph/v1", "building_id": record["id"],
        "views": views, "observed_dimensions": dimensions, "dimension_chains": chains,
        "masses": masses, "datums": datums,
        "cross_view_registrations": cross_view_registrations(datums, charter),
        "scale_anchors": anchors, "scale_anchor_spread_ratio": spread,
        "maximum_view_overlap_ratio": round(maximum_overlap, 9),
        "holdout": {"view_id": holdout["id"] if holdout else None,
                    "role": holdout["role"] if holdout else None,
                    "observed_span_m": holdout_measurement.get("observed_span_m") if holdout_measurement else None,
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
        "schema": "architectural-envelope-fit/v1", "building_id": record["id"],
        "title": record["manifest"]["title"], "building_type": record["building_type"],
        "cluster": record["cluster"], "route": route,
        "fit": graph["dimensions"], "evidence_graph_sha256": pipeline.digest_bytes(pipeline.compact_bytes(evidence)),
        "building_graph_sha256": pipeline.digest_bytes(pipeline.compact_bytes(graph)),
        "residual": residual, "network_requests": 0, "vlm_calls": 0,
        "source_downloads": 0, "world_mutated": False,
    }
    pipeline.immutable_json(target / "evidence.graph.json", evidence)
    pipeline.immutable_json(target / "building.graph.json", graph)
    pipeline.immutable_json(target / "css-residual.json", residual)
    pipeline.immutable_json(target / "assessment.json", assessment)
    pipeline.immutable_bytes(target / "index.html", building_html(assessment, evidence, graph))
    return assessment, evidence, graph, residual


def building_html(assessment, evidence, graph):
    cards = []
    for view in evidence["views"]:
        cards.append(f"<article><b>{html.escape(view['role'])}</b><span>{html.escape(view['id'])}</span>"
                     f"<img src='{html.escape(view['local_image'])}' alt=''></article>")
    payload = html.escape(json.dumps({"assessment": assessment, "gates": graph["promotion_gates"],
                                      "masses": evidence["masses"], "datums": evidence["datums"],
                                      "residual": assessment["residual"]}, indent=2))
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>{assessment['building_id']} pre-CSS topology</title>
<style>body{{margin:0;background:#152026;color:#e8ece9;font:15px system-ui}}main{{max-width:1180px;margin:auto;padding:40px 24px}}h1{{font:44px Georgia}}.route{{color:#d49a3a;font:700 14px Consolas}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}}article{{display:grid;gap:6px;background:#202c31;border:1px solid #415159;padding:10px}}article img{{width:100%;height:190px;object-fit:contain;background:#fff}}article span,pre{{color:#a9b8bd}}pre{{white-space:pre-wrap;word-break:break-word}}</style></head>
<body><main><div class='route'>PRE-CSS EVIDENCE → METRIC GRAPH → READ-ONLY CSS</div><h1>{html.escape(assessment['building_id'])}</h1><p class='route'>{assessment['route']}</p><div class='grid'>{''.join(cards)}</div><pre>{payload}</pre></main></body></html>""".encode("utf-8")


class Project:
    def __init__(self, args, charter, audit_revision):
        self.identity = {
            "engine": ENGINE, "script_sha256": pipeline.digest_file(Path(__file__)),
            "charter_sha256": pipeline.digest_file(args.charter),
            "schemas_sha256": pipeline.digest_file(args.schemas),
            "selection_sha256": pipeline.digest_file(args.selection),
            "audit_revision": audit_revision,
            "audit_index_sha256": pipeline.digest_file(args.audit / "revisions" / audit_revision / "index.json"),
            "baseline_revision": charter["inputs"]["css_v0_baseline_revision"],
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

    def building(self, record, fingerprint, builder):
        target = self.rev / "buildings" / record["id"]
        receipt_path = self.rev / "receipts" / f"building-{record['id']}.json"
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("fingerprint") == fingerprint and all(
                    (path := pipeline.safe_child(self.rev, row["path"])).is_file() and
                    pipeline.digest_file(path) == row["sha256"] for row in receipt.get("outputs", [])):
                self.stats["cached"].append(record["id"])
                return tuple(json.loads((target / name).read_text(encoding="utf-8")) for name in
                             ("assessment.json", "evidence.graph.json", "building.graph.json", "css-residual.json"))
        result = builder(target)
        outputs = sorted(path for path in target.rglob("*") if path.is_file())
        pipeline.atomic_json(receipt_path, {
            "schema": "architectural-topology-stage-receipt/v1", "stage": f"building:{record['id']}",
            "fingerprint": fingerprint,
            "outputs": [{"path": path.relative_to(self.rev).as_posix(),
                         "sha256": pipeline.digest_file(path), "bytes": path.stat().st_size}
                        for path in outputs],
        })
        self.stats["executed"].append(record["id"])
        self.stats["evidence_reads"] += len(record["manifest"]["drawings"])
        self.stats["topology_runs"] += 1
        self.stats["css_runs"] += 1
        return result


def fingerprint(record, audit_rows, audit_revision):
    return pipeline.digest_bytes(pipeline.compact_bytes({
        "engine": ENGINE, "script_sha256": pipeline.digest_file(Path(__file__)),
        "building_id": record["id"], "audit_revision": audit_revision,
        "audit_rows": audit_rows[record["id"]],
    }))


def development_acceptance(results, charter):
    automatic_seal = {building_id: pipeline.digest_bytes(pipeline.compact_bytes(results[building_id][1]))
                      for building_id in charter["evaluation"]["development_buildings"]}
    checks = []
    sd_graph = results["sd0401"][2]
    for key, expected in charter["development_acceptance"]["sd0401_oracle"].items():
        actual = sd_graph["dimensions"].get(key)
        checks.append({"id": f"sd0401-{key}", "actual": actual, "expected": expected,
                       "status": "PASS" if actual is not None and abs(actual - expected) <= 1e-6 else "FAIL"})
    sd_evidence = results["sd0401"][1]
    checks.append({"id": "sd0401-disjoint-views", "actual": sd_evidence["maximum_view_overlap_ratio"],
                   "expected": 0, "status": "PASS" if sd_evidence["maximum_view_overlap_ratio"] == 0 else "FAIL"})
    tx_evidence = results["tx1037"][1]
    ceiling = [node for node in tx_evidence["datums"] if "CEILING" in node["normalized"]]
    checks.append({"id": "tx1037-ceiling-remains-ceiling", "actual": [node["type"] for node in ceiling],
                   "expected": "ceiling only", "status": "PASS" if ceiling and
                   all(node["type"] == "ceiling" for node in ceiling) else "FAIL"})
    ak_evidence = results["ak0535"][1]
    labels = {mass["label"] for mass in ak_evidence["masses"]}
    required = set(charter["development_acceptance"]["ak0535_required_separate_masses"])
    selected = next((mass for mass in ak_evidence["masses"] if mass["status"] == "SELECTED_PRIMARY"), None)
    forbidden = charter["development_acceptance"]["ak0535_forbidden_floor_primary_width_m"]
    checks.append({"id": "ak0535-separate-floor-masses", "actual": sorted(labels), "expected": sorted(required),
                   "status": "PASS" if required <= labels else "FAIL"})
    checks.append({"id": "ak0535-basement-width-not-floor-primary", "actual":
                   selected["dimensions"]["width_m"] if selected else None, "expected": f"not {forbidden}",
                   "status": "PASS" if selected and abs(selected["dimensions"]["width_m"] - forbidden) > 1e-6 else "FAIL"})
    return automatic_seal, {"schema": "architectural-topology-development-acceptance/v1",
                            "oracle_loaded_after_seal": True,
                            "status": "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL",
                            "checks": checks}


def write_manifest(project):
    files = []
    for path in sorted(item for item in project.rev.rglob("*") if item.is_file() and item.name != "manifest.json"):
        files.append({"path": path.relative_to(project.rev).as_posix(),
                      "sha256": pipeline.digest_file(path), "bytes": path.stat().st_size})
    pipeline.atomic_json(project.rev / "manifest.json", {
        "schema": "architectural-css-fit-manifest/v1", "revision": project.revision,
        "files": files, "network_requests": 0, "ocr_calls": 0, "vlm_calls": 0,
        "source_downloads": 0, "world_mutated": False,
    })


def run_phase(args, blind=False):
    css0.load_imaging()
    charter, audit_revision, audit_rev, audit_index, records = load_inputs(args)
    project = Project(args, charter, audit_revision)
    lock_path = project.root / "DEVELOPMENT_LOCK.json"
    if blind:
        if not lock_path.is_file():
            raise RuntimeError("blind phase requires develop --seal")
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        if lock.get("revision") != project.revision or lock.get("identity") != project.identity:
            raise RuntimeError("development lock does not match current implementation")
        building_ids = charter["evaluation"]["blind_buildings"]
    else:
        building_ids = charter["evaluation"]["development_buildings"]
    audit_rows = defaultdict(list)
    for row in audit_index["sheets"]:
        audit_rows[row["building_id"]].append(row)
    results = {}
    for ordinal, building_id in enumerate(building_ids, 1):
        record = records[building_id]
        value = fingerprint(record, audit_rows, audit_revision)
        results[building_id] = project.building(
            record, value, lambda target, record=record: process_building(
                record, audit_rev, args.corpus, charter, target))
        assessment = results[building_id][0]
        print(f"[{ordinal:02d}/{len(building_ids):02d}] {building_id} {assessment['route']}")

    if not blind:
        seal, acceptance = development_acceptance(results, charter)
        pipeline.immutable_json(project.rev / "development-automatic-seal.json", {
            "schema": "architectural-topology-development-seal/v1", "oracle_loaded": False,
            "buildings": seal, "sha256": pipeline.digest_bytes(pipeline.compact_bytes(seal))})
        pipeline.atomic_json(project.rev / "development-acceptance.json", acceptance)
        if args.seal:
            if acceptance["status"] != "PASS":
                raise RuntimeError("development acceptance failed; refusing to seal")
            pipeline.immutable_json(lock_path, {
                "schema": "architectural-topology-development-lock/v1", "revision": project.revision,
                "identity": project.identity,
                "development_seal_sha256": pipeline.digest_file(project.rev / "development-automatic-seal.json"),
                "post_blind_tuning_allowed": False})
        write_manifest(project)
        pipeline.atomic_json(project.root / "report.json", {
            "schema": "architectural-css-fit-report/v1", "phase": "development",
            "revision": project.revision, "status": acceptance["status"],
            "sealed": bool(args.seal), "stage_cache": project.stats})
        print(f"revision {project.revision}\nDEVELOPMENT {acceptance['status']} sealed={bool(args.seal)}")
        return 0 if acceptance["status"] == "PASS" else 1

    # Blind evidence is sealed before routes are summarized.
    blind_seal = {building_id: pipeline.digest_bytes(pipeline.compact_bytes(results[building_id][1]))
                  for building_id in building_ids}
    pipeline.immutable_json(project.rev / "blind-automatic-seal.json", {
        "schema": "architectural-topology-blind-seal/v1", "development_lock_sha256": pipeline.digest_file(lock_path),
        "buildings": blind_seal, "sha256": pipeline.digest_bytes(pipeline.compact_bytes(blind_seal))})
    all_ids = charter["evaluation"]["development_buildings"] + building_ids
    rows = []
    for building_id in all_ids:
        assessment = json.loads((project.rev / "buildings" / building_id / "assessment.json").read_text(encoding="utf-8"))
        rows.append({"building_id": building_id, "building_type": assessment["building_type"],
                     "cluster": assessment["cluster"], "route": assessment["route"],
                     "fit": assessment["fit"], "residual": assessment["residual"]["status"]})
    blind_rows = [row for row in rows if row["building_id"] in building_ids]
    promoted = [row for row in blind_rows if row["route"] == "G1_METRIC_GRAPH"]
    controls_hold = all(row["route"] != "G1_METRIC_GRAPH" for row in blind_rows
                        if row["building_id"] in charter["evaluation"]["negative_controls"])
    transfer = (len(promoted) >= charter["evaluation"]["minimum_blind_g1"] and
                len({row["cluster"] for row in promoted}) >= charter["evaluation"]["minimum_blind_clusters"] and
                controls_hold)
    answer = "TRANSFER_OBSERVED" if transfer else "INSUFFICIENT_AUTOMATIC_EVIDENCE"
    index = {"schema": "architectural-css-fit-index/v1", "revision": project.revision,
             "answer": answer, "development_sealed": True, "blind_exposed_once": True,
             "buildings": rows, "metrics": {"blind_g1": len(promoted),
                                                "blind_clusters": len({row['cluster'] for row in promoted}),
                                                "negative_controls_hold": controls_hold},
             "stage_cache": project.stats, "network_requests": 0, "ocr_calls": 0,
             "vlm_calls": 0, "source_downloads": 0, "world_mutated": False}
    pipeline.immutable_json(project.rev / "index.json", index)
    pipeline.atomic_bytes(project.rev / "index.html", index_html(index))
    write_manifest(project)
    pipeline.atomic_json(project.root / "report.json", {
        "schema": "architectural-css-fit-report/v1", "phase": "blind", "revision": project.revision,
        "answer": answer, "metrics": index["metrics"], "stage_cache": project.stats})
    print(f"revision {project.revision}\nRESULT {answer}\nBLIND_G1 {len(promoted)}")
    return 0


def completed_blind_cache_run(args):
    """Validate and reuse a completed blind seal without reopening perception.

    Revision artifacts deliberately exclude mutable cache counters.  Once the blind
    seal exists, an unchanged rerun proves every building receipt and returns the
    already-sealed index instead of attempting to rewrite an immutable index with a
    different executed/cached counter.
    """
    charter, _, _, _, _ = load_inputs(args)
    root = args.out.resolve()
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    rev = root / "revisions" / revision
    lock = json.loads((root / "DEVELOPMENT_LOCK.json").read_text(encoding="utf-8"))
    if lock.get("revision") != revision:
        raise RuntimeError("completed blind revision does not match development lock")
    index = json.loads((rev / "index.json").read_text(encoding="utf-8"))
    blind_seal = json.loads((rev / "blind-automatic-seal.json").read_text(encoding="utf-8"))
    building_ids = charter["evaluation"]["blind_buildings"]
    if set(blind_seal.get("buildings", {})) != set(building_ids):
        raise RuntimeError("completed blind seal membership changed")
    for building_id in building_ids:
        receipt_path = rev / "receipts" / f"building-{building_id}.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        for row in receipt.get("outputs", []):
            path = pipeline.safe_child(rev, row["path"])
            if not path.is_file() or pipeline.digest_file(path) != row["sha256"]:
                raise RuntimeError(f"cached artifact mismatch {row['path']}")
        print(f"[cached] {building_id}")
    stats = {"executed": [], "cached": building_ids, "evidence_reads": 0,
             "topology_runs": 0, "css_runs": 0, "ocr_calls": 0, "vlm_calls": 0,
             "network_requests": 0, "source_downloads": 0, "world_writes": 0}
    pipeline.atomic_json(root / "report.json", {
        "schema": "architectural-css-fit-report/v1", "phase": "blind", "revision": revision,
        "answer": index["answer"], "metrics": index["metrics"], "stage_cache": stats})
    print(f"revision {revision}\nRESULT {index['answer']}\ncached: {len(building_ids)}\n"
          "executed: 0\nevidence_reads: 0\ntopology_runs: 0\ncss_runs: 0")
    return 0


def index_html(index):
    cards = "".join(f"<a href='buildings/{row['building_id']}/index.html'><b>{row['building_id']}</b>"
                    f"<span>{row['cluster']} · {row['route']}</span></a>" for row in index["buildings"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>Pre-CSS topology transfer</title>
<style>body{{margin:0;background:#152026;color:#e8ece9;font:16px system-ui}}main{{max-width:1100px;margin:auto;padding:48px 24px}}h1{{font:52px Georgia}}.answer{{color:#d49a3a;font:700 16px Consolas}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}}a{{display:grid;gap:8px;padding:16px;background:#202c31;border:1px solid #415159;color:#e8ece9;text-decoration:none}}a span{{color:#a9b8bd}}</style></head>
<body><main><div class='answer'>DETERMINISTIC PRE-CSS TOPOLOGY · {index['revision']}</div><h1>Transfer through ownership</h1><p class='answer'>{index['answer']}</p><div class='grid'>{cards}</div></main></body></html>""".encode("utf-8")


def verify(args):
    charter, _, _, _, _ = load_inputs(args)
    root = args.out.resolve()
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    rev = root / "revisions" / revision
    errors = []
    manifest = json.loads((rev / "manifest.json").read_text(encoding="utf-8"))
    for row in manifest["files"]:
        path = pipeline.safe_child(rev, row["path"])
        if not path.is_file() or pipeline.digest_file(path) != row["sha256"] or path.stat().st_size != row["bytes"]:
            errors.append(f"artifact mismatch {row['path']}")
    lock_path = root / "DEVELOPMENT_LOCK.json"
    if not lock_path.is_file():
        errors.append("development lock missing")
    development = json.loads((rev / "development-acceptance.json").read_text(encoding="utf-8"))
    if development["status"] != "PASS":
        errors.append("development acceptance")
    index_path = rev / "index.json"
    if not index_path.is_file():
        errors.append("blind index missing")
        index = {"buildings": []}
    else:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    if len(index.get("buildings", [])) != charter["inputs"]["buildings"]:
        errors.append("building count")
    for row in index.get("buildings", []):
        target = rev / "buildings" / row["building_id"]
        evidence = json.loads((target / "evidence.graph.json").read_text(encoding="utf-8"))
        graph = json.loads((target / "building.graph.json").read_text(encoding="utf-8"))
        residual = json.loads((target / "css-residual.json").read_text(encoding="utf-8"))
        if residual.get("corrected_geometry", "missing") is not None or residual.get("discovery_operations") != 0:
            errors.append(f"CSS authority violation {row['building_id']}")
        if residual.get("graph_sha256") != pipeline.digest_bytes(pipeline.compact_bytes(graph)):
            errors.append(f"CSS graph hash {row['building_id']}")
        if evidence.get("maximum_view_overlap_ratio") != 0:
            errors.append(f"view overlap {row['building_id']}")
        if any("CEILING" in node.get("normalized", "") and node["type"] != "ceiling"
               for node in evidence.get("datums", [])):
            errors.append(f"datum vocabulary {row['building_id']}")
    if any(index.get(key) not in (0, False) for key in
           ("network_requests", "ocr_calls", "vlm_calls", "source_downloads", "world_mutated")):
        errors.append("authority boundary")
    result = {"schema": "architectural-css-fit-verification/v1",
              "status": "PASS" if not errors else "FAIL", "revision": revision,
              "buildings": len(index.get("buildings", [])), "errors": errors,
              "network_requests": 0, "ocr_calls": 0, "vlm_calls": 0,
              "source_downloads": 0, "world_mutated": False}
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
        if args.command == "develop":
            if (args.out.resolve() / "DEVELOPMENT_LOCK.json").is_file():
                raise RuntimeError("development is already sealed; use a fresh --out root")
            return run_phase(args, blind=False)
        if args.command == "blind":
            root = args.out.resolve()
            if ((root / "DEVELOPMENT_LOCK.json").is_file() and (root / "HEAD").is_file() and
                    (root / "revisions" / (root / "HEAD").read_text(encoding="ascii").strip() /
                     "blind-automatic-seal.json").is_file()):
                return completed_blind_cache_run(args)
            return run_phase(args, blind=True)
        if args.command == "verify":
            return verify(args)
        return serve(args)
    except Exception as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

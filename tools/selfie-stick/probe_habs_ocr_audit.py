#!/usr/bin/env python3
"""Run every frozen HABS sheet through the real, pinned OCR/CV lane only.

This probe deliberately does not call a VLM, infer a building, compile pieces, contact
Valheim, or authorize scale from nearest-line heuristics.  It answers the smaller R&D
question frozen in architectural-ocr-audit-v1.json.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import statistics
import sys
import tempfile
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_architectural_curriculum as pipeline

DEFAULT_CHARTER = HERE / "architectural-ocr-audit-v1.json"
DEFAULT_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_OUT = HERE / "out" / "architectural-curriculum" / "real-ocr-audit-v1"
ENGINE = "habs-real-ocr-cv-audit/1.0.0"


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--charter", type=Path, default=DEFAULT_CHARTER)
    common.add_argument("--source-charter", type=Path, default=pipeline.DEFAULT_CHARTER,
                        help="selection-integrity charter consumed by the shared corpus loader")
    common.add_argument("--selection", type=Path, default=pipeline.DEFAULT_SELECTION)
    common.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", parents=[common])
    sub.add_parser("verify", parents=[common])
    serve = sub.add_parser("serve", parents=[common])
    serve.add_argument("--port", type=int, default=8877)
    return parser.parse_args()


def load_inputs(args):
    audit_charter = json.loads(args.charter.read_text(encoding="utf-8"))
    source_args = SimpleNamespace(charter=args.source_charter,
                                  selection=args.selection, corpus=args.corpus)
    _, selection, records = pipeline.load_inputs(source_args)
    source = pipeline.verify_sources(records, full_hash=True)
    dependencies = pipeline.dependency_preflight(False)
    blockers = []
    if source["status"] != "PASS":
        blockers.append("corpus integrity failed")
    if dependencies["status"] != "READY":
        blockers.append("pinned OCR/CV dependencies unavailable")
    if len(records) != audit_charter["inputs"]["buildings"]:
        blockers.append("building count differs from frozen audit")
    if source["drawings"] != audit_charter["inputs"]["sheets"]:
        blockers.append("sheet count differs from frozen audit")
    preflight = {
        "schema": "architectural-ocr-audit-preflight/v1",
        "status": "READY" if not blockers else "BLOCKED",
        "engine": ENGINE,
        "mode": "REAL_OCR_CV_ONLY",
        "source": source,
        "dependencies": dependencies,
        "blockers": blockers,
        "network_requests": 0,
        "vlm_calls": 0,
        "valheim_contacted": False,
        "world_mutated": False,
    }
    return audit_charter, selection, records, preflight


class AuditProject:
    def __init__(self, args, charter, records, preflight):
        identity = {
            "engine": ENGINE,
            "script_sha256": pipeline.digest_file(Path(__file__)),
            "charter_sha256": pipeline.digest_file(args.charter),
            "source_charter_sha256": pipeline.digest_file(args.source_charter),
            "parser_sha256": pipeline.digest_file(HERE / "probe_architectural_curriculum.py"),
            "requirements_sha256": pipeline.digest_file(
                HERE / "requirements-architectural-curriculum.txt"),
            "selection_sha256": pipeline.digest_file(args.selection),
            "runtime": preflight["dependencies"],
            "corpus": {record["id"]: preflight["source"]["manifest_hashes"][record["id"]]
                       for record in records},
            "mode": "REAL_OCR_CV_ONLY",
        }
        self.revision = pipeline.digest_bytes(pipeline.compact_bytes(identity))[:20]
        self.root = args.out.resolve()
        self.rev = self.root / "revisions" / self.revision
        self.stats = {"executed": [], "cached": [], "ocr_calls": 0,
                      "reused_ocr_artifacts": 0, "network_requests": 0, "vlm_calls": 0}
        self.runtime_fingerprint = pipeline.digest_bytes(pipeline.compact_bytes(
            preflight["dependencies"]))
        self.rev.mkdir(parents=True, exist_ok=True)
        pipeline.atomic_bytes(self.root / "HEAD", (self.revision + "\n").encode("ascii"))
        pipeline.immutable_json(self.rev / "identity.json", identity)

    def stage(self, name, input_value, builder):
        receipt_path = self.rev / "receipts" / f"{name}.json"
        fingerprint = pipeline.digest_bytes(pipeline.compact_bytes(
            {"engine": ENGINE, "input": input_value}))
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("fingerprint") == fingerprint:
                valid = all(
                    (path := pipeline.safe_child(self.rev, item["path"])).is_file() and
                    pipeline.digest_file(path) == item["sha256"]
                    for item in receipt.get("outputs", []))
                if valid:
                    self.stats["cached"].append(name)
                    return receipt.get("facts", {})
        outputs, facts = builder()
        rows = []
        for output in outputs:
            path = Path(output).resolve()
            rows.append({"path": path.relative_to(self.rev).as_posix(),
                         "sha256": pipeline.digest_file(path),
                         "bytes": path.stat().st_size})
        pipeline.immutable_json(receipt_path, {
            "schema": "architectural-ocr-audit-stage-receipt/v1",
            "stage": name,
            "fingerprint": fingerprint,
            "outputs": rows,
            "facts": facts,
        })
        self.stats["executed"].append(name)
        return facts


def union_region(tokens):
    return [min(item["region"][0] for item in tokens),
            min(item["region"][1] for item in tokens),
            max(item["region"][2] for item in tokens),
            max(item["region"][3] for item in tokens)]


def nearby_context(tokens, window):
    """Return spatial neighbors without treating OCR reading order as geometry."""
    region = union_region(window)
    neighbors = []
    window_ids = {id(item) for item in window}
    for token in tokens:
        if id(token) in window_ids:
            continue
        other = token["region"]
        horizontal_gap = max(0.0, region[0] - other[2], other[0] - region[2])
        vertical_gap = max(0.0, region[1] - other[3], other[1] - region[3])
        if horizontal_gap <= 0.18 and vertical_gap <= 0.025:
            neighbors.append(token)
    return neighbors


def dimension_context_rejection(tokens, window, match):
    context = " ".join(str(item["text"]) for item in nearby_context(tokens, window))
    if re.search(r"\b(?:metric|scale)\b", context, re.I):
        return "scale-legend-context"
    if match.group("metric") and re.search(r"\bft\.?\b", context, re.I):
        return "scale-legend-context"
    if (match.group("feet") and not match.group("inches") and
            re.search(r"\b\d+\s*[x×]\s*\d+\b", context, re.I)):
        return "material-size-context"
    return None


def dimension_signals(tokens):
    accepted = []
    consumed = set()
    context_rejections = {}
    for start in range(len(tokens)):
        if start in consumed:
            continue
        for width in range(1, min(4, len(tokens) - start + 1)):
            window = tokens[start:start + width]
            raw = " ".join(item["text"] for item in window)
            match = pipeline.DIMENSION_RE.search(raw)
            # Multi-token recovery is only for a dimension that begins in the
            # first token (for example ``12'-`` + ``6 1/2\"``).  Otherwise an
            # unrelated label can greedily consume a later, perfectly local
            # dimension and turn its evidence region into half a sheet.
            if match and width > 1 and match.start() > len(str(window[0]["text"])):
                continue
            if (match and width > 1 and match.group("feet") and
                    not match.group("inches")):
                continue
            value = pipeline.parse_dimension(raw)
            if value is None or not 0.15 <= value <= 100:
                continue
            rejection = dimension_context_rejection(tokens, window, match)
            if rejection:
                context_rejections[start] = {
                    "text": raw,
                    "confidence": round(min(float(item["confidence"]) for item in window), 6),
                    "region": union_region(window),
                    "reason": rejection,
                }
                break
            accepted.append({
                "text": raw,
                "value_m": round(value, 6),
                "unit_family": "metric" if match.group("metric") else "imperial",
                "confidence": round(min(float(item["confidence"]) for item in window), 6),
                "region": union_region(window),
                "token_start": start,
                "token_count": width,
                "status": "STRICT_OCR_PARSE",
            })
            consumed.update(range(start, start + width))
            break
    suspicious = list(context_rejections.values())
    architectural = re.compile(r"\d\s*['′]|\d+\s+\d+/\d+\s*(?:[°º]|$)|\d\s*[°º]", re.I)
    for index, token in enumerate(tokens):
        text = str(token["text"])
        if architectural.search(text) and not any(
                item["token_start"] <= index < item["token_start"] + item["token_count"]
                for item in accepted) and index not in context_rejections:
            suspicious.append({"text": text, "confidence": token["confidence"],
                               "region": token["region"], "reason": "architectural-like-unparsed"})
    return accepted, suspicious


def role_signals(tokens):
    text = " ".join(item["text"] for item in tokens).lower()
    patterns = {
        "plan": r"\b(?:floor\s+)?plans?\b",
        "elevation": r"\belevations?\b",
        "section": r"\bsections?\b|\bcross[ -]sections?\b",
        "detail": r"\bdetails?\b",
        "site": r"\bsite\s+plans?\b",
    }
    return sorted(name for name, pattern in patterns.items() if re.search(pattern, text))


def point_segment_distance(px, py, line):
    x1, y1, x2, y2 = line
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def cv_geometry(image_path, dimensions):
    import cv2
    import numpy as np

    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"OpenCV could not decode normalized sheet: {image_path.name}")
    height, width = image.shape
    edges = cv2.Canny(image, 60, 170, apertureSize=3)
    raw = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=55,
                          minLineLength=max(35, int(min(width, height) * .025)),
                          maxLineGap=max(8, int(min(width, height) * .008)))
    lines = []
    for item in raw[:, 0, :] if raw is not None else []:
        x1, y1, x2, y2 = (int(value) for value in item)
        length = math.hypot(x2 - x1, y2 - y1)
        angle = abs(math.degrees(math.atan2(y2 - y1, x2 - x1))) % 180
        axis = "horizontal" if min(angle, 180 - angle) <= 12 else \
               "vertical" if abs(angle - 90) <= 12 else "diagonal"
        lines.append({"pixels": [x1, y1, x2, y2], "length_px": round(length, 3),
                      "angle_degrees": round(angle, 3), "axis": axis})
    lines.sort(key=lambda item: (-item["length_px"], item["pixels"]))
    lines = lines[:2500]
    diagonal = math.hypot(width, height)
    anchors = []
    for dimension in dimensions:
        x0, y0, x1, y1 = dimension["region"]
        cx, cy = ((x0 + x1) * width / 2, (y0 + y1) * height / 2)
        candidates = []
        for line in lines:
            if line["axis"] == "diagonal" or line["length_px"] < min(width, height) * .04:
                continue
            distance = point_segment_distance(cx, cy, line["pixels"])
            if distance <= diagonal * .035:
                candidates.append((distance - line["length_px"] * .0005, distance, line))
        if not candidates:
            continue
        _, distance, line = min(candidates, key=lambda item: (item[0], item[2]["pixels"]))
        anchors.append({
            "dimension_text": dimension["text"],
            "value_m": dimension["value_m"],
            "dimension_region": dimension["region"],
            "line": {"normalized": [line["pixels"][0] / width, line["pixels"][1] / height,
                                     line["pixels"][2] / width, line["pixels"][3] / height],
                     "length_px": line["length_px"], "axis": line["axis"]},
            "distance_px": round(distance, 3),
            "candidate_scale_m_per_px": round(dimension["value_m"] / line["length_px"], 9),
            "status": "CANDIDATE_NOT_SCALE_AUTHORITY",
        })
    return {
        "schema": "architectural-cv-lines/v1",
        "engine": f"OpenCV/{cv2.__version__}",
        "pixels": [width, height],
        "edge_pixels": int((edges > 0).sum()),
        "line_count": len(lines),
        "axis_counts": dict(Counter(item["axis"] for item in lines)),
        "anchor_candidates": anchors,
        "authority": "candidate geometric support only",
    }


def sheet_html(audit):
    boxes = []
    for item in audit["strict_dimensions"]:
        x0, y0, x1, y1 = item["region"]
        boxes.append(
            f"<div class='box dim' style='left:{x0*100:.3f}%;top:{y0*100:.3f}%;"
            f"width:{(x1-x0)*100:.3f}%;height:{(y1-y0)*100:.3f}%'>"
            f"<span>{html.escape(item['text'])} → {item['value_m']:.3f} m</span></div>")
    for item in audit["suspicious_dimensions"]:
        x0, y0, x1, y1 = item["region"]
        boxes.append(
            f"<div class='box suspect' style='left:{x0*100:.3f}%;top:{y0*100:.3f}%;"
            f"width:{(x1-x0)*100:.3f}%;height:{(y1-y0)*100:.3f}%'></div>")
    rows = "".join(
        f"<tr><td>{html.escape(item['text'])}</td><td>{item['value_m']:.4f} m</td>"
        f"<td>{item['confidence']:.3f}</td></tr>" for item in audit["strict_dimensions"])
    return f"""<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>{audit['building_id']} sheet {audit['sheet_index']}</title><style>
:root{{--bg:#0b1317;--panel:#152329;--line:#38505a;--ink:#edf2ef;--muted:#9eb6c2;--gold:#efa92f;--bad:#f07167}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px Arial;padding:22px}}a{{color:#70cee9}}.k{{color:var(--gold);font:700 12px Consolas;letter-spacing:.12em}}h1{{margin:.25rem 0 1rem}}.grid{{display:grid;grid-template-columns:minmax(0,2fr) minmax(300px,1fr);gap:14px}}.panel{{background:var(--panel);border:1px solid var(--line);padding:14px}}.image{{position:relative;background:white}}.image img{{display:block;width:100%}}.box{{position:absolute;border:2px solid var(--gold);pointer-events:none}}.box span{{position:absolute;bottom:100%;left:-2px;background:#10191d;color:var(--gold);padding:2px 4px;white-space:nowrap;font:11px Consolas}}.suspect{{border-color:var(--bad);border-style:dashed}}table{{width:100%;border-collapse:collapse}}td,th{{border-top:1px solid var(--line);padding:7px;text-align:left}}.muted{{color:var(--muted)}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}</style>
<a href='../../../index.html'>← corpus audit</a><div class='k'>REAL OCR/CV · NO VLM · NO SCALE AUTHORITY</div>
<h1>{html.escape(audit['building_id'])} · sheet {audit['sheet_index']:02d}</h1><div class='grid'><section class='panel'><div class='image'><img src='normalized.png'>{''.join(boxes)}</div></section><aside class='panel'><p>{html.escape(audit['drawing_title'])}</p><p class='muted'>{audit['curriculum_cluster']} routing stratum · {audit['token_count']} tokens · {len(audit['strict_dimensions'])} strict dimensions · {len(audit['cv']['anchor_candidates'])} nearest-line candidates</p><p>OCR role signals: {', '.join(audit['ocr_role_signals']) or 'none'}</p><p>Catalog hints: {', '.join(audit['catalog_role_hints']) or 'none'}</p><table><tr><th>OCR text</th><th>Parsed</th><th>Confidence</th></tr>{rows}</table><p class='muted'>Gold boxes are strict text parses. Dashed red boxes resemble architectural dimensions but failed strict parsing. Nearby CV lines are candidates only. Cluster IDs are pre-sort routing strata, not visual evidence.</p></aside></div>""".encode("utf-8")


def dashboard_html(index):
    gates = "".join(
        f"<div class='gate {'pass' if gate['status']=='PASS' else 'fail'}'><span>{html.escape(gate['id'])}</span><b>{gate['status']}</b><small>{html.escape(str(gate['actual']))} / {html.escape(str(gate['minimum']))}</small></div>"
        for gate in index["gates"])
    rows = []
    for item in index["sheets"]:
        href = f"sheets/{item['building_id']}/sheet-{item['sheet_index']:02d}/index.html"
        rows.append(f"<tr><td><a href='{href}'>{item['building_id']} / {item['sheet_index']:02d}</a></td><td>{item['cluster']}</td><td>{item['tokens']}</td><td>{item['strict_dimensions']}</td><td>{item['suspicious_dimensions']}</td><td>{item['anchor_candidates']}</td><td>{', '.join(item['roles']) or '—'}</td></tr>")
    metrics = index["metrics"]
    cluster_cards = "".join(
        f"<div class='cluster'><b>{item['id']}</b><span>{item['buildings']} buildings · {item['sheets']} sheets</span><strong>{item['strict_dimension_sheet_ratio']*100:.1f}% dimension coverage</strong><small>{item['strict_dimensions']} strict / {item['suspicious_dimensions']} held</small></div>"
        for item in metrics["clusters"])
    return f"""<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>HABS real OCR/CV audit</title><style>
:root{{--bg:#0a1216;--panel:#142229;--line:#344b55;--ink:#edf2ef;--muted:#9eb6c2;--gold:#efa92f;--ok:#66dd91;--bad:#f07167}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px Arial;padding:24px}}.k{{color:var(--gold);font:700 12px Consolas;letter-spacing:.14em}}h1{{font-size:34px;margin:.3rem 0}}.banner{{border:1px solid var(--gold);padding:13px;margin:18px 0;color:var(--gold)}}.metrics,.gates,.clusters{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:9px;margin:12px 0}}.metric,.gate,.cluster{{background:var(--panel);border:1px solid var(--line);padding:12px;display:grid;gap:5px}}.metric b{{font-size:22px}}.metric span,.gate span,.gate small,.cluster span,.cluster small{{color:var(--muted)}}.cluster strong{{color:var(--gold)}}.pass b{{color:var(--ok)}}.fail b{{color:var(--bad)}}table{{width:100%;border-collapse:collapse;background:var(--panel);margin-top:16px}}th,td{{padding:8px;border-top:1px solid var(--line);text-align:left}}th{{position:sticky;top:0;background:#1b2d35}}a{{color:#72c9e7}}</style>
<div class='k'>BUILDINGS FROM BYTES · REAL DATA AUDIT</div><h1>Does the OCR/CV lane hold water?</h1><div class='banner'>{index['answer']} · {index['authority']}</div><div class='metrics'><div class='metric'><span>Sheets</span><b>{metrics['completed_sheets']}</b></div><div class='metric'><span>OCR tokens</span><b>{metrics['total_tokens']}</b></div><div class='metric'><span>Strict dimensions</span><b>{metrics['strict_dimensions']}</b></div><div class='metric'><span>Sheets with dimensions</span><b>{metrics['sheets_with_strict_dimensions']}</b></div><div class='metric'><span>Anchor candidates</span><b>{metrics['anchor_candidates']}</b></div><div class='metric'><span>Median confidence</span><b>{metrics['median_token_confidence']:.3f}</b></div></div><div class='gates'>{gates}</div><div class='k'>PRE-SORT STRATA · ROUTING ONLY</div><div class='clusters'>{cluster_cards}</div><div class='banner'><a href='review-contact.png'>Open the deterministic {len(index['visual_review']['samples'])}-signal visual review sample →</a></div><table><thead><tr><th>Sheet</th><th>Cluster</th><th>Tokens</th><th>Strict dims</th><th>Near misses</th><th>CV candidates</th><th>OCR roles</th></tr></thead><tbody>{''.join(rows)}</tbody></table>""".encode("utf-8")


def visual_review_sample(project, candidates):
    from PIL import Image, ImageDraw, ImageOps

    selected = []
    for cluster in sorted({item["cluster"] for item in candidates}):
        members = [item for item in candidates if item["cluster"] == cluster]
        members.sort(key=lambda item: pipeline.digest_bytes(pipeline.compact_bytes({
            "building_id": item["building_id"], "sheet_index": item["sheet_index"],
            "text": item["text"], "region": item["region"]})))
        strict = [item for item in members if item["status"] == "STRICT_OCR_PARSE"]
        held = [item for item in members if item["status"] != "STRICT_OCR_PARSE"]
        selected.extend((strict[:3] + held)[:3])
    tile_width, tile_height, columns = 600, 240, 3
    rows = math.ceil(len(selected) / columns)
    canvas = Image.new("RGB", (tile_width * columns, tile_height * rows), "#0b1317")
    draw = ImageDraw.Draw(canvas)
    manifest_rows = []
    for index, item in enumerate(selected):
        image_path = (project.rev / "sheets" / item["building_id"] /
                      f"sheet-{item['sheet_index']:02d}" / "normalized.png")
        with Image.open(image_path) as opened:
            image = opened.convert("RGB")
        width, height = image.size
        x0, y0, x1, y1 = item["region"]
        center_x, center_y = (x0 + x1) * width / 2, (y0 + y1) * height / 2
        crop_width = max(520, (x1 - x0) * width * 3.5)
        crop_height = max(150, (y1 - y0) * height * 5.0)
        left = max(0, int(center_x - crop_width / 2))
        top = max(0, int(center_y - crop_height / 2))
        right = min(width, int(center_x + crop_width / 2))
        bottom = min(height, int(center_y + crop_height / 2))
        crop = ImageOps.contain(image.crop((left, top, right, bottom)),
                                (tile_width - 16, tile_height - 55))
        column, row = index % columns, index // columns
        origin_x, origin_y = column * tile_width, row * tile_height
        paste_x = origin_x + (tile_width - crop.width) // 2
        paste_y = origin_y + 47 + (tile_height - 52 - crop.height) // 2
        canvas.paste(crop, (paste_x, paste_y))
        value = f"{item['value_m']:.3f} m" if item["value_m"] is not None else "HELD / UNPARSED"
        label = f"{item['cluster']} · {item['building_id']}/{item['sheet_index']:02d} · {value}"
        raw = item["text"].replace("\n", " ")[:76]
        draw.text((origin_x + 8, origin_y + 7), label, fill="#efa92f")
        draw.text((origin_x + 8, origin_y + 24), raw, fill="#edf2ef")
        draw.rectangle((origin_x, origin_y, origin_x + tile_width - 1,
                        origin_y + tile_height - 1), outline="#344b55")
        manifest_rows.append({**item, "crop_pixels": [left, top, right, bottom]})
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        canvas.save(temporary, "PNG", optimize=False, compress_level=9)
        pipeline.immutable_bytes(project.rev / "review-contact.png", temporary.read_bytes())
    finally:
        temporary.unlink(missing_ok=True)
    review = {"schema": "architectural-ocr-visual-review-sample/v1",
              "selection": "up to three strict parses per pre-sort cluster after SHA-256 ordering; held notation fills sparse strata",
              "authority": "UNADJUDICATED_VISUAL_SAMPLE", "samples": manifest_rows,
              "image": {"path": "review-contact.png",
                        "sha256": pipeline.digest_file(project.rev / "review-contact.png")}}
    pipeline.immutable_json(project.rev / "review-sample.json", review)
    return review


def reusable_ocr(project, record, drawing, target):
    """Reuse immutable OCR bytes across parser/report revisions when authority matches."""
    for revision in sorted((project.root / "revisions").glob("*")):
        if not revision.is_dir() or revision.resolve() == project.rev.resolve():
            continue
        identity_path = revision / "identity.json"
        prior_target = revision / "sheets" / record["id"] / f"sheet-{int(drawing['sheet_index']):02d}"
        audit_path, ocr_path = prior_target / "audit.json", prior_target / "ocr.json"
        normalized_path = prior_target / "normalized.png"
        if not all(path.is_file() for path in (identity_path, audit_path, ocr_path, normalized_path)):
            continue
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        if pipeline.digest_bytes(pipeline.compact_bytes(identity.get("runtime"))) != project.runtime_fingerprint:
            continue
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        ocr = json.loads(ocr_path.read_text(encoding="utf-8"))
        if (audit.get("source_sha256") != drawing["download"]["sha256"] or
                audit.get("raster", {}).get("normalized_sha256") != pipeline.digest_file(normalized_path) or
                not ocr.get("numeric_authority") or ocr.get("engine") != "RapidOCR/3.9.2"):
            continue
        pipeline.immutable_bytes(target / "normalized.png", normalized_path.read_bytes())
        project.stats["reused_ocr_artifacts"] += 1
        return audit["raster"], ocr, revision.name
    return None


def audit_sheet(project, record, drawing, target, cluster):
    download = drawing["download"]
    source = pipeline.safe_child(record["directory"], download["local_path"])
    normalized = target / "normalized.png"
    reused = reusable_ocr(project, record, drawing, target)
    if reused:
        raster, ocr, reused_from = reused
    else:
        raster = pipeline.normalize_sheet(source, normalized)
        ocr = pipeline.real_ocr(normalized)
        project.stats["ocr_calls"] += 1
        reused_from = None
    strict, suspicious = dimension_signals(ocr["tokens"])
    cv = cv_geometry(normalized, strict)
    roles = role_signals(ocr["tokens"])
    audit = {
        "schema": "architectural-ocr-sheet-audit/v1",
        "mode": "REAL_OCR_CV_ONLY",
        "building_id": record["id"],
        "building_type": record["building_type"],
        "curriculum_cluster": cluster,
        "cluster_authority": "PRE_SORT_ROUTING_ONLY",
        "building_title": record["manifest"]["title"],
        "sheet_index": int(drawing["sheet_index"]),
        "drawing_title": drawing["title"],
        "source_sha256": download["sha256"],
        "source_url": download["source_url"],
        "raster": raster,
        "ocr_engine": ocr["engine"],
        "token_count": len(ocr["tokens"]),
        "median_token_confidence": (statistics.median(float(item["confidence"])
                                                       for item in ocr["tokens"])
                                    if ocr["tokens"] else 0.0),
        "strict_dimensions": strict,
        "suspicious_dimensions": suspicious,
        "ocr_role_signals": roles,
        "catalog_role_hints": pipeline.catalog_role_hints(drawing),
        "cv": cv,
        "authority": "OCR observations plus non-authoritative CV line candidates",
        "network_requests": 0,
        "vlm_calls": 0,
        "world_mutated": False,
        "ocr_reused_from_revision": reused_from,
    }
    pipeline.immutable_json(target / "ocr.json", ocr)
    pipeline.immutable_json(target / "audit.json", audit)
    pipeline.immutable_bytes(target / "index.html", sheet_html(audit))
    return audit, [normalized, target / "ocr.json", target / "audit.json", target / "index.html"]


def aggregate(rows, charter):
    confidences = [item["median_confidence"] for item in rows if item["tokens"]]
    metrics = {
        "completed_sheets": len(rows),
        "sheets_with_ten_tokens": sum(item["tokens"] >= 10 for item in rows),
        "sheets_with_ten_tokens_ratio": sum(item["tokens"] >= 10 for item in rows) / len(rows),
        "total_tokens": sum(item["tokens"] for item in rows),
        "median_token_confidence": statistics.median(confidences) if confidences else 0.0,
        "strict_dimensions": sum(item["strict_dimensions"] for item in rows),
        "sheets_with_strict_dimensions": sum(item["strict_dimensions"] > 0 for item in rows),
        "sheets_with_strict_dimensions_ratio": sum(item["strict_dimensions"] > 0 for item in rows) / len(rows),
        "suspicious_dimensions": sum(item["suspicious_dimensions"] for item in rows),
        "anchor_candidates": sum(item["anchor_candidates"] for item in rows),
        "sheets_with_anchor_candidates": sum(item["anchor_candidates"] > 0 for item in rows),
        "sheets_with_anchor_candidates_ratio": sum(item["anchor_candidates"] > 0 for item in rows) / len(rows),
        "sheets_with_role_signal": sum(bool(item["roles"]) for item in rows),
        "sheets_with_role_signal_ratio": sum(bool(item["roles"]) for item in rows) / len(rows),
    }
    cluster_metrics = []
    for cluster_id in sorted({item["cluster"] for item in rows}):
        members = [item for item in rows if item["cluster"] == cluster_id]
        cluster_metrics.append({
            "id": cluster_id,
            "buildings": len({item["building_id"] for item in members}),
            "sheets": len(members),
            "tokens": sum(item["tokens"] for item in members),
            "strict_dimensions": sum(item["strict_dimensions"] for item in members),
            "suspicious_dimensions": sum(item["suspicious_dimensions"] for item in members),
            "anchor_candidates": sum(item["anchor_candidates"] for item in members),
            "strict_dimension_sheet_ratio": (sum(item["strict_dimensions"] > 0 for item in members) /
                                               len(members)),
            "median_token_confidence": statistics.median(
                item["median_confidence"] for item in members if item["tokens"]),
        })
    metrics["clusters"] = cluster_metrics
    frozen = charter["success_gates"]
    checks = [
        ("completed-sheets", metrics["completed_sheets"], frozen["completed_sheets"]),
        ("ten-token-coverage", metrics["sheets_with_ten_tokens_ratio"], frozen["minimum_sheets_with_ten_tokens_ratio"]),
        ("strict-dimension-coverage", metrics["sheets_with_strict_dimensions_ratio"], frozen["minimum_sheets_with_strict_dimensions_ratio"]),
        ("median-token-confidence", metrics["median_token_confidence"], frozen["minimum_median_token_confidence"]),
        ("ocr-role-coverage", metrics["sheets_with_role_signal_ratio"], frozen["minimum_sheets_with_role_signal_ratio"]),
        ("cv-anchor-candidate-coverage", metrics["sheets_with_anchor_candidates_ratio"], frozen["minimum_sheets_with_anchor_candidates_ratio"]),
    ]
    gates = [{"id": name, "status": "PASS" if actual >= minimum else "FAIL",
              "actual": round(actual, 6) if isinstance(actual, float) else actual,
              "minimum": minimum} for name, actual, minimum in checks]
    passed = all(item["status"] == "PASS" for item in gates)
    return metrics, gates, charter["outcomes"]["pass" if passed else "fail"]


def run(args):
    charter, _, records, preflight = load_inputs(args)
    project = AuditProject(args, charter, records, preflight)
    pipeline.atomic_json(project.root / "preflight.json", preflight)
    pipeline.immutable_json(project.rev / "preflight.json", preflight)
    if preflight["status"] != "READY":
        report = {"schema": "architectural-ocr-audit-report/v1", "answer": "BLOCKED",
                  "revision": project.revision, "blockers": preflight["blockers"],
                  "network_requests": 0, "vlm_calls": 0, "world_mutated": False}
        pipeline.atomic_json(project.root / "report.json", report)
        print(json.dumps(report, indent=2))
        return 2
    curriculum_charter = json.loads(pipeline.DEFAULT_CHARTER.read_text(encoding="utf-8"))
    presort_features = {record["id"]: pipeline.fixture_features(record) for record in records}
    presort_clusters, presort_order = pipeline.build_curriculum(
        records, presort_features, curriculum_charter)
    cluster_by_building = {building_id: cluster["id"] for cluster in presort_clusters
                           for building_id in cluster["members"]}
    rows = []
    review_candidates = []
    ordinal = 0
    for record in records:
        for drawing in record["manifest"]["drawings"]:
            ordinal += 1
            sheet_index = int(drawing["sheet_index"])
            cluster = cluster_by_building[record["id"]]
            target = project.rev / "sheets" / record["id"] / f"sheet-{sheet_index:02d}"
            holder = {}

            def build(record=record, drawing=drawing, target=target, cluster=cluster):
                audit, outputs = audit_sheet(project, record, drawing, target, cluster)
                holder["audit"] = audit
                return outputs, {"tokens": audit["token_count"],
                                 "strict_dimensions": len(audit["strict_dimensions"]),
                                 "suspicious_dimensions": len(audit["suspicious_dimensions"]),
                                 "anchor_candidates": len(audit["cv"]["anchor_candidates"]),
                                 "roles": audit["ocr_role_signals"]}

            facts = project.stage(
                f"sheet-{record['id']}-{sheet_index:02d}",
                {"source_sha256": drawing["download"]["sha256"],
                 "source_bytes": drawing["download"]["bytes"]}, build)
            audit = (holder.get("audit") or
                     json.loads((target / "audit.json").read_text(encoding="utf-8")))
            row = {"ordinal": ordinal, "building_id": record["id"],
                   "building_type": record["building_type"], "sheet_index": sheet_index,
                   "cluster": cluster,
                   "title": drawing["title"], "tokens": audit["token_count"],
                   "median_confidence": audit["median_token_confidence"],
                   "strict_dimensions": len(audit["strict_dimensions"]),
                   "suspicious_dimensions": len(audit["suspicious_dimensions"]),
                   "anchor_candidates": len(audit["cv"]["anchor_candidates"]),
                   "roles": audit["ocr_role_signals"],
                   "catalog_roles": audit["catalog_role_hints"]}
            rows.append(row)
            review_candidates.extend({"cluster": cluster, "building_id": record["id"],
                                      "sheet_index": sheet_index, "text": item["text"],
                                      "value_m": item["value_m"], "confidence": item["confidence"],
                                      "region": item["region"], "status": item["status"]}
                                     for item in audit["strict_dimensions"])
            review_candidates.extend({"cluster": cluster, "building_id": record["id"],
                                      "sheet_index": sheet_index, "text": item["text"],
                                      "value_m": None, "confidence": item["confidence"],
                                      "region": item["region"], "status": "HELD_UNPARSED"}
                                     for item in audit["suspicious_dimensions"])
            print(f"[{ordinal:02d}/{preflight['source']['drawings']:02d}] {record['id']} "
                  f"sheet {sheet_index:02d}: {row['tokens']} tokens, "
                  f"{row['strict_dimensions']} strict dims, {row['anchor_candidates']} CV candidates")
    metrics, gates, answer = aggregate(rows, charter)
    review = visual_review_sample(project, review_candidates)
    index = {"schema": "architectural-ocr-audit-index/v1", "revision": project.revision,
             "mode": "REAL_OCR_CV_ONLY", "answer": answer,
             "authority": charter["outcomes"]["always"], "metrics": metrics,
             "gates": gates, "sheets": rows, "presort": {
                 "authority": "PRE_SORT_ROUTING_ONLY_SIMULATED_FEATURES",
                 "clusters": presort_clusters, "curriculum_order": presort_order},
             "visual_review": review,
             "network_requests": 0,
             "vlm_calls": 0, "world_mutated": False}
    pipeline.immutable_json(project.rev / "index.json", index)
    pipeline.immutable_bytes(project.rev / "index.html", dashboard_html(index))
    report = {"schema": "architectural-ocr-audit-report/v1", "revision": project.revision,
              "answer": answer, "authority": index["authority"], "metrics": metrics,
              "gates": gates, "stage_cache": project.stats, "network_requests": 0,
              "vlm_calls": 0, "world_mutated": False}
    pipeline.atomic_json(project.root / "report.json", report)
    print(f"revision {project.revision}\nRESULT {answer} · {index['authority']}")
    return 0 if answer == charter["outcomes"]["pass"] else 3


def verify(args):
    charter = json.loads(args.charter.read_text(encoding="utf-8"))
    root = args.out.resolve()
    revision = (root / "HEAD").read_text(encoding="ascii").strip()
    rev = root / "revisions" / revision
    index = json.loads((rev / "index.json").read_text(encoding="utf-8"))
    errors = []
    if len(index.get("sheets", [])) != charter["inputs"]["sheets"]:
        errors.append("sheet count")
    if index.get("mode") != "REAL_OCR_CV_ONLY" or index.get("vlm_calls") != 0:
        errors.append("authority boundary")
    review = index.get("visual_review", {})
    review_image = rev / review.get("image", {}).get("path", "missing")
    sample_clusters = {row.get("cluster") for row in review.get("samples", [])}
    expected_clusters = {row["id"] for row in index.get("metrics", {}).get("clusters", [])}
    maximum_samples = 3 * len(expected_clusters)
    if (not review.get("samples") or len(review.get("samples", [])) > maximum_samples or
            sample_clusters != expected_clusters or not review_image.is_file() or
            pipeline.digest_file(review_image) != review.get("image", {}).get("sha256")):
        errors.append("visual review sample")
    for receipt_path in sorted((rev / "receipts").glob("*.json")):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        for item in receipt.get("outputs", []):
            path = pipeline.safe_child(rev, item["path"])
            if not path.is_file() or pipeline.digest_file(path) != item["sha256"]:
                errors.append(f"receipt mismatch {item['path']}")
    for row in index.get("sheets", []):
        target = rev / "sheets" / row["building_id"] / f"sheet-{row['sheet_index']:02d}"
        audit = json.loads((target / "audit.json").read_text(encoding="utf-8"))
        ocr = json.loads((target / "ocr.json").read_text(encoding="utf-8"))
        if audit.get("mode") != "REAL_OCR_CV_ONLY" or not ocr.get("numeric_authority"):
            errors.append(f"real OCR contract {row['building_id']}:{row['sheet_index']}")
        if audit.get("vlm_calls") != 0 or audit.get("network_requests") != 0:
            errors.append(f"network/VLM boundary {row['building_id']}:{row['sheet_index']}")
    result = {"schema": "architectural-ocr-audit-verification/v1",
              "status": "PASS" if not errors else "FAIL", "revision": revision,
              "sheets": len(index.get("sheets", [])), "errors": errors,
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

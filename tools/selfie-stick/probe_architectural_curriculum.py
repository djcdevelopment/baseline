#!/usr/bin/env python3
"""Automatic, cumulative HABS architectural curriculum.

The real lane is deliberately fail-closed: numeric geometry belongs to OCR/CV and
semantic proposals belong to a digest-pinned local vision model.  ``--fixture-vision``
exists only to exercise persistence, routing, rendering and packaging; every fixture
artifact is watermarked SIMULATION_NOT_EVIDENCE and is excluded from research counts.
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import importlib
import importlib.metadata
import io
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter, defaultdict
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
DEFAULT_CHARTER = HERE / "architectural-curriculum-v1.json"
DEFAULT_SELECTION = HERE / "habs-corpus.json"
DEFAULT_CORPUS = HERE / "out" / "loc-habs" / "corpus"
DEFAULT_OUT = HERE / "out" / "architectural-curriculum" / "habs-v1"
DEFAULT_OLLAMA = os.environ.get("COMFY_OLLAMA", "http://127.0.0.1:11434")
ENGINE = "architectural-curriculum/1.0.0"
LEVELS = ("A0_TRIAGED", "G1_METRIC_GRAPH", "F1_MASSING", "F2_WEATHER_SHELL")
Image = ImageOps = None
np = None
OCR_ENGINE = None


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--charter", type=Path, default=DEFAULT_CHARTER)
    common.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    common.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT)
    common.add_argument("--ollama", default=DEFAULT_OLLAMA)
    common.add_argument("--model")
    common.add_argument("--fixture-vision", action="store_true",
                        help="test-only deterministic semantics; never research evidence")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight", parents=[common])
    run = sub.add_parser("run", parents=[common])
    run.add_argument("--no-browser", action="store_true")
    run.add_argument("--max-buildings", type=int, default=0,
                     help="diagnostic prefix only; a partial run cannot pass")
    sub.add_parser("verify", parents=[common])
    serve = sub.add_parser("serve", parents=[common])
    serve.add_argument("--port", type=int, default=8876)
    return parser.parse_args()


def load_imaging():
    global Image, ImageOps, np
    if Image is None:
        from PIL import Image as pillow_image, ImageOps as pillow_ops
        import numpy as numpy_module
        pillow_image.MAX_IMAGE_PIXELS = None
        Image, ImageOps, np = pillow_image, pillow_ops, numpy_module


def compact_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest_file(path, chunk=1024 * 1024):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while block := handle.read(chunk):
            h.update(block)
    return h.hexdigest()


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".",
                                     suffix=".tmp", delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_json(path, value):
    atomic_bytes(path, canonical_bytes(value))


def immutable_bytes(path, data):
    path = Path(path)
    if path.is_file():
        if path.read_bytes() != data:
            raise RuntimeError(f"immutable artifact changed: {path}")
        return False
    atomic_bytes(path, data)
    return True


def immutable_json(path, value):
    return immutable_bytes(path, canonical_bytes(value))


def safe_child(root, relative):
    root = Path(root).resolve()
    pure = PurePosixPath(str(relative).replace("\\", "/"))
    if pure.is_absolute() or ".." in pure.parts:
        raise RuntimeError(f"unsafe relative path: {relative}")
    result = (root / Path(*pure.parts)).resolve()
    if result != root and root not in result.parents:
        raise RuntimeError(f"path escapes root: {relative}")
    return result


def portable_guard(value, label="artifact"):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    forbidden = (r"C:\\", r"C:/", r"E:\\", r"E:/", "file:///")
    found = [prefix for prefix in forbidden if prefix.lower() in text.lower()]
    if found:
        raise RuntimeError(f"{label} contains machine-specific path: {found[0]}")


def deterministic_zip(path, members):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".",
                                     suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as archive:
            for name in sorted(members):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, members[name])
        data = temporary.read_bytes()
        immutable_bytes(path, data)
    finally:
        temporary.unlink(missing_ok=True)


def package_versions():
    names = ["Pillow", "numpy", "opencv-python", "onnxruntime",
             "rapidocr", "scikit-learn"]
    versions = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def pinned_versions():
    pins = {}
    for line in (HERE / "requirements-architectural-curriculum.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, version = line.split("==", 1)
        pins[name.lower()] = version
    return pins


def load_inputs(args):
    charter = json.loads(args.charter.read_text(encoding="utf-8"))
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    expected = charter["selection"]
    actual_selection_sha = digest_file(args.selection)
    if actual_selection_sha != expected["sha256"]:
        raise RuntimeError("frozen HABS selection hash changed")
    buildings = selection.get("buildings", [])
    if len(buildings) != expected["buildings"]:
        raise RuntimeError("frozen building count changed")
    records = []
    for selected in buildings:
        building_id = selected["loc_id"]
        directory = safe_child(args.corpus, building_id)
        manifest_path, metadata_path = directory / "manifest.json", directory / "metadata.json"
        if not manifest_path.is_file() or not metadata_path.is_file():
            raise RuntimeError(f"corpus record incomplete: {building_id}")
        records.append({
            "id": building_id,
            "building_type": selected["building_type"],
            "selection_reason": selected["selection_reason"],
            "directory": directory,
            "manifest_path": manifest_path,
            "metadata_path": metadata_path,
            "manifest": json.loads(manifest_path.read_text(encoding="utf-8")),
            "metadata": json.loads(metadata_path.read_text(encoding="utf-8")),
        })
    return charter, selection, records


def verify_sources(records, full_hash=True):
    totals = {"buildings": len(records), "drawings": 0, "bytes": 0,
              "hashes_verified": 0, "errors": []}
    manifest_hashes = {}
    for record in records:
        manifest_hashes[record["id"]] = digest_file(record["manifest_path"])
        drawings = record["manifest"].get("drawings", [])
        totals["drawings"] += len(drawings)
        for drawing in drawings:
            download = drawing.get("download") or {}
            try:
                path = safe_child(record["directory"], download["local_path"])
                if not path.is_file():
                    raise RuntimeError("missing file")
                size = path.stat().st_size
                if size != download["bytes"]:
                    raise RuntimeError(f"byte mismatch {size} != {download['bytes']}")
                totals["bytes"] += size
                if full_hash:
                    actual = digest_file(path)
                    if actual != download["sha256"]:
                        raise RuntimeError("SHA-256 mismatch")
                    totals["hashes_verified"] += 1
            except Exception as error:
                totals["errors"].append({"building_id": record["id"],
                                          "sheet_index": drawing.get("sheet_index"),
                                          "error": str(error)})
    totals["status"] = "PASS" if not totals["errors"] else "FAIL"
    totals["manifest_hashes"] = manifest_hashes
    return totals


def request_json(url, payload=None, timeout=3):
    data = compact_bytes(payload) if payload is not None else None
    request = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="POST" if payload is not None else "GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def vision_preflight(endpoint, model):
    endpoint = endpoint.rstrip("/")
    try:
        tags = request_json(endpoint + "/api/tags", timeout=3)
        models = tags.get("models", [])
        aliases = {str(item.get("name")) for item in models} | {
            str(item.get("model")) for item in models}
        if model not in aliases and model + ":latest" not in aliases:
            return {"status": "BLOCKED", "endpoint": endpoint, "model": model,
                    "reason": "required model is not installed", "available": sorted(aliases)}
        show = request_json(endpoint + "/api/show", {"model": model}, timeout=10)
        tag = next((item for item in models
                    if item.get("name") in (model, model + ":latest") or
                    item.get("model") in (model, model + ":latest")), {})
        return {"status": "READY", "endpoint": endpoint, "model": model,
                "model_digest": tag.get("digest") or digest_bytes(compact_bytes(show)),
                "details_sha256": digest_bytes(compact_bytes(show)),
                "details": show.get("details", {})}
    except Exception as error:
        return {"status": "BLOCKED", "endpoint": endpoint, "model": model,
                "reason": f"{type(error).__name__}: {error}"}


def dependency_preflight(fixture=False):
    versions = package_versions()
    required = ["Pillow", "numpy"] if fixture else list(versions)
    missing = [name for name in required if not versions.get(name)]
    pins = pinned_versions()
    mismatched = []
    if not fixture:
        for name, actual in versions.items():
            expected = pins.get(name.lower())
            if expected and actual and actual != expected:
                mismatched.append({"package": name, "expected": expected, "actual": actual})
    modules = {}
    for name in ("PIL", "numpy", "cv2", "onnxruntime", "rapidocr", "sklearn"):
        try:
            modules[name] = bool(importlib.util.find_spec(name))
        except (ImportError, ValueError):
            modules[name] = False
    model_files = []
    if not fixture and not missing:
        try:
            module_root = Path(importlib.import_module("rapidocr").__file__).resolve().parent
            for path in sorted(module_root.rglob("*.onnx")):
                model_files.append({"name": path.relative_to(module_root).as_posix(),
                                    "sha256": digest_file(path), "bytes": path.stat().st_size})
        except Exception as error:
            mismatched.append({"package": "rapidocr-models", "error": str(error)})
    status = "READY" if not missing and not mismatched else "BLOCKED"
    return {"status": status, "versions": versions, "modules": modules,
            "pins": pins, "missing": missing, "mismatched": mismatched,
            "ocr_model_files": model_files, "python": sys.version.split()[0],
            "executable_sha256": digest_file(sys.executable)}


def run_preflight(args, full_hash=True):
    charter, selection, records = load_inputs(args)
    source = verify_sources(records, full_hash=full_hash)
    model = args.model or charter["automation_boundary"]["vision_model"]
    dependencies = dependency_preflight(args.fixture_vision)
    vision = ({"status": "FIXTURE_SIMULATION", "model": "deterministic-fixture/v1",
               "model_digest": digest_bytes(b"deterministic-fixture/v1")}
              if args.fixture_vision else vision_preflight(args.ollama, model))
    blockers = []
    if source["status"] != "PASS": blockers.append("corpus integrity failed")
    if dependencies["status"] != "READY": blockers.append("OCR/CV dependencies unavailable")
    if vision["status"] not in ("READY", "FIXTURE_SIMULATION"):
        blockers.append("pinned local vision model unavailable")
    receipt = {
        "schema": "architectural-curriculum-preflight/v1",
        "status": ("SIMULATION_READY" if args.fixture_vision and not blockers else
                   "READY" if not blockers else "BLOCKED"),
        "engine": ENGINE,
        "mode": "FIXTURE_SIMULATION" if args.fixture_vision else "REAL",
        "source": source,
        "dependencies": dependencies,
        "vision": vision,
        "blockers": blockers,
        "live_safety": {"valheim_contacted": False, "request_sent": False,
                        "world_mutated": False},
    }
    return receipt, charter, selection, records


def find_browser():
    """Reuse the browser locator from the already accepted WebGPU experiment."""
    sys.path.insert(0, str(HERE))
    import probe_architectural_roundtrip as roundtrip
    return roundtrip.find_browser()


class CurriculumProject:
    def __init__(self, args, preflight, charter, records):
        browser_requested = not getattr(args, "no_browser", False)
        browser = find_browser() if browser_requested else None
        corpus_state = {record["id"]: preflight["source"]["manifest_hashes"][record["id"]]
                        for record in records}
        identity = {
            "engine": ENGINE,
            "script_sha256": digest_file(Path(__file__)),
            "charter_sha256": digest_file(args.charter),
            "selection_sha256": digest_file(args.selection),
            "schemas_sha256": digest_file(HERE / "architectural-curriculum-schemas-v1.json"),
            "requirements_sha256": digest_file(HERE / "requirements-architectural-curriculum.txt"),
            "webgpu_runtime_sha256": digest_file(HERE / "probe_architectural_roundtrip.py"),
            "runtime": preflight["dependencies"],
            "vision": preflight["vision"],
            "corpus": corpus_state,
            "mode": preflight["mode"],
            "scope": {"diagnostic_max_buildings": getattr(args, "max_buildings", 0)},
            "rendering": {"requested": browser_requested,
                          "browser_available": browser is not None,
                          "browser_sha256": digest_file(browser) if browser else None},
        }
        self.revision = digest_bytes(compact_bytes(identity))[:20]
        self.root = args.out.resolve()
        self.rev = self.root / "revisions" / self.revision
        self.exports = self.root / "exports"
        self.mode = preflight["mode"]
        self.charter = charter
        self.ollama = args.ollama
        self.model = args.model or charter["automation_boundary"]["vision_model"]
        self.browser = browser
        self.stats = {"executed": [], "cached": [], "ocr_calls": 0,
                      "vision_calls": 0, "source_downloads": 0}
        self.rev.mkdir(parents=True, exist_ok=True)
        self.exports.mkdir(parents=True, exist_ok=True)
        atomic_bytes(self.root / "HEAD", (self.revision + "\n").encode("ascii"))
        immutable_json(self.rev / "identity.json", identity)

    def stage(self, name, input_value, builder):
        receipt_path = self.rev / "receipts" / f"{name}.json"
        fingerprint = digest_bytes(compact_bytes({"engine": ENGINE, "input": input_value}))
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("fingerprint") == fingerprint:
                valid = True
                for item in receipt.get("outputs", []):
                    path = safe_child(self.rev, item["path"])
                    if not path.is_file() or digest_file(path) != item["sha256"]:
                        valid = False
                        break
                if valid:
                    self.stats["cached"].append(name)
                    return receipt.get("facts", {})
        outputs, facts = builder()
        rows = []
        for path in outputs:
            path = Path(path).resolve()
            relative = path.relative_to(self.rev).as_posix()
            rows.append({"path": relative, "sha256": digest_file(path),
                         "bytes": path.stat().st_size})
        receipt = {"schema": "architectural-curriculum-stage-receipt/v1",
                   "stage": name, "fingerprint": fingerprint,
                   "outputs": rows, "facts": facts}
        immutable_json(receipt_path, receipt)
        self.stats["executed"].append(name)
        return facts


def normalize_title(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


ROLE_WORDS = {
    "plan": ("plan", "floor plan", "site plan", "loft"),
    "elevation": ("elevation", "facade"),
    "section": ("section", "cut-away", "cutaway"),
    "detail": ("detail", "jamb", "molding", "window", "door"),
}


def catalog_role_hints(drawing):
    hints = set(drawing.get("roles") or [])
    title = normalize_title(drawing.get("title")).lower()
    for role, words in ROLE_WORDS.items():
        if any(word in title for word in words):
            hints.add(role)
    return sorted(hints)


def normalize_sheet(source, target, max_side=2400):
    load_imaging()
    with Image.open(source) as opened:
        original_size = list(opened.size)
        image = ImageOps.autocontrast(opened.convert("L"))
        image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        array = np.asarray(image, dtype=np.uint8)
        mask = array < 210
        ys, xs = np.where(mask)
        if len(xs):
            bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        else:
            bbox = [0, 0, image.width, image.height]
        normalized = Image.fromarray(array, mode="L")
        buffer = io.BytesIO()
        normalized.save(buffer, "PNG", optimize=False, compress_level=9)
        immutable_bytes(target, buffer.getvalue())
        row_projection = mask.mean(axis=1)
        col_projection = mask.mean(axis=0)
        return {
            "source_pixels": original_size,
            "normalized_pixels": [image.width, image.height],
            "ink_bbox": bbox,
            "ink_fraction": round(float(mask.mean()), 8),
            "dense_rows": int((row_projection > 0.18).sum()),
            "dense_columns": int((col_projection > 0.18).sum()),
            "normalized_sha256": digest_bytes(buffer.getvalue()),
        }


def fixture_ocr(drawing):
    title = normalize_title(drawing.get("title"))
    roles = catalog_role_hints(drawing)
    tokens = [{"text": token, "confidence": 1.0, "region": [0.05, 0.05, 0.95, 0.12],
               "fixture": True} for token in ([title] + roles)]
    return {"schema": "architectural-ocr/v1", "engine": "fixture-title-tokenizer/v1",
            "tokens": tokens, "numeric_authority": False,
            "warning": "SIMULATION_NOT_EVIDENCE"}


def real_ocr(image_path):
    global OCR_ENGINE
    from rapidocr import RapidOCR
    if OCR_ENGINE is None:
        OCR_ENGINE = RapidOCR()
    result = OCR_ENGINE(str(image_path))
    boxes = result.boxes if result and result.boxes is not None else []
    texts = result.txts if result and result.txts is not None else []
    scores = result.scores if result and result.scores is not None else []
    load_imaging()
    with Image.open(image_path) as image:
        width, height = image.size
    tokens = []
    for box, text, score in zip(boxes, texts, scores):
        xs = [float(point[0]) for point in box]
        ys = [float(point[1]) for point in box]
        tokens.append({"text": str(text), "confidence": round(float(score), 6),
                       "region": [min(xs) / width, min(ys) / height,
                                  max(xs) / width, max(ys) / height]})
    return {"schema": "architectural-ocr/v1", "engine": "RapidOCR/3.9.2",
            "tokens": tokens, "numeric_authority": True}


def stable_number(building_id, slot, low, high):
    raw = hashlib.sha256(f"fixture:{building_id}:{slot}".encode()).digest()
    fraction = int.from_bytes(raw[:4], "big") / (2**32 - 1)
    return low + fraction * (high - low)


def inferred_floor_count(titles, building_type):
    text = " ".join(titles).lower()
    if re.search(r"third floor|three[- ]story|3[- ]story", text): return 3
    if re.search(r"second floor|first and second|two[- ]story|2[- ]story|hayloft|loft", text): return 2
    if "floor plans" in text and building_type in ("farmhouse", "house"): return 2
    return 1


def fixture_vision(record, sheets, lessons):
    titles = [item["title"] for item in sheets]
    floors = inferred_floor_count(titles, record["building_type"])
    base = {"cabin": (5.2, 10.5), "barn": (8.0, 17.0),
            "farmhouse": (7.5, 15.0), "house": (6.5, 12.0)}[record["building_type"]]
    width = stable_number(record["id"], "width", base[0], base[1])
    depth = stable_number(record["id"], "depth", base[0] * 0.65, base[1] * 0.78)
    mean_height = floors * stable_number(record["id"], "storey", 2.55, 3.15)
    ridge = mean_height + stable_number(record["id"], "roof", 1.0, 2.5)
    plan_sheet = next((s for s in sheets if "plan" in s["catalog_role_hints"]), sheets[0])
    vertical_sheet = next((s for s in sheets if set(s["catalog_role_hints"]) &
                           {"elevation", "section"}), sheets[-1])
    window_count = 2 + int(stable_number(record["id"], "windows", 0, 5))
    return {
        "schema": "architectural-vision-proposal/v1",
        "mode": "FIXTURE_SIMULATION", "warning": "SIMULATION_NOT_EVIDENCE",
        "views": [
            {"sheet_index": plan_sheet["sheet_index"], "kind": "plan",
             "bbox": [0.12, 0.40, 0.72, 0.88], "confidence": 0.99},
            {"sheet_index": vertical_sheet["sheet_index"], "kind": "elevation",
             "bbox": [0.12, 0.10, 0.78, 0.38], "confidence": 0.99},
        ],
        "building": {"floor_count": floors, "roof_type": "gable",
                     "footprint_width_m": round(width, 3),
                     "footprint_depth_m": round(depth, 3),
                     "mean_height_m": round(mean_height, 3),
                     "ridge_height_m": round(ridge, 3)},
        "dimension_evidence": [
            {"sheet_index": plan_sheet["sheet_index"], "text": f"{width:.3f} m",
             "semantic": "width", "start": [0.12, 0.90], "end": [0.72, 0.90],
             "value_m": round(width, 3), "fixture": True},
            {"sheet_index": plan_sheet["sheet_index"], "text": f"{depth:.3f} m",
             "semantic": "depth", "start": [0.75, 0.40], "end": [0.75, 0.88],
             "value_m": round(depth, 3), "fixture": True},
            {"sheet_index": vertical_sheet["sheet_index"], "text": f"{ridge:.3f} m",
             "semantic": "ridge_height", "start": [0.82, 0.38], "end": [0.82, 0.10],
             "value_m": round(ridge, 3), "fixture": True},
        ],
        "openings": ([{"kind": "door", "wall": "south", "u": 0.48,
                        "confidence": 0.9}] +
                     [{"kind": "window", "wall": side, "u": u, "confidence": 0.85}
                      for side, u in (["south", .22], ["south", .76], ["north", .25],
                                      ["north", .72], ["west", .5], ["east", .5])[:window_count]]),
        "lesson_examples_used": [item["building_id"] for item in lessons[:3]],
    }


VISION_PROMPT = """You are classifying a measured HABS architectural drawing sheet.
Return only JSON with this shape:
{"views":[{"sheet_index":1,"kind":"plan|elevation|section|detail|site|unknown","bbox":[x0,y0,x1,y1],"confidence":0.0}],
 "building":{"floor_count":1,"roof_type":"gable|hip|shed|flat|complex|unknown"},
 "dimension_evidence":[{"sheet_index":1,"text":"exact visible text","semantic":"width|depth|eave_height|ridge_height|storey_height|other","start":[x,y],"end":[x,y],"confidence":0.0}],
 "openings":[{"kind":"door|window","wall":"south|north|west|east|unknown","u":0.0,"confidence":0.0}]}
Input images are attached in sheet_index order beginning at 1. Coordinates are normalized
0..1 within the named sheet. Only include things actually visible. Do not calculate,
convert, or invent dimensions. The deterministic OCR/geometry lane will validate every
number and reject unsupported proposals."""


def extract_json_object(text):
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except Exception:
        match = re.search(r"\{.*\}", text or "", re.S)
        if not match: return None
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else None
        except Exception:
            return None


def real_vision(endpoint, model, image_paths, lessons):
    images = []
    for path in image_paths:
        with Image.open(path) as opened:
            image = opened.convert("RGB")
            image.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
            buffer = io.BytesIO(); image.save(buffer, "JPEG", quality=88)
            images.append(base64.b64encode(buffer.getvalue()).decode("ascii"))
    lesson_text = ""
    if lessons:
        examples = [{key: item.get(key) for key in ("building_id", "features", "route")}
                    for item in lessons[:3]]
        lesson_text = "\nPrior mechanically accepted examples (semantics only):\n" + json.dumps(examples)
    payload = {"model": model, "prompt": VISION_PROMPT + lesson_text,
               "images": images, "stream": False, "format": "json",
               "keep_alive": "20m", "options": {"temperature": 0}}
    response = request_json(endpoint.rstrip("/") + "/api/generate", payload, timeout=300)
    parsed = extract_json_object(response.get("response", ""))
    if parsed is None:
        raise RuntimeError("vision reply was not a JSON object")
    parsed.update({"schema": "architectural-vision-proposal/v1", "mode": "REAL",
                   "model": response.get("model", model),
                   "response_sha256": digest_bytes(compact_bytes(response)),
                   "lesson_examples_used": [item["building_id"] for item in lessons[:3]]})
    return parsed


DIMENSION_RE = re.compile(
    r"(?:(?P<feet>\d+(?:\.\d+)?)\s*['′](?:\s*[- ]?\s*(?P<inches>\d+(?:\.\d+)?(?:\s+\d+/\d+)?)\s*[\"″])?|(?P<metric>\d+(?:\.\d+)?)\s*(?P<unit>meters?|metres?|m)\b)",
    re.I)


def mixed_number(text):
    parts = str(text).strip().split()
    total = 0.0
    for part in parts:
        if "/" in part:
            numerator, denominator = part.split("/", 1)
            total += float(numerator) / float(denominator)
        else:
            total += float(part)
    return total


def parse_dimension(text):
    source = str(text or "")
    if "=" in source:
        return None
    match = DIMENSION_RE.search(source)
    if not match: return None
    leading = source[:match.start()]
    if re.search(r"\d\s*:\s*$", leading) or re.search(r"\d\s*[-–—]\s*$", leading):
        return None
    if match.group("metric"):
        # Graphic-scale legends are calibration aids, not observations of the
        # building.  Single-letter ``M`` is also too ambiguous when it follows
        # a sheet/reference number (``NO.6 M.`` was a real corpus false hit).
        if re.search(r"\b(?:metric|scale)\b", source, re.I):
            return None
        if match.group("unit").lower() == "m":
            if re.match(r"\s*\.", source[match.end():]):
                return None
            if re.search(r"\b(?:no|sheet)\s*\.?\s*$", leading, re.I):
                return None
        return float(match.group("metric"))
    # Do not accept a valid feet-only prefix when OCR has visibly corrupted the
    # following inches (for example ``2'-6 1/4°``).  A partial parse is more
    # dangerous than an unresolved measurement in this pipeline.
    trailing = source[match.end():]
    if (not match.group("inches") and
            re.search(r"\b\d+\s*[x×]\s*\d+\b", source[:match.start()], re.I)):
        return None
    if (not match.group("inches") and
            (re.match(r"\s*[A-Za-z]", trailing) or
             re.match(r"\s*[-–—./]?\s*\d", trailing) or
             re.match(r"\s*[-–—.]\s*$", trailing))):
        return None
    feet = float(match.group("feet"))
    inches = mixed_number(match.group("inches")) if match.group("inches") else 0.0
    return feet * 0.3048 + inches * 0.0254


def token_matches(text, tokens):
    needle = re.sub(r"[^a-z0-9]", "", str(text).lower())
    if not needle: return False
    normalized = [(re.sub(r"[^a-z0-9]", "", token["text"].lower()),
                   float(token.get("confidence", 0))) for token in tokens]
    for start in range(len(normalized)):
        haystack, confidence = "", 1.0
        for offset in range(4):
            if start + offset >= len(normalized): break
            value, score = normalized[start + offset]
            haystack += value
            confidence = min(confidence, score)
            if haystack and (needle in haystack or haystack in needle) and confidence >= 0.5:
                return True
    return False


def validate_proposal(record, sheets, proposal, fixture=False):
    by_index = {sheet["sheet_index"]: sheet for sheet in sheets}
    roles = defaultdict(set)
    valid_views = []
    for view in proposal.get("views", []):
        try:
            sheet = by_index[int(view["sheet_index"])]
            bbox = [float(value) for value in view["bbox"]]
            if len(bbox) != 4 or any(value < 0 or value > 1 for value in bbox): continue
            if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]: continue
            kind = str(view["kind"]).lower()
            if kind not in ("plan", "elevation", "section", "detail", "site", "unknown"): continue
            roles[sheet["sheet_index"]].add(kind)
            valid_views.append({"sheet_index": sheet["sheet_index"], "kind": kind,
                                "bbox": bbox, "confidence": float(view.get("confidence", 0))})
        except (KeyError, TypeError, ValueError):
            continue
    evidence = []
    for item in proposal.get("dimension_evidence", []):
        try:
            sheet = by_index[int(item["sheet_index"])]
            value = float(item["value_m"]) if fixture and item.get("value_m") else parse_dimension(item["text"])
            start, end = [float(v) for v in item["start"]], [float(v) for v in item["end"]]
            if value is None or not (0.15 <= value <= 100): continue
            if len(start) != 2 or len(end) != 2 or any(v < 0 or v > 1 for v in start + end): continue
            if not fixture and not token_matches(item["text"], sheet["ocr"]["tokens"]): continue
            width, height = sheet["raster"]["normalized_pixels"]
            dx, dy = (end[0] - start[0]) * width, (end[1] - start[1]) * height
            pixels = math.hypot(dx, dy)
            if pixels < 12: continue
            evidence.append({"sheet_index": sheet["sheet_index"], "text": item["text"],
                             "semantic": str(item.get("semantic", "other")),
                             "value_m": round(value, 6), "pixel_span": round(pixels, 3),
                             "scale_m_per_px": 0.01 if fixture else value / pixels,
                             "source_sha256": sheet["source_sha256"],
                             "source_url": sheet["source_url"],
                             "region": [*start, *end], "fixture": fixture})
        except (KeyError, TypeError, ValueError):
            continue
    building = proposal.get("building") if isinstance(proposal.get("building"), dict) else {}
    floors = int(building.get("floor_count") or 0)
    if floors < 1 or floors > 8: floors = 0
    return valid_views, evidence, floors, str(building.get("roof_type", "unknown")), roles


def measurements(record, sheets, proposal, fixture=False):
    views, evidence, floors, roof_type, roles = validate_proposal(record, sheets, proposal, fixture)
    semantic = defaultdict(list)
    for item in evidence: semantic[item["semantic"]].append(item["value_m"])
    building = proposal.get("building", {})
    if fixture:
        width = float(building["footprint_width_m"])
        depth = float(building["footprint_depth_m"])
        mean_height = float(building["mean_height_m"])
        ridge = float(building["ridge_height_m"])
    else:
        width = (sum(semantic["width"]) / len(semantic["width"])) if semantic["width"] else None
        depth = (sum(semantic["depth"]) / len(semantic["depth"])) if semantic["depth"] else None
        height_values = semantic["ridge_height"] or semantic["eave_height"] or semantic["storey_height"]
        ridge = max(height_values) if height_values else None
        mean_height = (sum(height_values) / len(height_values)) if height_values else None
    scales = [item["scale_m_per_px"] for item in evidence]
    if len(scales) >= 2 and min(scales) > 0:
        scale_spread = (max(scales) - min(scales)) / (sum(scales) / len(scales))
    else:
        scale_spread = None
    repeated_errors = []
    for name, values in semantic.items():
        if len(values) >= 2:
            spread = max(values) - min(values)
            repeated_errors.append({"semantic": name, "absolute_m": spread,
                                    "ratio": spread / max(sum(values) / len(values), 1e-9)})
    assertions = []
    for name, value in (("footprint-width", width), ("footprint-depth", depth),
                        ("mean-height", mean_height), ("ridge-height", ridge)):
        related = [item for item in evidence if name.split("-")[0] in item["semantic"] or
                   (name == "footprint-width" and item["semantic"] == "width") or
                   (name == "footprint-depth" and item["semantic"] == "depth")]
        assertions.append({"id": name, "status": "observed" if value is not None else "unresolved",
                           "claim": f"{name} = {value:.3f} m" if value is not None else f"{name} unresolved",
                           "provenance": [{"source_sha256": item["source_sha256"],
                                           "source_url": item["source_url"],
                                           "sheet_index": item["sheet_index"],
                                           "region": item["region"]} for item in related]})
    return {
        "views": views, "dimension_evidence": evidence, "floor_count": floors,
        "roof_type": roof_type, "width_m": width, "depth_m": depth,
        "mean_height_m": mean_height, "ridge_height_m": ridge,
        "scale_anchor_count": len(scales), "scale_spread_ratio": scale_spread,
        "cross_view_errors": repeated_errors,
        "maximum_cross_view_error_m": max((item["absolute_m"] for item in repeated_errors), default=0.0),
        "maximum_cross_view_error_ratio": max((item["ratio"] for item in repeated_errors), default=0.0),
        "roles": {str(key): sorted(value) for key, value in roles.items()},
        "assertions": assertions,
    }


def route_assessment(record, result, charter, fixture=False):
    promotion = charter["promotion"]
    kinds = {view["kind"] for view in result["views"]}
    a0 = "plan" in kinds and bool(kinds & {"elevation", "section"})
    numeric = (all(result.get(key) is not None for key in
                   ("width_m", "depth_m", "mean_height_m", "ridge_height_m")) and
               result.get("floor_count", 0) > 0)
    anchor_ok = result["scale_anchor_count"] >= promotion["minimum_independent_scale_anchors"]
    spread = result["scale_spread_ratio"]
    scale_ok = spread is not None and spread <= promotion["maximum_scale_anchor_spread_ratio"]
    cross_view_ok = (result["maximum_cross_view_error_m"] <= promotion["maximum_cross_view_error_m"] and
                     result["maximum_cross_view_error_ratio"] <= promotion["maximum_cross_view_error_ratio"])
    plausible = numeric and result["width_m"] > 1.5 and result["depth_m"] > 1.5 and result["ridge_height_m"] > 2
    g1 = a0 and anchor_ok and scale_ok and cross_view_ok and plausible
    gates = [
        {"id": "plan-and-vertical-view", "status": "PASS" if a0 else "FAIL",
         "actual": sorted(kinds)},
        {"id": "numeric-envelope", "status": "PASS" if numeric else "FAIL",
         "actual": numeric},
        {"id": "scale-anchors", "status": "PASS" if anchor_ok else "FAIL",
         "actual": result["scale_anchor_count"], "limit": promotion["minimum_independent_scale_anchors"]},
        {"id": "scale-spread", "status": "PASS" if scale_ok else "FAIL",
         "actual": spread, "limit": promotion["maximum_scale_anchor_spread_ratio"]},
        {"id": "cross-view-consistency", "status": "PASS" if cross_view_ok else "FAIL",
         "actual": {"metres": result["maximum_cross_view_error_m"],
                    "ratio": result["maximum_cross_view_error_ratio"]},
         "limit": {"metres": promotion["maximum_cross_view_error_m"],
                   "ratio": promotion["maximum_cross_view_error_ratio"]}},
        {"id": "plausible-envelope", "status": "PASS" if plausible else "FAIL",
         "actual": plausible},
    ]
    return {"A0_TRIAGED": a0, "G1_METRIC_GRAPH": g1,
            "F1_MASSING": False, "F2_WEATHER_SHELL": False,
            "approved": "G1_METRIC_GRAPH" if g1 else "A0_TRIAGED" if a0 else "HELD",
            "gates": gates, "fixture": fixture}


def make_graph(record, result, route, proposal, mode):
    if not route["G1_METRIC_GRAPH"]:
        return None
    width, depth = result["width_m"], result["depth_m"]
    floors = result["floor_count"]
    floor_height = max(2.2, result["mean_height_m"] / floors)
    graph = {
        "schema": "architectural-building-graph/v1",
        "id": f"habs-{record['id']}-automatic-g1",
        "building_id": record["id"], "label": record["manifest"]["title"],
        "mode": mode,
        "coordinate_frames": {
            "source_geo": "catalog provenance only",
            "building_local": {"units": "metres", "handedness": "right",
                               "axes": {"x": "plan-right", "y": "height", "z": "plan-up"},
                               "origin": "automatic primary-plan bounding-box lower-left at L0"},
            "valheim_world": "unresolved"
        },
        "dimensions": {"width_m": round(width, 6), "depth_m": round(depth, 6),
                       "mean_height_m": round(result["mean_height_m"], 6),
                       "ridge_height_m": round(result["ridge_height_m"], 6),
                       "floor_count": floors},
        "levels": [{"id": f"L{index}", "finished_floor_y_m": round(index * floor_height, 4),
                    "status": "observed" if index < floors else "inferred"}
                   for index in range(floors)],
        "footprints": [{"id": "primary", "level": "L0", "status": "inferred",
                        "polygon_xz": [[0, 0], [width, 0], [width, depth], [0, depth], [0, 0]]}],
        "roofs": [{"id": "primary-roof", "kind": result["roof_type"],
                   "eave_y_m": round(result["mean_height_m"], 4),
                   "ridge_y_m": round(result["ridge_height_m"], 4),
                   "status": "observed" if result["roof_type"] != "unknown" else "unresolved"}],
        "openings": [], "assertions": result["assertions"],
        "source_resources": [{"sheet_index": item["sheet_index"],
                              "source_sha256": item["source_sha256"],
                              "source_url": item["source_url"]}
                             for item in result["dimension_evidence"]],
    }
    for index, opening in enumerate(proposal.get("openings", [])):
        try:
            kind = str(opening["kind"])
            wall = str(opening["wall"])
            u = float(opening["u"])
            confidence = float(opening.get("confidence", 0))
            if kind not in ("door", "window") or wall not in ("south", "north", "west", "east"): continue
            if not 0.05 <= u <= 0.95 or confidence < 0.7: continue
            graph["openings"].append({"id": f"{kind}-{index+1}", "kind": kind,
                                      "wall": wall, "u": u, "confidence": confidence,
                                      "status": "inferred"})
        except (KeyError, TypeError, ValueError):
            continue
    graph["id"] += "-" + digest_bytes(compact_bytes(graph))[:12]
    return graph


def centers(span, module=2.0):
    count = max(1, math.ceil(span / module))
    if count == 1: return [span / 2]
    return [module / 2 + index * (span - module) / (count - 1) for index in range(count)]


def yaw_quaternion(degrees):
    angle = math.radians(degrees) / 2
    return [0.0, round(math.sin(angle), 8), 0.0, round(math.cos(angle), 8)]


def compile_generic(graph, maximum_pieces):
    width, depth = graph["dimensions"]["width_m"], graph["dimensions"]["depth_m"]
    floors = graph["dimensions"]["floor_count"]
    mean_height, ridge = graph["dimensions"]["mean_height_m"], graph["dimensions"]["ridge_height_m"]
    floor_height = mean_height / max(floors, 1)
    openings = defaultdict(list)
    for item in graph["openings"]: openings[item["wall"]].append(item)
    pieces = []

    def add(prefab, family, position, yaw=0, role="massing", source=None):
        pieces.append({"index": len(pieces), "prefab": prefab, "category": "BuildingWorkbench",
                       "family": family, "position": [round(float(v), 4) for v in position],
                       "rotation": yaw_quaternion(yaw), "yaw_degrees": yaw,
                       "semantic_role": role, "source": source})

    xs, zs = centers(width), centers(depth)
    for level in range(floors):
        y0 = level * floor_height
        for x in xs:
            for z in zs: add("wood_floor", "floor", [x, y0, z], role=f"L{level}:floor")
        y = y0 + min(1.0, floor_height / 2)
        for wall, span, fixed, axis, yaw in (
            ("south", width, 0, "x", 0), ("north", width, depth, "x", 0),
            ("west", depth, 0, "z", 90), ("east", depth, width, "z", 90)):
            wall_centers = centers(span)
            for ordinal, along in enumerate(wall_centers):
                matching = next((item for item in openings[wall]
                                 if abs(along / span - item["u"]) <= max(1 / len(wall_centers), .12)), None)
                if level == 0 and matching:
                    if matching["kind"] == "door":
                        pos = [along, y0 + 1.5, fixed] if axis == "x" else [fixed, y0 + 1.5, along]
                        add("wood_door", "door", pos, yaw, "operable-opening", matching["id"])
                    else:
                        pos = [along, y0 + 1.5, fixed] if axis == "x" else [fixed, y0 + 1.5, along]
                        add("wood_window", "window", pos, yaw, "weather-window", matching["id"])
                        sill = [along, y0 + .5, fixed] if axis == "x" else [fixed, y0 + .5, along]
                        add("wood_wall_quarter", "wall", sill, yaw, "window-sill", matching["id"])
                    continue
                pos = [along, y, fixed] if axis == "x" else [fixed, y, along]
                add("woodwall", "wall", pos, yaw, f"L{level}:exterior-wall")
    roof_y = mean_height
    roof_rise = max(0.5, ridge - mean_height)
    pitch = 45 if roof_rise / max(depth / 2, .1) > .72 else 26
    roof_prefab = "wood_roof_45" if pitch == 45 else "wood_roof"
    for x in xs:
        add(roof_prefab, "roof", [x, roof_y, depth * .25], 180, "south-roof-plane")
        add(roof_prefab, "roof", [x, roof_y, depth * .75], 0, "north-roof-plane")
    counts = Counter(piece["prefab"] for piece in pieces)
    return pieces, {"schema": "architectural-generic-composition/v1",
                    "piece_count": len(pieces), "maximum_pieces": maximum_pieces,
                    "within_budget": len(pieces) <= maximum_pieces,
                    "prefab_counts": dict(sorted(counts.items())),
                    "physical_scale": 1.0, "nonuniform_scale": False,
                    "roof_planes": 2, "compiled_openings": len(graph["openings"])}


def finish_route(route, graph, composition):
    if not graph or not composition: return route
    f1 = composition["within_budget"] and composition["piece_count"] > 0
    opening_kinds = Counter(item["kind"] for item in graph["openings"])
    roof_known = graph["roofs"][0]["kind"] in ("gable", "hip", "shed", "flat")
    f2 = f1 and opening_kinds["door"] >= 1 and opening_kinds["window"] >= 2 and roof_known
    route["F1_MASSING"], route["F2_WEATHER_SHELL"] = f1, f2
    route["approved"] = "F2_WEATHER_SHELL" if f2 else "F1_MASSING" if f1 else route["approved"]
    route["gates"].extend([
        {"id": "piece-budget", "status": "PASS" if f1 else "FAIL",
         "actual": composition["piece_count"], "limit": composition["maximum_pieces"]},
        {"id": "weather-opening-minimum", "status": "PASS" if opening_kinds["door"] >= 1 and opening_kinds["window"] >= 2 else "FAIL",
         "actual": dict(opening_kinds)},
        {"id": "explicit-roof", "status": "PASS" if roof_known else "FAIL",
         "actual": graph["roofs"][0]["kind"]},
    ])
    return route


def assessment_features(measured, route, fixture=False):
    width, depth = measured.get("width_m"), measured.get("depth_m")
    return {
        "total_footprint_area_m2": (round(width * depth, 6)
                                     if width is not None and depth is not None else None),
        "mean_elevation_height_m": measured.get("mean_height_m"),
        "maximum_ridge_height_m": measured.get("ridge_height_m"),
        "floor_count": measured.get("floor_count"),
        "confidence": ("SIMULATED" if fixture else
                       "MEASURED" if route["G1_METRIC_GRAPH"] else "UNRESOLVED"),
    }


def evaluate_candidate(project, record, proposal, sheets, fixture=False):
    measured = measurements(record, sheets, proposal, fixture)
    route = route_assessment(record, measured, project.charter, fixture)
    graph = make_graph(record, measured, route, proposal, project.mode)
    pieces, composition = (compile_generic(graph, project.charter["promotion"]["maximum_pieces"])
                           if graph else ([], None))
    route = finish_route(route, graph, composition)
    unresolved = sum(item["status"] == "unresolved" for item in measured["assertions"])
    return {"proposal": proposal, "measurements": measured, "route": route,
            "graph": graph, "pieces": pieces, "composition": composition,
            "features": assessment_features(measured, route, fixture),
            "unresolved_assertions": unresolved}


def route_rank(route):
    for rank, level in reversed(list(enumerate(LEVELS, 1))):
        if route.get(level):
            return rank
    return 0


def compare_candidates(baseline, cumulative):
    baseline_passes = {gate["id"] for gate in baseline["route"]["gates"]
                       if gate["status"] == "PASS"}
    cumulative_passes = {gate["id"] for gate in cumulative["route"]["gates"]
                         if gate["status"] == "PASS"}
    regressions = sorted(baseline_passes - cumulative_passes)
    if route_rank(cumulative["route"]) < route_rank(baseline["route"]):
        regressions.append("promotion-level")
    advanced = (route_rank(cumulative["route"]) > route_rank(baseline["route"]) or
                cumulative["unresolved_assertions"] < baseline["unresolved_assertions"])
    return {"baseline_route": baseline["route"]["approved"],
            "cumulative_route": cumulative["route"]["approved"],
            "baseline_unresolved_assertions": baseline["unresolved_assertions"],
            "cumulative_unresolved_assertions": cumulative["unresolved_assertions"],
            "advanced": advanced, "regressions": sorted(set(regressions)),
            "selected": "baseline" if regressions else "cumulative"}


def perceive_baseline(project, record, target, fixture=False):
    """Run the lesson-free lane once; its result owns clustering and the control arm."""
    normalized = target / "normalized"
    sheets = []
    for drawing in record["manifest"]["drawings"]:
        download = drawing["download"]
        source = safe_child(record["directory"], download["local_path"])
        output = normalized / f"sheet-{int(drawing['sheet_index']):02d}.png"
        raster = normalize_sheet(source, output)
        ocr = fixture_ocr(drawing) if fixture else real_ocr(output)
        project.stats["ocr_calls"] += 0 if fixture else 1
        sheets.append({"sheet_index": int(drawing["sheet_index"]),
                       "title": drawing["title"], "catalog_role_hints": catalog_role_hints(drawing),
                       "source_sha256": download["sha256"], "source_url": download["source_url"],
                       "local_normalized": f"normalized/{output.name}",
                       "raster": raster, "ocr": ocr})
    proposal = (fixture_vision(record, sheets, []) if fixture else
                real_vision(project.ollama, project.model,
                            [target / item["local_normalized"] for item in sheets], []))
    project.stats["vision_calls"] += 0 if fixture else 1
    evaluated = evaluate_candidate(project, record, proposal, sheets, fixture)
    baseline = {
        "schema": "architectural-baseline/v1", "building_id": record["id"],
        "title": record["manifest"]["title"], "building_type": record["building_type"],
        "mode": project.mode, "lesson_free": True, "sheets": sheets,
        "vision": proposal, "features": evaluated["features"],
        "measurements": evaluated["measurements"], "route": evaluated["route"],
        "composition": evaluated["composition"],
        "unresolved_assertions": evaluated["unresolved_assertions"],
        "source_downloads": 0,
    }
    return baseline


def analyze_record(project, record, target, lessons, baseline, fixture=False):
    sheets = baseline["sheets"]
    base = evaluate_candidate(project, record, baseline["vision"], sheets, fixture)
    if lessons:
        proposal = (fixture_vision(record, sheets, lessons) if fixture else
                    real_vision(project.ollama, project.model,
                                [target / item["local_normalized"] for item in sheets], lessons))
        project.stats["vision_calls"] += 0 if fixture else 1
        cumulative = evaluate_candidate(project, record, proposal, sheets, fixture)
    else:
        cumulative = base
    comparison = compare_candidates(base, cumulative)
    selected = base if comparison["selected"] == "baseline" else cumulative
    comparison.update({"lesson_examples_requested": [item["building_id"] for item in lessons],
                       "lesson_examples_used": cumulative["proposal"].get("lesson_examples_used", []),
                       "lesson_bundle_status": "REJECTED_REGRESSION" if comparison["regressions"] else
                                               "ACCEPTED" if lessons else "CONTROL"})
    assessment = {
        "schema": "architectural-assessment/v1", "building_id": record["id"],
        "title": record["manifest"]["title"], "building_type": record["building_type"],
        "mode": project.mode, "sheets": sheets, "vision": selected["proposal"],
        "features": selected["features"], "measurements": selected["measurements"],
        "route": selected["route"], "composition": selected["composition"],
        "unresolved_assertions": selected["unresolved_assertions"],
        "comparison": comparison,
        "lesson_examples_used": selected["proposal"].get("lesson_examples_used", []),
        "source_downloads": 0,
    }
    return assessment, selected["graph"], selected["pieces"]


def fixture_features(record):
    floors = inferred_floor_count([drawing["title"] for drawing in record["manifest"]["drawings"]],
                                  record["building_type"])
    base = {"cabin": (5.2, 10.5), "barn": (8, 17), "farmhouse": (7.5, 15),
            "house": (6.5, 12)}[record["building_type"]]
    width = stable_number(record["id"], "width", *base)
    depth = stable_number(record["id"], "depth", base[0] * .65, base[1] * .78)
    height = floors * stable_number(record["id"], "storey", 2.55, 3.15)
    return {"area": width * depth, "height": height, "floors": floors,
            "status": "SIMULATED"}


def bootstrap_features(record, fixture=False):
    if fixture: return fixture_features(record)
    titles = [drawing["title"] for drawing in record["manifest"]["drawings"]]
    floors = inferred_floor_count(titles, record["building_type"])
    return {"area": None, "height": None, "floors": floors, "status": "UNRESOLVED",
            "reason": "real bootstrap requires completed OCR/vision assessment"}


def standardize(rows):
    load_imaging()
    values = np.asarray(rows, dtype=float)
    median = np.median(values, axis=0)
    q1, q3 = np.percentile(values, [25, 75], axis=0)
    scale = q3 - q1
    scale[scale < 1e-9] = 1.0
    return (values - median) / scale


def deterministic_kmeans(points, ids, k):
    n = len(points)
    first = min(range(n), key=lambda index: (float(points[index].sum()), ids[index]))
    selected = [first]
    while len(selected) < k:
        candidate = max((index for index in range(n) if index not in selected),
                        key=lambda index: (min(float(np.linalg.norm(points[index] - points[j]))
                                               for j in selected), ids[index]))
        selected.append(candidate)
    centroids = points[selected].copy()
    labels = np.zeros(n, dtype=int)
    for _ in range(100):
        distances = np.linalg.norm(points[:, None, :] - centroids[None, :, :], axis=2)
        next_labels = np.argmin(distances, axis=1)
        next_centroids = centroids.copy()
        for cluster in range(k):
            members = points[next_labels == cluster]
            if len(members): next_centroids[cluster] = members.mean(axis=0)
        if np.array_equal(labels, next_labels) and np.allclose(centroids, next_centroids): break
        labels, centroids = next_labels, next_centroids
    return labels, centroids


def silhouette(points, labels, k):
    if k <= 1 or len(points) <= k: return -1.0
    scores = []
    for index, point in enumerate(points):
        own = labels[index]
        own_indices = [j for j in range(len(points)) if labels[j] == own and j != index]
        a = sum(float(np.linalg.norm(point - points[j])) for j in own_indices) / len(own_indices) if own_indices else 0
        b_values = []
        for cluster in range(k):
            if cluster == own: continue
            members = [j for j in range(len(points)) if labels[j] == cluster]
            if members:
                b_values.append(sum(float(np.linalg.norm(point - points[j])) for j in members) / len(members))
        b = min(b_values) if b_values else 0
        scores.append((b - a) / max(a, b) if max(a, b) else 0)
    return sum(scores) / len(scores)


def pareto_shells(clusters):
    remaining = list(clusters)
    shells = []
    while remaining:
        frontier = []
        for item in remaining:
            dominated = any(other["area"] <= item["area"] and other["vertical"] <= item["vertical"] and
                            (other["area"] < item["area"] or other["vertical"] < item["vertical"])
                            for other in remaining if other is not item)
            if not dominated: frontier.append(item)
        shell_index = len(shells)
        frontier.sort(key=(lambda item: (item["area"], item["vertical"], item["stable_id"]))
                      if shell_index % 2 == 0 else
                      (lambda item: (item["vertical"], item["area"], item["stable_id"])))
        shells.append(frontier)
        remaining = [item for item in remaining if item not in frontier]
    return shells


def build_curriculum(records, feature_map, charter):
    resolved = [record for record in records if feature_map[record["id"]]["area"] is not None and
                feature_map[record["id"]]["height"] is not None and feature_map[record["id"]]["floors"]]
    unresolved = [record for record in records if record not in resolved]
    clusters = []
    if resolved:
        raw = [[math.log1p(feature_map[r["id"]]["area"]), feature_map[r["id"]]["height"],
                feature_map[r["id"]]["floors"]] for r in resolved]
        points, ids = standardize(raw), [record["id"] for record in resolved]
        lower = min(charter["curriculum"]["minimum_clusters"], len(resolved))
        upper = min(charter["curriculum"]["maximum_clusters"], len(resolved) - 1)
        choices = []
        for k in range(max(2, lower), max(2, upper) + 1):
            labels, centers_ = deterministic_kmeans(points, ids, k)
            choices.append((silhouette(points, labels, k), -k, labels, centers_))
        if choices:
            score, _, labels, _ = max(choices, key=lambda item: (round(item[0], 12), item[1]))
        else:
            labels, score = np.zeros(len(resolved), dtype=int), 0.0
        grouped = defaultdict(list)
        for record, label in zip(resolved, labels): grouped[int(label)].append(record)
        summaries = []
        for label, members in grouped.items():
            areas = [feature_map[r["id"]]["area"] for r in members]
            heights = [feature_map[r["id"]]["height"] for r in members]
            floors = [feature_map[r["id"]]["floors"] for r in members]
            summaries.append({"source_label": label, "members": members,
                              "area": sum(areas) / len(areas),
                              "vertical": max(sum(heights) / len(heights), max(floors) * 3),
                              "mean_height_m": sum(heights) / len(heights),
                              "max_floors": max(floors), "stable_id": min(r["id"] for r in members),
                              "silhouette": score})
        for shell_index, shell in enumerate(pareto_shells(summaries)):
            for item in shell:
                members = sorted(item["members"], key=lambda record: (
                    feature_map[record["id"]]["area"] if shell_index % 2 == 0 else feature_map[record["id"]]["height"],
                    feature_map[record["id"]]["height"] if shell_index % 2 == 0 else feature_map[record["id"]]["area"],
                    record["id"]))
                clusters.append({"id": f"C{len(clusters):02d}", "shell": shell_index,
                                 "axis_priority": "footprint" if shell_index % 2 == 0 else "height",
                                 "centroid_area_m2": round(item["area"], 3),
                                 "centroid_height_m": round(item["mean_height_m"], 3),
                                 "maximum_floors": item["max_floors"],
                                 "members": [record["id"] for record in members],
                                 "silhouette": round(item["silhouette"], 6)})
    if unresolved:
        clusters.append({"id": "CU", "shell": None, "axis_priority": "unresolved-last",
                         "centroid_area_m2": None, "centroid_height_m": None,
                         "maximum_floors": None,
                         "members": [record["id"] for record in sorted(unresolved, key=lambda r: r["id"])],
                         "silhouette": None})
    order = [building_id for cluster in clusters for building_id in cluster["members"]]
    return clusters, order


def css_page(title, body):
    return f"""<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>{title}</title><style>
:root{{--bg:#0d1519;--panel:#142127;--line:#31434b;--ink:#edf2ef;--muted:#9eb6c2;--gold:#efa92f;--ok:#66dd91;--hold:#f07167}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 Arial,sans-serif;padding:24px}}
h1,h2{{margin:.2rem 0 .7rem}}.k{{color:var(--gold);font:700 12px monospace;letter-spacing:.14em;text-transform:uppercase}}
.grid{{display:grid;grid-template-columns:minmax(0,2fr) minmax(280px,1fr);gap:16px}}.panel{{background:var(--panel);border:1px solid var(--line);padding:16px}}
.row{{display:flex;justify-content:space-between;gap:18px;border-top:1px solid var(--line);padding:9px 0}}.ok{{color:var(--ok)}}.hold{{color:var(--hold)}}
img{{width:100%;filter:invert(1);background:white}}code,pre,.mono{{font-family:Consolas,monospace;color:var(--muted)}}a{{color:#72c9e7}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}
</style>{body}""".encode("utf-8")


def write_building_views(target, assessment, graph, pieces):
    first = assessment["sheets"][0] if assessment["sheets"] else None
    image = f"<img src='../{first['local_normalized']}' alt='normalized source sheet'>" if first else ""
    route = assessment["route"]
    comparison = assessment.get("comparison", {})
    rows = "".join(f"<div class='row'><span>{item['id']}</span><b class='{'ok' if item['status']=='PASS' else 'hold'}'>{item['status']}</b></div>"
                   for item in route["gates"])
    evidence = css_page(f"{assessment['building_id']} evidence", f"<div class='k'>automatic evidence</div><h1>{assessment['title']}</h1><div class='grid'><section class='panel'>{image}</section><aside class='panel'><h2>Route</h2><p class='mono'>{route['approved']}</p>{rows}</aside></div>")
    graph_body = f"<div class='k'>metric graph</div><h1>{assessment['building_id']} · {route['approved']}</h1><div class='grid'><section class='panel'><h2>Envelope</h2><div class='row'><span>Area</span><b>{assessment['features']['total_footprint_area_m2']}</b></div><div class='row'><span>Mean height</span><b>{assessment['features']['mean_elevation_height_m']}</b></div><div class='row'><span>Floors</span><b>{assessment['features']['floor_count']}</b></div><div class='row'><span>Pieces</span><b>{len(pieces)}</b></div></section><aside class='panel'><h2>Authority</h2><pre>{json.dumps(graph or {'status':'HELD'}, indent=2)[:5000]}</pre></aside></div>"
    transfer = (f"<div class='row'><span>Lesson-free control</span><b>{comparison.get('baseline_route')}</b></div>"
                f"<div class='row'><span>Cumulative candidate</span><b>{comparison.get('cumulative_route')}</b></div>"
                f"<div class='row'><span>Selected lane</span><b>{comparison.get('selected')}</b></div>"
                f"<div class='row'><span>Advanced</span><b>{comparison.get('advanced')}</b></div>"
                f"<div class='row'><span>Regressions</span><b>{', '.join(comparison.get('regressions', [])) or 'none'}</b></div>")
    route_body = f"<div class='k'>promotion ledger</div><h1>{assessment['building_id']} · {route['approved']}</h1><div class='grid'><section class='panel'><h2>Selected gates</h2>{rows}</section><aside class='panel'><h2>Control vs cumulative</h2>{transfer}</aside></div>"
    paths = [target / "css" / "evidence.html", target / "css" / "graph.html", target / "css" / "route.html"]
    for path, data in zip(paths, (evidence, css_page("graph", graph_body), css_page("route", route_body))):
        immutable_bytes(path, data)
    return paths


def write_simple_webgpu(target, assessment, graph, pieces, browser=None):
    if not pieces: return []
    sys.path.insert(0, str(HERE))
    import probe_architectural_roundtrip as v0
    class Project:
        rev = target
    lexicon, _ = v0.load_lexicon()
    outputs, _, receipt = v0.webgpu_scene(
        Project(), pieces, lexicon, browser,
        label=f"HABS {assessment['building_id']} · {assessment['route']['approved']}",
        kind="automatic curriculum · prefab-envelope proxies")
    if browser and receipt.get("status") != "ok":
        source = ast.parse((HERE / "probe_webgpu_render.py").read_text(encoding="utf-8"))
        node_collect = next(
            ast.literal_eval(node.value) for node in source.body if isinstance(node, ast.Assign)
            for name in node.targets if isinstance(name, ast.Name) and name.id == "NODE_COLLECT")
        attempts = [receipt]
        with v0.localhost(target / "webgpu") as base:
            url = f"{base}/index.html?view=iso&mode=solid&benchmark=1&capture=1"
            for _ in range(2):
                candidate = v0.run_webgpu_benchmark(browser, url, node_collect, 40)
                attempts.append(candidate)
                if candidate.get("status") == "ok":
                    candidate["capture_status"] = v0.capture_webgpu(
                        browser, url, target / "webgpu" / "preview.png")
                    receipt = candidate
                    break
        receipt = dict(receipt)
        receipt["attempt_count"] = len(attempts)
        receipt["attempts"] = [{key: item.get(key) for key in
                                ("status", "hardware_gate", "error", "wall_ms")}
                               for item in attempts]
        portable_guard(receipt, "WebGPU retry receipt")
        atomic_json(target / "webgpu" / "browser-receipt.json", receipt)
        preview = target / "webgpu" / "preview.png"
        if preview.is_file() and preview not in outputs:
            outputs.append(preview)
    return outputs


def building_capsule(project, target, assessment, graph, pieces):
    members = {}
    for name in ("baseline.json", "assessment.json", "building.graph.json", "pieces.json",
                 "css/evidence.html", "css/graph.html", "css/route.html",
                 "webgpu/index.html", "webgpu/scene.json", "webgpu/scene.bin",
                 "webgpu/browser-receipt.json", "webgpu/preview.png"):
        path = target / PurePosixPath(name)
        if path.is_file():
            data = path.read_bytes()
            if path.suffix.lower() in (".json", ".html"):
                portable_guard(data.decode("utf-8"), name)
            members[name] = data
    for path in sorted((target / "normalized").glob("*.png")):
        members[f"normalized/{path.name}"] = path.read_bytes()
    files = {name: {"sha256": digest_bytes(data), "bytes": len(data)}
             for name, data in members.items()}
    capsule = {"schema": "creator-os-architectural-capsule/v1",
               "id": f"habs-{assessment['building_id']}-{project.revision}",
               "mode": project.mode, "building_id": assessment["building_id"],
               "approved": assessment["route"]["approved"],
               "source_policy": "master TIFFs excluded; normalized PNG evidence included; source hashes and LOC URLs remain in assessment",
               "files": files}
    members["capsule.json"] = canonical_bytes(capsule)
    bundle = target / "building.capsule.zip"
    deterministic_zip(bundle, members)
    immutable_json(target / "capsule.json", capsule)
    return [bundle, target / "capsule.json"]


def lesson_distance(features, candidate):
    if not features or not candidate: return 999
    area1, area2 = features.get("total_footprint_area_m2"), candidate.get("features", {}).get("total_footprint_area_m2")
    h1, h2 = features.get("mean_elevation_height_m"), candidate.get("features", {}).get("mean_elevation_height_m")
    f1, f2 = features.get("floor_count"), candidate.get("features", {}).get("floor_count")
    if None in (area1, area2, h1, h2, f1, f2): return 999
    return abs(math.log1p(area1) - math.log1p(area2)) + abs(h1 - h2) / 3 + abs(f1 - f2)


def retrieved_lessons(accepted, features, maximum):
    return sorted(accepted, key=lambda item: (lesson_distance(features, item), item["building_id"]))[:maximum]


def scatter_svg(buildings, clusters):
    resolved = [item for item in buildings if item["features"]["area"] is not None and item["features"]["height"] is not None]
    if not resolved: return "<svg viewBox='0 0 900 500'><text x='40' y='70' fill='#f07167'>size/height bootstrap unresolved</text></svg>"
    areas = [math.log1p(item["features"]["area"]) for item in resolved]
    heights = [item["features"]["height"] for item in resolved]
    amin, amax, hmin, hmax = min(areas), max(areas), min(heights), max(heights)
    colors = ["#efa92f", "#55c5d8", "#66dd91", "#d596e8", "#f07167", "#91a0a6"]
    cluster_by_id = {building_id: index for index, cluster in enumerate(clusters)
                     for building_id in cluster["members"]}
    dots = []
    label_boxes = []
    for item in sorted(resolved, key=lambda row: (row["features"]["height"], row["features"]["area"], row["id"])):
        x = 70 + 760 * (math.log1p(item["features"]["area"]) - amin) / max(amax - amin, 1e-9)
        y = 430 - 350 * (item["features"]["height"] - hmin) / max(hmax - hmin, 1e-9)
        color = colors[cluster_by_id.get(item["id"], 0) % len(colors)]
        radius = 5 + min(item["features"]["floors"], 4) * 2
        chosen = None
        for dx, dy in ((10, -9), (10, 19), (-51, -9), (-51, 19), (10, -25), (-51, -25)):
            tx, ty = x + dx, y + dy
            box = (tx - 2, ty - 12, tx + 47, ty + 3)
            if 73 <= box[0] and box[2] <= 850 and 45 <= box[1] and box[3] <= 452 and not any(
                    box[0] < old[2] and box[2] > old[0] and box[1] < old[3] and box[3] > old[1]
                    for old in label_boxes):
                chosen = tx, ty, box
                break
        tx, ty, box = chosen or (x + 10, y - 9, (x + 8, y - 21, x + 57, y - 6))
        label_boxes.append(box)
        dots.append(f"<a href='buildings/{item['id']}/css/route.html'><circle cx='{x:.1f}' cy='{y:.1f}' r='{radius}' fill='{color}'/><path d='M{x:.1f} {y:.1f}L{tx:.1f} {ty-5:.1f}' stroke='{color}' stroke-width='.7'/><text x='{tx:.1f}' y='{ty:.1f}' fill='#edf2ef' font-size='10'>{item['id']}</text></a>")
    return "<svg viewBox='0 0 900 500' role='img'><path d='M70 55V430H850' fill='none' stroke='#52656d'/><text x='360' y='485' fill='#9eb6c2'>log total footprint area →</text><text x='18' y='270' transform='rotate(-90 18 270)' fill='#9eb6c2'>mean elevation height →</text>" + "".join(dots) + "</svg>"


def dashboard_html(index):
    mode = index["mode"]
    cards = []
    for item in index["buildings"]:
        route = item.get("approved", "BLOCKED")
        comparison = item.get("comparison", {})
        base = comparison.get("baseline_route")
        transfer = (f"control {base} → cumulative {comparison.get('cumulative_route')}"
                    if base else "dependency held")
        cards.append(f"<a class='card' href='buildings/{item['id']}/css/route.html'><b>{item['id']}</b><span>{item['building_type']}</span><strong>{route}</strong><small>{item.get('pieces',0)} pieces · L{item['features'].get('floors') or '?'}</small><small>{transfer}</small></a>")
    banner = "SIMULATION — NOT ARCHITECTURAL EVIDENCE" if mode == "FIXTURE_SIMULATION" else index["outcome"]["answer"]
    learning = index.get("learning", {"status": "NOT_RUN", "advanced_buildings": 0,
                                       "regressions": 0, "admitted_examples": 0})
    rendering = index.get("rendering", {"status": "NOT_RUN"})
    return f"""<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Architectural Curriculum</title>
<style>:root{{--bg:#0b1317;--panel:#142127;--line:#30434b;--ink:#edf2ef;--muted:#9eb6c2;--gold:#efa92f}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px Arial;padding:24px}}h1{{font-size:34px;margin:6px 0}}.k{{color:var(--gold);font:700 12px monospace;letter-spacing:.14em}}.banner{{border:1px solid var(--gold);padding:12px;color:var(--gold);margin:20px 0}}.panel{{background:var(--panel);border:1px solid var(--line);padding:14px}}.metrics{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px}}.metric{{background:var(--panel);border:1px solid var(--line);padding:12px}}.metric b{{display:block;font-size:20px;margin-top:5px}}svg{{width:100%;height:auto}}.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin-top:16px}}.card{{display:grid;gap:7px;background:var(--panel);border:1px solid var(--line);padding:14px;color:var(--ink);text-decoration:none}}.card span,.card small,.metric span{{color:var(--muted)}}.card strong{{color:#66dd91}}@media(max-width:900px){{.metrics{{grid-template-columns:1fr 1fr}}}}</style>
<div class='k'>BUILDINGS FROM BYTES / AUTOMATIC CURRICULUM</div><h1>Size first. Height next. Learn forward.</h1><div class='banner'>{banner}</div><div class='metrics'><div class='metric'><span>Learning claim</span><b>{learning['status']}</b></div><div class='metric'><span>Admitted controls</span><b>{learning['admitted_examples']}</b></div><div class='metric'><span>Advanced</span><b>{learning['advanced_buildings']}</b></div><div class='metric'><span>Regressions</span><b>{learning['regressions']}</b></div><div class='metric'><span>Hardware GPU</span><b>{rendering['status']}</b></div></div><section class='panel'>{scatter_svg(index['buildings'], index['clusters'])}</section><div class='cards'>{''.join(cards)}</div>""".encode("utf-8")


def compute_outcome(index, charter):
    unseen = [item for item in index["buildings"] if item["id"] != charter["selection"]["seed_control"]]
    counts = {level: sum(item.get(level, False) for item in unseen) for level in LEVELS}
    g1_types = len({item["building_type"] for item in unseen if item.get("G1_METRIC_GRAPH")})
    f2_types = len({item["building_type"] for item in unseen if item.get("F2_WEATHER_SHELL")})
    learning_rule = charter["outcome_ladder"]["learning"]
    learning = index.get("learning", {})
    learning_pass = ((learning.get("advanced_buildings", 0) >=
                      learning_rule["minimum_advanced_buildings"] or
                      learning.get("unresolved_reduction_ratio", 0) >=
                      learning_rule["or_minimum_unresolved_reduction_ratio"]) and
                     learning.get("regressions", 0) <=
                     learning_rule["prior_gate_regressions_allowed"])
    rendering_pass = index.get("rendering", {}).get("status") == "PASS"
    tier = None
    if index["mode"] != "REAL":
        answer = "SIMULATION_NOT_EVIDENCE"
    else:
        for name in ("wild", "strong", "minimum"):
            target = charter["outcome_ladder"][name]
            if (counts["G1_METRIC_GRAPH"] >= target["g1_unseen"] and
                counts["F1_MASSING"] >= target["f1_unseen"] and
                counts["F2_WEATHER_SHELL"] >= target["f2_unseen"] and
                g1_types >= target.get("g1_building_types", 0) and
                f2_types >= target.get("f2_building_types", 0)):
                tier = name.upper()
                break
        answer = (f"{tier}_SUCCESS" if tier and learning_pass and rendering_pass else
                  "EDGE_MAPPED_NO_PROMOTION")
    return {"answer": answer, "unseen_counts": counts, "g1_building_types": g1_types,
            "f2_building_types": f2_types, "manual_edits": 0,
            "source_downloads": 0, "live_world_mutated": False,
            "architectural_tier": tier, "learning_gate": learning_pass,
            "rendering_gate": rendering_pass}


def run_curriculum(args):
    preflight, charter, selection, records = run_preflight(args)
    project = CurriculumProject(args, preflight, charter, records)
    atomic_json(project.root / "preflight.json", preflight)
    immutable_json(project.rev / "preflight.json", preflight)
    if preflight["status"] == "BLOCKED":
        blocked_buildings = [{"id": record["id"], "building_type": record["building_type"],
                              "features": {"area": None, "height": None, "floors": None},
                              "approved": "BLOCKED_DEPENDENCY", **{level: False for level in LEVELS}}
                             for record in records]
        index = {"schema": "architectural-curriculum-index/v1", "revision": project.revision,
                 "mode": "REAL", "seed_control": "sd0401", "clusters": [],
                 "buildings": blocked_buildings,
                 "outcome": {"answer": "BLOCKED", "blockers": preflight["blockers"]}}
        immutable_json(project.rev / "index.json", index)
        immutable_bytes(project.rev / "index.html", dashboard_html(index))
        atomic_json(project.root / "report.json", {"schema": "architectural-curriculum-report/v1",
                    "revision": project.revision, "answer": "BLOCKED",
                    "blockers": preflight["blockers"], "request_sent": False,
                    "world_mutated": False})
        return 2, project, index

    # Freeze a lesson-free control arm for every building before clustering.  This
    # prevents curriculum order or earlier lessons from leaking into the size/height
    # features used to decide that very order.
    baselines = {}
    feature_map = {}
    for record in records:
        building_id = record["id"]
        target = project.rev / "buildings" / building_id
        holder = {}

        def build_baseline(record=record, target=target):
            baseline = perceive_baseline(project, record, target, fixture=args.fixture_vision)
            holder["baseline"] = baseline
            immutable_json(target / "baseline.json", baseline)
            outputs = [target / "baseline.json"]
            outputs.extend(target / item["local_normalized"] for item in baseline["sheets"])
            return outputs, {"features": baseline["features"],
                             "approved": baseline["route"]["approved"],
                             "unresolved": baseline["unresolved_assertions"]}

        project.stage(f"bootstrap-{building_id}",
                      {"manifest": preflight["source"]["manifest_hashes"][building_id],
                       "mode": project.mode, "lesson_free": True}, build_baseline)
        baseline = (holder.get("baseline") or
                    json.loads((target / "baseline.json").read_text(encoding="utf-8")))
        baselines[building_id] = baseline
        features = baseline["features"]
        feature_map[building_id] = {
            "area": features["total_footprint_area_m2"],
            "height": features["mean_elevation_height_m"],
            "floors": features["floor_count"],
            "status": features["confidence"],
        }
    clusters, order = build_curriculum(records, feature_map, charter)
    bootstrap = {"schema": "architectural-curriculum-bootstrap/v1",
                 "mode": project.mode, "features": feature_map, "clusters": clusters, "order": order,
                 "lesson_free": True}
    immutable_json(project.rev / "bootstrap.json", bootstrap)
    record_by_id = {record["id"]: record for record in records}
    accepted_lessons = []
    index_rows = []
    seed = charter["selection"]["seed_control"]
    process_order = [seed] + [item for item in order if item != seed]
    if args.max_buildings: process_order = process_order[:args.max_buildings]
    benchmark_building = max(
        process_order,
        key=lambda item: ((baselines[item].get("composition") or {}).get("piece_count", -1), item),
        default=None)
    cluster_by_building = {building_id: cluster for cluster in clusters for building_id in cluster["members"]}
    completed_by_cluster = defaultdict(list)
    advanced_buildings = 0
    regression_count = 0
    lesson_layer = 0
    previous_lesson_hash = None
    for ordinal, building_id in enumerate(process_order, 1):
        record = record_by_id[building_id]
        target = project.rev / "buildings" / building_id
        cluster = cluster_by_building.get(building_id, {"id": "SEED"})
        prior = retrieved_lessons(accepted_lessons, {"total_footprint_area_m2": feature_map[building_id]["area"],
                                                     "mean_elevation_height_m": feature_map[building_id]["height"],
                                                     "floor_count": feature_map[building_id]["floors"]},
                                  charter["curriculum"]["maximum_retrieved_lessons"])
        stage_name = f"building-{building_id}"
        input_value = {"manifest": preflight["source"]["manifest_hashes"][building_id],
                       "baseline": digest_file(target / "baseline.json"),
                       "cluster": cluster["id"],
                       "lessons": [item["assessment_sha256"] for item in prior],
                       "mode": project.mode}
        holder = {}
        def build():
            assessment, graph, pieces = analyze_record(project, record, target, prior,
                                                       baselines[building_id],
                                                       fixture=args.fixture_vision)
            holder.update({"assessment": assessment, "graph": graph, "pieces": pieces})
            outputs = []
            immutable_json(target / "assessment.json", assessment); outputs.append(target / "assessment.json")
            immutable_json(target / "building.graph.json", graph or {"schema": "architectural-building-graph/v1", "building_id": building_id, "status": "HELD"}); outputs.append(target / "building.graph.json")
            immutable_json(target / "pieces.json", {"schema": "architectural-piece-plan/v1", "pieces": pieces}); outputs.append(target / "pieces.json")
            outputs += write_building_views(target, assessment, graph, pieces)
            outputs += write_simple_webgpu(
                target, assessment, graph, pieces,
                browser=project.browser if building_id == benchmark_building else None)
            outputs += building_capsule(project, target, assessment, graph, pieces)
            return outputs, {"approved": assessment["route"]["approved"],
                             "pieces": len(pieces), "unresolved": assessment["unresolved_assertions"],
                             "comparison": assessment["comparison"]}
        facts = project.stage(stage_name, input_value, build)
        if not holder:
            assessment = json.loads((target / "assessment.json").read_text(encoding="utf-8"))
            pieces = json.loads((target / "pieces.json").read_text(encoding="utf-8"))["pieces"]
        else:
            assessment, pieces = holder["assessment"], holder["pieces"]
        row = {"id": building_id, "title": assessment["title"],
               "building_type": record["building_type"], "cluster": cluster["id"],
               "ordinal": ordinal, "features": {"area": feature_map[building_id]["area"],
                                                   "height": feature_map[building_id]["height"],
                                                   "floors": feature_map[building_id]["floors"]},
               "approved": assessment["route"]["approved"], "pieces": len(pieces),
               "unresolved_assertions": assessment["unresolved_assertions"],
               "comparison": assessment["comparison"],
               **{level: bool(assessment["route"].get(level)) for level in LEVELS}}
        index_rows.append(row); completed_by_cluster[cluster["id"]].append(row)
        comparison = assessment["comparison"]
        advanced_buildings += int(comparison["advanced"])
        regression_count += len(comparison["regressions"])
        if assessment["route"]["G1_METRIC_GRAPH"] and not comparison["regressions"]:
            accepted_lessons.append({"building_id": building_id,
                                     "features": assessment["features"],
                                     "route": assessment["route"]["approved"],
                                     "comparison": comparison,
                                     "assessment_sha256": digest_file(target / "assessment.json")})
        print(f"[{ordinal:02d}/{len(process_order):02d}] {building_id} {cluster['id']} -> {row['approved']} ({len(pieces)} pieces)")
        # Freeze a cumulative lesson checkpoint whenever its cluster has no remaining member.
        remaining_in_cluster = [item for item in process_order[ordinal:]
                                if cluster_by_building.get(item, {}).get("id") == cluster["id"]]
        if not remaining_in_cluster:
            prior_path = project.rev / "lessons" / f"layer-{lesson_layer:02d}.json"
            cluster_regressions = [
                {"building_id": item["id"], "gates": item["comparison"]["regressions"]}
                for item in completed_by_cluster[cluster["id"]]
                if item["comparison"]["regressions"]
            ]
            lesson = {"schema": "architectural-lesson-pack/v1", "layer": lesson_layer,
                      "cluster": cluster["id"],
                      "prior_sha256": previous_lesson_hash,
                      "status": "REJECTED" if cluster_regressions else
                                "ACCEPTED" if accepted_lessons else "EMPTY",
                      "admitted_examples": accepted_lessons,
                      "regressions": cluster_regressions, "continuous": True,
                      "mode": project.mode}
            immutable_json(prior_path, lesson)
            previous_lesson_hash = digest_file(prior_path)
            lesson_layer += 1
    partial = len(process_order) != len(records)
    base_unresolved = sum(item["comparison"]["baseline_unresolved_assertions"] for item in index_rows)
    cumulative_unresolved = sum(item["comparison"]["cumulative_unresolved_assertions"] for item in index_rows)
    unresolved_reduction = ((base_unresolved - cumulative_unresolved) / base_unresolved
                            if base_unresolved else 0.0)
    learning_rule = charter["outcome_ladder"]["learning"]
    learning_demonstrated = (
        project.mode == "REAL" and not regression_count and
        (advanced_buildings >= learning_rule["minimum_advanced_buildings"] or
         unresolved_reduction >= learning_rule["or_minimum_unresolved_reduction_ratio"]))
    rendering = {"status": "NOT_RUN", "building_id": benchmark_building,
                 "reason": "browser disabled or unavailable"}
    if benchmark_building and project.browser:
        receipt_path = project.rev / "buildings" / benchmark_building / "webgpu" / "browser-receipt.json"
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            limits = charter["rendering"]
            checks = {
                "hardware": receipt.get("hardware_gate") == "hardware",
                "status": receipt.get("status") == "ok",
                "startup": receipt.get("startup_ms", math.inf) <= limits["largest_promoted_candidate_startup_ms"],
                "frame_p95": receipt.get("frame_p95_ms", math.inf) <= limits["largest_promoted_candidate_frame_p95_ms"],
                "validation": not receipt.get("validation_errors", ["not-run"]),
                "capture": receipt.get("capture_status") == "PASS",
            }
            rendering = {"status": "PASS" if all(checks.values()) else "FAIL",
                         "building_id": benchmark_building, "checks": checks,
                         "receipt": receipt}
    index = {"schema": "architectural-curriculum-index/v1", "revision": project.revision,
             "mode": project.mode, "seed_control": seed, "clusters": clusters,
             "curriculum_order": order, "buildings": sorted(index_rows, key=lambda item: item["ordinal"]),
             "partial": partial, "learning": {"admitted_examples": len(accepted_lessons),
                                                "regressions": regression_count,
                                                "advanced_buildings": advanced_buildings,
                                                "baseline_unresolved_assertions": base_unresolved,
                                                "cumulative_unresolved_assertions": cumulative_unresolved,
                                                "unresolved_reduction_ratio": round(unresolved_reduction, 6),
                                                "status": "DEMONSTRATED" if learning_demonstrated else
                                                          "NOT_DEMONSTRATED"},
             "rendering": rendering, "outcome": {}}
    index["outcome"] = compute_outcome(index, charter) if not partial else {"answer": "PARTIAL_DIAGNOSTIC"}
    immutable_json(project.rev / "index.json", index)
    immutable_bytes(project.rev / "index.html", dashboard_html(index))
    catalog_members = {"index.json": canonical_bytes(index), "index.html": dashboard_html(index),
                       "bootstrap.json": canonical_bytes(bootstrap),
                       "identity.json": (project.rev / "identity.json").read_bytes(),
                       "preflight.json": (project.rev / "preflight.json").read_bytes()}
    for lesson_path in sorted((project.rev / "lessons").glob("layer-*.json")):
        catalog_members[f"lessons/{lesson_path.name}"] = lesson_path.read_bytes()
    for row in index_rows:
        source = project.rev / "buildings" / row["id"]
        for name in ("baseline.json", "assessment.json", "building.graph.json", "pieces.json",
                     "capsule.json", "building.capsule.zip"):
            data = (source / name).read_bytes()
            catalog_members[f"buildings/{row['id']}/{name}"] = data
    catalog = project.exports / f"architectural-curriculum-{project.revision}.capsule.zip"
    deterministic_zip(catalog, catalog_members)
    report = {"schema": "architectural-curriculum-report/v1", "revision": project.revision,
              "mode": project.mode, "answer": index["outcome"]["answer"],
              "outcome": index["outcome"], "clusters": len(clusters),
              "processed": len(index_rows), "catalog": {"sha256": digest_file(catalog),
                                                           "bytes": catalog.stat().st_size},
              "learning": index["learning"], "rendering": index["rendering"],
              "stage_cache": project.stats, "request_sent": False, "world_mutated": False,
              "next_earned_edge": (
                  "make the pinned local vision endpoint available"
                  if project.mode == "REAL" and preflight["vision"]["status"] != "READY" else
                  "restore a hardware WebGPU adapter for the largest-candidate gate"
                  if index["rendering"]["status"] != "PASS" else
                  "run blind visual adjudication before any fidelity claim")}
    atomic_json(project.root / "report.json", report)
    return 0, project, index


def verify_revision(args):
    root = args.out.resolve()
    if not (root / "HEAD").is_file(): raise RuntimeError("curriculum HEAD is missing")
    revision = (root / "HEAD").read_text(encoding="utf-8").strip()
    rev = root / "revisions" / revision
    index = json.loads((rev / "index.json").read_text(encoding="utf-8"))
    errors = []
    if index.get("schema") != "architectural-curriculum-index/v1": errors.append("index schema")
    expected_count = 20 if not index.get("partial") else len(index.get("buildings", []))
    if len(index.get("buildings", [])) != expected_count: errors.append("building count")
    for receipt_path in (rev / "receipts").glob("*.json") if (rev / "receipts").is_dir() else []:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        for item in receipt.get("outputs", []):
            path = safe_child(rev, item["path"])
            if not path.is_file() or digest_file(path) != item["sha256"]:
                errors.append(f"receipt mismatch: {item['path']}")
    for row in index.get("buildings", []):
        target = rev / "buildings" / row["id"]
        if row.get("approved") == "BLOCKED_DEPENDENCY":
            continue
        baseline = json.loads((target / "baseline.json").read_text(encoding="utf-8"))
        assessment = json.loads((target / "assessment.json").read_text(encoding="utf-8"))
        if baseline.get("schema") != "architectural-baseline/v1" or not baseline.get("lesson_free"):
            errors.append(f"baseline schema/control {row['id']}")
        if assessment.get("schema") != "architectural-assessment/v1": errors.append(f"assessment schema {row['id']}")
        comparison = assessment.get("comparison", {})
        if comparison.get("regressions") and comparison.get("selected") != "baseline":
            errors.append(f"regression fallback {row['id']}")
        bundle = target / "building.capsule.zip"
        if bundle.is_file():
            with zipfile.ZipFile(bundle) as archive:
                names = archive.namelist()
                if "capsule.json" not in names: errors.append(f"capsule manifest {row['id']}")
                capsule = json.loads(archive.read("capsule.json"))
                for name, record in capsule["files"].items():
                    payload = archive.read(name)
                    if digest_bytes(payload) != record["sha256"] or len(payload) != record["bytes"]:
                        errors.append(f"capsule member {row['id']}:{name}")
                normalized = [name for name in names if name.startswith("normalized/") and name.endswith(".png")]
                if len(normalized) != len(assessment.get("sheets", [])):
                    errors.append(f"capsule normalized evidence {row['id']}")
                if row.get("pieces", 0) and "webgpu/browser-receipt.json" not in names:
                    errors.append(f"capsule rendering receipt {row['id']}")
                if any(name.lower().endswith((".tif", ".tiff")) for name in names):
                    errors.append(f"source TIFF duplicated in {row['id']}")
    previous_lesson_hash = None
    for lesson_path in sorted((rev / "lessons").glob("layer-*.json")) if (rev / "lessons").is_dir() else []:
        lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
        if lesson.get("prior_sha256") != previous_lesson_hash:
            errors.append(f"lesson chain {lesson_path.name}")
        previous_lesson_hash = digest_file(lesson_path)
    exports = sorted((root / "exports").glob(f"architectural-curriculum-{revision}.capsule.zip"))
    if index.get("outcome", {}).get("answer") != "BLOCKED":
        if len(exports) != 1:
            errors.append("catalog capsule missing")
        else:
            with zipfile.ZipFile(exports[0]) as archive:
                names = archive.namelist()
                if any(name.lower().endswith((".tif", ".tiff")) for name in names):
                    errors.append("source TIFF duplicated in catalog")
                if not {"index.json", "bootstrap.json", "identity.json", "preflight.json"}.issubset(names):
                    errors.append("catalog contract members")
                for row in index.get("buildings", []):
                    if f"buildings/{row['id']}/building.capsule.zip" not in names:
                        errors.append(f"catalog building capsule {row['id']}")
    result = {"schema": "architectural-curriculum-verification/v1",
              "status": "PASS" if not errors else "FAIL", "revision": revision,
              "mode": index.get("mode"), "buildings": len(index.get("buildings", [])),
              "errors": errors, "request_sent": False, "world_mutated": False}
    atomic_json(root / "verification.json", result)
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


def preflight_command(args):
    receipt, charter, selection, records = run_preflight(args)
    args.out.mkdir(parents=True, exist_ok=True)
    atomic_json(args.out / "preflight.json", receipt)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] in ("READY", "SIMULATION_READY") else 2


def serve_command(args):
    root = args.out.resolve()
    revision = (root / "HEAD").read_text(encoding="utf-8").strip()
    directory = root / "revisions" / revision
    if not (directory / "index.html").is_file(): raise RuntimeError("curriculum dashboard missing")
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *handler_args, **handler_kwargs):
            super().__init__(*handler_args, directory=str(directory), **handler_kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"http://127.0.0.1:{args.port}/index.html")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0


def main():
    args = parse_args()
    try:
        if args.command == "preflight": return preflight_command(args)
        if args.command == "verify": return verify_revision(args)
        if args.command == "serve": return serve_command(args)
        code, project, index = run_curriculum(args)
        print(f"revision {project.revision}")
        print(f"RESULT {index['outcome']['answer']} · {len(index['buildings'])} buildings · mode {index['mode']}")
        return code
    except Exception as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

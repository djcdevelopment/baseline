#!/usr/bin/env python3
"""R&D lap: can one browser XYZ/yaw become one live Valheim blueprint placement?

This is intentionally a one-asset probe, not a catalog or an authoring framework. It
renders one reviewed Godbuild through the existing WebGPU cube instancer, stages that
exact capture/blueprint pair into Quest Lab's fixed directory, and writes only the
existing bounded batch mailbox. One correlated receipt ends the lap.
"""

import argparse
import ast
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "out" / "live-spatial-revision"
MAX_BODY_BYTES = 8192
MAX_WORLD_COORDINATE = 10500.0
INSTANCE_FLOATS = 20
INSTANCE_BYTES = INSTANCE_FLOATS * 4

FAMILY_COLORS = {
    "roof": (192, 57, 43), "beam": (109, 76, 65), "pole": (141, 110, 99),
    "light": (241, 196, 15), "sign": (255, 241, 118), "misc": (207, 216, 220),
}

PROXIES = {
    "fire_pit": ((1.55, 0.35, 1.55), "light"),
    "sign": ((1.2, 0.65, 0.12), "sign"),
    "wood_beam": ((2.0, 0.18, 0.18), "beam"),
    "wood_pole": ((0.18, 1.0, 0.18), "pole"),
    "wood_pole2": ((0.18, 2.0, 0.18), "pole"),
    "wood_roof": ((2.0, 0.16, 2.0), "roof"),
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--blueprint", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--lab-root", type=Path)
    parser.add_argument("--expected-machine")
    parser.add_argument("--expected-world-uid")
    parser.add_argument("--creator-session-id")
    parser.add_argument("--x", type=float)
    parser.add_argument("--y", type=float)
    parser.add_argument("--z", type=float)
    parser.add_argument("--yaw", type=float, default=37.0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--receipt-timeout-s", type=float, default=45.0)
    parser.add_argument("--no-browser", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--derive-only", action="store_true")
    mode.add_argument("--apply-once", action="store_true")
    parser.add_argument("--accepted-head", type=Path)
    parser.add_argument("--derived-name")
    parser.add_argument("--derive-yaw", type=float, default=90.0)
    parser.add_argument("--importer", type=Path)
    return parser.parse_args()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value, limit):
    return math.isfinite(value) and abs(value) <= limit


def validate_inputs(args, plan, manifest):
    for path in (args.plan, args.manifest, args.blueprint, args.capture):
        if not path.is_file():
            raise RuntimeError(f"required artifact is missing: {path}")
    if plan.get("schema") != "comfy-quest-godbuild-plan/v1":
        raise RuntimeError("plan schema is not comfy-quest-godbuild-plan/v1")
    if manifest.get("schema") != "comfy-quest-godbuild/v1":
        raise RuntimeError("manifest schema is not comfy-quest-godbuild/v1")
    name = manifest.get("name")
    if not name or plan.get("name") != name:
        raise RuntimeError("plan and manifest names disagree")
    expected = manifest.get("artifacts", {})
    for path in (args.blueprint, args.capture, args.plan):
        record = expected.get(path.name)
        if not record or sha256(path) != str(record.get("sha256", "")).lower():
            raise RuntimeError(f"reviewed artifact hash mismatch: {path.name}")
    if len(plan.get("pieces", [])) != manifest.get("piece_count"):
        raise RuntimeError("plan piece count disagrees with manifest")
    return name


def validate_live_args(args):
    required = {
        "--lab-root": args.lab_root,
        "--expected-machine": args.expected_machine,
        "--expected-world-uid": args.expected_world_uid,
        "--creator-session-id": args.creator_session_id,
        "--x": args.x,
        "--y": args.y,
        "--z": args.z,
    }
    missing = [option for option, value in required.items() if value is None or value == ""]
    if missing:
        raise RuntimeError("live mode requires " + ", ".join(missing))
    for value in (args.x, args.y, args.z):
        if not finite(value, MAX_WORLD_COORDINATE):
            raise RuntimeError("world coordinates must be finite and within +/-10500")
    if not finite(args.yaw, 3600.0):
        raise RuntimeError("yaw must be finite and within +/-3600 degrees")
    if not args.expected_world_uid.lstrip("-").isdigit() or args.expected_world_uid == "0":
        raise RuntimeError("expected world UID must be a non-zero integer")


def quaternion_matrix(rotation):
    x, y, z, w = (float(value) for value in rotation)
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm == 0:
        return np.eye(3, dtype=float)
    x, y, z, w = x / norm, y / norm, z / norm, w / norm
    return np.asarray([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=float)


def scene_pieces(plan):
    pieces = []
    for item in plan["pieces"]:
        prefab = item["prefab"]
        dimensions, family = PROXIES.get(prefab, ((0.5, 0.5, 0.5), "misc"))
        extent = np.asarray(dimensions, dtype=float)
        pieces.append({
            "zdo": f"plan:{int(item['index']):04d}",
            "name": prefab,
            "family": family,
            "center": np.asarray(item["position"], dtype=float),
            "R": quaternion_matrix(item["rotation"]),
            "extents": extent,
            "half": extent / 2.0,
            "source": "reviewed Godbuild proxy",
        })
    return pieces


def webgpu_page():
    """Read the already-proven page constant without importing its analysis dependencies."""
    source = (HERE / "probe_webgpu_render.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "HTML" for target in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("probe_webgpu_render.py no longer declares the HTML probe page")


def encode_scene(pieces, label, kind, out_dir, benchmark_frames, warmup_frames):
    corners = []
    signs = np.asarray([
        [-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1],
        [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1],
    ], dtype=float)
    for piece in pieces:
        corners.append(piece["center"] + (piece["R"] @ (signs * piece["half"]).T).T)
    all_corners = np.concatenate(corners)
    low, high = all_corners.min(axis=0), all_corners.max(axis=0)
    origin, dimensions = (low + high) / 2.0, high - low
    mirror_x = np.diag([-1.0, 1.0, 1.0])
    ordered = sorted(pieces, key=lambda piece: (piece["family"], piece["zdo"]))
    instances = np.empty((len(ordered), INSTANCE_FLOATS), dtype="<f4")
    families, start = [], 0
    for family in sorted({piece["family"] for piece in ordered}):
        count = sum(piece["family"] == family for piece in ordered)
        rgb = FAMILY_COLORS.get(family, FAMILY_COLORS["misc"])
        families.append({"name": family, "color": "#%02x%02x%02x" % rgb,
                         "start": start, "count": count})
        start += count
    colors = {family["name"]: [int(family["color"][offset:offset + 2], 16) / 255.0
                                for offset in (1, 3, 5)] + [1.0]
              for family in families}
    farthest = 0.0
    for index, piece in enumerate(ordered):
        center = mirror_x @ (piece["center"] - origin)
        rotation = mirror_x @ piece["R"] @ mirror_x
        model = np.eye(4, dtype=np.float32)
        model[:3, :3] = rotation @ np.diag(piece["extents"])
        model[:3, 3] = center
        instances[index, :16] = model.reshape(-1, order="F")
        instances[index, 16:] = colors[piece["family"]]
        farthest = max(farthest, float(np.linalg.norm(center) + np.linalg.norm(piece["half"])))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "scene.bin").write_bytes(instances.tobytes(order="C"))
    (out_dir / "index.html").write_text(webgpu_page(), encoding="utf-8")
    manifest = {
        "schema": "webgpu-zdo-scene/v1", "label": label, "kind": kind,
        "pieces": len(ordered), "triangles": len(ordered) * 12,
        "instance_stride": INSTANCE_BYTES, "instance_bytes": instances.nbytes,
        "dimensions_m": [round(float(value), 2) for value in dimensions],
        "radius_m": round(farthest, 3), "families": families,
        "benchmark_frames": benchmark_frames, "warmup_frames": warmup_frames,
    }
    (out_dir / "scene.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest, {}


def write_atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{uuid.uuid4().hex}")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def artifact_record(path):
    payload = path.read_bytes()
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def run_importer(importer, values):
    return subprocess.run(
        [sys.executable, str(importer), *[str(value) for value in values]],
        cwd=importer.parent,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )


def quaternion_product(left, right):
    ax, ay, az, aw = left
    bx, by, bz, bw = right
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def normalized_quaternion(values):
    norm = math.sqrt(sum(float(value) ** 2 for value in values))
    if norm < 1e-12:
        return (0.0, 0.0, 0.0, 1.0)
    return tuple(float(value) / norm for value in values)


def piece_identity(piece):
    return (
        piece["Prefab"], piece["Category"] or "Building",
        bool(piece["HasSignText"]), piece["SignText"] or "",
        bool(piece["HasItemStand"]), piece["ItemPrefab"] or "",
        int(piece["ItemVariant"]), int(piece["ItemQuality"]), int(piece["ItemType"]),
        piece["RuneSchool"] or "", piece["RuneStyle"] or "",
        piece["TextGlowSchool"] or "",
    )


def inverse_transform_proof(source, derived, yaw_degrees):
    position_tolerance = 0.0002
    quaternion_tolerance = 0.000002
    angle = math.radians(yaw_degrees)
    sine, cosine = math.sin(angle), math.cos(angle)
    half_sine, half_cosine = math.sin(angle / 2), math.cos(angle / 2)
    rotated = [
        (
            cosine * float(piece["X"]) + sine * float(piece["Z"]),
            float(piece["Y"]),
            -sine * float(piece["X"]) + cosine * float(piece["Z"]),
        )
        for piece in source["Pieces"]
    ]
    minima = tuple(min(position[axis] for position in rotated) for axis in range(3))
    inverse_yaw = (0.0, -half_sine, 0.0, half_cosine)
    reconstructed = []
    for piece in derived["Pieces"]:
        rx = float(piece["X"]) + minima[0]
        ry = float(piece["Y"]) + minima[1]
        rz = float(piece["Z"]) + minima[2]
        q = normalized_quaternion(
            quaternion_product(
                inverse_yaw,
                tuple(float(piece[key]) for key in ("Qx", "Qy", "Qz", "Qw")),
            )
        )
        reconstructed.append((
            piece,
            (cosine * rx - sine * rz, ry, sine * rx + cosine * rz),
            q,
        ))

    unused = set(range(len(source["Pieces"])))
    max_position_error = 0.0
    max_quaternion_error = 0.0
    for derived_piece, position, rotation in reconstructed:
        matches = []
        for index in unused:
            original = source["Pieces"][index]
            if piece_identity(original) != piece_identity(derived_piece):
                continue
            original_position = tuple(float(original[key]) for key in ("X", "Y", "Z"))
            position_error = max(abs(left - right)
                                 for left, right in zip(position, original_position))
            original_rotation = normalized_quaternion(
                tuple(float(original[key]) for key in ("Qx", "Qy", "Qz", "Qw"))
            )
            direct = max(abs(left - right)
                         for left, right in zip(rotation, original_rotation))
            negated = max(abs(left + right)
                          for left, right in zip(rotation, original_rotation))
            quaternion_error = min(direct, negated)
            if (position_error <= position_tolerance
                    and quaternion_error <= quaternion_tolerance):
                matches.append((position_error, quaternion_error, index))
        if not matches:
            raise RuntimeError(
                "inverse-transform proof could not match derived piece "
                f"{derived_piece['Prefab']} at {position!r}"
            )
        position_error, quaternion_error, index = min(matches)
        unused.remove(index)
        max_position_error = max(max_position_error, position_error)
        max_quaternion_error = max(max_quaternion_error, quaternion_error)
    if unused:
        raise RuntimeError(f"inverse-transform proof left {len(unused)} source pieces unmatched")
    return {
        "status": "PASS",
        "matched_pieces": len(reconstructed),
        "rotated_minimum_before_normalization": [round(value, 9) for value in minima],
        "position_component_tolerance_m": position_tolerance,
        "quaternion_component_tolerance": quaternion_tolerance,
        "maximum_position_component_error_m": max_position_error,
        "maximum_quaternion_component_error": max_quaternion_error,
    }


def publish_exact_folder(source, target):
    expected = {path.name: path for path in source.iterdir() if path.is_file()}
    if not expected:
        raise RuntimeError("authoritative importer produced no files")
    if target.exists():
        extras = sorted(path.name for path in target.iterdir()
                        if path.is_file() and path.name not in expected)
        if extras:
            raise RuntimeError("refusing non-exact canonical output folder: " + ", ".join(extras))
    target.mkdir(parents=True, exist_ok=True)
    for name, source_path in expected.items():
        destination = target / name
        payload = source_path.read_bytes()
        if destination.exists() and destination.read_bytes() != payload:
            raise RuntimeError(f"refusing to replace changed canonical artifact: {destination}")
        if not destination.exists():
            write_atomic(destination, payload)
    return [target / name for name in sorted(expected)]


def derive_live_pair(args, source_name):
    required = {
        "--accepted-head": args.accepted_head,
        "--derived-name": args.derived_name,
        "--importer": args.importer,
    }
    missing = [option for option, value in required.items() if value is None or value == ""]
    if missing:
        raise RuntimeError("--derive-only requires " + ", ".join(missing))
    if not finite(args.derive_yaw, 3600.0):
        raise RuntimeError("derive yaw must be finite and within +/-3600 degrees")
    if not re.fullmatch(r"[a-z0-9_-]{1,64}", args.derived_name):
        raise RuntimeError("derived name must use 1-64 lowercase letters, digits, '-' or '_'")
    if args.derived_name == source_name:
        raise RuntimeError("derived name must differ from the immutable accepted source")

    accepted_head = args.accepted_head.resolve()
    importer = args.importer.resolve()
    if not accepted_head.is_file():
        raise RuntimeError(f"accepted HEAD is missing: {accepted_head}")
    if not importer.is_file():
        raise RuntimeError(f"authoritative importer is missing: {importer}")
    head_payload = accepted_head.read_bytes()
    revision = head_payload.decode("utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{12,64}", revision):
        raise RuntimeError("accepted HEAD is not a hexadecimal immutable revision")
    sources = [args.plan.resolve(), args.manifest.resolve(), args.blueprint.resolve(),
               args.capture.resolve()]
    creator = args.plan.resolve().parent
    if any(path.parent != creator for path in sources):
        raise RuntimeError("accepted source artifacts must share one creator directory")
    expected_creator = (accepted_head.parent / "revisions" / revision / "creator").resolve()
    if creator != expected_creator:
        raise RuntimeError("accepted HEAD does not name the supplied creator revision")
    source_payloads = {path: path.read_bytes() for path in sources}

    with tempfile.TemporaryDirectory(prefix="live-boundary-") as temporary:
        scratch = Path(temporary)
        rejected = run_importer(importer, [
            args.capture.resolve(), "--output-root", scratch / "rejected",
        ])
        expected_rejection = "Selection must be 'mine' or 'lab'"
        if rejected.returncode == 0 or expected_rejection not in rejected.stderr:
            raise RuntimeError(
                "normal importer did not reject the architectural source at Selection"
            )

        generated_root = scratch / "generated"
        generated = run_importer(importer, [
            args.capture.resolve(), "--output-root", generated_root,
            "--derive-architectural-name", args.derived_name,
            "--derive-yaw-degrees", format(args.derive_yaw, ".9g"),
        ])
        if generated.returncode:
            raise RuntimeError("authoritative derivative failed: " + generated.stderr.strip())
        generated_folder = generated_root / args.derived_name
        generated_capture = generated_folder / f"{args.derived_name}.capture.json"
        generated_blueprint = generated_folder / f"{args.derived_name}.blueprint"
        if not generated_capture.is_file() or not generated_blueprint.is_file():
            raise RuntimeError("authoritative importer omitted the derived pair")

        checked = run_importer(importer, [
            generated_capture, "--output-root", generated_root, "--check",
        ])
        if checked.returncode:
            raise RuntimeError("normal importer rejected its derivative: " + checked.stderr.strip())
        regenerated_root = scratch / "regenerated"
        regenerated = run_importer(importer, [
            generated_capture, "--output-root", regenerated_root,
        ])
        if regenerated.returncode:
            raise RuntimeError("normal importer regeneration failed: " + regenerated.stderr.strip())
        regenerated_folder = regenerated_root / args.derived_name
        generated_files = {path.name: path for path in generated_folder.iterdir() if path.is_file()}
        regenerated_files = {path.name: path for path in regenerated_folder.iterdir() if path.is_file()}
        if set(generated_files) != set(regenerated_files):
            raise RuntimeError("normal importer regeneration emitted a different file set")
        differing = [name for name in generated_files
                     if generated_files[name].read_bytes() != regenerated_files[name].read_bytes()]
        if differing:
            raise RuntimeError("normal importer regeneration was not byte-identical: "
                               + ", ".join(sorted(differing)))

        source_capture = json.loads(args.capture.read_text(encoding="utf-8"))
        derivative = json.loads(generated_capture.read_text(encoding="utf-8"))
        inverse = inverse_transform_proof(source_capture, derivative, args.derive_yaw)
        published_folder = args.out.resolve() / "canonical" / args.derived_name
        published = publish_exact_folder(generated_folder, published_folder)

    if accepted_head.read_bytes() != head_payload:
        raise RuntimeError("accepted HEAD changed during derivative generation")
    changed = [str(path) for path, payload in source_payloads.items()
               if path.read_bytes() != payload]
    if changed:
        raise RuntimeError("accepted source changed during derivative generation: " + ", ".join(changed))
    receipt = {
        "schema": "live-spatial-offline-boundary/v1",
        "status": "PASS",
        "source": {
            "name": source_name,
            "revision": revision,
            "head": {"path": str(accepted_head), **artifact_record(accepted_head)},
            "artifacts": {path.name: artifact_record(path) for path in sources},
        },
        "derivative": {
            "name": args.derived_name,
            "yaw_degrees": args.derive_yaw,
            "selection": derivative["Selection"],
            "piece_count": derivative["PieceCount"],
            "pieces_sha256": derivative["PiecesSha256"],
            "folder": str(published_folder),
            "artifacts": {path.name: artifact_record(path) for path in published},
        },
        "importer": {
            "path": str(importer),
            **artifact_record(importer),
            "default_source_rejected": True,
            "normal_validation": "PASS",
            "byte_identical_regeneration": sorted(generated_files),
        },
        "inverse_transform": inverse,
    }
    write_atomic(args.out.resolve() / "live-boundary.json",
                 (json.dumps(receipt, indent=2) + "\n").encode())
    return receipt


def stage_reviewed_pair(config):
    target = config.lab_root / "blueprints"
    staged = []
    for source in (config.blueprint, config.capture):
        destination = target / source.name
        payload = source.read_bytes()
        if destination.exists():
            if destination.read_bytes() != payload:
                raise RuntimeError(f"refusing to replace changed Lab artifact: {destination.name}")
        else:
            write_atomic(destination, payload)
        staged.append({"name": destination.name, "sha256": hashlib.sha256(payload).hexdigest()})
    return staged


class ProbeConfig:
    def __init__(self, args, name, piece_count):
        self.lab_root = args.lab_root.resolve()
        self.blueprint = args.blueprint.resolve()
        self.capture = args.capture.resolve()
        self.name = name
        self.piece_count = int(piece_count)
        self.expected_machine = args.expected_machine
        self.expected_world_uid = args.expected_world_uid
        self.creator_session_id = args.creator_session_id
        self.timeout = args.receipt_timeout_s
        self.out = args.out.resolve()

    def request(self, operation, placement):
        request_id = f"spatial-{operation}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
        now = time.time()
        request = {
            "schema": "comfy-questlab-batch-request/v1",
            "request_id": request_id,
            "operation": "blueprint_build" if operation == "apply" else "blueprint_clear",
            "blueprint_name": self.name,
            "expected_machine": self.expected_machine,
            "expected_world_uid": self.expected_world_uid,
            "creator_session_id": self.creator_session_id,
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "expires_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 300)),
        }
        if operation == "apply":
            request.update({
                "build_mode": "at",
                "world_x": format(placement["x"], ".6f"),
                "world_y": format(placement["y"], ".6f"),
                "world_z": format(placement["z"], ".6f"),
                "yaw_degrees": format(placement["yaw_degrees"], ".6f"),
            })
        return request

    def dispatch(self, operation, placement, strict_build=False):
        stage_reviewed_pair(self)
        mailbox = self.lab_root / "requests" / "questlab-batch-request.json"
        if mailbox.exists():
            raise RuntimeError("Quest Lab mailbox is busy; no request was overwritten")
        request = self.request(operation, placement)
        payload = (json.dumps(request, separators=(",", ":"), sort_keys=True) + "\n").encode()
        if len(payload) > 4096:
            raise RuntimeError("request exceeds Quest Lab's bounded mailbox")
        write_atomic(mailbox, payload)
        receipt_path = self.lab_root / "receipts" / "requests" / f"{request['request_id']}.json"
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if receipt_path.is_file():
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                self.validate_receipt(request, receipt, placement, strict_build)
                envelope = {"request": request, "receipt": receipt}
                self.out.mkdir(parents=True, exist_ok=True)
                write_atomic(self.out / "last-live-receipt.json",
                             (json.dumps(envelope, indent=2) + "\n").encode())
                return envelope
            time.sleep(0.1)
        raise RuntimeError(f"no correlated Lab receipt within {self.timeout:g}s")

    def validate_receipt(self, request, receipt, placement, strict_build=False):
        expected = {
            "schema": "comfy-questlab-batch-request-receipt/v1",
            "request_id": request["request_id"],
            "operation": request["operation"],
            "machine": self.expected_machine,
            "world_uid": self.expected_world_uid,
            "creator_session_id": self.creator_session_id,
        }
        mismatches = [
            f"{key}={receipt.get(key)!r}, expected {value!r}"
            for key, value in expected.items() if str(receipt.get(key, "")) != str(value)
        ]
        if request["operation"] == "blueprint_build" and receipt.get("state") == "completed":
            echoed = receipt.get("placement")
            if not isinstance(echoed, dict):
                mismatches.append("placement echo is missing")
            else:
                for key in ("x", "y", "z", "yaw_degrees"):
                    try:
                        matches = math.isclose(float(echoed[key]), float(placement[key]),
                                               rel_tol=0.0, abs_tol=1e-4)
                    except (KeyError, TypeError, ValueError):
                        matches = False
                    if not matches:
                        mismatches.append(
                            f"placement.{key}={echoed.get(key)!r}, expected {placement[key]!r}")
        if strict_build:
            if request["operation"] != "blueprint_build":
                mismatches.append("strict build validation received a non-build operation")
            if receipt.get("state") != "completed":
                mismatches.append(f"state={receipt.get('state')!r}, expected 'completed'")
            detail = receipt.get("detail")
            match = (re.match(
                rf"^build-at {re.escape(self.name)}: placed=(\d+) failed=(\d+)(?:\s|$)",
                detail,
            ) if isinstance(detail, str) else None)
            if not match:
                mismatches.append("detail does not carry the exact build-at placed/failed result")
            else:
                placed, failed = (int(value) for value in match.groups())
                if placed != self.piece_count:
                    mismatches.append(f"placed={placed}, expected {self.piece_count}")
                if failed != 0:
                    mismatches.append(f"failed={failed}, expected 0")
        if mismatches:
            raise RuntimeError("receipt correlation failed: " + "; ".join(mismatches))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, config=None, **kwargs):
        self.config = config
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, *_):
        pass

    def send_json(self, status, value):
        payload = (json.dumps(value, indent=2) + "\n").encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        operation = self.path.removeprefix("/api/")
        if operation not in {"apply", "clear"}:
            self.send_json(404, {"ok": False, "error": "unknown operation"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > MAX_BODY_BYTES:
                raise RuntimeError("request body is outside the probe bound")
            body = json.loads(self.rfile.read(length) or b"{}")
            placement = {
                "x": float(body.get("x", 0)), "y": float(body.get("y", 0)),
                "z": float(body.get("z", 0)),
                "yaw_degrees": float(body.get("yaw_degrees", 0)),
            }
            if operation == "apply":
                if not all(finite(placement[key], MAX_WORLD_COORDINATE)
                           for key in ("x", "y", "z")):
                    raise RuntimeError("coordinates must be finite and within +/-10500")
                if not finite(placement["yaw_degrees"], 3600.0):
                    raise RuntimeError("yaw must be finite and within +/-3600 degrees")
            envelope = self.config.dispatch(operation, placement)
            state = envelope["receipt"].get("state")
            self.send_json(200 if state == "completed" else 409,
                           {"ok": state == "completed", **envelope})
        except Exception as error:
            self.send_json(409, {"ok": False, "error": str(error)})


def command_line(args):
    values = [
        "python", str(Path(__file__).resolve()), "--plan", str(args.plan.resolve()),
        "--manifest", str(args.manifest.resolve()), "--blueprint", str(args.blueprint.resolve()),
        "--capture", str(args.capture.resolve()), "--lab-root", str(args.lab_root.resolve()),
        "--expected-machine", args.expected_machine, "--expected-world-uid", args.expected_world_uid,
        "--creator-session-id", args.creator_session_id, "--x", str(args.x), "--y", str(args.y),
        "--z", str(args.z), "--yaw", str(args.yaw), "--out", str(args.out.resolve()),
    ]
    if args.apply_once:
        values.append("--apply-once")
    return subprocess.list2cmdline(values)


def main():
    args = parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    name = validate_inputs(args, plan, manifest)
    if args.derive_only:
        print(json.dumps(derive_live_pair(args, name), indent=2))
        return
    validate_live_args(args)
    config = ProbeConfig(args, name, manifest["piece_count"])
    scene, _ = encode_scene(scene_pieces(plan), name,
                            f"canonical {manifest['piece_count']}-piece live-placement control",
                            args.out, 1, 0)
    scene.update({
        "live_endpoint": True,
        "asset_sha256": manifest["source_pieces_sha256"],
        "default_placement": {"x": args.x, "y": args.y, "z": args.z,
                              "yaw_degrees": args.yaw},
        "coordinate_space": "Unity world XYZ; Y is height; asset origin is local bounds minimum",
    })
    (args.out / "scene.json").write_text(json.dumps(scene, indent=1) + "\n", encoding="utf-8")
    staged = stage_reviewed_pair(config)
    rerun = command_line(args)
    print(json.dumps({"schema": "live-spatial-probe-prepare/v1", "asset": name,
                      "pieces": len(plan["pieces"]), "staged": staged,
                      "rerun_command": rerun}, indent=2))
    if args.prepare_only:
        return
    if args.apply_once:
        placement = {"x": args.x, "y": args.y, "z": args.z,
                     "yaw_degrees": args.yaw}
        envelope = config.dispatch("apply", placement, strict_build=True)
        print(json.dumps({"schema": "live-spatial-apply-once/v1", "status": "PASS",
                          "piece_count": manifest["piece_count"], **envelope}, indent=2))
        return

    handler = lambda *values, **kwargs: Handler(
        *values, directory=str(args.out), config=config, **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{server.server_port}/index.html"
    print(f"LIVE_SPATIAL_URL={url}")
    print(f"RERUN={rerun}")
    if not args.no_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

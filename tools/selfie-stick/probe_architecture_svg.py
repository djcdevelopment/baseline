#!/usr/bin/env python3
"""R&D probe: can oriented world-save boxes become an architectural SVG plate?

One frozen building, one vector sheet, one edge.  Cluster 1820's already-verified
847-piece main component is projected into an axonometric, an axis-aligned roof plan,
and the paired 78.8 / 258.8 degree elevations whose AM4 photographs distinguish a
thatched hip from a stone gable.  This is not a catalog generator or a CAD system.

The SVG is self-contained and cluster-local.  Absolute world coordinates, JavaScript,
external fonts, images, and network dependencies are deliberately excluded.
"""

import argparse
import hashlib
import html
import json
import math
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import duckdb
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from probe_css_render import find_browser, load_cluster, load_rotation_receipt
from reconstruct_cluster import BOX_CORNERS, load_geometry
from segment_buildings import segment


HERE = Path(__file__).resolve().parent
ARCH = HERE / "out" / "era17" / "arch"
DEFAULT_CLUSTER_POINTS = Path(r"E:\omen\steward-era17-arch\cluster-zdos.parquet")
DEFAULT_BUILDING_GEOMETRY = Path(r"E:\omen\steward-era17-arch\building-geometry.parquet")
DEFAULT_OUT = HERE / "out" / "era17" / "architecture-svg" / "cluster-1820"
SHEET_WIDTH = 1800
SHEET_HEIGHT = 1200
MAX_SVG_BYTES = 5 * 1024 * 1024
MAX_SVG_ELEMENTS = 25000
DIMENSION_TOLERANCE_M = 0.011

# Indices match reconstruct_cluster.BOX_CORNERS.  Normals are local and point out.
BOX_QUADS = (
    ((0, 2, 3, 1), (-1.0, 0.0, 0.0)),
    ((4, 5, 7, 6), (1.0, 0.0, 0.0)),
    ((0, 1, 5, 4), (0.0, -1.0, 0.0)),
    ((2, 6, 7, 3), (0.0, 1.0, 0.0)),
    ((0, 4, 6, 2), (0.0, 0.0, -1.0)),
    ((1, 3, 7, 5), (0.0, 0.0, 1.0)),
)

PLATE_COLORS = {
    "beam": "#725548", "door": "#3f9370", "floor": "#72583f",
    "gate": "#3f9d91", "light": "#d8a938", "misc": "#aab2b4",
    "pole": "#8d7064", "roof": "#b87932", "seat": "#86669a",
    "stair": "#c87830", "table": "#795b8b", "wall": "#77858a",
    "window": "#39a6c7", "fence": "#947d73", "portal": "#31b9c7",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster-points", type=Path, default=DEFAULT_CLUSTER_POINTS)
    parser.add_argument("--building-geometry", type=Path, default=DEFAULT_BUILDING_GEOMETRY)
    parser.add_argument("--piece-geometry", type=Path,
                        default=ARCH / "piece-geometry.json")
    parser.add_argument("--rotation-verify", type=Path,
                        default=ARCH / "rotation-verify.json")
    parser.add_argument("--roof-sections", type=Path,
                        default=ARCH / "roof-sections.json")
    parser.add_argument("--webgpu-manifest", type=Path,
                        default=HERE / "out" / "era17" / "webgpu-render" /
                        "pilot-1820" / "scene.json")
    parser.add_argument("--hip-photo", type=Path,
                        default=ARCH / "roofends" / "1820_roofend2.png")
    parser.add_argument("--gable-photo", type=Path,
                        default=ARCH / "roofends" / "1820_roofend1.png")
    parser.add_argument("--cluster-id", type=int, default=1820)
    parser.add_argument("--expected-pieces", type=int, default=847)
    parser.add_argument("--hip-bearing", type=float, default=78.8)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--browser", type=Path)
    parser.add_argument("--browser-timeout-s", type=float, default=45.0)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--visual-verdict", choices=("PENDING", "PASS", "FAIL"),
                        default="PENDING")
    parser.add_argument("--visual-observation", action="append", default=[])
    return parser.parse_args()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path):
    return {"path": str(path.resolve()), "bytes": path.stat().st_size,
            "sha256": sha256(path)}


def unit(vector):
    value = np.asarray(vector, dtype=float)
    length = float(np.linalg.norm(value))
    if not math.isfinite(length) or length <= 1e-12:
        raise RuntimeError(f"cannot normalize vector {vector}")
    return value / length


def horizontal_camera(bearing):
    radians = math.radians(bearing)
    return unit([math.sin(radians), 0.0, math.cos(radians)])


def elevation_view(view_id, label, bearing, expected, panel):
    camera = horizontal_camera(bearing)
    up = np.asarray([0.0, 1.0, 0.0])
    right = unit(np.cross(up, camera))
    return {"id": view_id, "label": label, "kind": "elevation",
            "bearing": bearing % 360.0, "expected": expected, "camera": camera,
            "right": right, "up": up, "panel": panel, "dimensions": True}


def plan_view(bearing, panel):
    radians = math.radians(bearing)
    right = unit([math.sin(radians), 0.0, math.cos(radians)])
    camera = np.asarray([0.0, 1.0, 0.0])
    up = unit(np.cross(camera, right))
    return {"id": "roof-plan", "label": "A1 · ROOF PLAN", "kind": "roof plan",
            "bearing": bearing % 360.0, "expected": "ridge axis horizontal",
            "camera": camera, "right": right, "up": up, "panel": panel,
            "dimensions": True}


def axonometric_view(panel):
    azimuth = 315.0
    elevation = 28.0
    az = math.radians(azimuth)
    el = math.radians(elevation)
    camera = unit([math.sin(az) * math.cos(el), math.sin(el),
                   math.cos(az) * math.cos(el)])
    world_up = np.asarray([0.0, 1.0, 0.0])
    right = unit(np.cross(world_up, camera))
    up = unit(np.cross(camera, right))
    return {"id": "axonometric", "label": "A0 · AXONOMETRIC", "kind": "axonometric",
            "bearing": azimuth, "elevation": elevation,
            "expected": "tower, storeys, and stepped roof", "camera": camera,
            "right": right, "up": up, "panel": panel, "dimensions": False}


def all_piece_corners(pieces, origin):
    corners = []
    by_zdo = {}
    for piece in pieces:
        physical = ((BOX_CORNERS * piece["extents"]) @ piece["R"].T
                    + piece["center"] - origin)
        if not np.all(np.isfinite(physical)):
            raise RuntimeError(f"non-finite oriented corners for ZDO {piece['zdo']}")
        corners.append(physical)
        by_zdo[piece["zdo"]] = physical
    return np.concatenate(corners), by_zdo


def project(points, view):
    points = np.asarray(points, dtype=float)
    return np.column_stack((points @ view["right"], points @ view["up"])), \
        points @ view["camera"]


def shade(color, normal):
    rgb = np.asarray([int(color[index:index + 2], 16) for index in (1, 3, 5)], dtype=float)
    light = unit([-0.35, 0.85, 0.28])
    amount = 0.68 + 0.26 * max(0.0, float(np.dot(unit(normal), light)))
    value = np.clip(rgb * amount + np.asarray([12.0, 15.0, 16.0]), 0, 255).astype(int)
    return "#%02x%02x%02x" % tuple(value)


def face_records(pieces, corners_by_zdo, view):
    faces = []
    per_piece = Counter()
    for piece in pieces:
        corners = corners_by_zdo[piece["zdo"]]
        for face_index, (indices, local_normal) in enumerate(BOX_QUADS):
            normal = piece["R"] @ np.asarray(local_normal, dtype=float)
            if float(np.dot(normal, view["camera"])) <= 1e-7:
                continue
            world_face = corners[np.asarray(indices)]
            points, depths = project(world_face, view)
            polygon = Polygon(points)
            if not polygon.is_valid:
                polygon = polygon.buffer(0)
            if polygon.is_empty or polygon.area <= 1e-8:
                continue
            family = piece["family"]
            faces.append({
                "zdo": piece["zdo"], "prefab": piece["name"], "family": family,
                "face": face_index, "points": points, "depth": float(depths.mean()),
                "normal": normal, "fill": shade(
                    PLATE_COLORS.get(family, PLATE_COLORS["misc"]), normal),
                "polygon": polygon,
            })
            per_piece[piece["zdo"]] += 1
    faces.sort(key=lambda face: (face["depth"], face["zdo"], face["face"]))
    return faces, per_piece


def view_geometry(pieces, all_corners, corners_by_zdo, view):
    projected, _ = project(all_corners, view)
    low = projected.min(axis=0)
    high = projected.max(axis=0)
    span = high - low
    if not np.all(np.isfinite(span)) or np.any(span <= 0):
        raise RuntimeError(f"invalid projected span for {view['id']}: {span}")
    faces, per_piece = face_records(pieces, corners_by_zdo, view)
    if len(per_piece) != len(pieces):
        missing = sorted(set(piece["zdo"] for piece in pieces) - set(per_piece))
        raise RuntimeError(f"view {view['id']} omitted {len(missing)} pieces")
    silhouette = unary_union([face["polygon"] for face in faces])
    if silhouette.is_empty:
        raise RuntimeError(f"view {view['id']} produced an empty silhouette")
    return {**view, "low": low, "high": high, "span": span,
            "faces": faces, "visible_piece_count": len(per_piece),
            "silhouette": silhouette}


def fmt(value):
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


def map_point(point, transform):
    return (transform["cx"] + (float(point[0]) - transform["mid"][0]) * transform["scale"],
            transform["cy"] - (float(point[1]) - transform["mid"][1]) * transform["scale"])


def panel_transform(view):
    x, y, width, height = view["panel"]
    drawing = {"x": x + 54, "y": y + 43, "w": width - 92, "h": height - 104}
    scale = min(drawing["w"] / float(view["span"][0]),
                drawing["h"] / float(view["span"][1]))
    return {"cx": drawing["x"] + drawing["w"] / 2,
            "cy": drawing["y"] + drawing["h"] / 2,
            "scale": scale, "mid": (view["low"] + view["high"]) / 2,
            "drawing": drawing}


def polygon_points(points, transform):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in
                    (map_point(point, transform) for point in points))


def silhouette_path(geometry, transform):
    polygons = ([geometry] if geometry.geom_type == "Polygon"
                else list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [])
    commands = []
    for polygon in polygons:
        for ring in [polygon.exterior, *polygon.interiors]:
            mapped = [map_point(point, transform) for point in ring.coords]
            if len(mapped) < 3:
                continue
            commands.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in mapped) + " Z")
    return " ".join(commands)


def dimension_markup(view, transform):
    if not view["dimensions"]:
        return []
    drawing = transform["drawing"]
    left, right = drawing["x"], drawing["x"] + drawing["w"]
    top, bottom = drawing["y"], drawing["y"] + drawing["h"]
    actual_left, _ = map_point([view["low"][0], 0], transform)
    actual_right, _ = map_point([view["high"][0], 0], transform)
    _, actual_top = map_point([0, view["high"][1]], transform)
    _, actual_bottom = map_point([0, view["low"][1]], transform)
    dim_y = min(bottom + 18, view["panel"][1] + view["panel"][3] - 18)
    dim_x = max(left - 18, view["panel"][0] + 18)
    return [
        f'<g class="dimensions" aria-label="{fmt(view["span"][0])} metres wide by '
        f'{fmt(view["span"][1])} metres high">',
        f'<path d="M{actual_left:.2f},{dim_y:.2f}H{actual_right:.2f} '
        f'M{actual_left:.2f},{dim_y-5:.2f}V{dim_y+5:.2f} '
        f'M{actual_right:.2f},{dim_y-5:.2f}V{dim_y+5:.2f}"/>',
        f'<text x="{(actual_left+actual_right)/2:.2f}" y="{dim_y-5:.2f}" '
        f'text-anchor="middle">{fmt(view["span"][0])} m</text>',
        f'<path d="M{dim_x:.2f},{actual_top:.2f}V{actual_bottom:.2f} '
        f'M{dim_x-5:.2f},{actual_top:.2f}H{dim_x+5:.2f} '
        f'M{dim_x-5:.2f},{actual_bottom:.2f}H{dim_x+5:.2f}"/>',
        f'<text x="{dim_x+6:.2f}" y="{(actual_top+actual_bottom)/2:.2f}" '
        f'transform="rotate(-90 {dim_x+6:.2f} {(actual_top+actual_bottom)/2:.2f})" '
        f'text-anchor="middle">{fmt(view["span"][1])} m</text>',
        '</g>',
    ]


def view_markup(view):
    x, y, width, height = view["panel"]
    transform = panel_transform(view)
    lines = [
        f'<g id="view-{view["id"]}" class="view" data-kind="{view["kind"]}" '
        f'data-bearing="{view["bearing"]:.1f}">',
        f'<rect class="panel" x="{x}" y="{y}" width="{width}" height="{height}" rx="2"/>',
        f'<text class="view-label" x="{x+18}" y="{y+25}">{html.escape(view["label"])}</text>',
        f'<text class="view-note" x="{x+width-18}" y="{y+25}" text-anchor="end">'
        f'{html.escape(view["expected"])}</text>',
        '<g class="faces">',
    ]
    for face in view["faces"]:
        lines.append(
            f'<polygon id="{view["id"]}-zdo-{face["zdo"]}-face-{face["face"]}" '
            f'class="face family-{html.escape(face["family"], quote=True)}" '
            f'data-zdo="{face["zdo"]}" data-prefab="{html.escape(face["prefab"], quote=True)}" '
            f'data-family="{html.escape(face["family"], quote=True)}" '
            f'points="{polygon_points(face["points"], transform)}" fill="{face["fill"]}"/>')
    lines.extend([
        '</g>',
        f'<path class="silhouette" d="{silhouette_path(view["silhouette"], transform)}"/>',
        *dimension_markup(view, transform),
        '</g>',
    ])
    return lines


def source_aabb(pieces):
    low = np.full(3, np.inf)
    high = np.full(3, -np.inf)
    for piece in pieces:
        corners = (BOX_CORNERS * piece["extents"]) @ piece["R"].T + piece["center"]
        low = np.minimum(low, corners.min(axis=0))
        high = np.maximum(high, corners.max(axis=0))
    return low, high


def svg_document(cluster_id, pieces, join, views, rotation_winner, roof_record,
                 source_dimensions, source_hashes):
    families = Counter(piece["family"] for piece in pieces)
    legend = []
    legend_x, legend_y = 56, 1096
    for index, (family, count) in enumerate(sorted(families.items())):
        column, row = index % 7, index // 7
        x, y = legend_x + column * 122, legend_y + row * 28
        color = PLATE_COLORS.get(family, PLATE_COLORS["misc"])
        legend.extend([
            f'<rect x="{x}" y="{y-11}" width="10" height="10" fill="{color}"/>',
            f'<text class="legend" x="{x+16}" y="{y-2}">{html.escape(family)} {count}</text>',
        ])
    dimensions = " × ".join(f"{value:.2f}" for value in source_dimensions)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_WIDTH}" '
        f'height="{SHEET_HEIGHT}" viewBox="0 0 {SHEET_WIDTH} {SHEET_HEIGHT}" '
        f'role="img" aria-labelledby="sheet-title sheet-desc">',
        '<title id="sheet-title">Cluster 1820 architectural survey</title>',
        '<desc id="sheet-desc">Four cluster-local projections of the 847-piece main structure: '
        'axonometric, roof plan, thatched hip elevation at 78.8 degrees, and stone gable '
        'elevation at 258.8 degrees.</desc>',
        '<defs>',
        '<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">'
        '<path d="M20 0H0V20" fill="none" stroke="#1d2a31" stroke-width="0.55"/></pattern>',
        '<style>',
        'text{fill:#dce4e5;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}',
        '.eyebrow{fill:#d79a3b;font:700 12px ui-monospace,monospace;letter-spacing:2.2px}',
        '.title{font-size:30px;font-weight:620;letter-spacing:-.5px}',
        '.subtitle{fill:#95a5aa;font:13px ui-monospace,monospace}',
        '.panel{fill:url(#grid);stroke:#34464f;stroke-width:1}',
        '.view-label{fill:#d79a3b;font:700 12px ui-monospace,monospace;letter-spacing:1.4px}',
        '.view-note{fill:#83959b;font:11px ui-monospace,monospace}',
        '.face{stroke:#172229;stroke-width:.38;stroke-linejoin:round}',
        '.silhouette{fill:none;stroke:#ede5d5;stroke-width:1.45;stroke-linejoin:round;pointer-events:none}',
        '.dimensions path{fill:none;stroke:#6fc1d3;stroke-width:.8}',
        '.dimensions text{fill:#8fd0dd;font:10px ui-monospace,monospace}',
        '.legend{fill:#aab8bc;font:11px ui-monospace,monospace}',
        '.footer-label{fill:#65777e;font:10px ui-monospace,monospace;letter-spacing:1px}',
        '.footer-value{fill:#bdc8ca;font:11px ui-monospace,monospace}',
        '</style>',
        '</defs>',
        '<rect width="1800" height="1200" fill="#10171b"/>',
        '<path d="M40 103H1760" stroke="#34464f"/>',
        '<text class="eyebrow" x="40" y="34">BUILDINGS FROM BYTES / ARCHITECTURAL SURVEY</text>',
        f'<text class="title" x="40" y="72">CLUSTER {cluster_id} · MAIN STRUCTURE</text>',
        f'<text class="subtitle" x="1760" y="37" text-anchor="end">{len(pieces)} PIECES · '
        f'{dimensions} M</text>',
        f'<text class="subtitle" x="1760" y="66" text-anchor="end">'
        f'{html.escape(roof_record["main_mass_class"].upper())} · ROTATION {html.escape(rotation_winner)}</text>',
    ]
    for view in views:
        lines.extend(view_markup(view))
    lines.extend([
        '<path d="M40 1050H1760" stroke="#34464f"/>',
        '<text class="footer-label" x="40" y="1074">FAMILY LAYERS</text>',
        *legend,
        '<path d="M930 1068V1170" stroke="#34464f"/>',
        '<text class="footer-label" x="956" y="1090">SOURCE CONTRACT</text>',
        f'<text class="footer-value" x="956" y="1112">frozen members {join["frozen_members"]} '
        f'· joined {join["joined_rotation_rows"]} · mismatches {join["join_mismatches"]}</text>',
        f'<text class="footer-value" x="956" y="1133">geometry snap {join["geometry_sources"].get("snap", 0)} '
        f'· snap+mesh {join["geometry_sources"].get("snap+mesh", 0)} '
        f'· mesh {join["geometry_sources"].get("mesh", 0)}</text>',
        f'<text class="footer-value" x="956" y="1154">membership {source_hashes["cluster_points"][:12]} '
        f'· geometry {source_hashes["piece_geometry"][:12]} '
        f'· roof evidence {source_hashes["roof_sections"][:12]}</text>',
        '<text class="footer-label" x="1760" y="1182" text-anchor="end">'
        'CLUSTER-LOCAL ORIENTED-BOX PROXIES · NO TERRAIN · NO MESH SURFACES · R&amp;D</text>',
        '</svg>',
    ])
    return "\n".join(lines) + "\n", dict(sorted(families.items()))


def capture_svg(browser, svg_path, png_path, timeout_s):
    started = time.perf_counter()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
            prefix="architecture-svg-capture-", ignore_cleanup_errors=True) as profile:
        command = [str(browser), "--headless=new", "--no-first-run",
                   "--disable-default-apps", "--disable-extensions",
                   "--disable-background-networking", "--disable-component-update",
                   "--disable-sync", "--metrics-recording-only", "--mute-audio",
                   "--hide-scrollbars", "--allow-file-access-from-files",
                   "--run-all-compositor-stages-before-draw",
                   "--disable-renderer-backgrounding", "--disable-background-timer-throttling",
                   f"--user-data-dir={profile}", f"--window-size={SHEET_WIDTH},{SHEET_HEIGHT}",
                   "--force-device-scale-factor=1", "--virtual-time-budget=2500",
                   f"--screenshot={png_path.resolve()}", svg_path.resolve().as_uri()]
        try:
            process = subprocess.run(command, capture_output=True, text=True,
                                     timeout=timeout_s, encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return {"status": "browser_timeout", "path": str(png_path),
                    "wall_ms": round((time.perf_counter() - started) * 1000, 2)}
    receipt = {"status": "ok" if process.returncode == 0 and png_path.is_file()
               else "capture_error", "returncode": process.returncode,
               "path": str(png_path),
               "wall_ms": round((time.perf_counter() - started) * 1000, 2),
               "stderr_tail": process.stderr[-1200:]}
    if png_path.is_file():
        receipt["bytes"] = png_path.stat().st_size
    return receipt


def command_line(args):
    values = [
        sys.executable, str(Path(__file__).resolve()),
        "--cluster-points", str(args.cluster_points.resolve()),
        "--building-geometry", str(args.building_geometry.resolve()),
        "--piece-geometry", str(args.piece_geometry.resolve()),
        "--rotation-verify", str(args.rotation_verify.resolve()),
        "--roof-sections", str(args.roof_sections.resolve()),
        "--webgpu-manifest", str(args.webgpu_manifest.resolve()),
        "--hip-photo", str(args.hip_photo.resolve()),
        "--gable-photo", str(args.gable_photo.resolve()),
        "--cluster-id", str(args.cluster_id), "--expected-pieces", str(args.expected_pieces),
        "--hip-bearing", str(args.hip_bearing), "--out", str(args.out.resolve()),
        "--visual-verdict", args.visual_verdict,
    ]
    for observation in args.visual_observation:
        values.extend(["--visual-observation", observation])
    if args.browser:
        values.extend(["--browser", str(args.browser.resolve())])
    if args.no_browser:
        values.append("--no-browser")
    return subprocess.list2cmdline(values)


def main():
    args = parse_args()
    required = [args.cluster_points, args.building_geometry, args.piece_geometry,
                args.rotation_verify, args.roof_sections, args.webgpu_manifest,
                args.hip_photo, args.gable_photo]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("required evidence is missing: " + ", ".join(missing))

    winner, (to_rad, compose) = load_rotation_receipt(args.rotation_verify)
    geometry = load_geometry(args.piece_geometry)
    con = duckdb.connect()
    all_pieces, join = load_cluster(
        con, args.cluster_id, args.cluster_points, args.building_geometry,
        geometry, to_rad, compose)
    components = segment(all_pieces)
    pieces = [all_pieces[index] for index in components[0]]
    if len(pieces) != args.expected_pieces:
        raise RuntimeError(
            f"main component changed: {len(pieces)} != {args.expected_pieces}")

    roof_document = json.loads(args.roof_sections.read_text(encoding="utf-8"))
    roof_record = roof_document.get("clusters", {}).get(str(args.cluster_id))
    if not roof_record or roof_record.get("main_structure_pieces") != len(pieces):
        raise RuntimeError("roof evidence does not pin the selected main component")
    roof_bearings = [float(value) for value in roof_record.get("main_mass_bearings", [])]
    if not any(abs(((value - args.hip_bearing + 180) % 360) - 180) <= 0.15
               for value in roof_bearings):
        raise RuntimeError("hip bearing is absent from the frozen roof evidence")
    gable_bearing = (args.hip_bearing + 180.0) % 360.0

    low, high = source_aabb(pieces)
    origin = (low + high) / 2.0
    source_dimensions = high - low
    all_corners, corners_by_zdo = all_piece_corners(pieces, origin)
    panels = ((40, 125, 830, 430), (930, 125, 830, 430),
              (40, 585, 830, 430), (930, 585, 830, 430))
    view_specs = [
        axonometric_view(panels[0]),
        plan_view(args.hip_bearing, panels[1]),
        elevation_view("hip-078-8", "A2 · 78.8° ELEVATION", args.hip_bearing,
                       "thatched sloping hip plane", panels[2]),
        elevation_view("gable-258-8", "A3 · 258.8° ELEVATION", gable_bearing,
                       "stone gable · window rows", panels[3]),
    ]
    views = [view_geometry(pieces, all_corners, corners_by_zdo, view)
             for view in view_specs]

    source_paths = {
        "cluster_points": args.cluster_points, "building_geometry": args.building_geometry,
        "piece_geometry": args.piece_geometry, "rotation_verify": args.rotation_verify,
        "roof_sections": args.roof_sections, "webgpu_manifest": args.webgpu_manifest,
        "hip_photo": args.hip_photo, "gable_photo": args.gable_photo,
    }
    sources = {name: artifact(path) for name, path in source_paths.items()}
    source_hashes = {name: record["sha256"] for name, record in sources.items()}
    svg_text, family_counts = svg_document(
        args.cluster_id, pieces, join, views, winner, roof_record,
        source_dimensions, source_hashes)

    args.out.mkdir(parents=True, exist_ok=True)
    svg_path = args.out / "survey.svg"
    svg_path.write_text(svg_text, encoding="utf-8")
    xml_valid = True
    xml_error = ""
    try:
        root = ET.parse(svg_path).getroot()
        element_count = sum(1 for _ in root.iter())
    except ET.ParseError as error:
        xml_valid = False
        xml_error = str(error)
        element_count = 0

    webgpu = json.loads(args.webgpu_manifest.read_text(encoding="utf-8"))
    expected_dimensions = np.asarray(webgpu.get("dimensions_m", []), dtype=float)
    dimension_error = (np.abs(source_dimensions - expected_dimensions)
                       if expected_dimensions.shape == (3,) else np.full(3, np.inf))
    browser = None if args.no_browser else find_browser(args.browser)
    capture = ({"status": "browser_not_found"} if browser is None and not args.no_browser
               else {"status": "skipped"} if args.no_browser
               else capture_svg(browser, svg_path, args.out / "survey.png",
                                args.browser_timeout_s))

    mechanical_reasons = []
    if join["frozen_members"] != 861 or join["joined_rotation_rows"] != 861:
        mechanical_reasons.append("frozen membership or rotation join changed")
    if join["join_mismatches"] != 0 or join["missing_geometry_rows"] != 0:
        mechanical_reasons.append("geometry join is incomplete or mismatched")
    if len(pieces) != args.expected_pieces:
        mechanical_reasons.append("main component piece count changed")
    if not xml_valid:
        mechanical_reasons.append("SVG XML parse failed")
    if svg_path.stat().st_size > MAX_SVG_BYTES:
        mechanical_reasons.append("SVG exceeds 5 MiB")
    if element_count > MAX_SVG_ELEMENTS:
        mechanical_reasons.append("SVG exceeds 25,000 elements")
    if not np.all(dimension_error <= DIMENSION_TOLERANCE_M):
        mechanical_reasons.append("source AABB disagrees with the WebGPU control")
    if not args.no_browser and capture.get("status") != "ok":
        mechanical_reasons.append("headless browser did not paint the SVG")

    mechanical = "PASS" if not mechanical_reasons else "FAIL"
    overall = ("FAIL" if mechanical == "FAIL" or args.visual_verdict == "FAIL"
               else "PASS" if args.visual_verdict == "PASS" else "PENDING")
    result = {
        "schema": "architecture-svg-rnd/v1", "status": overall,
        "question": "can oriented world-save boxes become a legible architectural plate?",
        "cluster_id": args.cluster_id, "coordinate_space": "cluster-local; world origin withheld",
        "rotation_decode": winner, "join": join, "components": len(components),
        "main_component_pieces": len(pieces), "family_counts": family_counts,
        "source_aabb_dimensions_m": [round(float(value), 4) for value in source_dimensions],
        "webgpu_control_dimensions_m": webgpu.get("dimensions_m"),
        "dimension_error_m": [round(float(value), 6) for value in dimension_error],
        "roof_evidence": {"classification": roof_record["main_mass_class"],
                          "main_mass_bearings": roof_bearings,
                          "hip_bearing": args.hip_bearing,
                          "gable_bearing": gable_bearing},
        "views": [{"id": view["id"], "kind": view["kind"],
                   "bearing": view["bearing"],
                   "projected_span_m": [round(float(value), 4) for value in view["span"]],
                   "faces": len(view["faces"]),
                   "visible_pieces": view["visible_piece_count"],
                   "expected": view["expected"]} for view in views],
        "artifact": {"svg": artifact(svg_path), "element_count": element_count,
                     "xml_valid": xml_valid, "xml_error": xml_error,
                     "external_dependencies": []},
        "browser": str(browser) if browser else None, "capture": capture,
        "gates": {"mechanical": mechanical, "mechanical_reasons": mechanical_reasons,
                  "max_svg_bytes": MAX_SVG_BYTES, "max_svg_elements": MAX_SVG_ELEMENTS,
                  "dimension_tolerance_m": DIMENSION_TOLERANCE_M,
                  "visual": args.visual_verdict,
                  "visual_observations": args.visual_observation},
        "sources": sources, "rerun_command": command_line(args),
        "uncertainties": [
            "oriented boxes are massing proxies rather than render meshes",
            "global face-depth sorting is not exact hidden-surface removal for intersecting boxes",
            "roof plan is a top projection, not a semantic floor-plan cut",
            "dimension strings describe proxy envelopes, not build snap dimensions",
            "paired photographic controls include terrain, vegetation, lighting, and perspective",
            "one building cannot establish a catalog or general bearing inference",
        ],
        "promotion": "none; one passed plate earns a later shelter/catalog lap",
    }
    result_path = args.out / "result.json"
    result_path.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"status": overall, "mechanical": mechanical,
                      "visual": args.visual_verdict, "svg": str(svg_path),
                      "capture": capture, "result": str(result_path),
                      "pieces": len(pieces), "elements": element_count,
                      "bytes": svg_path.stat().st_size,
                      "rerun_command": result["rerun_command"]}, indent=2))
    if mechanical == "FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Derive component-local roof semantics from verified ZDO geometry.

The first architecture pass counted roof-piece yaws across an entire cluster.  That
mixes detached buildings and is numerically unstable at snapped half-angles.  This
module instead:

* reconstructs exact snap connectivity from raw (unrounded) rotations;
* separates roof-to-roof assemblies inside structural components;
* derives roof-plane normals from each prefab's snap points; and
* emits a private, versioned architecture companion keyed to frozen cluster ids.

Coordinates remain in ignored ``out/`` artifacts.  Public receipts should carry only
aggregate results, source revisions, byte counts, and SHA-256 hashes.
"""

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict

import duckdb
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.join(HERE, "out", "era17", "arch")
MODEL_VERSION = "roof-plane-assemblies/v1"
SCHEMA = "selfie-stick-architecture/v2"
ANGLE_STEP_DEG = 11.25


def rx(angle):
    cosine, sine = np.cos(angle), np.sin(angle)
    matrix = np.zeros(angle.shape + (3, 3))
    matrix[..., 0, 0] = 1
    matrix[..., 1, 1] = cosine
    matrix[..., 1, 2] = -sine
    matrix[..., 2, 1] = sine
    matrix[..., 2, 2] = cosine
    return matrix


def ry(angle):
    cosine, sine = np.cos(angle), np.sin(angle)
    matrix = np.zeros(angle.shape + (3, 3))
    matrix[..., 1, 1] = 1
    matrix[..., 0, 0] = cosine
    matrix[..., 0, 2] = sine
    matrix[..., 2, 0] = -sine
    matrix[..., 2, 2] = cosine
    return matrix


def rz(angle):
    cosine, sine = np.cos(angle), np.sin(angle)
    matrix = np.zeros(angle.shape + (3, 3))
    matrix[..., 2, 2] = 1
    matrix[..., 0, 0] = cosine
    matrix[..., 0, 1] = -sine
    matrix[..., 1, 0] = sine
    matrix[..., 1, 1] = cosine
    return matrix


# Keep the verifier's published hypotheses local so this report-only module does not
# inherit its optional SciPy dependency.  The winner still comes from the frozen
# rotation-verify.json receipt rather than being hardcoded here.
HYPOTHESES = {
    "deg_unity": (math.radians(1.0),
                  lambda x, y, z: ry(y) @ rx(x) @ rz(z)),
    "deg_unity_neg": (math.radians(-1.0),
                      lambda x, y, z: ry(y) @ rx(x) @ rz(z)),
    "deg_xyz": (math.radians(1.0),
                lambda x, y, z: rx(x) @ ry(y) @ rz(z)),
    "deg_zxy": (math.radians(1.0),
                lambda x, y, z: rz(z) @ rx(x) @ ry(y)),
    "rad_unity": (1.0, lambda x, y, z: ry(y) @ rx(x) @ rz(z)),
}


def euler_matrix(rot_xv, rot_yv, rot_zv, to_rad, compose):
    ax = np.asarray([rot_xv * to_rad])
    ay = np.asarray([rot_yv * to_rad])
    az = np.asarray([rot_zv * to_rad])
    return compose(ax, ay, az)[0]


def load_geometry(path):
    with open(path, encoding="utf-8") as stream:
        geometry = json.load(stream)
    return {entry["name"]: entry for entry in geometry["pieces"]}


def piece_pose(row, geom, to_rad, compose):
    x, y, z = row[3], row[4], row[5]
    has_rot, rot_xv, rot_yv, rot_zv = row[6], row[7], row[8], row[9]
    rotation = (euler_matrix(rot_xv, rot_yv, rot_zv, to_rad, compose)
                if has_rot else np.eye(3))
    pivot = np.array([x, y, z])
    center = pivot + rotation @ np.asarray(geom["center_offset"])
    return pivot, rotation, center


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.weight = [1] * size

    def find(self, value):
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left, right):
        left, right = self.find(left), self.find(right)
        if left == right:
            return
        if self.weight[left] < self.weight[right]:
            left, right = right, left
        self.parent[right] = left
        self.weight[left] += self.weight[right]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster-ids", required=True,
                        help="comma-separated frozen cluster ids")
    parser.add_argument("--parquet", required=True,
                        help="explicit building-geometry.parquet with raw rotations")
    parser.add_argument("--cluster-points", required=True,
                        help="exact frozen BUILDING membership from export_cluster_points.py")
    parser.add_argument("--geometry", default=os.path.join(ARCH, "piece-geometry.json"))
    parser.add_argument("--clusters", default=os.path.join(HERE, "out", "era17",
                                                            "clusters.json"))
    parser.add_argument("--verify", default=os.path.join(ARCH, "rotation-verify.json"))
    parser.add_argument("--out", default=os.path.join(HERE, "out", "era17",
                                                       "roof-semantics"))
    parser.add_argument("--epsilon", type=float, default=0.05)
    parser.add_argument("--orphan-distance", type=float, default=0.20)
    parser.add_argument("--source-revision", default="",
                        help="40-character ComfyStewardView revision recorded as provenance")
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def circular_distance(left, right):
    return abs((left - right + 180.0) % 360.0 - 180.0)


def quantize_bearing(value):
    """Nearest 11.25-degree bin without banker's-rounding half-step drift."""
    return (math.floor((value % 360.0 + ANGLE_STEP_DEG / 2.0) / ANGLE_STEP_DEG)
            * ANGLE_STEP_DEG) % 360.0


def convex_hull_area(points):
    """Area of a small 2-D point set via monotonic-chain hull + shoelace."""
    values = sorted({(float(point[0]), float(point[1])) for point in points})
    if len(values) < 3:
        return 0.0

    def cross(origin, left, right):
        return ((left[0] - origin[0]) * (right[1] - origin[1])
                - (left[1] - origin[1]) * (right[0] - origin[0]))

    lower = []
    for point in values:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(values):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    hull = lower[:-1] + upper[:-1]
    return abs(sum(hull[index][0] * hull[(index + 1) % len(hull)][1]
                   - hull[(index + 1) % len(hull)][0] * hull[index][1]
                   for index in range(len(hull)))) / 2.0


def spatial_pairs(points, radius):
    """Yield index pairs within ``radius`` using a deterministic 3-D cell hash."""
    if radius <= 0:
        return
    cells = defaultdict(list)
    radius_sq = radius * radius
    for index, point in enumerate(points):
        cell = tuple(math.floor(float(value) / radius) for value in point)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for other in cells.get((cell[0] + dx, cell[1] + dy,
                                            cell[2] + dz), ()):
                        delta = point - points[other]
                        if float(delta @ delta) <= radius_sq:
                            yield other, index
        cells[cell].append(index)


def planar_snap_normal(geom, rotation):
    """Return an upward world normal, panel area and planarity, or ``None``.

    Roof panels expose a coplanar snap rectangle.  Corners and junction pieces do
    not, so their smallest singular value is deliberately too large for this gate.
    """
    points = np.asarray(geom.get("snap_points") or [], dtype=float)
    if len(points) < 3:
        return None
    centered = points - points.mean(axis=0)
    _u, singular, axes = np.linalg.svd(centered, full_matrices=False)
    if singular[0] <= 1e-8:
        return None
    planarity = float(singular[-1] / singular[0])
    if planarity > 0.05:
        return None

    local_normal = axes[-1]
    world_normal = rotation @ local_normal
    norm = float(np.linalg.norm(world_normal))
    if norm <= 1e-8:
        return None
    world_normal /= norm
    if world_normal[1] < 0:
        world_normal *= -1.0

    # Project the coplanar points into their two principal axes.  Hull area is a
    # weighting signal, not mesh surface truth.
    projected = centered @ axes[:2].T
    area = convex_hull_area(projected)
    if not math.isfinite(area) or area <= 1e-6:
        return None
    return world_normal, area, planarity


def classify_roof_votes(votes, assembly_area, piece_count, prefabs=()):
    """Classify one roof assembly from area-weighted plane-normal votes."""
    result = {
        "shape_estimate": "unknown",
        "ridge_bearing_deg": None,
        "ridge_bearings_deg": [],
        "slope_bearings_deg": [],
        "confidence": 0.0,
        "usable_panel_pieces": len(votes),
        "usable_panel_area_m2": round(sum(v["area"] for v in votes), 2),
        "uncertainty_codes": [],
    }
    if piece_count < 2 or not votes or assembly_area <= 0:
        result["uncertainty_codes"].append("insufficient_planar_panels")
        return result

    usable_area = sum(v["area"] for v in votes)
    usable_coverage = min(1.0, usable_area / assembly_area)
    result["usable_area_fraction"] = round(usable_coverage, 3)
    if usable_coverage < 0.45:
        result["uncertainty_codes"].append("low_planar_area_coverage")

    flat_area = sum(v["area"] for v in votes if v["tilt_deg"] <= 10.0)
    sloped = [v for v in votes if 10.0 < v["tilt_deg"] < 80.0]
    if flat_area / usable_area >= 0.80:
        result.update({"shape_estimate": "flat",
                       "confidence": round(usable_coverage * flat_area / usable_area, 3)})
        return result
    if not sloped:
        result["uncertainty_codes"].append("no_sloped_panel_votes")
        return result

    bins = defaultdict(float)
    pieces_by_bin = Counter()
    prefabs_by_bin = defaultdict(Counter)
    for vote in sloped:
        bearing = quantize_bearing(vote["bearing_deg"])
        bins[bearing] += vote["area"]
        pieces_by_bin[bearing] += 1
        prefabs_by_bin[bearing][vote.get("prefab", "unknown")] += 1
    sloped_area = sum(bins.values())
    significant = {bearing: area for bearing, area in bins.items()
                   if area / sloped_area >= 0.10 and pieces_by_bin[bearing] >= 2}
    mode_coverage = sum(significant.values()) / sloped_area if sloped_area else 0.0
    ordered = sorted(significant)
    result["slope_bearings_deg"] = [round(value, 2) for value in ordered]
    result["mode_evidence"] = [
        {"bearing_deg": round(value, 2), "area_m2": round(bins[value], 2),
         "pieces": pieces_by_bin[value],
         "top_prefabs": [[name, count] for name, count in
                         prefabs_by_bin[value].most_common(3)]}
        for value in sorted(bins)
    ]
    result["mode_area_fraction"] = round(mode_coverage, 3)

    opposite_pairs = []
    used = set()
    for bearing in ordered:
        if bearing in used:
            continue
        candidates = [other for other in ordered if other != bearing and other not in used
                      and circular_distance((bearing + 180.0) % 360.0, other)
                      <= ANGLE_STEP_DEG]
        if candidates:
            other = min(candidates,
                        key=lambda value: circular_distance((bearing + 180.0) % 360.0,
                                                            value))
            opposite_pairs.append((bearing, other))
            used.update((bearing, other))

    quality = usable_coverage * mode_coverage
    pair_rows = sorted(
        ((significant[left] + significant[right], left, right)
         for left, right in opposite_pairs), reverse=True)
    inner_corners = sum(1 for name in prefabs if "icorner" in name.lower())
    outer_corners = sum(1 for name in prefabs if "ocorner" in name.lower())
    result["topology_evidence"] = {
        "opposing_slope_pairs": len(opposite_pairs),
        "inner_corner_pieces": inner_corners,
        "outer_corner_pieces": outer_corners,
    }

    # One opposing slope pair is the irreducible gable signal. Additional unmatched
    # planes are attached sheds/wings, not evidence that the gable ends disappeared.
    if len(opposite_pairs) == 1 and mode_coverage >= 0.80:
        _pair_weight, left, right = pair_rows[0]
        pair_area = significant[left] + significant[right]
        balance = 2.0 * min(significant[left], significant[right]) / pair_area
        pair_fraction = pair_area / sloped_area
        if balance >= 0.40 and pair_fraction >= 0.35:
            # Opposing slope normals share one ridge axis, perpendicular modulo 180.
            axis = left % 180.0
            ridge = round((axis + 90.0) % 180.0, 2)
            result.update({
                "shape_estimate": "gable",
                "ridge_bearing_deg": ridge,
                "ridge_bearings_deg": [ridge],
                "confidence": round(quality * balance * max(0.75, pair_fraction), 3),
            })
            if len(ordered) > 2:
                result["uncertainty_codes"].append("attached_unpaired_roof_planes")
            return result

    # Intersecting gables have two complete slope pairs plus inside-corner pieces.
    # They are still gabled architecture, but there is no single honest ridge axis.
    if len(opposite_pairs) >= 2 and inner_corners and mode_coverage >= 0.80:
        ridges = sorted({round((left % 180.0 + 90.0) % 180.0, 2)
                         for _weight, left, _right in pair_rows})
        result.update({"shape_estimate": "gable",
                       "ridge_bearings_deg": ridges,
                       "confidence": round(quality * pair_rows[0][0] / sloped_area, 3)})
        result["uncertainty_codes"].append("multiple_gable_ridge_axes")
        return result

    if len(ordered) == 4 and len(opposite_pairs) == 2 and not inner_corners \
            and mode_coverage >= 0.80:
        result.update({"shape_estimate": "hip",
                       "confidence": round(quality, 3)})
        result["uncertainty_codes"].append("hip_has_no_single_ridge_axis")
        return result

    result.update({"shape_estimate": "complex", "confidence": round(quality, 3)})
    result["uncertainty_codes"].append("slope_modes_do_not_form_simple_roof")
    return result


def _bounds(posed, indexes):
    points = np.asarray([posed[index][2] for index in indexes])
    return {
        "min": [round(float(value), 2) for value in points.min(axis=0)],
        "max": [round(float(value), 2) for value in points.max(axis=0)],
    }


def load_exact_members(connection, building_parquet, point_parquet, cluster_doc, targets):
    """Join rotation rows to exact frozen BUILDING membership by ``zdo_index``."""
    building_sql = building_parquet.replace("'", "''").replace("\\", "/")
    point_sql = point_parquet.replace("'", "''").replace("\\", "/")
    connection.execute(
        f"CREATE TEMP VIEW building_source AS SELECT * FROM read_parquet('{building_sql}')")
    connection.execute(
        f"CREATE TEMP VIEW point_source AS SELECT * FROM read_parquet('{point_sql}')")

    point_columns = {row[1] for row in
                     connection.execute("PRAGMA table_info('point_source')").fetchall()}
    building_columns = {row[1] for row in
                        connection.execute("PRAGMA table_info('building_source')").fetchall()}
    required_points = {"snapshot_id", "world_id", "cluster_id", "zdo_index",
                       "prefab_hash", "prefab_name", "category", "x", "y", "z"}
    required_building = {"zdo_index", "prefab_hash", "prefab_name", "category",
                         "x", "y", "z", "has_rot", "rot_x", "rot_y", "rot_z",
                         "creator_id"}
    if required_points - point_columns:
        raise ValueError("cluster point artifact missing: "
                         + ", ".join(sorted(required_points - point_columns)))
    if required_building - building_columns:
        raise ValueError("building geometry artifact missing: "
                         + ", ".join(sorted(required_building - building_columns)))

    metadata = connection.execute(
        "SELECT DISTINCT snapshot_id, world_id FROM point_source "
        "ORDER BY snapshot_id, world_id").fetchall()
    expected_metadata = (cluster_doc.get("snapshot_id"), cluster_doc.get("world_id"))
    if metadata != [expected_metadata]:
        raise ValueError(f"cluster points belong to {metadata}, clusters.json is "
                         f"{expected_metadata}")

    frozen_by_id = {int(item["cluster_id"]): item for item in cluster_doc["clusters"]}
    members = {}
    for cluster_id in targets:
        expected_count = int(frozen_by_id[cluster_id]["pieces"])
        count, join_missing, mismatches = connection.execute("""
            SELECT count(*),
                   count(*) FILTER (WHERE b.zdo_index IS NULL),
                   count(*) FILTER (WHERE b.zdo_index IS NOT NULL AND (
                       p.prefab_hash IS DISTINCT FROM b.prefab_hash OR
                       p.prefab_name IS DISTINCT FROM b.prefab_name OR
                       p.category IS DISTINCT FROM b.category OR
                       p.x IS DISTINCT FROM b.x OR p.y IS DISTINCT FROM b.y OR
                       p.z IS DISTINCT FROM b.z))
            FROM point_source p
            LEFT JOIN building_source b USING (zdo_index)
            WHERE p.cluster_id = ? AND p.category = 'BUILDING'
            """, [cluster_id]).fetchone()
        if count != expected_count or join_missing or mismatches:
            raise ValueError(
                f"cluster {cluster_id} exact-member gate failed: rows "
                f"{count}/{expected_count}, missing rotation rows {join_missing}, "
                f"identity/coordinate mismatches {mismatches}")
        members[cluster_id] = connection.execute("""
            SELECT b.zdo_index, b.prefab_name, b.category, b.x, b.y, b.z,
                   b.has_rot, b.rot_x, b.rot_y, b.rot_z, b.creator_id
            FROM point_source p
            JOIN building_source b USING (zdo_index)
            WHERE p.cluster_id = ? AND p.category = 'BUILDING'
            ORDER BY p.zdo_index
            """, [cluster_id]).fetchall()
    return members


def derive_cluster_roofs(cluster_id, rows, geom_by_name, to_rad, compose,
                         epsilon=0.05, orphan_distance=0.20):
    """Pure derivation used by the CLI and synthetic regression tests."""
    posed = []
    source_indexes = []
    for row in rows:
        geom = geom_by_name.get(row[1])
        if not geom:
            continue
        pivot, rotation, center = piece_pose(row, geom, to_rad, compose)
        posed.append((row, geom, pivot, rotation, center))
        source_indexes.append(int(row[0]))
    if not posed:
        return None

    snap_points = []
    snap_owners = []
    for index, (_row, geom, pivot, rotation, _center) in enumerate(posed):
        local = np.asarray(geom.get("snap_points") or [], dtype=float)
        if not len(local):
            continue
        world = local @ rotation.T + pivot
        snap_points.append(world)
        snap_owners.extend([index] * len(world))

    structural = UnionFind(len(posed))
    roof = UnionFind(len(posed))
    roof_indexes = {index for index, item in enumerate(posed)
                    if item[1].get("family") == "roof"}
    exact_piece_pairs = set()
    near_roof_pairs = set()
    if snap_points:
        points = np.vstack(snap_points)
        owners = np.asarray(snap_owners, dtype=int)
        for left, right in spatial_pairs(points, epsilon):
            a, b = int(owners[left]), int(owners[right])
            if a == b:
                continue
            pair = (min(a, b), max(a, b))
            if pair in exact_piece_pairs:
                continue
            exact_piece_pairs.add(pair)
            structural.union(a, b)
            if a in roof_indexes and b in roof_indexes:
                roof.union(a, b)
        if orphan_distance > epsilon:
            for left, right in spatial_pairs(points, orphan_distance):
                a, b = int(owners[left]), int(owners[right])
                if a == b or a not in roof_indexes or b not in roof_indexes:
                    continue
                pair = (min(a, b), max(a, b))
                if pair not in exact_piece_pairs:
                    near_roof_pairs.add(pair)

    roof_groups = defaultdict(list)
    for index in roof_indexes:
        roof_groups[roof.find(index)].append(index)
    structural_groups = defaultdict(list)
    for index in range(len(posed)):
        structural_groups[structural.find(index)].append(index)
    structure_id_by_root = {
        root: min(source_indexes[index] for index in indexes)
        for root, indexes in structural_groups.items()
    }

    # A single displaced roof piece may miss an exact snap on terrain.  Absorb it
    # only when its near-snap evidence names exactly one established assembly.
    group_for = {index: root for root, indexes in roof_groups.items() for index in indexes}
    singleton_targets = defaultdict(set)
    for left, right in near_roof_pairs:
        lroot, rroot = group_for[left], group_for[right]
        if lroot == rroot:
            continue
        if len(roof_groups[lroot]) == 1 and len(roof_groups[rroot]) > 1:
            singleton_targets[lroot].add(rroot)
        if len(roof_groups[rroot]) == 1 and len(roof_groups[lroot]) > 1:
            singleton_targets[rroot].add(lroot)
    absorbed = {}
    for singleton, targets in singleton_targets.items():
        if len(targets) == 1:
            target = next(iter(targets))
            roof_groups[target].extend(roof_groups[singleton])
            absorbed[singleton] = target
    for singleton in absorbed:
        del roof_groups[singleton]

    assemblies = []
    for indexes in roof_groups.values():
        indexes = sorted(indexes, key=lambda index: source_indexes[index])
        votes = []
        estimated_area = 0.0
        for index in indexes:
            _row, geom, _pivot, rotation, _center = posed[index]
            extents = sorted(float(value) for value in geom.get("extents") or [1, 1, 1])
            estimated_area += extents[-1] * extents[-2]
            plane = planar_snap_normal(geom, rotation)
            if not plane:
                continue
            normal, area, planarity = plane
            tilt = math.degrees(math.acos(max(-1.0, min(1.0, float(normal[1])))))
            bearing = (math.degrees(math.atan2(float(normal[0]), float(normal[2])))
                       % 360.0)
            votes.append({"area": area, "tilt_deg": tilt,
                          "bearing_deg": bearing, "planarity": planarity})
            votes[-1]["prefab"] = str(_row[1])

        classified = classify_roof_votes(
            votes, estimated_area, len(indexes),
            [str(posed[index][0][1]) for index in indexes])
        structure_roots = Counter(structural.find(index) for index in indexes)
        structure_root = structure_roots.most_common(1)[0][0]
        structural_members = structural_groups[structure_root]
        assembly = {
            "roof_id": min(source_indexes[index] for index in indexes),
            "structure_id": structure_id_by_root[structure_root],
            "piece_count": len(indexes),
            "panel_area_m2": round(estimated_area, 2),
            "bounds": _bounds(posed, indexes),
            **classified,
        }
        assemblies.append(assembly)

    assemblies.sort(key=lambda item: (-item["panel_area_m2"], item["roof_id"]))
    total_area = sum(item["panel_area_m2"] for item in assemblies)
    for item in assemblies:
        item["area_fraction"] = round(item["panel_area_m2"] / total_area, 3) \
            if total_area else 0.0
        item["fragment"] = item["piece_count"] < 8 and item["area_fraction"] < 0.05

    structures = defaultdict(list)
    for item in assemblies:
        structures[item["structure_id"]].append(item)
    structure_rows = []
    for structure_id, roof_rows in structures.items():
        root = next(root for root, stable_id in structure_id_by_root.items()
                    if stable_id == structure_id)
        member_indexes = structural_groups[root]
        structure_rows.append({
            "component_id": structure_id,
            "snap_piece_count": len(member_indexes),
            "bounds": _bounds(posed, member_indexes),
            "roof_assemblies": roof_rows,
        })
    structure_rows.sort(key=lambda item: (-sum(r["panel_area_m2"]
                                               for r in item["roof_assemblies"]),
                                           item["component_id"]))

    candidates = [item for item in assemblies if not item["fragment"]]
    dominant = candidates[0] if candidates else (assemblies[0] if assemblies else None)
    roof_summary = None
    if dominant:
        roof_summary = {
            key: dominant[key] for key in (
                "roof_id", "structure_id", "piece_count", "panel_area_m2",
                "shape_estimate", "ridge_bearing_deg", "slope_bearings_deg",
                "ridge_bearings_deg", "confidence", "uncertainty_codes")
        }
        roof_summary["source"] = "dominant_component_roof_assembly"

    return {
        "schema": SCHEMA,
        "model_version": MODEL_VERSION,
        "semantic_status": "experimental",
        "cluster_id": int(cluster_id),
        "pieces": len(rows),
        "posed_pieces": len(posed),
        "snap_edges": len(exact_piece_pairs),
        "absorbed_singleton_roofs": len(absorbed),
        "structures": structure_rows,
        "dominant_structure_id": dominant["structure_id"] if dominant else None,
        "roof": roof_summary,
        "uncertainties": [
            "component connectivity uses verified 5 cm snaps; non-snap decoration remains separate",
            "panel area is derived from snap planes and oriented-box extents, not render meshes",
        ],
    }


def main():
    args = parse_args()
    if args.source_revision and (len(args.source_revision) != 40 or
                                 any(ch not in "0123456789abcdefABCDEF"
                                     for ch in args.source_revision)):
        sys.exit("--source-revision must be a 40-character commit id")
    for path, label in ((args.parquet, "geometry parquet"),
                        (args.cluster_points, "cluster point parquet"),
                        (args.geometry, "piece geometry"),
                        (args.clusters, "clusters"),
                        (args.verify, "rotation verification")):
        if not os.path.isfile(path):
            sys.exit(f"{label} not found: {path}")

    with open(args.verify, encoding="utf-8") as stream:
        verify = json.load(stream)
    if verify.get("verdict") != "PASS":
        sys.exit(f"rotation verification is {verify.get('verdict')!r}; refusing")
    winner = verify["winner"]
    to_rad, compose = HYPOTHESES[winner]

    with open(args.clusters, encoding="utf-8") as stream:
        cluster_doc = json.load(stream)
    clusters = cluster_doc["clusters"]
    targets = [int(value) for value in args.cluster_ids.split(",") if value.strip()]
    known = {int(item["cluster_id"]) for item in clusters}
    missing = sorted(set(targets) - known)
    if missing:
        sys.exit(f"unknown frozen cluster id(s): {', '.join(map(str, missing))}")

    geom_by_name = load_geometry(args.geometry)
    connection = duckdb.connect()
    try:
        members = load_exact_members(connection, args.parquet, args.cluster_points,
                                     cluster_doc, targets)
    except ValueError as exc:
        connection.close()
        sys.exit(str(exc))
    connection.close()
    os.makedirs(args.out, exist_ok=True)

    manifest = {
        "schema": "selfie-stick-roof-semantics-manifest/v1",
        "model_version": MODEL_VERSION,
        "semantic_status": "experimental",
        "snapshot_id": cluster_doc.get("snapshot_id"),
        "world_id": cluster_doc.get("world_id"),
        "decode": winner,
        "source_revision": args.source_revision or None,
        "settings": {"epsilon_m": args.epsilon,
                     "orphan_distance_m": args.orphan_distance},
        "inputs": {
            "building_geometry": {"bytes": os.path.getsize(args.parquet),
                                  "sha256": sha256_file(args.parquet)},
            "cluster_points": {"bytes": os.path.getsize(args.cluster_points),
                               "sha256": sha256_file(args.cluster_points)},
            "piece_geometry": {"bytes": os.path.getsize(args.geometry),
                               "sha256": sha256_file(args.geometry)},
            "rotation_verify": {"bytes": os.path.getsize(args.verify),
                                "sha256": sha256_file(args.verify)},
            "clusters": {"bytes": os.path.getsize(args.clusters),
                         "sha256": sha256_file(args.clusters)},
            "roof_semantics_script": {"bytes": os.path.getsize(__file__),
                                      "sha256": sha256_file(__file__)},
        },
        "clusters": {},
    }

    for cluster_id in targets:
        result = derive_cluster_roofs(cluster_id, members[cluster_id], geom_by_name,
                                      to_rad, compose, args.epsilon,
                                      args.orphan_distance)
        if not result:
            print(f"cluster {cluster_id}: no posed members; skipped")
            continue
        result["snapshot_id"] = cluster_doc.get("snapshot_id")
        result["world_id"] = cluster_doc.get("world_id")
        path = os.path.join(args.out, f"{cluster_id}.architecture-v2.json")
        with open(path + ".tmp", "w", encoding="utf-8") as stream:
            json.dump(result, stream, indent=1, ensure_ascii=False)
        os.replace(path + ".tmp", path)
        roof = result.get("roof") or {}
        manifest["clusters"][str(cluster_id)] = {
            "file": os.path.basename(path),
            "bytes": os.path.getsize(path),
            "sha256": sha256_file(path),
            "structures": len(result["structures"]),
            "roof_assemblies": sum(len(item["roof_assemblies"])
                                   for item in result["structures"]),
            "dominant_shape": roof.get("shape_estimate"),
            "dominant_ridge_bearing_deg": roof.get("ridge_bearing_deg"),
            "confidence": roof.get("confidence"),
        }
        print(f"cluster {cluster_id}: {manifest['clusters'][str(cluster_id)]['roof_assemblies']} "
              f"roof assemblies; dominant {roof.get('shape_estimate')} "
              f"confidence={roof.get('confidence')}", flush=True)

    manifest_path = os.path.join(args.out, "roof-semantics-manifest.json")
    with open(manifest_path + ".tmp", "w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=1, ensure_ascii=False)
    os.replace(manifest_path + ".tmp", manifest_path)
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()

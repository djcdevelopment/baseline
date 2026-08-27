#!/usr/bin/env python3
"""Reconstruct a cluster as a CAD-style massing model from ZDOs alone.

Per pilot cluster this emits three artifacts into out/era17/arch/:

  <id>.glb        oriented-box model — one box per piece (extents + pivot offset from
                  piece-geometry.json, pose from the rotation parquet under the decode
                  hypothesis rotation-verify.json proved), one mesh per family,
                  family-coloured. Native Valheim coords are left-handed; the GLB bake
                  mirrors x and flips winding so the model reads correctly in RH viewers.
  <id>.graph.json snap connectivity — edges where two pieces' snap points coincide
                  within epsilon, plus orphans and a near-miss histogram (near-misses
                  are terrain-conforming placement, not decode error).
  <id>.arch.json  derived architecture: storey levels from the floor-piece y-histogram,
                  footprint polygon, roof ridge estimate, door/window positions with
                  facing normals and an exterior-side vote, room hints per storey.

Cluster identity is FROZEN (clusters.json is the gallery join key). Membership here is
padded-bbox containment with nearest-centre tie-break against overlapping boxes — the
same discipline scan_features.py uses. Never re-cluster, never renumber.

Usage:
  python reconstruct_cluster.py [--cluster-ids 714,578] [--pad 8]
      [--parquet PATH] [--geometry PATH] [--clusters PATH] [--verify PATH] [--out DIR]
  (default cluster ids: the pilots recorded in rotation-verify.json)
"""
import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict

import duckdb
import numpy as np
from scipy.spatial import cKDTree

from verify_rotation import HYPOTHESES, sig_angle

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.join(HERE, "out", "era17", "arch")
DEFAULT_PARQUET = r"E:\omen\steward-era17-arch\building-geometry.parquet"

FAMILY_COLORS = {
    "wall":      (158, 158, 158, 255),
    "roof":      (192,  57,  43, 255),
    "floor":     (121,  85,  61, 255),
    "door":      ( 39, 174,  96, 255),
    "gate":      ( 22, 160, 133, 255),
    "window":    ( 41, 182, 246, 255),
    "stair":     (230, 126,  34, 255),
    "beam":      (109,  76,  65, 255),
    "pole":      (141, 110,  99, 255),
    "fence":     (161, 136, 127, 255),
    "light":     (241, 196,  15, 255),
    "seat":      (155,  89, 182, 255),
    "table":     (142,  68, 173, 255),
    "bed":       (186, 104, 200, 255),
    "container": (175, 122, 197, 255),
    "portal":    (  0, 229, 255, 255),
    "sign":      (255, 241, 118, 255),
    "item_stand":(206, 147, 216, 255),
    "ballista":  (255, 138, 101, 255),
    "misc":      (207, 216, 220, 255),
}

# Faces of a unit box (indices into the 8-corner array), CCW as seen from outside
# in a right-handed frame; the LH bake reverses them.
BOX_CORNERS = np.array([[sx, sy, sz] for sx in (-0.5, 0.5)
                        for sy in (-0.5, 0.5) for sz in (-0.5, 0.5)])
BOX_FACES = np.array([
    [0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5],
    [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6],
    [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3],
])


def euler_matrix(rot_xv, rot_yv, rot_zv, to_rad, compose):
    ax = np.asarray([rot_xv * to_rad]); ay = np.asarray([rot_yv * to_rad])
    az = np.asarray([rot_zv * to_rad])
    return compose(ax, ay, az)[0]


def load_geometry(path):
    with open(path, encoding="utf-8") as fh:
        g = json.load(fh)
    return {e["name"]: e for e in g["pieces"]}


def assign_members(con, parquet, clusters, targets, pad):
    """Padded-bbox membership with nearest-centre tie-break against every overlapping
    frozen bbox (not only the targets), so a padded box cannot steal a neighbour's edge."""
    by_id = {c["cluster_id"]: c for c in clusters}
    members = {}
    for cid in targets:
        c = by_id[cid]
        rows = con.execute(f"""
            SELECT zdo_index, prefab_name, category, x, y, z,
                   has_rot, rot_x, rot_y, rot_z, creator_id
            FROM read_parquet('{parquet}')
            WHERE x BETWEEN ? AND ? AND z BETWEEN ? AND ? AND y BETWEEN ? AND ?
              AND prefab_name IS NOT NULL
            """, [c["min_x"] - pad, c["max_x"] + pad,
                  c["min_z"] - pad, c["max_z"] + pad,
                  c["min_y"] - pad, c["max_y"] + pad]).fetchall()
        overlapping = [o for o in clusters if not (
            o["max_x"] + pad < c["min_x"] - pad or o["min_x"] - pad > c["max_x"] + pad or
            o["max_z"] + pad < c["min_z"] - pad or o["min_z"] - pad > c["max_z"] + pad or
            o["max_y"] + pad < c["min_y"] - pad or o["min_y"] - pad > c["max_y"] + pad)]
        kept = []
        for r in rows:
            x, y, z = r[3], r[4], r[5]
            best, best_d = None, None
            for o in overlapping:
                if (o["min_x"] - pad <= x <= o["max_x"] + pad and
                        o["min_z"] - pad <= z <= o["max_z"] + pad and
                        o["min_y"] - pad <= y <= o["max_y"] + pad):
                    d = ((x - o["center_x"]) ** 2 + (y - o["center_y"]) ** 2
                         + (z - o["center_z"]) ** 2)
                    if best_d is None or d < best_d:
                        best, best_d = o["cluster_id"], d
            if best == cid:
                kept.append(r)
        members[cid] = kept
        print(f"  cluster {cid}: {len(rows)} in padded box, {len(kept)} assigned",
              flush=True)
    return members


def piece_pose(row, geom, to_rad, compose):
    name, x, y, z = row[1], row[3], row[4], row[5]
    has_rot, rx_v, ry_v, rz_v = row[6], row[7], row[8], row[9]
    rot = (euler_matrix(rx_v, ry_v, rz_v, to_rad, compose)
           if has_rot else np.eye(3))
    pivot = np.array([x, y, z])
    center = pivot + rot @ np.asarray(geom["center_offset"])
    return pivot, rot, center


def build_glb(members_rows, geom_by_name, to_rad, compose, out_path):
    import trimesh
    fam_verts, fam_faces = defaultdict(list), defaultdict(list)
    for row in members_rows:
        geom = geom_by_name.get(row[1])
        if not geom:
            continue
        pivot, rot, center = piece_pose(row, geom, to_rad, compose)
        ext = np.asarray(geom["extents"])
        corners = (BOX_CORNERS * ext) @ rot.T + center
        fam = geom["family"]
        base = len(fam_verts[fam]) * 8
        fam_verts[fam].append(corners)
        fam_faces[fam].append(BOX_FACES + base)
    scene = trimesh.Scene()
    for fam in sorted(fam_verts):
        verts = np.vstack(fam_verts[fam])
        faces = np.vstack(fam_faces[fam])
        # LH (Valheim) -> RH (glTF): mirror x, flip winding.
        verts = verts.copy(); verts[:, 0] *= -1.0
        faces = faces[:, ::-1]
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        mesh.visual.face_colors = np.tile(
            np.asarray(FAMILY_COLORS.get(fam, FAMILY_COLORS["misc"]), dtype=np.uint8),
            (len(faces), 1))
        scene.add_geometry(mesh, node_name=fam, geom_name=fam)
    scene.export(out_path)
    return sum(len(v) for v in fam_verts.values())


def build_graph(members_rows, geom_by_name, to_rad, compose, epsilon, out_path):
    pts, owners = [], []
    nodes = []
    for i, row in enumerate(members_rows):
        geom = geom_by_name.get(row[1])
        nodes.append({"zdo_index": row[0], "prefab": row[1],
                      "family": geom["family"] if geom else "misc",
                      "pos": [round(row[3], 3), round(row[4], 3), round(row[5], 3)],
                      "rot": [round(row[7], 2), round(row[8], 2), round(row[9], 2)]
                             if row[6] else None})
        if not geom or not geom["snap_points"]:
            continue
        pivot, rot, _ = piece_pose(row, geom, to_rad, compose)
        world = np.asarray(geom["snap_points"]) @ rot.T + pivot
        pts.append(world)
        owners.extend([i] * len(world))
    edges, orphan_pieces, near_hist = [], [], Counter()
    if pts:
        pts = np.vstack(pts); owners = np.asarray(owners)
        tree = cKDTree(pts)
        pairs = tree.query_pairs(epsilon, output_type="ndarray")
        seen = set()
        for a, b in pairs:
            pa, pb = int(owners[a]), int(owners[b])
            if pa == pb:
                continue
            key = (min(pa, pb), max(pa, pb))
            if key in seen:
                continue
            seen.add(key)
            d = float(np.linalg.norm(pts[a] - pts[b]))
            edges.append({"a": pa, "b": pb, "dist_m": round(d, 4)})
        connected = {e["a"] for e in edges} | {e["b"] for e in edges}
        snap_piece_ids = set(int(o) for o in owners)
        orphan_pieces = sorted(snap_piece_ids - connected)
        near_pairs = tree.query_pairs(0.20, output_type="ndarray")
        for a, b in near_pairs:
            if owners[a] == owners[b]:
                continue
            d = float(np.linalg.norm(pts[a] - pts[b]))
            if d >= epsilon:
                near_hist[f"{int(d * 100) // 5 * 5}-{int(d * 100) // 5 * 5 + 5}cm"] += 1
    out = {"nodes": nodes, "edges": edges,
           "stats": {"pieces": len(nodes), "snap_pieces": len(set(owners.tolist())) if len(edges) or len(orphan_pieces) else 0,
                     "edges": len(edges), "orphan_snap_pieces": len(orphan_pieces),
                     "near_miss_histogram_cm": dict(sorted(near_hist.items()))}}
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    return out["stats"]


def facing_normal(rot):
    """Walls/doors/windows are thin on local z; the facade normal is rotated +z."""
    n = rot @ np.array([0.0, 0.0, 1.0])
    n[1] = 0.0
    norm = np.linalg.norm(n)
    return n / norm if norm > 1e-6 else np.array([0.0, 0.0, 1.0])


def derive_architecture(cid, members_rows, geom_by_name, to_rad, compose, out_path):
    from shapely.geometry import MultiPoint, Polygon
    from shapely.ops import unary_union

    posed = []
    for row in members_rows:
        geom = geom_by_name.get(row[1])
        if not geom:
            continue
        pivot, rot, center = piece_pose(row, geom, to_rad, compose)
        posed.append((row, geom, pivot, rot, center))

    # ---- storeys: y-histogram of floor pivots, peaks >= 2 m apart ----
    floor_y = np.array([p[2][1] for p in posed if p[1]["family"] == "floor"])
    storeys = []
    if floor_y.size:
        lo, hi = floor_y.min(), floor_y.max()
        bins = np.arange(lo - 0.125, hi + 0.375, 0.25)
        hist, edges_ = np.histogram(floor_y, bins=bins)
        order = np.argsort(hist)[::-1]
        min_mass = max(3, int(0.02 * floor_y.size))
        for bi in order:
            if hist[bi] < min_mass:
                break
            level = float((edges_[bi] + edges_[bi + 1]) / 2)
            if all(abs(level - s["y"]) >= 2.0 for s in storeys):
                storeys.append({"y": round(level, 2), "floor_pieces": int(hist[bi])})
        storeys.sort(key=lambda s: s["y"])

    # ---- footprint: union of structural pieces' xz rectangles ----
    polys = []
    for row, geom, pivot, rot, center in posed:
        if geom["family"] not in ("wall", "floor", "roof", "door", "gate", "window",
                                  "stair", "misc"):
            continue
        ext = np.asarray(geom["extents"])
        corners = (BOX_CORNERS * ext) @ rot.T + center
        hull = MultiPoint(corners[:, [0, 2]]).convex_hull.buffer(0.25)
        if hull.is_valid and hull.area > 0:
            polys.append(hull)
    footprint = None
    if polys:
        u = unary_union(polys).simplify(0.5)
        biggest = max(u.geoms, key=lambda g: g.area) if u.geom_type == "MultiPolygon" else u
        footprint = {
            "area_m2": round(u.area, 1),
            "main_polygon_area_m2": round(biggest.area, 1),
            "main_polygon_xz": [[round(x, 2), round(z, 2)]
                                for x, z in biggest.exterior.coords],
            "disjoint_parts": len(u.geoms) if u.geom_type == "MultiPolygon" else 1,
        }

    # ---- roof: pitch classes by name, ridge from the yaw mode (mod 180) ----
    roof_rows = [p for p in posed if p[1]["family"] == "roof"]
    roof = None
    if roof_rows:
        pitches = Counter()
        for row, geom, *_ in roof_rows:
            low = row[1].lower()
            if "45" in low:
                pitches["45deg"] += 1
            elif "26" in low:
                pitches["26deg"] += 1
            elif "top" in low or "ridge" in low:
                pitches["ridge_cap"] += 1
            else:
                pitches["other"] += 1
        yaws = Counter(round(p[0][8] % 180.0 / 22.5) * 22.5 % 180.0
                       for p in roof_rows if p[0][6])
        slope_mode = yaws.most_common(1)[0][0] if yaws else None
        distinct_dirs = len([1 for _, n in yaws.items() if n >= max(3, 0.1 * len(roof_rows))])
        shape = ("flat" if not yaws else
                 "gable" if distinct_dirs <= 2 else
                 "hip" if distinct_dirs <= 4 else "complex")
        roof = {"pieces": len(roof_rows), "pitch_classes": dict(pitches),
                "slope_yaw_mode_deg": slope_mode,
                "ridge_bearing_deg": (round((slope_mode + 90) % 180, 1)
                                      if slope_mode is not None else None),
                "shape_estimate": shape}

    # ---- doors / gates / windows: position + facing + exterior vote ----
    all_centers = np.array([p[4] for p in posed]) if posed else np.zeros((0, 3))
    openings = []
    for row, geom, pivot, rot, center in posed:
        fam = geom["family"]
        if fam not in ("door", "gate", "window"):
            continue
        n = facing_normal(rot)
        rel = all_centers - center
        along = rel @ n
        near = (np.abs(along) <= 3.0) & (np.linalg.norm(rel, axis=1) <= 6.0)
        pos_side = int(((along > 0.3) & near).sum())
        neg_side = int(((along < -0.3) & near).sum())
        outward = n if pos_side <= neg_side else -n
        openings.append({
            "kind": fam, "prefab": row[1],
            "pos": [round(float(v), 2) for v in center],
            "facing_deg": round(math.degrees(math.atan2(float(outward[0]),
                                                        float(outward[2]))) % 360, 1),
            "outward_normal_xz": [round(float(outward[0]), 3),
                                  round(float(outward[2]), 3)],
            "is_exterior_vote": {"toward": min(pos_side, neg_side),
                                 "away": max(pos_side, neg_side)},
        })

    # ---- room hints per storey: wall occupancy grid, free-cell components ----
    rooms = []
    if storeys and footprint:
        from shapely.geometry import Point
        biggest_poly = Polygon(footprint["main_polygon_xz"])
        minx, minz, maxx, maxz = (biggest_poly.bounds[0], biggest_poly.bounds[1],
                                  biggest_poly.bounds[2], biggest_poly.bounds[3])
        step = 0.5
        for s in storeys:
            walls = [p for p in posed if p[1]["family"] in ("wall", "door", "gate", "window")
                     and s["y"] - 0.5 <= p[4][1] <= s["y"] + 2.5]
            if not walls:
                continue
            nx = max(1, int((maxx - minx) / step)); nz = max(1, int((maxz - minz) / step))
            if nx * nz > 400_000:
                continue
            occ = np.zeros((nx, nz), dtype=bool)
            for row, geom, pivot, rot, center in walls:
                ext = np.asarray(geom["extents"])
                corners = (BOX_CORNERS * ext) @ rot.T + center
                gx = np.clip(((corners[:, 0] - minx) / step).astype(int), 0, nx - 1)
                gz = np.clip(((corners[:, 2] - minz) / step).astype(int), 0, nz - 1)
                occ[gx.min():gx.max() + 1, gz.min():gz.max() + 1] |= True
            from scipy.ndimage import label
            free = ~occ
            lab, nlab = label(free)
            comps = []
            for li in range(1, nlab + 1):
                cells = np.argwhere(lab == li)
                area = len(cells) * step * step
                if area < 4.0:
                    continue
                cx = minx + (cells[:, 0].mean() + 0.5) * step
                cz = minz + (cells[:, 1].mean() + 0.5) * step
                if not biggest_poly.contains(Point(cx, cz)):
                    continue
                comps.append({"center_xz": [round(cx, 2), round(cz, 2)],
                              "area_m2": round(area, 1)})
            comps.sort(key=lambda r: -r["area_m2"])
            rooms.append({"storey_y": s["y"], "candidates": comps[:8]})

    creators = Counter(r[10] for r in members_rows if r[10])
    out = {
        "cluster_id": cid,
        "pieces": len(members_rows),
        "families": dict(Counter(geom_by_name[r[1]]["family"]
                                 for r in members_rows if r[1] in geom_by_name)),
        "top_creator": creators.most_common(1)[0][0] if creators else None,
        "storeys": storeys,
        "storey_count": len(storeys),
        "footprint": footprint,
        "roof": roof,
        "openings": openings,
        "room_hints": rooms,
        "caveats": ["room_hints and roof.shape_estimate are heuristics pending L3",
                    "storeys counted from floor-family pivots only"],
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cluster-ids", default="")
    p.add_argument("--pad", type=float, default=8.0)
    p.add_argument("--epsilon", type=float, default=0.05)
    p.add_argument("--parquet", default=DEFAULT_PARQUET)
    p.add_argument("--geometry", default=os.path.join(ARCH, "piece-geometry.json"))
    p.add_argument("--clusters", default=os.path.join(HERE, "out", "era17", "clusters.json"))
    p.add_argument("--verify", default=os.path.join(ARCH, "rotation-verify.json"))
    p.add_argument("--out", default=ARCH)
    args = p.parse_args()

    with open(args.verify, encoding="utf-8") as fh:
        verify = json.load(fh)
    if verify.get("verdict") != "PASS":
        sys.exit(f"rotation-verify verdict is {verify.get('verdict')!r}; refusing to "
                 "reconstruct on an unproven decode")
    winner = verify["winner"]
    to_rad, compose = HYPOTHESES[winner]
    print(f"decode: {winner} (verified {verify['means'].get(winner)})", flush=True)

    geom_by_name = load_geometry(args.geometry)
    with open(args.clusters, encoding="utf-8") as fh:
        clusters = json.load(fh)["clusters"]
    targets = ([int(s) for s in args.cluster_ids.split(",") if s.strip()]
               if args.cluster_ids else verify["pilot_cluster_ids"])
    print(f"targets: {targets}", flush=True)

    parquet = args.parquet.replace("'", "''").replace("\\", "/")
    con = duckdb.connect()
    members = assign_members(con, parquet, clusters, targets, args.pad)

    os.makedirs(args.out, exist_ok=True)
    manifest_path = os.path.join(args.out, "arch-manifest.json")
    manifest = {"decode": winner, "clusters": {}}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)

    for cid in targets:
        rows = members[cid]
        if not rows:
            print(f"  cluster {cid}: no members, skipped")
            continue
        glb = os.path.join(args.out, f"{cid}.glb")
        n = build_glb(rows, geom_by_name, to_rad, compose, glb)
        gstats = build_graph(rows, geom_by_name, to_rad, compose, args.epsilon,
                             os.path.join(args.out, f"{cid}.graph.json"))
        arch = derive_architecture(cid, rows, geom_by_name, to_rad, compose,
                                   os.path.join(args.out, f"{cid}.arch.json"))
        c = next(x for x in clusters if x["cluster_id"] == cid)
        manifest["clusters"][str(cid)] = {
            "glb": f"{cid}.glb", "graph": f"{cid}.graph.json",
            "arch": f"{cid}.arch.json", "pieces": len(rows),
            "center": [c["center_x"], c["center_y"], c["center_z"]],
            "storeys": arch["storey_count"],
            "openings": len(arch["openings"]),
            "graph_edges": gstats["edges"],
        }
        print(f"  cluster {cid}: {n} boxes -> {os.path.basename(glb)}; "
              f"graph {gstats['edges']} edges ({gstats['orphan_snap_pieces']} orphans); "
              f"storeys {arch['storey_count']}, openings {len(arch['openings'])}, "
              f"roof {arch['roof']['shape_estimate'] if arch['roof'] else 'none'}",
              flush=True)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()

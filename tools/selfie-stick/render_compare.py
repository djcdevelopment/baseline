#!/usr/bin/env python3
"""L2 of the architecture experiment: render the reconstructed model from the exact
camera pose that took each gallery frame, and score the agreement.

The renderer is a numpy z-buffer box rasterizer — no GL context, no LH/RH conversion
trap: everything stays in native Valheim coordinates (LH, y-up, yaw clockwise from +Z,
pitch positive-down, FOV_V 65 deg), which is exactly the space the game camera shot in.

Metrics per frame (both restricted to the HUD-cropped region depth_layers.py uses):

  depth_ordering   sample pixel pairs inside the rendered silhouette with rendered
                   depth gap > 1 m; agreement = share where Depth Anything orders the
                   pair the same way. DA is affine-invariant, so ORDERING is the only
                   honest comparison. Primary metric, target >= 0.80.
  silhouette_iou   rendered mask vs a photo-foreground mask (DA normalized depth).
                   Boxes-not-meshes, so >= 0.5 on exterior orbits is the bar.

Camera y handling: the capture rig may or may not add a lens offset to the planned
position, so every frame is scored at y+0 AND y+lens_offset_m and both are reported —
the summary says which convention the rig actually used. Measure, don't assume.

Usage (steward-arch venv):
  python render_compare.py --cluster-ids 1775,916,1820 [--source orbit]
Prereq: dump_depth.py (omen-perception venv) for the same frames.
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

import duckdb
import numpy as np

from verify_rotation import HYPOTHESES
from reconstruct_cluster import (ARCH, BOX_CORNERS, BOX_FACES, DEFAULT_PARQUET,
                                 assign_members, load_geometry, piece_pose)

HERE = os.path.dirname(os.path.abspath(__file__))
FOV_V_DEG = 65.0
CROP_FRAC = (0.0, 40 / 900, 1550 / 1600, 1.0)   # depth_layers.py's HUD crop
NEAR = 0.1


def load_shotplans(era_dir):
    """Every TSV row the mod could have executed, keyed by cluster id."""
    rows = defaultdict(list)
    for fname in sorted(os.listdir(era_dir)):
        if not fname.endswith(".tsv"):
            continue
        with open(os.path.join(era_dir, fname), encoding="utf-8") as fh:
            for ln in fh:
                if ln.startswith("#"):
                    continue
                parts = ln.rstrip("\n").split("\t")
                if len(parts) < 12:
                    continue
                try:
                    cid = int(parts[0])
                    cam = [float(parts[2]), float(parts[3]), float(parts[4])]
                    yaw, pitch = float(parts[5]), float(parts[6])
                except ValueError:
                    continue
                rows[cid].append({"shot": parts[1], "cam": cam, "yaw": yaw,
                                  "pitch": pitch, "plan": fname})
    return rows


def match_pose(frame, plans):
    """Nearest planned camera within 2 m wins; shot-name match is the fallback."""
    cands = plans.get(frame["cluster_id"], [])
    fx, fy, fz = frame["x"], frame["y"], frame["z"]
    best, best_d = None, 4.0
    for r in cands:
        d = math.dist((fx, fy, fz), r["cam"])
        if d < best_d:
            best, best_d = r, d
    if best:
        return best, round(best_d, 2)
    variant = frame["id"].split("_", 2)[-1]
    for r in cands:
        if r["shot"] == variant:
            return r, None
    return None, None


def camera_basis(yaw_deg, pitch_deg):
    y, p = math.radians(yaw_deg), math.radians(pitch_deg)
    f = np.array([math.cos(p) * math.sin(y), -math.sin(p), math.cos(p) * math.cos(y)])
    r = np.array([math.cos(y), 0.0, -math.sin(y)])
    u = np.array([math.sin(y) * math.sin(p), math.cos(p), math.cos(y) * math.sin(p)])
    return f, r, u


def render_depth(boxes, cam, yaw, pitch, w, h):
    """boxes: list of (8,3) world corner arrays. Returns depth buffer (inf = empty)."""
    f, r, u = camera_basis(yaw, pitch)
    tan_v = math.tan(math.radians(FOV_V_DEG / 2))
    tan_h = tan_v * (w / h)
    depth_buf = np.full((h, w), np.inf, dtype=np.float32)

    for corners in boxes:
        d = corners - cam
        z = d @ f
        if z.max() < NEAR:
            continue
        x_ndc = (d @ r) / (np.maximum(z, NEAR) * tan_h)
        y_ndc = (d @ u) / (np.maximum(z, NEAR) * tan_v)
        px = (1.0 + x_ndc) * 0.5 * w
        py = (1.0 - y_ndc) * 0.5 * h
        if px.max() < 0 or px.min() >= w or py.max() < 0 or py.min() >= h:
            continue
        for tri in BOX_FACES:
            tz = z[tri]
            if tz.min() < NEAR:      # crossing the near plane — drop, exteriors don't care
                continue
            tx, ty = px[tri], py[tri]
            x0 = max(int(np.floor(tx.min())), 0); x1 = min(int(np.ceil(tx.max())) + 1, w)
            y0 = max(int(np.floor(ty.min())), 0); y1 = min(int(np.ceil(ty.max())) + 1, h)
            if x0 >= x1 or y0 >= y1:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            d00 = (tx[1] - tx[0]) * (gy - ty[0]) - (ty[1] - ty[0]) * (gx - tx[0])
            d11 = (tx[2] - tx[1]) * (gy - ty[1]) - (ty[2] - ty[1]) * (gx - tx[1])
            d22 = (tx[0] - tx[2]) * (gy - ty[2]) - (ty[0] - ty[2]) * (gx - tx[2])
            inside = ((d00 >= 0) & (d11 >= 0) & (d22 >= 0)) | \
                     ((d00 <= 0) & (d11 <= 0) & (d22 <= 0))
            if not inside.any():
                continue
            area = (tx[1] - tx[0]) * (ty[2] - ty[0]) - (tx[2] - tx[0]) * (ty[1] - ty[0])
            if abs(area) < 1e-9:
                continue
            l0 = d11 / area; l1 = d22 / area; l2 = d00 / area
            inv_z = l0 / tz[0] + l1 / tz[1] + l2 / tz[2]
            with np.errstate(divide="ignore"):
                z_pix = np.where(inv_z > 0, 1.0 / inv_z, np.inf)
            z_pix = np.where(inside, z_pix, np.inf).astype(np.float32)
            region = depth_buf[y0:y1, x0:x1]
            np.minimum(region, z_pix, out=region)
    return depth_buf


def crop(arr):
    h, w = arr.shape[:2]
    l, t, r, b = CROP_FRAC
    return arr[int(t * h):int(b * h), int(l * w):int(r * w)]


def score_frame(depth_buf, da, rng):
    render = crop(depth_buf)
    photo = crop(da.astype(np.float32))
    mask = np.isfinite(render)
    out = {"render_coverage": round(float(mask.mean()), 4)}

    ys, xs = np.nonzero(mask)
    if len(ys) >= 200:
        i = rng.integers(0, len(ys), 20000)
        j = rng.integers(0, len(ys), 20000)
        ra = render[ys[i], xs[i]]; rb = render[ys[j], xs[j]]
        keep = np.abs(ra - rb) > 1.0
        if keep.sum() >= 500:
            pa = photo[ys[i][keep], xs[i][keep]]; pb = photo[ys[j][keep], xs[j][keep]]
            # render: smaller = closer; DA: larger = closer
            agree = ((ra[keep] < rb[keep]) == (pa > pb))
            out["depth_ordering"] = round(float(agree.mean()), 4)
            out["ordering_pairs"] = int(keep.sum())

    lo, hi = np.percentile(photo, 1), np.percentile(photo, 99)
    if hi - lo > 1e-6:
        n = np.clip((photo - lo) / (hi - lo), 0, 1)
        photo_fg = n >= 0.30
        inter = (mask & photo_fg).sum()
        union = (mask | photo_fg).sum()
        out["silhouette_iou"] = round(float(inter / union), 4) if union else None
    return out, mask


def save_overlay(image_path, mask_cropped, out_path, work_w):
    from PIL import Image
    from scipy.ndimage import binary_erosion
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    img = img.resize((work_w, int(round(h * work_w / w))), Image.BILINEAR)
    arr = np.asarray(crop(np.asarray(img))).copy()
    edge = mask_cropped & ~binary_erosion(mask_cropped, iterations=2)
    arr[edge] = [255, 40, 40]
    Image.fromarray(arr).save(out_path)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cluster-ids", required=True)
    p.add_argument("--source", default="orbit", help="index 'source' filter ('' = all)")
    p.add_argument("--pad", type=float, default=8.0)
    p.add_argument("--parquet", default=DEFAULT_PARQUET)
    p.add_argument("--geometry", default=os.path.join(ARCH, "piece-geometry.json"))
    p.add_argument("--clusters", default=os.path.join(HERE, "out", "era17", "clusters.json"))
    p.add_argument("--verify", default=os.path.join(ARCH, "rotation-verify.json"))
    p.add_argument("--index", default=os.path.join(HERE, "out", "era17", "gallery", "index.json"))
    p.add_argument("--images", default=os.path.join(HERE, "out", "era17", "gallery", "large"))
    p.add_argument("--depth-npy", default=os.path.join(ARCH, "depth-npy"))
    p.add_argument("--era-dir", default=os.path.join(HERE, "out", "era17"))
    p.add_argument("--out", default=os.path.join(ARCH, "experiment"))
    p.add_argument("--emit-ids-only", action="store_true",
                   help="print the frame ids needing depth dumps, then exit")
    args = p.parse_args()

    targets = [int(s) for s in args.cluster_ids.split(",") if s.strip()]
    with open(args.index, encoding="utf-8") as fh:
        index = json.load(fh)
    frames = [f for f in index["images"]
              if f.get("cluster_id") in targets
              and (not args.source or f.get("source") == args.source)]
    plans = load_shotplans(args.era_dir)
    posed_frames = []
    for f in frames:
        pose, dist = match_pose(f, plans)
        if pose:
            posed_frames.append((f, pose, dist))
    print(f"{len(frames)} frame(s) for clusters {targets}; {len(posed_frames)} with a pose")
    if args.emit_ids_only:
        for f, _, _ in posed_frames:
            print(f["id"])
        return

    with open(args.verify, encoding="utf-8") as fh:
        verify = json.load(fh)
    if verify.get("verdict") != "PASS":
        sys.exit("rotation decode not PASSed; run verify_rotation.py first")
    to_rad, compose = HYPOTHESES[verify["winner"]]
    geom_by_name = load_geometry(args.geometry)
    with open(args.clusters, encoding="utf-8") as fh:
        clusters = json.load(fh)["clusters"]

    parquet = args.parquet.replace("'", "''").replace("\\", "/")
    con = duckdb.connect()
    members = assign_members(con, parquet, clusters, targets, args.pad)
    boxes_by_cluster = {}
    for cid in targets:
        boxes = []
        for row in members[cid]:
            geom = geom_by_name.get(row[1])
            if not geom:
                continue
            _, rot, center = piece_pose(row, geom, to_rad, compose)
            boxes.append((BOX_CORNERS * np.asarray(geom["extents"])) @ rot.T + center)
        boxes_by_cluster[cid] = boxes

    os.makedirs(args.out, exist_ok=True)
    rng = np.random.default_rng(17)
    results = []
    for f, pose, dist in posed_frames:
        npy = os.path.join(args.depth_npy, f["id"] + ".npy")
        if not os.path.exists(npy):
            print(f"  - {f['id']}: no depth npy (run dump_depth.py), skipped")
            continue
        da = np.load(npy)
        h, w = da.shape
        offsets = {"y0": 0.0}
        if f.get("lens_offset_m"):
            offsets["y_lens"] = float(f["lens_offset_m"])
        entry = {"id": f["id"], "cluster_id": f["cluster_id"],
                 "shot": pose["shot"], "plan": pose["plan"], "pose_match_dist_m": dist,
                 "occluded": bool(f.get("occluded")),
                 "perspective": f.get("perspective"), "scores": {}}
        best_key, best_mask = None, None
        for key, dy in offsets.items():
            cam = np.array([pose["cam"][0], pose["cam"][1] + dy, pose["cam"][2]])
            buf = render_depth(boxes_by_cluster[f["cluster_id"]], cam,
                               pose["yaw"], pose["pitch"], w, h)
            score, mask = score_frame(buf, da, rng)
            entry["scores"][key] = score
            if best_key is None or (score.get("depth_ordering") or 0) > \
                    (entry["scores"][best_key].get("depth_ordering") or 0):
                best_key, best_mask = key, mask
        entry["best"] = best_key
        results.append(entry)
        img_path = os.path.join(args.images, f["id"] + ".webp")
        if best_mask is not None and os.path.exists(img_path):
            save_overlay(img_path, best_mask,
                         os.path.join(args.out, f["id"] + "_overlay.png"), w)
        s = entry["scores"][best_key]
        print(f"  {f['id']} [{best_key}] ordering={s.get('depth_ordering')} "
              f"iou={s.get('silhouette_iou')} cov={s.get('render_coverage')}")

    if results:
        def stats(subset):
            o = [r["scores"][r["best"]].get("depth_ordering") for r in subset]
            o = [v for v in o if v is not None]
            i = [r["scores"][r["best"]].get("silhouette_iou") for r in subset]
            i = [v for v in i if v is not None]
            c = [r["scores"][r["best"]].get("render_coverage") for r in subset]
            return {"frames": len(subset),
                    "mean_depth_ordering": round(float(np.mean(o)), 4) if o else None,
                    "mean_silhouette_iou": round(float(np.mean(i)), 4) if i else None,
                    "mean_render_coverage": round(float(np.mean(c)), 4) if c else None}

        best_votes = defaultdict(int)
        for r in results:
            best_votes[r["best"]] += 1
        # Stratify: an occluded frame and a frame where the model fills 12% of the
        # image are testing different things. The IoU denominator is ALL photo
        # foreground (terrain and trees included), so it is only meaningful where the
        # subject actually fills the frame — hence the coverage split.
        clear = [r for r in results if not r["occluded"]]
        summary = {
            "frames_scored": len(results),
            "all": stats(results),
            "unoccluded": stats(clear),
            "unoccluded_subject_fills_frame_cov_ge_0.30": stats(
                [r for r in clear
                 if (r["scores"][r["best"]].get("render_coverage") or 0) >= 0.30]),
            "unoccluded_distant_cov_lt_0.30": stats(
                [r for r in clear
                 if (r["scores"][r["best"]].get("render_coverage") or 0) < 0.30]),
            "occluded": stats([r for r in results if r["occluded"]]),
            "ordering_target": 0.80, "iou_target": 0.50,
            "camera_y_convention_votes": dict(best_votes),
            "note": ("silhouette_iou compares the model mask against ALL photo "
                     "foreground, so terrain and canopy depress it on distant shots; "
                     "read it only on the cov>=0.30 stratum."),
        }
        print(f"\nsummary: {json.dumps(summary, indent=1)}")
        with open(os.path.join(args.out, "l2-metrics.json"), "w", encoding="utf-8") as fh:
            json.dump({"summary": summary, "frames": results}, fh, indent=1)
        print(f"wrote {os.path.join(args.out, 'l2-metrics.json')}")


if __name__ == "__main__":
    main()

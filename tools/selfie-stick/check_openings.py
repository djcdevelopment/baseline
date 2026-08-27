#!/usr/bin/env python3
"""L3: do the doors the model claims actually appear where it says, in the photographs?

For every photographed frame with a known camera pose, project each door/gate the model
derived (position + outward facing normal) into image space and mark it. A door that
lands inside the frame, at the pixel where the photo shows a door, is a lexicon-grade
fact — it means the planner can aim a camera down a doorway it has never seen.

Two automatic measures, plus annotated images for the human/VLM pass:

  in_frame_rate     of the doors the camera should see (in front, within FOV, facing
                    the camera by its outward normal), how many project inside the
                    image. A miss means either the position or the facing is wrong.
  facing_agreement  a door whose outward normal points back toward the camera should be
                    the one you can see through; one facing away should be a closed
                    face. Reported as the share of visible doors whose normal has
                    negative dot with the view direction.

Writes experiment/l3-openings.json and experiment/<id>_doors.png.

Usage (steward-arch venv):
  python check_openings.py --cluster-ids 182,275,1820,916,1775
"""
import argparse
import json
import math
import os

import numpy as np

from render_compare import (CROP_FRAC, FOV_V_DEG, camera_basis, crop,
                            load_shotplans, match_pose)
from reconstruct_cluster import ARCH

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_W = 960


def project(pt, cam, f, r, u, w, h):
    d = np.asarray(pt) - cam
    z = float(d @ f)
    if z < 0.5:
        return None
    tan_v = math.tan(math.radians(FOV_V_DEG / 2))
    tan_h = tan_v * (w / h)
    px = (1.0 + (d @ r) / (z * tan_h)) * 0.5 * w
    py = (1.0 - (d @ u) / (z * tan_v)) * 0.5 * h
    return float(px), float(py), z


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cluster-ids", required=True)
    p.add_argument("--index", default=os.path.join(HERE, "out", "era17", "gallery", "index.json"))
    p.add_argument("--images", default=os.path.join(HERE, "out", "era17", "gallery", "large"))
    p.add_argument("--era-dir", default=os.path.join(HERE, "out", "era17"))
    p.add_argument("--out", default=os.path.join(ARCH, "experiment"))
    p.add_argument("--max-annotated", type=int, default=14)
    args = p.parse_args()

    from PIL import Image, ImageDraw

    targets = [int(s) for s in args.cluster_ids.split(",") if s.strip()]
    with open(args.index, encoding="utf-8") as fh:
        frames = [f for f in json.load(fh)["images"] if f.get("cluster_id") in targets]
    plans = load_shotplans(args.era_dir)
    arch = {}
    for cid in targets:
        path = os.path.join(ARCH, f"{cid}.arch.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                arch[cid] = json.load(fh)

    os.makedirs(args.out, exist_ok=True)
    rows, annotated = [], 0
    for f in frames:
        pose, dist = match_pose(f, plans)
        if not pose or f["cluster_id"] not in arch:
            continue
        doors = [o for o in arch[f["cluster_id"]]["openings"] if o["kind"] != "window"]
        if not doors:
            continue
        src = os.path.join(args.images, f["id"] + ".webp")
        if not os.path.exists(src):
            continue
        img = Image.open(src).convert("RGB")
        w0, h0 = img.size
        img = img.resize((WORK_W, int(round(h0 * WORK_W / w0))), Image.BILINEAR)
        w, h = img.size
        cam = np.array([pose["cam"][0],
                        pose["cam"][1] + float(f.get("lens_offset_m") or 0.0),
                        pose["cam"][2]])
        fwd, right, up = camera_basis(pose["yaw"], pose["pitch"])

        seen, hits, facing_ok = 0, 0, 0
        draw = ImageDraw.Draw(img)
        for o in doors:
            pos = np.asarray(o["pos"], dtype=float)
            d = pos - cam
            rng = float(np.linalg.norm(d))
            if rng > 90.0 or float(d @ fwd) < 0.5:
                continue
            seen += 1
            pr = project(pos, cam, fwd, right, up, w, h)
            if not pr:
                continue
            px, py, z = pr
            if 0 <= px < w and 0 <= py < h:
                hits += 1
                n = np.array([o["outward_normal_xz"][0], 0.0, o["outward_normal_xz"][1]])
                toward = float(n @ (-d / max(rng, 1e-6)))
                if toward > 0:
                    facing_ok += 1
                col = (0, 230, 118) if toward > 0 else (255, 180, 0)
                rad = max(6.0, 260.0 / max(z, 4.0))
                draw.ellipse([px - rad, py - rad, px + rad, py + rad], outline=col, width=3)
                draw.text((px + rad + 3, py - 7), f"{o['kind']} {o['facing_deg']:.0f}d",
                          fill=col)
        if seen == 0:
            continue
        rows.append({"id": f["id"], "cluster_id": f["cluster_id"], "shot": pose["shot"],
                     "doors_expected": seen, "doors_in_frame": hits,
                     "doors_facing_camera": facing_ok})
        if annotated < args.max_annotated:
            arr = np.asarray(img)
            Image.fromarray(np.asarray(crop(arr))).save(
                os.path.join(args.out, f["id"] + "_doors.png"))
            annotated += 1

    exp = sum(r["doors_expected"] for r in rows)
    hit = sum(r["doors_in_frame"] for r in rows)
    fac = sum(r["doors_facing_camera"] for r in rows)
    summary = {
        "frames": len(rows), "doors_expected_visible": exp, "doors_in_frame": hit,
        "in_frame_rate": round(hit / exp, 4) if exp else None,
        "facing_camera_share_of_in_frame": round(fac / hit, 4) if hit else None,
        "annotated_images": annotated,
    }
    print(json.dumps(summary, indent=1))
    with open(os.path.join(args.out, "l3-openings.json"), "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "frames": rows}, fh, indent=1)
    print(f"wrote {os.path.join(args.out, 'l3-openings.json')}")


if __name__ == "__main__":
    main()

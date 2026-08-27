#!/usr/bin/env python3
"""Dump raw Depth Anything depth maps for named gallery frames, for render_compare.py.

depth_layers.py runs the same model but persists only scalar metrics (and crops the
HUD first). The L2 render-vs-photo experiment needs the per-pixel map, pixel-aligned
to the frame, so this dumper works on the FULL frame and saves float16 .npy at a
fixed working width. render_compare.py applies the HUD crop identically to both
sides at metric time.

Run with the omen-perception venv (torch + transformers):
  C:\\work\\omen-perception\\venv\\Scripts\\python.exe dump_depth.py --ids id1,id2

Depth convention is Depth Anything's: LARGER = CLOSER (relative, affine-invariant).
"""
import argparse
import json
import os
import sys

WORK_W = 960
MODEL = "depth-anything/Depth-Anything-V2-Small-hf"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--images", default=os.path.join(here, "out", "era17", "gallery", "large"))
    p.add_argument("--ids", default="", help="comma-separated image ids (no extension)")
    p.add_argument("--ids-file", default="", help="file with one image id per line")
    p.add_argument("--out", default=os.path.join(here, "out", "era17", "arch", "depth-npy"))
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    ids = [s.strip() for s in args.ids.split(",") if s.strip()]
    if args.ids_file:
        with open(args.ids_file, encoding="utf-8") as fh:
            ids += [ln.strip() for ln in fh if ln.strip()]
    if not ids:
        sys.exit("no ids given")

    import numpy as np
    from PIL import Image
    from transformers import pipeline

    os.makedirs(args.out, exist_ok=True)
    todo = [i for i in ids if args.force or
            not os.path.exists(os.path.join(args.out, i + ".npy"))]
    print(f"{len(ids)} frame(s), {len(todo)} to dump")
    if not todo:
        return
    pipe = pipeline("depth-estimation", model=MODEL, device=-1)
    for n, image_id in enumerate(todo, 1):
        src = os.path.join(args.images, image_id + ".webp")
        if not os.path.exists(src):
            print(f"  ! missing {src}")
            continue
        img = Image.open(src).convert("RGB")
        w, h = img.size
        work = img.resize((WORK_W, int(round(h * WORK_W / w))), Image.BILINEAR)
        depth = np.array(pipe(work)["predicted_depth"], dtype="float32")
        if depth.ndim == 3:
            depth = depth[0]
        dm = Image.fromarray(depth).resize(work.size, Image.BILINEAR)
        arr = np.asarray(dm, dtype="float16")
        np.save(os.path.join(args.out, image_id + ".npy"), arr)
        print(f"  {n}/{len(todo)} {image_id} -> {arr.shape}")
    meta = {"work_width": WORK_W, "model": MODEL, "convention": "larger=closer"}
    with open(os.path.join(args.out, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh)


if __name__ == "__main__":
    main()

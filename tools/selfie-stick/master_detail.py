#!/usr/bin/env python3
"""Measure detail on the 4K masters themselves, where they sit, with no model.

Everything image-side in the corpus stats is measured on the 1600 px `large`
derivative -- make_derivatives pins that size so already-scored frames stay
comparable, and the masters never leave the capture host. That is the right
publishing rule and the wrong measurement plane for one question: how much of a
frame's detail exists only at full resolution?

This is the pure-numpy pass. It runs wherever the masters are (OMEN holds ~3,000;
AM4's fossil torch-xpu venv has numpy and pillow, so it runs there too with no
install) and emits a small JSON. No torch, no segmentation, nothing to download.

Per master, on the HUD-cropped luma:

  hfResidual      mean |a - up(down(a, 4))| at native: all detail finer than the
                  960 px plane.
  derivLoss       mean |native - up(resize(native, 1600))|: exactly the band the
                  1600 px derivative discards. derivLossShare divides it by
                  hfResidual, so 0 means the derivative keeps every fine detail
                  that exists and 1 means it loses all of it. This is the number
                  that says whether corpus stats measured on `large` are missing
                  something the master has.
  gradMean        mean gradient magnitude at native resolution.
  detailTop10     share of the frame's total gradient energy in its top-10% tiles
                  (16x9 grid). High means the detail is concentrated in a small
                  patch -- the "build is 4% of the picture" case seen from the
                  pixels rather than from the geometry.
  liveTileShare   fraction of tiles above a gradient floor: how much of the
                  frame has anything in it at all.

  python master_detail.py --images E:\\omen\\steward-multi-era\\captures\\era14\\images \\
      --out master-era14.json --jobs 12
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

CROP_FRAC = (0.0, 0.0, 1.0, 0.93)      # depth_layers.py's crop, so planes agree
DERIV_WIDTH = 1600                     # make_derivatives' large/ size
GRID_X, GRID_Y = 16, 9
LIVE_FLOOR = 0.008                     # score_frames.py's EDGE_FLOOR


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--images", required=True, help="directory (recursed) of PNG masters")
    p.add_argument("--out", required=True)
    p.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--force", action="store_true")
    return p.parse_args()


def hf_residual(a, np):
    h, w = a.shape
    small = a[::4, ::4]
    restored = np.repeat(np.repeat(small, 4, axis=0), 4, axis=1)[:h, :w]
    return float(np.abs(a - restored).mean())


def measure(path):
    import numpy as np
    from PIL import Image
    img = Image.open(path).convert("L")
    w, h = img.size
    l, t, r, b = CROP_FRAC
    img = img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    full = np.asarray(img, dtype="float32") / 255.0

    # The derivative plane, made the way make_derivatives makes it: resize to 1600
    # wide. Lanczos is what a quality resize does; the point is the band, not the
    # codec.
    dw = DERIV_WIDTH
    dh = int(round(img.size[1] * dw / float(img.size[0])))

    gy, gx = np.gradient(full)
    grad = np.hypot(gx, gy)
    H, W = grad.shape
    tiles = []
    for j in range(GRID_Y):
        for i in range(GRID_X):
            tile = grad[j * H // GRID_Y:(j + 1) * H // GRID_Y,
                        i * W // GRID_X:(i + 1) * W // GRID_X]
            tiles.append(float(tile.mean()))
    tiles_sorted = sorted(tiles, reverse=True)
    top = max(1, len(tiles) // 10)
    total = sum(tiles) or 1e-9

    # What the derivative plane discards: bring the 1600 px image back up to native
    # and difference. That is exactly the band between 1600 and 3840 wide. Expressed
    # as a share of everything finer than a 4x downsample (the 960 px plane), so 0
    # means the derivative keeps all the fine detail that exists and 1 means it
    # loses all of it.
    restored = np.asarray(
        img.resize((dw, dh), Image.LANCZOS).resize(img.size, Image.BICUBIC),
        dtype="float32") / 255.0
    lost = float(np.abs(full - restored).mean())
    hf_full = hf_residual(full, np)
    return {
        "width": w, "height": h,
        "gradMean": round(float(grad.mean()), 5),
        "hfResidualMaster": round(hf_full, 5),
        "derivLoss": round(lost, 5),
        "derivLossShare": round(lost / hf_full, 3) if hf_full > 1e-9 else None,
        "detailTop10": round(sum(tiles_sorted[:top]) / total, 4),
        "liveTileShare": round(sum(1 for t in tiles if t >= LIVE_FLOOR) / float(len(tiles)), 4),
    }


def main():
    args = parse_args()
    files = []
    for root, _, names in os.walk(args.images):
        for n in names:
            if n.lower().endswith(".png"):
                files.append(os.path.join(root, n))
    files.sort()

    done = {}
    if os.path.exists(args.out) and not args.force:
        with open(args.out, encoding="utf-8") as fh:
            done = json.load(fh).get("frames", {})
    key = lambda p: os.path.splitext(os.path.basename(p))[0]
    todo = [p for p in files if args.force or key(p) not in done]
    if args.limit:
        todo = todo[:args.limit]
    print(f"  {len(files)} master(s), {len(todo)} to measure, {args.jobs} workers")

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futs = {pool.submit(measure, p): p for p in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            p = futs[fut]
            try:
                done[key(p)] = fut.result()
            except Exception as exc:
                print(f"  ! {os.path.basename(p)}: {exc}")
            if i % 100 == 0 or i == len(todo):
                rate = i / max(time.time() - t0, 1e-3)
                print(f"    {i}/{len(todo)}   {rate:.1f}/s   "
                      f"~{(len(todo) - i) / max(rate, 1e-3) / 60:.0f} min left")

    doc = {"schema": "steward-master-detail/v1", "measuredOn": "master-native",
           "derivPlaneWidth": DERIV_WIDTH, "grid": [GRID_X, GRID_Y],
           "counts": {"frames": len(done)}, "frames": done}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    print(f"  wrote {args.out}: {len(done)} frame(s)")


if __name__ == "__main__":
    main()

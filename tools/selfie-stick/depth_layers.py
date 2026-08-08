#!/usr/bin/env python3
"""Measure whether each frame has the depth layers to feel like a place, or is
mostly one near surface with a camera pressed against it.

The aesthetic score is a taste opinion; this is a geometry measurement. A
monocular depth model (Depth Anything V2 Small, CPU is fine) turns each frame
into a depth map, and the metrics ask the questions a photographer would:

  far_mass      is there a visible background at all?
  center_block  is something near-depth sitting across the eye-line? A near
                layer at the BOTTOM of frame (a table edge, barrels, ground)
                is composition; the same mass across the upper centre is a
                wall the camera is stuck against.
  edge_frame    does the near layer hug the border (something you shoot past,
                which ADDS depth) rather than fill the middle?
  depth_span    how much of the near-to-far range the frame actually uses
  layers        how many distinct depth bands hold at least 8% of the pixels

  depth_score   composite in [0,1] — high means layered and open

Validated on 12 hand-labelled pilot frames: center_block > 0.45 fired on
exactly the two geometric duds (a crystal slab across the lens, a blocked
lattice) and on zero keepers. It is a veto and a diagnostic, not a ranker:
deep-but-unlit rooms score high here and fail on light, which the aesthetic
score already catches. The two signals are complementary.

Run with the omen-perception venv (torch + transformers):
  C:\\work\\omen-perception\\venv\\Scripts\\python.exe depth_layers.py

Writes out/depth.json  { image_id: {metrics...} }
"""
import argparse
import json
import os
import sys
import time

# curate.py's HUD crop, as fractions of the frame.
CROP_FRAC = (0.0, 40 / 900, 1550 / 1600, 1.0)
MODEL = "depth-anything/Depth-Anything-V2-Small-hf"


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--images", default=os.path.join(here, "out", "gallery", "large"))
    p.add_argument("--out", default=os.path.join(here, "out", "depth.json"))
    p.add_argument("--prefix", default="",
                   help="only image ids starting with this (e.g. a run id)")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--force", action="store_true", help="redo images already measured")
    return p.parse_args()


def crop_hud(img):
    w, h = img.size
    l, t, r, b = CROP_FRAC
    return img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))


def luma(img):
    """Mean luminance and p90-p10 spread on a 160x90 grey thumbnail — the same
    scale name_structures.py already uses to reject unreadable naming frames.
    High mean + low spread is a whiteout: fog with nothing behind it."""
    import numpy as np
    g = img.convert("L").copy()
    g.thumbnail((160, 90))
    a = np.asarray(g, dtype="float32")
    return round(float(a.mean()), 1), round(float(np.percentile(a, 90) - np.percentile(a, 10)), 1)


def metrics(depth):
    """depth: 2-D array, larger = closer (Depth Anything's convention)."""
    import numpy as np
    d = depth.astype("float32")
    lo, hi = np.percentile(d, 1), np.percentile(d, 99)
    if hi - lo < 1e-6:
        return {"near_mass": 1.0, "far_mass": 0.0, "depth_span": 0.0,
                "center_block": 1.0, "edge_frame": 0.0, "layers": 1,
                "depth_score": 0.0}
    n = np.clip((d - lo) / (hi - lo), 0.0, 1.0)          # 1 = nearest

    near = n >= 0.85
    far = n <= 0.40
    near_mass = float(near.mean())
    far_mass = float(far.mean())
    span = float(np.percentile(n, 95) - np.percentile(n, 5))

    # Upper-center box: near mass across the eye-line is blockage; the bottom
    # band is exempt because foreground there is how layered frames are built.
    h, w = n.shape
    center_block = float(near[int(h * 0.20):int(h * 0.65),
                              int(w * 0.25):int(w * 0.75)].mean())

    border = np.zeros_like(near, dtype=bool)
    bw_x, bw_y = max(1, int(w * 0.15)), max(1, int(h * 0.15))
    border[:bw_y, :] = border[-bw_y:, :] = True
    border[:, :bw_x] = border[:, -bw_x:] = True
    edge_frame = float((near & border).sum() / max(int(near.sum()), 1))

    hist, _ = np.histogram(n, bins=8, range=(0.0, 1.0))
    layers = int((hist / n.size >= 0.08).sum())

    framing_bonus = 1.0 + 0.5 * edge_frame * min(near_mass, 0.3) / 0.3
    score = far_mass * (1.0 - center_block) * span * framing_bonus
    return {"near_mass": round(near_mass, 3), "far_mass": round(far_mass, 3),
            "depth_span": round(span, 3), "center_block": round(center_block, 3),
            "edge_frame": round(edge_frame, 3), "layers": layers,
            "depth_score": round(float(min(score, 1.0)), 4)}


def main():
    args = parse_args()
    if not os.path.isdir(args.images):
        sys.exit(f"no images at {args.images} — run build_valheim_index.py --large first")

    try:
        import numpy as np
        from PIL import Image
        from transformers import pipeline
    except ImportError as exc:
        sys.exit(f"{exc}\nRun this with the omen-perception venv (torch + transformers)")

    done = {}
    if os.path.exists(args.out) and not args.force:
        with open(args.out, encoding="utf-8") as fh:
            done = json.load(fh)

    files = sorted(f for f in os.listdir(args.images) if f.endswith(".webp"))
    todo = [f for f in files
            if (args.force or f[:-5] not in done)
            and (not args.prefix or f.startswith(args.prefix))]
    if args.limit:
        todo = todo[: args.limit]
    print(f"  {len(files)} image(s), {len(todo)} to measure")
    if not todo:
        return

    pipe = pipeline("depth-estimation", model=MODEL, device=-1)
    t0 = time.time()
    for i, fname in enumerate(todo, 1):
        image_id = fname[:-5]
        try:
            img = crop_hud(Image.open(os.path.join(args.images, fname)).convert("RGB"))
            img.thumbnail((770, 770))
            depth = np.array(pipe(img)["predicted_depth"])
            m = metrics(depth)
            m["luma_mean"], m["luma_spread"] = luma(img)
            done[image_id] = m
        except Exception as exc:
            print(f"  ! {fname}: {exc}")
            continue
        if i % 25 == 0 or i == len(todo):
            rate = i / max(time.time() - t0, 0.001)
            print(f"    {i}/{len(todo)}   {rate:.1f}/s   "
                  f"~{(len(todo) - i) / max(rate, 0.001) / 60:.0f} min left")

    # Frames measured before luminance existed get a cheap top-up: no depth
    # model, just the grey thumbnail.
    topup = [i for i in done if "luma_mean" not in done[i]
             and os.path.exists(os.path.join(args.images, i + ".webp"))]
    if topup:
        print(f"  luma top-up for {len(topup)} earlier measurement(s)")
        for image_id in topup:
            try:
                img = crop_hud(Image.open(
                    os.path.join(args.images, image_id + ".webp")).convert("RGB"))
                done[image_id]["luma_mean"], done[image_id]["luma_spread"] = luma(img)
            except Exception as exc:
                print(f"  ! {image_id}: {exc}")

    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(done, fh, indent=1)
    os.replace(tmp, args.out)
    print(f"  wrote {args.out} ({len(done)} measured)")


if __name__ == "__main__":
    main()

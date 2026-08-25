#!/usr/bin/env python3
"""Measure the colour of the light in each frame: how much of it is warm, how
much is cool, what those two lobes actually are in hex, and how far apart they
sit.

The aesthetic head reads global tone and the depth model reads geometry. Neither
can answer the question a photographer asks about a lit interior -- does a warm
source separate from the ambient sky, or dissolve into it? These two lobes and
the gap between them answer it, measured within the 153 matched
(cluster, vantage) quads the Era 17 corpus already holds: 612 frames where
camera, build and framing are identical and only the light changes.

  scene_v               mean value of the lit frame: the exposure
  warm_frac/cool_frac   how much of the frame each chroma lobe holds
  warm_hex/cool_hex     the two lobe centroids, as hex
  warm_v/cool_v         and how bright each lobe is
  warm_lift             warm_v minus scene_v. How much the warm part of the
                        frame stands out from the frame. This is the number
                        that collapses at sunset, when ambient and fire share
                        a hue and no framing can separate them.
  opponent_gap          (R-B) of the warm lobe minus (R-B) of the cool lobe.
                        The separation number: high means the two lights in
                        frame are genuinely different colours.
  bright_warm_frac      fraction of the frame that is both warm and bright
  bright_warm_hex       what that region is
  ambient_hex/ambient_v the rest of the lit frame -- the field it sits against

WHAT THIS DOES NOT DO, so nobody rebuilds it: **it cannot detect a light
source.** `bright_warm_frac` is a description of the frame, not a fire detector,
and it must never be read as one. Two formulations were built and both failed:

  1. brightness above the frame's p90 plus an absolute floor, then "does the
     ring around it sit above the frame mean" -- the ring test reads 0.12-0.15
     on daylight exteriors with no light source in them at all;
  2. the corrected local gradient, core value minus ring value -- which ranks a
     hand-checked sunlit meadow (0.13) ABOVE a hand-checked blown-out hearth
     (0.056), because a big soft flame has a bright ring and dry grass does not.

And the decisive one: across 114 builds with a fixed-vocabulary light scan,
`bright_warm_frac` correlates r = 0.02-0.09 with how many warm lights the build
actually holds, in every condition. It is not measuring fire.

The reason is not a tuning problem. In daylight the sun IS the source and every
lit surface is its pool, so "brightest warm region" resolves to whatever the sun
is falling on. A source is only separable when ambient is low, which is the
question this file was written to measure rather than something it can assume
away.

PIL and numpy only. Unlike score_images.py and depth_layers.py this needs no
model, no GPU and no omen-perception venv:

  python color_layers.py --images out/era17/gallery/large --out out/era17/color.json

Writes out/color.json  { image_id: {metrics...} }
"""
import argparse
import json
import os
import sys
import time

# depth_layers.py's HUD crop, as fractions of the frame. Kept identical so the
# two measurements describe the same rectangle.
CROP_FRAC = (0.0, 40 / 900, 1550 / 1600, 1.0)

# Chroma lobes, in degrees. Warm wraps zero: firelight, torch, sunlit wood and
# thatch all land here. Cool is sky, water, storm light and blue-hour shadow --
# and in this world also the green, blue and cyan flames, which are half the
# light placed in it (see LIGHT_HUE in scan_features.py).
WARM_LO, WARM_HI = 335.0, 50.0
COOL_LO, COOL_HI = 170.0, 270.0
SAT_MIN = 0.22           # below this a pixel has no colour worth classifying
LIT_MIN = 0.10           # below this it is black, and black has no colour at all
BRIGHT_MIN = 0.45        # "bright" in absolute terms, so the number means the
                         # same thing in a dark room and at noon

# 1600px derivative down to 640 wide: 2.5x, which keeps a brazier flame a few
# pixels across. BOX, not the default bicubic -- bicubic reaches past the pixels
# a target pixel covers and smears a small bright source into the dark around
# it. Same lesson as check_overlay.py.
WORK_W, WORK_H = 640, 360


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--images", default=os.path.join(here, "out", "gallery", "large"))
    p.add_argument("--out", default=os.path.join(here, "out", "color.json"))
    p.add_argument("--prefix", default="",
                   help="only image ids starting with this (e.g. a run id)")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--force", action="store_true", help="redo images already measured")
    return p.parse_args()


def crop_hud(img):
    w, h = img.size
    l, t, r, b = CROP_FRAC
    return img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))


def hexof(rgb):
    return "#%02X%02X%02X" % tuple(int(round(max(0.0, min(255.0, c)))) for c in rgb)


def measure(img):
    """img: an already-cropped RGB PIL image. Returns the metric dict."""
    import numpy as np
    from PIL import Image

    img = img.resize((WORK_W, WORK_H), Image.Resampling.BOX)
    rgb = np.asarray(img, dtype="float32")
    hsv = np.asarray(img.convert("HSV"), dtype="float32")
    h = hsv[..., 0] * (360.0 / 255.0)
    s = hsv[..., 1] / 255.0
    v = hsv[..., 2] / 255.0

    lit = v >= LIT_MIN
    if int(lit.sum()) < 200:
        return {"lit_frac": round(float(lit.mean()), 4), "black": True}

    chroma = lit & (s >= SAT_MIN)
    warm = chroma & ((h >= WARM_LO) | (h < WARM_HI))
    cool = chroma & (h >= COOL_LO) & (h < COOL_HI)

    v_lit = float(v[lit].mean())
    out = {
        "lit_frac": round(float(lit.mean()), 4),
        "black": False,
        "scene_v": round(v_lit, 4),
        "warm_frac": round(float(warm.mean()), 4),
        "cool_frac": round(float(cool.mean()), 4),
    }

    def lobe(mask, name, floor=40):
        if int(mask.sum()) < floor:
            out[name + "_hex"] = None
            out[name + "_v"] = None
            return None
        c = rgb[mask].mean(axis=0)
        out[name + "_hex"] = hexof(c)
        out[name + "_v"] = round(float(v[mask].mean()), 4)
        return c

    cw = lobe(warm, "warm")
    cc = lobe(cool, "cool")
    out["opponent_gap"] = (round(float((cw[0] - cw[2]) - (cc[0] - cc[2])), 1)
                           if cw is not None and cc is not None else None)
    out["warm_lift"] = (round(out["warm_v"] - v_lit, 4)
                        if out["warm_v"] is not None else None)

    # Descriptive only. See the module docstring: this is not a fire detector,
    # and it fires happily on a sunlit meadow.
    bright_warm = warm & (v >= BRIGHT_MIN)
    out["bright_warm_frac"] = round(float(bright_warm.mean()), 5)
    lobe(bright_warm, "bright_warm", floor=20)
    out.pop("bright_warm_v", None)

    field = lit & ~bright_warm
    if int(field.sum()) >= 200:
        out["ambient_hex"] = hexof(rgb[field].mean(axis=0))
        out["ambient_v"] = round(float(v[field].mean()), 4)
    else:
        out["ambient_hex"] = None
        out["ambient_v"] = None
    return out


def main():
    args = parse_args()
    if not os.path.isdir(args.images):
        sys.exit(f"no images at {args.images} - run build_valheim_index.py --large first")
    try:
        import numpy  # noqa: F401
        from PIL import Image
    except ImportError as exc:
        sys.exit(f"{exc}\nThis one only needs PIL and numpy: pip install pillow numpy")

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

    t0 = time.time()
    failed = 0
    for i, fname in enumerate(todo, 1):
        image_id = fname[:-5]
        try:
            with Image.open(os.path.join(args.images, fname)) as im:
                done[image_id] = measure(crop_hud(im.convert("RGB")))
        except Exception as exc:
            print(f"  ! {fname}: {exc}")
            failed += 1
            continue
        if i % 200 == 0 or i == len(todo):
            rate = i / max(time.time() - t0, 0.001)
            print(f"    {i}/{len(todo)}   {rate:.1f}/s   "
                  f"~{(len(todo) - i) / max(rate, 0.001) / 60:.1f} min left")

    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(done, fh, indent=1)
    os.replace(tmp, args.out)
    print(f"  wrote {args.out} ({len(done)} measured, {failed} failed, "
          f"{time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()

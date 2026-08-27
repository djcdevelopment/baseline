#!/usr/bin/env python3
"""Find anything a mod is drawing on top of the frames, without being told where.

The ComfyQuest creator bar burned into 315 frames across five runs on 2026-08-24
before anyone noticed it, and the fix that followed -- a ShowCreatorBar gate in
ComfyQuestRuntime -- only closes that one mod. Five of the plugins installed
alongside the camera have an OnGUI; the next one to draw something will not
announce itself either, and a region check written against the bar's coordinates
would not see it.

So do not look for a known bar. Look for the property every overlay has and no
photograph does: it does not change when the scene does. Sample frames from
across a run -- different builds, different bearings, different light -- and take
the per-pixel standard deviation. Terrain, sky and architecture all move. A HUD
element sits at the same coordinates with the same pixels in every frame, so its
variance collapses to zero.

Measured on the two runs of 2026-08-24:

    20260824-071832  (creator bar present)   0.35% frozen, band at y 104-120
    20260824-083226  (mod parked)            0.00% frozen, no band

The bar occupies a third of a percent of the frame, which is why it survived
five runs of looking at pictures. It is unmissable in the variance map.

Exit status is the point: 0 clean, 1 something is drawing. That makes it a gate
a capture runner can call after its first few frames instead of after 240.

Usage:
  python check_overlay.py --run <capture-dir>            # a whole run
  python check_overlay.py --run <dir> --sample 6         # gate early
  python check_overlay.py --images out/era17/gallery/large --sample 30
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

# Frames are downsampled before comparison. An overlay is opaque and pixel-exact,
# so it survives an 8x reduction intact; the reduction is what makes 240 frames a
# few seconds of work instead of a few minutes.
# BOX, not the default bicubic: a box filter averages exactly the pixels a
# target pixel covers. Bicubic reaches past them, so a 16-px bar smears into the
# changing rows above and below it and stops looking frozen at all.
SCALE = 8
EXTS = (".png", ".jpg", ".jpeg", ".webp")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--run", help="a capture run directory of frames")
    src.add_argument("--images", help="any directory of frames")
    p.add_argument("--sample", type=int, default=24,
                   help="how many frames to compare (spread evenly through the run)")
    p.add_argument("--sd", type=float, default=2.0,
                   help="a pixel varying less than this across the sample is frozen")
    p.add_argument("--tolerance", type=float, default=0.05,
                   help="percent of the frame allowed to be frozen before failing")
    p.add_argument("--min-luma", type=float, default=16.0,
                   help="a pixel darker than this across the whole sample is not "
                        "counted as frozen: black sky is static because nothing is "
                        "there, a HUD is static because something is drawn there")
    p.add_argument("--ignore-right-px", type=int, default=0,
                   help="width of a right-edge strip to exclude, for a surface that "
                        "is deliberately retained in the client and cropped from the "
                        "derived images (match build_valheim_index --crop-right-ui-px)")
    return p.parse_args()


def sample_frames(directory, count):
    """Spread the sample across the run, so the frames compared are of different
    builds in different light. Consecutive frames are the same structure from
    adjacent bearings and share too much scene to tell an overlay from a wall."""
    names = sorted(f for f in os.listdir(directory) if f.lower().endswith(EXTS))
    if not names:
        sys.exit(f"no frames in {directory}")
    step = max(1, len(names) // count)
    return [os.path.join(directory, n) for n in names[::step]][:count], len(names)


def variance_map(paths):
    """Per-pixel standard deviation and mean of luminance across the sample."""
    first = Image.open(paths[0])
    size = (first.width // SCALE, first.height // SCALE)
    stack = np.stack([
        np.asarray(Image.open(p).convert("L").resize(size, Image.Resampling.BOX),
                   dtype=np.float32)
        for p in paths
    ])
    return stack.std(axis=0), stack.mean(axis=0), first.size


def bands(mask, axis, threshold=0.25):
    """Contiguous rows (or columns) that are mostly frozen. A HUD is a band; a
    frozen pixel here and there is a distant static object and not worth a word."""
    profile = mask.mean(axis=1 - axis)
    hot = np.where(profile > threshold)[0]
    out, run = [], []
    for i in hot:
        if run and i - run[-1] > 2:
            out.append((run[0], run[-1]))
            run = []
        run.append(i)
    if run:
        out.append((run[0], run[-1]))
    return out


def main():
    args = parse_args()
    directory = args.run or args.images
    paths, total = sample_frames(directory, args.sample)
    sd, mean, full = variance_map(paths)

    # Frozen AND lit. On a night run 62% of the frame sits below luma 16 and is
    # bit-identical whether or not anything is drawn on it, so plain variance
    # reports the sky as an overlay and the check can never pass. That is the
    # same darkness confound that made a naive static-pixel test score a clean
    # night run (4.61%) worse than a contaminated daylight one (0.00%).
    dark = mean < args.min_luma
    frozen = (sd < args.sd) & ~dark
    if args.ignore_right_px > 0:
        frozen[:, -max(1, args.ignore_right_px // SCALE):] = False
    pct = 100.0 * frozen.mean()

    print(f"  {os.path.basename(directory.rstrip(os.sep))}: "
          f"{len(paths)} of {total} frames at {full[0]}x{full[1]}")
    if dark.mean() > 0.2:
        print(f"  {100.0 * dark.mean():.1f}% of the frame is below luma "
              f"{args.min_luma:g} and is not judged (a dark scene, not a surface)")
    if args.ignore_right_px > 0:
        print(f"  right {args.ignore_right_px} px excluded -- cropped from the "
              f"derived images anyway")
    print(f"  {pct:.2f}% of the frame is frozen AND lit "
          f"(fails above {args.tolerance:.2f}%)")

    found = False
    for lo, hi in bands(frozen, 0):
        found = True
        print(f"    static horizontal band: y {lo * SCALE}-{(hi + 1) * SCALE}")
    for lo, hi in bands(frozen, 1):
        found = True
        print(f"    static vertical band:   x {lo * SCALE}-{(hi + 1) * SCALE}")

    if pct > args.tolerance:
        print("\n  Something is drawing on these frames. Five installed plugins have")
        print("  an OnGUI; find which one and turn its surface off at the mod, then")
        print("  re-shoot. Cropping hides it in the gallery and leaves it in the")
        print("  originals, which is how it survived five runs.")
        return 1
    if found:
        print("\n  Bands are within tolerance -- most likely scenery, not a HUD.")
    print("\n  Clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

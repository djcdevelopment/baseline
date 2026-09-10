#!/usr/bin/env python3
"""Separate the build from the landscape, so "how much detail" stops meaning "how much forest".

quality-<era>.json records edgeEnergy over the whole frame, on a thumbnail. That is
why an over-zoomed shot passes the gate: a build reduced to a speck at 180 m still
sits in a forest, and the trees supply all the edge energy the metric wants. The
number is real and measures the wrong thing.

So mask the structure and measure only there. What this tool is FOR, measured over
all 612 era11 frames against frame_forecast's independent geometry:

**It proves the forest problem.** Median edge density is 0.0190 on the build and
0.0153 on the background, and in **185 of 470 frames (39%) the background
out-textures the build**. Whole-frame edgeEnergy is measuring landscape in four
frames out of ten, which is the whole reason an over-zoomed shot passes the gate.
`edgeContrast` is the number that says so per frame.

**It is a veto for severe over-zoom, not a ranker.** By detail scale:

    px/m band     n   structure%   sky%   foliage%   bboxFill
    0-15        115          0.6   20.5        7.1      0.040
    15-25       139          4.7   14.0       20.5      0.263
    25-40        98         10.2    9.1       26.9      0.428
    40+         260          9.2    3.9       42.5      0.365

Below 15 px/m the model correctly sees almost no building (0.6%, 4% bbox fill).
But structure does not keep rising, so `corr(structureFraction, predictedPxPerM)`
is **+0.077** -- no monotonic quality signal. Structurally the same verdict this
project already reached about the LAION aesthetic head: use it to kill the
obvious, never to rank the good.

⚠ **The gap is domain, not capacity.** ADE20K is photographs and Valheim is not:
at close range its wood and thatch read as vegetation, so foliageFraction RISES
with closeness (+0.385). Swapping b0 for b4 changes nothing (structure -0.034,
foliage +0.388) -- a bigger model does not close it. Only labelled Valheim frames
would. The same mismatch calls hazy sky "water" at 70% and hallucinates a "person"
on an empty platform, which is why water is reported separately, never folded into
terrain, and why individual labels must not be read.

For "how zoomed out is this", use frame_forecast's predictedPxPerM instead. It is
exact, it is free, and it needs no image.

Measured on the 1600 px `large` derivative, not the master -- make_derivatives
pins that size so 4,536 already-scored frames stay comparable, and the masters
never leave the capture host. `measuredOn` records it.

  C:\\work\\venvs\\perception-xpu\\Scripts\\python.exe frame_geometry.py \\
      --images <era>/derivatives/large --out geometry-<era>.json --device xpu:0

Device selection follows ADR-0042: assert the free card by mem_get_info, never
trust an index, because enumeration order differs between an interactive shell
and a scheduled task.
"""
import argparse
import json
import os
import sys
import time

MODEL = "nvidia/segformer-b0-finetuned-ade-512-512"

# Substring match against the model's own id2label, so a class rename shows up as
# a missing group rather than a silently wrong index.
GROUPS = {
    "structure": ("wall", "building", "house", "skyscraper", "hut", "fence",
                  "railing", "column", "stairs", "stairway", "step", "door",
                  "windowpane", "bridge", "tower", "awning", "bannister", "booth"),
    "sky": ("sky",),
    "foliage": ("tree", "plant", "grass", "palm", "flower"),
    "terrain": ("earth", "ground", "field", "land", "hill", "mountain", "rock",
                "sand", "path", "dirt track"),
    "water": ("water", "sea", "river", "lake", "waterfall"),
}

# depth_layers.py's crop, so both passes measure the same rectangle.
CROP_FRAC = (0.0, 0.0, 1.0, 0.93)


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--images", default=os.path.join(here, "out", "gallery", "large"))
    p.add_argument("--out", default=os.path.join(here, "out", "geometry.json"))
    p.add_argument("--device", default="cpu",
                   help="cpu, or an accelerator. 'xpu' picks the freest Arc card by "
                        "mem_get_info rather than trusting an index (ADR-0042)")
    p.add_argument("--model", default=MODEL,
                   help="segmentation checkpoint. b0 is the default; larger "
                        "SegFormer variants are worth trying only with a labelled "
                        "set to judge them by, since the gap here is domain, not "
                        "capacity")
    p.add_argument("--prefix", default="")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--force", action="store_true", help="redo images already measured")
    return p.parse_args()


def resolve_device(want):
    """'xpu' means the card with the most free memory, asserted now, not assumed."""
    if want != "xpu":
        return want
    import torch
    if not torch.xpu.is_available():
        sys.exit("no XPU available; pass --device cpu")
    free = sorted(((i, torch.xpu.mem_get_info(i)[0]) for i in range(torch.xpu.device_count())),
                  key=lambda t: -t[1])
    idx, avail = free[0]
    print(f"  xpu:{idx} has {avail / 2**30:.1f} GiB free — using it")
    return f"xpu:{idx}"


def crop_hud(img):
    w, h = img.size
    l, t, r, b = CROP_FRAC
    return img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))


def build_group_ids(id2label):
    """Map each ADE20K id into one of GROUPS, and say what went unclaimed."""
    ids = {g: set() for g in GROUPS}
    for idx, label in id2label.items():
        name = str(label).lower()
        for group, needles in GROUPS.items():
            if any(n in name for n in needles):
                ids[group].add(int(idx))
                break
    return ids


def measure(labels, grey, group_ids, np):
    """labels: HxW class ids. grey: HxW float32 luma in 0..1."""
    h, w = labels.shape
    total = float(h * w)
    out = {}
    for group, members in group_ids.items():
        out[group + "Fraction"] = round(
            float(np.isin(labels, list(members)).sum()) / total, 5)

    mask = np.isin(labels, list(group_ids["structure"]))
    n = int(mask.sum())
    if n < 64:
        out.update({"subjectBBoxFill": 0.0, "subjectCentroidX": None,
                    "subjectCentroidY": None, "subjectSpread": 0.0,
                    "subjectEdgeDensity": 0.0, "backgroundEdgeDensity": 0.0,
                    "edgeContrast": None, "subjectDetailResidual": 0.0})
        return out

    ys, xs = np.nonzero(mask)
    out["subjectBBoxFill"] = round(
        float((xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)) / total, 5)
    out["subjectCentroidX"] = round(float(xs.mean()) / w, 4)
    out["subjectCentroidY"] = round(float(ys.mean()) / h, 4)
    # Spread as a fraction of the frame diagonal: a compound reads high even when
    # its bbox is the same as a solid build's, because its pixels are not together.
    diag = (h * h + w * w) ** 0.5
    out["subjectSpread"] = round(
        float(np.hypot(xs - xs.mean(), ys - ys.mean()).mean()) / diag, 4)

    # Gradient magnitude, inside the mask and outside it. The pair is the whole
    # argument: whole-frame edgeEnergy is the average of these two weighted by area,
    # and forest drives it.
    gy, gx = np.gradient(grey)
    grad = np.hypot(gx, gy)
    bg = ~mask
    out["subjectEdgeDensity"] = round(float(grad[mask].mean()), 5)
    out["backgroundEdgeDensity"] = round(float(grad[bg].mean()), 5) if bg.any() else 0.0
    out["edgeContrast"] = (round(out["subjectEdgeDensity"] / out["backgroundEdgeDensity"], 3)
                           if out["backgroundEdgeDensity"] > 1e-6 else None)

    # What a 4x downsample destroys, inside the mask: the detail that exists at
    # full size and does not survive being made small. Low means the subject is
    # already mush and a bigger print would not help it.
    small = grey[::4, ::4]
    restored = np.repeat(np.repeat(small, 4, axis=0), 4, axis=1)[:h, :w]
    out["subjectDetailResidual"] = round(float(np.abs(grey - restored)[mask].mean()), 5)
    return out


def main():
    args = parse_args()
    if not os.path.isdir(args.images):
        sys.exit(f"no images at {args.images}")

    try:
        import numpy as np
        import torch
        from PIL import Image
        from transformers import AutoImageProcessor, SegformerForSemanticSegmentation
    except ImportError as exc:
        sys.exit(f"{exc}\nRun this with C:\\work\\venvs\\perception-xpu "
                 f"(torch + transformers)")

    done = {}
    if os.path.exists(args.out) and not args.force:
        with open(args.out, encoding="utf-8") as fh:
            done = json.load(fh).get("frames", {})

    files = sorted(f for f in os.listdir(args.images) if f.endswith(".webp"))
    todo = [f for f in files
            if (args.force or f[:-5] not in done)
            and (not args.prefix or f.startswith(args.prefix))]
    if args.limit:
        todo = todo[:args.limit]
    print(f"  {len(files)} image(s), {len(todo)} to measure")
    if not todo:
        return

    device = resolve_device(args.device)
    processor = AutoImageProcessor.from_pretrained(args.model)
    model = SegformerForSemanticSegmentation.from_pretrained(args.model).to(device).eval()
    group_ids = build_group_ids(model.config.id2label)
    unclaimed = len(model.config.id2label) - sum(len(v) for v in group_ids.values())
    print(f"  {sum(len(v) for v in group_ids.values())} of "
          f"{len(model.config.id2label)} ADE20K classes grouped, {unclaimed} ignored")

    t0 = time.time()
    for i, fname in enumerate(todo, 1):
        try:
            img = crop_hud(Image.open(os.path.join(args.images, fname)).convert("RGB"))
            inputs = processor(images=img, return_tensors="pt").to(device)
            with torch.no_grad():
                logits = model(**inputs).logits
            # Upsample the class map to the frame, so fractions are of real pixels.
            up = torch.nn.functional.interpolate(
                logits, size=(img.size[1], img.size[0]),
                mode="bilinear", align_corners=False)
            labels = up.argmax(dim=1)[0].to("cpu").numpy()
            grey = np.asarray(img.convert("L"), dtype="float32") / 255.0
            done[fname[:-5]] = measure(labels, grey, group_ids, np)
        except Exception as exc:
            print(f"  ! {fname}: {exc}")
            continue
        if i % 25 == 0 or i == len(todo):
            rate = i / max(time.time() - t0, 0.001)
            print(f"    {i}/{len(todo)}   {rate:.1f}/s   "
                  f"~{(len(todo) - i) / max(rate, 0.001) / 60:.0f} min left")

    doc = {
        "schema": "steward-frame-geometry/v1",
        "model": args.model,
        "device": device,
        "measuredOn": "large-1600px",
        "groups": {g: sorted(v) for g, v in group_ids.items()},
        "counts": {"frames": len(done)},
        "frames": done,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    print(f"  wrote {args.out}: {len(done)} frame(s)")


if __name__ == "__main__":
    main()

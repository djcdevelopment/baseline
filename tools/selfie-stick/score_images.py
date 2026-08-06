#!/usr/bin/env python3
"""Score each photograph on its own merits, using the OMEN perception stack.

Until now the number on a gallery tile was the *structure's* ranking score: a
heuristic over piece count, height and footprint, identical across all six
photographs of the same building. It ranks places, and it cannot tell a good
picture of a place from a bad one — which is the thing a gallery actually needs.

This runs the same CLIP ViT-L/14 + LAION aesthetic head the image gallery uses,
so a Valheim screenshot is judged on the same scale as everything else on the
box. It is still a machine's opinion, and it is still not taste. But it is an
opinion about *this frame* rather than about the building in it.

Reuses the model and weights already on disk at C:\\work\\omen-perception — no
new download, no new dependency. Must be run with that project's venv, which has
torch and open_clip:

  C:\\work\\omen-perception\\venv\\Scripts\\python.exe score_images.py

Writes out/aesthetic.json  { image_id: {aesthetic, scored_at} }
"""
import argparse
import json
import os
import sys
import time

OMEN = r"C:\work\omen-perception"
DEFAULT_WEIGHTS = os.path.join(OMEN, "aesthetic_l14.pth")


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--images", default=os.path.join(here, "out", "gallery", "large"),
                   help="directory of renders to score (the 1600px ones)")
    p.add_argument("--out", default=os.path.join(here, "out", "aesthetic.json"))
    p.add_argument("--weights", default=DEFAULT_WEIGHTS)
    p.add_argument("--device", default="cpu")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--force", action="store_true", help="rescore images already done")
    return p.parse_args()


def build_model(device, weights):
    import torch
    import open_clip
    from torch import nn

    class Aesthetic(nn.Module):
        """LAION improved-aesthetic-predictor architecture, matching the weights."""

        def __init__(self, n=768):
            super().__init__()
            self.layers = nn.Sequential(
                nn.Linear(n, 1024), nn.Dropout(0.2),
                nn.Linear(1024, 128), nn.Dropout(0.2),
                nn.Linear(128, 64), nn.Dropout(0.1),
                nn.Linear(64, 16), nn.Linear(16, 1))

        def forward(self, x):
            return self.layers(x)

    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-L-14", pretrained="openai", force_quick_gelu=True, device=device)
    model.eval()
    aes = Aesthetic().to(device)
    aes.load_state_dict(torch.load(weights, map_location=device))
    aes.eval()
    return torch, model, preprocess, aes


def main():
    args = parse_args()
    if not os.path.isdir(args.images):
        sys.exit(f"no images at {args.images} — run build_valheim_index.py --large first")
    if not os.path.exists(args.weights):
        sys.exit(f"no aesthetic weights at {args.weights}")

    try:
        torch, model, preprocess, aes = build_model(args.device, args.weights)
    except ImportError as exc:
        sys.exit(f"{exc}\nRun this with the omen-perception venv:\n"
                 f"  {OMEN}\\venv\\Scripts\\python.exe {os.path.basename(__file__)}")
    from PIL import Image

    scores = {}
    if os.path.exists(args.out) and not args.force:
        with open(args.out, encoding="utf-8") as fh:
            scores = json.load(fh)

    files = sorted(f for f in os.listdir(args.images) if f.endswith(".webp"))
    todo = [f for f in files if args.force or f[:-5] not in scores]
    if args.limit:
        todo = todo[: args.limit]
    print(f"  {len(files)} image(s), {len(todo)} to score")

    t0 = time.time()
    for n, fname in enumerate(todo, 1):
        image_id = fname[:-5]
        try:
            img = preprocess(Image.open(os.path.join(args.images, fname))
                             .convert("RGB")).unsqueeze(0).to(args.device)
            with torch.no_grad():
                emb = model.encode_image(img)
                emb = emb / emb.norm(dim=-1, keepdim=True)
                value = float(aes(emb.float()).item())
        except Exception as exc:
            print(f"  ! {fname}: {exc}")
            continue
        scores[image_id] = {"aesthetic": round(value, 4), "scored_at": int(time.time())}
        if n % 50 == 0 or n == len(todo):
            rate = n / max(time.time() - t0, 0.001)
            left = (len(todo) - n) / max(rate, 0.001)
            print(f"    {n}/{len(todo)}   {rate:.1f}/s   ~{left/60:.0f} min left")

    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(scores, fh, indent=1)
    os.replace(tmp, args.out)

    vals = [v["aesthetic"] for v in scores.values()]
    if vals:
        vals.sort()
        print(f"\n  {len(vals)} scored -> {args.out}")
        print(f"  min {vals[0]:.2f}   median {vals[len(vals)//2]:.2f}   max {vals[-1]:.2f}")
    print("  rerun build_valheim_index.py to fold these into the gallery")


if __name__ == "__main__":
    main()

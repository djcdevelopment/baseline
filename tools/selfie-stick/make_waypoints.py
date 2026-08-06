#!/usr/bin/env python3
"""Emit a commands-only list plus a mod-readable waypoints.json.

Two outputs:
  commands.txt    one 'comfyproof_tp x y z' per line, nothing else — keep it
                  open beside the game and paste down the list.
  waypoints.json  the shape ComfyCameraProof already parses, so the mod can
                  walk the list itself. Field order matters: the plugin reads
                  it with a regex expecting rank, x, z, then y.

Usage:
  python make_waypoints.py [--clusters PATH] [--out DIR] [--region in-world]
                           [--limit 40] [--install]
"""
import argparse
import json
import os
import shutil

BEPINEX_CONFIG = r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config"


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--clusters", default=os.path.join(here, "out", "clusters.json"))
    p.add_argument("--out", default=os.path.join(here, "out"))
    p.add_argument("--region", default="in-world", choices=["all", "in-world", "outland"])
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--install", action="store_true",
                   help="also copy waypoints.json into BepInEx/config")
    return p.parse_args()


def main():
    args = parse_args()
    with open(args.clusters, encoding="utf-8") as fh:
        doc = json.load(fh)

    picked = [c for c in doc["clusters"]
              if args.region == "all" or c["region"] == args.region][: args.limit]

    os.makedirs(args.out, exist_ok=True)

    cmd_path = os.path.join(args.out, "commands.txt")
    with open(cmd_path, "w", encoding="utf-8") as fh:
        for c in picked:
            fh.write(f"comfyproof_tp {c['center_x']:.0f} "
                     f"{c['suggested_camera_y']:.0f} {c['center_z']:.0f}\n")

    # Field order is load-bearing: the plugin's regex wants rank, x, z, y.
    waypoints = [{
        "rank": i,
        "x": round(c["center_x"], 1),
        "z": round(c["center_z"], 1),
        "y": round(c["suggested_camera_y"], 1),
        "pieces": c["pieces"],
        "height_m": c["size_y"],
        "signs": c["signs"],
        "portals": c["portals"],
        "region": c["region"],
    } for i, c in enumerate(picked, start=1)]

    wp_path = os.path.join(args.out, "waypoints.json")
    with open(wp_path, "w", encoding="utf-8") as fh:
        json.dump({
            "world": doc.get("world"),
            "generated_from": "tools/selfie-stick/scan_clusters.py — 3-D BUILDING clustering",
            "region": args.region,
            "waypoints": waypoints,
        }, fh, indent=2, ensure_ascii=False)

    print(f"wrote {len(picked)} entries")
    print(f"  {cmd_path}")
    print(f"  {wp_path}")

    if args.install:
        if not os.path.isdir(BEPINEX_CONFIG):
            print(f"  ! BepInEx config not found: {BEPINEX_CONFIG}")
            return
        dest = os.path.join(BEPINEX_CONFIG, "waypoints.json")
        if os.path.exists(dest):
            backup = dest + ".bak"
            shutil.copy2(dest, backup)
            print(f"  backed up existing -> {backup}")
        shutil.copy2(wp_path, dest)
        print(f"  installed -> {dest}")


if __name__ == "__main__":
    main()

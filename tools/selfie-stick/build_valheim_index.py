#!/usr/bin/env python3
"""Build a gallery index from camera captures, joined to the structures they show.

Walks the capture folders written by the camera mod, reads each run's capture.json
for the position it was shot from, and joins that position back to the nearest
structure in clusters.json. The result is one row per image carrying not just
"a screenshot" but "a screenshot of a 19,720-piece hub with 66 portals, built by
creator 8829..., 113 m tall".

Modelled on the AM4 gallery's build_index.py (tools/am4-gallery/build_index.py):
same atomic .tmp + os.replace write, same top-level facet lists, same tolerance for
malformed rows — except that skips are reported loudly rather than silently, because
a contributor's whole drop can otherwise vanish without a message.

Usage:
  python build_valheim_index.py [--captures DIR] [--clusters PATH] [--dest DIR]
                                [--thumbs] [--max-join-m 250]
"""
import argparse
import json
import math
import os
import shutil
import sys
from collections import Counter

DEFAULT_CAPTURES = (r"C:\Program Files (x86)\Steam\steamapps\common\Valheim"
                    r"\BepInEx\config\comfy-manual-captures")
THUMB_PX = 512


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--captures", default=DEFAULT_CAPTURES,
                   help="directory of <timestamp>/ capture run folders")
    p.add_argument("--clusters", default=os.path.join(here, "out", "clusters.json"),
                   help="clusters.json from scan_clusters.py (optional but recommended)")
    p.add_argument("--dest", default=os.path.join(here, "out", "gallery"),
                   help="where index.json and thumb/ are written")
    p.add_argument("--thumbs", action="store_true",
                   help="also generate webp thumbnails (needs Pillow)")
    p.add_argument("--copy-full", action="store_true",
                   help="copy full-size images into dest/img (large; off by default)")
    p.add_argument("--max-join-m", type=float, default=250.0,
                   help="how far a shot may be from a cluster centre and still count "
                        "as a picture of it (default 250)")
    return p.parse_args()


def load_clusters(path):
    """Return clusters as a list, or [] if unavailable — the index still builds."""
    if not path or not os.path.exists(path):
        print(f"  ! no clusters.json at {path} — images will have no structure metadata")
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("clusters", [])


def nearest_cluster(clusters, x, z, max_m):
    """Nearest cluster centre in x/z. Ignores y: a shot from above is still of it."""
    best, best_d2 = None, None
    limit2 = max_m * max_m
    for c in clusters:
        dx = c["center_x"] - x
        dz = c["center_z"] - z
        d2 = dx * dx + dz * dz
        if best_d2 is None or d2 < best_d2:
            best, best_d2 = c, d2
    if best is None or best_d2 > limit2:
        return None, None
    return best, math.sqrt(best_d2)


def read_capture(run_dir):
    """Parse one run's capture.json. Returns (position, items) or raises."""
    path = os.path.join(run_dir, "capture.json")
    with open(path, encoding="utf-8-sig") as fh:      # the mod writes a BOM
        doc = json.load(fh)
    return doc["position"], doc.get("items", [])


def make_thumb(src, dest_path):
    from PIL import Image
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail((THUMB_PX, THUMB_PX))
        im.save(dest_path, "WEBP", quality=82, method=4)


def main():
    args = parse_args()
    if not os.path.isdir(args.captures):
        sys.exit(f"captures directory not found: {args.captures}")

    clusters = load_clusters(args.clusters)
    os.makedirs(args.dest, exist_ok=True)
    thumb_dir = os.path.join(args.dest, "thumb")
    img_dir = os.path.join(args.dest, "img")
    if args.thumbs:
        os.makedirs(thumb_dir, exist_ok=True)
    if args.copy_full:
        os.makedirs(img_dir, exist_ok=True)

    rows = []
    skipped = []
    unjoined = 0

    for run in sorted(os.listdir(args.captures)):
        run_dir = os.path.join(args.captures, run)
        if not os.path.isdir(run_dir):
            continue
        try:
            pos, items = read_capture(run_dir)
        except FileNotFoundError:
            skipped.append((run, "no capture.json (run interrupted?)"))
            continue
        except (json.JSONDecodeError, KeyError) as exc:
            skipped.append((run, f"unreadable capture.json: {exc}"))
            continue

        cluster, dist = nearest_cluster(clusters, pos["x"], pos["z"], args.max_join_m) \
            if clusters else (None, None)
        if clusters and cluster is None:
            unjoined += 1

        for item in items:
            still = item.get("still")
            if not still:
                skipped.append((run, "item with no filename"))
                continue
            src = os.path.join(run_dir, still)
            if not os.path.exists(src):
                skipped.append((run, f"{still} listed in manifest but missing on disk"))
                continue

            image_id = f"{run}_{os.path.splitext(still)[0]}"
            row = {
                "id": image_id,
                "run": run,                       # the "cell": all moods of one setup
                "variant": item.get("variant"),
                "environment": item.get("environment"),
                "time_of_day": item.get("timeOfDay"),
                "x": round(pos["x"], 1),
                "y": round(pos["y"], 1),
                "z": round(pos["z"], 1),
                "ts": int(os.path.getmtime(src)),
                "published": False,               # ingest is automatic, exposure is not
            }
            if cluster:
                row.update({
                    "cluster_id": cluster["cluster_id"],
                    "cluster_rank": cluster.get("rank"),
                    "shot_distance_m": round(dist, 1),
                    "pieces": cluster["pieces"],
                    "height_m": cluster["size_y"],
                    "region": cluster["region"],
                    "sky": cluster.get("sky", False),
                    "portals": cluster["portals"],
                    "beds": cluster["beds"],
                    "signs": cluster["signs"],
                    "builders": cluster["distinct_creators"],
                    "top_creator_id": cluster.get("top_creator_id"),
                })
            rows.append(row)

            if args.thumbs:
                try:
                    make_thumb(src, os.path.join(thumb_dir, image_id + ".webp"))
                except ImportError:
                    sys.exit("--thumbs needs Pillow: pip install pillow")
                except Exception as exc:
                    skipped.append((run, f"thumbnail failed for {still}: {exc}"))
            if args.copy_full:
                shutil.copy2(src, os.path.join(img_dir, image_id + ".png"))

    rows.sort(key=lambda r: -r["ts"])

    def facet(key):
        return sorted({r[key] for r in rows if r.get(key) is not None})

    doc = {
        "generated": int(__import__("time").time()),
        "n": len(rows),
        "runs": len({r["run"] for r in rows}),
        "joined": sum(1 for r in rows if "cluster_id" in r),
        "environments": facet("environment"),
        "regions": facet("region"),
        "variants": facet("variant"),
        "images": rows,
    }

    tmp = os.path.join(args.dest, "index.json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    os.replace(tmp, os.path.join(args.dest, "index.json"))

    print(f"  {len(rows):,} images across {doc['runs']} runs -> {args.dest}")
    print(f"  {doc['joined']:,} joined to a structure "
          f"({len(rows) - doc['joined']:,} without metadata)")
    if unjoined:
        print(f"  {unjoined} run(s) had no cluster within {args.max_join_m:g} m")
    if skipped:
        # Loud on purpose: build_index.py swallows these, and a contributor's whole
        # drop can disappear without a word.
        print(f"  ! skipped {len(skipped)} item(s):")
        for run, why in skipped[:12]:
            print(f"      {run}: {why}")
        if len(skipped) > 12:
            print(f"      ... and {len(skipped) - 12} more")


if __name__ == "__main__":
    main()

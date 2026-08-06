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
    p.add_argument("--orbit-captures", default=(r"C:\Program Files (x86)\Steam\steamapps"
                                                r"\common\Valheim\BepInEx\config\comfy-orbit-captures"),
                   help="directory of automated orbit capture runs")
    p.add_argument("--receipts", default=(r"C:\Program Files (x86)\Steam\steamapps\common"
                                          r"\Valheim\BepInEx\config\shotplan-receipts.jsonl"),
                   help="orbit run receipts, one JSON object per line")
    p.add_argument("--names", default=os.path.join(here, "out", "cluster-names.json"),
                   help="optional JSON map of cluster_id -> human name")
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


def read_orbit_receipts(path):
    """Orbit runs record their own provenance, one JSON object per line.

    Manual captures have to be joined to a structure by nearest centroid, because
    all the mod knew was where the player stood. An orbit shot was *planned* for a
    specific cluster, so its cluster_id is exact and carries the framing intent
    with it — planned vs actual lens position, occlusion, and how much of the build
    had streamed in when the shutter fired.
    """
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"  ! receipts line {n} unreadable: {exc}")
    return rows


def read_capture(run_dir):
    """Parse one run's capture.json. Returns (position, items) or raises."""
    path = os.path.join(run_dir, "capture.json")
    with open(path, encoding="utf-8-sig") as fh:      # the mod writes a BOM
        doc = json.load(fh)
    return doc["position"], doc.get("items", [])


def describe(c):
    """A readable name for a structure, since Valheim gives builds no names.

    Rank and piece count identify a cluster but say nothing about what it is, so
    lead with its most distinctive trait. Ordered by how strongly each trait
    characterises a place: a 66-portal hub reads as a hub first and a big build
    second, while sheer height is the defining fact about a tower.
    """
    portals, beds = c.get("portals", 0), c.get("beds", 0)
    signs, stands = c.get("signs", 0), c.get("item_stands", 0)
    h, foot = c.get("size_y", 0), c.get("footprint_m2", 0)
    builders = c.get("distinct_creators", 0)

    if portals >= 30:
        kind = "major hub"
    elif h >= 90:
        kind = "tower"
    elif stands >= 200:
        kind = "museum"
    elif signs >= 800:
        kind = "sign-covered"
    elif portals >= 10:
        kind = "hub"
    elif beds >= 10:
        kind = "settlement"
    elif foot >= 50000:
        kind = "sprawl"
    elif h >= 60:
        kind = "tall hall"
    elif builders >= 8:
        kind = "shared build"
    else:
        kind = "build"

    if c.get("sky"):
        kind = "sky " + kind
    return kind


def label_for(c, named):
    """Prefer a human name. `named` comes from the notes column of clusters.csv —
    fill it in while flying and the gallery picks it up on the next rebuild."""
    hand = (named or {}).get(str(c["cluster_id"]))
    if hand:
        return hand
    return f"{describe(c)} · {c['pieces']:,}"


def load_names(path):
    """Optional cluster_id -> name map, so structures can be named by hand."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig") as fh:
        return {str(k): str(v).strip() for k, v in json.load(fh).items() if str(v).strip()}


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
    by_id = {c["cluster_id"]: c for c in clusters}
    names = load_names(args.names)
    if names:
        print(f"  {len(names)} structure(s) named by hand")
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
                    "label": label_for(cluster, names),
                    "kind": describe(cluster),
                    "footprint_m2": cluster.get("footprint_m2"),
                    "item_stands": cluster.get("item_stands", 0),
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

    # ---- automated orbit runs -------------------------------------------------
    orbit_n = 0
    for rec in read_orbit_receipts(args.receipts):
        run, fname = rec.get("run"), rec.get("file")
        if not run or not fname:
            skipped.append((str(run), "receipt missing run or file"))
            continue
        src = os.path.join(args.orbit_captures, run, fname)
        if not os.path.exists(src):
            skipped.append((run, f"{fname} in receipts but not on disk"))
            continue
        cluster = by_id.get(rec.get("cluster_id"))
        image_id = f"{run}_{os.path.splitext(fname)[0]}"
        lens = rec.get("lens") or rec.get("placed") or {}
        row = {
            "id": image_id,
            "run": run,
            "variant": rec.get("shot"),
            "environment": rec.get("environment"),
            "time_of_day": rec.get("time_of_day"),
            "x": round(lens.get("x", 0.0), 1),
            "y": round(lens.get("y", 0.0), 1),
            "z": round(lens.get("z", 0.0), 1),
            "ts": int(os.path.getmtime(src)),
            "published": False,
            "source": "orbit",
            # orbit-only provenance: enough to tell a bad frame from a bad plan
            "occluded": bool(rec.get("occluded")),
            "pieces_near_aim": rec.get("pieces_near_aim"),
            "lens_offset_m": rec.get("lens_offset_m"),
        }
        if cluster:
            # Exact, not nearest: this shot was planned for this structure.
            row.update({
                "cluster_id": cluster["cluster_id"],
                "cluster_rank": cluster.get("rank"),
                "label": label_for(cluster, names),
                "kind": describe(cluster),
                "footprint_m2": cluster.get("footprint_m2"),
                "item_stands": cluster.get("item_stands", 0),
                "pieces": cluster["pieces"],
                "height_m": cluster["size_y"],
                "region": cluster["region"],
                "sky": cluster.get("sky", False),
                "portals": cluster["portals"],
                "beds": cluster["beds"],
                "signs": cluster["signs"],
                "builders": cluster["distinct_creators"],
                "top_creator_id": cluster.get("top_creator_id"),
                "shot_distance_m": 0.0,
            })
        rows.append(row)
        orbit_n += 1

        if args.thumbs:
            try:
                make_thumb(src, os.path.join(thumb_dir, image_id + ".webp"))
            except Exception as exc:
                skipped.append((run, f"thumbnail failed for {fname}: {exc}"))
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
        "kinds": facet("kind"),
        "images": rows,
    }

    tmp = os.path.join(args.dest, "index.json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    os.replace(tmp, os.path.join(args.dest, "index.json"))

    print(f"  {len(rows):,} images across {doc['runs']} runs -> {args.dest}")
    if orbit_n:
        occ = sum(1 for r in rows if r.get("source") == "orbit" and r.get("occluded"))
        print(f"  {orbit_n:,} from automated orbit runs ({occ} flagged occluded)")
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

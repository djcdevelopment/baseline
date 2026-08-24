#!/usr/bin/env python3
"""Choose which structures to photograph next, when quality cannot be predicted.

The ranking in scan_clusters.py sorts by piece mass, height, prefab variety and
compactness. It was never validated against how the results actually photograph,
and now that there are 2,081 scored frames it can be: measured across 268 builds
with three or more frames each, it correlates with photo quality at **r = -0.136**.
So does everything else about a structure --

    height -0.189   distinct prefabs -0.128   density -0.089   pieces -0.034
    portals, footprint, signs ~ 0     interior seats -0.252

-- every one near zero, most of them negative. Within-build spread (sd 0.239) is
nearly the whole of between-build spread (sd 0.275): which frame you keep matters
about as much as which building you point at.

There is therefore nothing to tune. No attribute of a structure tells you whether
it will make a good photograph, and a targeting rule that claims otherwise is
selling a correlation that is not there.

What targeting CAN control is who and where the gallery covers. Of Era 17's 299
in-world creators, 163 appear in it and 136 do not. For a gallery called "what
people built", one photograph of an unrepresented builder's work is worth more
than the ninth angle on the biggest hall. So the cascade is:

    creators   one build each for builders with nothing in the gallery
    cells      builds in 2 km cells that have no photograph at all
    depth      the old score order, for whatever the window has left

The score survives as a tie-break inside each tier. It is a reasonable ordering
heuristic; it is just not a quality one.

Creator ids never leave this machine. scrub_index.py drops top_creator_id from
the published index; this reads the local clusters.json and emits cluster ids.

Usage:
  python pick_targets.py --clusters out/era17/clusters.json \\
                         --index out/era17/gallery/index.json \\
                         --strategy coverage --count 48

stdout is the id list, ready for plan_shots.py --include-ids. stderr is the
summary, so `--include-ids "$(python pick_targets.py ...)"` works directly.
"""
import argparse
import json
import os
import sys

AREA_CELL_M = 2000.0        # same grid build_valheim_index.py groups areas on


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--clusters", default=os.path.join(here, "out", "clusters.json"))
    p.add_argument("--index", default=os.path.join(here, "out", "gallery", "index.json"),
                   help="gallery index, to know what has already been photographed")
    p.add_argument("--strategy", default="coverage",
                   choices=["coverage", "creators", "cells", "depth"])
    p.add_argument("--count", type=int, default=48)
    p.add_argument("--region", default="in-world", choices=["all", "in-world", "outland"])
    p.add_argument("--exclude-sky", action="store_true", default=True,
                   help="skip sky builds (default on; they blow out from every bearing)")
    p.add_argument("--include-sky", dest="exclude_sky", action="store_false")
    p.add_argument("--max-height-m", type=float, default=300.0,
                   help="skip clustering artifacts, same threshold plan_shots.py uses")
    return p.parse_args()


def load_json(path, what):
    if not os.path.exists(path):
        sys.exit(f"no {what} at {path}")
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def cell_of(c):
    return (int(c["center_x"] // AREA_CELL_M), int(c["center_z"] // AREA_CELL_M))


def by_creator(clusters):
    """Best-scoring unshot build for each creator, keyed by creator id."""
    best = {}
    for c in clusters:
        cid = c.get("top_creator_id")
        if not cid:
            continue
        if cid not in best or c["score"] > best[cid]["score"]:
            best[cid] = c
    return best


def main():
    args = parse_args()
    doc = load_json(args.clusters, "clusters.json")
    clusters = [c for c in doc["clusters"]
                if args.region == "all" or c["region"] == args.region]
    index = load_json(args.index, "gallery index")
    shot = {i["cluster_id"] for i in index.get("images", []) if i.get("cluster_id") is not None}

    dropped = []
    if args.exclude_sky:
        dropped += [(c, "sky") for c in clusters if c.get("sky")]
        clusters = [c for c in clusters if not c.get("sky")]
    if args.max_height_m:
        dropped += [(c, "too tall to be one structure")
                    for c in clusters if c["size_y"] > args.max_height_m]
        clusters = [c for c in clusters if c["size_y"] <= args.max_height_m]

    unshot = sorted((c for c in clusters if c["cluster_id"] not in shot),
                    key=lambda c: -c["score"])

    # --- who is already in the gallery, and where ---------------------------
    shot_creators = {c["top_creator_id"] for c in clusters
                     if c["cluster_id"] in shot and c.get("top_creator_id")}
    all_creators = {c["top_creator_id"] for c in clusters if c.get("top_creator_id")}
    shot_cells = {cell_of(c) for c in clusters if c["cluster_id"] in shot}

    tiers = {"creators": [], "cells": [], "depth": []}

    seen_creators = set(shot_creators)
    for creator, c in sorted(by_creator(unshot).items(),
                             key=lambda kv: -kv[1]["score"]):
        if creator in seen_creators:
            continue
        seen_creators.add(creator)
        tiers["creators"].append(c)

    taken = {c["cluster_id"] for c in tiers["creators"]}
    seen_cells = set(shot_cells)
    for c in unshot:
        if c["cluster_id"] in taken:
            continue
        cell = cell_of(c)
        if cell in seen_cells:
            continue
        seen_cells.add(cell)
        tiers["cells"].append(c)

    taken |= {c["cluster_id"] for c in tiers["cells"]}
    tiers["depth"] = [c for c in unshot if c["cluster_id"] not in taken]

    order = (["creators", "cells", "depth"] if args.strategy == "coverage"
             else [args.strategy])
    picked, from_tier = [], {}
    for tier in order:
        for c in tiers[tier]:
            if len(picked) >= args.count:
                break
            picked.append(c)
            from_tier[c["cluster_id"]] = tier

    # --- the summary goes to stderr so stdout stays pasteable ---------------
    def say(msg):
        print(msg, file=sys.stderr)

    say(f"  {len(clusters):,} {args.region} clusters, {len(shot & {c['cluster_id'] for c in clusters}):,} "
        f"photographed, {len(unshot):,} still unshot")
    if dropped:
        why = {}
        for c, reason in dropped:
            why[reason] = why.get(reason, 0) + 1
        say("  skipped " + ", ".join(f"{n} {reason}" for reason, n in sorted(why.items())))
    say(f"  creators: {len(shot_creators)}/{len(all_creators)} represented "
        f"({100.0 * len(shot_creators) / max(len(all_creators), 1):.0f}%)")
    say(f"  available by tier: {len(tiers['creators'])} creators, "
        f"{len(tiers['cells'])} new cells, {len(tiers['depth'])} depth")
    say("")
    chose = {}
    for cid, tier in from_tier.items():
        chose[tier] = chose.get(tier, 0) + 1
    say(f"  picked {len(picked)}: " +
        ", ".join(f"{n} from {tier}" for tier, n in chose.items()))
    if chose.get("creators"):
        after = len(shot_creators) + chose["creators"]
        say(f"  representation would move {len(shot_creators)} -> {after} "
            f"of {len(all_creators)} creators")
    if chose.get("cells"):
        say(f"  and reach {chose['cells']} 2 km cell(s) that have no photograph yet")
    say(f"  {len(picked) * 5} frames at five per build")

    print(",".join(str(c["cluster_id"]) for c in picked))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Freeze a deterministic roof-semantics candidate set and stratified holdout.

Pass 1 writes candidates before model output is inspected. Pass 2 reads those exact
candidates plus their private architecture-v2 files and selects five simple and five
compound roofs in the already-frozen hash order.
"""

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict

import duckdb


HERE = os.path.dirname(os.path.abspath(__file__))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster-points", required=True)
    parser.add_argument("--clusters", default=os.path.join(HERE, "out", "era17",
                                                            "clusters.json"))
    parser.add_argument("--gallery-index", default=os.path.join(
        HERE, "out", "era17", "gallery", "index.json"))
    parser.add_argument("--geometry", default=os.path.join(
        HERE, "out", "era17", "arch", "piece-geometry.json"))
    parser.add_argument("--calibration-ids", default="578,916,1775,1820")
    parser.add_argument("--snapshot-id", type=int, default=107)
    parser.add_argument("--candidate-count", type=int, default=40)
    parser.add_argument("--candidates", default="",
                        help="pass-1 manifest; supplying it enables final stratification")
    parser.add_argument("--architecture-dir", default="")
    parser.add_argument("--per-stratum", type=int, default=5)
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def write_json(path, value):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=1, ensure_ascii=False)
    os.replace(path + ".tmp", path)


def clean_orbit_frames(index):
    by_cluster = defaultdict(lambda: defaultdict(list))
    for frame in index["images"]:
        variant = str(frame.get("variant") or "")
        if (frame.get("source") != "orbit" or not variant.startswith("orbit")
                or frame.get("occluded") or frame.get("fog")):
            continue
        by_cluster[int(frame["cluster_id"])][variant].append(frame["id"])
    return by_cluster


def chosen_frame_ids(frames):
    variants = sorted(frames)
    preferred = [name for name in ("orbit1", "orbit2") if name in frames]
    for name in variants:
        if name not in preferred:
            preferred.append(name)
        if len(preferred) == 2:
            break
    return [sorted(frames[name])[-1] for name in preferred[:2]]


def candidate_pass(args):
    with open(args.clusters, encoding="utf-8") as stream:
        cluster_doc = json.load(stream)
    with open(args.gallery_index, encoding="utf-8") as stream:
        gallery = json.load(stream)
    with open(args.geometry, encoding="utf-8") as stream:
        geometry = json.load(stream)
    roof_names = [piece["name"] for piece in geometry["pieces"]
                  if piece.get("family") == "roof"]
    frames = clean_orbit_frames(gallery)
    calibration = {int(value) for value in args.calibration_ids.split(",")
                   if value.strip()}

    connection = duckdb.connect()
    point_path = args.cluster_points.replace("'", "''").replace("\\", "/")
    connection.execute(
        f"CREATE TEMP VIEW points AS SELECT * FROM read_parquet('{point_path}')")
    metadata = connection.execute(
        "SELECT DISTINCT snapshot_id, world_id FROM points").fetchall()
    expected = (cluster_doc.get("snapshot_id"), cluster_doc.get("world_id"))
    if metadata != [expected] or expected[0] != args.snapshot_id:
        connection.close()
        sys.exit(f"point metadata {metadata} does not match expected {expected}")
    connection.execute("CREATE TEMP TABLE roof_prefab(name VARCHAR)")
    connection.executemany("INSERT INTO roof_prefab VALUES (?)",
                           [(name,) for name in roof_names])
    roof_counts = dict(connection.execute("""
        SELECT cluster_id, count(*)
        FROM points JOIN roof_prefab ON prefab_name = name
        GROUP BY cluster_id
        """).fetchall())
    connection.close()

    candidates = []
    for cluster in cluster_doc["clusters"]:
        cluster_id = int(cluster["cluster_id"])
        pieces = int(cluster["pieces"])
        if (cluster_id in calibration or not 400 <= pieces <= 3000
                or len(frames[cluster_id]) < 2 or roof_counts.get(cluster_id, 0) < 20):
            continue
        order_key = hashlib.sha256(
            f"{args.snapshot_id}:{cluster_id}".encode("ascii")).hexdigest()
        candidates.append({
            "order_key": order_key,
            "cluster_id": cluster_id,
            "pieces": pieces,
            "roof_pieces": int(roof_counts[cluster_id]),
            "selected_frames": chosen_frame_ids(frames[cluster_id]),
        })
    candidates.sort(key=lambda item: item["order_key"])
    candidates = candidates[:args.candidate_count]
    out = {
        "schema": "selfie-stick-roof-holdout-candidates/v1",
        "snapshot_id": args.snapshot_id,
        "world_id": cluster_doc.get("world_id"),
        "selection_rule": {
            "pieces": "400..3000 inclusive",
            "minimum_roof_pieces": 20,
            "minimum_clean_orbit_variants": 2,
            "excluded_calibration_ids": sorted(calibration),
            "order": "sha256('<snapshot_id>:<cluster_id>') ascending",
            "candidate_count": args.candidate_count,
            "adjudication_frames": "latest orbit1 and orbit2, independent of model output",
        },
        "candidates": candidates,
    }
    write_json(args.out, out)
    print(f"froze {len(candidates)} candidates -> {args.out}")


def final_pass(args):
    if not args.architecture_dir:
        sys.exit("--architecture-dir is required with --candidates")
    with open(args.candidates, encoding="utf-8") as stream:
        candidate_doc = json.load(stream)
    strata = {"simple": [], "compound": []}
    audited = []
    for candidate in candidate_doc["candidates"]:
        cluster_id = candidate["cluster_id"]
        path = os.path.join(args.architecture_dir,
                            f"{cluster_id}.architecture-v2.json")
        if not os.path.isfile(path):
            sys.exit(f"architecture result missing: {path}")
        with open(path, encoding="utf-8") as stream:
            architecture = json.load(stream)
        assemblies = [roof for structure in architecture.get("structures", [])
                      for roof in structure.get("roof_assemblies", [])
                      if not roof.get("fragment")]
        assemblies.sort(key=lambda item: (-item["area_fraction"], item["roof_id"]))
        significant = [item for item in assemblies if item["area_fraction"] >= 0.10]
        dominant = assemblies[0]["area_fraction"] if assemblies else 0.0
        stratum = None
        if dominant >= 0.75 and len(significant) == 1:
            stratum = "simple"
        elif len(significant) >= 2:
            stratum = "compound"
        row = {**candidate, "stratum": stratum,
               "dominant_roof_area_fraction": round(dominant, 3),
               "significant_roof_assemblies": len(significant),
               "predicted_shape": (architecture.get("roof") or {}).get("shape_estimate")}
        audited.append(row)
        if stratum and len(strata[stratum]) < args.per_stratum:
            strata[stratum].append(row)

    if any(len(rows) != args.per_stratum for rows in strata.values()):
        sys.exit("candidate set did not yield the requested simple/compound strata: "
                 + ", ".join(f"{name}={len(rows)}" for name, rows in strata.items()))
    holdout = strata["simple"] + strata["compound"]
    out = {
        "schema": "selfie-stick-roof-holdout/v1",
        "snapshot_id": candidate_doc["snapshot_id"],
        "world_id": candidate_doc.get("world_id"),
        "stratification_rule": {
            "simple": "one >=10% assembly and dominant area fraction >=0.75",
            "compound": "at least two assemblies with area fraction >=0.10",
            "per_stratum": args.per_stratum,
            "selection": "first qualifying rows in frozen candidate order",
        },
        "holdout": holdout,
        "candidate_audit": audited,
    }
    write_json(args.out, out)
    print(f"froze {len(holdout)} holdout clusters -> {args.out}")
    print("  simple: " + ",".join(str(row["cluster_id"]) for row in strata["simple"]))
    print("  compound: " + ",".join(str(row["cluster_id"]) for row in strata["compound"]))


def main():
    args = parse_args()
    if args.candidates:
        final_pass(args)
    else:
        candidate_pass(args)


if __name__ == "__main__":
    main()

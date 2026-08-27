#!/usr/bin/env python3
"""Score a frozen roof-semantics holdout and emit the promotion verdict."""

import argparse
import hashlib
import json
import math
import os
import sys


MODEL_VERSION = "roof-plane-assemblies/v1"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--holdout", required=True)
    parser.add_argument("--judgments", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--minimum-score", type=int, default=16)
    parser.add_argument("--minimum-ridge-hits", type=int, default=8)
    parser.add_argument("--ridge-tolerance-deg", type=float, default=15.0)
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.holdout, encoding="utf-8") as stream:
        holdout = json.load(stream)
    with open(args.judgments, encoding="utf-8") as stream:
        judgments = json.load(stream)

    expected_rows = holdout["holdout"]
    expected = [int(item["cluster_id"]) for item in expected_rows]
    rows = judgments.get("judgments") or []
    actual = [int(item["cluster_id"]) for item in rows]
    if actual != expected:
        sys.exit(f"judgment ids/order {actual} do not match frozen holdout {expected}")
    if any(item.get("score") not in (0, 1, 2) for item in rows):
        sys.exit("every judgment score must be 0, 1, or 2")
    for expected_row, judgment in zip(expected_rows, rows):
        if judgment.get("predicted_shape") != expected_row.get("predicted_shape"):
            sys.exit("judgment predicted shape does not match frozen model output for "
                     f"cluster {judgment['cluster_id']}")
        ridge_error = judgment.get("ridge_error_deg")
        if ridge_error is not None and (not math.isfinite(float(ridge_error))
                                        or float(ridge_error) < 0):
            sys.exit("ridge_error_deg must be a finite non-negative number or null")

    total = sum(item["score"] for item in rows)
    maximum_score = 2 * len(rows)
    contradictions = [item["cluster_id"] for item in rows
                      if item.get("visibility") == "clear"
                      and item.get("verdict") == "contradicted"]
    ridge_rows = [item for item in rows if item.get("ridge_error_deg") is not None]
    ridge_hits = sum(float(item["ridge_error_deg"]) <= args.ridge_tolerance_deg
                     for item in ridge_rows)
    gates = {
        "semantic_score": {"actual": total, "required": args.minimum_score,
                           "pass": total >= args.minimum_score},
        "clear_contradictions": {"actual": len(contradictions), "required": 0,
                                 "cluster_ids": contradictions,
                                 "pass": not contradictions},
        "ridge_hits": {"actual": ridge_hits, "adjudicated": len(ridge_rows),
                       "required": args.minimum_ridge_hits,
                       "tolerance_deg": args.ridge_tolerance_deg,
                       "pass": ridge_hits >= args.minimum_ridge_hits},
    }
    verdict = "PASS" if all(item["pass"] for item in gates.values()) else "FAIL"
    out = {
        "schema": "selfie-stick-roof-model-validation/v1",
        "model_version": MODEL_VERSION,
        "snapshot_id": holdout.get("snapshot_id"),
        "world_id": holdout.get("world_id"),
        "verdict": verdict,
        "inputs": {
            "holdout": {"bytes": os.path.getsize(args.holdout),
                        "sha256": sha256_file(args.holdout)},
            "judgments": {"bytes": os.path.getsize(args.judgments),
                          "sha256": sha256_file(args.judgments)},
        },
        "settings": {
            "maximum_semantic_score": maximum_score,
            "minimum_semantic_score": args.minimum_score,
            "minimum_ridge_hits": args.minimum_ridge_hits,
            "ridge_tolerance_deg": args.ridge_tolerance_deg,
        },
        "gates": gates,
        "judgments": rows,
        "edge_found": judgments.get("edge_found"),
        "planner_consequence": ("roof semantics may be consumed by the planner"
                                if verdict == "PASS" else
                                "roof semantics remain report-only; do not emit roofline shots"),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out + ".tmp", "w", encoding="utf-8") as stream:
        json.dump(out, stream, indent=1, ensure_ascii=False)
    os.replace(args.out + ".tmp", args.out)
    print(f"roof semantic gate: {verdict} ({total}/{maximum_score}, "
          f"{len(contradictions)} clear contradiction(s), {ridge_hits} ridge hit(s))")
    print(args.out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Is this build worth a photograph at all? Decided before the shutter, from the pieces alone.

Of the 33 builds that lost both frames in the 77-pair light table of 2026-09-12, the judge
said about six in ten were not camera failures: sparse debris like a destroyed village, or a
flat floor with nothing standing on it. No pose fixes that. So the question is asked first,
of the ZDO point set, and a build that fails never enters a campaign.

Features (pure functions over (x, y, z, prefab_name) rows):
  pieces            construction pieces in the build
  largestMassShare  share of pieces in the biggest 8 m-cell component (scan_build_features)
  masses            components holding >= 2 % of the pieces
  height            p95 - p5 of piece elevation, metres (outliers ignored)
  density           pieces per square metre of the xz footprint
  floorShare        share of pieces whose prefab is a floor, path or terrain operation
  sprawl            mass_radii P100 / P90

Rules are the two failure modes the judge named, each a conjunction with thresholds that
mean something in metres and pieces -- NOT extremes fitted to a sample. The first attempt
fitted one threshold per feature to the 77 detail-tier builds (all >= 529 pieces, median
~3,000) and then rejected 50 single-storey houses in era 1 for being under 6.2 m tall: a
Valheim wall is 2 m, a roofed hut is 4-6 m, and that sample had simply never seen one.

  bare-floor   height < 3 m  AND floorShare > 0.5     a floor, a path, a fence line; nothing stands on it
  debris       density < 0.02 /m2 AND largestMassShare < 0.35    thin scatter with no coherent mass

`calibrate` REPORTS how the declared rules behave on labelled builds (kept must be 0 lost;
neither caught is whatever it is) and the per-feature distributions, so a threshold is
changed with evidence in hand. `gate` applies the rules to a campaign and writes the
filtered campaign beside a receipt naming every build it removed and why.

    python subject_gate.py calibrate --root E:/omen/steward-multi-era --era era11 \\
        --verdicts docs/evidence/2026-09-12-refine-loop-calibration/pair-verdicts.json \\
        --refine docs/evidence/2026-09-12-era11-refine-full/refine.json --out calibration.json
    python subject_gate.py gate --root E:/omen/steward-multi-era --era era1 --campaign R/campaign.json \\
        --thresholds thresholds.json --out R/campaign-gated.json
"""
import argparse
import itertools
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import frame_forecast          # noqa: E402  (mass_radii, percentile: pure)
import scan_build_features     # noqa: E402  (subclusters: pure)

FLOOR = re.compile(r"floor|paved|path|cultivat|raise|level|dirt|ground", re.IGNORECASE)
# Each rule is a conjunction of (feature, direction, limit); a build is rejected when it fails
# every clause of any rule. These are the defaults; a thresholds file may override the limits.
DEFAULT_RULES = {
    "bare-floor": [["height", "max", 3.0], ["floorShare", "min", 0.5]],
    "debris": [["density", "max", 0.02], ["largestMassShare", "max", 0.35]],
}


def load(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def features(rows):
    """rows: iterable of (x, y, z, prefab_name). Returns the feature dict, or None if empty."""
    rows = list(rows)
    if not rows:
        return None
    points = [(r[0], r[1], r[2]) for r in rows]
    n = len(points)
    ys = sorted(p[1] for p in points)
    height = frame_forecast.percentile(ys, 95.0) - frame_forecast.percentile(ys, 5.0)
    xs, zs = [p[0] for p in points], [p[2] for p in points]
    footprint = max(1.0, (max(xs) - min(xs)) * (max(zs) - min(zs)))
    components = scan_build_features.subclusters(points)
    sizes = sorted((c["pieces"] for c in components), reverse=True) or [n]
    floors = sum(1 for r in rows if r[3] and FLOOR.search(r[3]))
    _, _, _, p90, p100 = frame_forecast.mass_radii(points)
    return {"pieces": n, "largestMassShare": round(sizes[0] / n, 4), "masses": len(sizes),
            "height": round(height, 2), "density": round(n / footprint, 4), "floorShare": round(floors / n, 4),
            "sprawl": round(p100 / p90, 3) if p90 > 0 else 1.0}


def rules_from(thresholds):
    """Accept a thresholds file (steward-subject-gate-thresholds/v1) or the defaults."""
    if thresholds and thresholds.get("rules"):
        return thresholds["rules"]
    return DEFAULT_RULES


def verdict(feature, thresholds=None):
    """Every rule the build fails, with the clauses that failed it; an empty list is a pass."""
    reasons = []
    if not feature:
        return ["no pieces resolved"]
    for name, clauses in rules_from(thresholds).items():
        failed = []
        for key, direction, limit in clauses:
            value = feature.get(key)
            if value is None:
                break
            if (direction == "max" and value < limit) or (direction == "min" and value > limit):
                failed.append(f"{key} {value} {'<' if direction == 'max' else '>'} {limit}")
            else:
                break
        else:
            reasons.append(f"{name}: " + " and ".join(failed))
    return reasons


def calibrate(labelled, thresholds=None):
    """labelled: {build: (features, keep: bool)}. Reports how the declared rules behave on
    the labelled builds and where each feature's classes sit, so a limit is changed with the
    evidence in front of you rather than fitted to whatever sample happened to be labelled."""
    kept = {b: f for b, (f, keep) in labelled.items() if keep}
    lost = {b: f for b, (f, keep) in labelled.items() if not keep}
    rejected = {b: verdict(f, thresholds) for b, (f, keep) in labelled.items()}
    caught = sorted(b for b in lost if rejected[b])
    wrongly = sorted(b for b in kept if rejected[b])
    per_rule = {}
    for name in rules_from(thresholds):
        per_rule[name] = {"neitherCaught": sum(1 for b in lost if any(r.startswith(name + ":") for r in rejected[b])),
                          "keptRejected": sum(1 for b in kept if any(r.startswith(name + ":") for r in rejected[b]))}
    distributions = {}
    for key in ("pieces", "largestMassShare", "masses", "height", "density", "floorShare", "sprawl"):
        def q(values):
            values = sorted(v for v in values if v is not None)
            return {"min": values[0], "median": values[len(values) // 2], "max": values[-1]} if values else None
        distributions[key] = {"kept": q(f[key] for f in kept.values()), "neither": q(f[key] for f in lost.values())}
    return {"rules": rules_from(thresholds), "neither": len(lost), "kept": len(kept),
            "neitherCaught": len(caught), "rate": round(len(caught) / len(lost), 3) if lost else None,
            "keptRejected": wrongly, "caught": caught, "perRule": per_rule, "distributions": distributions}


def read_rows(root, era, build_keys):
    """(x, y, z, prefab_name) per build from the archive's own parquet, grouped by build key."""
    import duckdb
    import plan_detail_shots
    era_row, membership, zdo = plan_detail_shots.artifacts(root, era)
    out = {}
    with duckdb.connect(":memory:") as con:
        con.execute("SET threads=2; SET memory_limit='1GB'")
        con.execute("CREATE TABLE wanted(build_key VARCHAR PRIMARY KEY)")
        con.executemany("INSERT INTO wanted VALUES (?)", [(k,) for k in build_keys])
        cursor = con.execute(f"""
            SELECT m.build_key, z.x, z.y, z.z, z.prefab_name
            FROM read_parquet('{membership}') m JOIN wanted USING(build_key)
            JOIN read_parquet('{zdo}') z USING(snapshot_id, zdo_index)
            WHERE m.snapshot_id = ? ORDER BY m.build_key, z.zdo_index""", [era_row["snapshotId"]])

        def rows():
            while True:
                chunk = cursor.fetchmany(8192)
                if not chunk:
                    break
                yield from chunk
        for key, group in itertools.groupby(rows(), key=lambda r: r[0]):
            out.setdefault(key, []).extend((float(r[1]), float(r[2]), float(r[3]), r[4]) for r in group)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("calibrate")
    c.add_argument("--root", required=True); c.add_argument("--era", required=True)
    c.add_argument("--verdicts", required=True, help="pair-verdicts.json; `neither` is the lost class, everything decided is kept")
    c.add_argument("--refine", required=True, help="refine.json of the same run, for the full build keys")
    c.add_argument("--thresholds", default=None, help="rules to report on (default: the built-in rules)")
    c.add_argument("--out", required=True)
    g = sub.add_parser("gate")
    g.add_argument("--root", required=True); g.add_argument("--era", required=True)
    g.add_argument("--campaign", required=True); g.add_argument("--thresholds", required=True)
    g.add_argument("--out", required=True, help="filtered campaign.json; the receipt is written beside it")
    args = parser.parse_args()
    if args.command == "calibrate":
        verdicts = load(args.verdicts)["verdicts"]
        refine = load(args.refine)["builds"]
        full = {k[:8]: k for k in refine}
        labelled_keys = {full[v["build"]]: v["chose"] != "neither" for v in verdicts if v["build"] in full}
        rows = read_rows(args.root, args.era, list(labelled_keys))
        labelled = {k: (features(rows.get(k, [])), keep) for k, keep in labelled_keys.items() if rows.get(k)}
        thresholds = load(args.thresholds) if args.thresholds else None
        result = calibrate(labelled, thresholds)
        receipt = {"schema": "steward-subject-gate-calibration/v2", "era": args.era, "verdicts": args.verdicts,
                   "labelled": len(labelled), **result,
                   "features": {k[:8]: {**f, "kept": keep} for k, (f, keep) in labelled.items()}}
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(receipt, fh, indent=1)
        print(f"{result['neitherCaught']}/{result['neither']} neither builds rejected ({result['rate']:.0%}), "
              f"{len(result['keptRejected'])} kept builds wrongly rejected -> {args.out}")
        for name, row in result["perRule"].items():
            print(f"  {name:12} catches {row['neitherCaught']:2}/{result['neither']} neither, rejects {row['keptRejected']} kept")
        for key, d in result["distributions"].items():
            print(f"  {key:18} kept {d['kept']}   neither {d['neither']}")
    else:
        thresholds = load(args.thresholds)
        campaign = load(args.campaign)
        keys = [b["buildKey"] for b in campaign["builds"]]
        rows = read_rows(args.root, args.era, keys)
        kept, removed = [], []
        for build in campaign["builds"]:
            f = features(rows.get(build["buildKey"], []))
            reasons = verdict(f, thresholds)
            (removed if reasons else kept).append({"buildKey": build["buildKey"], "features": f, "reasons": reasons})
        filtered = {**campaign, "builds": [b for b in campaign["builds"] if not any(r["buildKey"] == b["buildKey"] for r in removed)],
                    "subjectGate": {"rules": rules_from(thresholds), "removed": len(removed)}}
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(filtered, fh, indent=2)
        receipt_path = os.path.join(os.path.dirname(os.path.abspath(args.out)), f"subject-gate-{args.era}.json")
        with open(receipt_path, "w", encoding="utf-8") as fh:
            json.dump({"schema": "steward-subject-gate/v1", "era": args.era, "rules": rules_from(thresholds),
                       "kept": len(kept), "removed": removed}, fh, indent=1)
        print(f"{len(kept)} builds pass, {len(removed)} removed before any shutter -> {args.out}; receipt {receipt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Turn a refine run's winners into a kit shot list, from the receipts, not the plan.

The archive's photography loop shoots a planned pose, judges it, moves the camera, and keeps
the best frame per build (refine.json). The receipt of the kept frame records where the
player's feet were actually placed, the yaw and pitch, and the aim -- after ground clamps and
occlusion recoveries -- so a row built from it reproduces the photograph, not the intent.
Builds the loop handed back to the planner (`needs`) are left out.

    python make_shots.py --refine <run>/refine.json --state <run>/state.json --out shots/shots-era11.tsv
"""
import argparse
import json
from pathlib import Path

HEADER = "# cluster_id\tshot\tcam_x\tcam_y\tcam_z\tyaw\tpitch\tenv\ttime\taim_x\taim_y\taim_z\tlabel\tmode\tfires\tflash\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--refine", type=Path, required=True)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--include-needs", action="store_true", help="also emit builds the loop could not fix")
    args = p.parse_args()
    refine = json.loads(args.refine.read_text(encoding="utf-8-sig"))
    completed = json.loads(args.state.read_text(encoding="utf-8-sig"))["completed"]
    rows, skipped = [], []
    for key, build in refine["builds"].items():
        if build.get("needs") and not args.include_needs:
            skipped.append((key[:8], build["needs"]))
            continue
        entry = completed.get(build.get("winnerShotKey") or "")
        receipt = (entry or {}).get("receipt") or {}
        placed, aim = receipt.get("placed"), receipt.get("aim")
        if not placed or not aim or receipt.get("yaw") is None:
            skipped.append((key[:8], "no receipt"))
            continue
        env = receipt.get("environment") or "Clear"
        tod = receipt.get("time_of_day", 0.64)
        rows.append("\t".join(str(v) for v in (
            build["localClusterId"], build["winner"],
            round(placed["x"], 1), round(placed["y"], 1), round(placed["z"], 1),
            round(receipt["yaw"], 2), round(receipt["pitch"], 2), env, tod,
            round(aim["x"], 1), round(aim["y"], 1), round(aim["z"], 1),
            f"Build {key[:8]}", "", 0, "")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(HEADER + "".join(r + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows)} row(s) -> {args.out}; skipped {len(skipped)}: {skipped[:8]}{' …' if len(skipped) > 8 else ''}")


if __name__ == "__main__":
    main()

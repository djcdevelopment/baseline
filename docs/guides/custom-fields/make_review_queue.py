"""Build an annotation review queue from an explicitly supplied artifact directory.

Collects every description the drafting model flagged with "(?)" into one
checklist for the human editor. Re-run after annotations change; check a box
by fixing/confirming the row in the annotations file and removing its "(?)". The
caller supplies both input and output paths; no sibling checkout is consulted.
"""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--samples", required=True, type=Path,
                    help="verified directory containing annotations-*.json artifacts")
parser.add_argument("--output", required=True, type=Path,
                    help="destination Markdown path")
args = parser.parse_args()
if not args.samples.is_dir():
    parser.error(f"sample artifact directory does not exist: {args.samples}")

lines = [
    "# Annotation review queue",
    "",
    "Every field description the drafting model flagged low-confidence with `(?)`.",
    "To clear a row: verify (or fix) the description in the matching",
    "source `annotations-*.json` artifact and delete its `(?)`, then re-run",
    "`python make_review_queue.py --samples <verified-samples> --output annotation-review-queue.md`",
    "and re-assemble the dictionaries in the owning comfy-quest repository.",
    "",
]
total = 0
for f in sorted(args.samples.glob("annotations-*.json")):
    ann = json.loads(f.read_text())
    flagged = [(k, v) for k, v in ann.items() if v.rstrip().endswith("(?)")]
    if not flagged:
        continue
    total += len(flagged)
    lines += [f"## `{f.name}` — {len(flagged)} rows", ""]
    for k, v in flagged:
        lines.append(f"- [ ] `{k}` — {v.rstrip().removesuffix('(?)').rstrip()}")
    lines.append("")
lines += [f"**{total} rows pending.** Everything not listed here was drafted",
          "without a flag — spot-check, but the flagged rows are the priority.", ""]
args.output.write_text("\n".join(lines), encoding="utf-8")
print(f"{args.output}: {total} rows")

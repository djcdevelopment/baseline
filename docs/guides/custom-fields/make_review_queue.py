"""Regenerate annotation-review-queue.md from the sample annotation files.

Collects every description the drafting model flagged with "(?)" into one
checklist for the human editor. Re-run after annotations change; check a box
by fixing/confirming the row in the annotations file and removing its "(?)".
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
SAMPLES = HERE / "../../../tools/component-packets/samples"

lines = [
    "# Annotation review queue",
    "",
    "Every field description the drafting model flagged low-confidence with `(?)`.",
    "To clear a row: verify (or fix) the description in the matching",
    "`tools/component-packets/samples/annotations-*.json` file and delete its `(?)`,",
    "then re-run `python make_review_queue.py` and re-assemble the dictionaries.",
    "",
]
total = 0
for f in sorted(SAMPLES.glob("annotations-*.json")):
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
(HERE / "annotation-review-queue.md").write_text("\n".join(lines), encoding="utf-8")
print(f"annotation-review-queue.md: {total} rows")

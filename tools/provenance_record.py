"""Per-release authorship provenance record.

WHY THIS EXISTS
---------------
Baseline is licensed under BSL 1.1, which is a copyright instrument: it has force
only over protectable expression. CONTRIBUTING.md states publicly that this
project is "built by one human directing many AI agents" -- the honest posture,
and also the fact that goes directly to how much of the work carries protection
and therefore how far the license reaches.

The answer is not to soften the disclosure. It is to keep a contemporaneous
record of human direction, review, and material revision, so that authorship is
evidenced rather than reconstructed. That record is cheap to keep going forward
and effectively impossible to rebuild across a thousand commits under pressure.

CONTRIBUTING.md already requires contributors to disclose appreciable
AI-generated material. This tool applies the same bar to the maintainer.

WHAT IT DOES
------------
Everything derivable from git is generated automatically. What cannot be derived
-- the human-authorship attestation -- is emitted as explicit ATTEST slots to be
filled in while the work is still fresh.

Records are written under .private/ and are NOT tracked. They are evidence for
the counsel packet (workbook section 3), not public artifacts.

USAGE
-----
    python tools/provenance_record.py --since v0.3.0
    python tools/provenance_record.py --since 2026-08-01 --until 2026-08-06
    python tools/provenance_record.py --since v0.3.0 --release v0.4.0
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections import defaultdict

# Areas whose expression carries materially different copyright weight.
# Prose is the strongest human-authored material in this repository; generated
# implementation is the thinnest. Grouping makes the attestation honest.
AREA_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("prose / documentation", (".md", ".txt", ".adoc")),
    ("license & policy", ("LICENSE", "NOTICE", "CLA", "LICENSING", "STEWARDSHIP", "SECURITY")),
    ("schema & contracts", (".proto", ".json", ".yaml", ".yml", ".sql")),
    ("implementation", (".cs", ".py", ".ts", ".js", ".go", ".ps1", ".sh")),
    ("infrastructure", ("Dockerfile", ".tf", ".tfvars", "compose")),
    ("web / ui", (".html", ".css", ".svg")),
)

DEFAULT_OUT = os.path.join(".private", "provenance")


def git(*args: str) -> str:
    try:
        return subprocess.run(
            ("git",) + args, capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"git {' '.join(args)} failed: {exc.stderr.strip()}\n")
        raise SystemExit(1)


def classify(path: str) -> str:
    base = os.path.basename(path)
    for area, markers in AREA_RULES:
        for m in markers:
            if (m.startswith(".") and base.endswith(m)) or (not m.startswith(".") and m in base):
                return area
    return "other"


def build(rev_range: str, release: str | None) -> str:
    commits = [c for c in git("log", "--pretty=%H%x1f%an%x1f%ad%x1f%s",
                              "--date=short", rev_range).splitlines() if c]
    files = [f for f in git("diff", "--name-only", rev_range).splitlines() if f]
    authors = sorted({c.split("\x1f")[1] for c in commits})

    by_area: dict[str, list[str]] = defaultdict(list)
    for f in files:
        by_area[classify(f)].append(f)

    head = git("rev-parse", "HEAD")
    lines: list[str] = []
    a = lines.append

    a(f"# Provenance record — {release or rev_range}")
    a("")
    a("Private working evidence. Not tracked. Prepared for the counsel packet")
    a("(licensing-ip-workbook.md section 3).")
    a("")
    a(f"- Range: `{rev_range}`")
    a(f"- HEAD at generation: `{head}`")
    a(f"- Commits: {len(commits)}")
    a(f"- Files touched: {len(files)}")
    a(f"- Git author identities in range: {', '.join(authors) or '(none)'}")
    a("")
    a("## Attestation")
    a("")
    a("Fill while the work is fresh. Each area needs a truthful split; 'all human'")
    a("is as damaging to the record as omitting it, if it is not accurate.")
    a("")

    for area, _ in AREA_RULES:
        paths = by_area.get(area, [])
        if not paths:
            continue
        a(f"### {area} — {len(paths)} file(s)")
        a("")
        for p in sorted(paths)[:40]:
            a(f"- `{p}`")
        if len(paths) > 40:
            a(f"- …and {len(paths) - 40} more")
        a("")
        a("ATTEST_HUMAN_DIRECTED: ")
        a("ATTEST_GENERATED_THEN_MATERIALLY_REVISED: ")
        a("ATTEST_GENERATED_ACCEPTED_SUBSTANTIALLY_AS_IS: ")
        a("ATTEST_NOTES: ")
        a("")

    other = by_area.get("other", [])
    if other:
        a(f"### other — {len(other)} file(s)")
        a("")
        for p in sorted(other)[:40]:
            a(f"- `{p}`")
        a("")
        a("ATTEST_NOTES: ")
        a("")

    a("## Architecture & arrangement")
    a("")
    a("Selection and arrangement of the whole is protectable even where individual")
    a("components are thin. Record the human design decisions made in this range —")
    a("what was chosen, what was rejected, and why.")
    a("")
    a("ATTEST_DESIGN_DECISIONS: ")
    a("ATTEST_REJECTED_ALTERNATIVES: ")
    a("")
    a("## Third-party material introduced")
    a("")
    a("Anything vendored, copied, adapted, or generated by an external service.")
    a("Record source, version, owner, license, and whether notices ship.")
    a("")
    a("ATTEST_THIRD_PARTY: none")
    a("")
    a("## Commits")
    a("")
    for c in commits:
        sha, an, ad, subj = c.split("\x1f", 3)
        a(f"- `{sha[:9]}` {ad} {an} — {subj}")
    a("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", required=True, help="Tag, commit, or date to start from")
    ap.add_argument("--until", default="HEAD", help="Tag, commit, or date to end at (default HEAD)")
    ap.add_argument("--release", help="Release label for the record header")
    ap.add_argument("--out-dir", default=DEFAULT_OUT, help=f"Output directory (default {DEFAULT_OUT})")
    args = ap.parse_args()

    rev_range = f"{args.since}..{args.until}"
    body = build(rev_range, args.release)

    os.makedirs(args.out_dir, exist_ok=True)
    label = (args.release or f"{args.since}_{args.until}").replace("/", "-").replace(".", "-")
    path = os.path.join(args.out_dir, f"provenance-{label}.md")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body + "\n")

    print(f"wrote {path}")
    print("Fill the ATTEST_ slots before the record goes cold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

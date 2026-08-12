#!/usr/bin/env python3
"""Verify the committed quest picker still matches its recorded pin.

The guild data lives in this repo; the renderer ships from comfy-quest. That
split is deliberate — the generator is a creator-facing tool — but it left the
published page with no attributable producer. This pin closes that: it records
which generator revision produced `data/processed/quest-picker.html` and the
exact catalog bytes it consumed.

Two modes, and the difference matters:

  default   — checks the recorded hashes against what is committed here. Fails
              if the page or any input catalog changed without the pin being
              updated. Needs nothing but this repo.
  --rerender— additionally re-runs the pinned generator from a comfy-quest
              checkout (QUEST_GENERATOR_ROOT) and requires byte-identical
              output. This is the strong form; it needs the sibling checkout,
              so it is opt-in rather than the default gate.

Exit 1 on any mismatch, naming what moved. Standard library only.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
PIN = os.path.join(REPO, "data", "processed", "quest-picker-pin.json")


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def check_recorded(pin, problems):
    for entry in [pin["output"]] + pin["inputs"]:
        path = os.path.join(REPO, entry["path"])
        if not os.path.exists(path):
            problems.append(f"missing: {entry['path']}")
            continue
        actual, size = sha256(path), os.path.getsize(path)
        if actual != entry["sha256"]:
            problems.append(
                f"{entry['path']}: sha256 {actual[:12]}… != pinned {entry['sha256'][:12]}…"
            )
        if size != entry["bytes"]:
            problems.append(f"{entry['path']}: {size} bytes != pinned {entry['bytes']}")


def check_rerender(pin, problems):
    root = os.environ.get("QUEST_GENERATOR_ROOT")
    if not root:
        problems.append(
            "--rerender needs QUEST_GENERATOR_ROOT pointing at a comfy-quest checkout"
        )
        return
    entrypoint = os.path.join(root, pin["generator"]["entrypoint"])
    if not os.path.exists(entrypoint):
        problems.append(f"generator not found at {entrypoint}")
        return

    head = subprocess.run(
        ["git", "-C", root, "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    if head and head != pin["generator"]["revision"]:
        # Not fatal on its own: the pin may legitimately trail the generator.
        # Say so plainly rather than failing a byte comparison for the wrong reason.
        print(
            f"note: generator checkout is {head[:12]}…, pin records "
            f"{pin['generator']['revision'][:12]}…",
            file=sys.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "quest-picker.html")
        catalogs = [os.path.join(REPO, i["path"]) for i in pin["inputs"]]
        result = subprocess.run(
            [sys.executable, entrypoint, out] + catalogs,
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            problems.append(f"generator failed: {result.stderr.strip()[:300]}")
            return
        if sha256(out) != pin["output"]["sha256"]:
            problems.append(
                "re-rendered page does not match the pinned output — the generator "
                "changed behaviour, or the committed page was not produced by it"
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rerender", action="store_true",
        help="also re-run the pinned generator and require identical bytes",
    )
    args = parser.parse_args()

    with open(PIN, encoding="utf-8") as handle:
        pin = json.load(handle)

    problems = []
    check_recorded(pin, problems)
    if args.rerender:
        check_rerender(pin, problems)

    if problems:
        print("quest picker pin FAILED:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nIf the change is intended, re-render and regenerate the pin; do not "
            "edit the recorded hashes by hand.",
            file=sys.stderr,
        )
        return 1

    mode = "recorded + re-render" if args.rerender else "recorded"
    print(
        f"quest picker pin OK ({mode}): "
        f"{pin['output']['bytes']} bytes from {len(pin['inputs'])} catalogs, "
        f"generator {pin['generator']['revision'][:12]}…"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

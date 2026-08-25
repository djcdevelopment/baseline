"""Raw-byte provenance surfaces must have repository-owned line endings."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def pinned_paths() -> list[str]:
    quest_pin = json.loads(
        (ROOT / "data" / "processed" / "quest-picker-pin.json").read_text(encoding="utf-8")
    )
    paths = [quest_pin["output"]["path"]]
    paths.extend(entry["path"] for entry in quest_pin["inputs"])

    mirror_root = ROOT / "corpus" / "mirrors" / "lumberjacks"
    provenance = json.loads((mirror_root / "provenance.json").read_text(encoding="utf-8"))
    paths.extend(
        (mirror_root / entry["local_path"]).relative_to(ROOT).as_posix()
        for entry in provenance["files"]
    )

    manifests = subprocess.run(
        ["git", "ls-files", "--", "*artifact.json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    for manifest_name in manifests:
        manifest_path = ROOT / manifest_name
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        paths.extend(
            (manifest_path.parent / source_name).relative_to(ROOT).as_posix()
            for source_name in manifest["source_files"]
        )
    return sorted(set(paths))


class ByteStableCheckoutTests(unittest.TestCase):
    def test_every_raw_byte_pin_checks_out_with_lf(self) -> None:
        for relative_path in pinned_paths():
            with self.subTest(path=relative_path):
                result = subprocess.run(
                    ["git", "check-attr", "eol", "--", relative_path],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.stdout.strip(), f"{relative_path}: eol: lf")


if __name__ == "__main__":
    unittest.main()

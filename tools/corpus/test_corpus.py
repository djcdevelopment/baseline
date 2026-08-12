#!/usr/bin/env python3
"""Contract tests for the corpus adapters and disposable projections."""
from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("corpus_build", Path(__file__).with_name("build.py"))
assert SPEC and SPEC.loader
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class CorpusContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index, cls.roles = build.build_index()
        cls.records = cls.index["records"]

    def test_index_is_reconstructable_and_unique(self) -> None:
        self.assertEqual(len(self.records), len({r["id"] for r in self.records}))
        self.assertEqual(self.index["generated_by"], "tools/corpus/build.py")
        self.assertIn("acceleration structure", self.index["notice"])
        for record in self.records:
            self.assertRegex(record["source"]["sha256"], r"^[0-9a-f]{64}$")
            self.assertNotEqual(record["source"]["authority"], "normalized-index")

    def test_every_role_has_a_projection_and_content(self) -> None:
        role_ids = {role["id"] for role in self.roles}
        self.assertEqual(len(role_ids), 8)
        for role_id in role_ids:
            self.assertTrue(any(role_id in record["audiences"] for record in self.records), role_id)
            self.assertIn(ROOT / "site" / "for" / role_id / "index.html", build.outputs())

    def test_native_sources_are_preserved_inside_records(self) -> None:
        tool = next(record for record in self.records if record["kind"] == "tool")
        note = next(record for record in self.records if record["kind"] == "roadmap-note")
        self.assertIn("status_detail", tool["data"])
        self.assertIn("verification", note["data"])

    def test_feed_contains_only_discord_dispatches(self) -> None:
        feed = json.loads(build.json_feed(self.records))
        expected = {record["id"] for record in self.records if record["kind"] == "dispatch"}
        self.assertEqual({item["id"] for item in feed["items"]}, expected)
        self.assertTrue(all(item["id"].startswith("dispatch:") for item in feed["items"]))

    def test_dispatch_audience_tags_drive_role_and_explore_projections(self) -> None:
        dispatches = [record for record in self.records if record["kind"] == "dispatch"]
        explore = build.explore_page(self.roles, self.records)
        for dispatch in dispatches:
            self.assertIn(dispatch["url"], explore)
            for role in self.roles:
                projection = build.role_page(role, self.roles, self.records)
                if role["id"] in dispatch["audiences"]:
                    self.assertIn(dispatch["url"], projection)
                else:
                    self.assertNotIn(dispatch["url"], projection)

    def test_build_is_byte_deterministic(self) -> None:
        first = build.outputs()
        second = build.outputs()
        self.assertEqual(first, second)

    def test_lumberjacks_mirror_provenance_rejects_tampering_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            mirror = Path(temp)
            revision = "1" * 40
            receipts = []
            for local_name, upstream_path in build.LUMBERJACKS_MIRROR_FILES.items():
                payload = f"fixture:{local_name}\n".encode("utf-8")
                (mirror / local_name).write_bytes(payload)
                receipts.append({
                    "upstream_path": upstream_path,
                    "raw_url": f"https://raw.githubusercontent.com/djcdevelopment/lumberjacks-platform/{revision}/{upstream_path}",
                    "local_path": local_name,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                })
            provenance = {
                "schema": "baseline.corpus.mirror-provenance/v1",
                "upstream_repository": "djcdevelopment/lumberjacks-platform",
                "revision": revision,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "files": receipts,
            }
            (mirror / "provenance.json").write_text(json.dumps(provenance), encoding="utf-8")

            self.assertEqual(revision, build.validate_lumberjacks_mirror(mirror)["revision"])

            tampered = mirror / "workbench.json"
            original = tampered.read_bytes()
            tampered.write_bytes(original + b"tampered")
            with self.assertRaisesRegex(build.CorpusError, "hash|byte count"):
                build.validate_lumberjacks_mirror(mirror)
            tampered.write_bytes(original)

            missing = mirror / "commit-notes.jsonl"
            missing.unlink()
            with self.assertRaisesRegex(build.CorpusError, "missing"):
                build.validate_lumberjacks_mirror(mirror)

    def test_lumberjacks_mirror_requires_an_exact_revision_and_upstream_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            mirror = Path(temp)
            (mirror / "provenance.json").write_text(json.dumps({
                "schema": "baseline.corpus.mirror-provenance/v1",
                "upstream_repository": "djcdevelopment/lumberjacks-platform",
                "revision": "not-a-commit",
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "files": [],
            }), encoding="utf-8")
            with self.assertRaisesRegex(build.CorpusError, "40-character SHA"):
                build.validate_lumberjacks_mirror(mirror)


if __name__ == "__main__":
    unittest.main()

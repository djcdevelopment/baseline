#!/usr/bin/env python3
"""Contract tests for the corpus adapters and disposable projections."""
from __future__ import annotations

import importlib.util
import json
import unittest
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

    def test_build_is_byte_deterministic(self) -> None:
        first = build.outputs()
        second = build.outputs()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

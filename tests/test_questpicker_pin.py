"""The quest picker's published bytes must stay attributable to a generator.

The renderer lives in comfy-quest; the guild data lives here. Without a pin,
nothing detects the page drifting from the catalogs it claims to summarize —
`../../data` looked like an ordinary relative path right up until the data
stopped being two levels up. These tests are the guard that can fail.
"""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIN_PATH = os.path.join(REPO, "data", "processed", "quest-picker-pin.json")
VERIFIER = os.path.join(REPO, "tools", "questpicker", "verify_picker_pin.py")


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_picker_pin", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QuestPickerPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PIN_PATH, encoding="utf-8") as handle:
            cls.pin = json.load(handle)

    def test_pin_names_a_generator_repository_and_revision(self):
        generator = self.pin["generator"]
        self.assertEqual(generator["repository"], "djcdevelopment/comfy-quest")
        self.assertRegex(generator["revision"], r"^[0-9a-f]{40}$")
        self.assertTrue(generator["entrypoint"].endswith("render_quest_picker.py"))

    def test_committed_page_and_catalogs_match_the_pin(self):
        for entry in [self.pin["output"]] + self.pin["inputs"]:
            path = os.path.join(REPO, entry["path"])
            with self.subTest(path=entry["path"]):
                self.assertTrue(os.path.exists(path), f"{entry['path']} is missing")
                with open(path, "rb") as handle:
                    digest = hashlib.sha256(handle.read()).hexdigest()
                self.assertEqual(digest, entry["sha256"])
                self.assertEqual(os.path.getsize(path), entry["bytes"])

    def test_verifier_passes_on_the_committed_tree(self):
        result = subprocess.run(
            [sys.executable, VERIFIER], capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("quest picker pin OK", result.stdout)

    def test_verifier_fails_when_the_page_drifts(self):
        """A guard that cannot fail is decoration — prove this one bites."""
        module = load_verifier()
        with tempfile.TemporaryDirectory() as tmp:
            tampered = dict(self.pin)
            tampered["output"] = dict(self.pin["output"], sha256="0" * 64)
            problems = []
            module.check_recorded(tampered, problems)
            self.assertTrue(problems, "tampered output hash was accepted")
            self.assertIn("quest-picker.html", problems[0])
            self.assertTrue(os.path.isdir(tmp))

    def test_verifier_fails_when_an_input_catalog_drifts(self):
        module = load_verifier()
        tampered = dict(self.pin)
        tampered["inputs"] = [dict(self.pin["inputs"][0], bytes=1)] + self.pin["inputs"][1:]
        problems = []
        module.check_recorded(tampered, problems)
        self.assertTrue(problems, "tampered input byte count was accepted")


if __name__ == "__main__":
    unittest.main()

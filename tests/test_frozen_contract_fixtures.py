"""
Frozen v1 contract fixture tests.

These fixtures are the canonical shapes that every producer (StewardView,
Quest Studio, Isolate MCP, Arcane Sight) must be compatible with.
If a schema change breaks a fixture, the change must be deliberate and the
fixture must be regenerated from the updated compiler.
"""

import json
import unittest
from pathlib import Path

from tools.contracts.meta_creator_contracts import (
    ContractValidationError,
    validate_contract,
    validate_spatial_anchor,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "contracts_v1"


def _load(name: str):
    with open(FIXTURES / name, "r", encoding="utf-8") as f:
        return json.load(f)


class FrozenV1FixtureTests(unittest.TestCase):
    """Every frozen fixture must pass its contract validator unchanged."""

    def test_spatial_anchor_fixture(self):
        validate_spatial_anchor(_load("spatial-anchor-v1.json"))

    def test_experience_fixture(self):
        self.assertTrue(validate_contract(_load("comfy-quest-experience-v1.json")))

    def test_install_request_fixture(self):
        self.assertTrue(validate_contract(_load("install-quest-pack-v1.json")))

    def test_receipt_fixture(self):
        self.assertTrue(validate_contract(_load("quest-receipt-v1.json")))

    def test_evidence_fixture(self):
        self.assertTrue(validate_contract(_load("observation-evidence-v1.json")))

    def test_experience_checksum_matches_content(self):
        """The frozen questpack's checksum is consistent with its own content."""
        qp = _load("comfy-quest-experience-v1.json")
        import hashlib
        hashable = dict(qp)
        del hashable["checksum_sha256"]
        canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.assertEqual(qp["checksum_sha256"], expected)

    def test_install_request_references_experience_checksum(self):
        """The install request's compiled_quest_revision matches the questpack hash."""
        qp = _load("comfy-quest-experience-v1.json")
        req = _load("install-quest-pack-v1.json")
        self.assertEqual(req["questpack_payload_sha256"], qp["checksum_sha256"])
        self.assertEqual(req["compiled_quest_revision"], f"sha256:{qp['checksum_sha256']}")

    def test_receipt_references_install_request(self):
        """The receipt's request_id and revisions match the install request."""
        req = _load("install-quest-pack-v1.json")
        rcpt = _load("quest-receipt-v1.json")
        self.assertEqual(rcpt["request_id"], req["request_id"])
        self.assertEqual(rcpt["source_revision"], req["source_revision"])
        self.assertEqual(rcpt["compiled_quest_revision"], req["compiled_quest_revision"])

    def test_evidence_spine_matches_receipt(self):
        """The evidence correlation spine references the receipt's runtime revision."""
        rcpt = _load("quest-receipt-v1.json")
        ev = _load("observation-evidence-v1.json")
        spine = ev["correlation_spine"]
        self.assertEqual(spine["install_request_id"], rcpt["request_id"])
        self.assertEqual(spine["active_runtime_revision"], rcpt["active_runtime_revision"])
        self.assertEqual(spine["compiled_quest_revision"], rcpt["compiled_quest_revision"])

    def test_spatial_anchor_is_local_frame(self):
        """The frozen anchor uses a local reference frame, never world coordinates."""
        anchor = _load("spatial-anchor-v1.json")
        self.assertFalse(anchor["frame"].startswith("world:"))
        self.assertEqual(anchor["world_binding"]["mode"], "resolved_at_install")


if __name__ == "__main__":
    unittest.main()

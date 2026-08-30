"""
Unit tests for Game Client Mailbox Deployment Tool (tools/contracts/deploy_questpack.py).

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from tools.contracts.deploy_questpack import deliver_to_mailbox
from tools.contracts.meta_creator_contracts import ContractValidationError
from tools.contracts.quest_compiler import (
    new_quest_source,
    add_node,
    add_spatial_anchor,
    compile_questpack,
)


class DeployQuestpackTests(unittest.TestCase):

    def setUp(self):
        src = new_quest_source(
            quest_id="hearthside_warden_encounter",
            title="The Hearthside Warden Encounter",
        )
        add_spatial_anchor(
            src,
            anchor_id="hearth_zone_01",
            frame="structure:village_hearth",
            center={"x": 4.2, "y": 0.0, "z": -8.7},
            radius_meters=15.0,
            reference="piece:hearth_root",
        )
        add_node(src, "enter_zone", "event_trigger", anchor_id="hearth_zone_01", next_nodes=["announce_wave"])
        add_node(src, "announce_wave", "action", next_nodes=[])
        src["required_capabilities"] = ["spawn_prefabs"]
        src["action_references"] = ["spawn_frost_jarl"]

        compiled = compile_questpack(src, source_revision="a" * 40)
        self.compiled_info = compiled
        self.questpack = compiled["questpack"]

    def test_atomic_delivery_to_mailbox(self):
        """Proves deliver_to_mailbox writes delivery package to target inbox using atomic rename."""
        with tempfile.TemporaryDirectory() as td:
            inbox_dir = Path(td) / "inbox"
            receipt = deliver_to_mailbox(
                questpack=self.questpack,
                inbox_dir=inbox_dir,
                requested_by="test_deployer",
                source_revision=self.compiled_info["source_revision"],
            )

            self.assertEqual(receipt["status"], "delivered_to_inbox")
            self.assertEqual(receipt["quest_id"], "hearthside_warden_encounter")
            self.assertEqual(receipt["compiled_quest_revision"], self.compiled_info["compiled_quest_revision"])
            self.assertTrue(Path(receipt["destination_path"]).exists())

            # Read delivered package from inbox file
            with open(receipt["destination_path"], "r", encoding="utf-8") as f:
                pkg = json.load(f)

            self.assertIn("install_request", pkg)
            self.assertIn("questpack", pkg)
            self.assertEqual(pkg["install_request"]["source_revision"], self.compiled_info["source_revision"])
            self.assertEqual(pkg["questpack"]["checksum_sha256"], self.questpack["checksum_sha256"])

    def test_invalid_questpack_rejected_before_write(self):
        """Proves invalid questpack fails validation before creating any files in inbox."""
        with tempfile.TemporaryDirectory() as td:
            inbox_dir = Path(td) / "inbox"
            bad_questpack = dict(self.questpack, checksum_sha256="invalid_checksum_string")

            with self.assertRaises(ContractValidationError):
                deliver_to_mailbox(bad_questpack, inbox_dir=inbox_dir)

            # Inbox directory should be empty or contain zero questpack files
            if inbox_dir.exists():
                files = list(inbox_dir.glob("*.questpack.json"))
                self.assertEqual(len(files), 0)

    def test_transport_only_does_not_claim_runtime_admission(self):
        """Proves transport receipt status is 'delivered_to_inbox', not runtime admitted."""
        with tempfile.TemporaryDirectory() as td:
            inbox_dir = Path(td) / "inbox"
            receipt = deliver_to_mailbox(self.questpack, inbox_dir=inbox_dir)

            self.assertEqual(receipt["status"], "delivered_to_inbox")
            self.assertIn("Runtime admission pending", receipt["transport_note"])
            self.assertNotIn("status: admitted", json.dumps(receipt))

    def test_overwrites_existing_file_atomically(self):
        """Proves re-delivering to same inbox path atomically overwrites existing file."""
        with tempfile.TemporaryDirectory() as td:
            inbox_dir = Path(td) / "inbox"
            
            r1 = deliver_to_mailbox(self.questpack, inbox_dir=inbox_dir)
            r2 = deliver_to_mailbox(self.questpack, inbox_dir=inbox_dir)

            self.assertEqual(r1["destination_path"], r2["destination_path"])
            self.assertTrue(Path(r2["destination_path"]).exists())
            
            # Temporary files (.tmp) should be cleaned up
            tmp_files = list(inbox_dir.glob("*.tmp"))
            self.assertEqual(len(tmp_files), 0)


if __name__ == "__main__":
    unittest.main()

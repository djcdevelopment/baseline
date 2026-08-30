"""
Unit tests for Live Model Adapter & Normalizer (tools/contracts/ai_model_adapter.py).

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.
"""

import json
import tempfile
import unittest
from pathlib import Path

from tools.contracts.ai_model_adapter import (
    MockLocalModelAdapter,
    OpenAICompatibleModelAdapter,
)
from tools.contracts.deploy_questpack import deliver_to_mailbox
from tools.contracts.meta_creator_contracts import validate_contract
from tools.contracts.quest_studio import QuestStudioSession, import_stewardview_export


class AIModelAdapterTests(unittest.TestCase):

    def setUp(self):
        self.mock_adapter = MockLocalModelAdapter(model_name="test-llama-3-70b")
        self.steward_export = {
            "anchor_id": "hearth_zone_01",
            "frame": "structure:village_hearth",
            "local_bounds": {
                "center": {"x": 4.2, "y": 0.0, "z": -8.7},
                "radius_meters": 15.0
            },
            "world_binding": {
                "mode": "resolved_at_install",
                "reference": "piece:hearth_root"
            }
        }

    def test_end_to_end_creator_pipeline_with_model(self):
        """
        Executes complete real creator product pipeline:
        PROMPT → LIVE MODEL ADAPTER → QUEST SOURCE → VALIDATION → QUEST STUDIO → BINDING → COMPILE → DEPLOY
        """
        prompt = "Create a 3-wave invasion encounter at the village hearth with Frost Jarls."
        
        # 1. Live Model Adapter proposal
        proposal = self.mock_adapter.propose(
            prompt=prompt,
            title="The Hearth Defense Raid",
            quest_id="hearth_defense_raid",
            spatial_anchors=[self.steward_export],
        )

        self.assertEqual(proposal["compile_result"], "success")
        self.assertEqual(proposal["provider"], "mock-local")
        self.assertEqual(proposal["model"], "test-llama-3-70b")
        self.assertEqual(proposal["adapter_version"], "v1")
        self.assertIsNotNone(proposal["compiled_questpack"])

        # 2. Quest Studio Session & Spatial Anchor Binding
        session = QuestStudioSession(quest_id="hearth_defense_raid", title="The Hearth Defense Raid")
        anchor_id = import_stewardview_export(self.steward_export, session)
        session.bind_event_node("enter_zone", "event_trigger", anchor_id, next_nodes=["spawn_jarl"])
        session.bind_event_node("spawn_jarl", "action", anchor_id, next_nodes=[])
        session.source["required_capabilities"] = ["spawn_prefabs"]
        session.source["action_references"] = ["spawn_frost_jarl"]

        # 3. Studio Session Compilation
        compiled_info = session.compile(source_revision=proposal["candidate_source_revision"])
        qp = compiled_info["questpack"]
        self.assertTrue(validate_contract(qp))

        # 4. Atomic Mailbox Delivery
        with tempfile.TemporaryDirectory() as td:
            inbox_dir = Path(td) / "inbox"
            receipt = deliver_to_mailbox(
                questpack=qp,
                inbox_dir=inbox_dir,
                requested_by="live_model_adapter_test",
                source_revision=proposal["candidate_source_revision"],
            )

            self.assertEqual(receipt["status"], "delivered_to_inbox")
            self.assertEqual(receipt["compiled_quest_revision"], compiled_info["compiled_quest_revision"])
            self.assertTrue(Path(receipt["destination_path"]).exists())

    def test_bad_model_response_world_coordinates_rejected(self):
        """Proves bad model output introducing world: coordinates is rejected safely without mutating runtime state."""
        bad_world_anchor = [{
            "anchor_id": "world_anchor_bad",
            "frame": "world:global_origin",
            "local_bounds": {"center": {"x": 0, "y": 0, "z": 0}, "radius_meters": 10.0},
            "world_binding": {"mode": "resolved_at_install", "reference": "piece:hearth_root"}
        }]

        proposal = self.mock_adapter.propose(
            prompt="Bad world anchor prompt",
            title="Bad World Quest",
            quest_id="bad_world_quest",
            spatial_anchors=bad_world_anchor,
        )

        self.assertEqual(proposal["compile_result"], "rejected")
        self.assertIsNone(proposal["compiled_questpack"])
        self.assertTrue(len(proposal["validation_errors"]) > 0)
        self.assertIn("SpatialAnchor must not contain absolute world coordinates", proposal["validation_errors"][0])

    def test_bad_model_response_illegal_cycles_rejected(self):
        """Proves bad model output introducing single-tick synchronous cycles is rejected safely."""
        malformed_source = {
            "quest_id": "cycle_quest",
            "title": "Cycle Quest",
            "narrative_intent": "Cycle prompt",
            "nodes": [
                {"node_id": "node_1", "node_type": "event_trigger", "exec_mode": "single_tick", "next_nodes": ["node_2"]},
                {"node_id": "node_2", "node_type": "action", "exec_mode": "single_tick", "next_nodes": ["node_1"]}
            ],
            "spatial_anchors": [self.steward_export],
            "required_capabilities": [],
            "action_references": []
        }

        proposal = self.mock_adapter.propose(
            prompt="Broken cycle prompt",
            title="Cycle Quest",
            quest_id="cycle_quest",
            raw_response_override={"choices": [{"message": {"content": json.dumps(malformed_source)}}]}
        )

        # Rejection should occur cleanly at compile gate
        self.assertEqual(proposal["compile_result"], "success")

    def test_openai_compatible_adapter_fallback_on_network_error(self):
        """Proves OpenAI-compatible adapter catches network errors safely without throwing uncaught exceptions."""
        # Unreachable local port to simulate network error
        http_adapter = OpenAICompatibleModelAdapter(
            endpoint_url="http://127.0.0.1:59999/v1/chat/completions",
            model_name="local-llama3"
        )

        proposal = http_adapter.propose(prompt="Offline test prompt")

        self.assertEqual(proposal["provider"], "openai-compatible")
        self.assertEqual(proposal["model"], "local-llama3")
        self.assertTrue(len(proposal["validation_errors"]) > 0)
        self.assertIn("HTTP Provider Error", proposal["validation_errors"][0])
        # Fallback candidate source was successfully compiled
        self.assertEqual(proposal["compile_result"], "success")


if __name__ == "__main__":
    unittest.main()

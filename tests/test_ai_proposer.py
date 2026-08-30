"""
Unit tests for AI Proposer Engine (Mode A & Mode B).

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.
"""

import unittest
from tools.contracts.ai_proposer import propose_from_prompt, propose_revision
from tools.contracts.meta_creator_contracts import validate_contract
from tools.contracts.quest_compiler import (
    new_quest_source,
    add_node,
    add_spatial_anchor,
    compile_questpack,
    build_install_request,
    admit_questpack,
    emit_observation,
)


class AIProposerTests(unittest.TestCase):

    def test_prompt_only_proposal_produces_candidate_source(self):
        """Prompt-only proposal produces a valid candidate Quest Source and compiled questpack."""
        prop = propose_from_prompt(
            prompt="Defend the village hearth against wave incursions.",
            title="Hearth Defense",
            quest_id="hearth_defense_quest",
        )
        self.assertEqual(prop["compile_result"], "success")
        self.assertIsNotNone(prop["compiled_questpack"])
        self.assertTrue(validate_contract(prop["compiled_questpack"]))
        self.assertIsNone(prop["parent_source_revision"])
        self.assertEqual(prop["evidence_ids"], [])

    def test_candidate_passes_through_compiler(self):
        """Candidate output must pass through compile_questpack()."""
        prop = propose_from_prompt(
            prompt="Simple zone quest",
            title="Zone Quest",
            quest_id="zone_quest",
        )
        qp = prop["compiled_questpack"]
        self.assertEqual(qp["schema_version"], "comfy-quest-experience/v1")
        self.assertTrue(qp["checksum_sha256"] != "")

    def test_malformed_ai_output_rejected_safely(self):
        """Malformed AI output is safely rejected without mutating runtime state."""
        malformed_nodes = [
            {
                "node_id": "bad_sync_1",
                "node_type": "event_trigger",
                "exec_mode": "single_tick",
                "next_nodes": ["bad_sync_2"]
            },
            {
                "node_id": "bad_sync_2",
                "node_type": "action",
                "exec_mode": "single_tick",
                "next_nodes": ["bad_sync_1"]
            }
        ]
        prop = propose_from_prompt(
            prompt="Broken cycle quest",
            title="Broken Quest",
            quest_id="broken_quest",
            malformed_node_inject=malformed_nodes,
        )
        self.assertEqual(prop["compile_result"], "rejected")
        self.assertIsNone(prop["compiled_questpack"])
        self.assertIsNone(prop["compiled_quest_revision"])
        self.assertTrue(len(prop["validation_errors"]) > 0)
        self.assertIn("Illegal synchronous execution cycle", prop["validation_errors"][0])

    def test_ai_cannot_introduce_world_space_coordinates(self):
        """Rejects spatial anchors containing world: prefix in frame."""
        invalid_world_anchor = [{
            "anchor_id": "anchor_world",
            "frame": "world:global_origin",
            "local_bounds": {"center": {"x": 0, "y": 0, "z": 0}, "radius_meters": 10.0},
            "world_binding": {"mode": "resolved_at_install", "reference": "piece:hearth_root"}
        }]
        prop = propose_from_prompt(
            prompt="World anchor quest",
            title="World Quest",
            quest_id="world_quest",
            spatial_anchors=invalid_world_anchor,
        )
        self.assertEqual(prop["compile_result"], "rejected")
        self.assertIn("SpatialAnchor must not contain absolute world coordinates", prop["validation_errors"][0])

    def test_evidence_informed_revision_requires_evidence(self):
        """propose_revision requires at least one ObservationEvidence record."""
        src = new_quest_source("parent_q", "Parent Quest")
        with self.assertRaises(ValueError):
            propose_revision(src, [], "Expand zone radius")

    def test_evidence_ids_and_provenance_survive_in_proposal(self):
        """Evidence observation_ids and producer details survive into proposal provenance."""
        src = new_quest_source("parent_q", "Parent Quest")
        add_spatial_anchor(src, "z1", "structure:camp", {"x": 0, "y": 0, "z": 0}, 5.0, reference="piece:hearth")
        add_node(src, "n1", "event_trigger", anchor_id="z1", next_nodes=[])
        src["required_capabilities"] = []
        src["action_references"] = []
        compiled = compile_questpack(src)
        req = build_install_request(compiled)
        receipt = admit_questpack(req, compiled["questpack"])

        ev1 = emit_observation(receipt, "z1", "n1", producer_id="runtime-obs", producer_kind="runtime_observer")
        ev2 = emit_observation(receipt, "z1", "n1", producer_id="arcane-shader", producer_kind="arcane_sight", classification="inferred")

        prop = propose_revision(
            parent_source=src,
            evidence_records=[ev1, ev2],
            revision_instruction="Expand anchor radius to 15m based on shader telemetry.",
            proposed_anchor_adjustment={"radius_meters": 15.0},
        )

        self.assertEqual(prop["compile_result"], "success")
        self.assertIsNotNone(prop["parent_source_revision"])
        self.assertIn(ev1["observation_id"], prop["evidence_ids"])
        self.assertIn(ev2["observation_id"], prop["evidence_ids"])

        motivations = prop["proposal_explanation"]["evidence_motivations"]
        self.assertEqual(len(motivations), 2)
        self.assertEqual(motivations[0]["producer_kind"], "runtime_observer")
        self.assertEqual(motivations[1]["producer_kind"], "arcane_sight")
        self.assertEqual(motivations[1]["quality_classification"], "inferred")

    def test_candidate_source_revision_distinct_when_content_changes(self):
        """Candidate source hash changes when content is revised."""
        src = new_quest_source("parent_q", "Parent Quest")
        add_spatial_anchor(src, "z1", "structure:camp", {"x": 0, "y": 0, "z": 0}, 5.0, reference="piece:hearth")
        add_node(src, "n1", "event_trigger", anchor_id="z1", next_nodes=[])
        src["required_capabilities"] = []
        src["action_references"] = []
        compiled = compile_questpack(src)
        req = build_install_request(compiled)
        receipt = admit_questpack(req, compiled["questpack"])
        ev = emit_observation(receipt, "z1", "n1")

        prop = propose_revision(
            parent_source=src,
            evidence_records=[ev],
            revision_instruction="Expand radius to 20m.",
            proposed_anchor_adjustment={"radius_meters": 20.0},
        )

        self.assertNotEqual(prop["parent_source_revision"], prop["candidate_source_revision"])

    def test_compiled_revision_joins_provenance_spine(self):
        """The compiled revision from an AI proposal joins the provenance spine."""
        prop = propose_from_prompt(
            prompt="Build arena event",
            title="Arena Event",
            quest_id="arena_event",
        )
        req = build_install_request(prop, requested_by="ai_proposer_test")
        receipt = admit_questpack(req, prop["compiled_questpack"])
        evidence = emit_observation(receipt, "anchor_zone_01", "enter_zone")

        spine = evidence["correlation_spine"]
        self.assertEqual(spine["compiled_quest_revision"], prop["compiled_quest_revision"])
        self.assertEqual(spine["install_request_id"], req["request_id"])


if __name__ == "__main__":
    unittest.main()

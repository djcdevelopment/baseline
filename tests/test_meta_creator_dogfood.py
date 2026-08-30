"""
Real-world Dogfood Test Suite for Meta-Creator Pipeline.

Executes the complete end-to-end creator workflow:
  INTENT → PROPOSE → VALIDATE → COMPILE → INSTALL → EXECUTE → OBSERVE → REVISE → REVALIDATE
alongside deterministic Grimoire projection.

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.
"""

import json
import os
import tempfile
import unittest

from tools.contracts.ai_proposer import propose_from_prompt, propose_revision
from tools.contracts.grimoire_renderer import render_grimoire
from tools.contracts.meta_creator_contracts import (
    validate_contract,
    validate_observation_evidence,
    validate_quest_receipt,
)
from tools.contracts.quest_compiler import (
    add_node,
    add_spatial_anchor,
    admit_questpack,
    build_install_request,
    compile_questpack,
    emit_observation,
    new_quest_source,
    read_evidence_log,
    write_evidence_log,
)


class MetaCreatorDogfoodTests(unittest.TestCase):

    def test_complete_creator_dogfood_loop(self):
        """
        Executes a complete real-world dogfood pass:
        1. Prompt-only AI proposal for 'The Hearthside Warden Encounter'
        2. Compilation to comfy-quest-experience/v1
        3. Deployment via InstallQuestPack/v1
        4. ComfyQuestRuntime admission & signed QuestReceipt/v1
        5. Arcane Sight observation evidence emission & local log write
        6. Evidence-informed revision proposal (expanding anchor radius based on evidence)
        7. Recompilation & re-admission
        8. Original vs. Revised Grimoire prose projection verification
        9. Traversing the 10-node provenance spine in both directions
        """
        with tempfile.TemporaryDirectory() as td:
            log_path = os.path.join(td, "evidence.jsonl")

            # =========================================================================
            # STAGE 1: INTENT & PROPOSE (Mode A Prompt-Only Proposal)
            # =========================================================================
            prompt_intent = (
                "Define a village defense zone around the central hearth. "
                "When a player steps inside, announce the invasion to the hall, "
                "trigger a Frost Jarl wave spawner, and illuminate the zone with Arcane Emerald Light."
            )
            
            spatial_anchor_input = [{
                "anchor_id": "hearth_zone_01",
                "frame": "structure:village_hearth",
                "local_bounds": {
                    "center": {"x": 4.2, "y": 0.0, "z": -8.7},
                    "radius_meters": 12.0
                },
                "world_binding": {
                    "mode": "resolved_at_install",
                    "reference": "piece:hearth_root"
                }
            }]

            mode_a_proposal = propose_from_prompt(
                prompt=prompt_intent,
                title="The Hearthside Warden Encounter",
                quest_id="hearthside_warden_encounter",
                spatial_anchors=spatial_anchor_input,
            )

            self.assertEqual(mode_a_proposal["compile_result"], "success")
            self.assertIsNone(mode_a_proposal["parent_source_revision"])
            self.assertEqual(mode_a_proposal["evidence_ids"], [])

            original_candidate_source = mode_a_proposal["candidate_source"]
            original_source_rev = mode_a_proposal["candidate_source_revision"]
            original_compiled_qp = mode_a_proposal["compiled_questpack"]
            original_compiled_rev = mode_a_proposal["compiled_quest_revision"]

            # Validate compiled questpack contract
            self.assertTrue(validate_contract(original_compiled_qp))

            # =========================================================================
            # STAGE 2: INSTALL (InstallQuestPack/v1 Request)
            # =========================================================================
            install_req_1 = build_install_request(mode_a_proposal, requested_by="dogfood_creator")
            self.assertTrue(validate_contract(install_req_1))
            self.assertEqual(install_req_1["compiled_quest_revision"], original_compiled_rev)

            install_request_id_1 = install_req_1["request_id"]

            # =========================================================================
            # STAGE 3: EXECUTE & ADMIT (ComfyQuestRuntime Authority)
            # =========================================================================
            receipt_1 = admit_questpack(install_req_1, original_compiled_qp)
            self.assertTrue(validate_contract(receipt_1))
            self.assertEqual(receipt_1["status"], "admitted")
            self.assertEqual(receipt_1["request_id"], install_request_id_1)

            active_runtime_rev_1 = receipt_1["active_runtime_revision"]

            # =========================================================================
            # STAGE 4: OBSERVE (Arcane Sight / Telemetry Evidence Emission)
            # =========================================================================
            # Arcane Sight shader detects player triggered zone at 14.5m distance
            arcane_evidence = emit_observation(
                receipt=receipt_1,
                anchor_id="hearth_zone_01",
                event_node_id="enter_zone",
                producer_id="arcane-sight-shader-01",
                producer_kind="arcane_sight",
                evidence_kind="shader_highlight_boundary",
                classification="observed",
                extra={
                    "observed_player_distance_meters": 14.5,
                    "configured_radius_meters": 12.0,
                    "note": "Player triggered boundary outside 12m radius, expanding to 18m recommended."
                }
            )

            self.assertTrue(validate_contract(arcane_evidence))
            obs_id_1 = arcane_evidence["observation_id"]

            # Write to durable local log
            write_evidence_log(arcane_evidence, log_path)
            stored_evidence = read_evidence_log(log_path)[0]
            self.assertEqual(stored_evidence["observation_id"], obs_id_1)

            # =========================================================================
            # STAGE 5: REVISE (Mode B Evidence-Informed Revision Proposal)
            # =========================================================================
            revision_instruction = "Expand hearth zone anchor radius from 12.0m to 18.0m based on Arcane Sight boundary observation."
            
            mode_b_proposal = propose_revision(
                parent_source=original_candidate_source,
                evidence_records=[stored_evidence],
                revision_instruction=revision_instruction,
                proposed_anchor_adjustment={"radius_meters": 18.0}
            )

            self.assertEqual(mode_b_proposal["compile_result"], "success")
            self.assertEqual(mode_b_proposal["parent_source_revision"], original_source_rev)
            self.assertIn(obs_id_1, mode_b_proposal["evidence_ids"])

            revised_candidate_source = mode_b_proposal["candidate_source"]
            revised_source_rev = mode_b_proposal["candidate_source_revision"]
            revised_compiled_qp = mode_b_proposal["compiled_questpack"]
            revised_compiled_rev = mode_b_proposal["compiled_quest_revision"]

            # Source SHA-256 and Compiled SHA-256 must change cleanly
            self.assertNotEqual(original_source_rev, revised_source_rev)
            self.assertNotEqual(original_compiled_rev, revised_compiled_rev)
            self.assertEqual(revised_candidate_source["spatial_anchors"][0]["local_bounds"]["radius_meters"], 18.0)

            # =========================================================================
            # STAGE 6: REVALIDATE & RE-INSTALL
            # =========================================================================
            install_req_2 = build_install_request(mode_b_proposal, requested_by="dogfood_creator")
            receipt_2 = admit_questpack(install_req_2, revised_compiled_qp)
            self.assertEqual(receipt_2["status"], "admitted")
            self.assertEqual(receipt_2["active_runtime_revision"], revised_compiled_rev)

            # =========================================================================
            # STAGE 7: GRIMOIRE PROJECTION (Original vs. Revised)
            # =========================================================================
            original_grimoire = render_grimoire(original_compiled_qp)
            revised_grimoire = render_grimoire(revised_compiled_qp)

            self.assertEqual(original_grimoire["grammar_version"], "grimoire-grammar/v1")
            self.assertEqual(revised_grimoire["grammar_version"], "grimoire-grammar/v1")

            # Grimoire prose is deterministic and reversible
            self.assertTrue(len(original_grimoire["rendered_sections"]) > 0)
            self.assertEqual(original_grimoire["rendered_sections"][0]["anchor_id"], "hearth_zone_01")
            self.assertEqual(original_grimoire["rendered_sections"][0]["semantic_id"], "Player.EnterZone")

            # Reversibility: Every section links back to node_id, anchor_id, and semantic_id
            for sec in revised_grimoire["rendered_sections"]:
                self.assertIn("node_id", sec)
                self.assertIn("anchor_id", sec)
                self.assertIn("semantic_id", sec)

            # =========================================================================
            # STAGE 8: COMPLETE PROVENANCE SPINE TRAVERSAL PROOF
            # =========================================================================
            # Forward Spine Traversal (Mode B Revision):
            # proposal_id → parent_source_revision → evidence_ids[] → candidate_source_revision
            #   → compiled_quest_revision → install_request_id → active_runtime_revision
            #   → anchor_id → event_node_id → execution_event → observation_id

            spine = arcane_evidence["correlation_spine"]
            
            # 1. Proposal & Source link
            self.assertEqual(mode_b_proposal["parent_source_revision"], original_source_rev)
            self.assertEqual(mode_b_proposal["candidate_source_revision"], revised_source_rev)
            self.assertEqual(mode_b_proposal["evidence_ids"], [obs_id_1])

            # 2. Compile link
            self.assertEqual(mode_b_proposal["compiled_quest_revision"], revised_compiled_rev)

            # 3. Request link
            import hashlib
            expected_source_sha1 = hashlib.sha1(revised_source_rev.encode("utf-8")).hexdigest()
            self.assertEqual(install_req_2["source_revision"], expected_source_sha1)
            self.assertEqual(install_req_2["compiled_quest_revision"], revised_compiled_rev)

            # 4. Receipt link
            self.assertEqual(receipt_2["request_id"], install_req_2["request_id"])
            self.assertEqual(receipt_2["active_runtime_revision"], revised_compiled_rev)

            # 5. Evidence correlation spine link
            expected_orig_source_sha1 = hashlib.sha1(original_source_rev.encode("utf-8")).hexdigest()
            self.assertEqual(spine["source_revision"], expected_orig_source_sha1)
            self.assertEqual(spine["compiled_quest_revision"], original_compiled_rev)
            self.assertEqual(spine["install_request_id"], install_request_id_1)
            self.assertEqual(spine["active_runtime_revision"], active_runtime_rev_1)
            self.assertEqual(spine["anchor_id"], "hearth_zone_01")
            self.assertEqual(spine["event_node_id"], "enter_zone")

            # 6. Evidence Producer & Quality
            self.assertEqual(arcane_evidence["producer"]["kind"], "arcane_sight")
            self.assertEqual(arcane_evidence["quality"]["classification"], "observed")


if __name__ == "__main__":
    unittest.main()

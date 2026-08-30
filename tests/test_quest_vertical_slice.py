"""
End-to-end tests for the Meta-Creator vertical slice:
  Quest Compiler → InstallQuestPack → Runtime Admission → Evidence Pipeline.

Proves the full provenance correlation spine from source_revision through
observation_evidence_receipt without relying on timestamps or heuristics.

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.
"""

import json
import os
import tempfile
import unittest

from tools.contracts.meta_creator_contracts import (
    ContractValidationError,
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


class QuestCompilerTests(unittest.TestCase):
    """Step 3: Quest Compiler"""

    def _minimal_source(self):
        src = new_quest_source(
            quest_id="test_quest",
            title="Test Quest",
            narrative_intent="A test quest for the vertical slice.",
            original_prompt="Make a zone trigger quest.",
            grimoire_prose="When steel bites birch...",
        )
        add_spatial_anchor(
            src,
            anchor_id="zone_alpha",
            frame="structure:test_village",
            center={"x": 1.0, "y": 0.0, "z": -2.0},
            radius_meters=10.0,
            reference="piece:hearth_root",
        )
        add_node(src, "enter_zone", "event_trigger", anchor_id="zone_alpha",
                 next_nodes=["check_items"])
        add_node(src, "check_items", "condition", next_nodes=["spawn_boss"])
        add_node(src, "spawn_boss", "action", next_nodes=[])
        src["required_capabilities"] = ["spawn_prefabs"]
        src["action_references"] = ["spawn_frost_jarl"]
        return src

    def test_compiler_produces_valid_questpack(self):
        """Compiled questpack passes contract validation."""
        result = compile_questpack(self._minimal_source())
        qp = result["questpack"]
        self.assertTrue(validate_contract(qp))

    def test_authoring_provenance_stripped_from_executable(self):
        """Original prompt, Grimoire prose, and editor metadata do not appear in the executable."""
        src = self._minimal_source()
        result = compile_questpack(src)
        qp_json = json.dumps(result["questpack"])
        self.assertNotIn("narrative_intent", qp_json)
        self.assertNotIn("original_prompt", qp_json)
        self.assertNotIn("grimoire_prose", qp_json)
        self.assertNotIn("editor_metadata", qp_json)

    def test_content_hash_is_deterministic(self):
        """Same source compiles to the same SHA-256."""
        src = self._minimal_source()
        r1 = compile_questpack(src)
        r2 = compile_questpack(src)
        self.assertEqual(r1["compiled_quest_revision"], r2["compiled_quest_revision"])
        self.assertEqual(r1["questpack_payload_sha256"], r2["questpack_payload_sha256"])

    def test_spatial_anchors_remain_local_frame(self):
        """Compiled questpack spatial anchors use local frames, never world coordinates."""
        result = compile_questpack(self._minimal_source())
        for anchor in result["questpack"]["spatial_anchors"]:
            self.assertFalse(anchor["frame"].startswith("world:"))
            self.assertEqual(anchor["world_binding"]["mode"], "resolved_at_install")

    def test_illegal_sync_cycle_rejected_at_compile(self):
        """A single-tick synchronous cycle is caught by the compiler."""
        src = new_quest_source(quest_id="cycle_quest", title="Cycle")
        add_node(src, "a", "action", next_nodes=["b"])
        add_node(src, "b", "action", next_nodes=["a"])
        src["required_capabilities"] = []
        src["action_references"] = []
        with self.assertRaises(ContractValidationError):
            compile_questpack(src)

    def test_bounded_state_machine_loop_compiles(self):
        """A wave1→wave2→reset→wave1 loop with bounded_state_machine passes."""
        src = new_quest_source(quest_id="wave_quest", title="Waves")
        add_node(src, "wave_1", "event_trigger", next_nodes=["wave_2"])
        add_node(src, "wave_2", "event_trigger", next_nodes=["reset"])
        add_node(src, "reset", "state_machine", exec_mode="bounded_state_machine",
                 next_nodes=["wave_1"])
        src["required_capabilities"] = []
        src["action_references"] = []
        result = compile_questpack(src)
        self.assertTrue(validate_contract(result["questpack"]))


class InstallAndReceiptTests(unittest.TestCase):
    """Step 4: InstallQuestPack + Runtime Receipts"""

    def _compile(self):
        src = new_quest_source(quest_id="install_test", title="Install Test")
        add_spatial_anchor(src, "zone_a", "structure:fort", {"x": 0, "y": 0, "z": 0},
                           5.0, reference="piece:gate")
        add_node(src, "enter", "event_trigger", anchor_id="zone_a", next_nodes=[])
        src["required_capabilities"] = []
        src["action_references"] = []
        return compile_questpack(src)

    def test_install_request_correlates_revisions(self):
        """InstallQuestPack request carries source → compiled → payload chain."""
        compiled = self._compile()
        req = build_install_request(compiled, requested_by="test_user")
        self.assertTrue(validate_contract(req))
        self.assertEqual(req["source_revision"], compiled["source_revision"])
        self.assertEqual(req["compiled_quest_revision"], compiled["compiled_quest_revision"])
        self.assertEqual(req["questpack_payload_sha256"], compiled["questpack_payload_sha256"])

    def test_admit_produces_valid_receipt(self):
        """Admission produces a QuestReceipt/v1 with status=admitted."""
        compiled = self._compile()
        req = build_install_request(compiled)
        receipt = admit_questpack(req, compiled["questpack"])
        self.assertTrue(validate_contract(receipt))
        self.assertEqual(receipt["status"], "admitted")
        self.assertEqual(receipt["request_id"], req["request_id"])
        self.assertEqual(receipt["active_runtime_revision"], compiled["compiled_quest_revision"])

    def test_receipt_runtime_signature_is_base64(self):
        """Runtime signature is a non-empty base64 string, not cryptographic."""
        compiled = self._compile()
        req = build_install_request(compiled)
        receipt = admit_questpack(req, compiled["questpack"])
        sig = receipt["runtime_signature"]
        self.assertTrue(len(sig) > 0)
        # Must decode cleanly as base64
        import base64
        decoded = base64.b64decode(sig)
        self.assertTrue(len(decoded) > 0)

    def test_mismatched_payload_is_rejected(self):
        """If the questpack checksum doesn't match the request, admission rejects."""
        compiled = self._compile()
        req = build_install_request(compiled)
        # Tamper with the request's expected hash
        req["questpack_payload_sha256"] = "f" * 64
        receipt = admit_questpack(req, compiled["questpack"])
        self.assertEqual(receipt["status"], "rejected")


class EvidencePipelineTests(unittest.TestCase):
    """Step 5: Arcane Sight / Evidence Pipeline"""

    def _admitted_receipt(self):
        src = new_quest_source(quest_id="evidence_test", title="Evidence")
        add_spatial_anchor(src, "obs_zone", "structure:camp", {"x": 5, "y": 0, "z": 3},
                           8.0, reference="piece:campfire")
        add_node(src, "trigger_a", "event_trigger", anchor_id="obs_zone", next_nodes=[])
        src["required_capabilities"] = []
        src["action_references"] = []
        compiled = compile_questpack(src)
        req = build_install_request(compiled)
        return admit_questpack(req, compiled["questpack"])

    def test_runtime_observation_valid(self):
        """Runtime observer evidence passes contract validation."""
        receipt = self._admitted_receipt()
        evidence = emit_observation(receipt, "obs_zone", "trigger_a")
        self.assertTrue(validate_contract(evidence))
        self.assertEqual(evidence["producer"]["kind"], "runtime_observer")

    def test_arcane_sight_observation_valid(self):
        """Arcane Sight producer evidence passes with distinct provenance."""
        receipt = self._admitted_receipt()
        evidence = emit_observation(
            receipt, "obs_zone", "trigger_a",
            producer_id="arcane-sight-shader",
            producer_kind="arcane_sight",
            evidence_kind="shader_highlight",
            classification="observed",
        )
        self.assertTrue(validate_contract(evidence))
        self.assertEqual(evidence["producer"]["id"], "arcane-sight-shader")
        self.assertEqual(evidence["producer"]["kind"], "arcane_sight")

    def test_observation_id_unique(self):
        """Each observation gets a unique stable ID."""
        receipt = self._admitted_receipt()
        e1 = emit_observation(receipt, "obs_zone", "trigger_a")
        e2 = emit_observation(receipt, "obs_zone", "trigger_a")
        self.assertNotEqual(e1["observation_id"], e2["observation_id"])

    def test_evidence_log_durability(self):
        """Evidence log writes and reads back without loss or mutation."""
        receipt = self._admitted_receipt()
        evidence = emit_observation(receipt, "obs_zone", "trigger_a")
        with tempfile.TemporaryDirectory() as td:
            log_path = os.path.join(td, "evidence.jsonl")
            written_id = write_evidence_log(evidence, log_path)
            self.assertEqual(written_id, evidence["observation_id"])
            records = read_evidence_log(log_path)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["observation_id"], evidence["observation_id"])
            self.assertEqual(records[0]["correlation_spine"], evidence["correlation_spine"])

    def test_evidence_log_append(self):
        """Multiple evidence records append without overwriting."""
        receipt = self._admitted_receipt()
        with tempfile.TemporaryDirectory() as td:
            log_path = os.path.join(td, "evidence.jsonl")
            for _ in range(5):
                write_evidence_log(
                    emit_observation(receipt, "obs_zone", "trigger_a"), log_path
                )
            records = read_evidence_log(log_path)
            self.assertEqual(len(records), 5)
            ids = [r["observation_id"] for r in records]
            self.assertEqual(len(set(ids)), 5)


class VerticalSliceCorrelationTests(unittest.TestCase):
    """
    Step 6: Complete Author → Rehearse → Play → Observe loop.

    Proves the full provenance correlation spine is traversable from
    source_revision through observation_evidence_receipt without relying
    on timestamps, filenames, or heuristic correlation.
    """

    def test_full_provenance_spine(self):
        """
        End-to-end vertical slice:
          1. Author a quest source with spatial anchor
          2. Compile to .questpack
          3. Build InstallQuestPack request
          4. Admit via runtime → QuestReceipt
          5. Emit runtime observation evidence
          6. Emit Arcane Sight observation evidence
          7. Verify the complete correlation spine traversal
        """
        # ── 1. Author ──
        src = new_quest_source(
            quest_id="vertical_slice_quest",
            title="Vertical Slice Acceptance Test",
            narrative_intent="Defend the village hearth against incursions.",
            original_prompt="Guild defense quest with zone triggers.",
            grimoire_prose="When your steel bites a standing Birch...",
        )
        add_spatial_anchor(
            src, "hearth_zone", "structure:village_01",
            {"x": 4.2, "y": 0.0, "z": -8.7}, 15.0,
            reference="piece:hearth_root",
        )
        add_node(src, "enter_zone", "event_trigger", anchor_id="hearth_zone",
                 next_nodes=["spawn_wave"])
        add_node(src, "spawn_wave", "action", next_nodes=[])
        src["required_capabilities"] = ["spawn_prefabs", "play_announcement"]
        src["action_references"] = ["spawn_frost_jarl"]

        # ── 2. Compile ──
        compiled = compile_questpack(src, source_revision="a" * 40)
        qp = compiled["questpack"]
        self.assertTrue(validate_contract(qp))

        # Authoring provenance is NOT in the executable
        qp_json = json.dumps(qp)
        self.assertNotIn("narrative_intent", qp_json)
        self.assertNotIn("original_prompt", qp_json)

        # ── 3. Install request ──
        req = build_install_request(compiled, requested_by="vertical_slice_test")
        self.assertTrue(validate_contract(req))

        # ── 4. Runtime admission ──
        receipt = admit_questpack(req, qp)
        self.assertTrue(validate_contract(receipt))
        self.assertEqual(receipt["status"], "admitted")

        # ── 5. Runtime observation ──
        runtime_evidence = emit_observation(
            receipt, "hearth_zone", "enter_zone",
            producer_id="comfy-quest-runtime",
            producer_kind="runtime_observer",
        )
        self.assertTrue(validate_contract(runtime_evidence))

        # ── 6. Arcane Sight observation ──
        arcane_evidence = emit_observation(
            receipt, "hearth_zone", "enter_zone",
            producer_id="arcane-sight",
            producer_kind="arcane_sight",
            evidence_kind="shader_highlight",
        )
        self.assertTrue(validate_contract(arcane_evidence))

        # ── 7. Prove the correlation spine ──
        for evidence in [runtime_evidence, arcane_evidence]:
            spine = evidence["correlation_spine"]

            # source_revision → compiled_quest_revision
            self.assertEqual(spine["source_revision"], compiled["source_revision"])
            self.assertEqual(spine["compiled_quest_revision"], compiled["compiled_quest_revision"])

            # install_request_id → active_runtime_revision
            self.assertEqual(spine["install_request_id"], req["request_id"])
            self.assertEqual(spine["active_runtime_revision"], receipt["active_runtime_revision"])

            # anchor_id → event_node_id
            self.assertEqual(spine["anchor_id"], "hearth_zone")
            self.assertEqual(spine["event_node_id"], "enter_zone")

        # ── Spine traversal is complete without timestamps or heuristics ──
        # Different producers are distinguishable
        self.assertNotEqual(
            runtime_evidence["producer"]["kind"],
            arcane_evidence["producer"]["kind"],
        )
        self.assertEqual(runtime_evidence["producer"]["kind"], "runtime_observer")
        self.assertEqual(arcane_evidence["producer"]["kind"], "arcane_sight")

    def test_evidence_survives_log_roundtrip(self):
        """Evidence records survive durable log write + read without mutation."""
        src = new_quest_source(quest_id="log_test", title="Log")
        add_spatial_anchor(src, "z", "structure:s", {"x": 0, "y": 0, "z": 0}, 5.0,
                           reference="piece:p")
        add_node(src, "t", "event_trigger", anchor_id="z", next_nodes=[])
        src["required_capabilities"] = []
        src["action_references"] = []
        compiled = compile_questpack(src)
        req = build_install_request(compiled)
        receipt = admit_questpack(req, compiled["questpack"])
        evidence = emit_observation(receipt, "z", "t")

        with tempfile.TemporaryDirectory() as td:
            log_path = os.path.join(td, "evidence.jsonl")
            write_evidence_log(evidence, log_path)
            loaded = read_evidence_log(log_path)[0]

            # Every spine field must survive the round-trip
            for key in evidence["correlation_spine"]:
                self.assertEqual(
                    loaded["correlation_spine"][key],
                    evidence["correlation_spine"][key],
                    f"Spine field '{key}' mutated during log round-trip",
                )


if __name__ == "__main__":
    unittest.main()

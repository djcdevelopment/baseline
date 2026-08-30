"""
Unit tests for Meta-Creator Canonical Contracts & Validation Suite.
"""

import unittest
from tools.contracts.meta_creator_contracts import (
    validate_contract,
    ContractValidationError,
    validate_spatial_anchor,
    detect_illegal_synchronous_cycles
)


class MetaCreatorContractTests(unittest.TestCase):

    def setUp(self):
        self.valid_anchor = {
            "anchor_id": "hearth_defense_zone_01",
            "frame": "structure:village_01",
            "local_bounds": {
                "center": {"x": 4.2, "y": 0.0, "z": -8.7},
                "radius_meters": 15.0
            },
            "world_binding": {
                "mode": "resolved_at_install",
                "reference": "piece:hearth_root"
            }
        }

        self.valid_experience = {
            "schema_version": "comfy-quest-experience/v1",
            "quest_id": "hearth_defense_quest",
            "title": "Defense of the Village Hearth",
            "nodes": [
                {
                    "node_id": "trigger_wave_1",
                    "node_type": "event_trigger",
                    "exec_mode": "single_tick",
                    "anchor_id": "hearth_defense_zone_01",
                    "next_nodes": ["condition_check_barricades"]
                },
                {
                    "node_id": "condition_check_barricades",
                    "node_type": "condition",
                    "exec_mode": "single_tick",
                    "next_nodes": ["action_spawn_jarl"]
                },
                {
                    "node_id": "action_spawn_jarl",
                    "node_type": "action",
                    "exec_mode": "single_tick",
                    "next_nodes": []
                }
            ],
            "spatial_anchors": [self.valid_anchor],
            "required_capabilities": ["spawn_prefabs", "play_announcement"],
            "action_references": ["spawn_frost_jarl"],
            "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }

        self.valid_install_request = {
            "schema_version": "InstallQuestPack/v1",
            "request_id": "req_20260829_001",
            "source_revision": "a1b2c3d4e5f678901234567890abcdef12345678",
            "compiled_quest_revision": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "questpack_payload_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "requested_by": "steward_studio_user"
        }

        self.valid_receipt = {
            "schema_version": "QuestReceipt/v1",
            "request_id": "req_20260829_001",
            "source_revision": "a1b2c3d4e5f678901234567890abcdef12345678",
            "compiled_quest_revision": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "active_runtime_revision": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "status": "admitted",
            "installed_at": "2026-08-29T23:08:25Z",
            "runtime_signature": "sig_comfy_runtime_v1_ok"
        }

        self.valid_evidence = {
            "schema_version": "ObservationEvidence/v1",
            "observation_id": "obs_20260829_99",
            "producer": {
                "id": "arcane-sight",
                "kind": "arcane_sight"
            },
            "evidence_kind": "event_observation",
            "subject": {
                "quest_revision": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "node_id": "trigger_wave_1",
                "anchor_id": "hearth_defense_zone_01"
            },
            "provenance": {
                "session_id": "sess_20260829_001",
                "observed_at": "2026-08-29T23:08:25Z"
            },
            "quality": {
                "classification": "observed"
            },
            "correlation_spine": {
                "source_revision": "a1b2c3d4e5f678901234567890abcdef12345678",
                "compiled_quest_revision": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "install_request_id": "req_20260829_001",
                "active_runtime_revision": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "anchor_id": "hearth_defense_zone_01",
                "event_node_id": "trigger_wave_1"
            }
        }

    def test_valid_contracts_pass(self):
        """Proves all canonical valid contract structures pass validation."""
        self.assertTrue(validate_contract(self.valid_experience))
        self.assertTrue(validate_contract(self.valid_install_request))
        self.assertTrue(validate_contract(self.valid_receipt))
        self.assertTrue(validate_contract(self.valid_evidence))

    def test_unknown_or_unsupported_version_fails_safely(self):
        """Proves unknown/unsupported schema versions are safely rejected."""
        invalid_doc = dict(self.valid_experience, schema_version="comfy-quest-experience/v999")
        with self.assertRaises(ContractValidationError) as ctx:
            validate_contract(invalid_doc)
        self.assertIn("Unsupported contract schema version", str(ctx.exception))

    def test_malformed_contract_fails(self):
        """Proves missing fields trigger validation errors."""
        malformed = dict(self.valid_install_request)
        del malformed["source_revision"]
        with self.assertRaises(ContractValidationError) as ctx:
            validate_contract(malformed)
        self.assertIn("InstallQuestPack missing required field: 'source_revision'", str(ctx.exception))

    def test_spatial_anchor_must_be_local_reference_frame(self):
        """Proves SpatialAnchors with absolute world coordinates are rejected."""
        absolute_world_anchor = dict(
            self.valid_anchor,
            frame="world:global_origin"
        )
        with self.assertRaises(ContractValidationError) as ctx:
            validate_spatial_anchor(absolute_world_anchor)
        self.assertIn("SpatialAnchor must not contain absolute world coordinates", str(ctx.exception))

    def test_illegal_synchronous_cycle_fails(self):
        """Proves illegal single-tick synchronous cycles are rejected."""
        cycling_nodes = [
            {
                "node_id": "node_a",
                "node_type": "event_trigger",
                "exec_mode": "single_tick",
                "next_nodes": ["node_b"]
            },
            {
                "node_id": "node_b",
                "node_type": "action",
                "exec_mode": "single_tick",
                "next_nodes": ["node_a"]
            }
        ]
        with self.assertRaises(ContractValidationError) as ctx:
            detect_illegal_synchronous_cycles(cycling_nodes)
        self.assertIn("Illegal synchronous execution cycle detected", str(ctx.exception))

    def test_valid_bounded_state_machine_loop_passes(self):
        """Proves valid state machine loops (e.g. wave1 -> wave2 -> reset -> wave1) pass cycle safety."""
        state_machine_nodes = [
            {
                "node_id": "wave_1",
                "node_type": "event_trigger",
                "exec_mode": "single_tick",
                "next_nodes": ["wave_2"]
            },
            {
                "node_id": "wave_2",
                "node_type": "event_trigger",
                "exec_mode": "single_tick",
                "next_nodes": ["reset_loop"]
            },
            {
                "node_id": "reset_loop",
                "node_type": "state_machine",
                "exec_mode": "bounded_state_machine",  # Breaks synchronous single-tick cycle
                "next_nodes": ["wave_1"]
            }
        ]
        # Should not raise exception
        detect_illegal_synchronous_cycles(state_machine_nodes)

    def test_provenance_and_correlation_spine(self):
        """Proves ObservationEvidence requires producer provenance and correlation spine."""
        broken_spine_evidence = dict(self.valid_evidence)
        broken_spine_evidence["correlation_spine"] = dict(
            self.valid_evidence["correlation_spine"],
            install_request_id=""
        )
        with self.assertRaises(ContractValidationError) as ctx:
            validate_contract(broken_spine_evidence)
        self.assertIn("correlation_spine missing or empty field: 'install_request_id'", str(ctx.exception))

    def test_stewardview_spatial_export_validation(self):
        """Proves SpatialAnchor exports from StewardView strictly validate against SpatialAnchor/v1 schema."""
        steward_export = {
            "anchor_id": "spatial_zone_01",
            "frame": "structure:village_01",
            "local_bounds": {
                "center": {"x": 4.2, "y": 0.0, "z": -8.7},
                "radius_meters": 15.0
            },
            "world_binding": {
                "mode": "resolved_at_install",
                "reference": "piece:hearth_root"
            }
        }
        # Validate anchor directly
        validate_spatial_anchor(steward_export)
        self.assertTrue(validate_contract(dict(self.valid_experience, spatial_anchors=[steward_export])))


if __name__ == "__main__":
    unittest.main()

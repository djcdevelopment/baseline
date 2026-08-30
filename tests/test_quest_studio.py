"""
Unit tests for Option B: StewardView ↔ Quest Studio Integration & Spatial Anchor Binding.

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.
"""

import json
import unittest

from tools.contracts.meta_creator_contracts import ContractValidationError, validate_contract
from tools.contracts.quest_studio import QuestStudioSession, import_stewardview_export


class QuestStudioIntegrationTests(unittest.TestCase):

    def setUp(self):
        # Simulated StewardView export output from /api/v1/spatial-anchors/export
        self.steward_export = {
            "anchor_id": "hearth_defense_zone_01",
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

    def test_quest_studio_imports_stewardview_export(self):
        """Proves Quest Studio imports SpatialAnchor/v1 export without manual JSON entry."""
        session = QuestStudioSession(quest_id="steward_quest", title="Steward Quest")
        anchor_id = import_stewardview_export(self.steward_export, session)
        
        self.assertEqual(anchor_id, "hearth_defense_zone_01")
        self.assertIn("hearth_defense_zone_01", session.imported_anchors)

    def test_anchor_fields_survive_unchanged(self):
        """Proves anchor_id, frame, local_bounds, and world_binding survive import unchanged."""
        session = QuestStudioSession(quest_id="steward_quest", title="Steward Quest")
        import_stewardview_export(self.steward_export, session)

        imported = session.imported_anchors["hearth_defense_zone_01"]
        self.assertEqual(imported["anchor_id"], self.steward_export["anchor_id"])
        self.assertEqual(imported["frame"], self.steward_export["frame"])
        self.assertEqual(imported["local_bounds"]["center"], self.steward_export["local_bounds"]["center"])
        self.assertEqual(imported["local_bounds"]["radius_meters"], self.steward_export["local_bounds"]["radius_meters"])
        self.assertEqual(imported["world_binding"]["mode"], self.steward_export["world_binding"]["mode"])
        self.assertEqual(imported["world_binding"]["reference"], self.steward_export["world_binding"]["reference"])

    def test_studio_binds_anchor_to_player_enter_zone(self):
        """Proves Studio attaches SpatialAnchor to Player.EnterZone node."""
        session = QuestStudioSession(quest_id="steward_quest", title="Steward Quest")
        anchor_id = import_stewardview_export(self.steward_export, session)

        bound_node = session.bind_event_node(
            node_id="enter_hearth_zone",
            node_type="event_trigger",
            anchor_id=anchor_id,
            exec_mode="single_tick",
            next_nodes=["announce_invasion"]
        )

        self.assertEqual(bound_node["anchor_id"], "hearth_defense_zone_01")
        self.assertEqual(bound_node["node_type"], "event_trigger")

    def test_recompiling_produces_expected_questpack(self):
        """Proves recompiling session via compile() produces valid comfy-quest-experience/v1 .questpack."""
        session = QuestStudioSession(quest_id="steward_quest", title="Steward Quest")
        anchor_id = import_stewardview_export(self.steward_export, session)
        session.bind_event_node("enter_hearth_zone", "event_trigger", anchor_id, next_nodes=[])
        session.source["required_capabilities"] = ["spawn_prefabs"]
        session.source["action_references"] = ["spawn_frost_jarl"]

        compiled_info = session.compile(source_revision="a" * 40)
        qp = compiled_info["questpack"]

        self.assertTrue(validate_contract(qp))
        self.assertEqual(qp["quest_id"], "steward_quest")
        self.assertEqual(qp["spatial_anchors"][0]["anchor_id"], "hearth_defense_zone_01")

    def test_no_world_space_coordinates_appear(self):
        """Proves compiled .questpack uses local frame coordinates, NEVER world coordinates."""
        session = QuestStudioSession(quest_id="steward_quest", title="Steward Quest")
        anchor_id = import_stewardview_export(self.steward_export, session)
        session.bind_event_node("enter_hearth_zone", "event_trigger", anchor_id)
        session.source["required_capabilities"] = []
        session.source["action_references"] = []

        compiled_info = session.compile()
        qp = compiled_info["questpack"]

        for anchor in qp["spatial_anchors"]:
            self.assertFalse(anchor["frame"].startswith("world:"))
            self.assertEqual(anchor["world_binding"]["mode"], "resolved_at_install")

    def test_modifying_studio_event_does_not_mutate_stewardview_geometry(self):
        """Proves modifying Studio event nodes does NOT mutate origin StewardView geometry object."""
        session = QuestStudioSession(quest_id="steward_quest", title="Steward Quest")
        import_stewardview_export(self.steward_export, session)

        # Modify event node in Studio
        session.bind_event_node("enter_hearth_zone", "event_trigger", "hearth_defense_zone_01", next_nodes=["new_action_node"])
        
        # Origin export dictionary must remain completely unchanged
        self.assertEqual(self.steward_export["local_bounds"]["radius_meters"], 15.0)
        self.assertEqual(self.steward_export["frame"], "structure:village_hearth")

    def test_malformed_unsupported_anchor_fails_visibly(self):
        """Proves malformed or world: frame anchors fail visibly with ContractValidationError."""
        session = QuestStudioSession(quest_id="steward_quest", title="Steward Quest")
        bad_world_anchor = {
            "anchor_id": "bad_world_anchor",
            "frame": "world:global_origin",
            "local_bounds": {"center": {"x": 0, "y": 0, "z": 0}, "radius_meters": 10.0},
            "world_binding": {"mode": "resolved_at_install", "reference": "piece:hearth_root"}
        }

        with self.assertRaises(ContractValidationError) as ctx:
            import_stewardview_export(bad_world_anchor, session)

        self.assertIn("SpatialAnchor must not contain absolute world coordinates", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

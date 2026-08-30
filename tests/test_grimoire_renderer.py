"""
Unit tests for Deterministic Grimoire Presentation Renderer.

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.
"""

import json
import unittest
from tools.contracts.grimoire_renderer import render_grimoire, load_grimoire_grammar
from tools.contracts.quest_compiler import (
    new_quest_source,
    add_node,
    add_spatial_anchor,
    compile_questpack,
)


class GrimoireRendererTests(unittest.TestCase):

    def setUp(self):
        src = new_quest_source(
            quest_id="grimoire_test_quest",
            title="Grimoire Presentation Test",
        )
        add_spatial_anchor(src, "village_hearth", "structure:village_01", {"x": 4.0, "y": 0.0, "z": -8.0}, 12.0, reference="piece:hearth")
        add_node(src, "enter_zone_hearth", "event_trigger", anchor_id="village_hearth", next_nodes=["spawn_wave_1"])
        add_node(src, "spawn_wave_1", "action", anchor_id="village_hearth", next_nodes=["announce_victory"])
        add_node(src, "announce_victory", "action", anchor_id="village_hearth", next_nodes=[])
        src["required_capabilities"] = []
        src["action_references"] = []
        
        compiled = compile_questpack(src)
        self.questpack = compiled["questpack"]

    def test_same_node_and_grammar_produces_identical_prose(self):
        """Same questpack + same grammar version produces 100% identical prose and hash."""
        r1 = render_grimoire(self.questpack)
        r2 = render_grimoire(self.questpack)
        self.assertEqual(r1["presentation_sha256"], r2["presentation_sha256"])
        self.assertEqual(r1["rendered_sections"], r2["rendered_sections"])

    def test_rendered_sections_correlate_to_canonical_semantic_ids(self):
        """Every section maps directly to node_id, anchor_id, and semantic_id."""
        presentation = render_grimoire(self.questpack)
        sections = presentation["rendered_sections"]
        self.assertEqual(len(sections), 3)

        s0 = sections[0]
        self.assertEqual(s0["node_id"], "enter_zone_hearth")
        self.assertEqual(s0["anchor_id"], "village_hearth")
        self.assertEqual(s0["semantic_id"], "Player.EnterZone")
        self.assertIn("village_hearth", s0["prose"])

        s1 = sections[1]
        self.assertEqual(s1["node_id"], "spawn_wave_1")
        self.assertEqual(s1["semantic_id"], "SpawnWave")
        self.assertIn("village_hearth", s1["prose"])

    def test_unknown_semantics_fail_gracefully(self):
        """Unknown semantic node types fall back to generic prose without failing."""
        qp_custom = dict(self.questpack, nodes=[
            {
                "node_id": "custom_exotic_node",
                "node_type": "exotic_type_xyz",
                "exec_mode": "single_tick",
                "anchor_id": "village_hearth",
                "next_nodes": []
            }
        ])
        presentation = render_grimoire(qp_custom)
        sections = presentation["rendered_sections"]
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["category"], "Generic")
        self.assertIn("custom_exotic_node", sections[0]["prose"])

    def test_presentation_cannot_alter_executable_behavior(self):
        """Rendering grimoire does not mutate the input questpack dictionary."""
        qp_before = json.dumps(self.questpack, sort_keys=True)
        _ = render_grimoire(self.questpack)
        qp_after = json.dumps(self.questpack, sort_keys=True)
        self.assertEqual(qp_before, qp_after)

    def test_grammar_versioning(self):
        """Presentation preserves grimoire grammar version metadata."""
        presentation = render_grimoire(self.questpack)
        self.assertEqual(presentation["grammar_version"], "grimoire-grammar/v1")


if __name__ == "__main__":
    import json
    unittest.main()

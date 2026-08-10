from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from comfy_gateway.toolsurface import questlab


DOC = {
    "schema_version": 1,
    "player": {"name": "tester"},
    "quests": [{
        "quest_id": "greyling_cull",
        "name": "Greyling Cull",
        "guild": "combat",
        "trigger": {"event": "creature_killed", "target": "greyling"},
    }],
}


class QuestLabBridgeTest(unittest.TestCase):
    def test_spell_round_trip_is_deterministic(self) -> None:
        first = questlab.questlab_spell_encode(DOC)
        second = questlab.questlab_spell_encode(DOC)
        self.assertEqual(first["spell"], second["spell"])
        decoded = questlab.questlab_spell_decode(first["spell"])
        self.assertEqual(DOC, decoded["document"])

    def test_spell_rejects_non_spell_and_bad_payload(self) -> None:
        with self.assertRaises(ValueError):
            questlab.questlab_spell_decode("not a spell")
        bad = "[Import: " + base64.b64encode(b"not json").decode("ascii") + "]"
        with self.assertRaises(ValueError):
            questlab.questlab_spell_decode(bad)

    def test_write_confines_names_and_refuses_accidental_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(questlab, "QUESTLAB_ROOT", Path(tmp)):
                result = questlab.questlab_write("draft.json", DOC, trigger_reload=False)
                self.assertTrue(result["ok"])
                self.assertEqual(1, result["quest_count"])
                with self.assertRaises(FileExistsError):
                    questlab.questlab_write("draft.json", DOC, trigger_reload=False)
                with self.assertRaises(ValueError):
                    questlab.questlab_write("..\\escape.json", DOC, trigger_reload=False)

    def test_reload_is_fixed_mailbox_operation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(questlab, "QUESTLAB_ROOT", Path(tmp)):
                result = questlab.questlab_reload()
                payload = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
                self.assertEqual("reload", payload["operation"])
                self.assertEqual("comfy-questlab-batch-request/v1", payload["schema"])
                self.assertEqual("questlab-batch-request.json", Path(result["path"]).name)

    def test_document_validation_rejects_duplicate_ids(self) -> None:
        duplicate = dict(DOC)
        duplicate["quests"] = [DOC["quests"][0], DOC["quests"][0]]
        with self.assertRaises(ValueError):
            questlab.questlab_spell_encode(duplicate)

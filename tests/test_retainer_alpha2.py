from __future__ import annotations

import json
import random
import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker
from crystal_guild.retainer import RETAINER_ASSIGNMENTS_BY_ID

ROOT = Path(__file__).resolve().parents[1]


class RetainerServiceAlpha2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), overlay_state_path=str(Path(self.temp.name) / "overlay.json"), rng=random.Random(1702))
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def state(self):
        return self.game.portal_retainer_state("100").data["retainer_state"]

    def test_alpha2_contract_and_history_schema(self):
        self.assertEqual(__version__, "1.7.0")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 15)
        self.assertEqual(self.db.schema_version(), 15)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 31)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='retainer_history'"))
        self.assertEqual(self.state()["history"], [])

    def test_focused_dispatch_guarantees_priority_and_charges_premium(self):
        before = self.state()["gil"]
        definition = RETAINER_ASSIGNMENTS_BY_ID["field_gathering"]
        result = self.game.portal_retainer_dispatch("100", "field_gathering", "a2-focus-1", "iron_ore")
        self.assertTrue(result.ok)
        self.assertEqual(result.data["retainer_state"]["gil"], before - int(definition["focused_cost_gil"]))
        stored = json.loads(self.db.one("SELECT reward_json FROM retainer_assignments WHERE player_id='100'")["reward_json"])
        self.assertEqual(stored["priority_item_id"], "iron_ore")
        self.assertGreaterEqual(sum(int(row["quantity"]) for row in stored["items"] if row["item_id"] == "iron_ore"), 1)
        self.assertEqual(result.data["retainer_state"]["assignment"]["priority"]["item_id"], "iron_ore")

    def test_general_dispatch_preserves_alpha1_cost(self):
        before = self.state()["gil"]
        definition = RETAINER_ASSIGNMENTS_BY_ID["field_gathering"]
        result = self.game.portal_retainer_dispatch("100", "field_gathering", "a2-general-1", "")
        self.assertTrue(result.ok)
        self.assertEqual(result.data["retainer_state"]["gil"], before - int(definition["cost_gil"]))
        stored = json.loads(self.db.one("SELECT reward_json FROM retainer_assignments WHERE player_id='100'")["reward_json"])
        self.assertIsNone(stored["priority_item_id"])

    def test_priority_must_exist_in_selected_route(self):
        result = self.game.portal_retainer_dispatch("100", "field_gathering", "a2-bad-priority", "bahamut_scale")
        self.assertFalse(result.ok)
        self.assertIn("priority material", " ".join(result.messages).lower())
        self.assertFalse(self.state()["busy"])

    def test_collection_writes_exactly_one_history_row(self):
        started = self.game.portal_retainer_dispatch("100", "field_gathering", "a2-history-start", "iron_ore")
        self.assertTrue(started.ok)
        self.db.execute("UPDATE retainer_assignments SET ready_at=? WHERE player_id='100'", (int(time.time()) - 1,))
        collected = self.game.portal_retainer_collect("100", "a2-history-collect")
        self.assertTrue(collected.ok)
        replay = self.game.portal_retainer_collect("100", "a2-history-collect")
        self.assertTrue(replay.ok)
        self.assertEqual(int(self.db.one("SELECT COUNT(*) AS n FROM retainer_history WHERE player_id='100'")["n"]), 1)
        history = self.state()["history"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["priority"]["item_id"], "iron_ore")
        self.assertEqual(history[0]["cost_gil"], RETAINER_ASSIGNMENTS_BY_ID["field_gathering"]["focused_cost_gil"])

    def test_worker_accepts_optional_priority_and_rejects_unknown_fields(self):
        worker = PortalActionWorker(self.game, "", "")
        base = {"protocol_version": ACTION_PROTOCOL_VERSION, "twitch_id": "100", "username": "van", "lease_token": "lease"}
        ok, _message, data = worker._execute({**base, "id": "a2-worker-focus", "type": "RETAINER_DISPATCH", "payload": {"assignment": "field_gathering", "priority": "iron_ore"}})
        self.assertTrue(ok)
        self.assertEqual(data["retainer_state"]["assignment"]["priority"]["item_id"], "iron_ore")
        ok, message, _data = worker._execute({**base, "id": "a2-worker-extra", "type": "RETAINER_DISPATCH", "payload": {"assignment": "field_gathering", "priority": "", "force": True}})
        self.assertFalse(ok)
        self.assertIn("optional priority", message.lower())


if __name__ == "__main__":
    unittest.main()

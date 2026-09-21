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
from crystal_guild.retainer import RETAINER_ASSIGNMENTS, RETAINER_ASSIGNMENTS_BY_ID, retainer_rank

ROOT = Path(__file__).resolve().parents[1]


class RetainerServiceAlpha1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1701),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def state(self):
        return self.game.portal_retainer_state("100").data["retainer_state"]

    def test_alpha1_contract_schema_protocol_and_default_retainer(self):
        self.assertEqual(__version__, "1.9.0-title-expansion-alpha3")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 19)
        self.assertEqual(self.db.schema_version(), 19)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 36)
        state = self.state()
        self.assertEqual(state["retainer"]["name"], "Guild Retainer")
        self.assertEqual(state["retainer"]["rank"], 1)
        self.assertFalse(state["busy"])
        self.assertEqual(len(state["assignments"]), len(RETAINER_ASSIGNMENTS))

    def test_dispatch_pays_gil_persists_hidden_reward_and_blocks_second_assignment(self):
        before = self.state()["gil"]
        definition = RETAINER_ASSIGNMENTS_BY_ID["field_gathering"]
        result = self.game.portal_retainer_dispatch("100", "field_gathering", "retainer-dispatch-1")
        self.assertTrue(result.ok)
        state = result.data["retainer_state"]
        self.assertEqual(state["gil"], before - int(definition["cost_gil"]))
        self.assertTrue(state["busy"])
        self.assertEqual(state["assignment"]["state"], "active")
        self.assertEqual(state["assignment"]["rewards"], [])
        row = self.db.one("SELECT reward_json,state FROM retainer_assignments WHERE player_id='100'")
        reward = json.loads(row["reward_json"])
        self.assertTrue(reward["items"])
        blocked = self.game.portal_retainer_dispatch("100", "monster_salvage", "retainer-dispatch-2")
        self.assertFalse(blocked.ok)

    def test_collect_is_exactly_once_and_grants_only_materials(self):
        started = self.game.portal_retainer_dispatch("100", "field_gathering", "retainer-start-collect")
        self.assertTrue(started.ok)
        self.db.execute("UPDATE retainer_assignments SET ready_at=?,state='active' WHERE player_id='100'", (int(time.time()) - 1,))
        ready = self.state()
        self.assertEqual(ready["assignment"]["state"], "ready")
        self.assertTrue(ready["assignment"]["rewards"])
        before = {row["item_id"]: int(row["quantity"]) for row in self.db.all("SELECT item_id,quantity FROM inventory WHERE player_id='100'")}
        collected = self.game.portal_retainer_collect("100", "retainer-collect-1")
        self.assertTrue(collected.ok)
        replay = self.game.portal_retainer_collect("100", "retainer-collect-1")
        self.assertEqual(replay.data.get("materials_collected"), collected.data.get("materials_collected"))
        after_first = {row["item_id"]: int(row["quantity"]) for row in self.db.all("SELECT item_id,quantity FROM inventory WHERE player_id='100'")}
        second = self.game.portal_retainer_collect("100", "retainer-collect-new-id")
        self.assertFalse(second.ok)
        after_second = {row["item_id"]: int(row["quantity"]) for row in self.db.all("SELECT item_id,quantity FROM inventory WHERE player_id='100'")}
        self.assertEqual(after_first, after_second)
        self.assertNotEqual(before, after_first)
        for item_id in after_first:
            if after_first[item_id] > before.get(item_id, 0):
                self.assertEqual(self.game.data.items[item_id]["type"], "material")
        retainer = self.state()["retainer"]
        self.assertEqual(retainer["assignments_completed"], 1)
        self.assertGreater(retainer["materials_found"], 0)

    def test_rank_unlocks_are_retainer_xp_gated(self):
        state = self.state()
        mineral = next(row for row in state["assignments"] if row["id"] == "mineral_survey")
        self.assertFalse(mineral["unlocked"])
        self.db.execute("UPDATE player_retainers SET xp=100 WHERE player_id='100'")
        state = self.state()
        self.assertEqual(state["retainer"]["rank"], 2)
        mineral = next(row for row in state["assignments"] if row["id"] == "mineral_survey")
        self.assertTrue(mineral["unlocked"])
        self.assertEqual(retainer_rank(1400)["rank_name"], "Master")

    def test_assignment_pools_never_include_relic_or_artifact_materials(self):
        for assignment in RETAINER_ASSIGNMENTS:
            for item_id, _weight in assignment["pool"]:
                item = self.game.data.items[item_id]
                self.assertEqual(item["type"], "material")
                self.assertNotIn(item.get("rarity"), {"relic", "artifact"})

    def test_bonus_find_is_stored_separately_and_collected_once(self):
        class BonusRng:
            @staticmethod
            def choices(ids, weights=None, k=1):
                return [ids[0]]
            @staticmethod
            def randint(low, high):
                return low
            @staticmethod
            def random():
                return 0.0

        self.game.rng = BonusRng()
        started = self.game.portal_retainer_dispatch("100", "field_gathering", "retainer-bonus-start")
        self.assertTrue(started.ok)
        stored = json.loads(self.db.one("SELECT reward_json FROM retainer_assignments WHERE player_id='100'")["reward_json"])
        self.assertEqual(stored["bonus"]["quantity"], 1)
        base_qty = sum(int(row["quantity"]) for row in stored["items"] if row["item_id"] == stored["bonus"]["item_id"])
        self.db.execute("UPDATE retainer_assignments SET ready_at=? WHERE player_id='100'", (int(time.time()) - 1,))
        ready = self.state()["assignment"]
        self.assertIsNotNone(ready["bonus"])
        self.assertEqual(sum(int(row["quantity"]) for row in ready["rewards"] if row["item_id"] == ready["bonus"]["item_id"]), base_qty)
        before = self.db.one("SELECT quantity FROM inventory WHERE player_id='100' AND item_id=?", (ready["bonus"]["item_id"],))
        before_qty = int(before["quantity"]) if before else 0
        collected = self.game.portal_retainer_collect("100", "retainer-bonus-collect")
        self.assertTrue(collected.ok)
        after_qty = int(self.db.one("SELECT quantity FROM inventory WHERE player_id='100' AND item_id=?", (ready["bonus"]["item_id"],))["quantity"])
        self.assertEqual(after_qty - before_qty, base_qty + 1)
        self.assertEqual(self.state()["retainer"]["bonus_finds"], 1)

    def test_worker_validates_retainer_actions(self):
        worker = PortalActionWorker(self.game, "", "")
        base = {"protocol_version": ACTION_PROTOCOL_VERSION, "twitch_id": "100", "username": "van", "lease_token": "lease"}
        ok, _message, data = worker._execute({**base, "id": "retainer-worker-state", "type": "RETAINER_STATE", "payload": {}})
        self.assertTrue(ok)
        self.assertEqual(data["retainer_state"]["retainer"]["rank"], 1)
        ok, _message, data = worker._execute({**base, "id": "retainer-worker-dispatch", "type": "RETAINER_DISPATCH", "payload": {"assignment": "field_gathering"}})
        self.assertTrue(ok)
        self.assertEqual(data["retainer_state"]["assignment"]["type"], "field_gathering")
        ok, message, _data = worker._execute({**base, "id": "retainer-worker-bad", "type": "RETAINER_DISPATCH", "payload": {"assignment": "../../bad"}})
        self.assertFalse(ok)
        self.assertIn("unavailable", message.lower())

    def test_restart_preserves_active_assignment_and_committed_reward(self):
        started = self.game.portal_retainer_dispatch("100", "monster_salvage", "retainer-restart-start")
        self.assertTrue(started.ok)
        row_before = self.db.one("SELECT assignment_id,reward_json,ready_at FROM retainer_assignments WHERE player_id='100'")
        self.db.close()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay-restart.json"),
            rng=random.Random(9999),
        )
        row_after = self.db.one("SELECT assignment_id,reward_json,ready_at FROM retainer_assignments WHERE player_id='100'")
        self.assertEqual(dict(row_before), dict(row_after))
        self.assertTrue(self.state()["busy"])


if __name__ == "__main__":
    unittest.main()

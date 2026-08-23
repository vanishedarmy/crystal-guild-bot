from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild.chocobo import (
    CHOC_MAX_LEVEL,
    QUEST_ID,
    STABLE_FACILITY_ID,
    WRIT_ACTIVATION_SECONDS,
    WRIT_COST_GIL,
)
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.fellowship import PROJECTS
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class ChocoboCompanionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
        )
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def make_personally_eligible(self, player_id: str = "100") -> None:
        self.db.execute(
            "UPDATE players SET level=10,ventures=10,gil=5000 WHERE twitch_id=?",
            (player_id,),
        )
        self.db.execute(
            "INSERT INTO player_hunts(player_id,hunt_id,clears,first_cleared_at,last_cleared_at) "
            "VALUES (?,'red_hot_problem',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP) "
            "ON CONFLICT(player_id,hunt_id) DO UPDATE SET clears=1",
            (player_id,),
        )

    def open_stable(self) -> None:
        self.db.execute(
            "UPDATE fellowship_facilities SET tier=1 WHERE facility_id=?",
            (STABLE_FACILITY_ID,),
        )

    def prepare_registered_chocobo(self, player_id: str = "100", name: str = "Biscuit") -> None:
        self.open_stable()
        self.make_personally_eligible(player_id)
        self.assertTrue(self.game.chocobo_quest(player_id).ok)
        self.assertTrue(self.game.buy_chocobo_writ(player_id).ok)
        self.db.execute(
            "UPDATE player_chocobos SET writ_ready_at=? WHERE player_id=?",
            (int(time.time()) - 1, player_id),
        )
        self.assertTrue(self.game.register_chocobo(player_id, name).ok)

    def test_schema_four_and_stable_project_are_additive(self):
        self.assertEqual(self.db.schema_version(), 5)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_chocobos'"))
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_chocobo_traits'"))
        project = PROJECTS["chocobo_stable_t1"]
        self.assertEqual(project["required_level"], 2)
        requirements = {item["key"]: item["target"] for item in project["requirements"]}
        self.assertEqual(requirements["gil"], 5000)
        self.assertEqual(requirements["activity:venture_complete"], 10)
        self.assertEqual(requirements["fellowship_level"], 2)

    def test_personal_quest_requires_level_ventures_and_c_rank_hunt(self):
        state = self.game._chocobo_state_data("100")
        self.assertFalse(state["quest"]["ready"])
        self.make_personally_eligible()
        state = self.game._chocobo_state_data("100")
        self.assertTrue(state["quest"]["ready"])
        before = int(self.game._player("100")["gil"])
        result = self.game.chocobo_quest("100")
        self.assertTrue(result.ok)
        self.assertTrue(self.game._chocobo_quest_done("100"))
        self.assertEqual(int(self.game._player("100")["gil"]), before + 250)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_quests WHERE player_id='100' AND quest_id=?", (QUEST_ID,)))

    def test_writ_requires_stable_and_quest_costs_500_and_waits_one_hour(self):
        self.make_personally_eligible()
        self.assertFalse(self.game.buy_chocobo_writ("100").ok)
        self.open_stable()
        self.assertFalse(self.game.buy_chocobo_writ("100").ok)
        self.assertTrue(self.game.chocobo_quest("100").ok)
        before = int(self.game._player("100")["gil"])
        start = int(time.time())
        result = self.game.buy_chocobo_writ("100")
        self.assertTrue(result.ok)
        self.assertEqual(int(self.game._player("100")["gil"]), before - WRIT_COST_GIL)
        self.assertEqual(self.game._inventory_qty("100", "chocobo_writ"), 1)
        row = self.db.one("SELECT writ_purchased_at,writ_ready_at FROM player_chocobos WHERE player_id='100'")
        self.assertGreaterEqual(int(row["writ_purchased_at"]), start)
        self.assertEqual(int(row["writ_ready_at"]) - int(row["writ_purchased_at"]), WRIT_ACTIVATION_SECONDS)
        self.assertFalse(self.game.register_chocobo("100", "Biscuit").ok)

    def test_registration_consumes_active_writ_assigns_persistent_trait_and_supports_rename(self):
        self.prepare_registered_chocobo()
        state = self.game._chocobo_state_data("100")
        self.assertTrue(state["companion"]["registered"])
        self.assertEqual(state["companion"]["name"], "Biscuit")
        self.assertEqual(state["companion"]["level"], 1)
        self.assertEqual(len(state["companion"]["traits"]), 1)
        self.assertEqual(self.game._inventory_qty("100", "chocobo_writ"), 0)
        renamed = self.game.rename_chocobo("100", "Drumstick")
        self.assertTrue(renamed.ok)
        self.assertEqual(self.game._chocobo_state_data("100")["companion"]["name"], "Drumstick")
        self.assertFalse(self.game.rename_chocobo("100", "!").ok)

    def test_bond_xp_levels_without_adding_combat_stats(self):
        self.prepare_registered_chocobo()
        notes = self.game._award_chocobo_xp("100", 50)
        state = self.game._chocobo_state_data("100")["companion"]
        self.assertEqual(state["total_xp"], 50)
        self.assertEqual(state["level"], 2)
        self.assertIn("CHOCOBO LEVEL UP", " ".join(notes))
        self.assertLessEqual(state["level"], CHOC_MAX_LEVEL)
        # Companion data is deliberately separate from character combat stats.
        self.assertNotIn("attack", state)
        self.assertNotIn("defense", state)

    def test_expedition_readiness_requires_registered_chocobo_and_board(self):
        self.prepare_registered_chocobo()
        state = self.game._chocobo_state_data("100")
        self.assertTrue(state["expedition"]["chocobo_ready"])
        self.assertFalse(state["expedition"]["ready"])
        self.db.execute("UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1")
        state = self.game._chocobo_state_data("100")
        self.assertTrue(state["expedition"]["board_ready"])
        self.assertTrue(state["expedition"]["ready"])

    def test_protocol_nine_worker_routes_typed_chocobo_actions(self):
        worker = PortalActionWorker(self.game, "https://guild.example", "sync-key")
        base = {
            "id": "chocobo-state-action", "protocol_version": ACTION_PROTOCOL_VERSION,
            "twitch_id": "100", "username": "van", "type": "CHOCOBO_STATE",
            "payload": {}, "lease_token": "lease",
        }
        ok, message, data = worker._execute(base)
        self.assertTrue(ok, message)
        self.assertIn("chocobo_state", data)
        bad = dict(base, id="bad-name", type="REGISTER_CHOCOBO", payload={})
        ok, message, _ = worker._execute(bad)
        self.assertFalse(ok)
        self.assertIn("name", message.lower())

    def test_portal_purchase_and_registration_are_replay_safe(self):
        self.open_stable()
        self.make_personally_eligible()
        self.assertTrue(self.game.chocobo_quest("100").ok)
        before = int(self.game._player("100")["gil"])
        first = self.game.portal_purchase_chocobo_writ("100", "writ-replay")
        second = self.game.portal_purchase_chocobo_writ("100", "writ-replay")
        self.assertTrue(first.ok)
        self.assertTrue(second.ok)
        self.assertEqual(int(self.game._player("100")["gil"]), before - WRIT_COST_GIL)
        self.assertEqual(self.game._inventory_qty("100", "chocobo_writ"), 1)
        self.db.execute("UPDATE player_chocobos SET writ_ready_at=? WHERE player_id='100'", (int(time.time()) - 1,))
        first = self.game.portal_register_chocobo("100", "Biscuit", "register-replay")
        second = self.game.portal_register_chocobo("100", "Biscuit", "register-replay")
        self.assertTrue(first.ok)
        self.assertTrue(second.ok)
        self.assertEqual(self.game._inventory_qty("100", "chocobo_writ"), 0)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_chocobo_traits WHERE player_id='100'")["n"], 1)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.expeditions import defeat_cache_keep, effective_travel_seconds

ROOT = Path(__file__).resolve().parents[1]


class ExpeditionV12Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db, self.data,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(120),
        )
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='100'")
        p = self.game._player("100")
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='100'", (self.game._max_hp(p),))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def unlock(self, *traits: str):
        self.db.execute("UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1")
        self.db.execute(
            "INSERT INTO player_chocobos(player_id,name,registered_at) VALUES ('100','Biscuit',CURRENT_TIMESTAMP) "
            "ON CONFLICT(player_id) DO UPDATE SET name='Biscuit',registered_at=CURRENT_TIMESTAMP"
        )
        for trait in traits:
            self.db.execute(
                "INSERT OR IGNORE INTO player_chocobo_traits(player_id,trait_id) VALUES ('100',?)", (trait,)
            )

    def test_schema_and_five_regions_are_present(self):
        self.assertEqual(self.db.schema_version(), 8)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_expeditions'"))
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_region_exploration'"))
        self.assertEqual(len(self.data.expedition_regions), 5)
        self.assertEqual(
            set(self.data.expedition_regions),
            {"emerald_wilds", "ashen_highlands", "mistfen_marshes", "frostveil_reach", "astral_scar"},
        )

    def test_launch_requires_board_and_registered_chocobo(self):
        result = self.game.expedition_start("100", "emerald_wilds", "scout")
        self.assertFalse(result.ok)
        self.assertIn("Expedition Board", " ".join(result.messages))
        self.db.execute("UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1")
        result = self.game.expedition_start("100", "emerald_wilds", "scout")
        self.assertFalse(result.ok)
        self.assertIn("registered Chocobo", " ".join(result.messages))
        self.unlock("fleet_feet")
        result = self.game.expedition_start("100", "emerald_wilds", "scout")
        self.assertTrue(result.ok, result.messages)
        state = self.game._expedition_load("100")
        self.assertEqual(state["status"], "travel")
        self.assertEqual(state["base_stages"], 3)
        self.assertEqual(state["max_stages"], 5)

    def test_fleet_feet_reduces_travel_and_run_persists(self):
        self.unlock("fleet_feet")
        self.assertEqual(effective_travel_seconds(240, {"fleet_feet"}), 204)
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        state = self.game._expedition_load("100")
        self.assertIsNotNone(state)
        self.assertEqual(int(state["travel_ready_at"]) - int(state["updated_at"]), 204)
        raw = self.db.one("SELECT state_json FROM player_expeditions WHERE player_id='100'")
        self.assertEqual(json.loads(raw["state_json"])["region_id"], "emerald_wilds")

    def test_stage_cannot_resolve_before_authoritative_timer(self):
        self.unlock()
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        result = self.game.expedition_resolve_stage("100")
        self.assertFalse(result.ok)
        self.assertIn("Travel completes", " ".join(result.messages))

    def test_resource_stage_progress_cache_and_safe_return(self):
        self.unlock("forager")
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        state = self.game._expedition_load("100")
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        with patch("crystal_guild.engine.expedition_event_weights", return_value=(["resource"], [1.0])):
            result = self.game.expedition_resolve_stage("100")
        self.assertTrue(result.ok, result.messages)
        state = self.game._expedition_load("100")
        self.assertEqual(state["status"], "choice")
        self.assertGreaterEqual(sum(int(row["quantity"]) for row in state["cache"]["items"]), 2)
        progress = self.game._expedition_progress("100", "emerald_wilds")
        self.assertGreaterEqual(progress["progress"], 1)
        before = sum(self.game._inventory_qty("100", row["id"]) for row in state["cache"]["items"])
        returned = self.game.expedition_return("100")
        self.assertTrue(returned.ok, returned.messages)
        self.assertIsNone(self.game._expedition_load("100"))
        after = sum(self.game._inventory_qty("100", row["id"]) for row in state["cache"]["items"])
        self.assertGreater(after, before)
        pending = self.game._pending_portal_adventure_results("100")
        self.assertTrue(any(row.get("kind") == "expedition" for row in pending))

    def test_route_continue_and_internal_camp(self):
        self.unlock()
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "journey").ok)
        state = self.game._expedition_load("100")
        state["status"] = "choice"
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        self.assertTrue(self.game.expedition_camp("100").ok)
        state = self.game._expedition_load("100")
        self.assertEqual(state["travel_penalty_seconds"], 120)
        continued = self.game.expedition_continue("100", "deep")
        self.assertTrue(continued.ok, continued.messages)
        state = self.game._expedition_load("100")
        self.assertEqual(state["stage"], 2)
        self.assertEqual(state["route"], "deep")
        self.assertEqual(state["status"], "travel")

    def test_chocobo_rescue_traits_raise_but_cap_cache_protection(self):
        self.assertAlmostEqual(defeat_cache_keep(set()), .70)
        self.assertAlmostEqual(defeat_cache_keep({"steady_strider"}), .80)
        self.assertAlmostEqual(defeat_cache_keep({"steady_strider", "lucky_plume"}), .85)

    def test_equipment_is_locked_for_active_expedition(self):
        self.unlock()
        self.game._change_item("100", "bronze_sword", 1, "test")
        self.assertTrue(self.game.equip("100", "bronze sword").ok)
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)

        equip = self.game.equip("100", "bronze sword")
        unequip = self.game.unequip("100", "weapon")
        self.assertFalse(equip.ok)
        self.assertFalse(unequip.ok)
        self.assertIn("Expedition", " ".join(equip.messages))
        self.assertIn("Expedition", " ".join(unequip.messages))

    def test_adventure_state_exposes_compact_expedition_board(self):
        self.unlock("keen_eye")
        state = self.game._portal_adventure_state_data("100")
        board = state["expeditions"]
        self.assertTrue(board["ready"])
        self.assertEqual(len(board["regions"]), 5)
        self.assertEqual([row["id"] for row in board["depths"]], ["scout", "journey", "deep"])
        self.assertIn("keen_eye", board["traits_active"])
        encoded = json.dumps({"adventure_state": state}, separators=(",", ":")).encode()
        self.assertLess(len(encoded), 16 * 1024)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class DungeonsAlpha3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0, overlay_state_path=str(Path(self.tmp.name) / "overlay.json"), rng=random.Random(1403))
        self.game.recruit("143", "warden", "Warden")
        self.game.choose_job("143", "warrior")
        self.db.execute("UPDATE players SET level=32,current_hp=420 WHERE twitch_id='143'")
        for region_id, progress in (("emerald_wilds", 60), ("ashen_highlands", 60), ("frostveil_reach", 45)):
            self.db.execute("INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES (?,?,?,?) ON CONFLICT(player_id,region_id) DO UPDATE SET progress=excluded.progress,stages_cleared=excluded.stages_cleared", ("143", region_id, progress, 8))

    def tearDown(self) -> None:
        self.db.close(); self.tmp.cleanup()

    def test_alpha3_keeps_schema10_protocol24_and_adds_third_dungeon(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 27)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 39)
        board = self.game._dungeon_board_state("143")
        self.assertEqual([row["id"] for row in board["dungeons"][:3]], ["forgotten_ossuary", "emberglass_foundry", "whiteglass_bastion"])
        whiteglass = board["dungeons"][2]
        self.assertTrue(whiteglass["unlocked"])
        self.assertEqual(whiteglass["rooms"], 9)
        self.assertEqual(whiteglass["choice_rooms"], 2)
        self.assertEqual(whiteglass["identity"], "Endurance & Wards")
        self.assertFalse(bool(whiteglass.get("first_clear_claimed")))
        self.assertTrue(any("Celestial Thread" in row for row in whiteglass["first_clear_rewards"]))

    def test_whiteglass_unlock_uses_frostveil_exploration(self):
        self.db.execute("UPDATE player_region_exploration SET progress=44 WHERE player_id='143' AND region_id='frostveil_reach'")
        entry = next(row for row in self.game._dungeon_board_state("143")["dungeons"] if row["id"] == "whiteglass_bastion")
        self.assertFalse(entry["unlocked"])
        self.assertTrue(any("Frostveil Reach" in row and "45%" in row for row in entry["missing"]))

    def test_route_boon_persists_then_changes_next_combat(self):
        self.assertTrue(self.game.dungeon_start("143", "whiteglass_bastion").ok)
        state = self.game._dungeon_load("143")
        state["room_index"] = 3
        self.game._dungeon_save("143", state)
        self.game._dungeon_begin_room("143", state)
        public = self.game._dungeon_public("143")
        choice = next(row for row in public["choices"] if row["id"] == "exposed_battlement")
        self.assertTrue(any("Next foe HP +8%" in row for row in choice["effects"]))
        run_id, room_id = public["run_id"], public["room"]["id"]
        self.assertTrue(self.game.portal_dungeon_choice("143", run_id, room_id, public["revision"], "exposed_battlement", "a3_battlement").ok)
        after = self.game._dungeon_public("143")
        self.assertTrue(any("Next foe HP +8%" in row for row in after["modifiers"]))
        self.assertTrue(any("Next combat rewards +20%" in row for row in after["modifiers"]))
        state = self.game._dungeon_load("143")
        state["room_index"] = 5
        self.game._dungeon_save("143", state)
        self.game._dungeon_begin_room("143", state)
        combat = self.game._dungeon_public("143")["combat"]
        base = int(self.game.data.monsters["iron_giant"]["hp"] * 1.22)
        self.assertGreater(combat["enemy"]["max_hp"], base)
        self.assertTrue(any("Combat rewards +20%" in row for row in combat["route_effects"]))

    def test_safe_route_reduces_next_hazard_damage(self):
        self.assertTrue(self.game.dungeon_start("143", "whiteglass_bastion").ok)
        state = self.game._dungeon_load("143")
        state["room_index"] = 3
        self.game._dungeon_save("143", state)
        self.game._dungeon_begin_room("143", state)
        public = self.game._dungeon_public("143")
        self.game.portal_dungeon_choice("143", public["run_id"], public["room"]["id"], public["revision"], "sheltered_gallery", "a3_sheltered")
        hp_before = int(self.db.one("SELECT current_hp FROM players WHERE twitch_id='143'")["current_hp"])
        state = self.game._dungeon_load("143")
        state["room_index"] = 4
        self.game._dungeon_save("143", state)
        self.game._dungeon_begin_room("143", state)
        hp_after = int(self.db.one("SELECT current_hp FROM players WHERE twitch_id='143'")["current_hp"])
        max_hp = self.game._max_hp(self.game._player("143"))
        full_hazard = int(round(max_hp * .18))
        self.assertLess(hp_before - hp_after, full_hazard)
        self.assertEqual(self.game._dungeon_public("143")["modifiers"], [])

    def test_first_clear_bonus_is_once_per_dungeon(self):
        dungeon = self.game.data.dungeons["whiteglass_bastion"]
        state = {"run_id":"first","dungeon_id":"whiteglass_bastion","room_index":8,"status":"choice","cache":{"xp":0,"jp":0,"gil":0,"items":[]},"history":[],"discoveries":[],"modifiers":{}}
        first = self.game._dungeon_finish("143", state, outcome="complete")
        self.assertTrue(first.ok)
        self.assertTrue(first.data["dungeon_result"]["first_clear"])
        first_gil = int(first.data["dungeon_result"]["rewards"]["gil"])
        state2 = {"run_id":"second","dungeon_id":"whiteglass_bastion","room_index":8,"status":"choice","cache":{"xp":0,"jp":0,"gil":0,"items":[]},"history":[],"discoveries":[],"modifiers":{}}
        second = self.game._dungeon_finish("143", state2, outcome="complete")
        self.assertFalse(second.data["dungeon_result"]["first_clear"])
        self.assertEqual(first_gil - int(second.data["dungeon_result"]["rewards"]["gil"]), int(dungeon["first_clear_bonus"]["gil"]))
        progress = self.game._dungeon_progress("143", "whiteglass_bastion")
        self.assertEqual(progress["clears"], 2)


if __name__ == "__main__":
    unittest.main()

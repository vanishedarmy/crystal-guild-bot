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


class DungeonsAlpha4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0, overlay_state_path=str(Path(self.tmp.name) / "overlay.json"), rng=random.Random(1404))
        self.game.recruit("144", "seer", "Seer")
        self.game.choose_job("144", "black_mage")
        self.db.execute("UPDATE players SET level=40,current_hp=420 WHERE twitch_id='144'")
        for region_id, progress in (("emerald_wilds",70),("ashen_highlands",70),("frostveil_reach",70),("astral_scar",55)):
            self.db.execute("INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES (?,?,?,?) ON CONFLICT(player_id,region_id) DO UPDATE SET progress=excluded.progress,stages_cleared=excluded.stages_cleared", ("144", region_id, progress, 8))

    def tearDown(self) -> None:
        self.db.close(); self.tmp.cleanup()

    def test_alpha4_keeps_schema10_protocol24_and_adds_fourth_dungeon(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 17)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 34)
        board = self.game._dungeon_board_state("144")
        self.assertEqual([row["id"] for row in board["dungeons"]], ["forgotten_ossuary", "emberglass_foundry", "whiteglass_bastion", "riftglass_observatory"])
        rift = board["dungeons"][-1]
        self.assertTrue(rift["unlocked"])
        self.assertEqual(rift["rooms"], 10)
        self.assertEqual(rift["choice_rooms"], 2)
        self.assertEqual(rift["event_rooms"], 1)
        self.assertEqual(rift["identity"], "Anomalies & Pressure")

    def test_riftglass_unlock_uses_astral_scar_exploration(self):
        self.db.execute("UPDATE player_region_exploration SET progress=54 WHERE player_id='144' AND region_id='astral_scar'")
        entry = next(row for row in self.game._dungeon_board_state("144")["dungeons"] if row["id"] == "riftglass_observatory")
        self.assertFalse(entry["unlocked"])
        self.assertTrue(any("Astral Scar" in row and "55%" in row for row in entry["missing"]))

    def test_event_room_resolves_one_persistent_outcome(self):
        self.assertTrue(self.game.dungeon_start("144", "riftglass_observatory").ok)
        state = self.game._dungeon_load("144")
        state["room_index"] = 2
        self.game._dungeon_save("144", state)
        result = self.game._dungeon_begin_room("144", state)
        self.assertTrue(result.ok)
        public = self.game._dungeon_public("144")
        self.assertEqual(public["room"]["type"], "event")
        self.assertEqual(public["status"], "choice")
        self.assertTrue(public["event"].get("outcome_id"))
        self.assertTrue(public["discoveries"])

    def test_miniboss_combat_rules_apply_status_without_round_defeat_limit(self):
        self.assertTrue(self.game.dungeon_start("144", "riftglass_observatory").ok)
        state = self.game._dungeon_load("144")
        state["room_index"] = 6
        self.game._dungeon_save("144", state)
        self.game._dungeon_begin_room("144", state)
        public = self.game._dungeon_public("144")
        self.assertEqual(public["combat"]["max_rounds"], 0)
        self.assertIn("Protect", public["combat"]["enemy"]["statuses"])
        self.assertFalse(any("defeat it within" in row.lower() for row in public["combat"]["mechanics"]))

    def test_boss_opening_resource_drain_is_persisted_in_run_state(self):
        self.assertTrue(self.game.dungeon_start("144", "riftglass_observatory").ok)
        state = self.game._dungeon_load("144")
        state["room_index"] = 9
        self.game._dungeon_save("144", state)
        self.game._dungeon_begin_room("144", state)
        public = self.game._dungeon_public("144")
        self.assertEqual(public["combat"]["max_rounds"], 0)
        self.assertTrue(public["combat"]["opening_effects"])
        self.assertTrue(any("Aperture drain" in row for row in public["combat"]["mechanics"]))


if __name__ == "__main__":
    unittest.main()

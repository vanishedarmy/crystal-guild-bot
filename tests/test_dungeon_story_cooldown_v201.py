from __future__ import annotations

import random
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.dungeons import DUNGEON_COOLDOWN_SECONDS, generate_dungeon_run_rooms
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class DungeonStoryCooldownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GameData(ROOT / "data")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, self.data, rng=random.Random(77),
                                       overlay_state_path=str(Path(self.tmp.name) / "state.json"))
        self.assertTrue(self.game.recruit("901", "storyhero", "Storyhero").ok)
        self.assertTrue(self.game.choose_job("901", "warrior").ok)
        self.db.execute("UPDATE players SET level=99,current_hp=2000 WHERE twitch_id='901'")
        for region in ("emerald_wilds", "ashen_highlands", "frostveil_reach", "astral_scar"):
            self.db.execute("INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES ('901', ?, 95, 10)", (region,))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_ten_dungeons_have_distinct_saved_scene_flavor(self):
        self.assertEqual(len(self.data.dungeons) + len(self.data.ascension_dungeons), 10)
        for dungeon in [*self.data.dungeons.values(), *self.data.ascension_dungeons.values()]:
            plans = [generate_dungeon_run_rooms(dungeon, self.data.monsters, random.Random(seed)) for seed in range(5)]
            self.assertTrue(all(plan[0].get("story_title") for plan in plans), dungeon["id"])
            self.assertTrue(all(plan[0].get("story_mood") for plan in plans), dungeon["id"])
            for plan in plans:
                self.assertEqual(plan[-1]["monster_id"], dungeon["rooms"][-1]["monster_id"])
                self.assertTrue(all(room.get("story_chapter") for room in plan))
                self.assertTrue(all(room.get("story") for room in plan))
            self.assertGreater(len({tuple(room["story"] for room in plan) for plan in plans}), 1, dungeon["id"])

    def test_retreat_sets_shared_ten_minute_cooldown_and_survives_restart(self):
        self.assertEqual(DUNGEON_COOLDOWN_SECONDS, 600)
        self.assertTrue(self.game.dungeon_start("901", "forgotten_ossuary").ok)
        run = self.game._dungeon_public("901")
        self.assertIn("story_title", run)
        self.assertTrue(run["room"].get("story"))
        self.assertTrue(self.game.dungeon_retreat("901").ok)
        board = self.game._dungeon_board_state("901")
        self.assertGreaterEqual(board["cooldown_remaining"], 598)
        self.assertEqual(board["cooldown_duration"], 600)
        self.assertGreater(board["cooldown_until"], int(time.time()))
        for target in ("forgotten_ossuary", "emberglass_foundry"):
            result = self.game.dungeon_start("901", target)
            self.assertFalse(result.ok)
            self.assertIn("10-minute rest", " ".join(result.messages))
        restarted = CrystalGuildEngine(self.db, self.data, rng=random.Random(88),
                                       overlay_state_path=str(Path(self.tmp.name) / "other.json"))
        self.assertFalse(restarted.dungeon_start("901", "emberglass_foundry").ok)
        self.db.execute("UPDATE cooldowns SET available_at=? WHERE player_id='901' AND action='dungeon'", (int(time.time())-1,))
        self.assertTrue(restarted.dungeon_start("901", "emberglass_foundry").ok)

    def test_defeat_and_clear_both_set_cooldown(self):
        for outcome in ("defeat", "complete"):
            self.db.execute("UPDATE cooldowns SET available_at=0 WHERE player_id='901' AND action='dungeon'")
            self.assertTrue(self.game.dungeon_start("901", "forgotten_ossuary").ok)
            state = self.game._dungeon_load("901")
            finished = self.game._dungeon_finish("901", state, outcome=outcome)
            self.assertTrue(finished.ok)
            self.assertEqual(finished.data["dungeon_result"]["cooldown_seconds"], 600)
            self.assertGreater(self.game._cooldown_remaining("901", "dungeon"), 0)

    def test_portal_action_rejects_cooldown_and_job_trial_remains_exempt(self):
        self.assertTrue(self.game.dungeon_start("901", "forgotten_ossuary").ok)
        self.assertTrue(self.game.dungeon_retreat("901").ok)
        reply = self.game.portal_dungeon_start("901", "emberglass_foundry", "rest-portal-901")
        self.assertFalse(reply.ok)
        self.assertIn("10-minute rest", " ".join(reply.messages))
        self.assertGreater(reply.data["adventure_state"]["dungeons"]["cooldown_remaining"], 0)
        # Trial level and quest gates are separately tested; here only verify
        # that the Dungeon rest key does not block the Job Trial entry path.
        with patch.object(self.game, "_dungeon_unlock", return_value=(True, [])):
            trial = self.game.dungeon_start("901", "ascension_warrior_60")
        self.assertTrue(trial.ok, trial.messages)
        self.assertEqual(self.game._dungeon_load("901")["dungeon_id"], "ascension_warrior_60")
        self.assertTrue(self.game.dungeon_retreat("901").ok)
        self.assertGreater(self.game._dungeon_rest_status("901")[0], 0)

    def test_legacy_rooms_still_resolve_without_story_fields(self):
        self.assertTrue(self.game.dungeon_start("901", "forgotten_ossuary").ok)
        state = self.game._dungeon_load("901")
        state.pop("run_rooms", None)
        self.game._dungeon_save("901", state)
        current = self.game._dungeon_public("901")
        self.assertFalse(current["variable_route"])
        self.assertEqual(current["room"]["story"], "")


if __name__ == "__main__":
    unittest.main()

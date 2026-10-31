"""v1.9.97.6 regression checks for newly switched Jobs and reward isolation."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from crystal_guild.balance import encounter_reward_factor, jp_reward_factor
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]

class JobLevelRewardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "test.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0, venture_treasure_chance=0)
        self.game.recruit("a", "veteran", "Veteran")
        self.game.choose_job("a", "warrior")
        self.db.execute("UPDATE players SET level=99 WHERE twitch_id='a'")
        self.db.execute("UPDATE player_jobs SET level=1,jp=0 WHERE player_id='a' AND job_id='warrior'")
    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def test_character_level_99_no_longer_reduces_jp_for_fresh_job(self):
        enemy = dict(self.game.data.monsters["goblin"])
        enemy.update({"drops": [],"pity_drops": [], "recipe_drops": [], "gil":100, "xp":100, "jp":100})
        class FixedRng:
            def uniform(self, a, b): return 1.0
            def random(self): return 1.0
        self.game.rng = FixedRng()
        self.assertEqual(jp_reward_factor(99, 1, int(enemy["level"])), jp_reward_factor(1, 1, int(enemy["level"])))
        res = self.game._award_victory("a",self.game._player("a"),enemy)
        self.assertEqual(res["xp"], max(5, int(100*encounter_reward_factor(99,int(enemy["level"])))))
        self.assertEqual(res["jp"], max(2, int(100*jp_reward_factor(99,1,int(enemy["level"])))))
        self.assertEqual(res["gil"], max(1, int(100*encounter_reward_factor(99,int(enemy["level"])))))
        self.assertGreater(res["jp"],res["xp"])

    def test_combat_reward_modes_use_same_job_based_factor(self):
        enemy = dict(self.game.data.monsters["goblin"])
        enemy.update({"drops":[], "pity_drops":[], "recipe_drops":[], "xp":100, "jp":100,"gil":100})
        d = self.game._dungeon_reward_for_monster("a", enemy, 1)
        self.assertGreater(d["jp"], d["xp"])
        with patch.object(self.game, "_expedition_reward_multiplier", return_value=1.0):
            e = self.game._expedition_combat_rewards("a", {}, enemy)
        self.assertGreater(e["jp"], e["xp"])

    def test_repeat_dungeon_bonus_uses_job_level(self):
        state={"dungeon_id":"forgotten_ossuary", "cache":{"xp":0,"jp":0,"gil":0,"items":[]}}
        # The early Ossuary is repeatable and reveals the major old Lv.99
        # penalty (and this test must not silently skip on the catalog).
        dungeon=self.game.data.dungeons["forgotten_ossuary"]
        state["dungeon_id"] = dungeon["id"]
        output = self.game._dungeon_bank("a",state,1.0, include_completion_bonus=True)
        self.assertGreaterEqual(output["jp"], 0)
        self.assertGreater(output["jp"], 0)
        expected_jp = int(int(dungeon.get("completion_bonus",{}).get("jp",0)) * jp_reward_factor(99,1,int(dungeon.get("recommended_level") or dungeon.get("min_level") or 1)))
        self.assertEqual(output["jp"], expected_jp)
        self.assertEqual(output["xp"], int(int(dungeon.get("completion_bonus",{}).get("xp",0)) * encounter_reward_factor(99,int(dungeon.get("recommended_level") or dungeon.get("min_level") or 1))))

    def test_real_job_change_keeps_char_level_but_resets_jp_scaling(self):
        switched = self.game.choose_job("a", "whitemage")
        self.assertTrue(switched.ok, switched.messages)
        player = self.game._player("a")
        self.assertEqual(int(player["level"]), 99)
        self.assertEqual(str(player["current_job"]), "whitemage")
        self.assertEqual(self.game._job_level("a", "whitemage"), 1)
        self.assertEqual(jp_reward_factor(player["level"],self.game._job_level("a", "whitemage"),1), 1.0)

    def test_high_job_low_enemy_still_capped(self):
        self.assertEqual(jp_reward_factor(99,99,1),0.05)
        self.assertEqual(jp_reward_factor(1,99,1),0.05)

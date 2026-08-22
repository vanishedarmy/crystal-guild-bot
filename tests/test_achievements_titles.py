from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository


ROOT = Path(__file__).resolve().parents[1]


class AchievementTitleExpansionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.db"
        self.db = Database(self.db_path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0, venture_treasure_chance=0.0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(4),
        )
        self.game.recruit("1", "van", "Van")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_v084_catalog_has_tiers_points_and_expanded_titles(self):
        self.assertGreaterEqual(len(self.game.data.achievements), 60)
        self.assertGreaterEqual(len(self.game.data.titles), 75)
        for achievement in self.game.data.achievements.values():
            self.assertIn(achievement["tier"], {"bronze", "silver", "gold", "crystal"})
            self.assertGreater(int(achievement["points"]), 0)
            self.assertTrue(achievement["category"])

    def test_v084_record_achievement_unlocks_reward_title(self):
        self.db.add_record_stat("1", "damage_dealt", 100000)
        result = self.game.achievements("1", "combat")
        self.assertTrue(result.ok)
        unlocked = self.db.one(
            "SELECT 1 FROM achievements WHERE player_id='1' AND achievement_id='damage_100k'"
        )
        title = self.db.one(
            "SELECT 1 FROM player_titles WHERE player_id='1' AND title_id='damage_dealer'"
        )
        self.assertIsNotNone(unlocked)
        self.assertIsNotNone(title)
        self.assertIn("AP", result.messages[0])

    def test_v084_secret_achievement_is_hidden_until_unlocked(self):
        locked = self.game.achievement("1", "grudge magnet")
        self.assertTrue(locked.ok)
        self.assertIn("SECRET ACHIEVEMENT", locked.messages[0])
        self.db.record_monster_result("1", "tonberry", won=False, knocked_out=True)
        for _ in range(9):
            self.db.record_monster_result("1", "tonberry", won=False, knocked_out=True)
        self.game.achievements("1")
        unlocked = self.game.achievement("1", "grudge magnet")
        self.assertIn("Grudge Magnet", unlocked.messages[0])
        self.assertIn("UNLOCKED", unlocked.messages[0])

    def test_v084_title_filter_and_equip_work(self):
        self.game._unlock_title("1", "damage_dealer")
        listing = self.game.titles("1", "combat")
        self.assertTrue(listing.ok)
        self.assertIn("Damage Dealer", " ".join(listing.messages))
        equipped = self.game.set_title("1", "damage dealer")
        self.assertTrue(equipped.ok)
        self.assertEqual(self.db.one("SELECT title FROM players WHERE twitch_id='1'")["title"], "Damage Dealer")

    def test_v084_snapshot_includes_progress_points_and_title_collection(self):
        self.db.add_record_stat("1", "damage_dealt", 50000)
        repo = PortalRepository(self.db_path, ROOT / "data")
        payload = repo.achievements("van")
        self.assertIsNotNone(payload)
        by_id = {item["id"]: item for item in payload["achievements"]}
        damage = by_id["damage_100k"]
        self.assertEqual(damage["progress"]["value"], 50000)
        self.assertEqual(damage["progress"]["target"], 100000)
        self.assertIn("points_total", payload["summary"])
        self.assertEqual(len(payload["titles"]), len(self.game.data.titles))
        secret = {item["id"]: item for item in payload["achievements"]}["tonberry_ko_10"]
        self.assertTrue(secret["progress"]["hidden"])
        self.assertIsNone(secret["reward_title"])


if __name__ == "__main__":
    unittest.main()

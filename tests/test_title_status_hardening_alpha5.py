from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.portal_sync import PortalSyncClient

ROOT = Path(__file__).resolve().parents[1]


class TitleStatusHardeningAlpha5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self) -> None:
        try:
            self.db.close()
        finally:
            self.temp.cleanup()

    def test_existing_achievement_repairs_missing_reward_title(self):
        self.db.execute(
            "INSERT OR IGNORE INTO achievements(player_id,achievement_id) VALUES ('100','warrior_of_light')"
        )
        self.db.execute("DELETE FROM player_titles WHERE player_id='100' AND title_id='warrior_of_light'")
        self.game.reconcile_achievements("100")
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='warrior_of_light'"
        ))

    def test_dependent_achievement_unlocks_in_same_reconciliation_pass(self):
        # Put the dependent achievement first to prove evaluation is no longer
        # dependent on JSON/dict ordering.
        self.game.data.titles["hardening_chain_title"] = {
            "id": "hardening_chain_title",
            "name": "Chain Reconciled",
            "description": "Test-only title.",
            "category": "HardeningTest",
            "rarity": "common",
            "source": "Achievement",
        }
        original = self.game.data.achievements
        self.game.data.achievements = {
            "hardening_chain_master": {
                "id": "hardening_chain_master",
                "name": "Chain Master",
                "description": "Test-only dependent achievement.",
                "condition": {"type": "achievement_category_count", "category": "HardeningTest", "amount": 1},
                "reward_title": "hardening_chain_title",
                "category": "HardeningTest",
                "tier": "silver",
                "points": 25,
                "secret": False,
            },
            "hardening_chain_source": {
                "id": "hardening_chain_source",
                "name": "Chain Source",
                "description": "Test-only source achievement.",
                "condition": {"type": "character_level", "amount": 1},
                "category": "HardeningTest",
                "tier": "bronze",
                "points": 10,
                "secret": False,
            },
            **original,
        }
        try:
            self.game.reconcile_achievements("100")
            self.assertIsNotNone(self.db.one(
                "SELECT 1 FROM achievements WHERE player_id='100' AND achievement_id='hardening_chain_source'"
            ))
            self.assertIsNotNone(self.db.one(
                "SELECT 1 FROM achievements WHERE player_id='100' AND achievement_id='hardening_chain_master'"
            ))
            self.assertIsNotNone(self.db.one(
                "SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='hardening_chain_title'"
            ))
        finally:
            self.game.data.achievements = original
            self.game.data.titles.pop("hardening_chain_title", None)

    def test_portal_snapshot_reports_expedition_progress_used_by_achievement_engine(self):
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES ('100','emerald_wilds',100,8) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=100,stages_cleared=8"
        )
        self.game.reconcile_achievements("100")
        repo = PortalRepository(self.path, ROOT / "data")
        payload = repo.achievements("van")
        repo.close()
        row = next(item for item in payload["achievements"] if item["id"] == "master_emerald_wilds")
        self.assertTrue(row["unlocked"])
        self.assertEqual(row["progress"]["raw_value"], 100)
        self.assertEqual(row["progress"]["percent"], 100)

    def test_portal_sync_reconciles_before_building_player_snapshot(self):
        # Simulate an older profile already satisfying a newly introduced title
        # without requiring another gameplay action.
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='100'")
        self.db.execute("DELETE FROM achievements WHERE player_id='100' AND achievement_id='warrior_of_light'")
        self.db.execute("DELETE FROM player_titles WHERE player_id='100' AND title_id='warrior_of_light'")
        repo = PortalRepository(self.path, ROOT / "data")
        client = PortalSyncClient(
            repo,
            "https://example.invalid",
            "test-key",
            player_prepare=self.game.reconcile_achievements,
        )
        payload = client.build_snapshot("van")
        repo.close()
        achievement = next(
            row for row in payload["snapshot"]["achievements"]["achievements"]
            if row["id"] == "warrior_of_light"
        )
        title = next(
            row for row in payload["snapshot"]["achievements"]["titles"]
            if row["id"] == "warrior_of_light"
        )
        self.assertTrue(achievement["unlocked"])
        self.assertTrue(title["unlocked"])


    def test_unlocked_reversible_requirement_stays_visually_complete(self):
        self.db.execute("UPDATE players SET gil=100000 WHERE twitch_id='100'")
        self.game.reconcile_achievements("100")
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM achievements WHERE player_id='100' AND achievement_id='gil_100k'"
        ))
        self.db.execute("UPDATE players SET gil=0 WHERE twitch_id='100'")
        repo = PortalRepository(self.path, ROOT / "data")
        payload = repo.achievements("van")
        repo.close()
        row = next(item for item in payload["achievements"] if item["id"] == "gil_100k")
        self.assertTrue(row["unlocked"])
        self.assertEqual(row["progress"]["value"], row["progress"]["target"])
        self.assertEqual(row["progress"]["percent"], 100)
        detail = self.game.achievement("100", "gil 100k")
        self.assertTrue(detail.ok)
        self.assertIn("remains permanently unlocked", detail.messages[1])

    def test_engine_startup_reconciles_existing_player_progress(self):
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='100'")
        self.db.execute("DELETE FROM achievements WHERE player_id='100' AND achievement_id='warrior_of_light'")
        self.db.execute("DELETE FROM player_titles WHERE player_id='100' AND title_id='warrior_of_light'")
        self.db.close()
        self.db = Database(self.path)
        CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay2.json"),
        )
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM achievements WHERE player_id='100' AND achievement_id='warrior_of_light'"
        ))
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='warrior_of_light'"
        ))


if __name__ == "__main__":
    unittest.main()

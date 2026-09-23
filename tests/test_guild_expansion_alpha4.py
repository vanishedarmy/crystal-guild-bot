from __future__ import annotations

import random
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class GuildExpansionAlpha4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.db_path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(71),
        )
        self.game.recruit("1", "van", "Van")
        self.game.fellowship_system.ensure_member("1")
        self.db.execute("UPDATE fellowship_state SET level=8,renown=27000 WHERE singleton_id=1")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_schema9_adds_persistent_airship_tables_without_reset(self):
        self.assertEqual(self.db.schema_version(), 22)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='fellowship_airship_state'"))
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='fellowship_airship_upgrades'"))
        self.assertEqual(int(self.db.one("SELECT COUNT(*) AS n FROM players")["n"]), 1)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 37)

    def test_direct_alpha3_schema8_upgrade_preserves_progress_and_adds_airship(self):
        path = Path(self.tmp.name) / "alpha3-schema8.db"
        legacy = Database(path)
        try:
            game = CrystalGuildEngine(
                legacy,
                GameData(ROOT / "data"),
                overlay_state_path=str(Path(self.tmp.name) / "a3-overlay.json"),
                rng=random.Random(72),
            )
            game.recruit("808", "legacy", "Legacy")
            game.choose_job("808", "warrior")
            legacy.execute("UPDATE players SET level=37,gil=54321 WHERE twitch_id='808'")
            legacy.execute("UPDATE fellowship_state SET level=8,renown=25000 WHERE singleton_id=1")
            legacy.execute("UPDATE fellowship_facilities SET tier=2 WHERE facility_id='workshop'")
            with legacy.tx() as conn:
                conn.execute("DELETE FROM schema_migrations WHERE version=9")
                conn.execute("DROP TABLE IF EXISTS fellowship_airship_mission_history")
                conn.execute("DROP TABLE IF EXISTS fellowship_airship_mission_members")
                conn.execute("DROP TABLE IF EXISTS fellowship_airship_upgrades")
                conn.execute("DROP TABLE IF EXISTS fellowship_airship_state")
        finally:
            legacy.close()

        upgraded = Database(path)
        try:
            self.assertEqual(upgraded.schema_version(), 22)
            player = upgraded.one("SELECT level,gil FROM players WHERE twitch_id='808'")
            self.assertEqual((int(player["level"]), int(player["gil"])), (37, 54321))
            self.assertEqual(int(upgraded.one("SELECT tier FROM fellowship_facilities WHERE facility_id='workshop'")["tier"]), 2)
            self.assertEqual(int(upgraded.one("SELECT built FROM fellowship_airship_state WHERE singleton_id=1")["built"]), 0)
            self.assertEqual(int(upgraded.one("SELECT COUNT(*) AS n FROM fellowship_airship_upgrades")["n"]), 5)
            self.assertIsNotNone(upgraded.pre_migration_backup_path)
            self.assertIn("pre_schema_9", Path(upgraded.pre_migration_backup_path).name)
            self.assertEqual(upgraded.quick_check(), [])
        finally:
            upgraded.close()

    def test_airship_dock_and_airship_construction_unlock_in_sequence(self):
        self.db.execute("UPDATE fellowship_facilities SET tier=2 WHERE facility_id='guild_hall'")
        available = {item["id"] for item in self.game.fellowship_system.available_projects()}
        self.assertIn("airship_dock_t1", available)
        self.assertNotIn("crystal_guild_airship", available)
        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='airship_dock'")
        available = {item["id"] for item in self.game.fellowship_system.available_projects()}
        self.assertIn("crystal_guild_airship", available)

        ok, message, project = self.game.fellowship_system.set_active_project("crystal guild airship")
        self.assertTrue(ok, message)
        self.assertEqual(project["id"], "crystal_guild_airship")
        for requirement in project["requirements"]:
            if requirement["kind"] != "level":
                self.db.execute(
                    "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES (?,?,?) ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=excluded.current",
                    (project["id"], requirement["key"], requirement["target"]),
                )
        notes = self.game.fellowship_system._check_project_completion("1")
        self.assertTrue(any("AIRSHIP COMPLETE" in note for note in notes), notes)
        self.assertEqual(int(self.db.one("SELECT built FROM fellowship_airship_state WHERE singleton_id=1")["built"]), 1)

    def test_airship_mission_progress_waits_for_return_then_rewards_once(self):
        self.db.execute("UPDATE fellowship_airship_state SET built=1 WHERE singleton_id=1")
        before_player = self.db.one("SELECT gil FROM players WHERE twitch_id='1'")
        before_member = self.db.one("SELECT renown FROM fellowship_members WHERE player_id='1'")
        before_guild = self.db.one("SELECT renown FROM fellowship_state WHERE singleton_id=1")
        ok, message, active = self.game.fellowship_system.start_airship_mission("merchant escort")
        self.assertTrue(ok, message)
        self.assertEqual(active["id"], "merchant_escort")
        run_id = active["run_id"]
        self.game.fellowship_system.record_activity("1", "venture_complete", amount=50, event_key="a4:escort:progress")
        state = self.db.one("SELECT progress,target,active_run_id FROM fellowship_airship_state WHERE singleton_id=1")
        self.assertEqual(int(state["progress"]), int(state["target"]))
        self.assertEqual(str(state["active_run_id"]), run_id)
        # Meeting the objective does not pay immediately; the deployment must return.
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]), int(before_player["gil"]))
        self.db.execute("UPDATE fellowship_airship_state SET ends_at=? WHERE singleton_id=1", (int(time.time()) - 1,))
        snapshot = self.game.fellowship_system.airship_snapshot()
        self.assertIsNone(snapshot["active_mission"])
        self.assertEqual(snapshot["missions_completed"], 1)
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]), int(before_player["gil"]) + 750)
        self.assertEqual(int(self.db.one("SELECT renown FROM fellowship_members WHERE player_id='1'")["renown"]), int(before_member["renown"]) + 25 + 8)
        self.assertGreaterEqual(int(self.db.one("SELECT renown FROM fellowship_state WHERE singleton_id=1")["renown"]), int(before_guild["renown"]) + 600)
        history = self.db.one("SELECT outcome,participant_count FROM fellowship_airship_mission_history WHERE run_id=?", (run_id,))
        self.assertEqual(history["outcome"], "success")
        self.assertEqual(int(history["participant_count"]), 1)
        # Re-reading state cannot duplicate a settled reward.
        self.game.fellowship_system.airship_snapshot()
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]), int(before_player["gil"]) + 750)

    def test_airship_upgrades_change_mission_profile_and_unlock_advanced_missions(self):
        self.db.execute("UPDATE fellowship_airship_state SET built=1 WHERE singleton_id=1")
        for upgrade_id, tier in {"hull": 3, "engine": 3, "cargo": 2, "survey": 2, "crystal_core": 2}.items():
            self.db.execute("UPDATE fellowship_airship_upgrades SET tier=? WHERE upgrade_id=?", (tier, upgrade_id))
        snapshot = self.game.fellowship_system.airship_snapshot()
        escort = next(m for m in snapshot["missions"] if m["id"] == "merchant_escort")
        relic = next(m for m in snapshot["missions"] if m["id"] == "relic_recovery")
        self.assertLess(escort["target_effective"], 50)
        self.assertLess(escort["duration_seconds"], 24 * 3600)
        self.assertTrue(relic["unlocked"])
        upgrades = {item["id"]: item["tier"] for item in snapshot["upgrades"]}
        self.assertEqual(upgrades["crystal_core"], 2)

    def test_airship_upgrade_projects_follow_dock_level(self):
        self.db.execute("UPDATE fellowship_airship_state SET built=1 WHERE singleton_id=1")
        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='airship_dock'")
        available = {item["id"] for item in self.game.fellowship_system.available_projects()}
        self.assertIn("airship_hull_t1", available)
        self.assertNotIn("airship_hull_t2", available)
        self.db.execute("UPDATE fellowship_airship_upgrades SET tier=1 WHERE upgrade_id='hull'")
        self.db.execute("UPDATE fellowship_facilities SET tier=2 WHERE facility_id='airship_dock'")
        available = {item["id"] for item in self.game.fellowship_system.available_projects()}
        self.assertIn("airship_hull_t2", available)


if __name__ == "__main__":
    unittest.main()

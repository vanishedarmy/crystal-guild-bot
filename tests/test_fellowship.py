from __future__ import annotations

import random
import sqlite3
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database, SCHEMA
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.fellowship import guild_rank_for_renown

ROOT = Path(__file__).resolve().parents[1]


class FellowshipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(17),
        )
        self.game.recruit("1", "van", "Van")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_fellowship_starts_at_plain_lvl_one_and_new_recruits_are_not_founders(self):
        snapshot = self.game.fellowship_system.public_snapshot()
        member = self.game.fellowship_system.member_snapshot("1")
        self.assertEqual(snapshot["level"], 1)
        self.assertEqual(snapshot["level_label"], "LVL 1")
        self.assertFalse(member["founding_member"])
        self.assertEqual(member["rank"]["name"], "Recruit")
        self.assertEqual(self.db.schema_version(), 6)

    def test_duplicate_activity_event_does_not_double_award_renown(self):
        first = self.game.fellowship_system.record_activity("1", "venture_complete", event_key="venture:once")
        second = self.game.fellowship_system.record_activity("1", "venture_complete", event_key="venture:once")
        self.assertEqual(second, [])
        member = self.game.fellowship_system.member_snapshot("1")
        guild = self.game.fellowship_system.public_snapshot()
        self.assertEqual(member["renown"], 8)
        self.assertEqual(guild["renown"], 8)
        self.assertIsInstance(first, list)

    def test_player_renown_earns_ff14_style_guild_rank_and_shared_level_stays_numeric(self):
        notes = self.game.fellowship_system.record_activity(
            "1", "job_mastery", event_key="mastery:test", renown=1_000
        )
        member = self.game.fellowship_system.member_snapshot("1")
        guild = self.game.fellowship_system.public_snapshot()
        self.assertEqual(member["rank"]["name"], guild_rank_for_renown(1_000)["name"])
        self.assertEqual(member["rank"]["name"], "Corporal")
        self.assertEqual(guild["level_label"], "LVL 2")
        self.assertTrue(any("GUILD RANK UP" in note for note in notes))
        self.assertTrue(any("FELLOWSHIP LEVEL UP" in note for note in notes))

    def test_contribution_caps_at_remaining_requirement_and_is_transactional(self):
        self.assertTrue(self.game.set_fellowship_project("infirmary").ok)
        self.db.execute("UPDATE players SET gil=10000 WHERE twitch_id='1'")
        result = self.game.contribute_fellowship("1", "gil 99999")
        self.assertTrue(result.ok, result.messages)
        player = self.db.one("SELECT gil FROM players WHERE twitch_id='1'")
        progress = self.db.one(
            "SELECT current FROM fellowship_project_progress WHERE project_id='infirmary_t1' AND requirement_key='gil'"
        )
        contribution = self.db.one(
            "SELECT amount FROM fellowship_contributions WHERE player_id='1' ORDER BY id DESC LIMIT 1"
        )
        self.assertEqual(int(player["gil"]), 5_000)
        self.assertEqual(int(progress["current"]), 5_000)
        self.assertEqual(int(contribution["amount"]), 5_000)
        self.assertIn("excess stayed with you", result.messages[0])

    def test_facility_effects_remain_modest_and_bounded(self):
        for facility in ("infirmary", "workshop", "training_hall", "quartermaster"):
            self.db.execute("UPDATE fellowship_facilities SET tier=5 WHERE facility_id=?", (facility,))
        effects = self.game.fellowship_system.effects()
        self.assertEqual(round(effects["camp_reduction"], 2), 0.20)
        self.assertEqual(round(effects["forge_discount"], 2), 0.10)
        self.assertEqual(round(effects["jp_bonus"], 2), 0.05)
        self.assertEqual(round(effects["shop_refresh_reduction"], 2), 0.15)
        self.assertEqual(self.game.fellowship_system.effective_forge_gil(1000), 900)
        self.assertEqual(self.game.fellowship_system.apply_jp_bonus(100), 105)

    def test_project_completion_upgrades_facility_and_applies_shared_benefit(self):
        self.assertTrue(self.game.set_fellowship_project("infirmary").ok)
        self.db.execute(
            "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES ('infirmary_t1','gil',5000) "
            "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=5000"
        )
        self.db.execute(
            "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES ('infirmary_t1','item:hi_potion',10) "
            "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=10"
        )
        notes = []
        for index in range(20):
            notes.extend(self.game.fellowship_system.record_activity(
                "1", "venture_complete", event_key=f"venture:project:{index}"
            ))
        facility = self.db.one("SELECT tier FROM fellowship_facilities WHERE facility_id='infirmary'")
        state = self.db.one("SELECT active_project_id FROM fellowship_state WHERE singleton_id=1")
        member = self.game.fellowship_system.member_snapshot("1")
        self.assertEqual(int(facility["tier"]), 1)
        self.assertIsNone(state["active_project_id"])
        self.assertEqual(self.game.fellowship_system.effective_camp_seconds(1800), 1728)
        self.assertGreaterEqual(member["renown"], 160)
        self.assertEqual(member["rank"]["name"], "Private Third Class")
        self.assertTrue(any("PROJECT COMPLETE" in note for note in notes))


class FellowshipMigrationTests(unittest.TestCase):
    def test_schema_two_database_migrates_to_five_and_marks_existing_players_as_founders(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v105.db"
            conn = sqlite3.connect(path)
            conn.executescript(SCHEMA)
            conn.execute("INSERT INTO schema_migrations(version,name) VALUES (1,'legacy_baseline')")
            conn.execute("INSERT INTO schema_migrations(version,name) VALUES (2,'persistent_mp_ap')")
            conn.execute(
                "INSERT INTO players(twitch_id,username,display_name,current_job,current_hp,level,xp,gil,current_mp,current_ap) "
                "VALUES ('100','legacy','Legacy','warrior',81,17,4321,9876,7,9)"
            )
            conn.commit()
            conn.close()

            db = Database(path)
            try:
                self.assertEqual(db.schema_version(), 6)
                player = db.one("SELECT level,xp,gil,current_hp,current_mp,current_ap FROM players WHERE twitch_id='100'")
                self.assertEqual(tuple(player), (17, 4321, 9876, 81, 7, 9))
                member = db.one("SELECT founding_member,renown FROM fellowship_members WHERE player_id='100'")
                self.assertEqual(int(member["founding_member"]), 1)
                self.assertEqual(int(member["renown"]), 0)
                self.assertIsNotNone(db.pre_migration_backup_path)
                self.assertIn("pre_schema_6", Path(db.pre_migration_backup_path).name)
                self.assertTrue(Path(db.pre_migration_backup_path).exists())
                verify = sqlite3.connect(db.pre_migration_backup_path)
                try:
                    self.assertEqual(verify.execute("PRAGMA quick_check").fetchone()[0], "ok")
                    self.assertIsNotNone(verify.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='fellowship_state'"
                    ).fetchone())
                    self.assertIsNotNone(verify.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='player_chocobos'"
                    ).fetchone())
                    self.assertIsNotNone(verify.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='solo_expeditions'"
                    ).fetchone())
                    chocobo_cols = {row[1] for row in verify.execute("PRAGMA table_info(player_chocobos)").fetchall()}
                    self.assertNotIn("portrait_id", chocobo_cols)
                finally:
                    verify.close()
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()

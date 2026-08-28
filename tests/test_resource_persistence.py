from __future__ import annotations

import random
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild.active_battle import battle_ap, battle_mp
from crystal_guild.data import GameData
from crystal_guild.database import Database, SCHEMA
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class PersistentResourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            venture_cooldown_seconds=0, venture_treasure_chance=0.0,
            encounter_join_seconds=5,
            encounter_round_seconds=5,
            camp_rest_seconds=60,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(22),
        )
        self.game.recruit("1", "van", "Van")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_level_one_resource_pools_are_tactical_not_oversized(self):
        self.assertLessEqual(battle_mp({"mag": 12, "spr": 12}), 18)
        self.assertLessEqual(battle_ap({"str": 12, "dex": 12}), 18)

    def test_spent_mp_survives_finished_battle_and_next_battle(self):
        self.game.choose_job("1", "blackmage")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.game.start_encounter_battle(opened.data["encounter_id"])
        before = int(self.game.encounter_roster["1"]["mp"])
        self.assertTrue(self.game.battle_ability("1", "fire").ok)
        self.game.advance_encounter_round(opened.data["encounter_id"])
        persisted = int(self.db.one("SELECT current_mp FROM players WHERE twitch_id='1'")["current_mp"])
        self.assertEqual(persisted, before - 5)
        if self.game.active_encounter:
            self.game.abort_encounter()
        opened2 = self.game.venture("1", bypass_cooldown=True)
        self.game.start_encounter_battle(opened2.data["encounter_id"])
        self.assertEqual(int(self.game.encounter_roster["1"]["mp"]), persisted)

    def test_camp_can_start_for_depleted_ap_with_full_hp_and_restores_it(self):
        self.game.choose_job("1", "warrior")
        p = self.game._player("1")
        resources = self.game._resource_state_for(p)
        self.db.execute(
            "UPDATE players SET current_hp=?, current_ap=1 WHERE twitch_id='1'",
            (self.game._max_hp(p),),
        )
        result = self.game.rest("1")
        self.assertTrue(result.ok, result.messages)
        self.assertGreater(self.game._camp_remaining("1"), 0)
        self.db.execute("UPDATE players SET camp_until=? WHERE twitch_id='1'", (int(time.time()) - 1,))
        self.assertTrue(self.game.rest("1").ok)
        after = self.game._player("1")
        self.assertEqual(int(after["current_ap"]), int(resources["max_ap"]))

    def test_ether_and_stamina_items_have_field_recovery(self):
        self.game.choose_job("1", "blackmage")
        p = self.game._player("1")
        max_mp = int(self.game._resource_state_for(p)["max_mp"])
        self.db.execute("UPDATE players SET current_mp=1 WHERE twitch_id='1'")
        self.game._change_item("1", "ether", 1, "test")
        result = self.game.use_item("1", "ether")
        self.assertTrue(result.ok, result.messages)
        restored = int(self.game._player("1")["current_mp"])
        self.assertGreater(restored, 1)
        self.assertLessEqual(restored, max_mp)

        self.game.choose_job("1", "warrior")
        p = self.game._player("1")
        max_ap = int(self.game._resource_state_for(p)["max_ap"])
        self.db.execute("UPDATE players SET current_ap=1 WHERE twitch_id='1'")
        self.game._change_item("1", "stamina_draught", 1, "test")
        result = self.game.use_item("1", "stamina draught")
        self.assertTrue(result.ok, result.messages)
        restored_ap = int(self.game._player("1")["current_ap"])
        self.assertGreater(restored_ap, 1)
        self.assertLessEqual(restored_ap, max_ap)

    def test_tent_restores_depleted_resource_even_when_hp_is_full(self):
        self.game.choose_job("1", "warrior")
        p = self.game._player("1")
        resources = self.game._resource_state_for(p)
        self.db.execute(
            "UPDATE players SET current_hp=?, current_ap=0 WHERE twitch_id='1'",
            (self.game._max_hp(p),),
        )
        self.game._change_item("1", "tent", 1, "test")
        result = self.game.use_item("1", "tent")
        self.assertTrue(result.ok, result.messages)
        after = self.game._player("1")
        self.assertEqual(int(after["current_ap"]), int(resources["max_ap"]))


class ResourceMigrationTests(unittest.TestCase):
    def test_legacy_database_migrates_in_place_with_verified_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.db"
            legacy_schema = SCHEMA.replace(
                "    current_mp INTEGER,\n    current_ap INTEGER,\n",
                "",
            )
            conn = sqlite3.connect(path)
            conn.executescript(legacy_schema)
            conn.execute(
                "INSERT INTO players(twitch_id,username,display_name,current_job,current_hp) "
                "VALUES ('100','legacy','Legacy','blackmage',100)"
            )
            conn.commit()
            conn.close()

            db = Database(path)
            try:
                columns = {row[1] for row in db.conn.execute("PRAGMA table_info(players)").fetchall()}
                self.assertIn("current_mp", columns)
                self.assertIn("current_ap", columns)
                self.assertEqual(db.schema_version(), 8)
                self.assertIsNone(db.one("SELECT current_mp FROM players WHERE twitch_id='100'")["current_mp"])
                self.assertIsNotNone(db.pre_migration_backup_path)
                self.assertTrue(Path(db.pre_migration_backup_path).exists())
                verify = sqlite3.connect(db.pre_migration_backup_path)
                try:
                    self.assertEqual(verify.execute("PRAGMA quick_check").fetchone()[0], "ok")
                    legacy_columns = {row[1] for row in verify.execute("PRAGMA table_info(players)").fetchall()}
                    self.assertIn("current_mp", legacy_columns)
                    tables = {row[0] for row in verify.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                    self.assertIn("fellowship_state", tables)
                    self.assertIn("player_chocobos", tables)
                    self.assertIn("solo_expeditions", tables)
                    chocobo_columns = {row[1] for row in verify.execute("PRAGMA table_info(player_chocobos)").fetchall()}
                    self.assertIn("portrait_id", chocobo_columns)
                    self.assertIn("portal_adventure_results", tables)
                finally:
                    verify.close()
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()

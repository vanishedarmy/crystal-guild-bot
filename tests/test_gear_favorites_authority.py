from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class GearFavoritesAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
        )
        self.game.recruit("100", "van", "Van")
        self.worker = PortalActionWorker(self.game, "https://guild.example", "sync-key")

    def tearDown(self) -> None:
        self.db.close()
        self.temp.cleanup()

    def action(self, action_id: str, favorites: list[str]) -> dict:
        return {
            "id": action_id,
            "protocol_version": ACTION_PROTOCOL_VERSION,
            "twitch_id": "100",
            "username": "van",
            "type": "SET_GEAR_FAVORITES",
            "payload": {"favorites": favorites},
            "lease_token": "lease-token",
        }

    def test_portal_favorites_persist_in_player_database_and_snapshot(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 26)
        ok, message, data = self.worker._execute(
            self.action("pa_favorites_1", ["hunters_axe", "chain_mail", "hunters_axe"])
        )
        self.assertTrue(ok, message)
        self.assertEqual(data["favorite_item_ids"], ["hunters_axe", "chain_mail"])

        rows = self.db.all(
            "SELECT item_id FROM player_gear_favorites WHERE player_id='100' ORDER BY created_at,item_id"
        )
        self.assertEqual({str(row["item_id"]) for row in rows}, {"hunters_axe", "chain_mail"})

        repo = PortalRepository(self.path, ROOT / "data")
        try:
            snapshot = repo.inventory("van")
            self.assertIsNotNone(snapshot)
            self.assertEqual(set(snapshot["favorite_item_ids"]), {"hunters_axe", "chain_mail"})
        finally:
            repo.close()

    def test_favorites_action_is_replay_safe_and_rejects_non_equipment(self):
        action = self.action("pa_favorites_replay", ["hunters_axe", "chain_mail"])
        first = self.worker._execute(action)
        second = self.worker._execute(action)
        self.assertTrue(first[0], first[1])
        self.assertTrue(second[0], second[1])
        rows = self.db.all("SELECT item_id FROM player_gear_favorites WHERE player_id='100'")
        self.assertEqual(len(rows), 2)

        bad = self.worker._execute(self.action("pa_favorites_bad", ["potion"]))
        self.assertFalse(bad[0])
        self.assertIn("equippable", bad[1].lower())
        rows_after = self.db.all("SELECT item_id FROM player_gear_favorites WHERE player_id='100'")
        self.assertEqual(len(rows_after), 2)

    def test_empty_favorites_are_authoritative_and_persisted(self):
        self.assertTrue(self.worker._execute(self.action("pa_favorites_seed", ["hunters_axe"]))[0])
        cleared = self.worker._execute(self.action("pa_favorites_clear", []))
        self.assertTrue(cleared[0], cleared[1])
        self.assertEqual(cleared[2]["favorite_item_ids"], [])
        self.assertEqual(self.db.all("SELECT item_id FROM player_gear_favorites WHERE player_id='100'"), [])
        repo = PortalRepository(self.path, ROOT / "data")
        try:
            self.assertEqual(repo.inventory("van")["favorite_item_ids"], [])
        finally:
            repo.close()


class GearFavoritesMigrationTests(unittest.TestCase):
    def test_schema_15_database_migrates_through_16_to_17_with_verified_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "guild.db"
            db = Database(path)
            db.close()
            conn = sqlite3.connect(path)
            conn.execute("DROP TABLE player_gear_favorites")
            conn.execute("DELETE FROM schema_migrations WHERE version>=16")
            conn.commit()
            conn.close()

            migrated = Database(path)
            try:
                self.assertEqual(migrated.schema_version(), 23)
                table = migrated.conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='player_gear_favorites'"
                ).fetchone()
                self.assertIsNotNone(table)
                self.assertIsNotNone(migrated.pre_migration_backup_path)
                backup = Path(migrated.pre_migration_backup_path)
                self.assertTrue(backup.exists())
                self.assertIn("pre_schema_23_", backup.name)
                verify = sqlite3.connect(backup)
                try:
                    self.assertEqual(verify.execute("PRAGMA quick_check").fetchone()[0], "ok")
                    version = verify.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
                    self.assertEqual(int(version), 22)
                    tables = {row[0] for row in verify.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    self.assertIn("player_gear_favorites", tables)
                finally:
                    verify.close()
            finally:
                migrated.close()


if __name__ == "__main__":
    unittest.main()

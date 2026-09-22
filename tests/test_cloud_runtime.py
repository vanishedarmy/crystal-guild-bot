from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.cloud_runtime import (
    cloud_bootstrap_ready,
    copy_database_for_migration,
    create_startup_backup,
    prepare_cloud_storage,
)
from crystal_guild.config import Settings
from crystal_guild.database import Database
from crystal_guild.portal_sync import PortalSyncWorker
from crystal_guild.token_store import TwitchTokenStore, copy_token_database, extract_token_pairs, import_twitchio_json

ROOT = Path(__file__).resolve().parents[1]


BASE_ENV = {
    "TWITCH_CLIENT_ID": "client",
    "TWITCH_CLIENT_SECRET": "secret",
    "TWITCH_BOT_ID": "100",
    "TWITCH_OWNER_ID": "200",
}


class CloudRuntimeTests(unittest.TestCase):
    def settings(self, **values) -> Settings:
        env = dict(BASE_ENV)
        env.update(values)
        with patch.dict(os.environ, env, clear=True):
            return Settings.from_env()

    def test_local_defaults_remain_backward_compatible(self):
        settings = self.settings()
        self.assertEqual(settings.runtime_mode, "local")
        self.assertEqual(settings.database_path, "crystal_guild.db")
        self.assertEqual(settings.log_dir, "logs")
        self.assertFalse(settings.portal_sync_in_process)
        self.assertEqual(settings.twitch_token_db, "")

    def test_cloud_defaults_use_persistent_disk_and_integrated_sync(self):
        settings = self.settings(CRYSTAL_GUILD_RUNTIME_MODE="cloud")
        self.assertTrue(settings.cloud_runtime)
        self.assertEqual(settings.database_path, "/var/data/crystal_guild.db")
        self.assertEqual(settings.twitch_token_db, "/var/data/twitch_tokens.db")
        self.assertEqual(settings.log_dir, "/tmp/crystal-guild-logs")
        self.assertTrue(settings.portal_sync_in_process)
        self.assertTrue(settings.cloud_require_existing_database)

    def test_token_store_round_trip_and_refresh_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TwitchTokenStore(Path(tmp) / "tokens.db")
            store.upsert("100", "access-a", "refresh-a")
            store.upsert("200", "access-b", "refresh-b")
            store.upsert("100", "access-new", "refresh-new")
            self.assertEqual(store.count(), 2)
            rows = {row["user_id"]: row for row in store.load()}
            self.assertEqual(rows["100"]["access_token"], "access-new")
            self.assertEqual(rows["100"]["refresh_token"], "refresh-new")

    def test_token_json_import_supports_user_keyed_twitchio_shapes(self):
        payload = {
            "100": {"token": "bot-access", "refresh": "bot-refresh"},
            "200": {"access_token": "owner-access", "refresh_token": "owner-refresh"},
        }
        pairs = extract_token_pairs(payload)
        self.assertEqual({pair[0] for pair in pairs}, {"100", "200"})
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / ".tio.tokens.json"
            dst = Path(tmp) / "tokens.db"
            src.write_text(json.dumps(payload), encoding="utf-8")
            result = import_twitchio_json(src, dst, expected_user_ids=["100", "200"])
            self.assertEqual(result["stored"], 2)
            self.assertEqual(result["missing_expected_user_ids"], [])

    def test_token_json_import_supports_twitchio_pair_lists(self):
        payload = {"100": ["bot-access", "bot-refresh"], "200": ["owner-access", "owner-refresh"]}
        pairs = extract_token_pairs(payload)
        self.assertEqual({pair[0] for pair in pairs}, {"100", "200"})

    def test_token_json_import_replaces_stale_target_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "tokens.db"
            stale = TwitchTokenStore(target)
            stale.upsert("999", "old-access", "old-refresh")
            source = root / "tokens.json"
            source.write_text(
                json.dumps({"111": ["new-access", "new-refresh"]}),
                encoding="utf-8",
            )
            result = import_twitchio_json(source, target, expected_user_ids=["111"])
            self.assertEqual(result["stored"], 1)
            self.assertEqual(TwitchTokenStore(target).user_ids(), {"111"})

    def test_token_database_copy_is_read_only_and_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.db"
            store = TwitchTokenStore(source)
            store.upsert("100", "a", "r")
            store.upsert("200", "b", "r2")
            result = copy_token_database(source, Path(tmp) / "copy.db", expected_user_ids=["100", "200"])
            self.assertEqual(result["stored"], 2)
            self.assertEqual(result["missing_expected_user_ids"], [])

    def test_cloud_guard_refuses_missing_private_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.settings(
                CRYSTAL_GUILD_RUNTIME_MODE="cloud",
                DATABASE_PATH=str(Path(tmp) / "guild.db"),
                TWITCH_TOKEN_DB=str(Path(tmp) / "tokens.db"),
            )
            ready, missing = cloud_bootstrap_ready(settings)
            self.assertFalse(ready)
            self.assertTrue(any("authoritative database" in item for item in missing))
            self.assertTrue(any("token database" in item.lower() for item in missing))

    def test_cloud_guard_rejects_wrong_or_empty_database_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "guild.db"
            sqlite3.connect(db_path).close()
            token_path = Path(tmp) / "tokens.db"
            store = TwitchTokenStore(token_path)
            store.upsert("100", "a", "r")
            store.upsert("200", "a2", "r2")
            settings = self.settings(
                CRYSTAL_GUILD_RUNTIME_MODE="cloud",
                DATABASE_PATH=str(db_path),
                TWITCH_TOKEN_DB=str(token_path),
            )
            ready, missing = cloud_bootstrap_ready(settings)
            self.assertFalse(ready)
            self.assertTrue(any("players table missing" in item for item in missing))

    def test_cloud_guard_requires_bot_and_owner_token_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "guild.db"
            db = Database(db_path)
            db.close()
            token_path = Path(tmp) / "tokens.db"
            store = TwitchTokenStore(token_path)
            store.upsert("100", "a", "r")
            settings = self.settings(
                CRYSTAL_GUILD_RUNTIME_MODE="cloud",
                DATABASE_PATH=str(db_path),
                TWITCH_TOKEN_DB=str(token_path),
            )
            ready, missing = cloud_bootstrap_ready(settings)
            self.assertFalse(ready)
            self.assertTrue(any("broadcaster Twitch token" in item for item in missing))
            store.upsert("200", "a2", "r2")
            ready, missing = cloud_bootstrap_ready(settings)
            self.assertTrue(ready, missing)

    def test_cloud_storage_prunes_before_new_backup_and_removes_stale_partials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "guild.db"
            db = Database(db_path)
            db.close()
            backup_dir = root / "backups"
            backup_dir.mkdir()
            old = []
            for idx in range(5):
                path = backup_dir / f"crystal_guild-startup-20260101-00000{idx}.db"
                path.write_bytes(b"old")
                os.utime(path, (idx + 1, idx + 1))
                old.append(path)
            partial = backup_dir / ".crystal_guild-startup-stale.partial"
            partial.write_bytes(b"partial")
            settings = self.settings(
                CRYSTAL_GUILD_RUNTIME_MODE="cloud",
                DATABASE_PATH=str(db_path),
                TWITCH_TOKEN_DB=str(root / "tokens.db"),
            )
            removed = prepare_cloud_storage(settings, keep=2)
            self.assertFalse(partial.exists())
            self.assertEqual(len(list(backup_dir.glob("crystal_guild-startup-*.db"))), 1)
            self.assertGreaterEqual(len(removed), 5)

    def test_cloud_startup_backup_skips_when_disk_cannot_fit_safe_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "guild.db"
            db = Database(db_path)
            db.close()
            settings = self.settings(
                CRYSTAL_GUILD_RUNTIME_MODE="cloud",
                DATABASE_PATH=str(db_path),
                TWITCH_TOKEN_DB=str(root / "tokens.db"),
            )
            fake_usage = type("Usage", (), {"total": 1, "used": 1, "free": 0})()
            with patch("crystal_guild.cloud_runtime.shutil.disk_usage", return_value=fake_usage):
                target = create_startup_backup(settings)
            self.assertIsNone(target)
            self.assertEqual(list((root / "backups").glob("*.partial")), [])

    def test_cloud_startup_backup_creates_consistent_copy_and_caps_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "guild.db"
            db = Database(db_path)
            db.execute("INSERT INTO players(twitch_id,username,display_name) VALUES ('1','van','Van')")
            db.close()
            backup_dir = root / "backups"
            backup_dir.mkdir()
            for idx in range(3):
                old = backup_dir / f"crystal_guild-startup-20260101-00000{idx}.db"
                old.write_bytes(b"old")
                os.utime(old, (idx + 1, idx + 1))
            settings = self.settings(
                CRYSTAL_GUILD_RUNTIME_MODE="cloud",
                DATABASE_PATH=str(db_path),
                TWITCH_TOKEN_DB=str(root / "tokens.db"),
            )
            target = create_startup_backup(settings, keep=2, reserve_bytes=0)
            self.assertIsNotNone(target)
            assert target is not None
            with sqlite3.connect(target) as conn:
                self.assertEqual(conn.execute("PRAGMA quick_check").fetchone()[0], "ok")
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM players").fetchone()[0], 1)
            self.assertLessEqual(len(list(backup_dir.glob("crystal_guild-startup-*.db"))), 2)

    def test_database_migration_copy_is_sqlite_consistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.db"
            db = Database(source)
            db.execute("INSERT INTO players(twitch_id,username,display_name) VALUES ('1','van','Van')")
            db.close()
            target = copy_database_for_migration(source, Path(tmp) / "out" / "crystal_guild.db")
            with sqlite3.connect(target) as conn:
                self.assertEqual(conn.execute("PRAGMA quick_check").fetchone()[0], "ok")
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM players").fetchone()[0], 1)

    def test_cloud_storage_reclaim_runs_before_file_logging(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        self.assertLess(source.index("prepare_cloud_storage(settings)"), source.index("twitchio.utils.setup_logging"))

    def test_render_blueprint_defines_one_disk_backed_worker_without_secret_values(self):
        source = (ROOT / "render.yaml").read_text(encoding="utf-8")
        self.assertIn("type: worker", source)
        self.assertIn("mountPath: /var/data", source)
        self.assertIn("startCommand: python run_bot.py", source)
        self.assertIn("CRYSTAL_GUILD_RUNTIME_MODE", source)
        self.assertIn("/tmp/crystal-guild-logs", source)
        self.assertNotIn("value: /var/data/logs", source)
        self.assertIn("sync: false", source)
        self.assertNotIn("TWITCH_CLIENT_SECRET=", source)

    def test_cloud_setup_docs_preserve_existing_database_and_explain_matching_web(self):
        source = (ROOT / "RENDER_CLOUD_SETUP.md").read_text(encoding="utf-8")
        self.assertIn("v1.9.0 Alpha 7 Hall of Trophies Bot and matching Web build", source)
        upgrade = (ROOT / "UPGRADE_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("17 → 18", upgrade)
        self.assertIn("pre_schema_20", upgrade)
        self.assertIn("/var/data/crystal_guild.db", source)
        self.assertIn("/var/data/twitch_tokens.db", source)
        self.assertIn("run_cloud_preflight.py", source)
        self.assertIn("/overlay", source)


class PortalSyncWorkerTests(unittest.TestCase):
    def test_worker_runs_and_stops_cleanly(self):
        class Repository:
            def __init__(self): self.closed = False
            def close(self): self.closed = True

        class Client:
            interval = 0.01
            def __init__(self):
                self.repository = Repository()
                self.calls = 0
            def sync_once(self, **_kwargs):
                self.calls += 1
                return {"players": 1, "changed": 1 if self.calls == 1 else 0, "removed": 0}

        client = Client()
        worker = PortalSyncWorker(client)  # type: ignore[arg-type]
        worker.start()
        import time
        deadline = time.time() + 1.0
        while client.calls < 1 and time.time() < deadline:
            time.sleep(0.01)
        worker.stop()
        status = worker.status()
        self.assertGreaterEqual(client.calls, 1)
        self.assertEqual(status["state"], "stopped")
        self.assertTrue(client.repository.closed)


if __name__ == "__main__":
    unittest.main()

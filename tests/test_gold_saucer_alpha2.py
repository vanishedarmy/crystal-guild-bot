from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import MONSTER_TOSS_COST, MONSTER_TOSS_DAILY_GAMES, MONSTER_TOSS_THROWS
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class GoldSaucerAlpha2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), overlay_state_path=str(Path(self.temp.name) / "overlay.json"))
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_alpha2_contract_and_monster_toss_state(self):
        self.assertEqual(__version__, "1.9.0-records-moments-alpha10")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 23)
        self.assertEqual(self.db.schema_version(), 23)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 37)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='gold_saucer_monster_toss'"))
        state = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        toss = state["monster_toss"]
        self.assertEqual(toss["cost"], MONSTER_TOSS_COST)
        self.assertEqual(toss["throws_per_game"], MONSTER_TOSS_THROWS)
        self.assertEqual(toss["daily_games"], MONSTER_TOSS_DAILY_GAMES)
        self.assertTrue(next(row for row in state["attractions"] if row["id"] == "monster_toss")["status"] == "open")

    def test_monster_toss_persists_each_throw_and_replays_exactly_once(self):
        before = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["points"]
        started = self.game.portal_monster_toss_start("100", "toss-start-1")
        self.assertTrue(started.ok)
        self.assertEqual(started.data["gold_saucer_state"]["points"], before - MONSTER_TOSS_COST)
        game = started.data["gold_saucer_state"]["monster_toss"]["active_game"]
        self.assertEqual(game["throw_index"], 0)
        self.assertEqual(game["throws_remaining"], MONSTER_TOSS_THROWS)

        first = self.game.portal_monster_toss_throw("100", "medium_pot", "normal", "toss-throw-1")
        self.assertTrue(first.ok)
        after_first = first.data["gold_saucer_state"]["monster_toss"]["active_game"]
        self.assertEqual(after_first["throw_index"], 1)
        self.assertEqual(len(after_first["throws"]), 1)

        replay = self.game.portal_monster_toss_throw("100", "medium_pot", "normal", "toss-throw-1")
        self.assertTrue(replay.ok)
        replay_game = replay.data["gold_saucer_state"]["monster_toss"]["active_game"]
        self.assertEqual(replay_game["throw_index"], 1)
        self.assertEqual(len(replay_game["throws"]), 1)

        refreshed = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["monster_toss"]["active_game"]
        self.assertEqual(refreshed["id"], game["id"])
        self.assertEqual(refreshed["throw_index"], 1)

    def test_fifth_throw_settles_once_and_updates_records(self):
        self.assertTrue(self.game.portal_monster_toss_start("100", "toss-start-final").ok)
        final = None
        for index in range(MONSTER_TOSS_THROWS):
            final = self.game.portal_monster_toss_throw("100", "golden_cactuar", "safe", f"toss-final-{index}")
            self.assertTrue(final.ok)
        self.assertTrue(final.data["monster_toss_complete"])
        state = final.data["gold_saucer_state"]
        self.assertIsNone(state["monster_toss"]["active_game"])
        self.assertEqual(state["monster_toss"]["games_today"], 1)
        self.assertEqual(state["records"]["monster_toss_games"], 1)
        self.assertEqual(state["records"]["monster_toss_throws"], MONSTER_TOSS_THROWS)
        self.assertGreaterEqual(state["records"]["monster_toss_best_score"], 0)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='monster_toss'")["n"], 1)

        replay = self.game.portal_monster_toss_throw("100", "golden_cactuar", "safe", f"toss-final-{MONSTER_TOSS_THROWS-1}")
        self.assertTrue(replay.ok)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='monster_toss'")["n"], 1)

    def test_daily_limit_blocks_fourth_completed_game(self):
        for game_no in range(MONSTER_TOSS_DAILY_GAMES):
            self.assertTrue(self.game.portal_monster_toss_start("100", f"limit-start-{game_no}").ok)
            for throw_no in range(MONSTER_TOSS_THROWS):
                self.assertTrue(self.game.portal_monster_toss_throw("100", "small_pot", "normal", f"limit-{game_no}-{throw_no}").ok)
        blocked = self.game.portal_monster_toss_start("100", "limit-fourth")
        self.assertFalse(blocked.ok)
        self.assertIn("daily games reset", " ".join(blocked.messages).lower())

    def test_portal_worker_routes_monster_toss_actions(self):
        worker = PortalActionWorker(self.game, "https://guild.example", "sync-key")
        base = {"protocol_version": 37, "twitch_id": "100", "username": "van", "payload": {}, "lease_token": "lease"}
        ok, _message, data = worker._execute({**base, "id": "worker-toss-start", "type": "MONSTER_TOSS_START"})
        self.assertTrue(ok)
        self.assertIsNotNone(data["gold_saucer_state"]["monster_toss"]["active_game"])
        ok, _message, data = worker._execute({**base, "id": "worker-toss-throw", "type": "MONSTER_TOSS_THROW", "payload": {"target": "large_pot", "style": "power"}})
        self.assertTrue(ok)
        self.assertEqual(data["monster_toss_throw"]["target"], "large_pot")
        self.assertEqual(data["monster_toss_throw"]["style"], "power")


class GoldSaucerAlpha2MigrationTests(unittest.TestCase):
    def test_schema11_database_upgrades_to_12_with_verified_backup(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "live.db"
            db = Database(path)
            game = CrystalGuildEngine(db, GameData(ROOT / "data"), overlay_state_path=str(Path(td) / "overlay.json"))
            self.assertTrue(game.recruit("42", "hero", "Hero").ok)
            db.execute("UPDATE players SET level=17,gil=4321 WHERE twitch_id='42'")
            db.conn.executescript("""
                DROP TABLE IF EXISTS gold_saucer_monster_toss;
                DELETE FROM schema_migrations WHERE version=12;
            """)
            db.conn.commit()
            db.close()

            upgraded = Database(path)
            try:
                self.assertEqual(upgraded.schema_version(), 23)
                row = upgraded.one("SELECT level,gil FROM players WHERE twitch_id='42'")
                self.assertEqual((int(row["level"]), int(row["gil"])), (17, 4321))
                self.assertIsNotNone(upgraded.pre_migration_backup_path)
                self.assertIn("pre_schema_12_", Path(upgraded.pre_migration_backup_path).name)
                self.assertTrue(Path(upgraded.pre_migration_backup_path).exists())
                self.assertEqual(upgraded.integrity_report()["foreign_key_violations"], [])
            finally:
                upgraded.close()


if __name__ == "__main__":
    unittest.main()

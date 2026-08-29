from __future__ import annotations

import json
import random
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database, SCHEMA
from crystal_guild.engine import CrystalGuildEngine, LONG_REST_SECONDS

ROOT = Path(__file__).resolve().parents[1]


class Beta4ReleaseHardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(404),
        )
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='100'")
        p = self.game._player("100")
        self.db.execute(
            "UPDATE players SET current_hp=?,current_ap=20 WHERE twitch_id='100'",
            (self.game._max_hp(p),),
        )
        self.unlock("100")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def unlock(self, uid: str):
        self.db.execute("UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1")
        self.db.execute(
            "INSERT INTO player_chocobos(player_id,name,registered_at) VALUES (?,'Biscuit',CURRENT_TIMESTAMP) "
            "ON CONFLICT(player_id) DO UPDATE SET name='Biscuit',registered_at=CURRENT_TIMESTAMP",
            (uid,),
        )

    def start_choice_expedition(self):
        result = self.game.expedition_start("100", "emerald_wilds", "scout")
        self.assertTrue(result.ok, result.messages)
        state = self.game._expedition_load("100")
        state["status"] = "choice"
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        return state

    def test_long_rest_never_heals_through_persistent_expedition(self):
        base = 1_000_000
        self.game.record_player_action("100", now=base)
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        self.db.execute("UPDATE players SET current_hp=3,current_ap=1 WHERE twitch_id='100'")

        direct = self.game.record_player_action("100", now=base + LONG_REST_SECONDS + 5)
        self.assertFalse(direct["refreshed"])
        self.assertTrue(direct["refresh_blocked_by_active_run"])
        player = self.game._player("100")
        self.assertEqual(int(player["current_hp"]), 3)
        self.assertEqual(int(player["current_ap"]), 1)

        # The daemon path must obey the same rule if no player action arrives.
        self.game._save_player_activity_state(
            "100", last_action_at=base, last_refresh_at=0, refresh_reason=""
        )
        sweep = self.game.refresh_due_long_rests(now=base + LONG_REST_SECONDS + 10)
        self.assertEqual(sweep["count"], 0)
        self.assertEqual(sweep["skipped_active_run_ids"], ["100"])
        self.assertEqual(int(self.game._player("100")["current_hp"]), 3)

    def test_stream_live_refresh_skips_active_runs_but_refreshes_idle_players_once(self):
        self.game.recruit("200", "idle", "Idle")
        self.game.choose_job("200", "warrior")
        self.db.execute("UPDATE players SET level=20,current_hp=1,current_ap=1 WHERE twitch_id='200'")
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        self.db.execute("UPDATE players SET current_hp=2,current_ap=1 WHERE twitch_id='100'")

        first = self.game.refresh_all_players_for_stream("2026-08-28T22:00:00Z")
        self.assertTrue(first["refreshed"])
        self.assertIn("100", first["skipped_active_run_ids"])
        self.assertIn("200", first["player_ids"])
        self.assertEqual(int(self.game._player("100")["current_hp"]), 2)
        self.assertGreater(int(self.game._player("200")["current_hp"]), 1)

        second = self.game.refresh_all_players_for_stream("2026-08-28T22:00:00Z")
        self.assertFalse(second["refreshed"])
        self.assertEqual(second["count"], 0)

    def test_expedition_state_survives_database_and_engine_restart(self):
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "journey").ok)
        state = self.game._expedition_load("100")
        state["status"] = "choice"
        state["stage"] = 2
        state["cache"]["gil"] = 321
        state.setdefault("history", []).append({"stage": 2, "type": "test", "label": "Restart checkpoint"})
        self.game._expedition_save("100", state)

        self.db.close()
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.tmp.name) / "overlay-after.json"),
            rng=random.Random(405),
        )
        recovered = self.game._expedition_load("100")
        self.assertEqual(recovered["status"], "choice")
        self.assertEqual(int(recovered["stage"]), 2)
        self.assertEqual(int(recovered["cache"]["gil"]), 321)
        self.assertEqual(recovered["history"][-1]["label"], "Restart checkpoint")
        continued = self.game.portal_expedition_continue("100", "unknown", "b4-restart-continue")
        self.assertTrue(continued.ok, continued.messages)
        self.assertEqual(int(self.game._expedition_load("100")["stage"]), 3)

    def test_portal_stage_mutation_rolls_back_if_replay_receipt_cannot_commit(self):
        self.start_choice_expedition()
        before = json.dumps(self.game._expedition_load("100"), sort_keys=True)
        with patch.object(self.game, "_portal_action_store_sql", side_effect=RuntimeError("receipt failure")):
            with self.assertRaisesRegex(RuntimeError, "receipt failure"):
                self.game.portal_expedition_continue("100", "deep", "b4-atomic-stage")
        after = json.dumps(self.game._expedition_load("100"), sort_keys=True)
        self.assertEqual(after, before)
        self.assertIsNone(self.game._portal_action_replay("b4-atomic-stage"))

    def test_portal_expedition_finish_and_rewards_commit_once_with_receipt(self):
        state = self.start_choice_expedition()
        state["stage"] = int(state["base_stages"])
        state["cache"]["gil"] = 250
        state["cache"]["xp"] = 100
        state["cache"]["jp"] = 50
        self.game._expedition_save("100", state)
        before_gil = int(self.game._player("100")["gil"])
        before_seals = int(self.game._player("100")["hunt_seals"])
        before_results = len(self.game._pending_portal_adventure_results("100"))

        with patch.object(self.game, "_portal_action_store_sql", side_effect=RuntimeError("receipt failure")):
            with self.assertRaisesRegex(RuntimeError, "receipt failure"):
                self.game.portal_expedition_return("100", "b4-atomic-finish")

        # Every nested bank/progress/result write must have rolled back with the missing receipt.
        self.assertIsNotNone(self.game._expedition_load("100"))
        self.assertEqual(int(self.game._player("100")["gil"]), before_gil)
        self.assertEqual(int(self.game._player("100")["hunt_seals"]), before_seals)
        self.assertEqual(len(self.game._pending_portal_adventure_results("100")), before_results)
        self.assertIsNone(self.game._portal_action_replay("b4-atomic-finish"))

        first = self.game.portal_expedition_return("100", "b4-atomic-finish")
        self.assertTrue(first.ok, first.messages)
        gil_once = int(self.game._player("100")["gil"])
        seals_once = int(self.game._player("100")["hunt_seals"])
        results_once = len(self.game._pending_portal_adventure_results("100"))
        self.assertIsNone(self.game._expedition_load("100"))

        replay = self.game.portal_expedition_return("100", "b4-atomic-finish")
        self.assertTrue(replay.ok)
        self.assertEqual(int(self.game._player("100")["gil"]), gil_once)
        self.assertEqual(int(self.game._player("100")["hunt_seals"]), seals_once)
        self.assertEqual(len(self.game._pending_portal_adventure_results("100")), results_once)
        self.assertEqual(replay.data, first.data)

    def test_schema_seven_player_progression_migrates_to_eight_without_reset(self):
        # Build representative current data, then roll only the migration-8
        # structures/ledger entry back to the immediately pre-v1.2 H9 shape.
        path = Path(self.tmp.name) / "schema7.db"
        legacy = Database(path)
        try:
            game = CrystalGuildEngine(
                legacy, GameData(ROOT / "data"),
                overlay_state_path=str(Path(self.tmp.name) / "legacy-overlay.json"),
            )
            game.recruit("999", "veteran", "Veteran")
            game.choose_job("999", "warrior")
            legacy.execute(
                "UPDATE players SET level=42,xp=12345,gil=77777,current_hp=88,current_mp=9,current_ap=11 WHERE twitch_id='999'"
            )
            legacy.execute("UPDATE inventory SET quantity=17 WHERE player_id='999' AND item_id='potion'")
            legacy.execute(
                "INSERT INTO player_chocobos(player_id,name,xp,level,registered_at,portrait_id) "
                "VALUES ('999','Legacy Bird',900,1,CURRENT_TIMESTAMP,'cobalt_blue') "
                "ON CONFLICT(player_id) DO UPDATE SET name='Legacy Bird',xp=900,portrait_id='cobalt_blue',registered_at=CURRENT_TIMESTAMP"
            )
            with legacy.tx() as conn:
                conn.execute("DELETE FROM schema_migrations WHERE version=8")
                conn.execute("DROP TABLE IF EXISTS player_region_exploration")
                conn.execute("DROP TABLE IF EXISTS player_expeditions")
        finally:
            legacy.close()

        upgraded = Database(path)
        try:
            self.assertEqual(upgraded.schema_version(), 8)
            row = upgraded.one(
                "SELECT level,xp,gil,current_hp,current_mp,current_ap FROM players WHERE twitch_id='999'"
            )
            self.assertEqual(tuple(row), (42, 12345, 77777, 88, 9, 11))
            self.assertEqual(int(upgraded.one("SELECT quantity FROM inventory WHERE player_id='999' AND item_id='potion'")["quantity"]), 17)
            self.assertEqual(upgraded.one("SELECT name FROM player_chocobos WHERE player_id='999'")["name"], "Legacy Bird")
            self.assertIsNotNone(upgraded.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_expeditions'"))
            self.assertIsNotNone(upgraded.pre_migration_backup_path)
            self.assertIn("pre_schema_8", Path(upgraded.pre_migration_backup_path).name)
            self.assertEqual(upgraded.quick_check(), [])
        finally:
            upgraded.close()



if __name__ == "__main__":
    unittest.main()

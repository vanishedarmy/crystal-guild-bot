from __future__ import annotations

import json
import random
import sqlite3
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class DungeonsAlpha1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.db_path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(1401),
        )
        self.game.recruit("140", "delver", "Delver")
        self.game.choose_job("140", "warrior")
        self.db.execute("UPDATE players SET level=20,current_hp=250 WHERE twitch_id='140'")
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES (?,?,?,?) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=excluded.progress,stages_cleared=excluded.stages_cleared",
            ("140", "emerald_wilds", 25, 5),
        )

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_schema10_and_protocol24_are_current(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 16)
        self.assertEqual(self.db.schema_version(), 16)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 33)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_dungeons'"))
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_dungeon_progress'"))

    def test_schema9_upgrade_adds_dungeons_with_verified_backup_and_preserves_player(self):
        path = Path(self.tmp.name) / "schema9.db"
        legacy = Database(path)
        try:
            game = CrystalGuildEngine(legacy, GameData(ROOT / "data"), overlay_state_path=str(Path(self.tmp.name) / "legacy-overlay.json"))
            game.recruit("909", "legacy", "Legacy")
            legacy.execute("UPDATE players SET level=37,gil=54321 WHERE twitch_id='909'")
        finally:
            legacy.close()
        raw = sqlite3.connect(path)
        try:
            raw.execute("DELETE FROM schema_migrations WHERE version=10")
            raw.execute("DROP TABLE IF EXISTS player_dungeon_progress")
            raw.execute("DROP TABLE IF EXISTS player_dungeons")
            raw.commit()
        finally:
            raw.close()
        upgraded = Database(path)
        try:
            self.assertEqual(upgraded.schema_version(), 16)
            row = upgraded.one("SELECT level,gil FROM players WHERE twitch_id='909'")
            self.assertEqual((int(row["level"]), int(row["gil"])), (37, 54321))
            self.assertIsNotNone(upgraded.pre_migration_backup_path)
            self.assertIn("pre_schema_10", Path(upgraded.pre_migration_backup_path).name)
            self.assertEqual(upgraded.quick_check(), [])
        finally:
            upgraded.close()

    def test_dungeon_board_unlocks_from_existing_expedition_progress(self):
        board = self.game._dungeon_board_state("140")
        self.assertGreaterEqual(len(board["dungeons"]), 2)
        entry = board["dungeons"][0]
        self.assertEqual(entry["id"], "forgotten_ossuary")
        self.assertTrue(entry["unlocked"])
        self.assertEqual(entry["rooms"], 8)
        self.assertEqual(entry.get("missing", []), [])

    def test_dungeon_run_persists_and_continues_into_combat(self):
        result = self.game.dungeon_start("140", "forgotten_ossuary")
        self.assertTrue(result.ok, result.messages)
        active = self.game._dungeon_public("140")
        self.assertEqual(active["room_number"], 1)
        self.assertEqual(active["status"], "choice")
        self.assertEqual(active["room"]["type"], "entrance")

        restarted = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.tmp.name) / "restart-overlay.json"),
            rng=random.Random(1401),
        )
        persisted = restarted._dungeon_public("140")
        self.assertEqual(persisted["run_id"], active["run_id"])
        advance = restarted.dungeon_continue("140")
        self.assertTrue(advance.ok, advance.messages)
        combat = restarted._dungeon_public("140")
        self.assertEqual(combat["room_number"], 2)
        self.assertEqual(combat["status"], "combat")
        self.assertEqual(combat["combat"]["enemy"]["id"], "skeleton")

    def test_dungeon_attack_advances_or_clears_combat_and_persists_condition(self):
        self.assertTrue(self.game.dungeon_start("140", "forgotten_ossuary").ok)
        self.assertTrue(self.game.dungeon_continue("140").ok)
        before = self.game._dungeon_public("140")
        self.assertEqual(before["status"], "combat")
        result = self.game.dungeon_action("140", "attack")
        self.assertTrue(result.ok, result.messages)
        after = self.game._dungeon_public("140")
        self.assertIsNotNone(after)
        self.assertIn(after["status"], {"combat", "choice"})
        if after["status"] == "combat":
            self.assertGreaterEqual(int(after["combat"]["round"]), 2)
        else:
            self.assertEqual(after["event"]["type"], "victory")
            bestiary = self.db.one("SELECT defeats FROM bestiary WHERE player_id='140' AND monster_id='skeleton'")
            self.assertIsNotNone(bestiary)
            self.assertGreaterEqual(int(bestiary["defeats"]), 1)
        player = self.db.one("SELECT current_hp FROM players WHERE twitch_id='140'")
        self.assertGreater(int(player["current_hp"]), 0)

    def test_retreat_banks_half_cache_and_clears_run(self):
        self.assertTrue(self.game.dungeon_start("140", "forgotten_ossuary").ok)
        state = self.game._dungeon_load("140")
        state["cache"] = {"xp": 101, "jp": 21, "gil": 99, "items": [{"id": "potion", "quantity": 3}]}
        self.game._dungeon_save("140", state)
        before = self.db.one("SELECT xp,gil FROM players WHERE twitch_id='140'")
        before_job = self.db.one("SELECT jp FROM player_jobs WHERE player_id='140' AND job_id='warrior'")
        before_potions = self.game._inventory_qty("140", "potion")
        result = self.game.dungeon_retreat("140")
        self.assertTrue(result.ok, result.messages)
        self.assertIsNone(self.game._dungeon_load("140"))
        after = self.db.one("SELECT xp,gil FROM players WHERE twitch_id='140'")
        after_job = self.db.one("SELECT jp FROM player_jobs WHERE player_id='140' AND job_id='warrior'")
        self.assertEqual(int(after["xp"]) - int(before["xp"]), 50)
        self.assertEqual(int(after["gil"]) - int(before["gil"]), 49)
        self.assertEqual(int(after_job["jp"]) - int(before_job["jp"]), 10)
        self.assertEqual(self.game._inventory_qty("140", "potion") - before_potions, 1)
        progress = self.db.one("SELECT retreats,best_rooms,last_outcome FROM player_dungeon_progress WHERE player_id='140' AND dungeon_id='forgotten_ossuary'")
        self.assertEqual((int(progress["retreats"]), str(progress["last_outcome"])), (1, "retreat"))

    def test_portal_completion_replay_cannot_pay_or_count_twice(self):
        self.assertTrue(self.game.dungeon_start("140", "forgotten_ossuary").ok)
        state = self.game._dungeon_load("140")
        state["room_index"] = 7
        state["status"] = "choice"
        state["cache"] = {"xp": 25, "jp": 5, "gil": 40, "items": []}
        self.game._dungeon_save("140", state)
        before = self.db.one("SELECT xp,gil FROM players WHERE twitch_id='140'")
        public = self.game._dungeon_public("140")
        run_id = str(public["run_id"])
        room_id = str(public["room"]["id"])
        revision = int(public["revision"])
        first = self.game.portal_dungeon_continue("140", run_id, room_id, revision, "pa_dungeon_final")
        second = self.game.portal_dungeon_continue("140", run_id, room_id, revision, "pa_dungeon_final")
        self.assertTrue(first.ok, first.messages)
        self.assertTrue(second.ok, second.messages)
        after = self.db.one("SELECT xp,gil FROM players WHERE twitch_id='140'")
        self.assertEqual(int(after["xp"]) - int(before["xp"]), 25 + 180 + 120)
        self.assertEqual(int(after["gil"]) - int(before["gil"]), 40 + 260 + 150)
        progress = self.db.one("SELECT clears FROM player_dungeon_progress WHERE player_id='140' AND dungeon_id='forgotten_ossuary'")
        self.assertEqual(int(progress["clears"]), 1)
        pending = self.db.one("SELECT COUNT(*) AS n FROM portal_adventure_results WHERE player_id='140' AND kind='dungeon'")
        self.assertEqual(int(pending["n"]), 1)


    def test_stale_dungeon_tab_cannot_mutate_newer_room_state(self):
        self.assertTrue(self.game.dungeon_start("140", "forgotten_ossuary").ok)
        first = self.game._dungeon_public("140")
        run_id = first["run_id"]
        room_id = first["room"]["id"]
        moved = self.game.portal_dungeon_continue("140", run_id, room_id, first["revision"], "pa_dungeon_continue_room1")
        self.assertTrue(moved.ok, moved.messages)
        current = self.game._dungeon_public("140")
        self.assertEqual(current["room_number"], 2)
        stale = self.game.portal_dungeon_retreat("140", run_id, room_id, first["revision"], "pa_dungeon_stale_retreat")
        self.assertFalse(stale.ok)
        self.assertTrue(stale.data.get("stale_dungeon"))
        self.assertIsNotNone(self.game._dungeon_load("140"))
        self.assertEqual(self.game._dungeon_public("140")["room_number"], 2)

    def test_defeat_recovers_quarter_cache_and_records_failure(self):
        self.assertTrue(self.game.dungeon_start("140", "forgotten_ossuary").ok)
        state = self.game._dungeon_load("140")
        state["cache"] = {"xp": 103, "jp": 23, "gil": 99, "items": [{"id": "potion", "quantity": 5}]}
        self.game._dungeon_save("140", state)
        before = self.db.one("SELECT xp,gil,deaths FROM players WHERE twitch_id='140'")
        before_job = self.db.one("SELECT jp FROM player_jobs WHERE player_id='140' AND job_id='warrior'")
        before_potions = self.game._inventory_qty("140", "potion")
        result = self.game._dungeon_finish("140", state, outcome="defeat")
        self.assertTrue(result.ok, result.messages)
        after = self.db.one("SELECT xp,gil,deaths FROM players WHERE twitch_id='140'")
        after_job = self.db.one("SELECT jp FROM player_jobs WHERE player_id='140' AND job_id='warrior'")
        self.assertEqual(int(after["xp"]) - int(before["xp"]), 25)
        self.assertEqual(int(after["gil"]) - int(before["gil"]), 24)
        self.assertEqual(int(after_job["jp"]) - int(before_job["jp"]), 5)
        self.assertEqual(self.game._inventory_qty("140", "potion") - before_potions, 1)
        self.assertEqual(int(after["deaths"]) - int(before["deaths"]), 1)
        progress = self.db.one("SELECT defeats,last_outcome FROM player_dungeon_progress WHERE player_id='140' AND dungeon_id='forgotten_ossuary'")
        self.assertEqual((int(progress["defeats"]), str(progress["last_outcome"])), (1, "defeat"))

    def test_sanctuary_restores_persistent_hp_and_job_resource(self):
        self.assertTrue(self.game.dungeon_start("140", "forgotten_ossuary").ok)
        self.db.execute("UPDATE players SET current_hp=20,current_ap=0,current_mp=0 WHERE twitch_id='140'")
        state = self.game._dungeon_load("140")
        state["room_index"] = 6
        state["status"] = "choice"
        result = self.game._dungeon_begin_room("140", state)
        self.assertTrue(result.ok, result.messages)
        player = self.db.one("SELECT current_hp,current_ap FROM players WHERE twitch_id='140'")
        self.assertGreater(int(player["current_hp"]), 20)
        self.assertGreater(int(player["current_ap"] or 0), 0)
        public = self.game._dungeon_public("140")
        self.assertEqual(public["room"]["type"], "sanctuary")
        self.assertGreater(int(public["event"].get("healed", 0)), 0)

    def test_clear_all_adventures_removes_active_dungeon_without_touching_progress(self):
        self.assertTrue(self.game.dungeon_start("140", "forgotten_ossuary").ok)
        self.db.execute("INSERT INTO player_dungeon_progress(player_id,dungeon_id,clears,best_rooms,last_outcome) VALUES (?,?,?,?,?)", ("140", "forgotten_ossuary", 2, 7, "complete"))
        result = self.game.clear_all_adventures()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(int(result.data.get("dungeons_cleared", 0)), 1)
        self.assertIsNone(self.game._dungeon_load("140"))
        progress = self.db.one("SELECT clears,best_rooms FROM player_dungeon_progress WHERE player_id='140' AND dungeon_id='forgotten_ossuary'")
        self.assertEqual((int(progress["clears"]), int(progress["best_rooms"])), (2, 7))

    def test_portal_worker_dungeon_start_is_replay_safe(self):
        from crystal_guild.portal_actions import PortalActionWorker
        worker = PortalActionWorker(self.game, "https://guild.example", "sync-key")
        action = {
            "id": "pa_dungeon_start",
            "protocol_version": ACTION_PROTOCOL_VERSION,
            "twitch_id": "140",
            "username": "delver",
            "type": "DUNGEON_START",
            "payload": {"dungeon_id": "forgotten_ossuary"},
            "lease_token": "lease",
        }
        first = worker._execute(action)
        run_id = self.game._dungeon_load("140")["run_id"]
        second = worker._execute(action)
        self.assertTrue(first[0], first[1])
        self.assertTrue(second[0], second[1])
        self.assertEqual(self.game._dungeon_load("140")["run_id"], run_id)
        self.assertIn("dungeons", first[2]["adventure_state"])


if __name__ == "__main__":
    unittest.main()

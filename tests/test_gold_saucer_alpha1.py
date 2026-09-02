from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import CACTPOT_COST, DAILY_ALLOWANCE_POINTS, SLOTS_COST, WELCOME_POINTS
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class GoldSaucerAlpha1Tests(unittest.TestCase):
    def setUp(self):
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

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_release_contract_advances_only_local_schema_and_portal_protocol(self):
        self.assertEqual(__version__, "1.7.0-emporium-annex-a3h2")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 15)
        self.assertEqual(self.db.schema_version(), 15)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 31)
        for table in ("player_gold_saucer", "gold_saucer_cactpot", "gold_saucer_history"):
            self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)))

    def test_first_floor_visit_grants_welcome_points_exactly_once(self):
        first = self.game.portal_gold_saucer_state("100")
        second = self.game.portal_gold_saucer_state("100")
        self.assertTrue(first.ok and second.ok)
        self.assertEqual(first.data["gold_saucer_state"]["points"], WELCOME_POINTS)
        self.assertEqual(second.data["gold_saucer_state"]["points"], WELCOME_POINTS)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='welcome'")["n"], 1)


    def test_daily_allowance_prevents_permanent_lockout_and_is_exactly_once(self):
        first = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        self.assertEqual(first["points"], WELCOME_POINTS)
        welcome = int(self.db.one("SELECT created_at FROM gold_saucer_history WHERE player_id='100' AND game='welcome'")["created_at"])
        future = welcome + 86401
        with self.db.tx(immediate=True) as conn:
            next_day = self.game._gold_saucer_state_sql(conn, "100", future)
            again = self.game._gold_saucer_state_sql(conn, "100", future + 60)
        self.assertEqual(next_day["points"], WELCOME_POINTS + DAILY_ALLOWANCE_POINTS)
        self.assertEqual(again["points"], WELCOME_POINTS + DAILY_ALLOWANCE_POINTS)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='daily_allowance'")["n"], 1)

    def test_prize_counter_is_cosmetic_atomic_and_replay_safe(self):
        state = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        prize = next(row for row in state["prizes"] if row["id"] == "saucer_regular")
        self.assertEqual(prize["cost"], 400)
        self.assertFalse(prize["owned"])
        bought = self.game.portal_saucer_buy("100", "saucer_regular", "prize-1")
        self.assertTrue(bought.ok)
        self.assertEqual(bought.data["gold_saucer_state"]["points"], WELCOME_POINTS - 400)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='saucer_regular'"))
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='100'")["gil"]), 250)
        replay = self.game.portal_saucer_buy("100", "saucer_regular", "prize-1")
        self.assertTrue(replay.ok)
        self.assertEqual(replay.data["gold_saucer_state"]["points"], WELCOME_POINTS - 400)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='prize'")["n"], 1)
        owned = next(row for row in replay.data["gold_saucer_state"]["prizes"] if row["id"] == "saucer_regular")
        self.assertTrue(owned["owned"])

    def test_cactpot_ticket_persists_reveals_and_resolves_once(self):
        started = self.game.portal_cactpot_start("100", "cactpot-start")
        self.assertTrue(started.ok)
        state = started.data["gold_saucer_state"]
        self.assertEqual(state["points"], WELCOME_POINTS - CACTPOT_COST)
        ticket = state["cactpot"]["ticket"]
        self.assertEqual(ticket["state"], "reveal")
        self.assertEqual(len(ticket["revealed"]), 1)
        original_ticket_id = ticket["id"]

        # A state refresh returns the same authoritative ticket rather than rerolling it.
        refreshed = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["cactpot"]["ticket"]
        self.assertEqual(refreshed["id"], original_ticket_id)

        revealed = set(ticket["revealed"])
        action = 0
        for cell in range(9):
            if cell in revealed:
                continue
            action += 1
            result = self.game.portal_cactpot_reveal("100", cell, f"reveal-{action}")
            self.assertTrue(result.ok)
            if action == 3:
                self.assertEqual(result.data["gold_saucer_state"]["cactpot"]["ticket"]["state"], "line")
                break

        resolved = self.game.portal_cactpot_line("100", 0, "line-0")
        self.assertTrue(resolved.ok)
        payout = int(resolved.data["cactpot_payout"])
        self.assertGreater(payout, 0)
        balance = resolved.data["gold_saucer_state"]["points"]
        replay = self.game.portal_cactpot_line("100", 0, "line-0")
        self.assertTrue(replay.ok)
        self.assertEqual(self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["points"], balance)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='mini_cactpot'")["n"], 1)

    def test_slots_spin_is_bounded_cooled_down_and_replay_safe(self):
        result = self.game.portal_slots_spin("100", "slots-1")
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data["reels"]), 3)
        self.assertGreaterEqual(int(result.data["payout"]), 0)
        first_state = result.data["gold_saucer_state"]
        self.assertEqual(first_state["account"]["slots_spins"], 1)
        self.assertGreater(first_state["slots"]["remaining_seconds"], 0)
        expected_points = WELCOME_POINTS - SLOTS_COST + int(result.data["payout"])
        self.assertEqual(first_state["points"], expected_points)

        replay = self.game.portal_slots_spin("100", "slots-1")
        self.assertEqual(replay.data["reels"], result.data["reels"])
        self.assertEqual(self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["account"]["slots_spins"], 1)

        blocked = self.game.portal_slots_spin("100", "slots-2")
        self.assertFalse(blocked.ok)
        self.assertIn("reset", " ".join(blocked.messages).lower())

    def test_streamer_saucer_controls_are_replay_safe_and_do_not_touch_gil(self):
        before_gil = int(self.db.one("SELECT gil FROM players WHERE twitch_id='100'")["gil"])
        grant = self.game.streamer_saucer_grant("van | 250", action_id="grant-1")
        self.assertTrue(grant.ok)
        self.assertEqual(grant.data["points"], WELCOME_POINTS + 250)
        replay = self.game.streamer_saucer_grant("van | 250", action_id="grant-1")
        self.assertEqual(replay.data["points"], WELCOME_POINTS + 250)
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='100'")["gil"]), before_gil)

        self.assertTrue(self.game.portal_cactpot_start("100", "ticket-reset-test").ok)
        reset = self.game.streamer_saucer_reset("van", action_id="reset-1")
        self.assertTrue(reset.ok)
        state = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        self.assertIsNone(state["cactpot"]["ticket"])
        self.assertEqual(state["cactpot"]["remaining_seconds"], 0)
        self.assertEqual(state["slots"]["remaining_seconds"], 0)

    def test_worker_dispatches_new_protocol_actions(self):
        worker = PortalActionWorker(self.game, "https://guild.example", "sync-key")
        base = {"protocol_version": 31, "twitch_id": "100", "username": "van", "payload": {}, "lease_token": "lease"}
        action = {**base, "id": "state-1", "type": "GOLD_SAUCER_STATE"}
        ok, _message, data = worker._execute(action)
        self.assertTrue(ok)
        self.assertEqual(data["gold_saucer_state"]["points"], WELCOME_POINTS)
        action = {**base, "id": "slot-worker", "type": "SLOTS_SPIN"}
        ok, _message, data = worker._execute(action)
        self.assertTrue(ok)
        self.assertIn("reels", data)
        # A cosmetic prize purchase routes through the same v26 authoritative worker.
        action = {**base, "id": "prize-worker", "type": "SAUCER_BUY", "payload": {"prize_id": "saucer_regular"}}
        ok, _message, data = worker._execute(action)
        self.assertTrue(ok)
        self.assertEqual(data["prize_id"], "saucer_regular")


class GoldSaucerMigrationTests(unittest.TestCase):
    def test_schema11_like_database_upgrades_to_12_with_verified_backup_and_player_data_intact(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "live.db"
            db = Database(path)
            game = CrystalGuildEngine(db, GameData(ROOT / "data"), overlay_state_path=str(Path(td) / "overlay.json"))
            self.assertTrue(game.recruit("42", "hero", "Hero").ok)
            db.execute("UPDATE players SET level=17,gil=4321 WHERE twitch_id='42'")
            # Simulate the exact pre-Alpha-1 state by removing only migration-11 objects/marker.
            db.conn.executescript("""
                DROP TABLE IF EXISTS gold_saucer_history;
                DROP TABLE IF EXISTS gold_saucer_cactpot;
                DROP TABLE IF EXISTS player_gold_saucer;
                DELETE FROM schema_migrations WHERE version=11;
            """)
            db.conn.commit()
            db.close()

            upgraded = Database(path)
            try:
                self.assertEqual(upgraded.schema_version(), 15)
                row = upgraded.one("SELECT level,gil FROM players WHERE twitch_id='42'")
                self.assertEqual((int(row["level"]), int(row["gil"])), (17, 4321))
                self.assertIsNotNone(upgraded.pre_migration_backup_path)
                self.assertTrue(Path(upgraded.pre_migration_backup_path).exists())
                self.assertEqual(upgraded.integrity_report()["foreign_key_violations"], [])
            finally:
                upgraded.close()

"""Step 6 release hardening: no invented history, loss of rewards or replay drift."""
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
from crystal_guild.moments_progress import (
    award_settlement, best_record, reconcile_all_owned_moment_rewards,
    reconcile_owned_moment_rewards, reconcile_verified_history,
)
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class Step6RecordsMomentsHardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "game.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.engine = CrystalGuildEngine(
            self.db, self.data, rng=random.Random(66),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
        )
        for pid, name in (("1", "van"), ("2", "mira")):
            self.assertTrue(self.engine.recruit(pid, name, name.title()).ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def moment_1hp(self, conn, pid="1", key="battle:one"):
        return award_settlement(conn, self.data, pid, key, {
            "event": "combat_victory", "settled": True,
            "player_alive": True, "final_hp": 1,
        })

    def world_close(self, conn, pid="1", key="world:one"):
        return award_settlement(conn, self.data, pid, key, {
            "event": "world_event_victory", "settled": True,
            "player_alive": True, "participant_count": 3, "living_party_count": 2,
            "highest_survivor_hp_pct_raw": 5.0,
        })

    def counts(self, pid="1"):
        return {t: self.db.one(f"SELECT COUNT(*) n FROM {t} WHERE player_id=?", (pid,))["n"]
                for t in ("player_moment_unlocks", "player_titles", "player_trophies", "player_record_events")}

    def test_repeat_event_key_identical_is_harmless_but_changed_evidence_rolls_back(self):
        with self.db.tx() as conn:
            self.assertEqual(self.moment_1hp(conn), ["Technically Alive"])
            self.assertEqual(self.moment_1hp(conn), [])
        baseline = self.counts()
        with self.assertRaisesRegex(ValueError, "Conflicting evidence"):
            with self.db.tx() as conn:
                self.moment_1hp(conn, "2", "other-player-event")
                # Different player, same event key, same trigger, but opposite HP.
                # The invalid replay must roll back the newly inserted other-player Moment.
                self.moment_1hp(conn, "1", "battle:one")
                award_settlement(conn, self.data, "1", "battle:one", {
                    "event": "combat_victory", "settled": True,
                    "player_alive": True, "final_hp": 2,
                })
        self.assertEqual(self.counts(), baseline)
        self.assertEqual(self.counts("2")["player_moment_unlocks"], 0)

    def test_same_key_is_scoped_to_player_and_multiple_actual_events_are_independent(self):
        with self.db.tx() as conn:
            self.assertEqual(self.moment_1hp(conn, "1", "same"), ["Technically Alive"])
            self.assertEqual(self.moment_1hp(conn, "2", "same"), ["Technically Alive"])
            self.assertEqual(self.moment_1hp(conn, "1", "next"), [])
        self.assertEqual(self.counts("1")["player_moment_unlocks"], 1)
        self.assertEqual(self.counts("2")["player_moment_unlocks"], 1)

    def test_invalid_ranges_and_inconsistent_survivors_never_write_rewards(self):
        bad = [
            {"event": "combat_victory", "settled": True, "player_alive": True, "final_hp": 0},
            {"event": "combat_victory", "settled": True, "player_alive": True, "final_hp": -5},
            {"event": "world_event_victory", "settled": True, "player_alive": True,
             "participant_count": 2, "living_party_count": 3, "highest_survivor_hp_pct_raw": 3.0},
            {"event": "world_event_victory", "settled": True, "player_alive": True,
             "participant_count": 2, "living_party_count": 1, "highest_survivor_hp_pct_raw": 101.0},
            {"event": "venture_completed", "settled": True, "successful": True, "player_alive": True,
             "final_hp_pct_pre_recovery_raw": -1.0, "consumables_used": 0},
            {"event": "purchase_settled", "settled": True,
             "qualifying_shop_purchase": True, "single_transaction": True,
             "record_id": "biggest_purchase", "record_value": -25000},
        ]
        for n, facts in enumerate(bad):
            with self.subTest(n=n), self.assertRaises(ValueError):
                with self.db.tx() as conn:
                    award_settlement(conn, self.data, "1", f"invalid:{n}", facts)
        self.assertEqual(self.counts()["player_moment_unlocks"], 0)

    def test_record_direction_is_fixed_and_single_event_cannot_rewrite_its_own_best(self):
        with self.db.tx() as conn:
            self.assertTrue(best_record(conn, "1", "closest_victory", 11, "fight:1"))
            self.assertFalse(best_record(conn, "1", "closest_victory", 20, "fight:2"))
            self.assertTrue(best_record(conn, "1", "closest_victory", 3, "fight:3"))
            with self.assertRaisesRegex(ValueError, "direction"):
                best_record(conn, "1", "closest_victory", 2, "fight:4", lower_is_better=False)
            with self.assertRaisesRegex(ValueError, "different results"):
                best_record(conn, "1", "closest_victory", 2, "fight:3")
            self.assertTrue(best_record(conn, "1", "longest_venture", 700, "venture:1"))
            self.assertFalse(best_record(conn, "1", "longest_venture", 500, "venture:2"))
            self.assertTrue(best_record(conn, "2", "closest_victory", 2, "fight:3"))
        repo = PortalRepository(self.db.path, ROOT / "data")
        try:
            a = {r["id"]: r for r in repo.records("van")["personal_records"]["records"]}
            b = {r["id"]: r for r in repo.records("mira")["personal_records"]["records"]}
            self.assertEqual(a["closest_victory"]["value"], 3)
            self.assertEqual(a["longest_venture"]["value"], 700)
            self.assertEqual(b["closest_victory"]["value"], 2)
            self.assertEqual(b["longest_venture"]["status"], "awaiting_tracking")
        finally:
            repo.close()

    def test_missing_reward_receipts_repair_only_proven_ownership_once(self):
        with self.db.tx() as conn:
            self.world_close(conn)
            owned = conn.execute("SELECT moment_id,title_id FROM player_moment_unlocks WHERE player_id='1'").fetchone()
            self.assertIsNotNone(owned)
            conn.execute("DELETE FROM player_titles WHERE player_id=? AND title_id=?", ("1", owned["title_id"]))
            conn.execute("DELETE FROM player_trophies WHERE player_id=? AND trophy_id=?",
                         ("1", "moment_trophy_world_event_close_call"))
            self.assertEqual(reconcile_owned_moment_rewards(conn, self.data, "2"), {"titles": 0, "trophies": 0})
            self.assertEqual(reconcile_owned_moment_rewards(conn, self.data, "1"), {"titles": 1, "trophies": 1})
            self.assertEqual(reconcile_owned_moment_rewards(conn, self.data, "1"), {"titles": 0, "trophies": 0})
        self.assertEqual(self.counts()["player_moment_unlocks"], 1)
        self.assertEqual(self.counts("2")["player_trophies"], 0)

    def test_restart_restores_missing_title_only_and_retains_original_date_and_records(self):
        with self.db.tx() as conn:
            self.moment_1hp(conn)
            best_record(conn, "1", "longest_venture", 3612, "venture:old",
                        occurred_at="2026-09-20T09:00:00Z")
            conn.execute("DELETE FROM player_titles WHERE player_id='1' AND title_id=?",
                         (self.data.moments["moment_technically_alive"]["reward"]["title_id"],))
        original = dict(self.db.one("SELECT * FROM player_moment_unlocks WHERE player_id='1'"))
        self.db.close()
        self.db = Database(self.path)
        self.engine = CrystalGuildEngine(self.db, self.data, rng=random.Random(67),
                                         overlay_state_path=str(Path(self.temp.name) / "overlay.json"))
        row = dict(self.db.one("SELECT * FROM player_moment_unlocks WHERE player_id='1'"))
        self.assertEqual(row, original, "repair must not touch the real earned timestamp or evidence")
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM player_titles WHERE player_id='1' AND title_id=?",
                                     (row["title_id"],))["n"], 1)
        self.assertEqual(self.db.one("SELECT best_value FROM player_record_events WHERE player_id='1' AND record_id='longest_venture'")["best_value"], 3612)
        self.assertEqual(reconcile_all_owned_moment_rewards(self.db, self.data)["titles_restored"], 0)
        self.assertEqual(self.db.quick_check(), [])

    def test_corrupt_negative_old_cactpot_payout_cannot_bridge_five_paid_losses(self):
        for n, payout in enumerate((0, 0, 0, -2, 0, 0), 1):
            self.db.execute(
                "INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) "
                "VALUES ('1','mini_cactpot',10,?,'old','{}',?)", (payout, n),
            )
        with self.db.tx() as conn:
            self.assertEqual(reconcile_verified_history(conn, self.data, "1"), [])
        self.assertEqual(self.counts()["player_moment_unlocks"], 0)

    def test_malformed_historical_rows_do_not_abort_startup_or_records_read(self):
        # SQLite's type affinity does not prevent imported, malformed text.
        for n, wager in enumerate(("10", "10", "garbage", "10", "10"), 1):
            self.db.execute(
                "INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) "
                "VALUES ('1','mini_cactpot',?,0,'old','{}',?)", (wager, n),
            )
        with self.db.tx() as conn:
            self.assertEqual(reconcile_verified_history(conn, self.data, "1"), [])
            best_record(conn, "1", "closest_victory", 2, "victory:valid")
            conn.execute("UPDATE player_record_events SET context_json='broken-json' WHERE player_id='1'")
        repo = PortalRepository(self.db.path, ROOT / "data")
        try:
            cards = {r["id"]: r for r in repo.records("van")["personal_records"]["records"]}
            self.assertEqual(cards["closest_victory"]["value"], 2)
            self.assertIsNone(cards["closest_victory"]["context"])
            self.assertEqual(cards["longest_cactpot_loss_streak"]["value"], 2)
        finally:
            repo.close()
        self.assertEqual(self.counts()["player_moment_unlocks"], 0)

    def test_schema_22_to_23_keeps_old_history_and_makes_verified_backup(self):
        self.db.execute("UPDATE players SET gil=321321 WHERE twitch_id='1'")
        self.db.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) "
                        "VALUES ('1','gil','gil',-25000,'shop')")
        with self.db.tx() as conn:
            for table in ("player_moment_unlocks", "player_record_events", "player_moment_reconciliation"):
                conn.execute(f"DROP TABLE {table}")
            conn.execute("DELETE FROM schema_migrations WHERE version>=23")
        self.db.close()
        self.db = Database(self.path)
        self.assertEqual(DATABASE_SCHEMA_VERSION, 27)
        self.assertEqual(self.db.schema_version(), 27)
        backup = sorted((self.path.parent / "backups").glob("pre_schema_23_*.db"))[-1]
        self.assertTrue(backup.is_file())
        with sqlite3.connect(backup) as old:
            self.assertEqual(old.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0], 22)
            self.assertEqual(old.execute("SELECT gil FROM players WHERE twitch_id='1'").fetchone()[0], 321321)
            self.assertEqual(old.execute("SELECT COUNT(*) FROM transactions WHERE player_id='1' AND source='shop' AND amount=-25000").fetchone()[0], 1)
        self.assertEqual(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"], 321321)
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM transactions WHERE player_id='1' AND source='shop' AND amount=-25000")["n"], 1)
        self.assertEqual(self.db.quick_check(), [])
        # Re-opening a completed schema-23 install must not make another backup.
        self.db.close()
        self.db = Database(self.path)
        self.assertIsNone(self.db.pre_migration_backup_path)
        self.assertEqual(self.db.schema_version(), 27)

    def test_reading_records_does_not_reconcile_rewards_or_reveal_other_user(self):
        with self.db.tx() as conn:
            self.world_close(conn)
            conn.execute("DELETE FROM player_trophies WHERE player_id='1' AND trophy_id=?",
                         ("moment_trophy_world_event_close_call",))
        repo = PortalRepository(self.db.path, ROOT / "data")
        try:
            before = self.counts()
            for _ in range(2):
                view = repo.records("van")
                self.assertIn("A Little Too Close", json.dumps(view))
                self.assertNotIn("The Close Call", json.dumps(view["moments"]))
                self.assertNotIn("A Little Too Close", json.dumps(repo.records("mira")))
                self.assertNotIn("moment_trophy_world_event_close_call", json.dumps(repo.trophies("mira")))
            self.assertEqual(self.counts(), before)
        finally:
            repo.close()


if __name__ == "__main__":
    unittest.main()

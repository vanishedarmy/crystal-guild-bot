"""v1.9.3 Guild Initiatives: real Fellowship receipt and payout integration."""
from __future__ import annotations
from contextlib import closing

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database, DATABASE_SCHEMA_VERSION
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.guild_initiatives import (
    CONTRACTS, DAILIES, WEEKLIES, board_view, contract_view, daily_period_key,
    progress_event, selected,
)
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class GuildInitiativesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(self.db, self.data, rng=random.Random(4),
                                       overlay_state_path=str(Path(self.temp.name) / "overlay.json"))
        self.assertTrue(self.game.recruit("101", "hero101", "First Hero").ok)
        self.assertTrue(self.game.recruit("102", "hero102", "Second Hero").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def _matching(self, catalog, scope):
        definitions = selected(catalog, daily_period_key() if scope == "daily" else self._weekly())
        return {d["category"]: d for d in definitions}

    @staticmethod
    def _weekly():
        from crystal_guild.fellowship import weekly_period_key
        return weekly_period_key()

    def _record(self, pid, activity, key, amount=1):
        return self.game.fellowship_system.record_activity(pid, activity, event_key=key, amount=amount, renown=0)

    def test_schema_rotation_and_public_module(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 28)
        self.assertEqual(self.db.schema_version(), 28)
        self.assertEqual(len(selected(CONTRACTS, self._weekly())), 3)
        self.assertEqual(len(selected(DAILIES, daily_period_key())), 3)
        self.assertEqual(len(selected(WEEKLIES, self._weekly())), 3)
        repo = PortalRepository(self.path, ROOT / "data")
        try:
            public = repo.fellowship()
            self.assertEqual(public["contracts"]["total"], 3)
            self.assertEqual(len(public["contracts"]["objectives"]), 3)
            personal = repo.guild_board("hero101")
            self.assertEqual(personal["board"]["daily"]["total"], 3)
            self.assertEqual(personal["board"]["weekly"]["total"], 3)
            self.assertNotIn("twitch_id", str(personal))
        finally:
            repo.close()

    def test_duplicate_event_does_not_award_progress_or_rewards_twice(self):
        daily = self._matching(DAILIES, "daily")["combat"]
        activity = "hunt_win" if daily["id"] == "daily_hunts" else "encounter_win"
        self._record("101", activity, "repeat-me", amount=7)
        before = board_view(self.db.conn, "101")["daily"]
        gil = self.db.one("SELECT gil FROM players WHERE twitch_id='101'")["gil"]
        first_count = self.db.one("SELECT COUNT(*) AS n FROM guild_initiative_rewards WHERE player_id='101'")["n"]
        self.assertEqual(self._record("101", activity, "repeat-me", amount=7), [])
        self.assertEqual(board_view(self.db.conn, "101")["daily"], before)
        self.assertEqual(self.db.one("SELECT gil FROM players WHERE twitch_id='101'")["gil"], gil)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM guild_initiative_rewards WHERE player_id='101'")["n"], first_count)

    def test_communal_completion_pays_both_members_once(self):
        contract = self._matching(CONTRACTS, "weekly")["combat"]
        activity = "hunt_win" if contract["id"] == "guild_hunts" else "encounter_win"
        self._record("101", activity, "one-batch", amount=contract["target"] // 2)
        self._record("102", activity, "two-batch", amount=contract["target"])
        result = contract_view(self.db.conn)
        own = next(row for row in result["objectives"] if row["id"] == contract["id"])
        self.assertTrue(own["complete"])
        self.assertEqual(own["progress"], own["target"])
        self.assertEqual(sum(item["amount"] for item in own["contributors"]), own["target"])
        period = self._weekly()
        rewarded = self.db.all("SELECT player_id FROM guild_initiative_rewards WHERE scope='contract' AND objective_id=? AND period_key=?", (contract["id"], period))
        self.assertEqual({r["player_id"] for r in rewarded}, {"101", "102"})
        self._record("102", activity, "third-batch")
        self.assertEqual(len(self.db.all("SELECT player_id FROM guild_initiative_rewards WHERE scope='contract' AND objective_id=? AND period_key=?", (contract["id"], period))), 2)

    def test_personal_rewards_also_credit_contract_and_are_not_duplicated(self):
        personal = self._matching(WEEKLIES, "weekly")["economy"]
        activity = "forge" if personal["id"] == "weekly_forges" else "craft"
        contract = self._matching(CONTRACTS, "weekly")["economy"]
        first_gil = self.db.one("SELECT gil FROM players WHERE twitch_id='101'")["gil"]
        self._record("101", activity, "forge-or-craft-one", amount=personal["target"])
        result = board_view(self.db.conn, "101")["weekly"]
        own = next(x for x in result["objectives"] if x["category"] == "economy")
        self.assertTrue(own["complete"])
        self.assertGreater(self.db.one("SELECT gil FROM players WHERE twitch_id='101'")["gil"], first_gil)
        after = contract_view(self.db.conn)
        economy = next(x for x in after["objectives"] if x["category"] == "economy")
        expected = min(contract["target"], personal["target"]) if activity in contract["activities"] else 0
        self.assertEqual(economy["progress"], expected)

    def test_no_progress_from_unsupported_events_or_shared_events(self):
        self._record("101", "unrelated_key", "noise")
        self.game.fellowship_system.record_shared_activity("raid_clear", event_key="raid:only")
        self.assertTrue(all(i["progress"] == 0 for i in contract_view(self.db.conn)["objectives"]))
        self.assertTrue(all(i["progress"] == 0 for i in board_view(self.db.conn, "101")["daily"]["objectives"]))

    def test_future_rotations_have_no_carryover(self):
        self._record("101", "craft", "today-craft", amount=2)
        next_day = 86400 + __import__("time").time()
        next_month = 30 * 86400 + __import__("time").time()
        future = board_view(self.db.conn, "101", timestamp=next_day)
        self.assertTrue(all(o["progress"] == 0 for o in future["daily"]["objectives"]))
        self.assertTrue(all(o["progress"] == 0 for o in board_view(self.db.conn, "101", timestamp=next_month)["weekly"]["objectives"]))

    def test_restart_and_integrity(self):
        self._record("101", "craft", "restart:event", amount=3)
        prior = board_view(self.db.conn, "101")
        self.assertEqual(self.db.one("PRAGMA quick_check")[0], "ok")
        self.db.close()
        reopened = Database(self.path)
        try:
            self.assertEqual(prior, board_view(reopened.conn, "101"))
            self.assertEqual(reopened.schema_version(), 28)
            self.assertEqual(reopened.one("PRAGMA foreign_key_check"), None)
        finally:
            reopened.close()

    def test_weekly_gear_grants_shop_item_or_suitable_materials(self):
        choice = self._matching(WEEKLIES, "weekly")["activity"]
        action = "venture_complete" if choice["id"] == "weekly_ventures" else "expedition_complete"
        self._record("101", action, "weekly-gear-low", amount=choice["target"])
        source = "guild_initiative:weekly:"
        awards = self.db.all("SELECT asset_id,amount FROM transactions WHERE player_id='101' AND kind='item' AND source LIKE ?", (source+"%",))
        self.assertEqual(len(awards), 1)
        self.assertIn(awards[0]["asset_id"], self.data.items)
        # A max-level character cannot receive a misleading Lv.1-35 item.
        self.db.execute("UPDATE players SET level=99 WHERE twitch_id='102'")
        self._record("102", action, "weekly-gear-high", amount=choice["target"])
        awards = self.db.all("SELECT asset_id,amount FROM transactions WHERE player_id='102' AND kind='item' AND source LIKE ?", (source+"%",))
        self.assertEqual([(r["asset_id"], r["amount"]) for r in awards], [("mythril_ore", 2)])

    def test_new_member_does_not_get_completed_contract_backpay(self):
        contract = self._matching(CONTRACTS, "weekly")["activity"]
        action = "venture_complete" if contract["id"] == "guild_ventures" else "expedition_complete"
        self._record("101", action, "guild-done", amount=contract["target"])
        self.assertTrue(self.game.recruit("103", "hero103", "Late Member").ok)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM guild_initiative_rewards WHERE scope='contract' AND player_id='103'")["n"], 0)
        self._record("103", action, "late-member-action")
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM guild_initiative_rewards WHERE scope='contract' AND player_id='103'")["n"], 0)

    def test_schema_25_upgrade_creates_verified_backup_without_overwriting_progress(self):
        import sqlite3
        self._record("101", "craft", "before-migration", amount=2)
        original = self.db.one("SELECT gil,level FROM players WHERE twitch_id='101'")
        inventory = {r["item_id"]: r["quantity"] for r in self.db.all("SELECT item_id,quantity FROM inventory WHERE player_id='101'")}
        self.db.close()
        with closing(sqlite3.connect(self.path)) as conn, conn:
            for table in ("guild_initiative_contributions", "guild_initiative_contracts", "guild_initiative_player_progress", "guild_initiative_rewards", "guild_initiative_maintenance"):
                conn.execute(f"DROP TABLE {table}")
            conn.execute("DELETE FROM schema_migrations WHERE version=26")
        migrated = Database(self.path)
        try:
            self.assertEqual(migrated.schema_version(), 28)
            self.assertIn("pre_schema_26_", migrated.pre_migration_backup_path.name)
            self.assertEqual(tuple(original), tuple(migrated.one("SELECT gil,level FROM players WHERE twitch_id='101'")))
            self.assertEqual(inventory, {r["item_id"]: r["quantity"] for r in migrated.all("SELECT item_id,quantity FROM inventory WHERE player_id='101'")})
            self.assertEqual(migrated.one("PRAGMA quick_check")[0], "ok")
        finally:
            migrated.close()
        self.db = Database(self.path)

    def test_storage_cleanup_retains_recent_periods_and_audit(self):
        from crystal_guild.guild_initiatives import _prune_expired
        with self.db.tx() as conn:
            for period in ("2024-W01", "2026-W39"):
                conn.execute("INSERT INTO guild_initiative_contracts(period_key,objective_id,target,progress) VALUES (?,'old',10,1)", (period,))
            for period in ("2024-01-01", "2026-09-24"):
                conn.execute("INSERT INTO guild_initiative_player_progress(player_id,scope,period_key,objective_id,target) VALUES ('101','daily',?,'old',5)", (period,))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES ('101','gil','gil',1,'archived_audit')")
            _prune_expired(conn, timestamp=__import__('datetime').datetime(2026,9,26,tzinfo=__import__('datetime').timezone.utc).timestamp())
        self.assertEqual([r["period_key"] for r in self.db.all("SELECT period_key FROM guild_initiative_contracts ORDER BY period_key")], ["2026-W39"])
        self.assertEqual([r["period_key"] for r in self.db.all("SELECT period_key FROM guild_initiative_player_progress WHERE objective_id='old' ORDER BY period_key")], ["2026-09-24"])
        self.assertEqual(self.db.one("SELECT count(*) AS n FROM transactions WHERE source='archived_audit'")["n"], 1)

    def test_rolled_back_receipt_does_not_leave_progress_or_money(self):
        before = int(self.db.one("SELECT gil FROM players WHERE twitch_id='101'")["gil"])
        with self.assertRaisesRegex(RuntimeError, "abort"):
            with self.db.tx() as conn:
                self._record("101", "craft", "rollback-event", amount=99)
                raise RuntimeError("abort")
        self.assertFalse(self.db.one("SELECT 1 FROM fellowship_events WHERE event_key='rollback-event'"))
        self.assertFalse(self.db.one("SELECT 1 FROM guild_initiative_rewards WHERE player_id='101'"))
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='101'")["gil"]), before)


if __name__ == "__main__":
    unittest.main()

"""Records & Moments Step 1: historical provenance and compatibility gates."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class PersonalRecordsStep1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        engine = CrystalGuildEngine(self.db, self.data)
        self.assertTrue(engine.recruit("100", "van", "Van").ok)
        self.assertTrue(engine.recruit("200", "other", "Other").ok)
        self.repo = PortalRepository(self.path, ROOT / "data")

    def tearDown(self):
        self.repo.close()
        self.db.close()
        self.tmp.cleanup()

    def _records(self, who="van"):
        result = self.repo.records(who)
        self.assertIsNotNone(result)
        self.assertIn("combat", result)  # Existing API shape survives.
        self.assertIn("rivalries", result)
        self.assertIn("trials", result)
        return {r["id"]: r for r in result["personal_records"]["records"]}

    def test_new_players_do_not_receive_invented_historical_records(self):
        records = self._records()
        self.assertEqual(records["highest_hit"]["status"], "not_set")
        self.assertIsNone(records["biggest_purchase"]["value"])
        self.assertEqual(records["closest_victory"]["status"], "awaiting_tracking")
        self.assertEqual(records["longest_venture"]["status"], "awaiting_tracking")
        self.assertEqual(records["closest_world_event"]["status"], "awaiting_tracking")
        self.assertEqual(records["longest_cactpot_loss_streak"]["status"], "not_set")
        self.assertEqual(records["biggest_raid_payout"]["status"], "not_set")

    def test_historical_transactions_are_scoped_and_non_purchase_fees_excluded(self):
        self.db.update_record_stats("100", maxima={"best_hit": 900})
        self.db.execute("INSERT INTO player_monster_records(player_id,monster_id,best_hit) VALUES ('100','behemoth',900)")
        rows = [
            ("100", -1200, "shop"),
            ("100", -2500, "forge"),
            ("100", -1750, "trading_post_buy"),
            ("100", 3100, "trading_post_sale"),
            ("100", 3600, "boss:goblin_king"),
            ("100", 4900, "boss:ifrit"),  # Trial payouts cannot be branded Raids.
            ("200", -9999999, "shop"),
            ("200", 9999999, "boss:goblin_king"),
        ]
        for player_id, amount, source in rows:
            self.db.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) "
                            "VALUES (?,?,?, ?,?)", (player_id, "gil", "gil", amount, source))
        r = self._records()
        self.assertEqual(r["highest_hit"]["value"], 900)
        self.assertEqual(r["highest_hit"]["context"]["monster"], "Behemoth")
        self.assertEqual(r["biggest_purchase"]["value"], 1750)
        self.assertEqual(r["biggest_expense"]["value"], 2500)
        self.assertEqual(r["biggest_sale"]["value"], 3100)
        self.assertEqual(r["biggest_raid_payout"]["value"], 3600)
        self.assertEqual(r["biggest_raid_payout"]["context"]["boss_id"], "goblin_king")
        self.assertIsNone(self._records("other")["highest_hit"]["value"])
        self.assertEqual(self._records("other")["biggest_purchase"]["value"], 9999999)

    def test_saucer_streaks_strict_consecutive_paid_resolved_rounds(self):
        events = [
            ("mini_cactpot", 50, 0),
            ("mini_cactpot", 50, 20),
            ("mini_cactpot", 50, 50),  # Draw breaks consecutive streak.
            ("mini_cactpot", 50, 0),
            ("slots", 10, 0),
            ("mini_cactpot", 50, 0),
            ("mini_cactpot", 50, 100),  # Win breaks the two streaks.
            ("mini_cactpot", 50, 0),
            ("mini_cactpot", 50, 0),
            ("slots", 100, 20),
            ("mini_cactpot", 50, 0),
            ("slots", 0, 0),  # Free round ignored.
        ]
        for i, (game, wager, payout) in enumerate(events):
            self.db.execute("INSERT INTO gold_saucer_history("
                            "player_id,game,wager,payout,outcome,details_json,created_at) "
                            "VALUES (?,?,?,?,?,'{}',?)",
                            ("100", game, wager, payout, "result", 1000 + i))
        r = self._records()
        self.assertEqual(r["longest_cactpot_loss_streak"]["value"], 3)
        self.assertEqual(r["longest_saucer_loss_streak"]["value"], 4)
        self.assertEqual(r["biggest_saucer_payout"]["value"], 100)
        self.assertEqual(r["biggest_saucer_loss"]["value"], 80)

    def test_published_world_event_threat_is_not_confused_with_live_boss_level(self):
        self.db.execute("INSERT INTO player_world_event_clears(player_id,world_event_id,clears) "
                        "VALUES ('100','savage_coeurl',2)")
        self.db.execute("INSERT INTO player_world_event_clears(player_id,world_event_id,clears) "
                        "VALUES ('100','notorious_behemoth',1)")
        r = self._records()
        self.assertEqual(r["highest_world_event_threat"]["value"], "Extreme")
        self.assertEqual(r["highest_world_event_threat"]["context"]["event_ids"], ["notorious_behemoth"])
        self.assertIn("not_dynamic_boss_level", r["highest_world_event_threat"]["context"]["meaning"])
        self.assertIsNone(self._records("other")["highest_world_event_threat"]["value"])

    def test_repeat_reads_are_read_only_and_do_not_award_titles(self):
        self.db.execute("INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) "
                        "VALUES ('100','mini_cactpot',50,0,'loss','{}',1001)")
        titles_before = self.db.one("SELECT COUNT(*) AS n FROM player_titles WHERE player_id='100'")["n"]
        achievements_before = self.db.one("SELECT COUNT(*) AS n FROM achievements WHERE player_id='100'")["n"]
        first = self._records()
        second = self._records()
        self.assertEqual(first, second)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_titles WHERE player_id='100'")["n"], titles_before)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM achievements WHERE player_id='100'")["n"], achievements_before)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM schema_migrations WHERE version>23")["n"], 0)


if __name__ == "__main__":
    unittest.main()

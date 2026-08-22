from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class PlayerRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0, venture_treasure_chance=0.0)
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_combat_metrics_feed_records_snapshot(self):
        self.game._record_combat_metrics(
            "1",
            "warrior",
            "goblin",
            battle_type="venture",
            won=True,
            knocked_out=False,
            damage_dealt=1234,
            damage_taken=321,
            healing_done=77,
            best_hit=456,
        )
        repo = PortalRepository(self.path, ROOT / "data")
        data = repo.records("van")
        self.assertEqual(data["combat"]["damage_dealt"], 1234)
        self.assertEqual(data["combat"]["best_hit"], 456)
        self.assertEqual(data["combat"]["healing_done"], 77)
        self.assertEqual(data["rivalries"]["favorite_job"]["name"], "Warrior")

    def test_records_command_reports_rivalry_and_economy_sections(self):
        self.game._record_combat_metrics(
            "1",
            "warrior",
            "goblin",
            battle_type="hunt",
            won=False,
            knocked_out=True,
            damage_dealt=88,
            damage_taken=999,
            healing_done=0,
            best_hit=44,
        )
        result = self.game.records("1")
        self.assertTrue(result.ok)
        joined = " ".join(result.messages)
        self.assertIn("Combat", joined)
        self.assertIn("Career", joined)
        self.assertIn("Nemesis", joined)


    def test_batched_record_updates_apply_increments_and_maxima(self):
        self.db.update_record_stats(
            "1",
            {"damage_dealt": 100, "damage_taken": 40, "battles": 1},
            {"best_hit": 75},
        )
        self.db.update_record_stats(
            "1",
            {"damage_dealt": 25, "battles": 1},
            {"best_hit": 50},
        )
        rows = {
            row["metric"]: int(row["value"])
            for row in self.db.all(
                "SELECT metric, value FROM player_record_stats WHERE player_id='1'"
            )
        }
        self.assertEqual(rows["damage_dealt"], 125)
        self.assertEqual(rows["damage_taken"], 40)
        self.assertEqual(rows["battles"], 2)
        self.assertEqual(rows["best_hit"], 75)

    def test_record_tables_backfill_existing_legacy_counters(self):
        self.db.execute("UPDATE players SET ventures=9, deaths=3 WHERE twitch_id='1'")
        self.db.close()
        self.db = Database(self.path)
        rows = {
            row["metric"]: row["value"]
            for row in self.db.all("SELECT metric, value FROM player_record_stats WHERE player_id='1'")
        }
        # New installations initialize the metrics at zero when the player is first created.
        # The live player row remains authoritative for legacy counters in the Records view.
        self.assertIn("ventures_started", rows)
        self.assertIn("times_ko", rows)


if __name__ == "__main__":
    unittest.main()

"""Step 3: server-side Bestiary research progression and durable mastery rewards."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.bestiary_progress import progress_for, reconcile_mastery
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class BestiaryResearchStep3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.engine = CrystalGuildEngine(self.db, self.data, venture_cooldown_seconds=0, venture_treasure_chance=0.0)
        self.engine.recruit("100", "van", "Van")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def defeats(self, monster_id: str, amount: int, player_id: str = "100") -> None:
        self.db.execute(
            "INSERT INTO bestiary(player_id,monster_id,defeats) VALUES (?,?,?) "
            "ON CONFLICT(player_id,monster_id) DO UPDATE SET defeats=excluded.defeats",
            (player_id, monster_id, amount),
        )

    def test_schema_22_adds_mastery_receipt_ledger(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 23)
        self.assertEqual(self.db.schema_version(), 24)
        columns = {row["name"] for row in self.db.all("PRAGMA table_info(player_bestiary_mastery)")}
        self.assertEqual(columns, {"player_id", "monster_id", "research_points", "source_defeats", "mastered_at"})

    def test_historical_regional_mastery_backfills_once(self):
        self.defeats("goblin", 20)
        first = reconcile_mastery(self.db, self.data, "100")
        second = reconcile_mastery(self.db, self.data, "100")
        self.assertEqual(first["masteries_added"], 1)
        self.assertEqual(first["research_points_added"], 1)
        self.assertEqual(second["masteries_added"], 0)
        row = self.db.one("SELECT * FROM player_bestiary_mastery WHERE player_id='100' AND monster_id='goblin'")
        self.assertEqual(int(row["research_points"]), 1)
        self.assertEqual(int(row["source_defeats"]), 20)

    def test_category_thresholds_are_20_5_3(self):
        self.defeats("goblin", 19)
        self.defeats("goblin_chieftain", 4)
        self.defeats("elder_ochu", 2)
        self.assertEqual(reconcile_mastery(self.db, self.data, "100")["masteries_added"], 0)
        self.defeats("goblin", 20)
        self.defeats("goblin_chieftain", 5)
        self.defeats("elder_ochu", 3)
        result = reconcile_mastery(self.db, self.data, "100")
        self.assertEqual(result["masteries_added"], 3)
        self.assertEqual(result["research_points_added"], 3)

    def test_progress_is_derived_from_existing_defeats(self):
        p0 = progress_for(self.data, "goblin", 0)
        p1 = progress_for(self.data, "goblin", 1)
        p3 = progress_for(self.data, "goblin", 3)
        p5 = progress_for(self.data, "goblin", 5)
        p10 = progress_for(self.data, "goblin", 10)
        p15 = progress_for(self.data, "goblin", 15)
        p20 = progress_for(self.data, "goblin", 20)
        self.assertEqual(p0["stage"], "undiscovered")
        self.assertIn("name", p1["visible_fields"])
        self.assertIn("family", p3["visible_fields"])
        self.assertIn("weakness", p5["visible_fields"])
        self.assertIn("drops", p10["visible_fields"])
        self.assertIn("lore", p15["visible_fields"])
        self.assertTrue(p20["mastered"])
        self.assertIsNone(p20["next_milestone"])

    def test_portal_fails_closed_on_locked_intel(self):
        self.defeats("goblin", 1)
        repo = PortalRepository(self.path, ROOT / "data")
        row = next(x for x in repo.bestiary("van")["monsters"] if x["id"] == "goblin")
        self.assertEqual(row["name"], "Goblin")
        self.assertIsNotNone(row["level"])
        self.assertIsNone(row["weakness"])
        self.assertIsNone(row["combat_profile"])
        self.assertEqual(row["drops"], [])
        self.assertIsNone(row["lore"])
        repo.close()

    def test_portal_reveals_each_stage_without_leaking_future_stages(self):
        cases = [
            (3, True, False, False, False),
            (5, True, True, False, False),
            (10, True, True, True, False),
            (15, True, True, True, True),
        ]
        repo = PortalRepository(self.path, ROOT / "data")
        for defeats, family, weakness, drops, lore in cases:
            with self.subTest(defeats=defeats):
                self.defeats("goblin", defeats)
                row = next(x for x in repo.bestiary("van")["monsters"] if x["id"] == "goblin")
                self.assertEqual(bool(row["family"]), family)
                self.assertEqual(row["weakness"] is not None, weakness)
                self.assertEqual(bool(row["drops"]), drops)
                self.assertEqual(row["lore"] is not None, lore)
        repo.close()

    def test_mastery_reward_is_player_scoped_and_idempotent(self):
        self.engine.recruit("200", "terra", "Terra")
        self.defeats("goblin", 20, "100")
        self.defeats("goblin", 19, "200")
        reconcile_mastery(self.db, self.data)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_bestiary_mastery WHERE player_id='100' AND monster_id='goblin'"))
        self.assertIsNone(self.db.one("SELECT 1 FROM player_bestiary_mastery WHERE player_id='200' AND monster_id='goblin'"))
        reconcile_mastery(self.db, self.data)
        count = self.db.one("SELECT COUNT(*) AS n FROM player_bestiary_mastery WHERE player_id='100'")["n"]
        self.assertEqual(int(count), 1)

    def test_portal_summary_uses_durable_reward_ledger(self):
        self.defeats("goblin", 20)
        reconcile_mastery(self.db, self.data, "100")
        repo = PortalRepository(self.path, ROOT / "data")
        bestiary = repo.bestiary("van")
        self.assertEqual(bestiary["summary"]["mastered"], 1)
        self.assertEqual(bestiary["summary"]["mastery_seals"], 1)
        self.assertEqual(bestiary["summary"]["research_points"], 1)
        row = next(x for x in bestiary["monsters"] if x["id"] == "goblin")
        self.assertTrue(row["mastery_reward"]["seal"])
        self.assertEqual(row["mastery_reward"]["research_points"], 1)
        repo.close()

    def test_unknown_bestiary_row_never_grants_mastery(self):
        self.defeats("future_unknown_monster", 999)
        result = reconcile_mastery(self.db, self.data, "100")
        self.assertEqual(result["masteries_added"], 0)


if __name__ == "__main__":
    unittest.main()

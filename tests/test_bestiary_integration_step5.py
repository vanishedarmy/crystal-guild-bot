"""Step 5: unified Bestiary projection over existing encounter systems."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.seasonal_events import EDITION_ID

ROOT = Path(__file__).resolve().parents[1]


class BestiaryIntegrationStep5Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.engine = CrystalGuildEngine(self.db, self.data, venture_cooldown_seconds=0, venture_treasure_chance=0.0)
        self.engine.recruit("100", "van", "Van")
        self.repo = PortalRepository(self.path, ROOT / "data")

    def tearDown(self):
        self.repo.close()
        self.db.close()
        self.tmp.cleanup()

    def snapshot(self):
        return self.repo.bestiary("van")

    def by_id(self, entry_id: str):
        return next(row for row in self.snapshot()["monsters"] if row["id"] == entry_id)

    def test_unified_catalog_has_173_unique_scoped_entries(self):
        snap = self.snapshot()
        rows = snap["monsters"]
        self.assertEqual(len(rows), 173)
        self.assertEqual(len({row["id"] for row in rows}), 173)
        scopes = {}
        for row in rows:
            scopes[row["scope"]] = scopes.get(row["scope"], 0) + 1
        self.assertEqual(scopes, {"base": 120, "boss": 38, "world_event": 10, "seasonal": 5})
        self.assertEqual(snap["summary"]["base_total"], 120)
        self.assertEqual(snap["summary"]["special_total"], 53)

    def test_locked_external_records_fail_closed(self):
        row = self.by_id("boss:ifrit")
        self.assertFalse(row["discovered"])
        self.assertEqual(row["name"], "???")
        self.assertIsNone(row["level"])
        self.assertEqual(row["drops"], [])
        self.assertIsNone(row["lore"])
        self.assertTrue(row["mastery_reward"]["external"])
        self.assertFalse(row["mastery_reward"]["seal"])

    def test_raid_clear_projects_from_existing_boss_history_without_bestiary_reward(self):
        self.db.execute(
            "INSERT INTO player_boss_clears(player_id,boss_id,clears,best_damage,last_cleared_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",
            ("100", "ifrit", 2, 9999),
        )
        row = self.by_id("boss:ifrit")
        self.assertTrue(row["discovered"])
        self.assertEqual(row["name"], "Ifrit")
        self.assertEqual(row["progress_count"], 2)
        self.assertEqual(row["progress_unit"], "clear")
        self.assertEqual(row["category"], "raid")
        self.assertTrue(row["research"]["mastered"])
        self.assertEqual(row["art"], "/retro-phase-ii/boss-art-v1/ifrit.webp")
        self.assertFalse(row["mastery_reward"]["seal"])
        self.assertEqual(row["mastery_reward"]["research_points"], 0)
        self.assertEqual(self.snapshot()["summary"]["research_points"], 0)

    def test_world_event_record_uses_world_event_clear_table(self):
        self.db.execute(
            "INSERT INTO player_world_event_clears(player_id,world_event_id,clears,first_cleared_at,last_cleared_at) VALUES (?,?,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
            ("100", "notorious_behemoth"),
        )
        row = self.by_id("world_event:notorious_behemoth")
        self.assertTrue(row["discovered"])
        self.assertEqual(row["name"], "Notorious Behemoth")
        self.assertEqual(row["category"], "world_event")
        self.assertEqual(row["progress_unit"], "victory")
        self.assertIn("world-events/a1/notorious_behemoth.webp", row["art"])
        self.assertIn("Hall of Trophies", row["mastery_reward"]["source"])

    def test_seasonal_records_are_edition_scoped_and_persist_from_event_tables(self):
        self.db.execute(
            "INSERT INTO player_seasonal_monster_clears(player_id,edition_id,variant_id,clears,first_cleared_at,last_cleared_at) VALUES (?,?,?,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
            ("100", EDITION_ID, "jack_o_bomb"),
        )
        self.db.execute(
            "INSERT INTO player_seasonal_event_progress(player_id,edition_id,warden_clears) VALUES (?,?,1) "
            "ON CONFLICT(player_id,edition_id) DO UPDATE SET warden_clears=1",
            ("100", EDITION_ID),
        )
        jack = self.by_id(f"seasonal:{EDITION_ID}:jack_o_bomb")
        warden = self.by_id(f"seasonal:{EDITION_ID}:hollow_warden")
        self.assertTrue(jack["discovered"])
        self.assertTrue(warden["discovered"])
        self.assertEqual(jack["edition_id"], EDITION_ID)
        self.assertTrue(jack["locked_art"].endswith("jack-o-bomb-locked.webp"))
        self.assertTrue(warden["locked_art"].endswith("hollow-warden-locked.webp"))

    def test_scoped_ids_keep_base_and_boss_tonberry_king_separate(self):
        snap = self.snapshot()
        ids = {row["id"] for row in snap["monsters"]}
        self.assertIn("tonberry_king", ids)
        self.assertIn("boss:tonberry_king", ids)

    def test_external_records_do_not_create_mastery_ledger_rows(self):
        self.db.execute(
            "INSERT INTO player_boss_clears(player_id,boss_id,clears,best_damage,last_cleared_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",
            ("100", "ifrit", 1, 5000),
        )
        self.snapshot()
        count = self.db.one("SELECT COUNT(*) AS n FROM player_bestiary_mastery WHERE player_id=?", ("100",))["n"]
        self.assertEqual(int(count), 0)


if __name__ == "__main__":
    unittest.main()

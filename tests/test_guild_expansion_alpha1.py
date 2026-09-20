from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class GuildExpansionAlpha1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(31),
        )
        self.game.recruit("1", "van", "Van")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_public_guild_board_exposes_major_facilities_plus_service_buildings(self):
        guild = self.game.fellowship_system.public_snapshot()
        ids = [facility["id"] for facility in guild["facilities"]]
        self.assertEqual(ids, ["guild_hall", "workshop", "emporium_annex", "trading_post", "chocobo_stable", "archives", "airship_dock"])
        self.assertTrue(all(int(facility["max_level"]) == 3 for facility in guild["facilities"] if facility["id"] not in {"emporium_annex", "trading_post"}))
        annex = next(facility for facility in guild["facilities"] if facility["id"] == "emporium_annex")
        self.assertEqual(int(annex["max_level"]), 1)
        trading_post = next(facility for facility in guild["facilities"] if facility["id"] == "trading_post")
        self.assertEqual(int(trading_post["max_level"]), 1)
        dock = next(facility for facility in guild["facilities"] if facility["id"] == "airship_dock")
        self.assertFalse(dock["locked"])
        self.assertIn(dock["status"], {"Buildable", "Complete"})
        self.assertEqual(self.db.schema_version(), 19)

    def test_major_facility_projects_use_shared_resources_and_gameplay_milestones(self):
        self.db.execute("UPDATE fellowship_state SET level=6,renown=13000 WHERE singleton_id=1")
        available = {project["id"]: project for project in self.game.fellowship_system.available_projects()}
        self.assertIn("guild_hall_t2", available)
        self.assertIn("workshop_t1", available)
        self.assertIn("chocobo_stable_t1", available)
        self.assertIn("archives_t1", available)
        self.assertFalse(any(project["facility_id"] == "airship_dock" for project in available.values()))
        self.assertFalse(any(project.get("legacy") for project in available.values()))
        workshop = available["workshop_t1"]
        kinds = {req["kind"] for req in workshop["requirements"]}
        self.assertTrue({"gil", "item", "activity", "level"}.issubset(kinds))

    def test_prior_high_tiers_are_not_downgraded(self):
        self.db.execute("UPDATE fellowship_facilities SET tier=5 WHERE facility_id='workshop'")
        guild = self.game.fellowship_system.public_snapshot()
        workshop = next(facility for facility in guild["facilities"] if facility["id"] == "workshop")
        self.assertEqual(workshop["level"], 3)
        raw = self.db.one("SELECT tier FROM fellowship_facilities WHERE facility_id='workshop'")
        self.assertEqual(int(raw["tier"]), 5)
        self.assertEqual(round(self.game.fellowship_system.effects()["forge_discount"], 2), 0.10)

    def test_v12_schema8_database_adds_airship_dock_without_migration_or_reset(self):
        self.db.execute("DELETE FROM fellowship_facilities WHERE facility_id='airship_dock'")
        self.db.execute("UPDATE fellowship_facilities SET tier=4 WHERE facility_id='workshop'")
        self.db.close()
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay2.json"), rng=random.Random(32),
        )
        self.assertEqual(self.db.schema_version(), 19)
        dock = self.db.one("SELECT tier FROM fellowship_facilities WHERE facility_id='airship_dock'")
        workshop = self.db.one("SELECT tier FROM fellowship_facilities WHERE facility_id='workshop'")
        player = self.db.one("SELECT display_name FROM players WHERE twitch_id='1'")
        self.assertEqual(int(dock["tier"]), 0)
        self.assertEqual(int(workshop["tier"]), 4)
        self.assertEqual(player["display_name"], "Van")

    def test_existing_legacy_project_can_still_finish_after_upgrade(self):
        self.db.execute("UPDATE fellowship_state SET level=10,renown=50000 WHERE singleton_id=1")
        selected = self.game.set_fellowship_project("infirmary")
        self.assertTrue(selected.ok)
        active = self.game.fellowship_system.project_snapshot()
        self.assertEqual(active["facility_id"], "infirmary")
        self.assertTrue(active["legacy"])
        public_ids = {project["facility_id"] for project in self.game.fellowship_system.available_projects()}
        self.assertNotIn("infirmary", public_ids)


if __name__ == "__main__":
    unittest.main()

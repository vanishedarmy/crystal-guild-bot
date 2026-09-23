"""Player-facing copy and location labels must never change Bestiary authority."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class PlayerFacingLanguageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database_file = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.database_file)
        self.data = GameData(ROOT / "data")
        self.engine = CrystalGuildEngine(self.db, self.data)
        self.assertTrue(self.engine.recruit("100", "van", "Van").ok)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def snapshot(self):
        with_repo = PortalRepository(self.database_file, ROOT / "data")
        try:
            return with_repo.bestiary("van")
        finally:
            with_repo.close()

    def set_count(self, monster_id, n):
        self.db.execute(
            "INSERT INTO bestiary(player_id,monster_id,defeats) VALUES (?,?,?) "
            "ON CONFLICT(player_id,monster_id) DO UPDATE SET defeats=excluded.defeats",
            ("100", monster_id, n),
        )

    def test_names_are_hidden_until_habitat_reveals(self):
        self.set_count("sahagin", 1)  # First defeat only reveals its name.
        row = next(row for row in self.snapshot()["monsters"] if row["id"] == "sahagin")
        self.assertEqual(row["habitats"], [])
        self.assertEqual(row["habitat_names"], [])
        self.assertIsNone(row["family_description"])
        self.set_count("sahagin", 3)
        row = next(row for row in self.snapshot()["monsters"] if row["id"] == "sahagin")
        self.assertIn("sable_coast", row["habitats"])
        self.assertIn("Sable Coast", row["habitat_names"])
        self.assertNotIn("sable_coast", row["habitat_names"])
        self.assertTrue(row["family_description"])
        self.assertNotIn("Field records for", row["family_description"])
        self.assertIsNone(row["weakness"])
        self.assertEqual(row["drops"], [])

    def test_all_locations_match_authoritative_names(self):
        lookup = {**self.data.regions, **self.data.expedition_regions}
        for monster_id, entry in self.data.bestiary_research["entries"].items():
            milestone = self.data.bestiary_research["tiers"][entry["category"]]["milestones"][0]
            # Set enough defeats to reveal location and keep the raw ID stable.
            self.set_count(monster_id, max(3, milestone["defeats"]))
        rows = self.snapshot()["monsters"]
        for row in rows:
            if row["scope"] != "base":
                continue
            self.assertEqual(row["habitat_names"], [lookup[r]["name"] for r in row["habitats"]])
            self.assertEqual(row["habitats"], self.data.bestiary_research["entries"][row["id"]]["habitats"])

    def test_chat_status_uses_player_facing_language(self):
        self.assertIn("first entry", self.engine.bestiary("100").messages[0])
        self.set_count("goblin", 20)
        result = self.engine.bestiary("100")
        output = " ".join(result.messages)
        self.assertIn("Your Bestiary", output)
        self.assertIn("Most familiar:", output)
        self.assertIn("Research Points", output)
        self.assertNotIn("schema", output.lower())


if __name__ == "__main__":
    unittest.main()

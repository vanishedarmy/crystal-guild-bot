from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class MoogleEmporiumAnnexAlpha3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(1703),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.db.execute("UPDATE players SET level=99,current_job='warrior' WHERE twitch_id='100'")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_release_contract_keeps_schema_and_protocol_stable(self):
        self.assertEqual(__version__, "1.8.0-merc-rc2")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 17)
        self.assertEqual(self.db.schema_version(), 17)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 34)
        annex = self.db.one("SELECT tier FROM fellowship_facilities WHERE facility_id='emporium_annex'")
        self.assertIsNotNone(annex)
        self.assertEqual(int(annex["tier"]), 0)

    def test_annex_is_one_time_fellowship_construction(self):
        self.db.execute("UPDATE fellowship_state SET level=3,renown=5000 WHERE singleton_id=1")
        available = {project["id"]: project for project in self.game.fellowship_system.available_projects()}
        self.assertIn("emporium_annex_t1", available)
        annex = available["emporium_annex_t1"]
        self.assertEqual(int(annex["tier"]), 1)
        self.assertEqual(int(annex["required_level"]), 3)
        targets = {req["key"]: int(req["target"]) for req in annex["requirements"]}
        self.assertEqual(targets["gil"], 20_000)
        self.assertEqual(targets["item:mythril_ore"], 12)
        self.assertEqual(targets["activity:craft"], 20)
        self.assertEqual(targets["fellowship_level"], 3)

    def test_completion_expands_cached_rotations_from_nine_to_twelve(self):
        stock_before, _ = self.game._shop_stock("100")
        self.assertEqual(len(stock_before), 9)
        self.assertEqual(self.game.fellowship_system.emporium_stock_slots(), 9)

        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='emporium_annex'")
        stock_after, _ = self.game._shop_stock("100")
        self.assertEqual(self.game.fellowship_system.emporium_stock_slots(), 12)
        self.assertEqual(len(stock_after), 12)
        cached = self.db.one("SELECT stock_json FROM player_shops WHERE player_id='100'")
        self.assertIn(stock_after[-1]["id"], str(cached["stock_json"]))

    def test_portal_shop_and_fellowship_services_report_annex_state(self):
        closed = self.game.portal_shop_state("100")
        self.assertTrue(closed.ok)
        self.assertFalse(closed.data["annex_unlocked"])
        self.assertEqual(closed.data["stock_slots"], 9)

        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='emporium_annex'")
        opened = self.game.portal_shop_state("100")
        self.assertTrue(opened.ok)
        self.assertTrue(opened.data["annex_unlocked"])
        self.assertEqual(opened.data["stock_slots"], 12)
        self.assertEqual(opened.data["annex_bonus_slots"], 3)
        services = self.game.fellowship_system.workshop_services_snapshot("100")["emporium_annex"]
        self.assertTrue(services["unlocked"])
        self.assertEqual(services["stock_slots"], 12)

    def test_project_completion_constructs_annex_once(self):
        self.db.execute("UPDATE fellowship_state SET level=3,renown=5000 WHERE singleton_id=1")
        selected = self.game.set_fellowship_project("emporium_annex")
        self.assertTrue(selected.ok)
        project = self.game.fellowship_system.project_snapshot()
        self.assertEqual(project["id"], "emporium_annex_t1")
        for requirement in project["requirements"]:
            if requirement["kind"] == "level":
                continue
            self.db.execute(
                "UPDATE fellowship_project_progress SET current=? WHERE project_id=? AND requirement_key=?",
                (int(requirement["target"]), project["id"], requirement["key"]),
            )
        notes = self.game.fellowship_system._check_project_completion("100")
        self.assertTrue(any("Annex constructed" in note for note in notes))
        row = self.db.one("SELECT tier FROM fellowship_facilities WHERE facility_id='emporium_annex'")
        self.assertEqual(int(row["tier"]), 1)
        self.assertNotIn("emporium_annex_t1", {p["id"] for p in self.game.fellowship_system.available_projects()})


if __name__ == "__main__":
    unittest.main()

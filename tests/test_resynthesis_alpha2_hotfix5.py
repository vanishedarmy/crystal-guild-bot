from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class ResynthesisAlpha2Hotfix5Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db, self.data, venture_cooldown_seconds=0,
            venture_treasure_chance=1.0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(17),
        )
        self.game.recruit("100", "h5hero", "H5 Hero")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_release_contract_and_stream_venture_are_encounter_only(self):
        self.assertEqual(__version__, "1.9.0-world-events-alpha6")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 19)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 36)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)
        result = self.game.venture("100", bypass_cooldown=True)
        self.assertTrue(result.ok)
        self.assertEqual(result.data.get("venture_event"), "encounter")
        self.assertIsNotNone(self.game.active_encounter)
        self.assertEqual(self.game.active_encounter.get("kind"), "venture")
        state = self.game.portal_adventure_state("100").data["adventure_state"]
        self.assertFalse(state["venture"]["treasure_possible"])
        self.assertEqual(state["venture"]["encounter_chance_percent"], 100)
        self.assertEqual(state["venture"]["treasure_chance_percent"], 0)
        self.assertEqual(state["solo_venture"]["encounter_chance_percent"], 80)
        self.assertEqual(state["solo_venture"]["treasure_chance_percent"], 20)

    def test_inventory_gear_is_sorted_by_level_desc_and_equipment_exposes_level_jobs(self):
        for item_id in ("bronze_waraxe", "rune_axe", "steel_greataxe"):
            self.db.execute(
                "INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,1) "
                "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=1",
                ("100", item_id),
            )
        self.db.execute(
            "INSERT INTO equipment(player_id,weapon_id,armor_id,accessory_id) VALUES (?,?,NULL,NULL) "
            "ON CONFLICT(player_id) DO UPDATE SET weapon_id=excluded.weapon_id",
            ("100", "rune_axe"),
        )
        repo = PortalRepository(self.path, ROOT / "data")
        try:
            inventory = repo.inventory("h5hero")
            weapons = [row for row in inventory["items"] if row["type"] == "weapon"]
            levels = [row["min_level"] for row in weapons]
            self.assertEqual(levels, sorted(levels, reverse=True))
            overview = repo.overview("h5hero")
            equipped = next(row for row in overview["equipment"] if row["slot"] == "weapon")
            self.assertEqual(equipped["id"], "rune_axe")
            self.assertEqual(equipped["min_level"], 20)
            self.assertEqual(equipped["allowed_job_ids"][:3], ["beastmaster", "warrior", "darkknight"])
            self.assertEqual(equipped["allowed_jobs"][:3], ["Beastmaster", "Warrior", "Dark Knight"])
        finally:
            repo.close()


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.mercenary import HEROES_BY_ID

ROOT = Path(__file__).resolve().parents[1]


class MercServiceAlpha2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1804),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)
        self.db.execute("UPDATE players SET level=40,hunt_seals=300 WHERE twitch_id='100'")
        for hunt_id, clears in (("chieftains_challenge", 6), ("alpha_on_the_prowl", 5), ("sting_operation", 5)):
            self.db.execute(
                "INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100',?,?)",
                (hunt_id, clears),
            )

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_release_identity_and_rebalanced_fees(self):
        self.assertEqual(__version__, "1.8.0-merc-rc2")
        self.assertEqual(
            {hero: HEROES_BY_ID[hero]["fee_seals"] for hero in ("aerith", "tifa", "zidane", "yuna", "balthier", "cloud")},
            {"aerith": 5, "tifa": 6, "zidane": 5, "yuna": 7, "balthier": 9, "cloud": 12},
        )

    def test_mission_availability_explains_open_unsupported_and_occupied_states(self):
        state = self.game.portal_merc_state("100").data["merc_state"]
        by_id = {hero["id"]: hero for hero in state["heroes"]}
        self.assertEqual(by_id["aerith"]["mission_availability"]["hunt"]["status"], "available")
        self.assertIn("5 Hunt Seals", by_id["aerith"]["mission_availability"]["hunt"]["reason"])
        self.assertEqual(by_id["zidane"]["mission_availability"]["raid"]["status"], "unavailable")
        self.assertIn("Does not accept Raid", by_id["zidane"]["mission_availability"]["raid"]["reason"])

        self.assertTrue(self.game.portal_merc_hire("100", "tifa", "hunt", "a2-hunt").ok)
        state = self.game.portal_merc_state("100").data["merc_state"]
        by_id = {hero["id"]: hero for hero in state["heroes"]}
        self.assertEqual(by_id["tifa"]["mission_availability"]["raid"]["status"], "contracted")
        self.assertEqual(by_id["tifa"]["mission_availability"]["raid"]["reason"], "On contract — Hunt")
        self.assertEqual(by_id["aerith"]["mission_availability"]["hunt"]["status"], "unavailable")
        self.assertIn("Hunt slot occupied by Tifa Lockhart", by_id["aerith"]["mission_availability"]["hunt"]["reason"])

    def test_progression_locked_reason_is_preserved_per_mission(self):
        self.db.execute("UPDATE players SET level=1 WHERE twitch_id='100'")
        state = self.game.portal_merc_state("100").data["merc_state"]
        cloud = next(hero for hero in state["heroes"] if hero["id"] == "cloud")
        self.assertEqual(cloud["mission_availability"]["raid"]["status"], "locked")
        self.assertIn("Requires level 30", cloud["mission_availability"]["raid"]["reason"])


if __name__ == "__main__":
    unittest.main()

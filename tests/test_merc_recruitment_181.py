from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.mercenary import HEROES_BY_ID
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class MercRecruitment181Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1810),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)
        self.db.execute("UPDATE players SET level=40,hunt_seals=500,gil=200000 WHERE twitch_id='100'")
        self.db.execute(
            "INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100','chieftains_challenge',15)"
        )
        self.db.execute(
            "INSERT INTO player_dungeon_progress(player_id,dungeon_id,clears,defeats,retreats,best_rooms,last_outcome,last_completed_at) "
            "VALUES ('100','forgotten_ossuary',3,0,0,5,'complete',1)"
        )

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_release_contract_and_schema_18_registry_table(self):
        self.assertEqual(__version__, "1.8.1-merc-recruitment")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 18)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 35)
        self.assertEqual(self.db.schema_version(), 18)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_merc_recruits'"))
        state = self.game.portal_merc_state("100").data["merc_state"]
        self.assertEqual(len(state["heroes"]), 12)
        self.assertEqual(state["registry"], {"recruited": 6, "total": 12})

    def test_expansion_hero_is_locked_until_permanently_recruited(self):
        state = self.game.portal_merc_state("100").data["merc_state"]
        auron = next(hero for hero in state["heroes"] if hero["id"] == "auron")
        self.assertFalse(auron["available"])
        self.assertFalse(auron["recruited"])
        self.assertEqual(auron["recruitment"]["status"], "ready")
        blocked = self.game.portal_merc_hire("100", "auron", "hunt", "hire-auron-before-recruit")
        self.assertFalse(blocked.ok)
        self.assertIn("has not joined your Merc Registry", blocked.messages[0])

        recruited = self.game.portal_merc_recruit("100", "auron", "recruit-auron")
        self.assertTrue(recruited.ok)
        auron = next(hero for hero in recruited.data["merc_state"]["heroes"] if hero["id"] == "auron")
        self.assertTrue(auron["recruited"])
        self.assertTrue(auron["available"])
        self.assertEqual(recruited.data["merc_state"]["registry"]["recruited"], 7)
        hired = self.game.portal_merc_hire("100", "auron", "hunt", "hire-auron-after-recruit")
        self.assertTrue(hired.ok)
        self.assertEqual(hired.data["merc_state"]["contracts_by_mission"]["hunt"]["hero_id"], "auron")

    def test_contract_recruitment_charges_gil_once_and_replay_is_safe(self):
        before = int(self.db.one("SELECT gil FROM players WHERE twitch_id='100'")["gil"])
        cost = int(HEROES_BY_ID["terra"]["recruitment"]["gil_cost"])
        first = self.game.portal_merc_recruit("100", "terra", "recruit-terra")
        self.assertTrue(first.ok)
        self.assertEqual(first.data["gil_paid"], cost)
        after = int(self.db.one("SELECT gil FROM players WHERE twitch_id='100'")["gil"])
        self.assertEqual(after, before - cost)
        replay = self.game.portal_merc_recruit("100", "terra", "recruit-terra")
        self.assertTrue(replay.ok)
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='100'")["gil"]), after)
        rows = self.db.all("SELECT amount FROM transactions WHERE player_id='100' AND source='merc_recruit:terra'")
        self.assertEqual([int(row["amount"]) for row in rows], [-cost])
        recruit = self.db.one("SELECT unlock_method,gil_paid FROM player_merc_recruits WHERE player_id='100' AND hero_id='terra'")
        self.assertEqual(recruit["unlock_method"], "contract")
        self.assertEqual(int(recruit["gil_paid"]), cost)

    def test_recruitment_objectives_require_dungeon_progress(self):
        self.db.execute("DELETE FROM player_dungeon_progress WHERE player_id='100'")
        blocked = self.game.portal_merc_recruit("100", "ramza", "recruit-ramza-blocked")
        self.assertFalse(blocked.ok)
        self.assertIn("Dungeon Clears 0/3", blocked.messages[0])
        state = blocked.data["merc_state"]
        ramza = next(hero for hero in state["heroes"] if hero["id"] == "ramza")
        self.assertEqual(ramza["recruitment"]["status"], "locked")

    def test_founding_roster_does_not_require_recruitment(self):
        state = self.game.portal_merc_state("100").data["merc_state"]
        cloud = next(hero for hero in state["heroes"] if hero["id"] == "cloud")
        self.assertTrue(cloud["recruited"])
        self.assertFalse(cloud["recruitment"]["required"])
        denied = self.game.portal_merc_recruit("100", "cloud", "recruit-founder")
        self.assertFalse(denied.ok)
        self.assertIn("founding Merc roster", denied.messages[0])


if __name__ == "__main__":
    unittest.main()

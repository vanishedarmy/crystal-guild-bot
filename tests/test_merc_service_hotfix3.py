from __future__ import annotations

import random
import sqlite3
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class MercServiceHotfix3Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), overlay_state_path=str(Path(self.temp.name) / "overlay.json"), rng=random.Random(1803))
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)
        self.db.execute("UPDATE players SET level=40,hunt_seals=200 WHERE twitch_id='100'")
        for hunt_id, clears in (("chieftains_challenge", 6), ("alpha_on_the_prowl", 5), ("sting_operation", 5)):
            self.db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100',?,?)", (hunt_id, clears))

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def test_three_independent_slots_and_unique_heroes(self):
        self.assertTrue(self.game.portal_merc_hire("100", "tifa", "hunt", "h3-hunt").ok)
        self.assertTrue(self.game.portal_merc_hire("100", "zidane", "venture", "h3-venture").ok)
        self.assertTrue(self.game.portal_merc_hire("100", "yuna", "raid", "h3-raid").ok)
        state = self.game.portal_merc_state("100").data["merc_state"]
        self.assertEqual(len(state["contracts"]), 3)
        self.assertEqual(set(state["contracts_by_mission"]), {"hunt", "venture", "raid"})
        self.assertEqual(state["open_mission_types"], [])
        self.assertFalse(state["can_hire"])
        self.assertTrue(all(h["status"] in {"contracted", "unavailable", "locked"} for h in state["heroes"]))

    def test_slot_and_hero_cannot_be_double_booked(self):
        self.assertTrue(self.game.portal_merc_hire("100", "tifa", "hunt", "h3-a").ok)
        self.assertFalse(self.game.portal_merc_hire("100", "aerith", "hunt", "h3-b").ok)
        self.assertFalse(self.game.portal_merc_hire("100", "tifa", "raid", "h3-c").ok)
        self.assertTrue(self.game.portal_merc_hire("100", "aerith", "raid", "h3-d").ok)

    def test_claim_consumes_only_matching_slot(self):
        self.assertTrue(self.game.portal_merc_hire("100", "tifa", "hunt", "h3-hunt-2").ok)
        self.assertTrue(self.game.portal_merc_hire("100", "zidane", "venture", "h3-venture-2").ok)
        claimed = self.game._merc_claim_for_mission("100", "hunt")
        self.assertEqual(claimed["hero_id"], "tifa")
        state = self.game.portal_merc_state("100").data["merc_state"]
        self.assertNotIn("hunt", state["contracts_by_mission"])
        self.assertEqual(state["contracts_by_mission"]["venture"]["hero_id"], "zidane")

    def test_cancel_specific_slot(self):
        self.assertTrue(self.game.portal_merc_hire("100", "tifa", "hunt", "h3-hunt-3").ok)
        self.assertTrue(self.game.portal_merc_hire("100", "aerith", "raid", "h3-raid-3").ok)
        cancelled = self.game.portal_merc_cancel("100", "h3-cancel", "raid")
        self.assertTrue(cancelled.ok)
        state = cancelled.data["merc_state"]
        self.assertIn("hunt", state["contracts_by_mission"])
        self.assertNotIn("raid", state["contracts_by_mission"])

    def test_schema17_single_slot_layout_is_upgraded_in_place(self):
        self.db.close()
        raw = sqlite3.connect(self.path)
        raw.execute("ALTER TABLE player_merc_contracts RENAME TO player_merc_contracts_new")
        raw.execute("CREATE TABLE player_merc_contracts (player_id TEXT PRIMARY KEY, hero_id TEXT NOT NULL, mission_type TEXT NOT NULL, fee_marks INTEGER NOT NULL, hired_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)")
        raw.execute("INSERT INTO player_merc_contracts SELECT player_id,hero_id,mission_type,fee_marks,hired_at,updated_at FROM player_merc_contracts_new LIMIT 0")
        raw.execute("DROP TABLE player_merc_contracts_new")
        raw.commit(); raw.close()
        self.db = Database(self.path)
        info = self.db.all("PRAGMA table_info(player_merc_contracts)")
        pk = [r["name"] for r in sorted(info, key=lambda r: int(r["pk"] or 0)) if int(r["pk"] or 0) > 0]
        self.assertEqual(pk, ["player_id", "mission_type"])
        self.assertEqual(self.db.schema_version(), 20)


if __name__ == "__main__":
    unittest.main()

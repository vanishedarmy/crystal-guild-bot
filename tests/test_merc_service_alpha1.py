from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.mercenary import HEROES_BY_ID, MERC_PROPRIETOR
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class MercServiceAlpha1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1801),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)
        self.db.execute("UPDATE players SET level=30,hunt_seals=100 WHERE twitch_id='100'")
        # Seven lifetime Hunt clears unlock every launch merc except Cloud.
        for idx, hunt_id in enumerate(("chieftains_challenge", "alpha_on_the_prowl", "sting_operation")):
            self.db.execute(
                "INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100',?,?)",
                (hunt_id, (3, 2, 2)[idx]),
            )

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def test_release_contract_and_roster(self):
        self.assertEqual(__version__, "1.9.0-records-moments-alpha10")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 23)
        self.assertEqual(self.db.schema_version(), 23)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 37)
        state = self.game.portal_merc_state("100").data["merc_state"]
        self.assertEqual(state["proprietor"], MERC_PROPRIETOR)
        self.assertEqual(len(state["heroes"]), 18)
        self.assertEqual(state["hunt_seals"], 100)
        cloud = next(h for h in state["heroes"] if h["id"] == "cloud")
        self.assertFalse(cloud["available"])
        self.assertIn("15 Hunt clears", cloud["locked_reason"])

    def test_hire_is_persistent_paid_in_seals_and_supports_one_slot_per_job(self):
        before = self.game.portal_merc_state("100").data["merc_state"]["hunt_seals"]
        fee = HEROES_BY_ID["tifa"]["fee_seals"]
        hired = self.game.portal_merc_hire("100", "tifa", "hunt", "merc-hire-1")
        self.assertTrue(hired.ok)
        state = hired.data["merc_state"]
        self.assertEqual(state["hunt_seals"], before - fee)
        self.assertEqual(state["contract"]["hero_id"], "tifa")
        tifa = next(h for h in state["heroes"] if h["id"] == "tifa")
        aerith = next(h for h in state["heroes"] if h["id"] == "aerith")
        self.assertTrue(tifa["contracted"])
        self.assertEqual(tifa["status"], "contracted")
        self.assertEqual(tifa["contract_mission_type"], "hunt")
        self.assertTrue(tifa["available"])  # progression remains unlocked; contract state is separate
        self.assertFalse(aerith["contracted"])
        self.assertEqual(aerith["status"], "available")
        second = self.game.portal_merc_hire("100", "aerith", "raid", "merc-hire-2")
        self.assertTrue(second.ok)
        self.assertEqual(len(second.data["merc_state"]["contracts"]), 2)
        replay = self.game.portal_merc_hire("100", "tifa", "hunt", "merc-hire-1")
        self.assertTrue(replay.ok)
        self.assertEqual(self.game.portal_merc_state("100").data["merc_state"]["hunt_seals"], before - fee - HEROES_BY_ID["aerith"]["fee_seals"])
        tx = self.db.one("SELECT kind,amount FROM transactions WHERE player_id='100' AND source='merc_hire:tifa:hunt' ORDER BY id DESC LIMIT 1")
        self.assertEqual(tx["kind"], "hunt_seals")
        self.assertEqual(tx["amount"], -fee)

    def test_contract_claims_only_matching_mission(self):
        self.assertTrue(self.game.portal_merc_hire("100", "zidane", "venture", "merc-zidane").ok)
        self.assertIsNone(self.game._merc_claim_for_mission("100", "hunt"))
        claimed = self.game._merc_claim_for_mission("100", "venture")
        self.assertEqual(claimed["hero_id"], "zidane")
        self.assertIsNone(self.game.portal_merc_state("100").data["merc_state"]["contract"])
        row = self.db.one("SELECT outcome,fee_marks FROM merc_contract_history WHERE player_id='100' ORDER BY id DESC LIMIT 1")
        self.assertEqual(row["outcome"], "deployed")
        self.assertEqual(row["fee_marks"], HEROES_BY_ID["zidane"]["fee_seals"])

    def test_cancel_is_nonrefundable_and_recorded(self):
        before = self.game.portal_merc_state("100").data["merc_state"]["hunt_seals"]
        fee = HEROES_BY_ID["aerith"]["fee_seals"]
        self.assertTrue(self.game.portal_merc_hire("100", "aerith", "raid", "merc-aerith").ok)
        cancelled = self.game.portal_merc_cancel("100", "merc-cancel")
        self.assertTrue(cancelled.ok)
        self.assertEqual(cancelled.data["merc_state"]["hunt_seals"], before - fee)
        aerith = next(h for h in cancelled.data["merc_state"]["heroes"] if h["id"] == "aerith")
        self.assertFalse(aerith["contracted"])
        self.assertEqual(aerith["status"], "available")
        self.assertIsNone(aerith["contract_mission_type"])
        row = self.db.one("SELECT outcome FROM merc_contract_history WHERE player_id='100' ORDER BY id DESC LIMIT 1")
        self.assertEqual(row["outcome"], "cancelled")

    def test_locked_hero_unlocks_from_progression(self):
        locked = self.game.portal_merc_hire("100", "cloud", "raid", "merc-cloud-locked")
        self.assertFalse(locked.ok)
        self.assertIn("15 Hunt clears", locked.messages[0])
        self.db.execute("UPDATE player_hunts SET clears=clears+8 WHERE player_id='100' AND hunt_id='chieftains_challenge'")
        unlocked = self.game.portal_merc_hire("100", "cloud", "raid", "merc-cloud-open")
        self.assertTrue(unlocked.ok)
        self.assertEqual(unlocked.data["merc_state"]["contract"]["hero_id"], "cloud")

    def test_hunts_award_existing_hunt_seals_without_second_currency(self):
        player = self.game._player("100")
        hunt = self.game.data.hunts["chieftains_challenge"]
        monster = self.game.data.monsters[hunt["monster_id"]]
        before = self.game._player("100")
        seals_before = int(before["hunt_seals"])
        reward = self.game._award_hunt_victory("100", player, hunt, monster)
        after = self.game._player("100")
        self.assertEqual(int(after["hunt_seals"]), seals_before + int(reward["seals"]))
        kinds = {r["kind"] for r in self.db.all("SELECT kind FROM transactions WHERE player_id='100' AND source='hunt:chieftains_challenge'")}
        self.assertEqual(kinds, {"hunt_seals", "gil"})


if __name__ == "__main__":
    unittest.main()

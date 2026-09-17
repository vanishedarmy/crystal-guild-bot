from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class MercServiceRC1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            encounter_join_seconds=1,
            encounter_round_seconds=1,
            raid_join_seconds=1,
            raid_round_seconds=1,
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1805),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)
        self.db.execute("UPDATE players SET level=60,hunt_seals=300 WHERE twitch_id='100'")
        self.db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100','chieftains_challenge',20)")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_timed_hunt_stays_deployed_until_resolution(self):
        self.assertTrue(self.game.portal_merc_hire("100", "tifa", "hunt", "rc-hire-hunt").ok)
        dispatched = self.game.hunt("100", "chieftains_challenge", bypass_cooldown=True)
        self.assertTrue(dispatched.ok, dispatched.messages)

        state = self.game.portal_merc_state("100").data["merc_state"]
        hunt = state["contracts_by_mission"]["hunt"]
        self.assertTrue(hunt["deployed"])
        self.assertEqual(hunt["state"], "deployed")
        self.assertFalse(hunt["cancelable"])
        tifa = next(row for row in state["heroes"] if row["id"] == "tifa")
        self.assertEqual(tifa["status"], "deployed")
        self.assertIn("in progress", tifa["mission_availability"]["hunt"]["reason"])

        blocked_hire = self.game.portal_merc_hire("100", "aerith", "hunt", "rc-hire-blocked")
        self.assertFalse(blocked_hire.ok)
        self.assertIn("already deployed", blocked_hire.messages[0])
        blocked_cancel = self.game.portal_merc_cancel("100", "rc-cancel-blocked", "hunt")
        self.assertFalse(blocked_cancel.ok)
        self.assertIn("cannot be cancelled", blocked_cancel.messages[0])

        assignment = self.game.active_hunts["100"]
        assignment["encounter"]["monster_hp"] = 1
        result = self.game.resolve_hunt("100", force=True)
        self.assertTrue(result.ok, result.messages)
        state = self.game.portal_merc_state("100").data["merc_state"]
        self.assertNotIn("hunt", state["contracts_by_mission"])
        tifa = next(row for row in state["heroes"] if row["id"] == "tifa")
        self.assertFalse(tifa["deployed"])
        self.assertIn("hunt", tifa["hireable_mission_types"])


    def test_deployed_hunt_state_survives_runtime_recovery(self):
        self.assertTrue(self.game.portal_merc_hire("100", "tifa", "hunt", "rc-recovery-hire").ok)
        self.assertTrue(self.game.hunt("100", "chieftains_challenge", bypass_cooldown=True).ok)
        self.game._persist_runtime_state()

        overlay_path = str(Path(self.temp.name) / "overlay.json")
        recovered = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            encounter_join_seconds=1,
            encounter_round_seconds=1,
            raid_join_seconds=1,
            raid_round_seconds=1,
            overlay_state_path=overlay_path,
            rng=random.Random(1806),
        )
        state = recovered.portal_merc_state("100").data["merc_state"]
        self.assertTrue(state["contracts_by_mission"]["hunt"]["deployed"])
        self.assertEqual(state["contracts_by_mission"]["hunt"]["hero_id"], "tifa")
        self.assertFalse(recovered.portal_merc_hire("100", "aerith", "hunt", "rc-recovery-block").ok)

    def test_solo_venture_setup_failure_restores_paid_reservation(self):
        self.assertTrue(self.game.portal_merc_hire("100", "zidane", "venture", "rc-hire-venture").ok)
        before = self.game.portal_merc_state("100").data["merc_state"]["hunt_seals"]
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0), patch.object(self.game, "_solo_select_monster", return_value=None):
            result = self.game.solo_venture("100", bypass_cooldown=True)
        self.assertFalse(result.ok)
        state = self.game.portal_merc_state("100").data["merc_state"]
        venture = state["contracts_by_mission"]["venture"]
        self.assertEqual(venture["hero_id"], "zidane")
        self.assertEqual(venture["state"], "reserved")
        self.assertTrue(venture["cancelable"])
        self.assertEqual(state["hunt_seals"], before)
        self.assertIsNone(self.game._solo_expedition_load("100"))
        history = self.db.all("SELECT outcome FROM merc_contract_history WHERE player_id='100' ORDER BY id DESC LIMIT 2")
        self.assertTrue(any(str(row["outcome"]).startswith("start_failed_restored") for row in history))

    def test_raid_deployment_blocks_rehire_until_raid_resolves(self):
        self.assertTrue(self.game.portal_merc_hire("100", "yuna", "raid", "rc-hire-raid").ok)
        self.assertTrue(self.game.spawn_boss("goblin_king").ok)
        self.assertTrue(self.game.raid_join("100").ok)
        state = self.game.portal_merc_state("100").data["merc_state"]
        self.assertTrue(state["contracts_by_mission"]["raid"]["deployed"])
        self.assertFalse(self.game.portal_merc_hire("100", "balthier", "raid", "rc-double-raid").ok)
        self.assertTrue(self.game.start_raid().ok)
        self.game.active_boss["current_hp"] = 1
        self.game.active_boss["attacks_per_round"] = 0
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        state = self.game.portal_merc_state("100").data["merc_state"]
        self.assertNotIn("raid", state["contracts_by_mission"])


if __name__ == "__main__":
    unittest.main()

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


class MercServiceBatch2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            encounter_join_seconds=1,
            encounter_round_seconds=1,
            raid_join_seconds=1,
            raid_round_seconds=1,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(1802),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)
        self.db.execute("UPDATE players SET level=60,hunt_marks=100 WHERE twitch_id='100'")
        self.db.execute(
            "INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100','chieftains_challenge',20)"
        )

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_rally_venture_claims_cloud_only_when_combat_starts_and_reports_assist(self):
        self.assertTrue(self.game.portal_merc_hire("100", "cloud", "venture", "cloud-v").ok)
        started = self.game.venture("100", bypass_cooldown=True)
        self.assertTrue(started.ok, started.messages)
        self.assertIsNotNone(self.game.portal_merc_state("100").data["merc_state"]["contract"])
        battle = self.game.start_encounter_battle()
        self.assertTrue(battle.ok, battle.messages)
        self.assertIsNone(self.game.portal_merc_state("100").data["merc_state"]["contract"])
        self.assertEqual(self.game.encounter_roster["100"]["merc_contract"]["hero_id"], "cloud")
        self.game.active_encounter["monster_hp"] = 1
        result = self.game.advance_encounter_round()
        self.assertTrue(result.ok, result.messages)
        self.assertTrue(result.data.get("won"))
        personal = " ".join(result.data.get("participant_result_messages") or [])
        self.assertIn("Merc Cloud Strife", personal)
        self.assertIn("Braver", personal)

    def test_timed_hunt_tifa_burst_is_persisted_in_hunt_result(self):
        self.assertTrue(self.game.portal_merc_hire("100", "tifa", "hunt", "tifa-h").ok)
        dispatched = self.game.hunt("100", "chieftains_challenge", bypass_cooldown=True)
        self.assertTrue(dispatched.ok, dispatched.messages)
        assignment = self.game.active_hunts["100"]
        self.assertEqual(assignment["roster"]["100"]["merc_contract"]["hero_id"], "tifa")
        assignment["encounter"]["monster_hp"] = 1
        result = self.game.resolve_hunt("100", force=True)
        self.assertTrue(result.ok, result.messages)
        summary = self.game._last_battle_history["hunt_results"]["100"]
        self.assertEqual(summary["merc"]["hero_id"], "tifa")
        self.assertGreater(summary["merc"]["damage"], 0)
        self.assertTrue(any("Beat Rush" in row for row in summary["merc"]["events"]))

    def test_solo_venture_zidane_secures_one_extra_find(self):
        self.assertTrue(self.game.portal_merc_hire("100", "zidane", "venture", "zidane-v").ok)
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0):
            opened = self.game.solo_venture("100", bypass_cooldown=True)
        self.assertTrue(opened.ok, opened.messages)
        state = self.game._solo_expedition_load("100")
        self.assertEqual(state["merc_contract"]["hero_id"], "zidane")
        combat = state["combat"]
        # Use a known monster with a material drop so Treasure Hunter is deterministic.
        combat["encounter"]["monster_id"] = "goblin_chieftain"
        combat["encounter"]["monster_hp"] = 1
        combat["encounter"]["monster_max_hp"] = max(1, int(combat["encounter"].get("monster_max_hp", 1)))
        state["combat"] = combat
        self.game._solo_expedition_save("100", state)
        acted = self.game.solo_expedition_action("100", "attack")
        self.assertTrue(acted.ok, acted.messages)
        state = self.game._solo_expedition_load("100")
        last_stage = state["last_stage"]
        self.assertEqual(last_stage["merc"]["hero_id"], "zidane")
        self.assertTrue(last_stage["merc"]["bonus_loot"])
        self.assertTrue(any("Treasure Hunter" in row for row in last_stage["merc"]["events"]))
        self.assertTrue(any(row.get("kind") == "merc_bonus" for row in last_stage["rewards"]["items"]))

    def test_aerith_healing_wind_heals_and_applies_regen(self):
        self.assertTrue(self.game.portal_merc_hire("100", "aerith", "venture", "aerith-v").ok)
        self.assertTrue(self.game.venture("100", bypass_cooldown=True).ok)
        self.assertTrue(self.game.start_encounter_battle().ok)
        meta = self.game.encounter_roster["100"]
        meta["hp"] = max(1, int(meta["max_hp"] * 0.40))
        before = int(meta["hp"])
        self.game.active_encounter["monster_hp"] = max(999999, int(self.game.active_encounter["monster_hp"]))
        result = self.game.advance_encounter_round()
        self.assertTrue(result.ok, result.messages)
        meta = self.game.encounter_roster["100"]
        self.assertGreater(int(meta["healing"]), 0)
        self.assertTrue(any("Healing Wind" in row for row in meta["merc_result"]["events"]))
        self.assertTrue("regen" in meta.get("statuses", {}) or int(meta["merc_result"]["healing"]) > 0)
        self.assertGreaterEqual(int(meta["hp"]), 0)
        self.assertGreater(int(meta["merc_result"]["healing"]), 0)
        self.assertGreater(before, 0)

    def test_yuna_guardians_grace_protects_raid_participant(self):
        self.assertTrue(self.game.portal_merc_hire("100", "yuna", "raid", "yuna-r").ok)
        self.assertTrue(self.game.spawn_boss("goblin_king").ok)
        joined = self.game.raid_join("100")
        self.assertTrue(joined.ok, joined.messages)
        self.assertTrue(self.game.start_raid().ok)
        meta = self.game.raid_roster["100"]
        meta["hp"] = max(1, int(meta["max_hp"] * 0.45))
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999
        self.game.active_boss["attacks_per_round"] = 0
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        meta = self.game.raid_roster["100"]
        self.assertTrue(any("Guardian's Grace" in row for row in meta["merc_result"]["events"]))
        self.assertGreater(int(meta["merc_result"]["healing"]), 0)
        self.assertGreater(int(meta["merc_result"]["mitigation"]), 0)

    def test_balthier_raid_result_names_merc_and_rare_spoil(self):
        self.assertTrue(self.game.portal_merc_hire("100", "balthier", "raid", "balthier-r").ok)
        self.assertTrue(self.game.spawn_boss("goblin_king").ok)
        self.assertTrue(self.game.raid_join("100").ok)
        self.assertTrue(self.game.start_raid().ok)
        self.game.active_boss["current_hp"] = 1
        # Force the rare-spoil roll (and normal drop rolls) to succeed for a deterministic test.
        original_random = self.game.rng.random
        self.game.rng.random = lambda: 0.0
        try:
            result = self.game.raid_round()
        finally:
            self.game.rng.random = original_random
        self.assertTrue(result.ok, result.messages)
        self.assertTrue(result.data.get("won"))
        personal = " ".join(result.data.get("participant_result_messages") or [])
        self.assertIn("Merc Balthier", personal)
        self.assertIn("Leading Man", personal)
        self.assertIn("Loot:", personal)


if __name__ == "__main__":
    unittest.main()

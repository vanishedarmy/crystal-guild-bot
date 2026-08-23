from __future__ import annotations

import random
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.balance import (
    active_hunt_hp,
    active_hunt_pressure,
    active_hunt_round_limit,
)
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.encounter_daemon import EncounterDaemon
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class ActiveHuntTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "active-hunts.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            venture_cooldown_seconds=0, venture_treasure_chance=0.0,
            encounter_join_seconds=5,
            encounter_round_seconds=5,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(33),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='1'")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def start_hunt(self, name: str = "red hot problem"):
        result = self.game.hunt("1", name, bypass_cooldown=True)
        self.assertTrue(result.ok, result.messages)
        self.assertTrue(result.data.get("hunt_started"))
        return result

    def test_hunt_enters_shared_active_battle_without_legacy_resolver(self):
        self.assertFalse(hasattr(self.game, "_battle"))
        started = self.start_hunt()
        self.assertEqual(self.game.active_encounter["kind"], "hunt")
        self.assertEqual(self.game.active_encounter["state"], "combat")
        self.assertEqual(self.game.active_encounter["hunt_id"], "red_hot_problem")
        self.assertEqual(set(self.game.encounter_roster), {"1"})
        self.assertEqual(started.data["encounter_id"], self.game.active_encounter["id"])

    def test_hunt_rewards_are_deferred_until_active_battle_victory(self):
        started = self.start_hunt()
        self.assertIsNone(
            self.db.one(
                "SELECT clears FROM player_hunts WHERE player_id='1' AND hunt_id='red_hot_problem'"
            )
        )
        self.game.active_encounter["monster_hp"] = 1
        self.assertTrue(self.game.battle_attack("1").ok)
        result = self.game.advance_encounter_round(started.data["encounter_id"])
        self.assertTrue(result.data.get("hunt_finished"))
        self.assertTrue(result.data.get("won"))
        row = self.db.one(
            "SELECT clears FROM player_hunts WHERE player_id='1' AND hunt_id='red_hot_problem'"
        )
        self.assertEqual(row["clears"], 1)

    def test_hunt_is_solo_and_cannot_be_joined(self):
        self.start_hunt()
        self.game.recruit("2", "aeris", "Aeris")
        self.game.choose_job("2", "whitemage")
        joined = self.game.join_encounter("2", bypass_cooldown=True)
        self.assertFalse(joined.ok)
        self.assertIn("solo", joined.messages[0].lower())
        self.assertEqual(set(self.game.encounter_roster), {"1"})

    def test_hunt_status_identifies_rank_mark_and_active_mode(self):
        self.start_hunt()
        status = self.game.encounter_status()
        text = " ".join(status.messages)
        self.assertIn("ACTIVE HUNT [C]", text)
        self.assertIn("Red Hot Problem", text)
        self.assertIn("Crimson Detonator", text)

    def test_hunt_cooldown_begins_at_acceptance(self):
        self.start_hunt()
        remaining = self.game._cooldown_remaining("1", "hunt:red_hot_problem")
        self.assertGreater(remaining, 0)

    def test_hunt_round_deadline_rejects_late_chat_without_advancing(self):
        self.start_hunt()
        before_round = self.game.active_encounter["round"]
        before_hp = self.game.active_encounter["monster_hp"]
        self.game.active_encounter["next_round_at"] = time.time() - 0.01
        result = self.game.battle_attack("1")
        self.assertFalse(result.ok)
        self.assertIn("timer has closed", result.messages[0])
        self.assertEqual(self.game.active_encounter["round"], before_round)
        self.assertEqual(self.game.active_encounter["monster_hp"], before_hp)

    def test_daemon_advances_active_hunt_without_followup_chat(self):
        started = self.start_hunt()
        self.game.active_encounter["monster_hp"] = 1
        self.game.active_encounter["next_round_at"] = time.time() - 0.01
        announcements = []
        daemon = EncounterDaemon(self.game, announcements.append, poll_interval=0.05)
        acted = daemon._tick_encounter(self.game.combat_snapshot(), time.time())
        self.assertTrue(acted)
        self.assertIsNone(self.game.active_encounter)
        self.assertTrue(announcements)
        self.assertTrue(announcements[-1].data.get("hunt_finished"))
        self.assertEqual(daemon.last_resolved_id, started.data["encounter_id"])

    def test_rank_scaling_is_conservative_and_monotonic(self):
        hp_values = [active_hunt_hp(1000, rank) for rank in ("C", "B", "A", "S")]
        pressure = [active_hunt_pressure(rank) for rank in ("C", "B", "A", "S")]
        rounds = [active_hunt_round_limit(rank) for rank in ("C", "B", "A", "S")]
        self.assertEqual(hp_values, sorted(hp_values))
        self.assertEqual(pressure, sorted(pressure))
        self.assertEqual(rounds, sorted(rounds))
        self.assertEqual(hp_values[0], 1000)
        self.assertLessEqual(hp_values[-1], 1300)
        self.assertLessEqual(pressure[-1], 1.15)

    def test_active_hunt_records_hunt_combat_metrics(self):
        started = self.start_hunt()
        self.game.active_encounter["monster_hp"] = 1
        self.game.battle_attack("1")
        self.game.advance_encounter_round(started.data["encounter_id"])
        row = self.db.one(
            "SELECT value FROM player_record_stats WHERE player_id='1' AND metric='hunt_wins'"
        )
        self.assertIsNotNone(row)
        self.assertGreaterEqual(row["value"], 1)

    def test_twitch_hunt_adapter_wakes_scheduler_without_resolving_chat_side(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        self.assertIn('result.data.get("hunt_started")', source)
        self.assertIn("encounter_daemon.wake()", source)
        # The thin adapter should never call the authoritative round resolver.
        hunt_block = source[source.index("async def hunt"):source.index("async def quests")]
        self.assertNotIn("advance_encounter_round", hunt_block)

    def test_solo_venture_encounter_waits_for_portal_action_without_taking_global_battle_slot(self):
        self.db.execute("UPDATE players SET level=20 WHERE twitch_id='1'")
        refreshed = self.game._player("1")
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='1'", (self.game._max_hp(refreshed),))
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0):
            result = self.game.portal_solo_venture("1", "solo_wayfarer")
        self.assertTrue(result.ok)
        expedition = result.data["adventure_state"]["solo_venture"]["expedition"]
        self.assertEqual(expedition["status"], "combat")
        self.assertIn("intent", expedition["combat"]["enemy"])
        self.assertEqual(expedition["combat"]["round"], 1)
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})
        self.assertIsNotNone(self.db.one("SELECT state_json FROM solo_expeditions WHERE player_id='1'"))




if __name__ == "__main__":
    unittest.main()

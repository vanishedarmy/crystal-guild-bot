from __future__ import annotations

import json
import random
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.balance import active_hunt_hp, active_hunt_pressure, active_hunt_round_limit
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.encounter_daemon import EncounterDaemon
from crystal_guild.engine import CrystalGuildEngine, HUNT_AUTO_ITEM_CAP, HUNT_DURATION_SECONDS

ROOT = Path(__file__).resolve().parents[1]


class ActiveHuntTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "active-hunts.db"
        self.db = Database(self.db_path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            venture_cooldown_seconds=0,
            venture_treasure_chance=0.0,
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

    def test_rank_duration_contract(self):
        self.assertEqual(HUNT_DURATION_SECONDS, {
            "C": 5 * 60,
            "B": 15 * 60,
            "A": 30 * 60,
            "S": 60 * 60,
            "S+": 2 * 60 * 60,
        })
        for rank, seconds in HUNT_DURATION_SECONDS.items():
            self.assertEqual(self.game._hunt_duration_seconds(rank), seconds)

    def test_hunt_is_personal_timed_assignment_not_shared_active_battle(self):
        started = self.start_hunt()
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})
        assignment = self.game.active_hunts["1"]
        self.assertEqual(assignment["hunt_id"], "red_hot_problem")
        self.assertEqual(assignment["rank"], "C")
        self.assertEqual(started.data["duration_seconds"], 300)
        self.assertGreaterEqual(int(assignment["resolves_at"]), int(assignment["started_at"]) + 300)
        self.assertIn("No chat combat is required", " ".join(started.messages))

    def test_hunt_rewards_are_deferred_until_timer_resolution(self):
        started = self.start_hunt()
        self.assertIsNone(self.db.one("SELECT clears FROM player_hunts WHERE player_id='1' AND hunt_id='red_hot_problem'"))
        early = self.game.resolve_hunt("1", started.data["hunt_run_id"])
        self.assertFalse(early.ok)
        self.assertIn("returns in", early.messages[0])
        self.assertIsNone(self.db.one("SELECT clears FROM player_hunts WHERE player_id='1' AND hunt_id='red_hot_problem'"))
        result = self.game.resolve_hunt("1", started.data["hunt_run_id"], force=True)
        self.assertTrue(result.ok, result.messages)
        self.assertTrue(result.data.get("hunt_finished"))
        self.assertTrue(result.data.get("timed_hunt"))
        self.assertIsNotNone(self.db.one("SELECT clears FROM player_hunts WHERE player_id='1' AND hunt_id='red_hot_problem'"))
        self.assertNotIn("1", self.game.active_hunts)

    def test_daemon_waits_until_deadline_then_resolves_once(self):
        started = self.start_hunt()
        announcements = []
        daemon = EncounterDaemon(self.game, announcements.append, poll_interval=0.05)
        assignment = self.game.active_hunts["1"]
        before_due = float(assignment["resolves_at"]) - 1
        self.assertFalse(daemon._tick_hunts(self.game.combat_snapshot(), before_due))
        self.assertIn("1", self.game.active_hunts)
        self.assertEqual(announcements, [])

        assignment["resolves_at"] = time.time() - 0.01
        acted = daemon._tick_hunts(self.game.combat_snapshot(), time.time())
        self.assertTrue(acted)
        self.assertNotIn("1", self.game.active_hunts)
        self.assertEqual(len(announcements), 1)
        self.assertTrue(announcements[0].data.get("hunt_finished"))
        self.assertTrue(announcements[0].data.get("timed_hunt"))
        self.assertEqual(daemon.last_resolved_id, started.data["hunt_run_id"])

    def test_timed_hunt_deadline_is_exposed_to_daemon(self):
        started = self.start_hunt()
        snapshot = self.game.combat_snapshot()
        self.assertEqual(len(snapshot["hunts"]), 1)
        row = snapshot["hunts"][0]
        self.assertEqual(row["player_id"], "1")
        self.assertEqual(row["id"], started.data["hunt_run_id"])
        deadlines = EncounterDaemon._deadlines(snapshot)
        self.assertTrue(any(label.startswith("hunt:1:") for label, _ in deadlines))

    def test_player_can_only_have_one_hunt_and_is_activity_locked(self):
        self.start_hunt()
        second = self.game.hunt("1", "prince of the tide", bypass_cooldown=True)
        self.assertFalse(second.ok)
        self.assertIn("already have a Hunt", second.messages[0])
        switched = self.game.choose_job("1", "monk")
        self.assertFalse(switched.ok)
        self.assertIn("locked", switched.messages[0].lower())

    def test_concurrent_personal_hunts_do_not_occupy_global_battle_slot(self):
        self.start_hunt()
        self.game.recruit("2", "aeris", "Aeris")
        self.game.choose_job("2", "warrior")
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='2'")
        second = self.game.hunt("2", "red hot problem", bypass_cooldown=True)
        self.assertTrue(second.ok, second.messages)
        self.assertEqual(set(self.game.active_hunts), {"1", "2"})
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})

    def test_hunt_cooldown_begins_at_acceptance_and_covers_assignment(self):
        started = self.start_hunt()
        remaining = self.game._cooldown_remaining("1", "hunt:red_hot_problem")
        self.assertGreaterEqual(remaining, started.data["duration_seconds"] - 2)

    def test_auto_items_are_hard_capped_by_rank(self):
        self.game._change_item("1", "potion", 5, "test")
        started = self.start_hunt()
        meta = self.game.active_hunts["1"]["roster"]["1"]
        meta["hp"] = max(1, int(meta["max_hp"] * 0.2))
        meta["items_used"] = 0
        action = self.game._hunt_survival_item_action("1", meta, "C")
        self.assertIsNotNone(action)
        self.assertEqual(action["kind"], "item")
        meta["items_used"] = HUNT_AUTO_ITEM_CAP["C"]
        self.assertIsNone(self.game._hunt_survival_item_action("1", meta, "C"))

    def test_auto_plan_prefers_urgent_survival_without_spamming_rare_items(self):
        self.game._change_item("1", "potion", 3, "test")
        self.game._change_item("1", "elixir", 1, "test")
        self.start_hunt()
        assignment = self.game.active_hunts["1"]
        old_encounter, old_roster = self.game.active_encounter, self.game.encounter_roster
        try:
            self.game.active_encounter = assignment["encounter"]
            self.game.encounter_roster = assignment["roster"]
            meta = self.game.encounter_roster["1"]
            meta["hp"] = max(1, int(meta["max_hp"] * 0.2))
            action = self.game._hunt_auto_action("1", meta, self.data.monsters[assignment["monster_id"]], "C")
            self.assertIn(action["kind"], {"ability", "item", "defend"})
            if action["kind"] == "item":
                self.assertNotEqual(action["item_id"], "elixir")
        finally:
            self.game.active_encounter, self.game.encounter_roster = old_encounter, old_roster

    def test_hunt_state_is_persisted_in_runtime_checkpoint(self):
        started = self.start_hunt()
        row = self.db.one("SELECT value_json FROM runtime_state WHERE state_key='combat'")
        self.assertIsNotNone(row)
        payload = json.loads(row["value_json"])
        self.assertIn("1", payload.get("active_hunts", {}))
        self.assertEqual(payload["active_hunts"]["1"]["id"], started.data["hunt_run_id"])

    def test_rank_scaling_is_conservative_and_monotonic(self):
        hp_values = [active_hunt_hp(1000, rank) for rank in ("C", "B", "A", "S", "S+")]
        pressure = [active_hunt_pressure(rank) for rank in ("C", "B", "A", "S", "S+")]
        rounds = [active_hunt_round_limit(rank) for rank in ("C", "B", "A", "S", "S+")]
        self.assertEqual(hp_values, sorted(hp_values))
        self.assertEqual(pressure, sorted(pressure))
        self.assertEqual(rounds, sorted(rounds))
        self.assertEqual(hp_values[0], 1000)
        self.assertEqual(hp_values[-1], 1300)
        self.assertEqual(pressure[-1], 1.15)

    def test_timed_hunt_records_hunt_combat_metrics(self):
        started = self.start_hunt()
        result = self.game.resolve_hunt("1", started.data["hunt_run_id"], force=True)
        self.assertTrue(result.ok, result.messages)
        row = self.db.one("SELECT value FROM player_record_stats WHERE player_id='1' AND metric='hunt_wins'")
        self.assertIsNotNone(row)
        self.assertGreaterEqual(row["value"], 1)

    def test_timed_hunt_exposes_structured_recent_result_for_portal(self):
        started = self.start_hunt()
        result = self.game.resolve_hunt("1", started.data["hunt_run_id"], force=True)
        self.assertTrue(result.ok, result.messages)
        state = self.game.portal_adventure_state("1")
        self.assertTrue(state.ok, state.messages)
        recent = state.data["adventure_state"]["recent_result"]
        self.assertEqual(recent["kind"], "hunt")
        summary = recent["summary"]
        self.assertEqual(summary["type"], "hunt")
        self.assertIn(summary["outcome"], {"victory", "defeat"})
        self.assertEqual(summary["hunt_name"], "Red Hot Problem")
        self.assertIn("combat", summary)
        self.assertIn("player", summary)
        self.assertIn("auto_plan", summary)

    def test_twitch_hunt_adapter_only_wakes_scheduler(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        self.assertIn('result.data.get("hunt_started")', source)
        self.assertIn("encounter_daemon.wake()", source)
        hunt_block = source[source.index("async def hunt"):source.index("async def quests")]
        self.assertNotIn("advance_encounter_round", hunt_block)
        self.assertNotIn("resolve_hunt", hunt_block)

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

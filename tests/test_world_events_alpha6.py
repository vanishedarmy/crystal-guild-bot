from __future__ import annotations

import random
import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.encounter_daemon import EncounterDaemon
from crystal_guild.world_events import WORLD_EVENTS, WORLD_EVENT_LEVEL_CAP_ABOVE_HIGHEST

ROOT = Path(__file__).resolve().parents[1]


class WorldEventsAlpha6Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "world-events.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=600,
            encounter_join_seconds=60,
            encounter_round_seconds=60,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(1906),
        )
        for pid, login, name, job, level in (
            ("1", "van", "Van", "warrior", 42),
            ("2", "mira", "Mira", "whitemage", 57),
        ):
            self.assertTrue(self.game.recruit(pid, login, name).ok)
            self.assertTrue(self.game.choose_job(pid, job).ok)
            self.db.execute("UPDATE players SET level=? WHERE twitch_id=?", (level, pid))
            self.game.choose_job(pid, job)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def spawn(self):
        result = self.game.maybe_spawn_world_event(stream_live=True, now=time.time(), force=True)
        self.assertTrue(result.ok, result.messages)
        self.assertTrue(result.data.get("world_event_spawned"))
        return result

    def test_catalog_has_ten_distinct_notorious_variants(self):
        catalog = self.game.world_event_catalog()
        self.assertEqual(len(catalog), 10)
        self.assertEqual(len({row["id"] for row in catalog}), 10)
        self.assertTrue(all(row["art"].startswith("/world-events/a1/") for row in catalog))
        self.assertEqual(len(WORLD_EVENTS), 10)

    def test_spawn_is_stream_gated_and_never_exceeds_highest_plus_ten(self):
        offline = self.game.maybe_spawn_world_event(stream_live=False, now=time.time(), force=True)
        self.assertFalse(offline.data.get("world_event_spawned"))
        result = self.spawn()
        monster = self.game._encounter_monster(self.game.active_encounter)
        self.assertEqual(self.game.active_encounter["kind"], "world_event")
        self.assertLessEqual(monster["level"], 57 + WORLD_EVENT_LEVEL_CAP_ABOVE_HIGHEST)
        self.assertGreater(monster["level"], 57)
        self.assertFalse(self.game.active_boss)

    def test_world_event_rally_starts_empty_and_ignores_venture_cooldown(self):
        result = self.spawn()
        self.assertEqual(self.game.encounter_roster, {})
        self.game._set_cooldown("1", "venture", 3600)
        joined = self.game.portal_live_event_join("1", "world_event", str(result.data["encounter_id"]), "we-join-1", stream_live=True)
        self.assertTrue(joined.ok, joined.messages)
        row = self.db.one("SELECT ventures,party_encounters FROM players WHERE twitch_id='1'")
        self.assertEqual(row["ventures"], 0)
        self.assertEqual(row["party_encounters"], 1)

    def test_world_event_portal_state_and_controls_use_world_event_identity(self):
        result = self.spawn()
        eid = str(result.data["encounter_id"])
        self.assertTrue(self.game.portal_live_event_join("1", "world_event", eid, "we-join-2", stream_live=True).ok)
        before = self.game._portal_adventure_state_data("1", stream_live=True)
        self.assertTrue(before["world_events"]["active"])
        self.assertNotIn("catalog", before["world_events"])
        self.assertEqual(before["world_events"]["max_level_above_highest"], WORLD_EVENT_LEVEL_CAP_ABOVE_HIGHEST)
        self.assertEqual(before["encounter"]["kind"], "world_event")
        self.assertTrue(before["encounter"]["world_event"]["art"].startswith("/world-events/a1/"))
        self.assertTrue(self.game.start_encounter_battle(int(eid)).ok)
        combat = self.game._portal_adventure_state_data("1", stream_live=True)["encounter"]
        self.assertTrue(combat["web_combat_controls"])
        self.assertEqual(combat["controls"]["event"], "world_event")
        queued = self.game.portal_live_event_action("1", "world_event", eid, 1, "defend", "", "", "we-action-1", stream_live=True)
        self.assertTrue(queued.ok, queued.messages)
        self.assertEqual(self.game.encounter_roster["1"]["action"]["kind"], "defend")


    def test_high_level_guild_can_spawn_above_level_99_but_never_above_plus_ten(self):
        self.db.execute("UPDATE players SET level=99 WHERE twitch_id='2'")
        result = self.spawn()
        monster = self.game._encounter_monster(self.game.active_encounter)
        self.assertGreater(monster["level"], 99)
        self.assertLessEqual(monster["level"], 109)

    def test_world_event_encounter_status_uses_realm_label_and_variant_name(self):
        result = self.spawn()
        status = self.game.encounter_status()
        self.assertTrue(status.ok, status.messages)
        joined = " ".join(status.messages)
        self.assertIn("@ The Realm", joined)
        event_name = self.game._encounter_monster(self.game.active_encounter)["name"]
        self.assertIn(event_name, joined)
        self.assertTrue(self.game.portal_live_event_join("1", "world_event", str(result.data["encounter_id"]), "we-status-join", stream_live=True).ok)
        self.assertTrue(self.game.start_encounter_battle(int(result.data["encounter_id"])).ok)
        combat_status = " ".join(self.game.encounter_status().messages)
        self.assertIn("WORLD EVENT", combat_status)
        self.assertIn(event_name, combat_status)

    def test_spawn_schedule_waits_through_initial_grace_without_force(self):
        now = 2_000_000_000.0
        first = self.game.maybe_spawn_world_event(stream_live=True, now=now, force=False)
        self.assertFalse(first.data.get("world_event_spawned"))
        self.assertGreater(int(first.data.get("next_check_at") or 0), int(now))
        second = self.game.maybe_spawn_world_event(stream_live=True, now=now + 10, force=False)
        self.assertFalse(second.data.get("world_event_spawned"))
        self.assertEqual(int(second.data.get("next_check_at") or 0), int(first.data.get("next_check_at") or 0))


    def test_daemon_world_event_scan_respects_live_lookup_and_publishes_spawn(self):
        notices = []
        daemon = EncounterDaemon(self.game, notices.append, stream_live_lookup=lambda: True)
        original = self.game.maybe_spawn_world_event
        self.game.maybe_spawn_world_event = lambda **kwargs: original(force=True, **kwargs)
        try:
            acted = daemon._tick_world_event_spawn(time.time())
        finally:
            self.game.maybe_spawn_world_event = original
        self.assertTrue(acted)
        self.assertEqual(len(notices), 1)
        self.assertTrue(notices[0].data.get("world_event_spawned"))

    def test_world_event_cannot_spawn_over_an_existing_battle(self):
        self.assertTrue(self.game.venture("1", bypass_cooldown=True).ok)
        blocked = self.game.maybe_spawn_world_event(stream_live=True, now=time.time(), force=True)
        self.assertFalse(blocked.data.get("world_event_spawned"))
        self.assertEqual(self.game.active_encounter["kind"], "venture")

    def test_unanswered_world_event_closes_without_starting_a_raid(self):
        result = self.spawn()
        eid = int(result.data["encounter_id"])
        ended = self.game.start_encounter_battle(eid)
        self.assertTrue(ended.ok, ended.messages)
        self.assertTrue(ended.data.get("encounter_finished"))
        self.assertIsNone(self.game.active_encounter)
        self.assertIsNone(self.game.active_boss)
        schedule = self.game._world_event_schedule()
        self.assertGreater(int(schedule.get("cooldown_until") or 0), 0)


if __name__ == "__main__":
    unittest.main()

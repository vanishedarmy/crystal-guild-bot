"""v2.1.0 regression: overdue timers, independent scheduler deadlines and Portal recovery."""
from __future__ import annotations

import random
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.encounter_daemon import EncounterDaemon
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import PortalActionWorker, ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class ResolutionRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"), rng=random.Random(20),
            venture_cooldown_seconds=0, encounter_join_seconds=5,
            encounter_round_seconds=5, overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
        )
        self.worker = PortalActionWorker(self.game, "https://guild.example", "key")
        for pid in ("100", "200"):
            self.game.recruit(pid, f"hero{pid}", f"Hero{pid}")
            self.game.choose_job(pid, "warrior")
            self.db.execute("UPDATE players SET level=30 WHERE twitch_id=?", (pid,))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def assignment(self, pid="100"):
        started = self.game.hunt(pid, "red_hot_problem", bypass_cooldown=True)
        self.assertTrue(started.ok, started.messages)
        return self.game.active_hunts[pid]

    def portal(self, kind, payload, id, pid="100"):
        return self.worker._execute({
            "id": id, "type": kind, "payload": payload,
            "twitch_id": pid, "username": f"hero{pid}",
            "protocol_version": ACTION_PROTOCOL_VERSION,
        })

    def test_manual_resolution_never_bypasses_deadline_or_wrong_run(self):
        hunt = self.assignment()
        run_id = hunt["id"]
        early = self.portal("RESOLVE_HUNT", {"hunt_run_id": run_id}, "pa_early")
        self.assertFalse(early[0]); self.assertIn("returns in", early[1]); self.assertIn("100", self.game.active_hunts)
        wrong = self.portal("RESOLVE_HUNT", {"hunt_run_id": run_id + 42}, "pa_wrong")
        self.assertFalse(wrong[0]); self.assertIn("replaced", wrong[1]); self.assertIn("100", self.game.active_hunts)
        self.game.active_hunts["100"]["resolves_at"] = time.time() - 1
        accepted = self.portal("RESOLVE_HUNT", {"hunt_run_id": run_id}, "pa_completed")
        self.assertTrue(accepted[0], accepted[1]); self.assertNotIn("100", self.game.active_hunts)
        self.assertTrue(accepted[2].get("hunt_finished"))
        self.assertTrue(accepted[2].get("adventure_state"))
        replay = self.portal("RESOLVE_HUNT", {"hunt_run_id": run_id}, "pa_completed")
        self.assertEqual(accepted, replay)
        duplicate = self.portal("RESOLVE_HUNT", {"hunt_run_id": run_id}, "pa_new_request")
        self.assertFalse(duplicate[0]); self.assertIn("no longer active", duplicate[1])
        row = self.db.one("SELECT clears FROM player_hunts WHERE player_id=? AND hunt_id=?", ("100", "red_hot_problem"))
        self.assertEqual(int(row["clears"]), 1)

    def test_adventure_state_recovers_overdue_hunt_without_manual_button(self):
        run = self.assignment()
        run["resolves_at"] = time.time() - 1
        ok, _, payload = self.portal("ADVENTURE_STATE", {}, "pa_refresh")
        self.assertTrue(ok)
        self.assertNotIn("100", self.game.active_hunts)
        self.assertIsNone(payload["adventure_state"].get("active_hunt"))
        ok2, _, payload2 = self.portal("ADVENTURE_STATE", {}, "pa_refresh2")
        self.assertTrue(ok2)
        records = [r for r in payload2["adventure_state"].get("pending_results", []) if r.get("kind") == "hunt"]
        self.assertEqual(len(records), 1)
        row = self.db.one("SELECT clears FROM player_hunts WHERE player_id='100' AND hunt_id='red_hot_problem'")
        self.assertEqual(int(row["clears"]), 1)

    def test_failed_hunt_does_not_starve_other_hunts_or_battle_deadline(self):
        run_a = self.assignment("100")
        run_b = self.assignment("200")
        for run in (run_a, run_b):
            run["resolves_at"] = time.time() - 1
        announced = []
        daemon = EncounterDaemon(self.game, announced.append, poll_interval=.05)
        original = self.game.resolve_hunt

        def fail_first(player_id, run_id=None, *, force=False):
            if str(player_id) == "100":
                raise RuntimeError("simulated corrupted Hunt input")
            return original(player_id, run_id, force=force)

        with patch.object(self.game, "resolve_hunt", side_effect=fail_first):
            self.assertTrue(daemon._tick_hunts(self.game.combat_snapshot(), time.time()))
        self.assertIn("100", self.game.active_hunts)
        self.assertNotIn("200", self.game.active_hunts)
        self.assertEqual(len(announced), 1)
        self.assertEqual(daemon.status()["hunt_retries_pending"], 1)
        self.assertGreater(daemon._wait_timeout(self.game.combat_snapshot()), 0.01)
        self.assertFalse(daemon._tick_hunts(self.game.combat_snapshot(), time.time()))
        daemon._hunt_retry_at.clear()
        self.assertTrue(daemon._tick_hunts(self.game.combat_snapshot(), time.time()))
        self.assertNotIn("100", self.game.active_hunts)
        self.assertEqual(daemon.status()["hunt_retries_pending"], 0)
        self.assertEqual(len(announced), 2)

    def test_live_scheduler_continues_hunt_when_passive_recovery_scan_fails(self):
        run = self.assignment("100")
        run["resolves_at"] = time.time() - 1
        posted = []
        daemon = EncounterDaemon(self.game, posted.append, poll_interval=.05)
        with patch.object(self.game, "refresh_due_long_rests", side_effect=RuntimeError("test-only passive scan failure")):
            daemon.start()
            try:
                for _ in range(40):
                    if "100" not in self.game.active_hunts:
                        break
                    time.sleep(.025)
                self.assertTrue(daemon.is_alive)
                self.assertNotIn("100", self.game.active_hunts)
                self.assertEqual(len(posted), 1)
            finally:
                daemon.stop()

    def test_portal_result_recovers_from_database_restart_and_remains_single_award(self):
        hunt = self.assignment()
        run_id = int(hunt["id"])
        # The saved assignment is authoritative after the Bot is recreated.
        self.game._persist_runtime_state()
        self.game = CrystalGuildEngine(self.db, self.game.data, rng=random.Random(30), overlay_state_path=str(Path(self.tmp.name) / "overlay_restart.json"))
        self.worker = PortalActionWorker(self.game, "https://guild.example", "key")
        self.game.active_hunts["100"]["resolves_at"] = time.time() - 1
        first = self.portal("RESOLVE_HUNT", {"hunt_run_id": run_id}, "pa_restart")
        self.assertTrue(first[0], first[1])
        second = self.portal("RESOLVE_HUNT", {"hunt_run_id": run_id}, "pa_restart2")
        self.assertFalse(second[0]); self.assertNotIn("100", self.game.active_hunts)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import random
import tempfile
import threading
import time
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class GuildExpansionBeta3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(1313),
        )
        self.game.recruit("1", "one", "One")
        self.game.recruit("2", "two", "Two")
        self.db.execute("UPDATE players SET gil=50000 WHERE twitch_id IN ('1','2')")
        self.db.execute("UPDATE fellowship_state SET level=10,renown=70000 WHERE singleton_id=1")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_beta3_advances_protocol_only(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 23)
        self.assertEqual(self.db.schema_version(), 24)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 38)

    def test_simultaneous_contributions_never_overfill_or_overcharge(self):
        self.assertTrue(self.game.set_fellowship_project("infirmary").ok)
        barrier = threading.Barrier(3)
        results = []

        def contribute(player_id: str) -> None:
            barrier.wait()
            results.append(self.game.contribute_fellowship(player_id, "gil 5000"))

        threads = [threading.Thread(target=contribute, args=(pid,)) for pid in ("1", "2")]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=5)

        self.assertFalse(any(thread.is_alive() for thread in threads))
        progress = self.db.one(
            "SELECT current FROM fellowship_project_progress WHERE project_id='infirmary_t1' AND requirement_key='gil'"
        )
        self.assertEqual(int(progress["current"]), 5000)
        remaining_gil = sum(int(self.db.one("SELECT gil FROM players WHERE twitch_id=?", (pid,))["gil"]) for pid in ("1", "2"))
        self.assertEqual(remaining_gil, 95000)
        contributed = self.db.one(
            "SELECT COALESCE(SUM(amount),0) AS n FROM fellowship_contributions WHERE project_id='infirmary_t1' AND kind='gil'"
        )
        self.assertEqual(int(contributed["n"]), 5000)
        self.assertEqual(sum(1 for result in results if result.ok), 1)

    def test_same_portal_action_from_two_tabs_mutates_once(self):
        self.assertTrue(self.game.set_fellowship_project("infirmary").ok)
        barrier = threading.Barrier(3)
        results = []

        def submit() -> None:
            barrier.wait()
            results.append(
                self.game.portal_contribute_gil(
                    "1", 2000, "beta3:same-action", expected_project_id="infirmary_t1"
                )
            )

        threads = [threading.Thread(target=submit) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=5)

        self.assertTrue(all(result.ok for result in results))
        self.assertEqual(results[0].data, results[1].data)
        self.assertEqual(int(self.game._player("1")["gil"]), 48000)
        progress = self.db.one(
            "SELECT current FROM fellowship_project_progress WHERE project_id='infirmary_t1' AND requirement_key='gil'"
        )
        self.assertEqual(int(progress["current"]), 2000)
        count = self.db.one(
            "SELECT COUNT(*) AS n FROM fellowship_contributions WHERE player_id='1' AND project_id='infirmary_t1' AND kind='gil'"
        )
        self.assertEqual(int(count["n"]), 1)

    def test_stale_portal_project_version_cannot_donate_to_new_project(self):
        self.assertTrue(self.game.set_fellowship_project("infirmary").ok)
        old_id = self.game.fellowship_system.project_snapshot()["id"]
        self.assertTrue(self.game.set_fellowship_project("workshop").ok)
        before = int(self.game._player("1")["gil"])

        result = self.game.portal_contribute_gil(
            "1", 1000, "beta3:stale-project", expected_project_id=old_id
        )
        self.assertFalse(result.ok)
        self.assertIn("project changed", result.messages[0].lower())
        self.assertEqual(int(self.game._player("1")["gil"]), before)
        state = self.db.one("SELECT active_project_id FROM fellowship_state WHERE singleton_id=1")
        self.assertEqual(str(state["active_project_id"]), "workshop_t1")

    def test_project_completion_holds_lock_until_upgrade_is_finalized(self):
        self.assertTrue(self.game.set_fellowship_project("infirmary").ok)
        self.db.execute(
            "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES ('infirmary_t1','gil',5000) "
            "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=5000"
        )
        self.db.execute(
            "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES ('infirmary_t1','item:hi_potion',10) "
            "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=10"
        )
        self.db.execute(
            "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES ('infirmary_t1','activity:venture_complete',19) "
            "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=19"
        )

        entered = threading.Event()
        release = threading.Event()
        switched = threading.Event()
        original = self.game.fellowship_system._check_project_completion

        def delayed(triggering_player_id):
            entered.set()
            self.assertTrue(release.wait(3))
            return original(triggering_player_id)

        self.game.fellowship_system._check_project_completion = delayed
        activity_thread = threading.Thread(
            target=lambda: self.game.fellowship_system.record_activity(
                "1", "venture_complete", event_key="beta3:final-venture"
            )
        )
        switch_thread = threading.Thread(
            target=lambda: (self.game.set_fellowship_project("workshop"), switched.set())
        )
        activity_thread.start()
        self.assertTrue(entered.wait(2))
        switch_thread.start()
        time.sleep(0.15)
        self.assertFalse(switched.is_set(), "project switch escaped the completion transaction")
        release.set()
        activity_thread.join(timeout=5)
        switch_thread.join(timeout=5)
        self.game.fellowship_system._check_project_completion = original

        tier = self.db.one("SELECT tier FROM fellowship_facilities WHERE facility_id='infirmary'")
        self.assertEqual(int(tier["tier"]), 1)
        state = self.db.one("SELECT active_project_id FROM fellowship_state WHERE singleton_id=1")
        self.assertEqual(str(state["active_project_id"]), "workshop_t1")

    def test_concurrent_airship_launches_create_only_one_run(self):
        self.db.execute("UPDATE fellowship_airship_state SET built=1 WHERE singleton_id=1")
        barrier = threading.Barrier(3)
        results = []

        def launch(name: str) -> None:
            barrier.wait()
            results.append((name, self.game.fellowship_system.start_airship_mission(name)))

        threads = [
            threading.Thread(target=launch, args=("merchant escort",)),
            threading.Thread(target=launch, args=("monster suppression",)),
        ]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=5)

        successes = [(name, result) for name, result in results if result[0]]
        failures = [(name, result) for name, result in results if not result[0]]
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        state = self.db.one(
            "SELECT active_mission_id,active_run_id FROM fellowship_airship_state WHERE singleton_id=1"
        )
        self.assertTrue(state["active_mission_id"])
        self.assertTrue(state["active_run_id"])
        self.assertEqual(
            int(self.db.one("SELECT COUNT(*) AS n FROM fellowship_activity WHERE kind='airship_mission_started'")["n"]),
            1,
        )

    def test_due_airship_settles_once_after_restart(self):
        self.db.execute("UPDATE fellowship_airship_state SET built=1 WHERE singleton_id=1")
        ok, _, active = self.game.fellowship_system.start_airship_mission("merchant escort")
        self.assertTrue(ok)
        run_id = active["run_id"]
        self.game.fellowship_system.record_activity(
            "1", "venture_complete", amount=50, event_key="beta3:restart-progress"
        )
        self.db.execute(
            "UPDATE fellowship_airship_state SET ends_at=? WHERE singleton_id=1",
            (int(time.time()) - 1,),
        )
        before_gil = int(self.game._player("1")["gil"])

        self.db.close()
        restarted_db = Database(self.path)
        restarted_game = CrystalGuildEngine(
            restarted_db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay-restarted.json"),
            rng=random.Random(1314),
        )
        try:
            snapshot = restarted_game.fellowship_system.airship_snapshot()
            self.assertIsNone(snapshot["active_mission"])
            self.assertEqual(snapshot["missions_completed"], 1)
            after_first = int(restarted_game._player("1")["gil"])
            self.assertGreater(after_first, before_gil)
            restarted_game.fellowship_system.airship_snapshot()
            self.assertEqual(int(restarted_game._player("1")["gil"]), after_first)
            history = restarted_db.one(
                "SELECT outcome FROM fellowship_airship_mission_history WHERE run_id=?", (run_id,)
            )
            self.assertEqual(str(history["outcome"]), "success")
            receipts = restarted_db.one(
                "SELECT COUNT(*) AS n FROM fellowship_events WHERE event_key=?",
                (f"airship_mission_settle:{run_id}",),
            )
            self.assertEqual(int(receipts["n"]), 1)
        finally:
            restarted_db.close()
            # Restore a closed handle so tearDown remains harmless.
            self.db = Database(self.path)


if __name__ == "__main__":
    unittest.main()

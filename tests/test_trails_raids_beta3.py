from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class TrailsRaidsBeta3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(self.db, self.data, raid_join_seconds=90, raid_round_seconds=60, rng=random.Random(1530))
        for pid, name, job in [("1", "Van", "warrior"), ("2", "Mira", "whitemage")]:
            self.game.recruit(pid, name.lower(), name)
            self.game.choose_job(pid, job)
            self.db.execute("UPDATE players SET level=70 WHERE twitch_id=?", (pid,))
            self.game.choose_job(pid, job)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _start(self, boss_id="goblin_king"):
        self.assertTrue(self.game.spawn_boss(boss_id).ok)
        for pid in ("1", "2"):
            self.assertTrue(self.game.raid_join(pid).ok)
        self.assertTrue(self.game.start_raid().ok)
        return self.game.active_boss

    def test_beta3_identity_keeps_schema10_protocol25(self):
        self.assertEqual(__version__, "1.5.1-relic-arsenal-complete")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 10)
        self.assertEqual(self.db.schema_version(), 10)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 25)

    def test_cross_connection_action_queues_merge_instead_of_clobbering(self):
        self._start()
        stale_db = Database(self.path)
        stale = CrystalGuildEngine(stale_db, self.data, rng=random.Random(1531))
        try:
            initial_revision = self.game._runtime_revision
            self.assertTrue(self.game.battle_attack("1").ok)
            self.assertTrue(stale.battle_defend("2").ok)
            # Refresh the first connection from the second connection's commit.
            self.assertTrue(self.game.boss_status().ok)
            self.assertEqual(self.game.raid_roster["1"]["action"]["kind"], "attack")
            self.assertEqual(self.game.raid_roster["2"]["action"]["kind"], "defend")
            self.assertGreater(self.game._runtime_revision, initial_revision)
            self.assertEqual(self.game.raid_roster["1"]["action"]["raid_round"], 1)
            self.assertEqual(self.game.raid_roster["2"]["action"]["raid_round"], 1)
        finally:
            stale_db.close()

    def test_duplicate_timer_snapshot_cannot_advance_two_rounds(self):
        boss = self._start()
        boss["attacks_per_round"] = 0
        self.assertTrue(self.game.battle_attack("1").ok)  # persists the test-safe boss edit
        run_id = boss["raid_instance_id"]
        stale_db = Database(self.path)
        stale = CrystalGuildEngine(stale_db, self.data, rng=random.Random(1532))
        try:
            first = self.game.raid_round(boss["id"], expected_instance_id=run_id, expected_round=0)
            self.assertTrue(first.ok, first.messages)
            replay = stale.raid_round(boss["id"], expected_instance_id=run_id, expected_round=0)
            self.assertTrue(replay.ok, replay.messages)
            self.assertTrue(replay.data.get("stale_raid_tick"))
            self.assertEqual(replay.messages, [])
            self.assertTrue(self.game.boss_status().ok)
            self.assertEqual(self.game.active_boss["round"], 1)
        finally:
            stale_db.close()

    def test_new_raid_actions_are_exact_run_and_round_scoped(self):
        boss = self._start()
        self.assertTrue(self.game.battle_defend("1").ok)
        action = self.game.raid_roster["1"]["action"]
        self.assertEqual(action["raid_round"], 1)
        self.assertEqual(action["raid_run"], boss["raid_instance_id"])
        overlay = json.dumps(self.game._overlay_payload())
        self.assertNotIn("raid_run", overlay)
        self.assertNotIn(boss["raid_instance_id"], overlay)

    def test_legacy_unstamped_beta2_action_is_honored_once(self):
        boss = self._start()
        boss["attacks_per_round"] = 0
        self.game.raid_roster["1"]["action"] = {"kind": "defend"}
        self.game._persist_runtime_state()
        before = int(self.game.raid_roster["1"].get("defends", 0))
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(int(self.game.raid_roster["1"].get("defends", 0)), before + 1)

    def test_internal_combat_snapshot_carries_run_identity_but_public_overlay_does_not(self):
        boss = self._start()
        snapshot = self.game.combat_snapshot()
        self.assertEqual(snapshot["boss"]["raid_instance_id"], boss["raid_instance_id"])
        self.assertNotIn("raid_instance_id", self.game._overlay_payload())


if __name__ == "__main__":
    unittest.main()

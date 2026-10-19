from __future__ import annotations

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


class TrailsRaidsRC1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            raid_join_seconds=90,
            raid_round_seconds=60,
            rng=random.Random(1550),
        )
        for pid, name, job in [("1", "Van", "warrior"), ("2", "Mira", "whitemage")]:
            self.game.recruit(pid, name.lower(), name)
            self.game.choose_job(pid, job)
            self.db.execute("UPDATE players SET level=70 WHERE twitch_id=?", (pid,))
            self.game.choose_job(pid, job)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _start(self):
        self.assertTrue(self.game.spawn_boss("goblin_king").ok)
        for pid in ("1", "2"):
            self.assertTrue(self.game.raid_join(pid).ok)
        self.assertTrue(self.game.start_raid().ok)
        self.game.active_boss["attacks_per_round"] = 0
        return self.game.active_boss

    def test_rc1_identity_keeps_schema10_protocol25(self):
        self.assertEqual(__version__, "1.9.3-guild-initiatives")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 26)
        self.assertEqual(self.db.schema_version(), 26)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 39)

    def test_current_round_actions_are_the_only_actions_counted_ready(self):
        boss = self._start()
        self.assertTrue(self.game.battle_attack("1").ok)
        self.assertTrue(self.game.battle_defend("2").ok)
        self.assertTrue(self.game._all_raid_actions_queued())
        overlay = self.game._overlay_payload()
        self.assertEqual(overlay["ready_actions"], 2)
        self.assertEqual(overlay["actionable_raiders"], 2)
        for meta in self.game.raid_roster.values():
            self.assertEqual(meta["action"]["raid_run"], boss["raid_instance_id"])
            self.assertEqual(meta["action"]["raid_round"], 1)

    def test_stale_prior_round_action_does_not_make_party_ready(self):
        boss = self._start()
        run_id = boss["raid_instance_id"]
        self.game.raid_roster["1"]["action"] = {"kind": "attack", "raid_run": run_id, "raid_round": 0}
        self.game.raid_roster["2"]["action"] = {"kind": "defend", "raid_run": run_id, "raid_round": 1}
        self.assertFalse(self.game._all_raid_actions_queued())
        self.assertEqual(self.game._overlay_payload()["ready_actions"], 1)

    def test_stale_other_run_action_does_not_make_party_ready(self):
        self._start()
        self.game.raid_roster["1"]["action"] = {"kind": "attack", "raid_run": "old-run", "raid_round": 1}
        self.assertTrue(self.game.battle_defend("2").ok)
        self.assertFalse(self.game._all_raid_actions_queued())
        self.assertEqual(self.game._overlay_payload()["ready_actions"], 1)

    def test_malformed_round_stamp_fails_closed_and_resolution_auto_attacks(self):
        boss = self._start()
        self.game.raid_roster["1"]["action"] = {
            "kind": "defend",
            "raid_run": boss["raid_instance_id"],
            "raid_round": "not-a-round",
        }
        self.assertEqual(self.game._overlay_payload()["ready_actions"], 0)
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["round"], 1)
        self.assertEqual(self.game.raid_roster["1"]["defends"], 0)

    def test_legacy_unstamped_upgrade_action_remains_ready_once(self):
        self._start()
        self.game.raid_roster["1"]["action"] = {"kind": "defend"}
        self.game.raid_roster["2"]["action"] = {"kind": "attack"}
        self.assertTrue(self.game._all_raid_actions_queued())
        self.assertEqual(self.game._overlay_payload()["ready_actions"], 2)
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.raid_roster["1"]["defends"], 1)
        self.assertEqual(self.game._overlay_payload()["ready_actions"], 0)


if __name__ == "__main__":
    unittest.main()

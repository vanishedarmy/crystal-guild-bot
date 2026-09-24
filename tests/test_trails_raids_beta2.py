from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class TrailsRaidsBeta2Tests(unittest.TestCase):
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
            rng=random.Random(1520),
        )
        for pid, name, job in [("1", "Van", "warrior"), ("2", "Mira", "whitemage")]:
            self.game.recruit(pid, name.lower(), name)
            self.game.choose_job(pid, job)
            self.db.execute("UPDATE players SET level=70 WHERE twitch_id=?", (pid,))
            self.game.choose_job(pid, job)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _start(self, boss_id="ifrit"):
        self.assertTrue(self.game.spawn_boss(boss_id).ok)
        for pid in ("1", "2"):
            self.assertTrue(self.game.raid_join(pid).ok)
        self.assertTrue(self.game.start_raid().ok)
        return self.game.active_boss

    def test_beta2_identity_keeps_schema10_protocol25(self):
        self.assertEqual(__version__, "1.9.0-trading-post-qol-alpha13")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 25)
        self.assertEqual(self.db.schema_version(), 25)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 39)

    def test_overlay_reports_action_readiness_without_private_ids(self):
        self._start("ifrit")
        self.assertTrue(self.game.battle_attack("1").ok)
        overlay = self.game._overlay_payload()
        self.assertEqual(overlay["ready_actions"], 1)
        self.assertEqual(overlay["actionable_raiders"], 2)
        self.assertNotIn("raid_instance_id", overlay)
        self.assertNotIn("target_id", overlay.get("mechanic") or {})

    def test_repeat_clear_mastery_is_derived_from_existing_clear_ledger(self):
        rows = [("ifrit", 10), ("shiva", 5), ("ramuh", 3), ("titan", 1)]
        for boss_id, clears in rows:
            self.db.execute(
                "INSERT INTO player_boss_clears(player_id,boss_id,clears,best_damage,last_cleared_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",
                ("1", boss_id, clears, clears * 100),
            )
        repo = PortalRepository(self.path, ROOT / "data")
        try:
            records = repo.records("van")
        finally:
            repo.close()
        trial = {row["id"]: row for row in records["trials"]}
        self.assertEqual(trial["ifrit"]["repeat_mastery"], "Mastered")
        self.assertIsNone(trial["ifrit"]["next_clear_goal"])
        self.assertEqual(trial["shiva"]["repeat_mastery"], "Veteran")
        self.assertEqual(trial["shiva"]["next_clear_goal"], 10)
        self.assertEqual(trial["ramuh"]["repeat_mastery"], "Seasoned")
        self.assertEqual(trial["titan"]["repeat_mastery"], "Proven")
        self.assertEqual(records["trial_summary"]["mastered_trials"], 1)

    def test_duplicate_stale_engine_settlement_cannot_double_rewards(self):
        boss = self._start("ifrit")
        boss["round"] = 5
        self.game.raid_roster["1"].update(damage=9000, healing=0, mitigation=500)
        self.game.raid_roster["2"].update(damage=3000, healing=3500, mitigation=200)

        # A second connection restores the same active raid before the first
        # connection commits the victory, reproducing stale process state.
        stale_db = Database(self.path)
        stale = CrystalGuildEngine(stale_db, self.data, rng=random.Random(1521))
        try:
            self.assertEqual(stale.active_boss["raid_instance_id"], boss["raid_instance_id"])
            before_gil = int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"])
            first = self.game._finish_raid(True)
            self.assertTrue(first.ok, first.messages)
            after_first = int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"])
            clears_first = int(self.db.one("SELECT clears FROM player_boss_clears WHERE player_id='1' AND boss_id='ifrit'")["clears"])
            self.assertGreater(after_first, before_gil)
            self.assertEqual(clears_first, 1)

            replay = stale._finish_raid(True)
            self.assertTrue(replay.ok, replay.messages)
            self.assertTrue(replay.data.get("settlement_replay"))
            after_replay = int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"])
            clears_replay = int(self.db.one("SELECT clears FROM player_boss_clears WHERE player_id='1' AND boss_id='ifrit'")["clears"])
            self.assertEqual(after_replay, after_first)
            self.assertEqual(clears_replay, 1)
            self.assertIsNone(stale.active_boss)
        finally:
            stale_db.close()

    def test_legacy_restored_raid_gets_stable_settlement_identity(self):
        boss = self._start("shiva")
        boss.pop("raid_instance_id", None)
        legacy_id = self.game._raid_instance_id(boss)
        self.assertTrue(legacy_id.startswith("legacy-shiva-"))
        self.assertEqual(self.game._raid_instance_id(boss), legacy_id)

    def test_settlement_receipts_are_bounded(self):
        for index in range(70):
            fake = {"id": "ifrit", "round": index + 1, "raid_instance_id": f"run-{index}"}
            self.game._record_raid_settlement_receipt(fake, won=bool(index % 2))
        receipts = self.game._raid_settlement_receipts()
        self.assertEqual(len(receipts), 64)
        self.assertEqual(receipts[0]["raid_instance_id"], "run-6")
        self.assertEqual(receipts[-1]["raid_instance_id"], "run-69")


if __name__ == "__main__":
    unittest.main()

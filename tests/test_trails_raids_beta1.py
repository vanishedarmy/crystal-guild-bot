from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine, raid_contribution_score
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class TrailsRaidsBeta1Tests(unittest.TestCase):
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
            rng=random.Random(1510),
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

    def test_beta1_identity_keeps_schema10_protocol25(self):
        self.assertEqual(__version__, "1.9.0-world-events-alpha6")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 19)
        self.assertEqual(self.db.schema_version(), 19)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 36)

    def test_trial_victory_persists_fastest_and_contribution_bests(self):
        boss = self._start("ifrit")
        boss["round"] = 7
        self.game.raid_roster["1"].update(damage=9200, healing=120, mitigation=800)
        self.game.raid_roster["2"].update(damage=3100, healing=4400, mitigation=500)
        result = self.game._finish_raid(True)
        self.assertTrue(result.ok, result.messages)
        stats = {r["metric"]: int(r["value"]) for r in self.db.all("SELECT metric,value FROM player_record_stats WHERE player_id='1'")}
        self.assertEqual(stats["trial_ifrit_fastest_rounds"], 7)
        self.assertEqual(stats["trial_ifrit_best_damage"], 9200)
        self.assertEqual(stats["trial_ifrit_best_healing"], 120)
        self.assertEqual(stats["trial_ifrit_best_mitigation"], 800)
        self.assertEqual(stats["trial_ifrit_best_score"], int(round(raid_contribution_score(damage=9200, healing=120, mitigation=800))))

    def test_trial_wipe_tracks_without_erasing_fastest_clear(self):
        boss = self._start("shiva")
        boss["round"] = 6
        self.game.raid_roster["1"].update(damage=6000, healing=0, mitigation=300)
        self.assertTrue(self.game._finish_raid(True).ok)
        boss = self._start("shiva")
        boss["round"] = 4
        self.game.raid_roster["1"].update(damage=7000, healing=0, mitigation=200)
        self.assertTrue(self.game._finish_raid(False, reason="Beta record test").ok)
        stats = {r["metric"]: int(r["value"]) for r in self.db.all("SELECT metric,value FROM player_record_stats WHERE player_id='1'")}
        self.assertEqual(stats["trial_shiva_wipes"], 1)
        self.assertEqual(stats["trial_shiva_fastest_rounds"], 6)
        self.assertEqual(stats["trial_shiva_best_damage"], 7000)

    def test_records_merge_legacy_clears_with_beta_metrics(self):
        self.db.execute(
            "INSERT INTO player_boss_clears(player_id,boss_id,clears,best_damage,last_cleared_at) VALUES ('1','ramuh',3,12345,CURRENT_TIMESTAMP)"
        )
        self.db.add_record_stat("1", "trial_ramuh_wipes", 2)
        self.db.max_record_stat("1", "trial_ramuh_best_score", 16000)
        repo = PortalRepository(self.path, ROOT / "data")
        try:
            records = repo.records("van")
        finally:
            repo.close()
        ramuh = next(row for row in records["trials"] if row["id"] == "ramuh")
        self.assertEqual(ramuh["clears"], 3)
        self.assertEqual(ramuh["wipes"], 2)
        self.assertEqual(ramuh["attempts"], 5)
        self.assertEqual(ramuh["best_damage"], 12345)
        self.assertEqual(ramuh["best_score"], 16000)

    def test_trial_chronicle_rank_uses_unique_flagship_clears(self):
        for boss_id in ("ifrit", "shiva", "ramuh"):
            self.db.execute(
                "INSERT INTO player_boss_clears(player_id,boss_id,clears,best_damage,last_cleared_at) VALUES (?,?,1,100,CURRENT_TIMESTAMP)",
                ("1", boss_id),
            )
        repo = PortalRepository(self.path, ROOT / "data")
        try:
            records = repo.records("van")
        finally:
            repo.close()
        self.assertEqual(records["trial_summary"]["unique_clears"], 3)
        self.assertEqual(records["trial_summary"]["total_trials"], 7)
        self.assertEqual(records["trial_summary"]["rank"], "Trial Vanguard")
        self.assertEqual(len(records["trials"]), 7)

    def test_unscripted_raid_does_not_create_trial_metrics(self):
        boss = self._start("bomb_king")
        boss["round"] = 2
        self.game.raid_roster["1"].update(damage=1000, healing=0, mitigation=0)
        self.assertTrue(self.game._finish_raid(False, reason="test").ok)
        row = self.db.one("SELECT COUNT(*) AS n FROM player_record_stats WHERE player_id='1' AND metric LIKE 'trial_bomb_king_%'")
        self.assertEqual(int(row["n"]), 0)


if __name__ == "__main__":
    unittest.main()

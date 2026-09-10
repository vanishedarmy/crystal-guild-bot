from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.active_battle import FULL_RESOURCE_SENTINEL
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine, LONG_REST_SECONDS


ROOT = Path(__file__).resolve().parents[1]


class PassiveRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(9),
        )
        self.assertTrue(self.game.recruit("1", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("1", "blackmage").ok)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def _max_resources(self, player_id: str = "1") -> tuple[int, int, int]:
        p = self.db.one("SELECT * FROM players WHERE twitch_id=?", (player_id,))
        job = self.game.data.jobs[p["current_job"]]
        stats = self.game._stats(p, job)
        from crystal_guild.active_battle import battle_resource_pools
        pools = battle_resource_pools(stats, job)
        return int(stats["hp"]), int(pools.get("max_mp") or 0), int(pools.get("max_ap") or 0)

    def test_long_rest_refreshes_after_eight_hours_without_player_action(self):
        start = 1_000_000
        self.game.record_player_action("1", now=start)
        self.db.execute(
            "UPDATE players SET current_hp=1, current_mp=1, current_ap=0, camp_until=? WHERE twitch_id='1'",
            (start + 99_999,),
        )

        result = self.game.record_player_action("1", now=start + LONG_REST_SECONDS)
        self.assertTrue(result["refreshed"])
        row = self.db.one("SELECT * FROM players WHERE twitch_id='1'")
        max_hp, max_mp, max_ap = self._max_resources()
        self.assertEqual(int(row["current_hp"]), max_hp)
        self.assertEqual(int(row["current_mp"]), FULL_RESOURCE_SENTINEL)
        self.assertEqual(int(row["current_ap"]), FULL_RESOURCE_SENTINEL)
        resources = self.game._resource_state_for(row, initialize=False)
        self.assertEqual(int(resources["mp"]), max_mp)
        self.assertEqual(int(resources["ap"]), max_ap)
        self.assertEqual(int(row["camp_until"]), 0)

    def test_long_rest_restores_inactive_resource_family_before_job_switch(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        warrior = self.game._resource_state_for(self.game._player("1"))
        self.db.execute("UPDATE players SET current_ap=1 WHERE twitch_id='1'")
        self.assertTrue(self.game.choose_job("1", "blackmage").ok)
        blackmage = self.game._resource_state_for(self.game._player("1"))
        self.db.execute("UPDATE players SET current_mp=1 WHERE twitch_id='1'")

        start = 1_500_000
        self.game.record_player_action("1", now=start)
        result = self.game.record_player_action("1", now=start + LONG_REST_SECONDS)
        self.assertTrue(result["refreshed"])

        after_rest = self.game._player("1")
        self.assertEqual(int(after_rest["current_mp"]), FULL_RESOURCE_SENTINEL)
        self.assertEqual(int(after_rest["current_ap"]), FULL_RESOURCE_SENTINEL)
        current = self.game._resource_state_for(after_rest, initialize=False)
        self.assertEqual(int(current["mp"]), int(blackmage["max_mp"]))

        switched = self.game.choose_job("1", "warrior")
        self.assertTrue(switched.ok, switched.messages)
        restored = self.game._resource_state_for(self.game._player("1"), initialize=False)
        self.assertEqual(int(restored["ap"]), int(restored["max_ap"]))
        self.assertGreaterEqual(int(restored["ap"]), int(warrior["max_ap"]))

    def test_long_rest_does_not_fire_before_eight_hours(self):
        start = 2_000_000
        self.game.record_player_action("1", now=start)
        self.db.execute("UPDATE players SET current_hp=1, current_mp=1 WHERE twitch_id='1'")
        result = self.game.record_player_action("1", now=start + LONG_REST_SECONDS - 1)
        self.assertFalse(result["refreshed"])
        row = self.db.one("SELECT current_hp,current_mp FROM players WHERE twitch_id='1'")
        self.assertEqual(int(row["current_hp"]), 1)
        self.assertEqual(int(row["current_mp"] or 0), 1)

    def test_scheduler_refreshes_due_long_rest_without_player_action(self):
        start = 3_000_000
        self.game.record_player_action("1", now=start)
        self.db.execute("UPDATE players SET current_hp=1, current_mp=1 WHERE twitch_id='1'")

        early = self.game.refresh_due_long_rests(now=start + LONG_REST_SECONDS - 1)
        self.assertEqual(early["count"], 0)
        self.assertEqual(int(self.db.one("SELECT current_hp FROM players WHERE twitch_id='1'")["current_hp"]), 1)

        due = self.game.refresh_due_long_rests(now=start + LONG_REST_SECONDS)
        self.assertEqual(due["count"], 1)
        row = self.db.one("SELECT * FROM players WHERE twitch_id='1'")
        self.assertEqual(int(row["current_hp"]), self.game._max_hp(row))

        self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='1'")
        repeat = self.game.refresh_due_long_rests(now=start + LONG_REST_SECONDS + 60)
        self.assertEqual(repeat["count"], 0)
        self.assertEqual(int(self.db.one("SELECT current_hp FROM players WHERE twitch_id='1'")["current_hp"]), 1)

    def test_stream_live_refreshes_all_players_once_per_started_at(self):
        self.assertTrue(self.game.recruit("2", "terra", "Terra").ok)
        self.assertTrue(self.game.choose_job("2", "warrior").ok)
        self.db.execute("UPDATE players SET current_hp=1, current_mp=1, current_ap=1, camp_until=9999999999")

        first = self.game.refresh_all_players_for_stream("2026-08-25T23:00:00Z")
        self.assertTrue(first["refreshed"])
        self.assertEqual(first["count"], 2)
        for player_id in ("1", "2"):
            row = self.db.one("SELECT * FROM players WHERE twitch_id=?", (player_id,))
            self.assertEqual(int(row["current_hp"]), self.game._max_hp(row))
            self.assertEqual(int(row["camp_until"]), 0)

        self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='1'")
        repeat = self.game.refresh_all_players_for_stream("2026-08-25T23:00:00Z")
        self.assertFalse(repeat["refreshed"])
        self.assertEqual(int(self.db.one("SELECT current_hp FROM players WHERE twitch_id='1'")["current_hp"]), 1)

        next_stream = self.game.refresh_all_players_for_stream("2026-08-26T23:00:00Z")
        self.assertTrue(next_stream["refreshed"])
        row = self.db.one("SELECT * FROM players WHERE twitch_id='1'")
        self.assertEqual(int(row["current_hp"]), self.game._max_hp(row))


if __name__ == "__main__":
    unittest.main()

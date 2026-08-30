from __future__ import annotations

import random
import tempfile
import threading
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class DungeonsBeta3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db1 = Database(self.path)
        self.game1 = CrystalGuildEngine(
            self.db1,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay1.json"),
            rng=random.Random(1430),
        )
        self.game1.recruit("1430", "beta3", "Beta Three")
        self.game1.choose_job("1430", "warrior")
        self.db1.execute("UPDATE players SET level=40,current_hp=1800 WHERE twitch_id='1430'")
        for region_id, progress in (("emerald_wilds", 70), ("ashen_highlands", 70), ("frostveil_reach", 70), ("astral_scar", 70)):
            self.db1.execute(
                "INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES (?,?,?,8) "
                "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=excluded.progress,stages_cleared=excluded.stages_cleared",
                ("1430", region_id, progress),
            )
        self.db2 = Database(self.path)
        self.game2 = CrystalGuildEngine(
            self.db2,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay2.json"),
            rng=random.Random(1431),
        )

    def tearDown(self) -> None:
        self.db2.close()
        self.db1.close()
        self.tmp.cleanup()

    def _enter_first_combat(self):
        started = self.game1.portal_dungeon_start("1430", "forgotten_ossuary", "b3_start")
        self.assertTrue(started.ok, started.messages)
        entrance = self.game1._dungeon_public("1430")
        moved = self.game1.portal_dungeon_continue(
            "1430", entrance["run_id"], entrance["room"]["id"], entrance["revision"], "b3_enter_combat"
        )
        self.assertTrue(moved.ok, moved.messages)
        public = self.game1._dungeon_public("1430")
        self.assertEqual(public["status"], "combat")
        return public

    @staticmethod
    def _run_together(call_a, call_b):
        barrier = threading.Barrier(2)
        results = [None, None]
        errors = []

        def runner(index, fn):
            try:
                barrier.wait(timeout=5)
                results[index] = fn()
            except BaseException as exc:  # surface worker failures in the test thread
                errors.append(exc)

        threads = [threading.Thread(target=runner, args=(0, call_a)), threading.Thread(target=runner, args=(1, call_b))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        if errors:
            raise errors[0]
        if any(thread.is_alive() for thread in threads):
            raise AssertionError("Concurrent Dungeon action did not finish")
        return results

    def test_beta3_identity_keeps_schema10_protocol25_and_feature_freeze(self):
        self.assertEqual(__version__, "1.4.0-dungeons-delves")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 10)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 25)
        self.assertEqual(len(self.game1._dungeon_board_state("1430")["dungeons"]), 4)

    def test_two_engine_connections_cannot_spend_same_revision_twice(self):
        public = self._enter_first_combat()
        calls = (
            lambda: self.game1.portal_dungeon_action("1430", public["run_id"], public["room"]["id"], public["revision"], "defend", "b3_parallel_a"),
            lambda: self.game2.portal_dungeon_action("1430", public["run_id"], public["room"]["id"], public["revision"], "defend", "b3_parallel_b"),
        )
        first, second = self._run_together(*calls)
        oks = [result for result in (first, second) if result.ok]
        stale = [result for result in (first, second) if not result.ok and result.data.get("stale_dungeon")]
        self.assertEqual(len(oks), 1)
        self.assertEqual(len(stale), 1)
        after = self.game1._dungeon_public("1430")
        self.assertEqual(int(after["combat"]["round"]), int(public["combat"]["round"]) + 1)
        self.assertGreater(int(after["revision"]), int(public["revision"]))

    def test_two_engine_connections_replay_same_action_id_exactly_once(self):
        public = self._enter_first_combat()
        call = lambda game: game.portal_dungeon_action(
            "1430", public["run_id"], public["room"]["id"], public["revision"], "defend", "b3_parallel_same_receipt"
        )
        first, second = self._run_together(lambda: call(self.game1), lambda: call(self.game2))
        self.assertTrue(first.ok)
        self.assertTrue(second.ok)
        self.assertEqual(first.messages, second.messages)
        after = self.game1._dungeon_public("1430")
        self.assertEqual(int(after["combat"]["round"]), int(public["combat"]["round"]) + 1)
        receipt = self.db1.runtime_state("portal_action:b3_parallel_same_receipt")
        self.assertIsNotNone(receipt)

    def test_continue_and_retreat_from_same_render_serialize_across_connections(self):
        start = self.game1.portal_dungeon_start("1430", "forgotten_ossuary", "b3_race_start")
        self.assertTrue(start.ok)
        public = self.game1._dungeon_public("1430")
        first, second = self._run_together(
            lambda: self.game1.portal_dungeon_continue("1430", public["run_id"], public["room"]["id"], public["revision"], "b3_race_continue"),
            lambda: self.game2.portal_dungeon_retreat("1430", public["run_id"], public["room"]["id"], public["revision"], "b3_race_retreat"),
        )
        oks = [result for result in (first, second) if result.ok]
        stale = [result for result in (first, second) if not result.ok and result.data.get("stale_dungeon")]
        self.assertEqual(len(oks), 1)
        self.assertEqual(len(stale), 1)
        progress = self.db1.one("SELECT retreats FROM player_dungeon_progress WHERE player_id=? AND dungeon_id=?", ("1430", "forgotten_ossuary"))
        active = self.game1._dungeon_public("1430")
        if active is None:
            self.assertIsNotNone(progress)
            self.assertEqual(int(progress["retreats"]), 1)
        else:
            self.assertEqual(int(active["room_number"]), 2)
            self.assertTrue(progress is None or int(progress["retreats"]) == 0)


if __name__ == "__main__":
    unittest.main()

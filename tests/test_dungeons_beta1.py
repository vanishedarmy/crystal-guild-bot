from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class DungeonsBeta1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(1410),
        )
        self.game.recruit("1410", "beta", "Beta")
        self.game.choose_job("1410", "warrior")
        self.db.execute("UPDATE players SET level=40,current_hp=1200 WHERE twitch_id='1410'")
        for region_id, progress in (("emerald_wilds",70),("ashen_highlands",70),("frostveil_reach",70),("astral_scar",70)):
            self.db.execute(
                "INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES (?,?,?,8) "
                "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=excluded.progress,stages_cleared=excluded.stages_cleared",
                ("1410", region_id, progress),
            )

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def _enter_first_combat(self):
        start = self.game.portal_dungeon_start("1410", "forgotten_ossuary", "b1_start")
        self.assertTrue(start.ok)
        public = self.game._dungeon_public("1410")
        self.assertGreater(public["revision"], 0)
        moved = self.game.portal_dungeon_continue(
            "1410", public["run_id"], public["room"]["id"], public["revision"], "b1_continue"
        )
        self.assertTrue(moved.ok)
        combat = self.game._dungeon_public("1410")
        self.assertEqual(combat["status"], "combat")
        return combat

    def test_beta1_protocol25_schema10_and_four_dungeon_feature_freeze(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 27)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 39)
        board = self.game._dungeon_board_state("1410")
        self.assertEqual(len(board["dungeons"]), 4)
        self.assertEqual(
            [row["id"] for row in board["dungeons"]],
            ["forgotten_ossuary", "emberglass_foundry", "whiteglass_bastion", "riftglass_observatory"],
        )

    def test_same_room_old_revision_cannot_spend_a_second_combat_turn(self):
        public = self._enter_first_combat()
        old_revision = public["revision"]
        first = self.game.portal_dungeon_action(
            "1410", public["run_id"], public["room"]["id"], old_revision, "defend", "b1_round_1"
        )
        self.assertTrue(first.ok)
        after = self.game._dungeon_public("1410")
        self.assertGreater(after["revision"], old_revision)
        round_after_first = int(after["combat"]["round"])

        stale = self.game.portal_dungeon_action(
            "1410", public["run_id"], public["room"]["id"], old_revision, "defend", "b1_stale_round"
        )
        self.assertFalse(stale.ok)
        self.assertTrue(stale.data.get("stale_dungeon"))
        final = self.game._dungeon_public("1410")
        self.assertEqual(int(final["combat"]["round"]), round_after_first)

    def test_same_action_id_replays_before_revision_check_without_advancing_twice(self):
        public = self._enter_first_combat()
        result = self.game.portal_dungeon_action(
            "1410", public["run_id"], public["room"]["id"], public["revision"], "defend", "b1_replay_round"
        )
        self.assertTrue(result.ok)
        after = self.game._dungeon_public("1410")
        round_after = int(after["combat"]["round"])
        replay = self.game.portal_dungeon_action(
            "1410", public["run_id"], public["room"]["id"], public["revision"], "defend", "b1_replay_round"
        )
        self.assertEqual(replay.ok, result.ok)
        self.assertEqual(int(self.game._dungeon_public("1410")["combat"]["round"]), round_after)

    def test_old_revision_cannot_retreat_newer_same_room_state(self):
        public = self._enter_first_combat()
        old_revision = public["revision"]
        self.assertTrue(self.game.portal_dungeon_action(
            "1410", public["run_id"], public["room"]["id"], old_revision, "defend", "b1_round_for_retreat"
        ).ok)
        stale = self.game.portal_dungeon_retreat(
            "1410", public["run_id"], public["room"]["id"], old_revision, "b1_stale_retreat"
        )
        self.assertFalse(stale.ok)
        self.assertIsNotNone(self.game._dungeon_load("1410"))

    def test_revision_survives_engine_reconnect(self):
        public = self._enter_first_combat()
        revision = public["revision"]
        self.db.close()
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay2.json"),
            rng=random.Random(1411),
        )
        restored = self.game._dungeon_public("1410")
        self.assertEqual(restored["revision"], revision)
        self.assertEqual(restored["run_id"], public["run_id"])
        self.assertEqual(restored["room"]["id"], public["room"]["id"])

    def test_adventure_payload_remains_below_16k_after_revision_binding(self):
        payload = self.game._portal_adventure_state_data("1410", stream_live=True)
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertLess(len(encoded), 16 * 1024)


if __name__ == "__main__":
    unittest.main()

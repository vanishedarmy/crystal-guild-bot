from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class DungeonsAlpha2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.db_path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(1402),
        )
        self.game.recruit("142", "pathfinder", "Pathfinder")
        self.game.choose_job("142", "warrior")
        self.db.execute("UPDATE players SET level=25,current_hp=280 WHERE twitch_id='142'")
        for region_id, progress in (("emerald_wilds", 25), ("ashen_highlands", 35)):
            self.db.execute(
                "INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES (?,?,?,?) "
                "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=excluded.progress,stages_cleared=excluded.stages_cleared",
                ("142", region_id, progress, 8),
            )

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_alpha2_keeps_schema10_and_advances_protocol24(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 22)
        self.assertEqual(self.db.schema_version(), 22)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 37)

    def test_board_exposes_two_dungeons_with_route_choices(self):
        board = self.game._dungeon_board_state("142")
        self.assertEqual([row["id"] for row in board["dungeons"][:2]], ["forgotten_ossuary", "emberglass_foundry"])
        self.assertTrue(all(row["unlocked"] for row in board["dungeons"][:2]))
        self.assertEqual([row["rooms"] for row in board["dungeons"][:2]], [8, 8])
        self.assertEqual([row["choice_rooms"] for row in board["dungeons"][:2]], [1, 1])
        self.assertEqual(board["dungeons"][1]["recommended_level"], 21)

    def test_locked_foundry_reports_existing_expedition_requirement(self):
        self.db.execute("UPDATE player_region_exploration SET progress=34 WHERE player_id='142' AND region_id='ashen_highlands'")
        board = self.game._dungeon_board_state("142")
        foundry = next(row for row in board["dungeons"] if row["id"] == "emberglass_foundry")
        self.assertFalse(foundry["unlocked"])
        self.assertTrue(any("Ashen Highlands" in value and "35%" in value for value in foundry["missing"]))

    def test_ossuary_crossroads_applies_risk_reward_and_discovery(self):
        self.assertTrue(self.game.dungeon_start("142", "forgotten_ossuary").ok)
        state = self.game._dungeon_load("142")
        state["room_index"] = 3
        state["status"] = "choice"
        self.game._dungeon_save("142", state)
        entered = self.game._dungeon_begin_room("142", state)
        self.assertTrue(entered.ok, entered.messages)
        public = self.game._dungeon_public("142")
        self.assertEqual(public["status"], "decision")
        self.assertEqual(public["room"]["id"], "forked_crypt")
        self.assertEqual({row["id"] for row in public["choices"]}, {"warded_stair", "sealed_reliquary"})

        hp_before = int(self.db.one("SELECT current_hp FROM players WHERE twitch_id='142'")["current_hp"])
        run_id = public["run_id"]
        room_id = public["room"]["id"]
        result = self.game.portal_dungeon_choice("142", run_id, room_id, public["revision"], "sealed_reliquary", "pa_a2_reliquary")
        self.assertTrue(result.ok, result.messages)
        after = self.game._dungeon_public("142")
        hp_after = int(self.db.one("SELECT current_hp FROM players WHERE twitch_id='142'")["current_hp"])
        self.assertLess(hp_after, hp_before)
        self.assertGreaterEqual(int(after["cache"]["gil"]), 110)
        self.assertIn("Sealed Reliquary", after["discoveries"])
        self.assertTrue(any(row.get("id") == "ancient_coin" for row in after["cache"]["items"]))

        replay = self.game.portal_dungeon_choice("142", run_id, room_id, public["revision"], "sealed_reliquary", "pa_a2_reliquary")
        self.assertTrue(replay.ok, replay.messages)
        replay_state = self.game._dungeon_public("142")
        self.assertEqual(int(replay_state["cache"]["gil"]), int(after["cache"]["gil"]))

    def test_foundry_can_start_and_exposes_its_own_art_and_route(self):
        result = self.game.dungeon_start("142", "emberglass_foundry")
        self.assertTrue(result.ok, result.messages)
        public = self.game._dungeon_public("142")
        self.assertEqual(public["name"], "The Emberglass Foundry")
        self.assertEqual(public["art"], "/expeditions/ashen-highlands.webp")
        self.assertEqual(public["room_count"], 8)

    def test_portal_worker_accepts_typed_dungeon_choice_action(self):
        self.assertTrue(self.game.dungeon_start("142", "forgotten_ossuary").ok)
        state = self.game._dungeon_load("142")
        state["room_index"] = 3
        state["status"] = "choice"
        self.game._dungeon_save("142", state)
        self.game._dungeon_begin_room("142", state)
        public = self.game._dungeon_public("142")
        worker = PortalActionWorker(self.game, "https://guild.example", "sync-key")
        action = {
            "id": "pa_a2_choice_worker",
            "protocol_version": ACTION_PROTOCOL_VERSION,
            "twitch_id": "142",
            "username": "pathfinder",
            "type": "DUNGEON_CHOICE",
            "payload": {"run_id": public["run_id"], "room_id": public["room"]["id"], "revision": public["revision"], "choice_id": "warded_stair"},
            "lease_token": "lease",
        }
        ok, message, data = worker._execute(action)
        self.assertTrue(ok, message)
        self.assertIn("adventure_state", data)
        current = self.game._dungeon_public("142")
        self.assertIn("Warden’s Route", current["discoveries"])


if __name__ == "__main__":
    unittest.main()

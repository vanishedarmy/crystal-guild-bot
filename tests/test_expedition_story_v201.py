from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.expedition_story import REGION_SCENES, scene

ROOT = Path(__file__).resolve().parents[1]


class ExpeditionStoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db, self.data,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(20201),
        )
        self.game.recruit("100", "storyhero", "Story Hero")
        self.game.choose_job("100", "warrior")
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='100'")
        self.db.execute("UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1")
        self.db.execute(
            "INSERT INTO player_chocobos(player_id,name,registered_at) VALUES ('100','Biscuit',CURRENT_TIMESTAMP) "
            "ON CONFLICT(player_id) DO UPDATE SET name='Biscuit'"
        )

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_all_eleven_regions_get_distinct_atmosphere(self):
        self.assertEqual(set(REGION_SCENES), set(self.data.expedition_regions))
        self.assertEqual(len(REGION_SCENES), 11)
        for region_id, rows in REGION_SCENES.items():
            for kind in ("arrival", "travel", "combat", "camp", "return"):
                self.assertGreaterEqual(len(rows[kind]), 2, (region_id, kind))
                self.assertTrue(scene(region_id, kind, "abc", 2))
            for kind in ("resource", "treasure", "hazard", "discovery", "traveler", "chocobo", "airship", "rare"):
                self.assertTrue(scene(region_id, kind, "abc", 3), (region_id, kind))

    def test_narration_is_repeatable_without_advancing_gameplay_rng(self):
        rng = random.Random(321)
        before = rng.getstate()
        a = scene("emerald_wilds", "travel", "run-1", 2, "safe")
        self.assertEqual(a, scene("emerald_wilds", "travel", "run-1", 2, "safe"))
        self.assertEqual(before, rng.getstate())
        # Different run ids should create different scenes across a reasonable sampling.
        self.assertGreaterEqual(len({scene("emerald_wilds", "travel", f"run-{i}", 2, "deep") for i in range(30)}), 3)

    def test_launch_travel_and_stage_event_are_saved_and_visible(self):
        result = self.game.expedition_start("100", "emerald_wilds", "scout")
        self.assertTrue(result.ok, result.messages)
        self.assertIn("Emerald Wilds", " ".join(result.messages))
        state = self.game._expedition_load("100")
        self.assertEqual(state["status"], "travel")
        self.assertTrue(state["travel_story"])
        self.assertEqual(state["history"][-1]["type"], "travel")
        self.assertEqual(self.game._expedition_public("100")["history"][-1]["label"], state["travel_story"])
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        with patch.object(self.game.rng, "random", return_value=1.0), patch(
            "crystal_guild.engine.expedition_event_weights", return_value=(["resource"], [1.0])
        ):
            event_result = self.game.expedition_resolve_stage("100")
        self.assertTrue(event_result.ok, event_result.messages)
        updated = self.game._expedition_load("100")
        self.assertEqual(updated["event"]["type"], "resource")
        self.assertTrue(updated["event"]["story"])
        self.assertIn(updated["event"]["story"], updated["event"]["label"])
        self.assertEqual(updated["history"][-1]["label"], updated["event"]["label"])
        self.assertEqual(self.game._expedition_public("100")["event"]["label"], updated["event"]["label"])
        # An engine reloading the same database must not regenerate the journal.
        new_engine = CrystalGuildEngine(self.db, self.data, overlay_state_path=str(Path(self.tmp.name) / "overlay2.json"), rng=random.Random(50))
        self.assertEqual(new_engine._expedition_public("100")["event"]["label"], updated["event"]["label"])

    def test_camp_and_return_add_ending_to_existing_history(self):
        result = self.game.expedition_start("100", "ashen_highlands", "journey")
        self.assertTrue(result.ok, result.messages)
        state = self.game._expedition_load("100")
        state["status"] = "choice"
        self.game._expedition_save("100", state)
        camp = self.game.expedition_camp("100")
        self.assertTrue(camp.ok, camp.messages)
        state = self.game._expedition_load("100")
        self.assertIn("Made Expedition Camp", state["history"][-1]["label"])
        self.assertIn("camp", state["history"][-1]["type"])
        returned = self.game.expedition_return("100")
        self.assertTrue(returned.ok, returned.messages)
        summary = returned.data.get("expedition_result") or {}
        self.assertEqual(summary["history"][-1]["type"], "return")
        self.assertTrue(summary["history"][-1]["label"])
        self.assertIsNone(self.game._expedition_load("100"))


if __name__ == "__main__":
    unittest.main()

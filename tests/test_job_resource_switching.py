from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine, RESOURCE_POOL_REPAIR_STATE_KEY

ROOT = Path(__file__).resolve().parents[1]


class JobResourceSwitchingHotfixTests(unittest.TestCase):
    def _engine(self, db: Database, tmp: str, seed: int = 71) -> CrystalGuildEngine:
        return CrystalGuildEngine(
            db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(tmp) / f"overlay-{seed}.json"),
            rng=random.Random(seed),
        )

    def test_inactive_resource_survives_refresh_and_equipment_normalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                game = self._engine(db, tmp)
                game.recruit("1", "van", "Van")
                self.assertTrue(game.choose_job("1", "warrior").ok)
                db.execute("UPDATE players SET current_ap=7 WHERE twitch_id='1'")

                self.assertTrue(game.choose_job("1", "blackmage").ok)
                before = game._player("1")
                self.assertEqual(int(before["current_ap"]), 7)

                game._full_refresh_player_row(before)
                after_refresh = game._player("1")
                self.assertEqual(int(after_refresh["current_ap"]), 7)

                game._normalize_after_equipment_change("1")
                after_equipment = game._player("1")
                self.assertEqual(int(after_equipment["current_ap"]), 7)

                switched = game.choose_job("1", "warrior")
                self.assertTrue(switched.ok, switched.messages)
                resources = game._resource_state_for(game._player("1"), initialize=False)
                self.assertEqual(int(resources["ap"]), 7)
            finally:
                db.close()

    def test_startup_repairs_legacy_inactive_zero_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                db.execute(
                    "INSERT INTO players(twitch_id,username,display_name,current_job,current_hp,current_mp,current_ap) "
                    "VALUES ('9','legacy','Legacy','blackmage',100,5,0)"
                )
                db.execute("INSERT INTO equipment(player_id) VALUES ('9')")
                db.execute("INSERT INTO player_jobs(player_id,job_id,level,jp) VALUES ('9','blackmage',10,0)")

                game = self._engine(db, tmp, 72)
                repaired = game._player("9")
                self.assertIsNone(repaired["current_ap"])
                self.assertIsNotNone(db.runtime_state(RESOURCE_POOL_REPAIR_STATE_KEY))

                switched = game.choose_job("9", "warrior")
                self.assertTrue(switched.ok, switched.messages)
                resources = game._resource_state_for(game._player("9"), initialize=False)
                self.assertGreater(int(resources["ap"]), 0)

                # The compatibility repair is startup-once, not a repeatable refill.
                self.assertTrue(game.choose_job("9", "blackmage").ok)
                db.execute("UPDATE players SET current_ap=0 WHERE twitch_id='9'")
                self._engine(db, tmp, 73)
                self.assertEqual(int(game._player("9")["current_ap"]), 0)
            finally:
                db.close()

    def test_legitimate_zero_resource_is_not_refilled_by_job_swapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                game = self._engine(db, tmp, 74)
                game.recruit("1", "van", "Van")
                self.assertTrue(game.choose_job("1", "warrior").ok)
                db.execute("UPDATE players SET current_ap=0 WHERE twitch_id='1'")

                self.assertTrue(game.choose_job("1", "blackmage").ok)
                game._full_refresh_player_row(game._player("1"))
                game._normalize_after_equipment_change("1")
                self.assertEqual(int(game._player("1")["current_ap"]), 0)

                switched = game.choose_job("1", "warrior")
                self.assertTrue(switched.ok, switched.messages)
                resources = game._resource_state_for(game._player("1"), initialize=False)
                self.assertEqual(int(resources["ap"]), 0)
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()

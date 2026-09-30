from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.fellowship import AIRSHIP_MISSIONS, DEEDS, LEGACY_ACCOMPLISHMENTS, ORDER_DEFINITIONS, PROJECTS
from crystal_guild.fellowship_system import FellowshipSystem

ROOT = Path(__file__).resolve().parents[1]
LIVE_ONLY = {"raid_clear", "raid_win", "raid_participation"}


class OfflineProgression1948Tests(unittest.TestCase):
    def test_upgrade_and_fellowship_progression_has_no_live_only_requirement(self):
        for project_id, project in PROJECTS.items():
            for req in project.get("requirements", []):
                if req.get("kind") == "activity":
                    self.assertNotIn(req.get("asset_id"), LIVE_ONLY, (project_id, req))
                    self.assertFalse(any(token in str(req.get("key", "")) for token in LIVE_ONLY), (project_id, req))
        for mission in AIRSHIP_MISSIONS:
            self.assertTrue(LIVE_ONLY.isdisjoint(set((mission.get("activities") or {}).keys())), mission)
        for order in ORDER_DEFINITIONS:
            self.assertNotIn(order.get("activity"), LIVE_ONLY, order)
        for deed in DEEDS:
            self.assertNotIn(deed.get("activity"), LIVE_ONLY, deed)
        for accomplishment in LEGACY_ACCOMPLISHMENTS:
            self.assertNotIn(accomplishment.get("metric"), {"raids_won", "raid_wins", "raid_participations"}, accomplishment)

    def test_old_raid_gated_project_progress_is_carried_to_new_offline_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            data = GameData(ROOT / "data")
            system = FellowshipSystem(db, data)
            db.execute(
                "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES ('guild_hall_t2','activity:raid_clear',2) "
                "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=2"
            )
            system = FellowshipSystem(db, data)
            row = db.one(
                "SELECT current FROM fellowship_project_progress WHERE project_id='guild_hall_t2' AND requirement_key='activity:hunt_win'"
            )
            self.assertIsNotNone(row)
            self.assertEqual(int(row["current"]), 2)
            db.close()


if __name__ == "__main__":
    unittest.main()

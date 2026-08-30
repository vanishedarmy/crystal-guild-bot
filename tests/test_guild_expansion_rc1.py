from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class GuildExpansionFinalTests(unittest.TestCase):
    def test_final_identity_schema_and_protocol_are_release_values(self):
        self.assertEqual(__version__, "1.5.0-trails-raids-a2")
        self.assertEqual(ACTION_PROTOCOL_VERSION, 25)
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "final.db")
            try:
                self.assertEqual(db.schema_version(), 10)
                self.assertEqual(db.quick_check(), [])
            finally:
                db.close()

    def test_final_restart_preserves_airship_and_fellowship_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "guild.db"
            overlay = str(Path(tmp) / "overlay.json")
            db = Database(db_path)
            try:
                game = CrystalGuildEngine(db, GameData(ROOT / "data"), overlay_state_path=overlay, rng=random.Random(1301))
                game.recruit("1", "hero", "Hero")
                game.fellowship_system.ensure_member("1")
                db.execute("UPDATE fellowship_state SET level=8,renown=27000 WHERE singleton_id=1")
                db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='airship_dock'")
                db.execute("UPDATE fellowship_airship_state SET built=1,missions_completed=7 WHERE singleton_id=1")
                db.execute("UPDATE fellowship_airship_upgrades SET tier=2 WHERE upgrade_id='engine'")
            finally:
                db.close()

            reopened = Database(db_path)
            try:
                game2 = CrystalGuildEngine(reopened, GameData(ROOT / "data"), overlay_state_path=overlay, rng=random.Random(1302))
                snapshot = game2.fellowship_system.airship_snapshot()
                self.assertTrue(snapshot["built"])
                self.assertEqual(snapshot["missions_completed"], 7)
                engine = next(item for item in snapshot["upgrades"] if item["id"] == "engine")
                self.assertEqual(engine["tier"], 2)
                self.assertEqual(int(reopened.one("SELECT level FROM fellowship_state WHERE singleton_id=1")["level"]), 8)
                self.assertEqual(reopened.quick_check(), [])
            finally:
                reopened.close()

    def test_control_panel_and_upgrade_helper_identify_final_release(self):
        panel = (ROOT / "CRYSTAL_GUILD_CONTROL_PANEL.bat").read_text(encoding="utf-8")
        upgrade = (ROOT / "upgrade_crystal_guild.py").read_text(encoding="utf-8")
        self.assertIn("TRAILS & RAIDS ALPHA 1", panel.upper())
        self.assertIn("Trails & Raids Alpha 2", upgrade)
        self.assertNotIn("GUILD EXPANSION BETA 1", panel.upper())


if __name__ == "__main__":
    unittest.main()

"""Regression checks for runtime defects exposed by the v1.9.7/LW-0 audit.

These use new temporary databases and do not require a live stream or Portal.
"""
from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.seasonal_events import set_event_control

ROOT = Path(__file__).resolve().parents[1]


class RuntimeFailureAuditLW0Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "test.db")
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(777),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")
        with self.db.tx() as conn:
            set_event_control(conn, enabled=False)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_raid_overlay_reads_current_hp_without_legacy_hp(self):
        self.game.active_boss = {
            "id": "watchdog", "name": "Watchdog", "state": "combat",
            "round": 2, "current_hp": 25, "max_hp": 100,
        }
        overlay = self.game._overlay_payload()
        self.assertEqual((overlay["boss"], overlay["hp"], overlay["max_hp"]), ("Watchdog", 25, 100))
        self.game.active_boss = {"id": "minimal_watchdog", "state": "combat", "round": 2}
        minimal = self.game._overlay_payload()
        self.assertEqual((minimal["boss"], minimal["hp"], minimal["max_hp"]), ("minimal_watchdog", 1, 1))

    def test_guaranteed_enemy_self_buffs_ignore_hostile_accuracy_cap(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        self.assertTrue(self.game.start_encounter_battle(opened.data["encounter_id"]).ok)
        ability = self.game.data.enemy_actions["ironclad"]["ability"]
        self.game.active_encounter["monster_statuses"] = {}
        with patch.object(self.game.rng, "random", return_value=0.999):
            self.game._resolve_enemy_special(
                self.game.data.monsters["ironclad"],
                self.game.data.enemy_profiles["defensive"], ability, [],
            )
        statuses = self.game.active_encounter["monster_statuses"]
        self.assertIn("protect", statuses)
        self.assertIn("power_up", statuses)


if __name__ == "__main__":
    unittest.main()

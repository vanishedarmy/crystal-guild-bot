from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_sync import PortalSyncClient

ROOT = Path(__file__).resolve().parents[1]


class TrailsRaidsAlpha2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.overlay = Path(self.tmp.name) / "overlay.json"
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"), raid_join_seconds=90,
            raid_round_seconds=60, overlay_state_path=str(self.overlay),
            rng=random.Random(1502),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET level=60 WHERE twitch_id='1'")
        self.game.choose_job("1", "warrior")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def _start_shiva(self) -> None:
        self.assertTrue(self.game.spawn_boss("shiva").ok)
        self.assertTrue(self.game.raid_join("1").ok)
        started = self.game.start_raid()
        self.assertTrue(started.ok, started.messages)
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999
        self.game.active_boss["attacks_per_round"] = 0

    def test_alpha2_shiva_declares_diamond_throne_script(self):
        shiva = self.game.data.bosses["shiva"]
        self.assertEqual(shiva["encounter_type"], "Trial")
        self.assertEqual(shiva["encounter_name"], "Diamond Throne")
        self.assertEqual(shiva["raid_script"], "shiva_diamond_throne")
        self.assertEqual(
            [row["name"] for row in shiva["mechanics"]],
            ["Frostbrand Cleave", "Icebound Mirrors", "Diamond Aegis", "Staggered", "Diamond Dust"],
        )
        self.assertEqual(self.game.data.validate(), [])

    def test_alpha2_shiva_opens_with_cleave_then_spawns_adds(self):
        self._start_shiva()
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Frostbrand Cleave")
        first = self.game.raid_round()
        self.assertTrue(first.ok, first.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Icebound Mirrors")
        self.assertEqual(len(self.game._raid_live_adds()), 2)
        payload = self.game._overlay_payload()
        self.assertEqual(len(payload["adds"]), 2)
        self.assertEqual(payload["top"][0]["role"], "Tank")

    def test_alpha2_adds_intercept_boss_targeted_damage(self):
        self._start_shiva()
        self.game.raid_round()  # cleave -> mirrors
        boss_hp = int(self.game.active_boss["current_hp"])
        add = self.game._raid_live_adds()[0]
        add_hp = int(add["current_hp"])
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(int(self.game.active_boss["current_hp"]), boss_hp)
        self.assertLess(int(add["current_hp"]), add_hp)

    def test_alpha2_clearing_adds_advances_to_break_gauge(self):
        self._start_shiva()
        self.game.raid_round()
        self.game.active_boss["adds"][0]["current_hp"] = 0
        self.game.active_boss["adds"][1]["current_hp"] = 1
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Diamond Aegis")
        self.assertEqual(self.game._raid_live_adds(), [])
        self.assertTrue(any("ICEBOUND MIRRORS" in line for line in result.messages))

    def test_alpha2_break_success_creates_stagger_window(self):
        self._start_shiva()
        self.game.active_boss["adds"] = []
        self.game.active_boss["mechanic"] = {
            "name": "Diamond Aegis", "kind": "break_check", "warning": "test",
            "rounds_remaining": 2, "required": 1, "progress": 0,
        }
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["kind"], "stagger")
        self.assertEqual(self.game.active_boss["last_mechanic"]["result"], "broken")
        self.assertTrue(any("STAGGERED" in line for line in result.messages))
        followup = self.game.raid_round()
        self.assertTrue(followup.ok, followup.messages)
        self.assertTrue(any("STAGGER" in line for line in followup.messages))

    def test_alpha2_overlay_sync_sanitizes_adds_and_roles(self):
        self._start_shiva()
        self.game.raid_round()
        client = PortalSyncClient(object(), "https://guild.invalid", "key", overlay_state_path=self.overlay)  # type: ignore[arg-type]
        snapshot = client.build_overlay_snapshot()
        self.assertIsNotNone(snapshot)
        overlay = snapshot["overlay"]
        self.assertEqual(overlay["encounter_name"], "Diamond Throne")
        self.assertEqual(overlay["top"][0]["role"], "Tank")
        self.assertEqual(len(overlay["adds"]), 2)
        self.assertEqual(set(overlay["adds"][0]), {"name", "hp", "max_hp"})
        encoded = json.dumps(snapshot)
        self.assertNotIn("target_id", encoded)
        self.assertNotIn("icebound_mirror_a", encoded)


if __name__ == "__main__":
    unittest.main()

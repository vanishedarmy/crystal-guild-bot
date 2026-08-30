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


class TrailsRaidsAlpha1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.overlay = Path(self.tmp.name) / "overlay.json"
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            raid_join_seconds=90,
            raid_round_seconds=60,
            overlay_state_path=str(self.overlay),
            rng=random.Random(1501),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET level=60 WHERE twitch_id='1'")
        self.game.choose_job("1", "warrior")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def _start_ifrit(self) -> None:
        self.assertTrue(self.game.spawn_boss("ifrit").ok)
        self.assertTrue(self.game.raid_join("1").ok)
        started = self.game.start_raid()
        self.assertTrue(started.ok, started.messages)
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999
        self.game.active_boss["attacks_per_round"] = 0

    def test_alpha1_ifrit_declares_inferno_crucible_script(self):
        ifrit = self.game.data.bosses["ifrit"]
        self.assertEqual(ifrit["encounter_type"], "Trial")
        self.assertEqual(ifrit["encounter_name"], "Inferno Crucible")
        self.assertEqual(ifrit["raid_script"], "ifrit_inferno_crucible")
        self.assertEqual([row["name"] for row in ifrit["mechanics"]], ["Incinerate", "Radiant Plume", "Infernal Nails", "Hellfire"])
        self.assertEqual(self.game.data.validate(), [])

    def test_alpha1_start_telegraphs_incinerate_without_public_target_id(self):
        self._start_ifrit()
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Incinerate")
        self.assertEqual(self.game.active_boss["mechanic"]["target_id"], "1")
        payload = self.game._overlay_payload()
        self.assertEqual(payload["encounter_type"], "Trial")
        self.assertEqual(payload["encounter_name"], "Inferno Crucible")
        self.assertEqual(payload["mechanic"]["name"], "Incinerate")
        self.assertEqual(payload["mechanic"]["target"], "Van")
        self.assertNotIn("target_id", payload["mechanic"])

    def test_alpha1_ifrit_cycles_targeted_raidwide_then_nails(self):
        self._start_ifrit()
        first = self.game.raid_round()
        self.assertTrue(first.ok, first.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Radiant Plume")
        second = self.game.raid_round()
        self.assertTrue(second.ok, second.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Infernal Nails")
        self.assertEqual(self.game.active_boss["mechanic"]["rounds_remaining"], 2)
        self.assertTrue(any("TELEGRAPH" in line or "DAMAGE CHECK" in line for line in second.messages))

    def test_alpha1_infernal_nails_success_weakens_hellfire(self):
        self._start_ifrit()
        self.game.active_boss["mechanic"] = {
            "name": "Infernal Nails", "kind": "damage_check", "warning": "test",
            "rounds_remaining": 1, "required": 1, "progress": 0,
        }
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["last_mechanic"]["name"], "Hellfire")
        self.assertEqual(self.game.active_boss["last_mechanic"]["result"], "weakened")
        self.assertTrue(any("HELLFIRE" in line and "weakened" in line for line in result.messages))

    def test_alpha1_infernal_nails_failure_empowers_hellfire(self):
        self._start_ifrit()
        self.game.active_boss["mechanic"] = {
            "name": "Infernal Nails", "kind": "damage_check", "warning": "test",
            "rounds_remaining": 1, "required": 99999999, "progress": 0,
        }
        self.assertTrue(self.game.battle_defend("1").ok)
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["last_mechanic"]["result"], "empowered")
        self.assertTrue(any("HELLFIRE" in line and "empowered" in line for line in result.messages))

    def test_alpha1_overlay_sync_sanitizes_mechanics_and_contribution(self):
        self._start_ifrit()
        self.game.raid_round()
        client = PortalSyncClient(object(), "https://guild.invalid", "key", overlay_state_path=self.overlay)  # type: ignore[arg-type]
        snapshot = client.build_overlay_snapshot()
        self.assertIsNotNone(snapshot)
        overlay = snapshot["overlay"]
        self.assertEqual(overlay["encounter_type"], "Trial")
        self.assertNotIn("target_id", overlay.get("mechanic") or {})
        self.assertTrue(overlay["top"])
        self.assertIn("score", overlay["top"][0])
        self.assertIn("mitigation", overlay["top"][0])
        encoded = json.dumps(snapshot)
        self.assertNotIn('"target_id"', encoded)
        self.assertNotIn('"1"', encoded)


if __name__ == "__main__":
    unittest.main()

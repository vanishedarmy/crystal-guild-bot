from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class TrailsRaidsAlpha4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"), raid_join_seconds=90,
            raid_round_seconds=60, rng=random.Random(1504),
        )
        for pid, name, job in [("1", "Van", "warrior"), ("2", "Ari", "monk"), ("3", "Mira", "whitemage")]:
            self.game.recruit(pid, name.lower(), name)
            self.game.choose_job(pid, job if job in self.game.data.jobs else "warrior")
            self.db.execute("UPDATE players SET level=60 WHERE twitch_id=?", (pid,))
            self.game.choose_job(pid, job if job in self.game.data.jobs else "warrior")

    def tearDown(self) -> None:
        self.db.close(); self.tmp.cleanup()

    def _start_titan(self) -> None:
        self.assertTrue(self.game.spawn_boss("titan").ok)
        for pid in ("1", "2", "3"):
            self.assertTrue(self.game.raid_join(pid).ok)
        started = self.game.start_raid(); self.assertTrue(started.ok, started.messages)
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999
        self.game.active_boss["attacks_per_round"] = 0

    def test_alpha4_titan_declares_heart_of_the_crag(self):
        titan = self.game.data.bosses["titan"]
        self.assertEqual(titan["tier"], "Primal Boss")
        self.assertEqual(titan["encounter_type"], "Trial")
        self.assertEqual(titan["encounter_name"], "Heart of the Crag")
        self.assertEqual(titan["raid_script"], "titan_heart_of_crag")
        self.assertEqual(
            [row["name"] for row in titan["mechanics"]],
            ["Landslide", "Granite Gaol", "Heart of the Crag", "Earthen Fury"],
        )
        self.assertEqual(self.game.data.validate(), [])

    def test_alpha4_cycle_moves_from_landslide_to_gaol_to_heart(self):
        self._start_titan()
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Landslide")
        first = self.game.raid_round(); self.assertTrue(first.ok, first.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Granite Gaol")
        target_id = str(self.game.active_boss["mechanic"]["target_id"])
        self.assertEqual(self.game.raid_roster[target_id]["restrained"], "Granite Gaol")
        self.game.active_boss["adds"][0]["current_hp"] = 1
        second = self.game.raid_round(); self.assertTrue(second.ok, second.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Heart of the Crag")
        self.assertIsNone(self.game.raid_roster[target_id].get("restrained"))
        self.assertEqual(self.game._raid_live_adds()[0]["name"], "Heart of the Crag")

    def test_alpha4_landslide_defend_braces_and_avoids_knockdown(self):
        self._start_titan()
        self.game.active_boss["attacks_per_round"] = 2
        self.game.active_boss["mechanic"] = {
            "name": "Landslide", "kind": "knockback", "warning": "test",
            "target_id": "1", "target": "Van", "rounds_remaining": 1,
        }
        self.assertTrue(self.game.battle_defend("1").ok)
        result = self.game.raid_round(); self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["last_mechanic"]["result"], "braced")
        self.assertFalse(bool(self.game.raid_roster["1"].get("statuses", {}).get("stun")))
        self.assertTrue(any("braces through" in line for line in result.messages))

    def test_alpha4_granite_gaol_blocks_actions_until_party_breaks_it(self):
        self._start_titan()
        self.game.active_boss["mechanic"] = {
            "name": "Granite Gaol", "kind": "restraint", "warning": "test",
            "target_id": "1", "target": "Van", "rounds_remaining": 2,
        }
        self.game.active_boss["adds"] = [{
            "id": "granite_gaol", "name": "Granite Gaol — Van", "max_hp": 1,
            "current_hp": 1, "release_target_id": "1",
        }]
        self.game.raid_roster["1"]["restrained"] = "Granite Gaol"
        queued = self.game.battle_attack("1")
        self.assertFalse(queued.ok)
        self.assertIn("trapped", " ".join(queued.messages).lower())
        result = self.game.raid_round(); self.assertTrue(result.ok, result.messages)
        self.assertIsNone(self.game.raid_roster["1"].get("restrained"))
        self.assertTrue(any("freed" in line for line in result.messages))

    def test_alpha4_heart_clear_weakens_earthen_fury(self):
        self._start_titan()
        self.game.active_boss["mechanic"] = {
            "name": "Heart of the Crag", "kind": "heart_check", "warning": "test",
            "rounds_remaining": 2, "required": 1, "progress": 0,
        }
        self.game.active_boss["adds"] = [{"id": "heart_of_the_crag", "name": "Heart of the Crag", "max_hp": 1, "current_hp": 1}]
        result = self.game.raid_round(); self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["last_mechanic"]["name"], "Earthen Fury")
        self.assertEqual(self.game.active_boss["last_mechanic"]["result"], "weakened")
        self.assertTrue(any("EARTHEN FURY" in line for line in result.messages))

    def test_alpha4_overlay_sanitizes_gaol_target_ids(self):
        self._start_titan()
        self.game.raid_round()  # Landslide -> Granite Gaol
        payload = self.game._overlay_payload()
        self.assertEqual(payload["encounter_name"], "Heart of the Crag")
        self.assertEqual(payload["mechanic"]["name"], "Granite Gaol")
        self.assertNotIn("target_id", payload["mechanic"])
        self.assertEqual(set(payload["adds"][0]), {"name", "hp", "max_hp"})
        encoded = json.dumps(payload)
        self.assertNotIn("release_target_id", encoded)
        self.assertNotIn("granite_gaol", encoded)


if __name__ == "__main__":
    unittest.main()

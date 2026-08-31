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


class TrailsRaidsAlpha6Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            raid_join_seconds=90,
            raid_round_seconds=60,
            rng=random.Random(1506),
        )
        for pid, name, job in [("1", "Van", "warrior"), ("2", "Ari", "monk"), ("3", "Mira", "whitemage")]:
            self.game.recruit(pid, name.lower(), name)
            self.game.choose_job(pid, job)
            self.db.execute("UPDATE players SET level=60 WHERE twitch_id=?", (pid,))
            self.game.choose_job(pid, job)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _start(self):
        self.assertTrue(self.game.spawn_boss("leviathan").ok)
        for pid in ("1", "2", "3"):
            self.assertTrue(self.game.raid_join(pid).ok)
        self.assertTrue(self.game.start_raid().ok)
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999

    def test_alpha6_leviathan_declares_tidebreak_expanse(self):
        boss = self.game.data.bosses["leviathan"]
        self.assertEqual(boss["tier"], "Primal Boss")
        self.assertEqual(boss["encounter_type"], "Trial")
        self.assertEqual(boss["encounter_name"], "Tidebreak Expanse")
        self.assertEqual(boss["raid_script"], "leviathan_tidebreak_expanse")
        self.assertEqual([m["name"] for m in boss["mechanics"]], ["Tidal Sweep", "Undertow", "Maelstrom Surge", "Tidal Wave"])
        self.assertEqual(self.game.data.validate(), [])

    def test_alpha6_cycle_reaches_maelstrom_surge(self):
        self._start()
        self.game.active_boss["attacks_per_round"] = 0
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Tidal Sweep")
        self.assertTrue(self.game.raid_round().ok)
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Undertow")
        self.assertTrue(self.game.raid_round().ok)
        self.assertEqual(self.game.active_boss["mechanic"]["name"], "Maelstrom Surge")
        self.assertEqual(self.game.active_boss["mechanic"]["rounds_remaining"], 2)

    def test_alpha6_tidal_sweep_rewards_defend(self):
        self._start()
        self.game.active_boss["attacks_per_round"] = 2
        self.game.active_boss["mechanic"] = {
            "name": "Tidal Sweep", "kind": "side_sweep", "warning": "test", "side": "Port",
            "target_ids": ["1"], "target": "Van", "rounds_remaining": 1,
        }
        self.assertTrue(self.game.battle_defend("1").ok)
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["last_mechanic"]["result"], "braced")
        self.assertFalse(bool(self.game.raid_roster["1"].get("statuses", {}).get("slow")))

    def test_alpha6_undertow_unbraced_drains_resources_and_splashes(self):
        self._start()
        self.game.active_boss["attacks_per_round"] = 2
        meta = self.game.raid_roster["3"]
        before_mp = int(meta.get("mp", 0))
        before_hp = {pid: int(row["hp"]) for pid, row in self.game.raid_roster.items()}
        self.game.active_boss["mechanic"] = {
            "name": "Undertow", "kind": "undertow", "warning": "test",
            "target_id": "3", "target": "Mira", "rounds_remaining": 1,
        }
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["last_mechanic"]["result"], "dragged_under")
        self.assertLess(int(self.game.raid_roster["3"].get("mp", 0)), before_mp)
        self.assertTrue(all(int(self.game.raid_roster[pid]["hp"]) < before_hp[pid] for pid in before_hp))

    def test_alpha6_maelstrom_defends_stabilize_tidal_wave(self):
        self._start()
        self.game.active_boss["attacks_per_round"] = 2
        self.game.active_boss["mechanic"] = {
            "name": "Maelstrom Surge", "kind": "survival_check", "warning": "test",
            "rounds_remaining": 1, "required": 2, "progress": 0,
        }
        self.assertTrue(self.game.battle_defend("1").ok)
        self.assertTrue(self.game.battle_defend("2").ok)
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["last_mechanic"]["name"], "Tidal Wave")
        self.assertEqual(self.game.active_boss["last_mechanic"]["result"], "stabilized")

    def test_alpha6_overlay_sanitizes_side_target_ids(self):
        self._start()
        payload = self.game._overlay_payload()
        self.assertEqual(payload["encounter_name"], "Tidebreak Expanse")
        self.assertEqual(payload["mechanic"]["name"], "Tidal Sweep")
        encoded = json.dumps(payload)
        self.assertNotIn("target_ids", encoded)
        self.assertNotIn("_leviathan", encoded)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class TrailsRaidsAlpha3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), raid_join_seconds=90, raid_round_seconds=60, rng=random.Random(1503))
        for pid, name, job in [("1", "Van", "warrior"), ("2", "Ari", "monk"), ("3", "Mira", "whitemage")]:
            self.game.recruit(pid, name.lower(), name)
            self.game.choose_job(pid, job if job in self.game.data.jobs else "warrior")
            self.db.execute("UPDATE players SET level=60 WHERE twitch_id=?", (pid,))
            self.game.choose_job(pid, job if job in self.game.data.jobs else "warrior")

    def tearDown(self) -> None:
        self.db.close(); self.tmp.cleanup()

    def _start_ramuh(self) -> None:
        self.assertTrue(self.game.spawn_boss("ramuh").ok)
        for pid in ("1","2","3"):
            self.assertTrue(self.game.raid_join(pid).ok)
        started=self.game.start_raid(); self.assertTrue(started.ok, started.messages)
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999
        self.game.active_boss["attacks_per_round"] = 0

    def test_alpha3_ramuh_declares_judgment_spire(self):
        ramuh=self.game.data.bosses["ramuh"]
        self.assertEqual(ramuh["encounter_type"], "Trial")
        self.assertEqual(ramuh["encounter_name"], "Judgment Spire")
        self.assertEqual(ramuh["raid_script"], "ramuh_judgment_spire")
        self.assertEqual([m["name"] for m in ramuh["mechanics"]], ["Rolling Thunder","Levinshare","Judgment Charge","Judgment Bolt"])
        self.assertEqual(self.game.data.validate(), [])

    def test_alpha3_ramuh_opens_with_chain_then_stack(self):
        self._start_ramuh()
        self.assertEqual(self.game.active_boss["mechanic"]["kind"], "chain")
        first=self.game.raid_round(); self.assertTrue(first.ok, first.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["kind"], "shared_hit")
        second=self.game.raid_round(); self.assertTrue(second.ok, second.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["kind"], "guard_check")

    def test_alpha3_levinshare_uses_defenders_as_stack_partners(self):
        self._start_ramuh()
        self.game.active_boss["attacks_per_round"] = 2
        self.game.active_boss["mechanic"]={"name":"Levinshare","kind":"shared_hit","warning":"test","target_id":"1","target":"Van","rounds_remaining":1}
        self.game.battle_defend("2")
        result=self.game.raid_round(); self.assertTrue(result.ok, result.messages)
        last=self.game.active_boss["last_mechanic"]
        self.assertEqual(last["name"], "Levinshare")
        self.assertEqual(last["result"], "shared_2")
        self.assertTrue(any("Van, Ari" in line or "Ari, Van" in line for line in result.messages))

    def test_alpha3_guard_check_counts_defend_actions_and_weakens_judgment(self):
        self._start_ramuh()
        self.game.active_boss["attacks_per_round"] = 2
        self.game.active_boss["mechanic"]={"name":"Judgment Charge","kind":"guard_check","warning":"test","rounds_remaining":2,"required":2,"progress":0}
        self.game.battle_defend("1"); self.game.battle_defend("2")
        first=self.game.raid_round(); self.assertTrue(first.ok, first.messages)
        self.assertEqual(self.game.active_boss["mechanic"]["progress"], 2)
        second=self.game.raid_round(); self.assertTrue(second.ok, second.messages)
        self.assertEqual(self.game.active_boss["last_mechanic"]["result"], "grounded")
        self.assertTrue(any("JUDGMENT BOLT" in line for line in second.messages))

    def test_alpha3_zero_retaliation_preserves_script_compatibility(self):
        self._start_ramuh()
        hp={pid:int(meta["hp"]) for pid,meta in self.game.raid_roster.items()}
        result=self.game.raid_round(); self.assertTrue(result.ok, result.messages)
        self.assertEqual({pid:int(meta["hp"]) for pid,meta in self.game.raid_roster.items()}, hp)
        self.assertTrue(any("suppressed" in line for line in result.messages))


if __name__ == "__main__":
    unittest.main()

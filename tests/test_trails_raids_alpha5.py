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

class TrailsRaidsAlpha5Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=Database(Path(self.tmp.name)/"guild.db")
        self.game=CrystalGuildEngine(self.db,GameData(ROOT/"data"),raid_join_seconds=90,raid_round_seconds=60,rng=random.Random(1505))
        for pid,name,job in [("1","Van","warrior"),("2","Ari","monk"),("3","Mira","whitemage")]:
            self.game.recruit(pid,name.lower(),name); self.game.choose_job(pid,job); self.db.execute("UPDATE players SET level=60 WHERE twitch_id=?",(pid,)); self.game.choose_job(pid,job)
    def tearDown(self): self.db.close(); self.tmp.cleanup()
    def _start(self):
        self.assertTrue(self.game.spawn_boss("garuda_prime").ok)
        for pid in ("1","2","3"): self.assertTrue(self.game.raid_join(pid).ok)
        self.assertTrue(self.game.start_raid().ok); self.game.active_boss["current_hp"]=999999; self.game.active_boss["max_hp"]=999999
    def test_alpha5_garuda_declares_eye_of_storm(self):
        g=self.game.data.bosses["garuda_prime"]; self.assertEqual(g["tier"],"Primal Boss"); self.assertEqual(g["encounter_type"],"Trial"); self.assertEqual(g["encounter_name"],"Eye of the Storm"); self.assertEqual(g["raid_script"],"garuda_eye_of_storm"); self.assertEqual([m["name"] for m in g["mechanics"]],["Slipstream","Friction","Plume Squadron","Aerial Blast"]); self.assertEqual(self.game.data.validate(),[])
    def test_alpha5_cycle_reaches_plume_squadron(self):
        self._start(); self.game.active_boss["attacks_per_round"]=0
        self.assertEqual(self.game.active_boss["mechanic"]["name"],"Slipstream"); self.assertTrue(self.game.raid_round().ok); self.assertEqual(self.game.active_boss["mechanic"]["name"],"Friction"); self.assertTrue(self.game.raid_round().ok); self.assertEqual(self.game.active_boss["mechanic"]["name"],"Plume Squadron"); self.assertEqual([a["name"] for a in self.game._raid_live_adds()],["Satin Plume","Razor Plume"])
    def test_alpha5_slipstream_defend_braces(self):
        self._start(); self.game.active_boss["attacks_per_round"]=2; self.game.active_boss["mechanic"]={"name":"Slipstream","kind":"wind_pressure","warning":"test","target_id":"1","target":"Van","rounds_remaining":1}; self.assertTrue(self.game.battle_defend("1").ok); r=self.game.raid_round(); self.assertTrue(r.ok,r.messages); self.assertEqual(self.game.active_boss["last_mechanic"]["result"],"braced"); self.assertFalse(bool(self.game.raid_roster["1"].get("statuses",{}).get("slow")))
    def test_alpha5_friction_uncontained_splashes_party(self):
        self._start(); self.game.active_boss["attacks_per_round"]=2; self.game.active_boss["mechanic"]={"name":"Friction","kind":"wind_mark","warning":"test","target_id":"1","target":"Van","rounds_remaining":1}; before={pid:m["hp"] for pid,m in self.game.raid_roster.items()}; r=self.game.raid_round(); self.assertTrue(r.ok,r.messages); self.assertEqual(self.game.active_boss["last_mechanic"]["result"],"released"); self.assertTrue(all(self.game.raid_roster[pid]["hp"]<before[pid] for pid in before))
    def test_alpha5_plumes_clear_weakens_aerial_blast(self):
        self._start(); self.game.active_boss["attacks_per_round"]=0; self.game.active_boss["mechanic"]={"name":"Plume Squadron","kind":"adds","warning":"test","rounds_remaining":2,"required":2,"progress":0}; self.game.active_boss["adds"]=[{"id":"satin_plume","name":"Satin Plume","max_hp":1,"current_hp":1},{"id":"razor_plume","name":"Razor Plume","max_hp":1,"current_hp":1}]; r=self.game.raid_round(); self.assertTrue(r.ok,r.messages); self.assertEqual(self.game.active_boss["last_mechanic"]["name"],"Aerial Blast"); self.assertEqual(self.game.active_boss["last_mechanic"]["result"],"weakened")
    def test_alpha5_overlay_sanitizes_plume_ids(self):
        self._start(); self.game.active_boss["attacks_per_round"]=0; self.game.raid_round(); self.game.raid_round(); payload=self.game._overlay_payload(); self.assertEqual(payload["encounter_name"],"Eye of the Storm"); self.assertEqual(payload["mechanic"]["name"],"Plume Squadron"); self.assertEqual(set(payload["adds"][0]),{"name","hp","max_hp"}); encoded=json.dumps(payload); self.assertNotIn("satin_plume",encoded); self.assertNotIn("razor_plume",encoded)

if __name__=="__main__": unittest.main()

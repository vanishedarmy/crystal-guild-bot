from __future__ import annotations
import json, random, tempfile, unittest
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
ROOT=Path(__file__).resolve().parents[1]
class TrailsRaidsAlpha7Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=Database(Path(self.tmp.name)/"guild.db")
        self.game=CrystalGuildEngine(self.db,GameData(ROOT/"data"),raid_join_seconds=90,raid_round_seconds=60,rng=random.Random(1507))
        for pid,name,job in [("1","Van","warrior"),("2","Ari","monk"),("3","Mira","whitemage")]:
            self.game.recruit(pid,name.lower(),name); self.game.choose_job(pid,job); self.db.execute("UPDATE players SET level=70 WHERE twitch_id=?",(pid,)); self.game.choose_job(pid,job)
    def tearDown(self): self.db.close(); self.tmp.cleanup()
    def _start(self):
        self.assertTrue(self.game.spawn_boss("bahamut").ok)
        for pid in ("1","2","3"): self.assertTrue(self.game.raid_join(pid).ok)
        self.assertTrue(self.game.start_raid().ok); self.game.active_boss["current_hp"]=999999; self.game.active_boss["max_hp"]=999999
    def test_alpha7_bahamut_declares_final_coil(self):
        b=self.game.data.bosses["bahamut"]; self.assertEqual(b["tier"],"High Boss"); self.assertEqual(b["encounter_type"],"Trial"); self.assertEqual(b["encounter_name"],"The Final Coil"); self.assertEqual(b["raid_script"],"bahamut_final_coil"); self.assertEqual([m["name"] for m in b["mechanics"]],["Flare Breath","Akh Morn","Megaflare Towers","Teraflare Charge"]); self.assertEqual(self.game.data.validate(),[])
    def test_alpha7_cycle_reaches_megaflare_towers(self):
        self._start(); self.game.active_boss["attacks_per_round"]=0; self.assertEqual(self.game.active_boss["mechanic"]["name"],"Flare Breath"); self.game.raid_round(); self.assertEqual(self.game.active_boss["mechanic"]["name"],"Akh Morn"); self.game.raid_round(); self.assertEqual(self.game.active_boss["mechanic"]["name"],"Megaflare Towers")
    def test_alpha7_akh_morn_is_shared_by_defenders(self):
        self._start(); self.game.active_boss["attacks_per_round"]=3; self.game.active_boss["mechanic"]={"name":"Akh Morn","kind":"shared_hit","warning":"test","target_id":"1","target":"Van","rounds_remaining":1}; self.game.battle_defend("2"); self.game.battle_defend("3"); r=self.game.raid_round(); self.assertTrue(r.ok,r.messages); self.assertEqual(self.game.active_boss["last_mechanic"]["result"],"shared_3")
    def test_alpha7_megaflare_towers_reward_coordinated_defend(self):
        self._start(); self.game.active_boss["attacks_per_round"]=3; self.game.active_boss["mechanic"]={"name":"Megaflare Towers","kind":"tower_check","warning":"test","required":2,"progress":0,"rounds_remaining":1}; self.game.battle_defend("1"); self.game.battle_defend("2"); r=self.game.raid_round(); self.assertTrue(r.ok,r.messages); self.assertEqual(self.game.active_boss["last_mechanic"]["result"],"soaked")
    def test_alpha7_critical_hp_unlocks_teraflare(self):
        self._start(); b=self.game.active_boss; b["current_hp"]=25000; b["max_hp"]=100000; b["mechanic"]=None; m=self.game._bahamut_prepare_next_mechanic(b); self.assertEqual(m["name"],"Teraflare Charge"); self.assertEqual(m["kind"],"final_damage_check"); self.assertEqual(m["rounds_remaining"],3)
    def test_alpha7_overlay_sanitizes_internal_final_state(self):
        self._start(); payload=self.game._overlay_payload(); self.assertEqual(payload["encounter_name"],"The Final Coil"); encoded=json.dumps(payload); self.assertNotIn("target_id",encoded); self.assertNotIn("_bahamut",encoded)
if __name__=='__main__': unittest.main()

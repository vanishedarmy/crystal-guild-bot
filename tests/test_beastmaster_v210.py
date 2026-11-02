"""V2.10: Beastmaster persistence, ownership validation and Relic integration."""
from __future__ import annotations
import random
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.beastmaster import MAX_COMPANIONS, is_tameable
from crystal_guild.relic_live import damage_multiplier

ROOT=Path(__file__).resolve().parents[1]

class BeastmasterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=GameData(ROOT/'data')
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'player.sqlite'
        self.db=Database(self.path)
        self.game=CrystalGuildEngine(self.db,self.data,overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(9))
        self.game.recruit('b','beast','Beast')
        self.db.execute("UPDATE players SET level=99,current_job='beastmaster',current_hp=500 WHERE twitch_id='b'")
        self.db.execute("INSERT OR REPLACE INTO player_jobs(player_id,job_id,level,jp) VALUES ('b','beastmaster',99,0)")
        self.defeats('wolf',3)
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def defeats(self,monster_id,n=3):
        self.db.execute('INSERT INTO bestiary(player_id,monster_id,defeats) VALUES (?,?,?) ON CONFLICT(player_id,monster_id) DO UPDATE SET defeats=excluded.defeats',('b',monster_id,n))
    def count(self):
        return self.db.one("SELECT COUNT(*) AS n FROM beastmaster_companions WHERE player_id='b'")['n']
    def test_schema_migrates_and_enforces_one_active(self):
        self.assertGreaterEqual(self.db.schema_version(),29)
        self.game.tame_beast('b','wolf')
        self.defeats('coeurl')
        self.game.tame_beast('b','coeurl')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE beastmaster_companions SET active=1 WHERE player_id='b' AND monster_id='coeurl'")
    def test_tame_requires_real_verified_defeats(self):
        self.defeats('wolf',2)
        self.assertFalse(self.game.tame_beast('b','wolf').ok)
        self.assertEqual(self.count(),0)
        self.defeats('wolf',3)
        self.assertTrue(self.game.tame_beast('b','wolf').ok)
        self.assertEqual(self.count(),1)
        self.assertFalse(self.game.tame_beast('b','wolf').ok)
    def test_wrong_job_or_level_rejected(self):
        self.db.execute("UPDATE players SET current_job='paladin' WHERE twitch_id='b'")
        self.assertFalse(self.game.tame_beast('b','wolf').ok)
        self.db.execute("UPDATE players SET current_job='beastmaster' WHERE twitch_id='b'")
        self.db.execute("UPDATE player_jobs SET level=29 WHERE player_id='b' AND job_id='beastmaster'")
        self.assertFalse(self.game.tame_beast('b','wolf').ok)
        self.db.execute("UPDATE player_jobs SET level=30 WHERE player_id='b' AND job_id='beastmaster'")
        self.assertTrue(self.game.tame_beast('b','wolf').ok)
    def test_raid_boss_and_mark_never_tameable(self):
        self.assertFalse(is_tameable('mark_the_last_singularity',self.data.monsters))
        self.assertFalse(self.game.tame_beast('b','mark_the_last_singularity').ok)
        self.assertFalse(self.game.tame_beast('b','singularity_archon').ok)
        self.assertFalse(self.game.tame_beast('b','made_up_dragon').ok)
        self.assertEqual(self.count(),0)
    def test_roster_limit_and_selection(self):
        for name in ['wolf','coeurl','bat','cactuar','chimera']:
            self.defeats(name)
            self.assertTrue(self.game.tame_beast('b',name).ok,name)
        self.assertEqual(self.count(),MAX_COMPANIONS)
        self.defeats('mandragora')
        self.assertFalse(self.game.tame_beast('b','mandragora').ok)
        self.assertTrue(self.game.select_beast('b','chimera').ok)
        self.assertEqual(self.game._selected_tamed_companion('b')['monster_id'],'chimera')
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM beastmaster_companions WHERE player_id='b' AND active=1")['n'],1)
        self.assertTrue(self.game.release_beast('b','chimera').ok)
        self.assertEqual(self.count(),4)
        self.assertTrue(self.game.tame_beast('b','mandragora').ok)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM beastmaster_companions WHERE player_id='b' AND active=1")['n'],1)
    def test_nonowned_selection_and_release_rejected(self):
        self.assertFalse(self.game.select_beast('b','wolf').ok)
        self.assertFalse(self.game.release_beast('b','wolf').ok)
        self.assertEqual(self.count(),0)
    def test_restarts_preserve_ownership(self):
        self.game.tame_beast('b','wolf')
        self.db.close()
        self.db=Database(self.path)
        self.game=CrystalGuildEngine(self.db,self.data,overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(9))
        self.assertEqual(self.game._selected_tamed_companion('b')['monster_id'],'wolf')
        self.assertGreaterEqual(self.db.schema_version(),29)
    def test_wrong_job_no_companion_in_combat(self):
        self.game.tame_beast('b','wolf')
        p=self.game._player('b')
        self.db.execute("UPDATE players SET current_job='warrior' WHERE twitch_id='b'")
        self.game.encounter_roster={'b':{'name':'Beast','job_id':'warrior'}}
        self.game._initialize_active_combat({'kind':'venture','monster_id':'goblin'})
        self.assertIsNone(self.game.encounter_roster['b']['_tamed_companion'])
    def test_active_encounter_snapshot_from_owned_pet(self):
        self.game.tame_beast('b','wolf')
        self.game.encounter_roster={'b':{'name':'Beast','job_id':'beastmaster'}}
        self.game._initialize_active_combat({'kind':'venture','monster_id':'goblin'})
        self.assertEqual(self.game.encounter_roster['b']['_tamed_companion']['monster_id'],'wolf')
    def test_damage_without_owned_pet_never_gets_relic_trait(self):
        meta={'job_id':'beastmaster','relic_trait':{'key':'pack_coordination','value':0.30},
              'relic_signature':{'key':'alpha_pact','value':0.18}}
        self.assertEqual(damage_multiplier(meta,action='call_beast',boss=True),1.0)
        self.assertEqual(damage_multiplier(meta,action='king_of_beasts',boss=True),1.0)
        meta['_tamed_companion']={'monster_id':'wolf','name':'Wolf','level':2}
        self.assertGreater(damage_multiplier(meta,action='call_beast',boss=True),1.50)
        self.assertEqual(damage_multiplier(meta,action='attack',boss=True),1.0)
    def test_pet_bonus_clamped(self):
        meta={'job_id':'beastmaster','_tamed_companion':{'monster_id':'wolf','level':10_000}}
        self.assertLessEqual(damage_multiplier(meta,action='call_beast'),1.08)
    def test_raid_snapshot_and_damage(self):
        self.game.tame_beast('b','wolf')
        self.game.raid_roster={'b':{'name':'Beast','job_id':'beastmaster'}}
        self.game.active_boss={'id':'goblin','state':'combat','statuses':{},'current_hp':10000,'max_hp':10000}
        self.game._initialize_raid_combat()
        meta=self.game.raid_roster['b']
        self.assertEqual(meta['_tamed_companion']['monster_id'],'wolf')
        meta['relic_trait']={'key':'pack_coordination','value':0.30}
        meta['relic_signature']={'key':'alpha_pact','value':0.18}
        baseline={**meta,'_tamed_companion':None}
        with patch.object(self.game.rng,'uniform',return_value=1.2):
            ordinary=self.game._raid_base_damage(baseline,relic_action='call_beast')
            empowered=self.game._raid_base_damage(meta,relic_action='call_beast')
        self.assertGreater(empowered,ordinary)
    def test_regular_attack_unchanged(self):
        self.game.tame_beast('b','wolf')
        meta={'job_id':'beastmaster','_tamed_companion':self.game._selected_tamed_companion('b'),
              'relic_trait':{'key':'pack_coordination','value':0.30}, 'relic_signature':{'key':'alpha_pact','value':0.18}}
        self.assertEqual(damage_multiplier(meta,action=''),1.0)
    def test_foreign_key_cascade_on_player_delete(self):
        self.game.tame_beast('b','wolf')
        self.db.execute("DELETE FROM players WHERE twitch_id='b'")
        self.assertEqual(self.count(),0)
    def test_schema_v28_to_v29_preserves_existing_tables(self):
        self.db.execute("INSERT INTO blue_magic_memories(player_id,ability_id,monster_id) VALUES ('b','aqua_breath','chimera')")
        self.db.close()
        self.db=Database(self.path)
        self.assertGreaterEqual(self.db.schema_version(),29)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM blue_magic_memories WHERE player_id='b'"))

if __name__=='__main__':unittest.main()

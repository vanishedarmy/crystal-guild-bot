"""V2.9 real Bot tests for authenticated, receipt-protected Thief Mug loot."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]

class MugStealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=GameData(ROOT/'data')
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'bot.sqlite'
        self.db=Database(self.path)
        self.engine=CrystalGuildEngine(self.db,self.data,overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(3))
        self.engine.recruit('1','thief','Thief')
        self.db.execute("UPDATE players SET level=99,current_job='thief' WHERE twitch_id='1'")
        self.db.execute("UPDATE equipment SET weapon_id='ultimate_thief_eternal' WHERE player_id='1'")
        self.actor=self._actor()
        self.engine.active_encounter={'id':99,'state':'combat','moment_run_key':'encounter-x','monster_hp':2000,'monster_max_hp':2000,'monster_statuses':{}}
        self.engine.encounter_roster={'1':self.actor}
        self.monster=self.data.monsters['goblin']
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def _actor(self):
        traits=self.engine._equipment_traits(self.engine._player('1'),self.data.jobs['thief'])
        return {'name':'Thief','job_id':'thief','hp':500,'max_hp':500,'ap':250,'max_ap':250,'mp':100,'max_mp':100,
                'stats':{'str':100,'dex':70,'lck':30,'mag':25,'spr':30,'attack':150,'magic_power':20},'effects':{},
                'statuses':{},'abilities_used':0,'damage':0,'best_hit':0,'healing':0,**traits}
    def qty(self,id):
        row=self.db.one('SELECT quantity FROM inventory WHERE player_id=? AND item_id=?',('1',id))
        return int(row['quantity']) if row else 0
    def test_mug_steals_and_records_once(self):
        with patch.object(self.engine.rng,'random',return_value=0.0):
            note=self.engine._try_relic_mug_steal('1',self.actor,self.monster)
            self.assertIn('Steal:', note)
        receipt=self.db.one('SELECT item_id FROM relic_steal_attempts WHERE player_id=?',('1',))
        self.assertTrue(receipt['item_id'])
        item=receipt['item_id'];old=self.qty(item)
        self.assertEqual(self.engine._try_relic_mug_steal('1',self.actor,self.monster),'')
        self.assertEqual(self.qty(item),old)
        self.assertEqual(len(self.db.all("SELECT * FROM transactions WHERE source LIKE 'mug:%'")),1)
    def test_failed_roll_consumes_attempt(self):
        with patch.object(self.engine.rng,'random',return_value=0.99):
            self.assertIn('no item',self.engine._try_relic_mug_steal('1',self.actor,self.monster))
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.assertEqual(self.engine._try_relic_mug_steal('1',self.actor,self.monster),'')
        self.assertEqual(self.db.one('SELECT succeeded FROM relic_steal_attempts WHERE player_id=?',('1',))['succeeded'],0)
    def test_no_reward_if_wrong_job_or_unverified_roster(self):
        self.actor['job_id']='paladin'
        self.assertEqual(self.engine._try_relic_mug_steal('1',self.actor,self.monster),'')
        self.actor['job_id']='thief'
        self.engine.encounter_roster['1']={}
        self.assertEqual(self.engine._try_relic_mug_steal('1',self.actor,self.monster),'')
        self.assertEqual(len(self.db.all('SELECT * FROM relic_steal_attempts')),0)
    def test_boss_premium_items_never_stolen(self):
        monster={'id':'premium','drops':[{'item_id':'ultimate_thief_eternal','chance':1}, {'item_id':'goblin_medallion','chance':.2}]}
        with patch.object(self.engine.rng,'random',return_value=0.0):
            result=self.engine._try_relic_mug_steal('1',self.actor,monster)
        self.assertIn('Steal:',result)
        self.assertEqual(self.qty('ultimate_thief_eternal'),0)
        self.assertEqual(self.qty('goblin_medallion'),1)
    def test_live_active_mug_trigger_not_ordinary_damage(self):
        ability=next(x for x in self.data.active_abilities['thief'] if x['id']=='mug')
        with patch.object(self.engine,'_basic_active_damage',return_value=(100,False)):
            with patch.object(self.engine.rng,'random',return_value=0.0):
                messages=[]
                self.engine._resolve_active_ability(self.actor,{'ability_id':'mug','target_id':'monster'},self.monster,messages)
        self.assertEqual(len(self.db.all('SELECT * FROM relic_steal_attempts')),1)
        self.assertTrue(any('Steal:' in msg for msg in messages), messages)
    def test_missing_damage_does_not_roll(self):
        with patch.object(self.engine,'_basic_active_damage',return_value=(0,False)):
            self.engine._resolve_active_ability(self.actor,{'ability_id':'mug','target_id':'monster'},self.monster,[])
        self.assertEqual(len(self.db.all('SELECT * FROM relic_steal_attempts')),0)
    def test_successful_receipt_survives_restart(self):
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.engine._try_relic_mug_steal('1',self.actor,self.monster)
        self.db.close()
        self.db=Database(self.path)
        self.engine=CrystalGuildEngine(self.db,self.data,overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(3))
        self.engine.encounter_roster={'1':self.actor}
        self.engine.active_encounter={'id':99,'state':'combat','moment_run_key':'encounter-x'}
        before=len(self.db.all("SELECT * FROM transactions WHERE source LIKE 'mug:%'"))
        self.assertEqual(self.engine._try_relic_mug_steal('1',self.actor,self.monster),'')
        self.assertEqual(len(self.db.all("SELECT * FROM transactions WHERE source LIKE 'mug:%'")),before)
    def test_rollback_rolls_back_receipt(self):
        self.db.execute("CREATE TRIGGER fail_steal BEFORE INSERT ON inventory BEGIN SELECT RAISE(ABORT,'write failed'); END")
        with patch.object(self.engine.rng,'random',return_value=0.0):
            with self.assertRaises(Exception):self.engine._try_relic_mug_steal('1',self.actor,self.monster)
        self.assertEqual(len(self.db.all('SELECT * FROM relic_steal_attempts')),0)
    def test_raid_server_monster_data_and_once_per_instance(self):
        self.engine.active_boss={'id':'goblin','raid_instance_id':'raid-1','state':'combat','drops':self.monster['drops'],
                                  'current_hp':10000,'max_hp':10000,'statuses':{},'round':1}
        self.engine.raid_roster={'1':self.actor}
        self.actor['ap']=300;self.actor['max_ap']=300
        with patch.object(self.engine,'_raid_base_damage',return_value=100):
            with patch.object(self.engine.rng,'random',return_value=0.0):
                logs=[]
                self.engine._resolve_raid_ability('1',self.actor,{'ability_id':'mug','target_id':'boss'},0.0,[],logs)
                self.engine._resolve_raid_ability('1',self.actor,{'ability_id':'mug','target_id':'boss'},0.0,[],logs)
        self.assertEqual(len(self.db.all('SELECT * FROM relic_steal_attempts')),1)
        self.assertEqual(len(self.db.all("SELECT * FROM transactions WHERE source LIKE 'mug:%'")),1)
    def test_non_eligible_loot_consumes_attempt_safely(self):
        monster={'id':'premium','drops':[{'item_id':'ultimate_thief_eternal','chance':1}]}
        note=self.engine._try_relic_mug_steal('1',self.actor,monster)
        self.assertIn('no item',note)
        self.assertEqual(self.qty('ultimate_thief_eternal'),0)
    def test_migration_applies_to_existing_db(self):
        version=self.db.one('SELECT MAX(version) AS v FROM schema_migrations')['v']
        self.assertGreaterEqual(version,28)

class BlueMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=GameData(ROOT/'data')
    def setUp(self):
        self._actor=lambda: MugStealTests._actor(self)
        MugStealTests.setUp(self)
        self.db.execute("UPDATE players SET current_job='bluemage' WHERE twitch_id='1'")
        self.db.execute("UPDATE equipment SET weapon_id='ultimate_bluemage_eternal' WHERE player_id='1'")
        traits=self.engine._equipment_traits(self.engine._player('1'), self.data.jobs['bluemage'])
        self.actor.update(traits)
        self.actor['job_id']='bluemage'
        self.actor['job_level']=99
    def tearDown(self):
        MugStealTests.tearDown(self)
    def test_real_enemy_skill_mastery_stored(self):
        enemy=self.data.monsters['chimera']
        special=self.data.enemy_actions['chimera']['ability']
        with patch.object(self.engine.rng,'random',return_value=0.0):
            log=[];self.engine._observe_blue_enemy_ability(enemy,special,log)
        self.assertIn('aqua_breath',self.engine._blue_memory_ids('1'))
        self.assertIn('aqua_breath',self.actor['_blue_memories'])
        self.assertTrue(any('Aqua Breath' in line for line in log))
    def test_no_duplicate_or_client_noncanonical_spells(self):
        enemy=self.data.monsters['chimera'];special=self.data.enemy_actions['chimera']['ability']
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.engine._observe_blue_enemy_ability(enemy,special,[])
            self.engine._observe_blue_enemy_ability(enemy,special,[])
            self.engine._observe_blue_enemy_ability(enemy,{'id':'made_up','name':'Made Up'},[])
        self.assertEqual(len(self.db.all('SELECT * FROM blue_magic_memories')),1)
    def test_cactuar_maps_needles(self):
        enemy=self.data.monsters['cactuar'];special=self.data.enemy_actions['cactuar']['ability']
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.engine._observe_blue_enemy_ability(enemy,special,[])
        self.assertIn('thousand_needles',self.engine._blue_memory_ids('1'))
    def test_no_mastery_before_level_or_for_nonblue(self):
        enemy=self.data.monsters['chimera'];special=self.data.enemy_actions['chimera']['ability']
        self.actor['job_level']=1
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.engine._observe_blue_enemy_ability(enemy,special,[])
        self.assertEqual(self.engine._blue_memory_ids('1'),[])
        self.actor['job_level']=99;self.actor['job_id']='paladin'
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.engine._observe_blue_enemy_ability(enemy,special,[])
        self.assertEqual(self.engine._blue_memory_ids('1'),[])
    def test_failed_memory_roll_only_once_per_battle(self):
        enemy=self.data.monsters['chimera'];special=self.data.enemy_actions['chimera']['ability']
        with patch.object(self.engine.rng,'random',return_value=0.999):
            self.engine._observe_blue_enemy_ability(enemy,special,[])
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.engine._observe_blue_enemy_ability(enemy,special,[])
        self.assertEqual(self.engine._blue_memory_ids('1'),[])
        self.actor['_blue_observed_attempts']=[]
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.engine._observe_blue_enemy_ability(enemy,special,[])
        self.assertEqual(self.engine._blue_memory_ids('1'),['aqua_breath'])
    def test_enemy_cast_path_triggers_memory(self):
        enemy=self.data.monsters['chimera'];special=self.data.enemy_actions['chimera']['ability']
        profile=self.data.enemy_profiles['caster']
        self.engine.active_encounter.update({'monster_hp':2000,'monster_max_hp':2000,'monster_statuses':{}})
        self.actor.update({'hp':500,'max_hp':500,'statuses':{},'damage_taken':0,'limit':0,'effects':{}})
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.engine._resolve_enemy_special(enemy,profile,special,[])
        self.assertEqual(self.engine._blue_memory_ids('1'),['aqua_breath'])
    def test_mastery_damage_bonus_is_only_on_matching_skill(self):
        from crystal_guild.relic_live import damage_multiplier
        actor=dict(self.actor)
        actor['_blue_memories']=[]
        before=damage_multiplier(actor, action='aqua_breath')
        actor['_blue_memories']=['aqua_breath']
        after=damage_multiplier(actor, action='aqua_breath')
        self.assertAlmostEqual(after/before,1.05)
        self.assertAlmostEqual(damage_multiplier(actor,action='goblin_punch'),damage_multiplier(dict(actor,_blue_memories=[]),action='goblin_punch'))
    def test_memory_persists_database_reopen(self):
        enemy=self.data.monsters['chimera'];special=self.data.enemy_actions['chimera']['ability']
        with patch.object(self.engine.rng,'random',return_value=0.0):
            self.engine._observe_blue_enemy_ability(enemy,special,[])
        self.db.close();self.db=Database(self.path)
        self.engine=CrystalGuildEngine(self.db,self.data,overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(5))
        self.assertEqual(self.engine._blue_memory_ids('1'),['aqua_breath'])

if __name__=='__main__':unittest.main()

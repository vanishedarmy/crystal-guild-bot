"""V2.8 active and raid tests against real Crystal Guild Python combat paths."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.relic_live import monk_combo_hit, relic_guard_hit, damage_multiplier

ROOT=Path(__file__).resolve().parents[1]

class RelicV28Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=GameData(ROOT/'data')
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.db=Database(Path(self.tmp.name)/'bot.sqlite')
  self.engine=CrystalGuildEngine(self.db,self.data,overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(32))
  self.engine.recruit('1','tester','Tester')
  self.db.execute("UPDATE players SET level=99,gil=100000,current_job='paladin' WHERE twitch_id='1'")
 def tearDown(self):
  self.db.close();self.tmp.cleanup()
 def actor(self,job,weapon):
  self.db.execute('UPDATE players SET current_job=? WHERE twitch_id=?',(job,'1'))
  self.db.execute('UPDATE equipment SET weapon_id=? WHERE player_id=?',(weapon,'1'))
  traits=self.engine._equipment_traits(self.engine._player('1'),self.data.jobs[job])
  return dict(name='Tester',job_id=job,stats={'str':50,'vit':50,'spr':40,'dex':40,'lck':30,'attack':150,'mag':50,'magic_power':40},effects={},stance='balanced',hp=600,max_hp=600,ap=50,max_ap=100,mp=100,max_mp=100,statuses={},damage=0,healing=0,damage_taken=0,best_hit=0,abilities_used=0,**traits)
 def test_monk_three_hits_and_ap_cap(self):
  monk=self.actor('monk','ultimate_monk_eternal')
  self.assertEqual(monk['relic_trait']['value'],6)
  self.assertEqual([monk_combo_hit(monk,40),monk_combo_hit(monk,41),monk_combo_hit(monk,42)],[0,0,6])
  self.assertEqual(monk['ap'],56)
  monk['ap']=99
  for _ in range(2):self.assertEqual(monk_combo_hit(monk,20),0)
  self.assertEqual(monk_combo_hit(monk,20),1)
  self.assertEqual(monk['ap'],100)
 def test_monk_miss_resets_chain_and_finisher_only_third(self):
  m=self.actor('monk','ultimate_monk_eternal')
  self.assertEqual(monk_combo_hit(m,50),0)
  self.assertEqual(monk_combo_hit(m,0),0)
  self.assertEqual(m['_relic_monk_combo_count'],0)
  self.assertEqual(damage_multiplier(m,action='phantom_rush'),1)
  monk_combo_hit(m,20); monk_combo_hit(m,20)
  self.assertGreater(damage_multiplier(m,action='phantom_rush'),1)
  self.assertEqual(damage_multiplier(m,action='bootshine'),1)
 def test_non_relic_monk_and_wrong_job_no_ap(self):
  m=self.actor('monk','ultimate_monk_eternal')
  m['relic_trait']=None
  for _ in range(3):self.assertEqual(monk_combo_hit(m,100),0)
  m=self.actor('paladin','ultimate_paladin_eternal')
  for _ in range(3):self.assertEqual(monk_combo_hit(m,100),0)
 def test_monk_active_basic_ap_after_third_hit(self):
  m=self.actor('monk','ultimate_monk_eternal')
  self.engine.encounter_roster={'1':m}
  self.engine.active_encounter={'kind':'venture','round':1,'monster_hp':100000,'monster_max_hp':100000,'monster_statuses':{}}
  monster={'id':'test','name':'Foe','attack':30,'defense':10,'spirit':10}
  with patch.object(self.engine,'_basic_active_damage',return_value=(100,False)):
   logs=[]
   for _ in range(3):self.engine._resolve_active_attack(m,monster,logs)
  self.assertEqual(m['ap'],56)
  self.assertTrue(any('COMBO +6 AP' in msg for msg in logs))
 def test_monk_raid_basic_damage_counts_three_hits(self):
  m=self.actor('monk','ultimate_monk_eternal')
  self.engine.raid_roster={'1':m}
  self.engine.active_boss={'id':'test','name':'Foe','current_hp':100000,'max_hp':100000,'status':{},'statuses':{},'round':0}
  with patch.object(self.engine,'_raid_base_damage',return_value=100):
   messages=[self.engine._raid_basic_attack('1',m,0.0,[]) for _ in range(3)]
  self.assertEqual(m['ap'],56)
  self.assertEqual([m[0] for m in messages],[100,100,100])
  self.assertIn('COMBO +6 AP',messages[2][1])
 def test_paladin_raid_cover_arms_and_scripted_hit_consumes(self):
  pal=self.actor('paladin','ultimate_paladin_eternal')
  ally=dict(name='Ally',job_id='warrior',hp=300,max_hp=300,statuses={})
  self.engine.raid_roster={'1':pal,'2':ally}
  self.engine.active_boss={'id':'test','name':'Boss','current_hp':20000,'max_hp':20000,'statuses':{},'round':1}
  pal['ap']=200;pal['max_ap']=200;pal['mp']=200;pal['max_mp']=200
  self.engine._resolve_raid_ability('1',pal,{'ability_id':'cover','target_id':'2'},0.0,[],[])
  self.assertAlmostEqual(pal.get('_relic_cover_guard_ready',0),0.30)
  self.assertEqual(pal.get('_relic_reprisal_ready',False),False)
  self.engine._raid_apply_scripted_hit('1',raw=200,ko_names=[])
  self.assertNotIn('_relic_cover_guard_ready',pal)
  self.assertTrue(pal.get('_relic_reprisal_ready'))
  self.assertEqual(relic_guard_hit(pal,100),100)
 def test_raid_unequipped_cover_not_armed(self):
  pal=self.actor('paladin','ultimate_paladin_eternal')
  pal['relic_trait']=None;pal['relic_signature']=None
  ally=dict(name='Ally',job_id='warrior',hp=300,max_hp=300,statuses={})
  self.engine.raid_roster={'1':pal,'2':ally}
  self.engine.active_boss={'id':'test','name':'Boss','current_hp':20000,'max_hp':20000,'statuses':{},'round':1}
  pal['ap']=200;pal['max_ap']=200;pal['mp']=200;pal['max_mp']=200
  self.engine._resolve_raid_ability('1',pal,{'ability_id':'cover','target_id':'2'},0.0,[],[])
  self.assertNotIn('_relic_cover_guard_ready',pal)
 def test_no_reprisal_if_protected_hit_kos_paladin(self):
  pal=self.actor('paladin','ultimate_paladin_eternal')
  pal['_relic_cover_guard_ready']=0.3;pal['hp']=50
  self.assertEqual(relic_guard_hit(pal,200),140)
  self.assertFalse(pal.get('_relic_reprisal_ready',False))
 def test_raid_reprisal_on_next_basic_only(self):
  pal=self.actor('paladin','ultimate_paladin_eternal')
  pal['_relic_reprisal_ready']=True
  self.engine.active_boss={'id':'test','name':'Boss','current_hp':5000,'max_hp':5000,'statuses':{},'round':1}
  with patch.object(self.engine,'_raid_base_damage',return_value=100):
   first,suffix=self.engine._raid_basic_attack('1',pal,0.0,[])
   second,second_suffix=self.engine._raid_basic_attack('1',pal,0.0,[])
  self.assertEqual((first,second),(118,100))
  self.assertIn('AEGIS REPRISAL',suffix)
  self.assertNotIn('AEGIS REPRISAL',second_suffix)
  self.assertFalse(pal.get('_relic_reprisal_ready',False))
  self.assertEqual(self.engine.active_boss['current_hp'],4782)

 def test_monk_active_abilities_restore_only_on_third_verified_hit(self):
  monk=self.actor('monk','ultimate_monk_eternal')
  monk['ap']=180;monk['max_ap']=200
  self.engine.encounter_roster={'1':monk}
  self.engine.active_encounter={'kind':'venture','round':1,'monster_hp':100000,'monster_max_hp':100000,'monster_statuses':{}}
  monster={'id':'test','name':'Foe','attack':30,'defense':10,'spirit':10}
  from crystal_guild.active_battle import ability_cost
  ability=next(x for x in self.data.active_abilities['monk'] if x['id']=='bootshine')
  cost=ability_cost(ability)
  with patch.object(self.engine,'_basic_active_damage',return_value=(100,False)):
   logs=[]
   for _ in range(3): self.engine._resolve_active_ability(monk,{'ability_id':'bootshine','target_id':'monster'},monster,logs)
  self.assertEqual(monk['ap'],180-3*cost+6)
  self.assertTrue(any('Combo Momentum +6 AP' in msg for msg in logs))

 def test_monk_raid_abilities_restore_ap_once_per_three_hits(self):
  monk=self.actor('monk','ultimate_monk_eternal')
  monk['ap']=180;monk['max_ap']=200
  self.engine.raid_roster={'1':monk}
  self.engine.active_boss={'id':'test','name':'Foe','current_hp':100000,'max_hp':100000,'statuses':{},'round':1}
  from crystal_guild.active_battle import ability_cost
  cost=ability_cost(next(x for x in self.data.active_abilities['monk'] if x['id']=='bootshine'))
  with patch.object(self.engine,'_raid_base_damage',return_value=100):
   logs=[]
   for _ in range(3):self.engine._resolve_raid_ability('1',monk,{'ability_id':'bootshine','target_id':'boss'},0.0,[],logs)
  self.assertEqual(monk['ap'],180-3*cost+6)
  self.assertTrue(any('Combo Momentum +6 AP' in msg for msg in logs))

if __name__=='__main__':unittest.main()

"""V2.7 regression coverage for new real-Bot crafting and Paladin hooks."""
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


class NewLiveHooksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GameData(ROOT / 'data')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'bot.sqlite')
        self.engine = CrystalGuildEngine(self.db, self.data, overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'), rng=random.Random(17))
        self.engine.recruit('1', 'maker', 'Maker')
        self.engine.choose_job('1', 'paladin')
        self.db.execute('UPDATE players SET level=99,gil=100000,hunt_seals=1000,current_job=? WHERE twitch_id=?', ('paladin', '1'))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def prepare_recipe(self, hammer=True):
        self.db.execute('UPDATE equipment SET accessory_id=? WHERE player_id=?', ('artisan_hammer' if hammer else None, '1'))
        recipe = self.data.recipes['antidote_satchel']
        for m in recipe['materials']:
            self.engine._change_item('1',m['item_id'],m['quantity']*3,'test_seed')
        return recipe

    def test_hammer_salvages_one_verified_material_and_records_receipt(self):
        r = self.prepare_recipe()
        before = self.engine._inventory_qty('1','wolf_fang')
        with patch.object(self.engine.rng, 'random', return_value=0.0):
            done = self.engine.portal_craft_recipe('1',r['id'],2,'hammer-1')
        self.assertTrue(done.ok,done.messages)
        self.assertEqual(done.data['craft_bonus'], {'item_id':'wolf_fang','name':'Wolf Fang','quantity':1})
        self.assertEqual(self.engine._inventory_qty('1','wolf_fang'),before-2+1)
        logs = self.db.all("SELECT asset_id,amount,source FROM transactions WHERE source LIKE 'craft_bonus:%'")
        self.assertEqual(len(logs),1)
        self.assertEqual((logs[0]['asset_id'],logs[0]['amount']),('wolf_fang',1))
        replay = self.engine.portal_craft_recipe('1',r['id'],2,'hammer-1')
        self.assertTrue(replay.ok)
        self.assertEqual(self.engine._inventory_qty('1','wolf_fang'),before-2+1)
        self.assertEqual(len(self.db.all("SELECT * FROM transactions WHERE source LIKE 'craft_bonus:%'")),1)

    def test_hammer_not_equipped_or_not_level_eligible(self):
        r=self.prepare_recipe(hammer=False)
        with patch.object(self.engine.rng,'random',return_value=0.0):
            done=self.engine.portal_craft_recipe('1',r['id'],1,'hammer-unequipped')
        self.assertTrue(done.ok)
        self.assertIsNone(done.data['craft_bonus'])
        self.db.execute('UPDATE equipment SET accessory_id=? WHERE player_id=?',('artisan_hammer','1'))
        self.db.execute('UPDATE players SET level=20 WHERE twitch_id=?',('1',))
        with patch.object(self.engine.rng,'random',return_value=0.0):
            done=self.engine.portal_craft_recipe('1',r['id'],1,'hammer-underlevel')
        self.assertTrue(done.ok)
        self.assertIsNone(done.data['craft_bonus'])

    def test_no_bonus_on_unlucky_roll_or_failed_craft(self):
        r=self.prepare_recipe()
        with patch.object(self.engine.rng,'random',return_value=0.95):
            done=self.engine.portal_craft_recipe('1',r['id'],1,'hammer-fail-roll')
        self.assertTrue(done.ok)
        self.assertIsNone(done.data['craft_bonus'])
        self.db.execute("DELETE FROM inventory WHERE player_id='1' AND item_id='wolf_fang'")
        with patch.object(self.engine.rng,'random',return_value=0.0):
            failed=self.engine.portal_craft_recipe('1',r['id'],1,'hammer-not-enough')
        self.assertFalse(failed.ok)
        self.assertEqual(len(self.db.all("SELECT * FROM transactions WHERE source LIKE 'craft_bonus:%'")),0)

    def test_failed_bonus_write_rolls_back_full_craft_and_does_not_stamp_receipt(self):
        r=self.prepare_recipe()
        before_gil=int(self.engine._player('1')['gil'])
        before_material=self.engine._inventory_qty('1','wolf_fang')
        before_output=self.engine._inventory_qty('1','antidote')
        with patch.object(self.engine.rng,'random',return_value=0.0), patch.object(self.engine.rng,'choice',side_effect=RuntimeError('simulated interrupted craft')):
            with self.assertRaisesRegex(RuntimeError, 'interrupted craft'):
                self.engine.portal_craft_recipe('1',r['id'],1,'craft-rollback')
        self.assertEqual(int(self.engine._player('1')['gil']),before_gil)
        self.assertEqual(self.engine._inventory_qty('1','wolf_fang'),before_material)
        self.assertEqual(self.engine._inventory_qty('1','antidote'),before_output)
        self.assertIsNone(self.engine._portal_action_replay('craft-rollback'))

    def test_artisan_does_not_salvage_rare_quest_materials(self):
        from crystal_guild.relic_live import artisan_salvage_candidates
        rows=[{'item_id':'omega_core','quantity':2},{'item_id':'wolf_fang','quantity':1},
              {'item_id':'potion','quantity':1}]
        self.assertEqual(artisan_salvage_candidates({'materials': rows},self.data.items), ['wolf_fang'])
        self.assertEqual(artisan_salvage_candidates({'materials': [rows[0]]},self.data.items), [])

    def paladin_fixture(self, with_relic=True):
        if with_relic:
            self.db.execute('UPDATE equipment SET weapon_id=? WHERE player_id=?',('ultimate_paladin_eternal','1'))
        else:
            self.db.execute('UPDATE equipment SET weapon_id=NULL WHERE player_id=?',('1',))
        t=self.engine._equipment_traits(self.engine._player('1'),self.data.jobs['paladin'])
        actor={'name':'Paladin','job_id':'paladin','stats':{'str':50,'vit':50,'spr':50,'dex':30,'lck':30,'attack':150,'mag':30,'magic_power':30},
            'effects':{}, 'stance':'balanced','hp':500,'max_hp':500, 'ap':200,'max_ap':200, 'mp':0,'max_mp':0,
            'statuses':{},'damage':0,'healing':0,'damage_taken':0,'best_hit':0,'abilities_used':0, **t}
        ally={'name':'Ally','job_id':'warrior','hp':250,'max_hp':250,'statuses':{}}
        self.engine.encounter_roster={'1':actor, '2':ally}
        self.engine.active_encounter={'kind':'venture','round':1,'monster_hp':2000,'monster_max_hp':2000,'monster_statuses':{}}
        self.engine.rng.uniform = lambda low, high: 1.0
        self.engine.rng.random = lambda: 0.99
        monster={'attack':140,'defense':5,'spirit':5,'name':'Boss','id':'test-boss'}
        return actor,ally,monster

    def test_cover_arms_sacred_guard_only_with_relic_and_ally(self):
        pal,ally,m=self.paladin_fixture()
        self.engine._resolve_active_ability(pal,{'ability_id':'cover','target_id':'2'},m,[])
        self.assertAlmostEqual(pal['_relic_cover_guard_ready'],0.30)
        self.assertIn('protect',ally['statuses'])
        pal,ally,m=self.paladin_fixture(with_relic=False)
        self.engine._resolve_active_ability(pal,{'ability_id':'cover','target_id':'2'},m,[])
        self.assertNotIn('_relic_cover_guard_ready',pal)

    def test_guard_consumes_only_on_real_hit_then_arms_reprisal(self):
        pal,ally,m=self.paladin_fixture()
        self.engine._resolve_active_ability(pal,{'ability_id':'cover','target_id':'2'},m,[])
        no_guard=dict(pal)
        no_guard['statuses'] = dict(pal['statuses'])
        no_guard.pop('_relic_cover_guard_ready',None)
        base=self.engine._enemy_damage_against(m,no_guard,{},power=1.0)
        self.assertGreater(base,0)
        self.engine._apply_enemy_hit(m,pal,{},scaling='physical',power=1.0)
        self.assertEqual(pal['hp'], 500-max(1,int(base*0.70)))
        self.assertTrue(pal.get('_relic_reprisal_ready'))
        self.assertNotIn('_relic_cover_guard_ready',pal)
        with patch.object(self.engine,'_basic_active_damage',return_value=(100,False)):
            log=[]
            self.engine._resolve_active_attack(pal,m,log)
            self.assertEqual(self.engine.active_encounter['monster_hp'],1882)
            self.assertIn('AEGIS REPRISAL',' '.join(log))
            self.engine._resolve_active_attack(pal,m,log)
            self.assertEqual(self.engine.active_encounter['monster_hp'],1782)

    def test_evaded_hit_does_not_spend_guard(self):
        pal,ally,m=self.paladin_fixture()
        pal['_relic_cover_guard_ready']=0.30
        pal['effects']['evade_chance']=1.0
        self.engine.rng.random=lambda:0.0
        self.assertEqual(self.engine._enemy_damage_against(m,pal,{},power=1.0),0)
        self.assertEqual(pal['_relic_cover_guard_ready'],0.30)
        self.assertNotIn('_relic_reprisal_ready',pal)

if __name__ == '__main__':unittest.main()

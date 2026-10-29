"""v1.9.94: battle recovery, World Event rewards and revival audit."""
from __future__ import annotations
import random
import tempfile
import time
import unittest
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine, WORLD_EVENT_TREASURE

ROOT = Path(__file__).resolve().parents[1]

class BattleRewards1994Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / 'game.db')
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / 'data'), rng=random.Random(1994), overlay_state_path=str(Path(self.temp.name) / 'overlay.json'))
        for pid, username, job in [('101','alex','warrior'), ('102','bea','whitemage')]:
            self.assertTrue(self.game.recruit(pid, username, username.title()).ok)
            self.assertTrue(self.game.choose_job(pid, job).ok)
            self.db.execute('UPDATE players SET level=65 WHERE twitch_id=?', (pid,))

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_every_usable_consumable_effect_is_known_and_well_formed(self):
        items = list(self.game.data.items.values())
        self.assertEqual(len([item for item in items if item.get('type') == 'consumable']), 34)
        types = {'heal_hp','restore_mp','restore_ap','revive','cleanse','status','damage','open_cache'}
        for item in items:
            use = item.get('use')
            if item.get('type') != 'consumable' or not use:
                continue
            with self.subTest(item=item['id']):
                self.assertIn(use.get('target'), {'self','ally','party','enemy'})
                self.assertTrue(use.get('effects'))
                for effect in use['effects']:
                    self.assertIn(effect['type'], types)
                    if effect['type'] in {'heal_hp','restore_mp','restore_ap','revive'}:
                        self.assertTrue(effect.get('amount',0)>0 or effect.get('fraction',0)>0)
                    if effect['type'] == 'cleanse':
                        self.assertTrue(effect.get('statuses') or effect.get('all_harmful'))
                    if effect['type'] == 'damage':
                        self.assertGreater(effect.get('amount',0),0)

    def test_megalixir_fully_restores_all_living_allies_in_active_battle(self):
        actor = {'name':'Alex','hp':1,'max_hp':333,'mp':2,'max_mp':72,'ap':0,'max_ap':0,'healing':0,'items_used':0,'statuses':{}}
        ally = {'name':'Bea','hp':15,'max_hp':800,'mp':0,'max_mp':202,'ap':4,'max_ap':60,'statuses':{}}
        self.game.active_encounter = {'state':'combat','round':1}
        self.game.encounter_roster = {'101':actor,'102':ally}
        self.game._change_item('101','megalixir',1,'test')
        logs = []
        self.game._resolve_active_item('101', actor, {'item_id':'megalixir','target_id':'party'}, logs)
        self.assertEqual((actor['hp'],actor['mp']),(333,72))
        self.assertEqual((ally['hp'],ally['mp'],ally['ap']),(800,202,60))
        self.assertEqual(self.game._inventory_qty('101','megalixir'),0)
        self.assertIn('FULL HP at item resolution',' '.join(logs))

    def test_megalixir_fully_restores_raid_roster(self):
        actor = {'name':'Alex','hp':1,'max_hp':300,'mp':0,'max_mp':0,'ap':0,'max_ap':90,'healing':0,'items_used':0,'statuses':{}}
        ally = {'name':'Bea','hp':8,'max_hp':700,'mp':1,'max_mp':220,'ap':0,'max_ap':0,'statuses':{}}
        self.game.raid_roster = {'101':actor,'102':ally}
        self.game._change_item('101','megalixir',1,'test')
        logs = []
        self.game._resolve_raid_item('101',actor,{'item_id':'megalixir','target_id':'party'},[],logs)
        self.assertEqual((actor['hp'],actor['ap']),(300,90))
        self.assertEqual((ally['hp'],ally['mp']),(700,220))
        self.assertEqual(self.game._inventory_qty('101','megalixir'),0)

    def test_revive_command_in_venture_and_world_event(self):
        for kind in ('venture','world_event'):
            with self.subTest(kind=kind):
                self.game.active_encounter = {'id':123,'kind':kind,'state':'combat','round':1,'next_round_at':time.time()+90}
                self.game.encounter_roster = {
                    '101':{'name':'Alex','username':'alex','hp':150,'max_hp':180},
                    '102':{'name':'Bea','username':'bea','hp':0,'max_hp':200,'ko_counted':True},
                }
                self.game._change_item('101','phoenix_down',1,'test')
                result = self.game.revive_active('101','@bea')
                self.assertTrue(result.ok,result.messages)
                self.assertEqual(self.game.encounter_roster['102']['hp'],60)
                self.assertFalse(self.game.encounter_roster['102']['ko_counted'])
                self.assertEqual(self.game._inventory_qty('101','phoenix_down'),0)
                second = self.game.revive_active('101','bea')
                self.assertFalse(second.ok)
                self.assertEqual(self.game._inventory_qty('101','phoenix_down'),0)
                self.game.active_encounter = None
                self.game.encounter_roster = {}

    def test_world_event_treasure_is_valid_and_one_rare_is_guaranteed(self):
        for event, (rare, premium) in WORLD_EVENT_TREASURE.items():
            self.assertTrue(rare, event)
            self.assertTrue(all(i in self.game.data.items for i in (*rare,*premium)),event)
        monster = dict(self.game.data.monsters['behemoth'])
        ordinary = self.game._award_victory('101',self.game._player('101'),monster)
        boosted = self.game._award_victory('102',self.game._player('102'),monster,world_event_id='notorious_behemoth')
        self.assertGreaterEqual(boosted['xp'],ordinary['xp']*3)
        self.assertGreaterEqual(boosted['jp'],ordinary['jp']*2)
        self.assertTrue(any('World Event rare' in loot for loot in boosted['loot']))

if __name__ == '__main__':
    unittest.main()

# Tests below deliberately exercise the live battle item interpreter, rather
# than relying solely on catalog metadata descriptions.
class BattleStatusConsumables1994Tests(BattleRewards1994Tests):
    def test_cures_and_buffs_resolve_and_consume_only_when_effective(self):
        cures = {
            'antidote': 'poison', 'echo_herbs': 'silence', 'eye_drops': 'blind',
            'chronos_tear': 'slow', 'smelling_salts': 'stun',
            'remedy': 'poison', 'panacea': 'blind',
        }
        buffs = {
            'iron_tonic': 'protect', 'swiftwater': 'haste', 'regen_tonic': 'regen',
            'war_horn': 'power_up', 'mages_incense': 'focus', 'smoke_bomb': 'evade',
        }
        hero = {'name':'Alex','hp':70,'max_hp':200,'mp':0,'max_mp':0,'ap':15,'max_ap':40,
                'healing':0,'items_used':0,'statuses':{}}
        self.game.encounter_roster={'101':hero}
        self.game.active_encounter={'state':'combat','round':1}
        for item_id, status in cures.items():
            with self.subTest(item=item_id):
                hero['statuses']={status:{'turns':3,'magnitude':0.1}}
                self.game._change_item('101',item_id,1,'test')
                logs=[]
                self.game._resolve_active_item('101',hero,{'item_id':item_id,'target_id':'101'},logs)
                self.assertNotIn(status,hero['statuses'])
                self.assertEqual(self.game._inventory_qty('101',item_id),0)
        for item_id,status in buffs.items():
            with self.subTest(item=item_id):
                hero['statuses']={}
                self.game._change_item('101',item_id,1,'test')
                self.game._resolve_active_item('101',hero,{'item_id':item_id,'target_id':'101'},[])
                self.assertIn(status,hero['statuses'])
                self.assertEqual(self.game._inventory_qty('101',item_id),0)

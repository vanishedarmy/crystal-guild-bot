"""LW-1: earned-on-settlement, idempotency, public projection, offline gates."""
from pathlib import Path
import random
import tempfile
import unittest
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.living_world import record_solo_bank, player_snapshot
ROOT=Path(__file__).resolve().parents[1]

class LivingWorldLW1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Database(Path(self.tmp.name)/'guild.db')
        self.data=GameData(ROOT/'data')
        self.game=CrystalGuildEngine(self.db,self.data,rng=random.Random(7),overlay_state_path=str(Path(self.tmp.name)/'overlay.json'))
        self.assertTrue(self.game.recruit('3456','willow','Willow').ok)
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def state(self,key='venture-one',region='greenwind_plains',status='choice',history=None):
        return {'region_id':region,'status':status,'lw_activity_id':key,'started_at':12345,'stage':1,
                'history':history if history is not None else [{'stage':1,'type':'victory'}]}
    def test_exactly_once_and_four_discoveries_with_one_time_gil(self):
        begin=int(self.db.one("SELECT gil FROM players WHERE twitch_id='3456'")['gil'])
        self.assertIsNone(record_solo_bank(self.db,'3456',self.state(status='combat'),self.data.living_world_discoveries))
        self.assertIsNone(record_solo_bank(self.db,'3456',self.state(region='crescent_isle'),self.data.living_world_discoveries))
        self.assertIsNone(record_solo_bank(self.db,'3456',self.state(history=[]),self.data.living_world_discoveries))
        prizes=[]
        for i in range(4):
            st=self.state(f'venture-{i}')
            found=record_solo_bank(self.db,'3456',st,self.data.living_world_discoveries)
            self.assertIsNotNone(found)
            prizes.append(found['reward_gil'])
            self.assertIsNone(record_solo_bank(self.db,'3456',st,self.data.living_world_discoveries))
        self.assertIsNone(record_solo_bank(self.db,'3456',self.state('venture-fifth'),self.data.living_world_discoveries))
        self.assertEqual(prizes,[75,100,125,200])
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='3456'")['gil']),begin+500)
        self.assertEqual(self.db.one('SELECT COUNT(*) AS n FROM lw_discoveries')['n'],4)
        self.assertEqual(self.db.one('SELECT COUNT(*) AS n FROM lw_reward_receipts')['n'],4)
        self.assertEqual(self.db.one("SELECT progress FROM lw_region_progress WHERE player_id='3456'")['progress'],100)
        snap=player_snapshot(self.db.conn,'3456',self.data.living_world_regions,self.data.living_world_config,self.data.living_world_discoveries)
        self.assertTrue(snap['playable']);self.assertEqual(snap['regions'][0]['status'],'completed')
        self.assertEqual(snap['summary']['discoveries'],4)
        self.assertNotIn('3456',str(snap))
    def test_failure_rolls_back_unique_receipt_and_protects_currency(self):
        with self.db.tx() as conn:
            conn.execute('DROP TABLE lw_reward_receipts')
        with self.assertRaises(Exception):
            record_solo_bank(self.db,'3456',self.state(),self.data.living_world_discoveries)
        self.assertEqual(self.db.one('SELECT COUNT(*) AS n FROM lw_activity_receipts')['n'],0)
        self.assertEqual(self.db.one('SELECT COUNT(*) AS n FROM lw_discoveries')['n'],0)
    def test_snapshot_hides_undiscovered_content(self):
        snap=player_snapshot(self.db.conn,'3456',self.data.living_world_regions,self.data.living_world_config,self.data.living_world_discoveries)
        self.assertEqual(snap['summary']['regions_unlocked'],1)
        self.assertEqual(snap['regions'][0]['status'],'available')
        self.assertFalse(any(d['discovered'] for d in snap['regions'][0]['discoveries']))
        self.assertNotIn('Oldstone Arch',str(snap))
        self.assertTrue(all(not r['unlocked'] for r in snap['regions'][1:]))
    def test_real_bank_has_discovery_in_result_and_no_duplicate(self):
        self.assertTrue(self.game.choose_job('3456','warrior').ok)
        expedition=self.state();expedition.update(spoils={'gil':0,'items':[]},secured={'xp':0,'jp':0},secured_loot=[],history=[{'type':'victory','stage':1}],updated_at=12345)
        result=self.game._solo_bank_spoils('3456',expedition,outcome='returned')
        self.assertTrue(result.ok)
        self.assertEqual(result.data['living_world_discovery']['name'],'Oldstone Arch')
        self.assertIn('LIVING WORLD',str(result.data['solo_result']['notes']))
        self.assertEqual(self.db.one('SELECT COUNT(*) AS n FROM lw_discoveries')['n'],1)

if __name__=='__main__':unittest.main()

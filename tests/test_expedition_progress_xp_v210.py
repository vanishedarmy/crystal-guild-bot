"""v2.1.0: stage XP is modest, declining, cache-based and idempotent."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.expeditions import stage_exploration_xp

ROOT=Path(__file__).resolve().parents[1]

class ExpeditionProgressXPV210Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Database(Path(self.tmp.name)/'exp.db')
        self.game=CrystalGuildEngine(self.db,GameData(ROOT/'data'),rng=random.Random(210),overlay_state_path=str(Path(self.tmp.name)/'overlay.json'))
        self.game.recruit('100','xphero','Hero')
        self.game.choose_job('100','warrior')
        self.db.execute("UPDATE players SET level=5 WHERE twitch_id='100'")
        self.db.execute('UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1')
        self.db.execute("INSERT INTO player_chocobos(player_id,name,registered_at) VALUES ('100','Biscuit',CURRENT_TIMESTAMP)")
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def start(self):
        self.assertTrue(self.game.expedition_start('100','emerald_wilds','scout').ok)
    def resolve_resource(self):
        state=self.game._expedition_load('100');state['travel_ready_at']=0;self.game._expedition_save('100',state)
        with patch.object(self.game.rng,'random',return_value=1.0),patch('crystal_guild.engine.expedition_event_weights',return_value=(['resource'],[1.0])):
            result=self.game.expedition_resolve_stage('100')
        self.assertTrue(result.ok,result.messages)
        return self.game._expedition_load('100')
    def test_no_early_reward_duplicate_or_award_before_return(self):
        self.start()
        player_xp=int(self.game._player('100')['xp'])
        self.assertFalse(self.game.expedition_resolve_stage('100').ok)
        self.assertEqual(self.game._expedition_load('100')['cache']['xp'],0)
        state=self.resolve_resource()
        award=int(state['event']['stage_xp'])
        self.assertGreater(award,0)
        self.assertEqual(state['cache']['xp'],award)
        self.assertEqual(self.game._player('100')['xp'],player_xp)
        self.assertIn('exploration XP',state['event']['label'])
        self.assertFalse(self.game.expedition_resolve_stage('100').ok)
        self.assertEqual(self.game._expedition_load('100')['cache']['xp'],award)
        first=self.game._expedition_public('100')
        self.assertEqual(first['event']['stage_xp'],award)
        returned=self.game.expedition_return('100')
        self.assertTrue(returned.ok,returned.messages)
        self.assertEqual(returned.data['expedition_result']['rewards']['xp'],award)
        self.assertEqual(int(self.game._player('100')['xp']),player_xp+award)
    def test_second_stage_less_xp_and_reload_preserves_cache(self):
        self.start(); one=self.resolve_resource();stage1=int(one['event']['stage_xp'])
        self.assertTrue(self.game.expedition_continue('100','unknown').ok)
        two=self.resolve_resource();stage2=int(two['event']['stage_xp'])
        self.assertGreater(stage1,stage2)
        self.assertEqual(two['cache']['xp'],stage1+stage2)
        self.assertEqual(two['exploration_xp_stages'],[1,2])
        self.assertEqual(CrystalGuildEngine(self.db,self.game.data,rng=random.Random(2),overlay_state_path=str(Path(self.tmp.name)/'other.json'))._expedition_public('100')['cache']['xp'],stage1+stage2)
    def test_non_combat_reward_is_smaller_than_one_local_enemy_victory(self):
        baseline=[m['xp'] for m in self.game.data.monsters.values() if m['id'] in {r['monster_id'] for r in self.game.data.expedition_regions['emerald_wilds']['encounters']}]
        self.assertLess(stage_exploration_xp(sorted(baseline)[len(baseline)//2],1,1),min(baseline))
        self.assertGreater(stage_exploration_xp(80,1,1),stage_exploration_xp(80,1,4))
        self.assertLess(stage_exploration_xp(80,.1,1),stage_exploration_xp(80,1,1))
    def test_idempotent_stage_reward_even_if_replayed(self):
        self.start();state=self.resolve_resource();first=state['cache']['xp']
        self.game._expedition_stage_resolved('100',state,{'type':'event','label':'Replay'})
        self.assertEqual(self.game._expedition_load('100')['cache']['xp'],first)
        self.assertEqual(self.game._expedition_load('100')['event']['stage_xp'],0)

if __name__=='__main__':unittest.main()

"""V2.12: Bond XP in victorious Hunt, solo Expedition, and Dungeon paths."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine, GameResult

ROOT = Path(__file__).resolve().parents[1]

class BeastmasterSoloModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=GameData(ROOT/'data')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'game.sqlite'
        self.db=Database(self.path)
        self.game=CrystalGuildEngine(self.db,self.data,overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(31))
        self.game.recruit('b','beast','Beast')
        self.db.execute("UPDATE players SET level=99,current_job='beastmaster',current_hp=600 WHERE twitch_id='b'")
        self.db.execute("INSERT OR REPLACE INTO player_jobs(player_id,job_id,level,jp) VALUES('b','beastmaster',99,0)")
        self.db.execute("INSERT OR REPLACE INTO bestiary(player_id,monster_id,defeats) VALUES('b','wolf',3)")
        self.assertTrue(self.game.tame_beast('b','wolf').ok)
        self.monster=self.data.monsters['wolf']

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def meta(self, assists=1, species=None):
        pet=self.game._selected_tamed_companion('b')
        if species is not None:pet={**pet,'monster_id':species}
        return {'job_id':'beastmaster','_tamed_companion':pet,'_pet_assists':assists,
                'hp':500,'max_hp':600,'damage':120,'damage_taken':0,'healing':0,'best_hit':120,'name':'Beast'}

    def bond(self):
        row=self.db.one("SELECT bond_xp,bond_assists FROM beastmaster_companions WHERE player_id='b' AND monster_id='wolf'")
        return (row['bond_xp'],row['bond_assists'])

    def receipts(self):
        return self.db.all("SELECT event_key,player_id FROM beastmaster_bond_receipts ORDER BY event_key")

    def test_hunt_winner_with_assist_awarded_once_inside_victory_transaction(self):
        hunt=next(x for x in self.data.hunts.values() if x.get('rewards'))
        self.game._award_hunt_victory('b',self.game._player('b'),hunt,self.monster,
                                       companion_meta=self.meta(),encounter_key='hunt:one')
        xp=self.bond()[0]
        self.assertGreater(xp,0)
        self.game._award_hunt_victory('b',self.game._player('b'),hunt,self.monster,
                                       companion_meta=self.meta(),encounter_key='hunt:one')
        self.assertEqual(self.bond(),(xp,1))
        self.assertEqual(len(self.receipts()),1)

    def test_hunt_no_assist_or_wrong_job_no_bond(self):
        hunt=next(x for x in self.data.hunts.values() if x.get('rewards'))
        self.game._award_hunt_victory('b',self.game._player('b'),hunt,self.monster,
                                       companion_meta=self.meta(assists=0),encounter_key='hunt:none')
        self.game._award_hunt_victory('b',self.game._player('b'),hunt,self.monster,
                                       companion_meta={**self.meta(),'job_id':'warrior'},encounter_key='hunt:warrior')
        self.assertEqual(self.bond(),(0,0))

    def test_hunt_event_key_only_from_dispatch_snapshot(self):
        # New Hunt routing passes a unique server-run receipt into _award_hunt_victory.
        import inspect
        code=inspect.getsource(self.game._finish_active_encounter)
        self.assertIn('encounter_key=f"hunt:{moment_run}"',code)

    def test_expedition_victory_and_retry_use_same_receipt(self):
        state={'run_id':'run-exp-1','started_at':100,'region_id':'starter','stage':3,'history':[],
               'cache':{'xp':0,'jp':0,'gil':0,'items':[]},'boss_encounter':False}
        with patch.object(self.game,'_expedition_stage_resolved',return_value=GameResult.success('won')):
            self.game._finish_expedition_combat_victory('b',state,self.monster,self.meta(),1,[])
            xp=self.bond()[0]
            self.assertGreater(xp,0)
            self.game._finish_expedition_combat_victory('b',state,self.monster,self.meta(),1,[])
        self.assertEqual(self.bond(),(xp,1))
        self.assertEqual(len(self.receipts()),1)
        self.assertTrue(self.receipts()[0]['event_key'].startswith('expedition:run-exp-1:3:'))

    def test_expedition_no_reward_without_pet_participation(self):
        state={'run_id':'run-exp-2','started_at':100,'region_id':'starter','stage':3,'history':[],
               'cache':{'xp':0,'jp':0,'gil':0,'items':[]},'boss_encounter':False}
        with patch.object(self.game,'_expedition_stage_resolved',return_value=GameResult.success('won')):
            self.game._finish_expedition_combat_victory('b',state,self.monster,self.meta(0),1,[])
        self.assertEqual(self.bond(),(0,0))

    def test_expedition_legacy_save_has_stable_key(self):
        state={'started_at':100,'region_id':'starter','stage':3,'history':[],
               'cache':{'xp':0,'jp':0,'gil':0,'items':[]},'boss_encounter':False}
        with patch.object(self.game,'_expedition_stage_resolved',return_value=GameResult.success('won')):
            self.game._finish_expedition_combat_victory('b',state,self.monster,self.meta(),1,[])
        self.assertIn('expedition:legacy:100:starter:3:',self.receipts()[0]['event_key'])

    def test_dungeon_victory_credits_once_by_run_room(self):
        state={'run_id':'run-dung-1','dungeon_id':'test','started_at':100,'room_index':2,
               'cache':{'xp':0,'jp':0,'gil':0,'items':[]},'history':[]}
        with patch.object(self.game,'_dungeon_finish',return_value=GameResult.success('complete')):
            self.game._dungeon_finish_room_victory('b',state,self.monster,self.meta(),1,[])
            xp=self.bond()[0]
            self.assertGreater(xp,0)
            self.game._dungeon_finish_room_victory('b',state,self.monster,self.meta(),1,[])
        self.assertEqual(self.bond(),(xp,1))
        self.assertEqual(len(self.receipts()),1)
        self.assertTrue(self.receipts()[0]['event_key'].startswith('dungeon:run-dung-1:2:'))

    def test_dungeon_no_assist_and_unowned_cannot_gain(self):
        state={'run_id':'run-dung-2','dungeon_id':'test','started_at':100,'room_index':2,
               'cache':{'xp':0,'jp':0,'gil':0,'items':[]},'history':[]}
        with patch.object(self.game,'_dungeon_finish',return_value=GameResult.success('complete')):
            self.game._dungeon_finish_room_victory('b',state,self.monster,self.meta(0),1,[])
            self.game._dungeon_finish_room_victory('b',state,self.monster,self.meta(1,'coeurl'),1,[])
        self.assertEqual(self.bond(),(0,0))
        self.assertFalse(self.receipts())

    def test_dungeon_receipt_rolls_back_if_victory_write_fails(self):
        state={'run_id':'run-dung-fail','dungeon_id':'test','started_at':100,'room_index':2,
               'cache':{'xp':0,'jp':0,'gil':0,'items':[]},'history':[]}
        # Force the helper to fail after the defeat counter has been updated.
        with patch('crystal_guild.beastmaster.award_companion_bond',side_effect=RuntimeError('simulated DB failure')):
            with self.assertRaises(RuntimeError):
                self.game._dungeon_finish_room_victory('b',state,self.monster,self.meta(),1,[])
        self.assertEqual(self.bond(),(0,0))
        self.assertEqual(self.db.one("SELECT defeats FROM bestiary WHERE player_id='b' AND monster_id='wolf'")['defeats'],3)

    def test_real_solo_expedition_assist_to_victory(self):
        # Resolve the same active ability handler used by Expedition combat.
        self.game.encounter_roster={'b':{'name':'Beast','job_id':'beastmaster'}}
        encounter={'kind':'expedition','monster_id':'wolf','round':1,'monster_hp':200000,
                   'max_rounds':10}
        self.game._initialize_active_combat(encounter)
        meta=self.game.encounter_roster['b']
        meta['ap']=max(100,int(meta.get('ap',0)))
        self.game.active_encounter=encounter
        self.game._resolve_active_ability(meta,{'ability_id':'call_beast','target_id':'monster'},self.monster,[])
        self.assertGreater(meta.get('_pet_assists',0),0)
        state={'run_id':'exp-actual','started_at':99,'region_id':'starter','stage':1,'history':[],
               'cache':{'xp':0,'jp':0,'gil':0,'items':[]},'boss_encounter':False}
        with patch.object(self.game,'_expedition_stage_resolved',return_value=GameResult.success('won')):
            self.game._finish_expedition_combat_victory('b',state,self.monster,meta,2,[])
        self.assertGreater(self.bond()[0],0)

    def test_real_dungeon_assist_to_victory(self):
        self.game.encounter_roster={'b':{'name':'Beast','job_id':'beastmaster'}}
        encounter={'kind':'dungeon','monster_id':'wolf','round':1,'monster_hp':200000,
                   'max_rounds':10}
        self.game._initialize_active_combat(encounter)
        meta=self.game.encounter_roster['b']
        meta['ap']=max(100,int(meta.get('ap',0)))
        self.game.active_encounter=encounter
        self.game._resolve_active_ability(meta,{'ability_id':'call_beast','target_id':'monster'},self.monster,[])
        self.assertGreater(meta.get('_pet_assists',0),0)
        state={'run_id':'dung-actual','started_at':99,'dungeon_id':'test','room_index':0,
               'cache':{'xp':0,'jp':0,'gil':0,'items':[]},'history':[]}
        with patch.object(self.game,'_dungeon_finish',return_value=GameResult.success('won')):
            self.game._dungeon_finish_room_victory('b',state,self.monster,meta,2,[])
        self.assertGreater(self.bond()[0],0)

    def test_expedition_transaction_rollback_of_bestiary_and_bond(self):
        state={'run_id':'exp-fail','started_at':99,'region_id':'starter','stage':2,'history':[],
               'cache':{'xp':0,'jp':0,'gil':0,'items':[]},'boss_encounter':False}
        with patch('crystal_guild.beastmaster.award_companion_bond',side_effect=RuntimeError('rollback')):
            with self.assertRaises(RuntimeError):
                self.game._finish_expedition_combat_victory('b',state,self.monster,self.meta(),2,[])
        self.assertEqual(self.bond(),(0,0))
        self.assertEqual(self.db.one("SELECT defeats FROM bestiary WHERE player_id='b' AND monster_id='wolf'")['defeats'],3)

    def test_no_schema_change_needed(self):
        self.assertEqual(self.db.schema_version(),30)

if __name__=='__main__':unittest.main()

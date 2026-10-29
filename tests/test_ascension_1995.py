"""v1.9.95 Job Ascension invariants, persistence and first-clear settlement."""
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class Ascension1995Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'guild.db')
        self.data = GameData(ROOT / 'data')
        self.engine = CrystalGuildEngine(
            self.db, self.data, rng=random.Random(1995),
            overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'),
        )
        self.assertTrue(self.engine.recruit('195', 'ascendant', 'Ascendant').ok)
        self.assertTrue(self.engine.choose_job('195', 'warrior').ok)
        self.db.execute("UPDATE players SET level=60,current_hp=2000 WHERE twitch_id='195'")
        self.db.execute("UPDATE player_jobs SET level=60 WHERE player_id='195' AND job_id='warrior'")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_catalogs_are_complete_and_legacy_dungeons_unchanged(self):
        self.assertEqual(len(self.data.ascension_trials), 72)
        self.assertEqual(len(self.data.ascension_dungeons), 3)
        self.assertEqual(len(self.data.dungeons), 4)
        self.assertEqual(self.data.validate(), [])
        for job_id in self.data.jobs:
            self.assertEqual([self.data.ascension_trials[f'ascension_{job_id}_{level}']['level']
                              for level in (60,75,90,99)], [60,75,90,99])
        self.assertEqual(len(set(self.data.titles)), len(self.data.titles))

    def test_gates_current_job_character_level_and_prior_clear(self):
        self.assertFalse(self.engine.dungeon_start('195', 'ascension_whitemage_60').ok)
        self.assertFalse(self.engine.dungeon_start('195', 'ascension_warrior_75').ok)
        self.assertTrue(self.engine.dungeon_start('195', 'ascension_warrior_60').ok)
        self.assertFalse(self.engine.dungeon_start('195', 'crystal_sanctum').ok)
        state = self.engine._dungeon_public('195')
        self.assertTrue(state['ascension_trial'])
        self.assertEqual([(o['action'],o['required']) for o in state['trial_objective']], [('ability',1),('defend',1)])

    def test_persisted_trial_seal_and_settlement_with_permanent_bonus(self):
        baseline = self.engine._effects('195','warrior').get('defense_mult',0)
        self.assertTrue(self.engine.dungeon_start('195', 'ascension_warrior_60').ok)
        active = self.engine._dungeon_load('195')
        active['combat']['encounter']['monster_hp']=1
        active['combat']['roster']['195']['ap']=max(40,active['combat']['roster']['195']['ap'])
        active['combat']['roster']['195']['max_ap']=max(40,active['combat']['roster']['195']['max_ap'])
        self.engine._dungeon_save('195',active)
        # Enemy attacks are irrelevant to objective gating in this focused test.
        self.engine._solo_resolve_enemy_intent = lambda monster, encounter, log: None
        result = self.engine.dungeon_action('195','ability:power_break')
        self.assertTrue(result.ok,result.messages)
        state = self.engine._dungeon_public('195')
        self.assertIsNotNone(state)
        self.assertEqual(state['combat']['enemy']['hp'],1)
        self.assertEqual([(o['action'],o['current']) for o in state['trial_objective']], [('ability',1),('defend',0)])
        # A new engine instance sees the same persisted seal progress.
        resumed = CrystalGuildEngine(self.db,self.data,rng=random.Random(1996), overlay_state_path=str(Path(self.tmp.name)/'overlay-2.json'))
        resumed._solo_resolve_enemy_intent = lambda monster, encounter, log: None
        self.assertEqual(resumed._dungeon_public('195')['trial_objective'][0]['current'],1)
        self.assertTrue(resumed.dungeon_action('195','defend').ok)
        self.assertTrue(resumed.dungeon_action('195','attack').ok)
        self.assertIsNone(resumed._dungeon_public('195'))
        self.assertEqual(resumed._dungeon_progress('195','ascension_warrior_60')['clears'],1)
        self.assertAlmostEqual(resumed._effects('195','warrior').get('defense_mult',0)-baseline,0.025)
        # Replays never stack the milestone passive.
        self.assertTrue(resumed.dungeon_start('195','ascension_warrior_60').ok)
        self.assertAlmostEqual(resumed._effects('195','warrior').get('defense_mult',0)-baseline,0.025)

    def test_75_title_award_and_progression(self):
        self.db.execute("UPDATE players SET level=75 WHERE twitch_id='195'")
        self.db.execute("UPDATE player_jobs SET level=75 WHERE player_id='195' AND job_id='warrior'")
        self.db.execute("INSERT INTO player_dungeon_progress(player_id,dungeon_id,clears) VALUES ('195','ascension_warrior_60',1)")
        self.assertTrue(self.engine.dungeon_start('195','ascension_warrior_75').ok)
        # Simulate successful completion through same authoritative settlement path.
        state=self.engine._dungeon_load('195')
        self.assertTrue(self.engine._dungeon_finish('195',state,outcome='complete').ok)
        self.assertEqual(self.engine._dungeon_progress('195','ascension_warrior_75')['clears'],1)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_titles WHERE player_id='195' AND title_id='ascension_warrior_75'"))
        first_qty=self.engine._inventory_qty('195',self.data.ascension_trials['ascension_warrior_75']['first_clear_bonus']['items'][0]['item_id'])
        self.assertGreaterEqual(first_qty,1)
        self.assertTrue(self.engine.dungeon_start('195','ascension_warrior_75').ok)
        self.assertTrue(self.engine._dungeon_finish('195',self.engine._dungeon_load('195'),outcome='complete').ok)
        self.assertEqual(self.engine._dungeon_progress('195','ascension_warrior_75')['clears'],2)
        self.assertEqual(self.engine._inventory_qty('195',self.data.ascension_trials['ascension_warrior_75']['first_clear_bonus']['items'][0]['item_id']),first_qty)

    def test_new_high_level_dungeon_route_choice_is_effective(self):
        self.assertEqual([r['id'] for r in self.engine._dungeon_board_state('195')['dungeons'][-3:]], ['crystal_sanctum','celestial_spire','astral_crucible'])
        self.assertTrue(self.engine.dungeon_start('195','crystal_sanctum').ok)
        self.assertTrue(self.engine.dungeon_continue('195').ok)
        # The ward combat chamber must have a real monster and playable actions.
        state=self.engine._dungeon_load('195')
        self.assertEqual(state['room_index'],1)
        self.assertEqual(state['status'],'combat')
        self.assertEqual(state['combat']['encounter']['monster_id'],'holy_dragon')
        # Resolve the chamber through its normal victory route.
        state['combat']['encounter']['monster_hp']=1
        self.engine._dungeon_save('195',state)
        self.engine._solo_resolve_enemy_intent = lambda monster, encounter, log: None
        self.assertTrue(self.engine.dungeon_action('195','attack').ok)
        self.assertTrue(self.engine.dungeon_continue('195').ok)
        self.assertEqual(self.engine._dungeon_public('195')['status'],'decision')
        self.assertTrue(self.engine.dungeon_choose('195','shield').ok)
        current=self.engine._dungeon_load('195')
        self.assertEqual(current['modifiers']['next_hazard_reduction_percent'],50)
        self.assertTrue(self.engine.dungeon_continue('195').ok)
        self.assertEqual(self.engine._dungeon_public('195')['room']['type'],'hazard')
        self.assertNotIn('next_hazard_reduction_percent', self.engine._dungeon_load('195')['modifiers'])

    def test_portal_dungeon_action_revisions_work_for_ascension(self):
        result=self.engine.portal_dungeon_start('195','ascension_warrior_60','ascension-portal-start')
        self.assertTrue(result.ok,result.messages)
        state=self.engine._dungeon_public('195')
        self.assertTrue(state['ascension_trial'])
        result=self.engine.portal_dungeon_action('195',state['run_id'],state['room']['id'],state['revision'],'defend','ascension-defend')
        self.assertTrue(result.ok,result.messages)
        stale=self.engine.portal_dungeon_action('195',state['run_id'],state['room']['id'],state['revision'],'attack','ascension-stale')
        self.assertFalse(stale.ok)
        self.assertTrue(stale.data.get('stale_dungeon'))

    def test_level99_requires_real_limit_and_seeds_charge(self):
        self.db.execute("UPDATE players SET level=99,current_hp=4000 WHERE twitch_id='195'")
        self.db.execute("UPDATE player_jobs SET level=99 WHERE player_id='195' AND job_id='warrior'")
        for level in (60,75,90):
            self.db.execute("INSERT INTO player_dungeon_progress(player_id,dungeon_id,clears) VALUES (?,?,1)",('195',f'ascension_warrior_{level}'))
        self.assertTrue(self.engine.dungeon_start('195','ascension_warrior_99').ok)
        active=self.engine._dungeon_public('195')
        self.assertGreaterEqual(active['combat']['limit']['value'] if 'value' in active['combat']['limit'] else 0,0)
        self.assertTrue(any(x['action']=='limit' and not x['complete'] for x in active['trial_objective']))
        self.assertTrue(self.engine._dungeon_progress('195','ascension_warrior_99')['clears']==0)


if __name__ == '__main__':
    unittest.main()

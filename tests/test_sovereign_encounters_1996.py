"""v1.9.96 advanced boss mechanics, deterministic phase/telegraph and saved encounters."""
import copy
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from crystal_guild.advanced_encounters import affinity_multiplier, affinities, phase_for_hp, telegraph_for_round, validate_config
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class Sovereign1996Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / 'test.db')
        self.data = GameData(ROOT / 'data')
        self.engine = CrystalGuildEngine(self.db, self.data, rng=random.Random(196), overlay_state_path=str(Path(self.temp.name) / 'overlay.json'))
        self.assertTrue(self.engine.recruit('196', 'bossrunner', 'Boss Runner').ok)
        self.assertTrue(self.engine.choose_job('196', 'warrior').ok)
        self.db.execute("UPDATE players SET level=99,current_hp=9999 WHERE twitch_id='196'")
        self.db.execute("UPDATE player_jobs SET level=99 WHERE player_id='196' AND job_id='warrior'")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_six_ascension_dungeons_all_have_phase_bosses_and_items(self):
        self.assertEqual(len(self.data.ascension_dungeons), 6)
        self.assertEqual(self.data.validate(), [])
        self.assertEqual(sorted(d['min_level'] for d in self.data.ascension_dungeons.values()), [55,65,75,85,95,99])
        for d in self.data.ascension_dungeons.values():
            self.assertEqual(len(d['rooms']),6)
            self.assertTrue(d['rooms'][-1]['advanced_combat'])
            self.assertIn(d['first_clear_bonus']['items'][0]['item_id'], self.data.items)
        self.assertEqual(sum(bool(t.get('advanced_combat')) for t in self.data.ascension_trials.values()), 54)

    def test_affinities_change_with_remaining_hp(self):
        cfg=self.data.ascension_dungeons['abyssal_foundry']['rooms'][-1]['advanced_combat']
        self.assertEqual(phase_for_hp(cfg, 100, 100)['name'], 'Molten Armor')
        self.assertIn('fire',affinities(cfg,100,100)['weak'])
        self.assertEqual(affinity_multiplier(cfg,100,100,'Fire'), (1.4, 'WEAKNESS'))
        self.assertEqual(affinity_multiplier(cfg,100,100,'Ice'), (0.65, 'RESISTED'))
        self.assertEqual(affinity_multiplier(cfg,100,100,'water'), (1.0, ''))
        self.assertEqual(phase_for_hp(cfg,59,100)['name'], 'Fractured Molten Armor')
        self.assertEqual(affinity_multiplier(cfg,59,100,'Water'), (1.4,'WEAKNESS'))
        self.assertEqual(phase_for_hp(cfg,25,100)['name'], 'Desperate Molten Armor')
        self.assertEqual(affinity_multiplier(cfg,25,100,'Fire'), (1.4,'WEAKNESS'))
        self.assertEqual(telegraph_for_round(cfg,1),None)
        self.assertEqual(telegraph_for_round(cfg,3)['kind'],'dungeon_telegraph')
        self.assertEqual(telegraph_for_round(cfg,4),None)
        with self.assertRaises(ValueError):
            validate_config({'affinities': {'weak':['fire'], 'resist':['fire']}}, 'test')

    def _enter_foundry_battle(self):
        self.assertTrue(self.engine.dungeon_start('196','abyssal_foundry').ok)
        self.assertTrue(self.engine.dungeon_continue('196').ok)
        state=self.engine._dungeon_load('196')
        self.assertEqual(state['status'],'combat')
        return state

    def test_portal_phase_visibility_and_persistence_restart(self):
        state=self._enter_foundry_battle()
        public=self.engine._dungeon_public('196')
        self.assertEqual(public['combat']['advanced']['phase'],'Molten Armor')
        self.assertEqual(public['combat']['advanced']['weak'],['fire'])
        self.assertEqual(public['combat']['advanced']['resist'],['ice'])
        encounter=state['combat']['encounter'];encounter['monster_hp']=int(encounter['monster_max_hp']*.59)
        self.engine._dungeon_save('196',state)
        restarted=CrystalGuildEngine(self.db,self.data,rng=random.Random(196),overlay_state_path=str(Path(self.temp.name)/'new-overlay.json'))
        self.assertTrue(restarted.dungeon_action('196','defend').ok)
        current=restarted._dungeon_public('196')
        self.assertEqual(current['combat']['advanced']['phase'],'Fractured Molten Armor')
        self.assertIn('water',current['combat']['advanced']['weak'])
        self.assertEqual(current['combat']['enemy']['intent'],current['combat']['enemy']['intent'])
        self.assertTrue(restarted._dungeon_load('196')['combat']['encounter']['advanced_combat'])

    def test_telegraph_guard_has_real_combat_reduction(self):
        state=self._enter_foundry_battle()
        cfg=state['combat']['encounter']['advanced_combat']
        monster=self.data.monsters[state['combat']['encounter']['monster_id']]
        state['combat']['encounter']['round']=4  # Ward warns on round 4.
        warning=self.engine._dungeon_enemy_intent(monster,state['combat']['encounter'])
        self.assertEqual(warning['kind'],'dungeon_telegraph')
        self.assertIn('DEFEND', warning['label'])
        encounter=state['combat']['encounter']
        self.engine.active_encounter=encounter
        meta=state['combat']['roster']['196']
        self.engine.encounter_roster={'196':meta}
        powers=[]
        def hit(monster, target, profile, *, scaling, power):
            powers.append(power)
            return 11
        with patch.object(self.engine,'_apply_enemy_hit',side_effect=hit):
            encounter['enemy_intent']=warning
            meta['defending']=False
            self.engine._dungeon_enemy_response(monster,encounter,[])
            meta['defending']=True
            self.engine._dungeon_enemy_response(monster,encounter,[])
        self.assertAlmostEqual(powers[1]/powers[0],0.60)

    def test_elemental_multipliers_used_in_actual_damage(self):
        state=self._enter_foundry_battle()
        encounter=state['combat']['encounter'];meta=state['combat']['roster']['196'];monster=self.data.monsters[encounter['monster_id']]
        self.engine.active_encounter=encounter;self.engine.encounter_roster={'196':meta}
        def calc(elem):
            self.engine.rng=random.Random(500)
            return self.engine._basic_active_damage(meta,monster,scaling='magic',element=elem)[0]
        weak=calc('fire');neutral=calc('water');resist=calc('ice')
        self.assertGreater(weak,neutral)
        self.assertLess(resist,neutral)

    def test_old_dungeon_has_no_advanced_mechanics(self):
        self.assertTrue(self.engine.dungeon_start('196','forgotten_ossuary').ok is False)  # Different regional unlock unchanged.
        self.assertIsNone(telegraph_for_round({},4))

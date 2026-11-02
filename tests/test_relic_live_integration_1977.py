"""Tests for the real Python Bot integration, not the JavaScript staging resolver."""
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.relic_live import (damage_multiplier, adjusted_cost, heal_multiplier, eligible_relic,
                                       relic_resistance)

BASE=Path(__file__).resolve().parents[1]

class IntegratedRelicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=GameData(BASE/'data')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Database(Path(self.tmp.name)/'db.sqlite')
        self.engine=CrystalGuildEngine(self.db, self.catalog, overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(7))
        self.engine.recruit('1','player1','Player 1')
        self.engine.choose_job('1','dragoon')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def equip(self,item_id,job='dragoon',lvl=99,accessory=None):
        self.db.execute('UPDATE players SET level=?,current_job=? WHERE twitch_id=?',(lvl,job,'1'))
        self.db.execute('UPDATE equipment SET weapon_id=?,accessory_id=? WHERE player_id=?',(item_id,accessory,'1'))
        return self.engine._equipment_traits(self.engine._player('1'), self.catalog.jobs[job])

    def test_all_618_items_and_relic_quests_validate(self):
        self.catalog.validate_or_raise()
        self.assertEqual(len(self.catalog.items),618)
        r=[i for i in self.catalog.items.values() if i.get('relic_trait')]
        self.assertEqual(len(r),108)
        self.assertEqual(sum(bool(i.get('relic_signature')) for i in r),54)
        self.assertTrue(all(i['rarity']=='relic' and i.get('relic_id') for i in r))
        self.assertTrue(all(i['type']=='weapon' and i.get('relic_id') for i in self.catalog.items.values() if i['rarity']=='relic'))

    def test_ribbon_and_fragment_progression(self):
        self.assertEqual(self.catalog.items['ribbon']['min_level'],55)
        self.assertEqual(self.catalog.items['ribbon_fragment']['min_level'],35)
        self.assertEqual(len(self.catalog.items['ribbon']['status_immune']),7)

    def test_relic_job_and_level_are_checked_against_bot_database(self):
        ok=self.equip('ultimate_dragoon_eternal',lvl=99)
        self.assertEqual(ok['relic_trait']['key'],'skyward_mastery')
        self.assertEqual(ok['relic_signature']['key'],'dragonfall')
        too_low=self.equip('ultimate_dragoon_eternal',lvl=80)
        self.assertIsNone(too_low['relic_trait'])
        wrong_job=self.equip('ultimate_dragoon_eternal',job='warrior',lvl=99)
        self.assertIsNone(wrong_job['relic_trait'])

    def test_relic_is_not_inventory_only_bonus(self):
        t=self.equip(None)
        self.assertIsNone(t['relic_trait'])

    def test_multiplicative_resistance_stacking(self):
        self.db.execute('UPDATE players SET level=99 WHERE twitch_id=?',('1',))
        self.db.execute('UPDATE equipment SET armor_id=?,accessory_id=? WHERE player_id=?',('white_robe','ribbon_fragment','1'))
        t=self.engine._equipment_traits(self.engine._player('1'),self.catalog.jobs['dragoon'])
        self.assertAlmostEqual(t['status_resist']['silence'],0.625)
        self.assertAlmostEqual(self.engine._player_status_chance(t,'silence',1.0),0.375)

    def test_real_weapon_damage_bonus(self):
        t=self.equip('ultimate_dragoon_eternal',accessory='dragoon_boots')
        actor={'job_id':'dragoon',**t}
        val=damage_multiplier(actor,action='jump',monster={'id':'elder_dragon'})
        self.assertAlmostEqual(val,1.25*1.08*1.22)
        self.assertEqual(damage_multiplier(actor,action='',monster={'id':'elder_dragon'}),1.0)

    def test_resource_cost_discounters_only_when_equipped(self):
        raw={'job_id':'summoner','accessory_id':'sages_emblem','relic_trait':{'key':'resonance','value':0.22}}
        self.assertEqual(adjusted_cost(raw,100,'grand_summon'),73)
        self.assertEqual(adjusted_cost({'job_id':'summoner'},100),100)

    def test_white_mage_relic_healing_injured_ally(self):
        actor={'job_id':'whitemage','relic_trait':{'key':'gentle_benediction','value':0.3},'relic_signature':{'key':'lifewave','value':0.18}}
        self.assertAlmostEqual(heal_multiplier(actor,{'hp':40,'max_hp':100}),1.3*1.18)
        self.assertAlmostEqual(heal_multiplier(actor,{'hp':90,'max_hp':100}),1.3)

    def test_guard_bonus_is_once_only(self):
        actor={'job_id':'warrior','_relic_guard_ready':True,'relic_trait':{'key':'guard_to_strike','value':0.25}}
        self.assertAlmostEqual(damage_multiplier(actor),1.25)
        self.assertEqual(damage_multiplier(actor),1.0)

    def test_disallowed_relics_do_not_cross_class(self):
        item=self.catalog.items['gae_bolg_zenith']
        self.assertFalse(eligible_relic(item,'warrior'))
        self.assertTrue(eligible_relic(item,'dragoon'))

if __name__=='__main__':unittest.main()

"""Gameplay regression for six airship regions and endgame World Map boss."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT=Path(__file__).resolve().parents[1]
NEW=['emberglass_caldera','frostveil_observatory','gilded_mirage_expanse']
ORIGINAL=['shattered_sky_isles','aetherstorm_expanse','forgotten_dominion']
SUPER='eclipsed_singularity_citadel'

class SkyboundSingularityV199(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.db=Database(Path(self.tmp.name)/'guild.db')
  self.data=GameData(ROOT/'data')
  self.game=CrystalGuildEngine(self.db,self.data,overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(199))
  self.game.recruit('199','skyfarer','Skyfarer')
  self.game.choose_job('199','warrior')
  self.db.execute("UPDATE players SET level=99 WHERE twitch_id='199'")
  self.db.execute('UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1')
  self.db.execute('UPDATE fellowship_airship_state SET built=1 WHERE singleton_id=1')
 def tearDown(self):
  self.db.close();self.tmp.cleanup()
 def set_core(self,n):
  self.db.execute("UPDATE fellowship_airship_upgrades SET tier=? WHERE upgrade_id='crystal_core'",(n,))
 def test_catalog_extends_instead_of_overwriting_existing_regions(self):
  self.data.validate_or_raise()
  self.assertEqual([r['id'] for r in self.data.expedition_regions.values() if r.get('transport')=='airship'],ORIGINAL+NEW)
  self.assertEqual(self.game._expedition_atlas('199','airship')['region_count'],6)
  self.assertEqual(self.game._expedition_atlas('199')['region_count'],5)
  self.assertEqual(len(self.data.regions),9)
  self.assertGreater(self.data.regions[SUPER]['min_level'],self.data.regions['omega_ruins']['min_level'])
 def test_new_airship_regions_require_correct_core_levels(self):
  for region in NEW:
   needed=int(self.data.expedition_regions[region]['required_core'])
   self.set_core(needed-1)
   fail=self.game.expedition_start('199',region,'scout')
   self.assertFalse(fail.ok,fail.messages)
   self.assertIn('Crystal Core Tier', ' '.join(fail.messages))
   self.set_core(needed)
   started=self.game.expedition_start('199',region,'scout')
   self.assertTrue(started.ok,started.messages)
   active=self.game._expedition_load('199')
   self.assertEqual(active['region_id'],region)
   self.assertEqual(active['transport'],'airship')
   self.assertTrue(self.game.expedition_return('199').ok)
 def test_airship_level_gate_and_regional_boss_rewards(self):
  self.set_core(3)
  for rid in NEW:
   region=self.data.expedition_regions[rid]
   self.db.execute("UPDATE players SET level=? WHERE twitch_id='199'",(region['min_level']-1,))
   denied=self.game.expedition_start('199',rid,'scout')
   self.assertFalse(denied.ok)
   self.db.execute("UPDATE players SET level=99 WHERE twitch_id='199'")
   self.assertIn(region['boss']['monster_id'],self.data.monsters)
   self.assertIn(region['boss']['guaranteed_rewards'][0]['item_id'],self.data.items)
 def test_superboss_world_zone_travel_and_raid_catalog(self):
  self.db.execute("UPDATE players SET level=96 WHERE twitch_id='199'")
  denied=self.game.travel('199',SUPER)
  self.assertFalse(denied.ok)
  self.db.execute("UPDATE players SET level=99 WHERE twitch_id='199'")
  self.assertTrue(self.game.travel('199',SUPER).ok)
  self.assertEqual(self.game._player('199')['current_region'],SUPER)
  self.assertTrue(self.game.boss_info('eclipse sovereign').ok)
  sovereign=self.data.bosses['eclipse_sovereign']
  self.assertEqual(sovereign['tier'],'Ultimate Superboss')
  self.assertGreater(sovereign['hp'],self.data.bosses['absolute_virtue']['hp'])
  self.assertTrue(self.game.spawn_boss('eclipse sovereign').ok)

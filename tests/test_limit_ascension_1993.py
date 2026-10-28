"""Regressions for v1.9.93 tier-locked, charge-based Limit Breaks."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

DATA = Path(__file__).resolve().parents[1] / 'data'

class LimitAscensionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / 'limits.db')
        self.data = GameData(DATA)
        self.game = CrystalGuildEngine(self.db, self.data, rng=random.Random(1993),
            encounter_round_seconds=8, raid_round_seconds=15,
            venture_cooldown_seconds=0, venture_treasure_chance=0,
            overlay_state_path=str(Path(self.temp.name) / 'overlay.json'))
        for pid, username, job in [('1','tank','warrior'),('2','healer','whitemage'),('3','caster','blackmage')]:
            self.assertTrue(self.game.recruit(pid, username, username.title()).ok)
            self.assertTrue(self.game.choose_job(pid, job).ok)
            self.db.execute('UPDATE player_jobs SET level=99 WHERE player_id=? AND job_id=?',(pid,job))
            self.db.execute('UPDATE players SET level=99 WHERE twitch_id=?',(pid,))

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def raid(self):
        self.assertTrue(self.game.spawn_boss('goblin_king').ok)
        for pid in ('1','2','3'):
            self.assertTrue(self.game.raid_join(pid).ok)
        self.assertTrue(self.game.start_raid().ok)
        self.game.active_boss['current_hp'] = 9999999
        self.game.active_boss['max_hp'] = 9999999
        self.game.active_boss['attacks_per_round'] = 0

    def test_every_job_has_four_different_limits_with_level_locks(self):
        self.assertEqual(set(self.data.limit_breaks),set(self.data.jobs))
        self.assertEqual(sum(map(len,self.data.limit_breaks.values())),72)
        self.assertEqual(len({tech['id'] for moves in self.data.limit_breaks.values() for tech in moves}),72)
        for job in self.data.jobs:
            meta = {'job_id':job,'job_level':49,'hp':10}
            self.assertFalse(self.game._limit_options(meta))
            for level,count in ((50,1),(74,1),(75,2),(89,2),(90,3),(98,3),(99,4)):
                meta['job_level'] = level
                self.assertEqual(len(self.game._limit_options(meta)),count,(job,level))

    def test_raid_queue_does_not_consume_gauge_until_resolution(self):
        self.raid()
        actor = self.game.raid_roster['3']
        actor['limit'] = 100
        blocked = self.game.limit_break('3','95')
        self.assertFalse(blocked.ok)
        result = self.game.limit_break('3','75')
        self.assertTrue(result.ok,result.messages)
        self.assertEqual(actor['limit'],100)
        self.assertEqual(actor['action']['limit_level'],75)
        self.assertEqual(actor['action']['raid_round'],1)
        overlay = self.game._overlay_payload()
        mage = next(x for x in overlay['members'] if x['name']=='Caster')
        self.assertTrue(mage['limit_ready'])
        self.assertEqual(mage['limit'],100)
        self.assertEqual(mage['action'],'Flare Star')
        self.assertEqual(self.game._portal_live_combat_controls('3',event='raid')['limit']['charge'],100)
        before = int(self.game.active_boss['current_hp'])
        self.assertTrue(self.game.raid_round().ok)
        self.assertEqual(self.game.raid_roster['3']['limit'],0)
        self.assertLess(self.game.active_boss['current_hp'],before)
        self.assertEqual(self.db.one("SELECT limit_breaks FROM players WHERE twitch_id='3'")['limit_breaks'],1)

    def test_raid_queued_limit_can_be_replaced_without_wasting_gauge(self):
        self.raid()
        actor = self.game.raid_roster['1'];actor['limit']=100
        self.assertTrue(self.game.limit_break('1','50').ok)
        self.assertTrue(self.game.battle_defend('1').ok)
        self.assertEqual(actor['limit'],100)
        self.assertTrue(self.game.raid_round().ok)
        self.assertGreater(actor['limit'],0)
        self.assertEqual(self.db.one("SELECT limit_breaks FROM players WHERE twitch_id='1'")['limit_breaks'],0)

    def test_raid_white_mage_lv90_restores_and_revives(self):
        self.raid()
        caster = self.game.raid_roster['2'];caster['limit']=100
        self.game.raid_roster['1']['hp']=0
        self.game.raid_roster['1']['ko_counted']=True
        caster['hp']=max(1,int(caster['max_hp']//3))
        self.assertTrue(self.game.limit_break('2','90').ok)
        self.assertTrue(self.game.raid_round().ok)
        self.assertGreater(self.game.raid_roster['1']['hp'],0)
        self.assertFalse(self.game.raid_roster['1']['ko_counted'])
        self.assertGreater(self.game.raid_roster['2']['hp'],int(caster['max_hp']//3))
        self.assertEqual(caster['limit'],0)

    def test_active_battle_limit_gauge_progress_and_consumption(self):
        opened=self.game.venture('1',bypass_cooldown=True)
        self.assertTrue(opened.ok,opened.messages)
        self.assertTrue(self.game.start_encounter_battle(opened.data['encounter_id']).ok)
        actor=self.game.encounter_roster['1']
        self.assertEqual(actor['limit'],0)
        self.game.active_encounter['monster_hp']=999999
        self.game.active_encounter['monster_max_hp']=999999
        self.assertFalse(self.game.limit_break('1').ok)
        self.assertTrue(self.game.battle_defend('1').ok)
        from unittest.mock import patch
        with patch.object(self.game,'_active_enemy_turn',return_value=None):
            self.assertTrue(self.game.advance_encounter_round(opened.data['encounter_id']).ok)
        self.assertGreaterEqual(actor['limit'],12)
        actor['limit']=100
        self.assertTrue(self.game.limit_break('1','50').ok)
        self.assertEqual(actor['action']['kind'],'limit')
        self.assertEqual(actor['limit'],100)
        with patch.object(self.game,'_active_enemy_turn',return_value=None):
            self.assertTrue(self.game.advance_encounter_round(opened.data['encounter_id']).ok)
        self.assertEqual(actor['limit'],0)
        self.assertEqual(self.db.one("SELECT limit_breaks FROM players WHERE twitch_id='1'")['limit_breaks'],1)

if __name__=='__main__': unittest.main()

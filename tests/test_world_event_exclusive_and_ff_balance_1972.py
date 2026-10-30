"""v1.9.97.2: event-only bosses and Final Fantasy-style encounter reward bands."""
from __future__ import annotations

import random
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from crystal_guild.balance import encounter_reward_factor, dungeon_repeat_bonus_factor
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.world_events import WORLD_EVENTS

ROOT = Path(__file__).resolve().parents[1]


class EventExclusivityBalanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / 'guild.db')
        self.data = GameData(ROOT / 'data')
        self.game = CrystalGuildEngine(self.db, self.data, rng=random.Random(721),
                                      overlay_state_path=str(Path(self.temp.name) / 'overlay.json'))
        self.game.recruit('1001','hero','Hero')
        self.game.choose_job('1001','warrior')

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_no_world_event_templates_in_dungeons_or_trials(self):
        reserved = {e['base_monster_id'] for e in WORLD_EVENTS}
        for dungeon in [*self.data.dungeons.values(), *self.data.ascension_dungeons.values()]:
            for room in dungeon.get('rooms', []):
                self.assertNotIn(room.get('monster_id'), reserved, dungeon['id'])
        for trial in self.data.ascension_trials.values():
            self.assertNotIn(trial['guardian'], reserved, trial['id'])

    def test_elite_world_event_templates_not_in_normal_exploration(self):
        elite = {e['base_monster_id'] for e in WORLD_EVENTS if e.get('tier')=='elite'}
        for region in self.data.regions.values():
            for encounter in region.get('encounters', []):
                self.assertNotIn(encounter['monster_id'], elite)
        for region in self.data.expedition_regions.values():
            for encounter in region.get('encounters', []) + region.get('rare_encounters', []):
                self.assertNotIn(encounter['monster_id'], elite)
            self.assertNotIn((region.get('boss') or {}).get('monster_id'), elite)
        self.assertEqual(self.data.validate(), [])

    def test_event_only_spawns_while_stream_live(self):
        offline = self.game.maybe_spawn_world_event(stream_live=False, force=True)
        self.assertFalse(offline.data.get('world_event_spawned'))
        self.assertIsNone(self.game.active_encounter)
        online = self.game.maybe_spawn_world_event(stream_live=True, now=time.time(), force=True)
        self.assertTrue(online.data['world_event_spawned'])
        self.assertEqual(self.game.active_encounter['kind'],'world_event')
        ended = self.game.end_world_event_if_offline()
        self.assertTrue(ended.data['world_event_ended'])
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})
        self.assertFalse(self.game.end_world_event_if_offline().data['world_event_ended'])

    def test_daemon_cancels_world_event_when_stream_offline(self):
        from crystal_guild.encounter_daemon import EncounterDaemon
        notices = []
        self.game.maybe_spawn_world_event(stream_live=True, force=True)
        daemon = EncounterDaemon(self.game, notices.append, stream_live_lookup=lambda: False)
        self.assertTrue(daemon._tick_world_event_spawn(time.time()))
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(len(notices), 1)
        self.assertTrue(notices[0].data.get("world_event_ended"))

    def test_elite_event_requires_player_level_not_just_guild_level(self):
        self.db.execute('UPDATE players SET level=99 WHERE twitch_id=?',('1001',))
        self.game.rng.choice = lambda seq: next(e for e in seq if e['id']=='frostveil_tempest')
        with patch('crystal_guild.engine.seasonal_event_state',return_value={'active':False}):
            result=self.game.maybe_spawn_world_event(stream_live=True,force=True)
        self.assertTrue(result.ok)
        self.game.recruit('1002','newcomer','Newcomer')
        self.game.choose_job('1002','warrior')
        blocked=self.game.join_encounter('1002')
        self.assertFalse(blocked.ok)
        self.assertIn('Lv.80',' '.join(blocked.messages))
        self.assertNotIn('1002',self.game.encounter_roster)

    def test_fights_near_own_level_are_worth_more_than_farming_low_level(self):
        self.assertAlmostEqual(encounter_reward_factor(60,60),1.0)
        self.assertGreater(encounter_reward_factor(60,55),encounter_reward_factor(60,45))
        self.assertGreater(encounter_reward_factor(60,45),encounter_reward_factor(60,20))
        self.assertEqual(encounter_reward_factor(99,1),0.05)
        self.assertEqual(encounter_reward_factor(20,30),1.5)
        self.assertEqual(dungeon_repeat_bonus_factor(99,30),0.05)
        self.assertEqual(dungeon_repeat_bonus_factor(55,55),1.0)

    def test_repeat_dungeon_completion_scales_down_but_first_clear_not_cut(self):
        self.db.execute('UPDATE players SET level=99 WHERE twitch_id=?',('1001',))
        dungeon=self.data.dungeons['whiteglass_bastion']
        state=lambda:{'run_id':'test','dungeon_id':'whiteglass_bastion','room_index':8,
                       'status':'choice','cache':{'xp':0,'jp':0,'gil':0,'items':[]},
                       'history':[],'discoveries':[],'modifiers':{}}
        first=self.game._dungeon_finish('1001',state(),outcome='complete')
        repeat=self.game._dungeon_finish('1001',state(),outcome='complete')
        self.assertEqual(first.data['dungeon_result']['rewards']['gil'],
                         dungeon['completion_bonus']['gil']+dungeon['first_clear_bonus']['gil'])
        self.assertLessEqual(repeat.data['dungeon_result']['rewards']['gil'],
                             max(1,int(dungeon['completion_bonus']['gil']*0.06)))

if __name__=='__main__': unittest.main()

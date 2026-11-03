"""V2.0.1: Portal Limit Break action must reach the authoritative combat resolver."""
from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class LimitPortalAction201Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'limit-portal.db')
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / 'data'), rng=random.Random(201),
            venture_cooldown_seconds=0, venture_treasure_chance=0,
            encounter_round_seconds=90, raid_round_seconds=90,
            overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'),
        )
        self.assertTrue(self.game.recruit('1', 'heroa', 'Hero A').ok)
        self.assertTrue(self.game.choose_job('1', 'warrior').ok)
        self.db.execute("UPDATE player_jobs SET level=75 WHERE player_id='1' AND job_id='warrior'")
        self.db.execute("UPDATE players SET level=75 WHERE twitch_id='1'")
        self.worker = PortalActionWorker(self.game, 'https://example.test', 'key', stream_live_lookup=lambda: True)
        self.sequence = 0

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def portal_limit(self, event, event_id, round_no=1, choice='50'):
        self.sequence += 1
        return self.worker._execute({
            'id': f'v201-portal-limit-{self.sequence}',
            'protocol_version': ACTION_PROTOCOL_VERSION,
            'twitch_id': '1', 'username': 'heroa',
            'type': 'LIVE_EVENT_ACTION',
            'payload': {'event': event, 'event_id': event_id,
                        'round': round_no, 'kind': 'limit', 'choice': choice},
        })

    def test_venture_limit_is_accepted_queued_and_actually_resolves(self):
        opened = self.game.venture('1', bypass_cooldown=True)
        self.assertTrue(opened.ok, opened.messages)
        encounter_id = int(opened.data['encounter_id'])
        self.assertTrue(self.game.start_encounter_battle(encounter_id).ok)
        meta = self.game.encounter_roster['1']
        meta['limit'] = 100
        self.game.active_encounter['monster_hp'] = 1_000_000
        self.game.active_encounter['monster_max_hp'] = 1_000_000
        ok, message, result = self.portal_limit('venture', str(encounter_id))
        self.assertTrue(ok, message)
        self.assertEqual(meta['action']['kind'], 'limit')
        self.assertEqual(meta['action']['limit_level'], 50)
        self.assertEqual(result['adventure_state']['encounter']['controls']['queued_action'], 'Mountain Buster')
        self.assertEqual(result['adventure_state']['encounter']['controls']['queued_action_kind'], 'limit')
        before = self.game.active_encounter['monster_hp']
        with patch.object(self.game, '_active_enemy_turn', return_value=None):
            self.assertTrue(self.game.advance_encounter_round(encounter_id).ok)
        self.assertLess(self.game.active_encounter['monster_hp'], before)
        self.assertEqual(meta['limit'], 0)
        self.assertEqual(self.db.one("SELECT limit_breaks FROM players WHERE twitch_id='1'")['limit_breaks'], 1)

    def test_world_event_limit_reaches_active_encounter(self):
        spawned = self.game.maybe_spawn_world_event(stream_live=True, force=True)
        self.assertTrue(spawned.ok, spawned.messages)
        self.assertTrue(spawned.data['world_event_spawned'])
        encounter_id = int(spawned.data['encounter_id'])
        self.assertTrue(self.game.join_encounter('1').ok)
        self.assertTrue(self.game.start_encounter_battle(encounter_id).ok)
        meta = self.game.encounter_roster['1']
        meta['limit'] = 100
        self.game.active_encounter['monster_hp'] = 1_000_000
        self.game.active_encounter['monster_max_hp'] = 1_000_000
        ok, message, result = self.portal_limit('world_event', str(encounter_id))
        self.assertTrue(ok, message)
        self.assertEqual(meta['action']['kind'], 'limit')
        self.assertEqual(result['adventure_state']['encounter']['controls']['queued_action'], 'Mountain Buster')
        self.assertEqual(result['adventure_state']['encounter']['controls']['queued_action_kind'], 'limit')
        with patch.object(self.game, '_active_enemy_turn', return_value=None):
            self.assertTrue(self.game.advance_encounter_round(encounter_id).ok)
        self.assertEqual(meta['limit'], 0)
        self.assertEqual(self.db.one("SELECT limit_breaks FROM players WHERE twitch_id='1'")['limit_breaks'], 1)

    def test_raid_limit_reaches_raid_resolver_and_updates_overlay(self):
        self.assertTrue(self.game.spawn_boss('goblin_king').ok)
        event_id = self.game._raid_instance_id(self.game.active_boss)
        self.assertTrue(self.game.raid_join('1').ok)
        self.assertTrue(self.game.start_raid().ok)
        meta = self.game.raid_roster['1']
        meta['limit'] = 100
        self.game.active_boss['current_hp'] = 10_000_000
        self.game.active_boss['max_hp'] = 10_000_000
        self.game.active_boss['attacks_per_round'] = 0
        ok, message, result = self.portal_limit('raid', event_id)
        self.assertTrue(ok, message)
        self.assertEqual(meta['action']['kind'], 'limit')
        self.assertEqual(meta['action']['raid_round'], 1)
        self.assertEqual(result['adventure_state']['raid']['controls']['queued_action'], 'Mountain Buster')
        self.assertEqual(result['adventure_state']['raid']['controls']['queued_action_kind'], 'limit')
        before = self.game.active_boss['current_hp']
        self.assertTrue(self.game.raid_round().ok)
        self.assertLess(self.game.active_boss['current_hp'], before)
        self.assertEqual(meta['limit'], 0)
        self.assertEqual(self.db.one("SELECT limit_breaks FROM players WHERE twitch_id='1'")['limit_breaks'], 1)

    def test_limit_remains_locked_below_100_gauge(self):
        opened = self.game.venture('1', bypass_cooldown=True)
        encounter_id = int(opened.data['encounter_id'])
        self.assertTrue(self.game.start_encounter_battle(encounter_id).ok)
        meta = self.game.encounter_roster['1']
        meta['limit'] = 85
        ok, message, result = self.portal_limit('venture', str(encounter_id))
        self.assertFalse(ok)
        self.assertIn('85%', message)
        self.assertIsNone(meta['action'])
        self.assertEqual(meta['limit'], 85)
        self.assertEqual(self.db.one("SELECT limit_breaks FROM players WHERE twitch_id='1'")['limit_breaks'], 0)


if __name__ == '__main__':
    unittest.main()

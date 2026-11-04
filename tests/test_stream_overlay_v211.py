"""Venture / World Event OBS strip: separate data, persistent telegraph, no leaks."""
from __future__ import annotations
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.bestiary_progress import progress_for
from crystal_guild.portal_sync import PortalSyncClient
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]

class StreamOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data = GameData(ROOT / "data")
        self.db = Database(Path(self.temp.name)/"combat.db")
        self.file = Path(self.temp.name)/"overlay"/"state.json"
        self.game = CrystalGuildEngine(self.db,self.data,venture_cooldown_seconds=0,
            encounter_join_seconds=5,encounter_round_seconds=5,
            overlay_state_path=str(self.file),rng=random.Random(12))
        self.game.recruit('1','tester','Tester')
        self.game.choose_job('1','warrior')
    def tearDown(self):
        self.db.close()
        self.temp.cleanup()
    def published(self):
        return json.loads(self.file.with_name('stream_state.json').read_text())
    def test_stream_overlay_never_replaces_raid_file(self):
        raid_before = json.loads(self.file.read_text())
        opened = self.game.venture('1',bypass_cooldown=True)
        self.assertTrue(opened.ok)
        rally = self.published()
        self.assertTrue(rally['active'])
        self.assertEqual(rally['kind'],'venture')
        self.assertEqual(rally['status'],'RALLY')
        self.assertEqual(rally['weaknesses'],[])
        self.assertEqual(json.loads(self.file.read_text()),raid_before)
        started = self.game.start_encounter_battle(opened.data['encounter_id'])
        self.assertTrue(started.ok)
        live = self.published()
        self.assertEqual(live['status'],'COMBAT')
        self.assertEqual(live['attack_kind'],self.game.active_encounter['stream_enemy_intent']['kind'])
        self.assertGreater(live['max_hp'],0)
        self.assertGreaterEqual(live['hp'],0)
    def test_joined_member_only_research_weakness_visibility(self):
        opened = self.game.venture('1',bypass_cooldown=True)
        self.assertTrue(opened.ok)
        enemy_id = self.game.active_encounter['monster_id']
        threshold = next(i for i in range(1,200) if 'weakness' in progress_for(self.data,enemy_id,i).get('visible_fields',[]))
        self.db.execute('INSERT INTO bestiary(player_id,monster_id,defeats) VALUES(?,?,?)',('1',enemy_id,threshold))
        view = self.game._stream_overlay_payload()
        self.assertEqual(view['weaknesses'],[self.data.monsters[enemy_id]['weakness'].lower()])
        # Losing the knowing participant from the encounter must immediately hide it.
        self.game.encounter_roster.clear()
        self.assertEqual(self.game._stream_overlay_payload()['weaknesses'],[])
    def test_world_event_research_requires_previous_victory(self):
        self.game.venture('1',bypass_cooldown=True)
        from crystal_guild.world_events import WORLD_EVENTS
        event = WORLD_EVENTS[0]
        self.game.active_encounter['kind']='world_event'
        self.game.active_encounter['world_event_id']=event['id']
        self.game.active_encounter['monster_id']=event['base_monster_id']
        self.assertEqual(self.game._stream_overlay_payload()['weaknesses'],[])
        self.db.execute('INSERT INTO player_world_event_clears(player_id,world_event_id,clears,last_cleared_at) VALUES(?,?,?,CURRENT_TIMESTAMP)',('1',event['id'],1))
        view = self.game._stream_overlay_payload()
        self.assertEqual(view['weaknesses'],[self.data.monsters[event['base_monster_id']]['weakness'].lower()])
    def test_telegraph_resolves_precommitted_attack_not_a_second_roll(self):
        opened = self.game.venture('1',bypass_cooldown=True)
        self.game.start_encounter_battle(opened.data['encounter_id'])
        planned = dict(self.game.active_encounter['stream_enemy_intent'])
        monster = self.game._encounter_monster(self.game.active_encounter)
        # Do not choose a new move when the already telegraphed action resolves.
        with patch('crystal_guild.engine.choose_enemy_action', side_effect=AssertionError('enemy move rerolled')):
            self.game._active_enemy_turn(monster, [])
        self.assertNotIn('stream_enemy_intent', self.game.active_encounter)
        self.assertIn(planned['kind'],{'attack','special','utility'})
    def test_sync_posts_separate_hud_without_replacing_raid_payload(self):
        self.game.venture('1',bypass_cooldown=True)
        repo = PortalRepository(Path(self.temp.name)/'combat.db', ROOT/'data')
        try:
            sync = PortalSyncClient(repo,'http://localhost:8080','test-key',overlay_state_path=self.file)
            posts = []
            sync._post = lambda path, body: posts.append((path, body)) or {}
            sync.sync_once(force=True)
            self.assertTrue(any(path == '/api/sync/stream-overlay' for path,_ in posts))
            self.assertTrue(any(path == '/api/sync/overlay' for path,_ in posts))
            stream = next(body for path,body in posts if path == '/api/sync/stream-overlay')
            self.assertTrue(stream['stream_overlay']['active'])
            self.assertFalse(any('roster' in k or 'player_id' in k for k in stream['stream_overlay']))
        finally:
            repo.close()

    def test_sync_sanitizes_and_reads_separate_stream_file(self):
        self.game.venture('1',bypass_cooldown=True)
        repo = PortalRepository(Path(self.temp.name)/'combat.db', ROOT/'data')
        try:
            sync = PortalSyncClient(repo,'http://localhost:8080','test-key',overlay_state_path=self.file)
            payload = sync.build_stream_overlay_snapshot()
            self.assertEqual(payload['schema_version'],1)
            self.assertTrue(payload['stream_overlay']['active'])
            self.assertFalse(any('player' in k or 'twitch' in k for k in payload['stream_overlay']))
        finally:
            repo.close()

if __name__ == '__main__': unittest.main()

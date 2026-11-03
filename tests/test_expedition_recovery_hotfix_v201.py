from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import PortalActionWorker, ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]

class ExpeditionRecoveryHotfixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        folder = Path(self.temp.name)
        self.db = Database(folder / 'guild.db')
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / 'data'), rng=random.Random(11), overlay_state_path=str(folder/'overlay.json'))
        for pid, username in (('100','playerone'),('200','playertwo')):
            self.assertTrue(self.game.recruit(pid, username, username).ok)
            self.assertTrue(self.game.choose_job(pid, 'warrior').ok)
            self.db.execute('UPDATE players SET level=99 WHERE twitch_id=?', (pid,))
            hp=self.game._max_hp(self.game._player(pid))
            self.db.execute('UPDATE players SET current_hp=? WHERE twitch_id=?', (hp,pid))
            self.db.execute('INSERT INTO player_chocobos(player_id,name,registered_at) VALUES (?,?,CURRENT_TIMESTAMP)', (pid, username+' chocobo'))
        self.db.execute('UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1')
        self.worker=PortalActionWorker(self.game,'https://example.invalid','testkey',owner_id='900')

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def owner(self, command, argument, action_id):
        return self.worker._execute({'id':action_id,'protocol_version':ACTION_PROTOCOL_VERSION,'type':'STREAMER_COMMAND','twitch_id':'900','username':'streamer','payload':{'command':command,'argument':argument}})

    def test_expedition_launches_while_unrelated_boss_is_active_and_resolves_via_portal(self):
        self.assertTrue(self.game.spawn_boss('ifrit').ok)
        self.assertTrue(self.game.raid_join('200').ok)
        launched=self.game.portal_expedition_start('100','emerald_wilds','scout','hotfix-launch')
        self.assertTrue(launched.ok, launched.messages)
        self.assertEqual(self.game._expedition_load('100')['status'],'travel')
        # The authoritative timer still rejects early resolution.
        denied=self.game.portal_expedition_resolve_stage('100','hotfix-early')
        self.assertFalse(denied.ok)
        self.assertIn('Travel completes',' '.join(denied.messages))
        state=self.game._expedition_load('100');state['travel_ready_at']=0;self.game._expedition_save('100',state)
        with patch('crystal_guild.engine.expedition_event_weights',return_value=(['resource'],[1.0])):
            resolved=self.game.portal_expedition_resolve_stage('100','hotfix-resolve')
        self.assertTrue(resolved.ok, resolved.messages)
        self.assertEqual(self.game._expedition_load('100')['status'],'choice')
        self.assertTrue(self.game.portal_expedition_return('100','hotfix-return').ok)
        self.assertIsNone(self.game._expedition_load('100'))
        self.assertIn('200',self.game.raid_roster)

    def test_admin_removal_is_selective_idempotent_and_preserves_progress(self):
        self.assertTrue(self.game.expedition_start('100','emerald_wilds','scout').ok)
        self.assertTrue(self.game.expedition_start('200','emerald_wilds','scout').ok)
        self.db.execute('UPDATE players SET gil=999 WHERE twitch_id=?',('100',))
        ok,message,data=self.owner('removeactivity','playerone','hotfix-remove-1')
        self.assertTrue(ok,message)
        self.assertEqual(data['removed_activities'],['Expedition'])
        self.assertIsNone(self.game._expedition_load('100'))
        self.assertIsNotNone(self.game._expedition_load('200'))
        self.assertEqual(self.game._player('100')['gil'],999)
        duplicate=self.owner('removeactivity','playerone','hotfix-remove-1')
        self.assertEqual(duplicate,(ok,message,data))
        self.assertIsNone(self.game._expedition_load('100'))
        unauthorized=self.worker._execute({'id':'unauthorized','protocol_version':ACTION_PROTOCOL_VERSION,'type':'STREAMER_COMMAND','twitch_id':'100','username':'playerone','payload':{'command':'removeactivity','argument':'playertwo'}})
        self.assertFalse(unauthorized[0]);self.assertIsNotNone(self.game._expedition_load('200'))

    def test_recovers_persisted_activities_and_runtime_hunts(self):
        self.db.execute("INSERT INTO player_expeditions(player_id,state_json,started_at,updated_at) VALUES('100','{}',1,1)")
        self.db.execute("INSERT INTO solo_expeditions(player_id,state_json,started_at,updated_at) VALUES('100','{}',1,1)")
        self.db.execute("INSERT INTO player_dungeons(player_id,state_json,started_at,updated_at) VALUES('100','{}',1,1)")
        self.game.active_hunts['100']={'id':1,'hunt_id':'red_hot_problem','resolves_at':9999999999}
        ok,_,data=self.owner('removeactivity','playerone','hotfix-remove-all')
        self.assertTrue(ok)
        self.assertEqual(set(data['removed_activities']),{'Expedition','Solo Venture','Dungeon','Hunt'})
        self.assertNotIn('100',self.game.active_hunts)
        for tbl in ('player_expeditions','solo_expeditions','player_dungeons'):
            self.assertFalse(self.db.one(f'SELECT 1 FROM {tbl} WHERE player_id=?',('100',)))

    def test_removing_raid_member_preserves_other_players_and_last_member_clears_combat(self):
        self.assertTrue(self.game.spawn_boss('ifrit').ok)
        self.assertTrue(self.game.raid_join('100').ok)
        self.assertTrue(self.game.raid_join('200').ok)
        ok,_,data=self.owner('removeactivity','playerone','hotfix-remove-raid1')
        self.assertTrue(ok);self.assertIn('Raid',data['removed_activities'])
        self.assertIn('200',self.game.raid_roster)
        self.assertIsNotNone(self.game.active_boss)
        # When the last raider exits a battle in progress, the boss cannot remain stranded.
        self.game.active_boss['state']='combat'
        ok,_,data=self.owner('removeactivity','playertwo','hotfix-remove-raid2')
        self.assertTrue(ok)
        self.assertIsNone(self.game.active_boss)

    def test_unknown_player_is_not_removed(self):
        ok,message,_=self.owner('removeactivity','doesnotexist','hotfix-remove-unknown')
        self.assertFalse(ok)
        self.assertIn('not found',message)

if __name__=='__main__': unittest.main()

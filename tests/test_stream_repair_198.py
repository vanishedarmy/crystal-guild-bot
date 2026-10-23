"""v1.9.8 stream repair: raid revive, world-event Mist, overlay and public status."""
from __future__ import annotations
import json
import random
import tempfile
import time
import unittest
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.portal_sync import PortalSyncClient

ROOT = Path(__file__).resolve().parents[1]

class StreamRepair198(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'guild.db'
        self.db = Database(self.path)
        self.overlay = Path(self.temp.name) / 'overlay.json'
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / 'data'),
            overlay_state_path=str(self.overlay),rng=random.Random(198),
            venture_cooldown_seconds=0)
        for pid, username in [('1','alpha'),('2','beta')]:
            self.assertTrue(self.game.recruit(pid, username, username.title()).ok)
            self.assertTrue(self.game.choose_job(pid, 'warrior').ok)
            self.db.execute('UPDATE players SET gil=5000 WHERE twitch_id=?',(pid,))
        self.repo = PortalRepository(self.path, ROOT/'data')

    def tearDown(self):
        self.repo.close()
        self.db.close()
        self.temp.cleanup()

    def test_raid_revive_uses_mention_and_name_or_username(self):
        self.assertTrue(self.game.spawn_boss('goblin_king').ok)
        self.assertTrue(self.game.raid_join('1').ok)
        self.assertTrue(self.game.raid_join('2').ok)
        self.assertTrue(self.game.start_raid().ok)
        self.game._change_item('1','phoenix_down',1,'test')
        self.game.raid_roster['2']['hp'] = 0
        self.assertTrue(self.game.revive_raid('1','@beta').ok)
        self.assertGreater(self.game.raid_roster['2']['hp'],0)
        self.assertFalse(self.game.revive_raid('1','@beta').ok)
        self.assertFalse(self.game.revive_raid('1','').ok)
        self.assertEqual(self.game._inventory_qty('1','phoenix_down'),0)

    def test_world_event_once_per_player_no_double_charge_and_new_event_resets(self):
        opened=self.game.venture('1',bypass_cooldown=True)
        self.assertTrue(opened.ok,opened.messages)
        self.assertTrue(self.game.join_encounter('2').ok)
        self.assertTrue(self.game.start_encounter_battle(opened.data['encounter_id']).ok)
        self.game.active_encounter['kind']='world_event'
        for person in self.game.encounter_roster.values(): person['hp'] = 1
        before=int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")['gil'])
        self.assertTrue(self.game.heal_party('1','2').ok)
        self.assertEqual(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")['gil'],before-250)
        result=self.game.heal_party('1','4')
        self.assertFalse(result.ok)
        self.assertTrue(self.game.encounter_roster['1']['mist_heal_used'])
        self.assertEqual(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")['gil'],before-250)
        self.game.encounter_roster['2']['hp']=1
        self.assertTrue(self.game.heal_party('2','1').ok)
        receipt=self.db.one("SELECT source FROM transactions WHERE player_id='1' AND amount=-250")
        self.assertEqual(receipt['source'],'world_event_party_heal')
        restarted=CrystalGuildEngine(Database(self.path),GameData(ROOT/'data'),overlay_state_path=str(Path(self.temp.name)/'second.json'))
        try:
            self.assertFalse(restarted.heal_party('1','1').ok)
        finally: restarted.db.close()

    def test_overlay_sync_keeps_raid_roster_without_ids(self):
        self.assertTrue(self.game.spawn_boss('goblin_king').ok)
        self.assertTrue(self.game.raid_join('1').ok)
        self.assertTrue(self.game.raid_join('2').ok)
        client=PortalSyncClient(self.repo,'https://invalid.test','key',overlay_state_path=self.overlay)
        public=client.build_overlay_snapshot()['overlay']
        self.assertEqual(public['raiders'],2)
        self.assertEqual([m['name'] for m in public['members']],['Alpha','Beta'])
        self.assertEqual(public['members'][0]['state'],'JOINED')
        self.assertEqual(public['rally_closes_at'],int(self.game.active_boss['closes_at']))
        self.assertNotIn('twitch_id',json.dumps(public))
        self.assertNotIn('raid_instance_id',json.dumps(public))

    def test_portal_raid_status_and_round_deadline(self):
        self.assertTrue(self.game.spawn_boss('goblin_king').ok)
        self.assertTrue(self.game.raid_join('1').ok)
        rally=self.repo.overview('alpha')['status']
        self.assertEqual(rally['state'],'in_raid')
        self.assertIn('Rally',rally['label'])
        self.assertGreater(rally['until'],int(time.time()))
        self.assertTrue(self.game.start_raid().ok)
        battle=self.repo.overview('alpha')['status']
        self.assertEqual(battle['state'],'in_raid')
        self.assertIn('In Battle',battle['label'])
        self.assertGreater(battle['until'],int(time.time()))
        # A nonparticipant must not inherit the Raid indicator.
        self.assertEqual(self.repo.overview('beta')['status']['state'],'ready')

    def test_portal_world_event_battle_and_chocobo_expedition(self):
        opened=self.game.venture('1',bypass_cooldown=True)
        self.assertTrue(opened.ok)
        self.game.active_encounter['kind']='world_event'
        self.game._persist_runtime_state()
        status=self.repo.overview('alpha')['status']
        self.assertEqual(status['state'],'in_battle')
        self.assertIn('World Event',status['label'])
        self.assertTrue(self.game.start_encounter_battle(opened.data['encounter_id']).ok)
        self.assertGreater(self.repo.overview('alpha')['status']['remaining_seconds'],0)
        self.game.active_encounter=None;self.game.encounter_roster.clear()
        self.game._persist_runtime_state()
        with self.db.tx() as conn:
            conn.execute("INSERT INTO player_expeditions(player_id,state_json,started_at,updated_at) VALUES (?,?,?,?)",
                         ('1',json.dumps({'status':'travel','transport':'chocobo','travel_ready_at':int(time.time())+150}),int(time.time()),int(time.time())))
        status=self.repo.overview('alpha')['status']
        self.assertEqual(status['state'],'on_expedition')
        self.assertIn('Chocobo',status['label'])
        self.assertGreater(status['remaining_seconds'],140)

    def test_portal_hunt_status_has_deadline_and_rest_fallback(self):
        player=self.db.one("SELECT * FROM players WHERE twitch_id='1'")
        with self.repo.connect() as conn:
            self.assertEqual(self.repo._status(player,conn=conn)['state'],'ready')
        self.game.active_hunts['1']={'hunt_id':'red_hot_problem','resolves_at':time.time()+400,'started_at':time.time()}
        self.game._persist_runtime_state()
        live=self.repo.overview('alpha')['status']
        self.assertEqual(live['state'],'on_hunt')
        self.assertGreater(live['remaining_seconds'],390)
        self.assertGreater(live['until'],int(time.time()))
        self.game.active_hunts.clear();self.game._persist_runtime_state()
        self.db.execute('UPDATE players SET camp_until=? WHERE twitch_id=?',(int(time.time())+300,'1'))
        self.assertEqual(self.repo.overview('alpha')['status']['state'],'resting')

if __name__=='__main__': unittest.main()

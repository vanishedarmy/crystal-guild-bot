"""Relic Portal stage advancement: shared authoritative rules and exactly-once receipts."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import PortalActionWorker, ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]

class RelicPortalAwakenTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'guild.db')
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / 'data'), overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'))
        self.assertTrue(self.game.recruit('100', 'relichero', 'Relic Hero').ok)
        self.db.execute("UPDATE players SET level=70,current_job='dragoon',gil=100000,hunt_seals=400 WHERE twitch_id='100'")
        self.db.execute("INSERT OR REPLACE INTO player_jobs(player_id,job_id,level,jp) VALUES('100','dragoon',70,0)")
        for item, qty in [('mythril_ore',20),('crystal_shard',20)]:
            self.game._change_item('100', item, qty, 'test')
        self.worker = PortalActionWorker(self.game, 'https://guild.example', 'test-key')

    def tearDown(self):
        self.db.close(); self.tmp.cleanup()

    def request(self, action_id='relic:stage1', payload=None):
        return self.worker._execute({'id':action_id, 'protocol_version':ACTION_PROTOCOL_VERSION,
            'twitch_id':'100', 'username':'relichero', 'type':'RELIC_AWAKEN',
            'payload':payload if payload is not None else {'relic_id':'gae_bolg'}})

    def test_stage_requires_accepted_quest_and_exact_class(self):
        ok, message, _ = self.request()
        self.assertFalse(ok)
        self.assertIn('Begin', message)
        self.assertTrue(self.game.begin_relic_quest('100','gae_bolg').ok)
        self.db.execute("UPDATE players SET current_job='warrior' WHERE twitch_id='100'")
        ok, message, _ = self.request('wrong-job')
        self.assertFalse(ok)
        self.assertIn('Dragoon', message)
        self.db.execute("UPDATE players SET current_job='dragoon' WHERE twitch_id='100'")

    def test_awaken_spends_resources_once_and_replay_does_not_advance_again(self):
        self.assertTrue(self.game.begin_relic_quest('100','gae_bolg').ok)
        before = self.db.one("SELECT gil,hunt_seals FROM players WHERE twitch_id='100'")
        ok, message, data = self.request('relic:unique:1')
        self.assertTrue(ok, message)
        self.assertIn('RELIC AWAKENED', message)
        self.assertEqual(self.db.one("SELECT stage FROM player_relics WHERE player_id='100' AND relic_id='gae_bolg'")['stage'], 1)
        self.assertEqual(self.game._inventory_qty('100','gae_bolg_dormant'), 1)
        self.assertEqual(self.game._inventory_qty('100','mythril_ore'), 12)
        self.assertEqual(self.game._inventory_qty('100','crystal_shard'), 16)
        after = self.db.one("SELECT gil,hunt_seals FROM players WHERE twitch_id='100'")
        self.assertEqual(int(before['gil'])-int(after['gil']),5000)
        self.assertEqual(int(before['hunt_seals'])-int(after['hunt_seals']),40)
        replay_ok, replay_msg, _ = self.request('relic:unique:1')
        self.assertTrue(replay_ok, replay_msg)
        self.assertEqual(self.db.one("SELECT stage FROM player_relics WHERE player_id='100' AND relic_id='gae_bolg'")['stage'],1)
        self.assertEqual(self.game._inventory_qty('100','gae_bolg_dormant'),1)
        self.assertEqual(self.game._inventory_qty('100','mythril_ore'),12)

    def test_invalid_payload_and_insufficient_cost_never_grant_weapon(self):
        self.assertTrue(self.game.begin_relic_quest('100','gae_bolg').ok)
        for payload in ({'relic_id':'gae_bolg','stage':3}, {'relic_id':'../../bad'}, {}):
            ok, _, _ = self.request('reject-'+str(len(payload)), payload)
            self.assertFalse(ok)
        self.db.execute("UPDATE players SET gil=0 WHERE twitch_id='100'")
        ok, message, _ = self.request('relic:poor')
        self.assertFalse(ok)
        self.assertIn('not ready', message)
        self.assertEqual(self.game._inventory_qty('100','gae_bolg_dormant'),0)

if __name__ == '__main__': unittest.main()

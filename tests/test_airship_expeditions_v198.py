"""v1.9.8 Airship Expedition regression coverage; no production DB needed."""
from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class AirshipExpedition198(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'guild.db')
        self.data = GameData(ROOT / 'data')
        self.game = CrystalGuildEngine(self.db, self.data, overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'), rng=random.Random(198))
        for uid in ['198', '199']:
            self.game.recruit(uid, f'pilot{uid}', f'Pilot{uid}')
            self.game.choose_job(uid, 'warrior')
            self.db.execute('UPDATE players SET level=50 WHERE twitch_id=?', (uid,))
            p = self.game._player(uid)
            self.db.execute('UPDATE players SET current_hp=? WHERE twitch_id=?', (self.game._max_hp(p), uid))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def gate(self, built=True, core=0):
        self.db.execute('UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1')
        self.db.execute('UPDATE fellowship_airship_state SET built=? WHERE singleton_id=1', (1 if built else 0,))
        self.db.execute("UPDATE fellowship_airship_upgrades SET tier=? WHERE upgrade_id='crystal_core'", (core,))

    def test_catalog_and_original_ground_atlas_unchanged(self):
        self.assertEqual(self.data.validate(), [])
        self.assertEqual(len([r for r in self.data.expedition_regions.values() if r.get('transport') != 'airship']), 5)
        self.assertEqual(len([r for r in self.data.expedition_regions.values() if r.get('transport') == 'airship']), 6)
        self.assertEqual(self.game._expedition_atlas('198')['region_count'], 5)
        self.assertEqual(self.game._expedition_atlas('198', 'airship')['region_count'], 6)

    def test_airship_requires_guild_board_construction_level_and_core(self):
        a = self.game.expedition_start('198', 'shattered_sky_isles', 'scout')
        self.assertFalse(a.ok)
        self.gate(built=False)
        a = self.game.expedition_start('198', 'shattered_sky_isles', 'scout')
        self.assertFalse(a.ok)
        self.assertIn('constructed', ' '.join(a.messages))
        self.gate(built=True)
        a = self.game.expedition_start('198', 'aetherstorm_expanse', 'scout')
        self.assertFalse(a.ok)
        self.assertIn('Crystal Core Tier 1', ' '.join(a.messages))
        a = self.game.expedition_start('198', 'forgotten_dominion', 'scout')
        self.assertFalse(a.ok)
        self.assertIn('Crystal Core Tier 2', ' '.join(a.messages))
        self.db.execute("UPDATE players SET level=20 WHERE twitch_id='198'")
        a = self.game.expedition_start('198', 'shattered_sky_isles', 'scout')
        self.assertFalse(a.ok)
        self.assertIn('Lv.25', ' '.join(a.messages))
        self.db.execute("UPDATE players SET level=50 WHERE twitch_id='198'")
        self.assertTrue(self.game.expedition_start('198', 'shattered_sky_isles', 'scout').ok)
        state = self.game._expedition_load('198')
        self.assertEqual(state['transport'], 'airship')
        self.assertFalse(bool(self.db.one("SELECT * FROM player_chocobos WHERE player_id='198'")))

    def test_ground_still_requires_chocobo_even_when_airship_built(self):
        self.gate()
        ground = self.game.expedition_start('198', 'emerald_wilds', 'scout')
        self.assertFalse(ground.ok)
        self.assertIn('registered Chocobo', ' '.join(ground.messages))

    def test_upgrades_freeze_on_launch_and_change_airship_travel(self):
        self.gate(core=2)
        self.db.execute("UPDATE fellowship_airship_upgrades SET tier=3 WHERE upgrade_id='engine'")
        self.db.execute("UPDATE fellowship_airship_upgrades SET tier=2 WHERE upgrade_id='hull'")
        self.db.execute("UPDATE fellowship_airship_upgrades SET tier=2 WHERE upgrade_id='cargo'")
        self.db.execute("UPDATE fellowship_airship_upgrades SET tier=1 WHERE upgrade_id='survey'")
        self.assertTrue(self.game.expedition_start('198', 'forgotten_dominion', 'scout').ok)
        state = self.game._expedition_load('198')
        self.assertEqual(state['airship_upgrades']['engine'], 3)
        self.assertEqual(state['airship_upgrades']['hull'], 2)
        self.assertEqual(state['airship_upgrades']['cargo'], 2)
        self.assertEqual(int(state['travel_ready_at']) - int(state['travel_started_at']), 154)  # round(240 * 0.64)
        self.db.execute("UPDATE fellowship_airship_upgrades SET tier=0 WHERE upgrade_id='engine'")
        self.assertEqual(self.game._expedition_public('198')['airship_upgrades']['engine'], 3)
        self.assertAlmostEqual(self.game._expedition_defeat_keep('198', state), 0.82)

    def test_independent_runs_and_reward_persistence(self):
        self.gate()
        self.assertTrue(self.game.expedition_start('198', 'shattered_sky_isles', 'scout').ok)
        self.assertTrue(self.game.expedition_start('199', 'shattered_sky_isles', 'journey').ok)
        a = self.game._expedition_load('198');a['travel_ready_at'] = 0; self.game._expedition_save('198',a)
        with patch('crystal_guild.engine.expedition_event_weights', return_value=(['resource'], [1])):
            result = self.game.expedition_resolve_stage('198')
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game._expedition_load('198')['status'], 'choice')
        self.assertEqual(self.game._expedition_load('199')['status'], 'travel')
        bank = self.game.expedition_return('198')
        self.assertTrue(bank.ok, bank.messages)
        self.assertIsNone(self.game._expedition_load('198'))
        self.assertIsNotNone(self.game._expedition_load('199'))
        self.assertTrue(any(x.get('kind') == 'expedition' and x.get('summary',{}).get('transport') == 'airship' for x in self.game._pending_portal_adventure_results('198')))

    def test_browse_regions_and_retire_old_mission_launch(self):
        self.gate(built=True, core=1)
        board = self.game._expedition_board_state('198')
        self.assertEqual(len(board['regions']), 11)
        self.assertEqual(sum(r['unlocked'] for r in board['regions'] if r['transport'] == 'airship'), 2)
        self.assertTrue(board['airship_ready'])
        self.assertFalse(board['ground_ready'])
        self.assertFalse(self.game.set_airship_mission('merchant_escort').ok)
        self.assertFalse(self.game.fellowship_system.start_airship_mission('merchant_escort')[0])
        self.assertEqual(self.db.one('SELECT built FROM fellowship_airship_state WHERE singleton_id=1')['built'], 1)


if __name__ == '__main__':
    unittest.main()

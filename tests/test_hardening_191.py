"""Regression coverage for malformed per-region Moogle Emporium caches.

Regional stock is keyed by player, current map region and job; legacy
player_shops stock_json must no longer override these independent rotations.
"""
import json
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.emporium import eligible_stock
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class EmporiumHardening191Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'guild.db')
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / 'data'),
                                       overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'),
                                       rng=random.Random(191))
        self.assertTrue(self.game.recruit('100', 'van', 'Van').ok)
        self.db.execute("UPDATE players SET level=30,current_job='warrior' WHERE twitch_id='100'")
        self.game._shop_stock('100')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def current(self):
        p = self.game._player('100')
        context = self.game._emporium_context(p)
        region_id, job_id = context['id'], p['current_job']
        row = self.db.one('SELECT * FROM player_regional_shops WHERE player_id=? AND region_id=? AND job_id=?',
                          ('100', region_id, job_id))
        self.assertIsNotNone(row)
        allowed = {item['id'] for item in eligible_stock(p, self.game.data.items, context)}
        return row, context, allowed

    def assert_repairs(self, stock_json, expires_at=None):
        row, context, eligible = self.current()
        if expires_at is None:
            self.db.execute('UPDATE player_regional_shops SET stock_json=? WHERE player_id=? AND region_id=? AND job_id=?',
                            (stock_json, '100', context['id'], row['job_id']))
        else:
            self.db.execute('UPDATE player_regional_shops SET stock_json=?,expires_at=? WHERE player_id=? AND region_id=? AND job_id=?',
                            (stock_json, expires_at, '100', context['id'], row['job_id']))
        state = self.game.portal_shop_state('100')
        self.assertTrue(state.ok, state.messages)
        stock = state.data['stock']
        expected = min(context['stock_slots'], len(eligible))
        self.assertEqual(len(stock), expected)
        ids = [item['id'] for item in stock]
        self.assertEqual(len(set(ids)), expected)
        self.assertLessEqual(set(ids), eligible)
        saved, context2, _ = self.current()
        self.assertEqual(context2['id'], context['id'])
        self.assertEqual(json.loads(saved['stock_json']), ids)
        self.assertGreater(int(saved['expires_at']), 0)

    def test_non_array_or_malformed_rotation_self_repairs(self):
        for raw in ('{}', '42', '[', '[null]'):
            with self.subTest(raw=raw):
                self.assert_repairs(raw)

    def test_duplicated_stock_self_repairs(self):
        rows, _ = self.game._shop_stock('100')
        self.assert_repairs(json.dumps([rows[0]['id']] * 9))

    def test_bad_expiration_self_repairs(self):
        rows, _ = self.game._shop_stock('100')
        self.assert_repairs(json.dumps([r['id'] for r in rows]), 'not-a-number')

    def test_old_unscoped_cache_cannot_override_regional_stock(self):
        row, context, _ = self.current()
        original = json.loads(row['stock_json'])
        self.db.execute('UPDATE player_shops SET stock_json=? WHERE player_id=?', ('["invalid-item"]', '100'))
        refreshed, _ = self.game._shop_stock('100')
        self.assertEqual([item['id'] for item in refreshed], original)


if __name__ == '__main__':
    unittest.main()

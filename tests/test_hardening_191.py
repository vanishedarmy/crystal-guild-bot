"""Regression coverage for malformed preexisting Emporium rotation caches."""
import json
import random
import tempfile
import unittest
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
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

    def assert_repairs(self, stock_json, expires_at=None):
        if expires_at is None:
            self.db.execute('UPDATE player_regional_shops SET stock_json=? WHERE player_id=?',
                            (stock_json, '100'))
        else:
            self.db.execute('UPDATE player_regional_shops SET stock_json=?,expires_at=? WHERE player_id=?',
                            (stock_json, expires_at, '100'))
        state = self.game.portal_shop_state('100')
        self.assertTrue(state.ok, state.messages)
        stock = state.data['stock']
        self.assertEqual(len(stock), 12)
        self.assertEqual(len({item['id'] for item in stock}), 12)
        saved = self.db.one('SELECT stock_json FROM player_regional_shops WHERE player_id=?', ('100',))
        self.assertEqual(len(json.loads(saved['stock_json'])), 12)

    def test_non_array_or_malformed_rotation_self_repairs(self):
        for raw in ('{}', '42', '[', '[null]'):
            with self.subTest(raw=raw):
                self.assert_repairs(raw)

    def test_duplicated_stock_self_repairs(self):
        rows, _ = self.game._shop_stock('100')
        self.assert_repairs(json.dumps([rows[0]['id']] * 12))

    def test_bad_expiration_self_repairs(self):
        rows, _ = self.game._shop_stock('100')
        self.assert_repairs(json.dumps([r['id'] for r in rows]), 'not-a-number')


if __name__ == '__main__':
    unittest.main()

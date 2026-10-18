"""LW-0 foundation: migration 28, receipts, safe dormant player projection."""
from __future__ import annotations

import concurrent.futures
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database, DATABASE_SCHEMA_VERSION
from crystal_guild.living_world import empty_snapshot, receipt_once
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.portal_sync import MODULES, PortalSyncClient

ROOT = Path(__file__).resolve().parents[1]


class LivingWorldFoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "guild.db"
        self.db = Database(self.path)
        self.db.execute("INSERT INTO players(twitch_id,username,display_name) VALUES (?,?,?)", ("10001", "van", "Van"))
        self.catalog = GameData(ROOT / "data")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_region_registry_and_lw1_offline_policy(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 28)
        self.assertEqual([x['order'] for x in self.catalog.living_world_regions], list(range(1, 9)))
        self.assertEqual(len(self.catalog.living_world_regions), 8)
        self.assertEqual(self.catalog.validate(), [])
        self.assertTrue(self.catalog.living_world_config['enabled'])
        self.assertTrue(self.catalog.living_world_config['offline_completion_required'])
        self.assertTrue(self.catalog.living_world_config['fellowship_is_optional'])
        self.assertTrue(self.catalog.living_world_config['feature_flags']['exploration'])
        self.assertFalse(self.catalog.living_world_config['feature_flags']['world_events'])
        self.assertEqual(len(self.catalog.living_world_art_slots['slots']), 20)
        result = empty_snapshot(self.catalog.living_world_regions)
        self.assertTrue(all(r['status'] == 'locked' for r in result['regions']))
        self.assertFalse(result['playable'])

    def test_receipts_persist_and_reject_duplicates_across_restarts(self):
        self.assertTrue(receipt_once(self.db, "10001", "solo_venture", "solo:42"))
        self.assertFalse(receipt_once(self.db, "10001", "solo_venture", "solo:42"))
        self.assertTrue(receipt_once(self.db, "10001", "stream_venture", "solo:42"))
        self.db.close()
        self.db = Database(self.path)
        self.assertFalse(receipt_once(self.db, "10001", "solo_venture", "solo:42"))
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM lw_activity_receipts")['n'], 2)

    def test_receipt_race_and_input_validation(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(lambda _: receipt_once(self.db, "10001", "hunt", "hunt:1"), range(20)))
        self.assertEqual(sum(results), 1)
        with self.assertRaises(ValueError):
            receipt_once(self.db, '10001', 'raid_only', 'x')
        with self.assertRaises(ValueError):
            receipt_once(self.db, '10001', 'hunt', '')

    def test_schema_integrity_and_new_table_slots(self):
        self.assertEqual(self.db.schema_version(), 28)
        self.assertEqual(self.db.quick_check(), [])
        self.assertEqual(self.db.conn.execute('PRAGMA foreign_key_check').fetchall(), [])
        names = {r[0] for r in self.db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({'lw_region_progress','lw_activity_receipts','lw_discoveries',
                         'lw_world_events','lw_event_contributions','lw_reward_receipts',
                         'lw_world_state'}.issubset(names))

    def test_read_only_snapshot_and_private_identity(self):
        repo = PortalRepository(self.path, ROOT / 'data')
        try:
            snap = repo.living_world('van')
            self.assertEqual(len(snap['regions']), 8)
            self.assertTrue(snap['enabled'])
            self.assertTrue(snap['playable'])
            self.assertNotIn('10001', repr(snap))
            self.assertIn('living_world', MODULES)
            client = PortalSyncClient(repo, 'https://invalid.example', 'test-key')
            actual = client.build_snapshot('van')
            self.assertIn('living_world', actual['snapshot'])
            self.assertNotIn('10001', repr(actual['snapshot']['living_world']))
        finally:
            repo.close()

    def test_upgrade_27_to_28_creates_backup_and_keeps_regional_shop(self):
        # Simulate a real v27 file by dropping only the freshly created v28 tables.
        self.db.close()
        with closing(sqlite3.connect(self.path)) as raw, raw:
            raw.execute('PRAGMA foreign_keys=OFF')
            for name in ('lw_event_contributions','lw_world_events','lw_discoveries',
                         'lw_activity_receipts','lw_region_progress','lw_reward_receipts','lw_world_state'):
                raw.execute(f'DROP TABLE {name}')
            raw.execute('DELETE FROM schema_migrations WHERE version=28')
        upgraded = Database(self.path)
        try:
            self.assertEqual(upgraded.schema_version(), 28)
            self.assertTrue(upgraded.pre_migration_backup_path and upgraded.pre_migration_backup_path.is_file())
            self.assertIsNotNone(upgraded.one("SELECT name FROM sqlite_master WHERE name='player_regional_shops'"))
            self.assertEqual(upgraded.one('SELECT COUNT(*) AS n FROM players')['n'], 1)
            self.assertEqual(upgraded.quick_check(), [])
        finally:
            upgraded.close()
        self.db = Database(self.path)


if __name__ == '__main__':
    unittest.main()

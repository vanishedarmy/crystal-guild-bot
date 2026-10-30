"""Daily UTC reset, unlimited regional supplies, and class-bound Relic quest gates."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.emporium import eligible_stock, shop_context
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class DailyShopRelicHotfixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'guild.db'
        self.db = Database(self.path)
        self.data = GameData(ROOT / 'data')
        self.game = CrystalGuildEngine(self.db, self.data, overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'))
        assert self.game.recruit('100', 'hero', 'Hero').ok
        assert self.game.recruit('200', 'other', 'Other').ok

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_daily_provisions_roll_over_at_midnight_utc_even_for_old_24h_cooldown(self):
        before_midnight = 1793490600  # UTC day start and rollover are calculated, not local time
        day_start, tomorrow = self.game._utc_daily_reset(before_midnight)
        self.assertEqual(tomorrow - day_start, 86400)
        self.assertEqual(tomorrow % 86400, 0)
        # Use 23:50 UTC on that date.
        before_midnight = tomorrow - 600
        with patch('crystal_guild.engine.time.time', return_value=before_midnight):
            self.assertTrue(self.game.daily('100').ok)
            self.db.execute("UPDATE transactions SET created_at=datetime(?,'unixepoch') WHERE player_id='100' AND source='daily'", (before_midnight,))
            state = self.game._portal_daily_state_data('100')
            self.assertEqual(state['available_at'], tomorrow)
            self.assertEqual(state['remaining_seconds'], 600)
            self.assertFalse(self.game.daily('100').ok)
            row = self.db.one("SELECT available_at FROM cooldowns WHERE player_id='100' AND action='daily'")
            self.assertEqual(int(row['available_at']), tomorrow)
        # Old rolling cooldowns from yesterday must not block a new UTC day.
        with patch('crystal_guild.engine.time.time', return_value=tomorrow + 15):
            self.db.execute("UPDATE cooldowns SET available_at=? WHERE player_id='100' AND action='daily'", (tomorrow + 60000,))
            self.assertTrue(self.game._portal_daily_state_data('100')['available'])
            self.assertTrue(self.game.portal_claim_daily('100', 'daily:next-day').ok)
            self.db.execute("UPDATE transactions SET created_at=datetime(?,'unixepoch') WHERE player_id='100' AND source='daily' AND created_at>=datetime('now','-1 minute')", (tomorrow+15,))
            self.assertFalse(self.game.daily('100').ok)

    def test_shop_has_all_regular_regional_supplies_without_a_cap(self):
        self.db.execute("UPDATE players SET level=99,current_job='warrior',current_region='omega_ruins' WHERE twitch_id='100'")
        p = self.game._player('100')
        ctx = shop_context(p, self.data.regions)
        expected = {item['id'] for item in eligible_stock(p, self.data.items, ctx) if item['type'] == 'consumable'}
        state = self.game.portal_shop_state('100').data
        stock = state['stock']
        self.assertTrue(expected <= {row['id'] for row in stock})
        self.assertGreater(len(stock), 18)
        self.assertTrue({'turbo_ether','heros_brew','panacea','shadow_gem'} <= expected)
        self.assertFalse({'elixir','megalixir','spooky_supply_cache'} & {row['id'] for row in stock})
        self.assertTrue(all(not self.data.items[row['id']].get('relic_id') for row in stock))
        self.assertLessEqual(sum(row['type'] == 'weapon' for row in stock), 3)
        first = self.game.portal_shop_state('100').data
        self.assertEqual(stock, first['stock'])
        self.assertEqual(state['expires_at'], first['expires_at'])
        self.db.execute("UPDATE player_regional_shops SET stock_json='[\"potion\"]' WHERE player_id='100'")
        self.assertTrue(expected <= {row['id'] for row in self.game.portal_shop_state('100').data['stock']})

    def test_quest_must_be_accepted_by_the_matching_job_and_never_deletes_old_weapons(self):
        self.db.execute("UPDATE players SET level=99,gil=100000,hunt_seals=1000 WHERE twitch_id='100'")
        self.db.execute("INSERT OR REPLACE INTO player_jobs(player_id,job_id,level,jp) VALUES ('100','dragoon',99,0)")
        self.game._change_item('100','gae_bolg_dormant',1,'legacy')
        self.assertFalse(self.game.awaken_relic('100','gae_bolg').ok)
        self.assertFalse(self.game.begin_relic_quest('100','gae_bolg').ok)
        self.db.execute("UPDATE players SET current_job='dragoon' WHERE twitch_id='100'")
        started = self.game.portal_begin_relic_quest('100','gae_bolg','start:gaebolg')
        self.assertTrue(started.ok, started.messages)
        self.assertTrue(self.game.portal_begin_relic_quest('100','gae_bolg','start:gaebolg').ok)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_relic_quests WHERE player_id='100'")['n'], 1)
        self.assertEqual(self.game._inventory_qty('100','gae_bolg_dormant'),1)
        repo = PortalRepository(self.path, ROOT / 'data')
        try:
            record = next(r for r in repo.relics('hero')['relics'] if r['id'] == 'gae_bolg')
            other = next(r for r in repo.relics('other')['relics'] if r['id'] == 'gae_bolg')
            self.assertTrue(record['quest_started'])
            self.assertFalse(other['quest_started'])
        finally:
            repo.close()
        # Legacy partially completed paths must remain valid without rewriting progress.
        self.db.execute("INSERT INTO player_relics(player_id,relic_id,stage) VALUES ('200','gae_bolg',1)")
        self.db.execute("INSERT OR REPLACE INTO player_jobs(player_id,job_id,level,jp) VALUES ('200','dragoon',50,0)")
        self.db.execute("UPDATE players SET current_job='dragoon' WHERE twitch_id='200'")
        repo = PortalRepository(self.path, ROOT / 'data')
        try:
            old = next(r for r in repo.relics('other')['relics'] if r['id'] == 'gae_bolg')
            self.assertTrue(old['quest_started'])
            self.assertEqual(old['stage'], 1)
        finally:
            repo.close()

    def test_quest_start_rejects_ultimate_without_classic_zenith(self):
        self.db.execute("UPDATE players SET level=99,current_job='dragoon' WHERE twitch_id='100'")
        self.db.execute("INSERT OR REPLACE INTO player_jobs(player_id,job_id,level,jp) VALUES ('100','dragoon',99,0)")
        ultimate = next(r for r in self.data.relics.values() if r['job_id']=='dragoon' and r.get('tier')=='ultimate')
        self.assertFalse(self.game.begin_relic_quest('100',ultimate['id']).ok)


if __name__ == '__main__':
    unittest.main()

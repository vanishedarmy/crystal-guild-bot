"""v1.9.97 high-level Hunt/World Event catalog and reward regression."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine, HUNT_DURATION_SECONDS
from crystal_guild.world_events import WORLD_EVENTS
from crystal_guild.seasonal_events import set_event_control

ROOT = Path(__file__).resolve().parents[1]


class EliteProgression197Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'elite.db')
        self.data = GameData(ROOT / 'data')
        self.engine = CrystalGuildEngine(self.db, self.data, rng=random.Random(197), overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'))
        self.assertTrue(self.engine.recruit('197', 'hero197', 'Hero197').ok)
        self.assertTrue(self.engine.choose_job('197', 'warrior').ok)
        with self.db.tx() as conn:
            set_event_control(conn, enabled=False, paused=False, activation_mode='manual')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_catalog_validation_and_hunt_ranks(self):
        self.assertEqual(self.data.validate(), [])
        elite = [row for row in self.data.hunts.values() if row['rank'] in ('S+', 'SS')]
        self.assertEqual(len(elite), 6)
        self.assertEqual(sum(row['rank']=='SS' for row in elite), 3)
        self.assertEqual(HUNT_DURATION_SECONDS['SS'], 6 * 3600)
        self.assertTrue(all(row['monster_id'].startswith('mark_') for row in elite))
        self.assertTrue(all(row['first_clear_title'] in self.data.titles for row in elite))

    def test_hunt_level_and_prior_clear_gates(self):
        hunt = self.data.hunts['the_hollow_sun']
        allowed, missing = self.engine._hunt_available('197', hunt)
        self.assertFalse(allowed)
        self.assertTrue(any('Lv.80' in line for line in missing))
        self.db.execute('UPDATE players SET level=80 WHERE twitch_id=?', ('197',))
        allowed, missing = self.engine._hunt_available('197', hunt)
        self.assertFalse(allowed)
        self.assertTrue(missing)
        for hunt_id in ('tyrant_of_the_rift', 'the_mountain_moves'):
            self.db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('197', ?, 1)", (hunt_id,))
        allowed, missing = self.engine._hunt_available('197', hunt)
        self.assertTrue(allowed, missing)

    def test_elite_hunt_first_clear_and_repeat_drop(self):
        hunt = self.data.hunts['the_hollow_sun']
        monster = self.data.monsters[hunt['monster_id']]
        self.db.execute('UPDATE players SET level=90 WHERE twitch_id=?', ('197',))
        with patch.object(self.engine.rng, 'random', return_value=0.0):
            first = self.engine._award_hunt_victory('197', self.engine._player('197'), hunt, monster)
        self.assertTrue(first['first_clear'])
        self.assertTrue(any('Elite Hunt drop' in item for item in first['loot']))
        self.assertTrue(any('Title:' in item for item in first['first_rewards']))
        with patch.object(self.engine.rng, 'random', return_value=0.0):
            repeat = self.engine._award_hunt_victory('197', self.engine._player('197'), hunt, monster)
        self.assertFalse(repeat['first_clear'])
        self.assertFalse(repeat['first_rewards'])
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_titles WHERE player_id='197' AND title_id=?", (hunt['first_clear_title'],))['n'], 1)
        self.assertEqual(self.db.one("SELECT clears FROM player_hunts WHERE player_id='197' AND hunt_id=?", (hunt['id'],))['clears'], 2)

    def test_world_event_availability_thresholds_and_snapshots(self):
        self.assertEqual(len(WORLD_EVENTS), 13)
        def prefer_elite(rows):
            return next((r for r in rows if r.get('tier') == 'elite'), rows[0])
        with patch.object(self.engine.rng, 'choice', side_effect=prefer_elite):
            low = self.engine.maybe_spawn_world_event(stream_live=True, force=True)
        self.assertTrue(low.ok)
        self.assertNotEqual(self.engine.active_encounter.get('world_event_tier'), 'elite')
        self.engine.active_encounter = None
        self.engine.encounter_roster = {}
        self.db.execute('UPDATE players SET level=99 WHERE twitch_id=?', ('197',))
        with patch.object(self.engine.rng, 'choice', side_effect=prefer_elite):
            high = self.engine.maybe_spawn_world_event(stream_live=True, force=True)
        self.assertTrue(high.ok)
        self.assertEqual(self.engine.active_encounter['world_event_tier'], 'elite')
        self.assertEqual(self.engine.active_encounter['world_event_id'], 'frostveil_tempest')
        public = self.engine._portal_adventure_state_data('197', stream_live=True)
        self.assertEqual(public['encounter']['world_event']['tier'], 'elite')

    def test_elite_world_event_grants_two_guaranteed_rare_items(self):
        player=self.engine._player('197')
        monster=dict(self.data.monsters['frostveil_astrolabe']);monster['drops']=[];monster['pity_drops']=[]
        # Deliberately miss the optional premium drop, confirm two guaranteed items.
        with patch.object(self.engine.rng, 'random', return_value=0.99):
            reward=self.engine._award_victory('197',player,monster,world_event_id='frostveil_tempest')
        self.assertEqual(sum('rare)' in name or 'Elite bonus)' in name for name in reward['loot']),2)
        self.assertGreater(reward['xp'],0)
        self.assertGreater(reward['jp'],0)

if __name__=='__main__':unittest.main()

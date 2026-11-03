from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.dungeons import generate_dungeon_run_rooms
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class DungeonRunVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GameData(ROOT / 'data')

    def test_all_dungeons_have_varied_route_and_enemy_choices(self):
        self.assertEqual(len(self.data.dungeons), 4)
        for dungeon in self.data.dungeons.values():
            runs = [generate_dungeon_run_rooms(dungeon, self.data.monsters, random.Random(seed)) for seed in range(50)]
            patterns = set()
            foe_patterns = set()
            for run in runs:
                self.assertIn(len(run), (9, 10))
                self.assertEqual(run[0]['type'], 'entrance')
                self.assertEqual(run[-1]['type'], 'boss')
                self.assertEqual(run[-1]['monster_id'], dungeon['rooms'][-1]['monster_id'])
                self.assertEqual(sum(row['type'] == 'combat' for row in run), 2)
                self.assertEqual(sum(row['type'] == 'miniboss' for row in run), 1)
                self.assertEqual(len({row['id'] for row in run}), len(run))
                self.assertTrue(any(row['type'] == 'choice' for row in run))
                self.assertTrue(any(row['type'] == 'event' for row in run))
                for room in run:
                    if room.get('monster_id'):
                        self.assertIn(room['monster_id'], self.data.monsters)
                patterns.add(tuple(row['id'] for row in run))
                foe_patterns.add(tuple(row['monster_id'] for row in run if row['type'] in ('combat', 'miniboss')))
            self.assertGreaterEqual(len(patterns), 4, dungeon['id'])
            self.assertGreaterEqual(len(foe_patterns), 8, dungeon['id'])

    def test_advanced_dungeons_vary_but_keep_phase_bosses(self):
        self.assertEqual(len(self.data.ascension_dungeons), 6)
        for dungeon in self.data.ascension_dungeons.values():
            runs = [generate_dungeon_run_rooms(dungeon, self.data.monsters, random.Random(seed)) for seed in range(60)]
            original_boss = dungeon['rooms'][-1]
            patterns = set()
            foes = set()
            for run in runs:
                self.assertIn(len(run), (8, 9))
                self.assertEqual(run[0]['type'], 'entrance')
                self.assertEqual(run[-1]['monster_id'], original_boss['monster_id'])
                self.assertEqual(run[-1]['advanced_combat'], original_boss['advanced_combat'])
                self.assertEqual(sum(room['type'] == 'combat' for room in run), 2)
                self.assertEqual(sum(room['type'] == 'event' for room in run), len(run)-7)
                self.assertEqual(sum(room['type'] == 'boss' for room in run), 1)
                self.assertEqual(sum(room['type'] == 'choice' for room in run), 1)
                self.assertEqual(sum(room['type'] == 'sanctuary' for room in run), 1)
                self.assertEqual(len({row['id'] for row in run}), len(run))
                advanced_wards = [row for row in run if row['type'] == 'combat' and row.get('advanced_combat')]
                ordinary_side = [row for row in run if row['type'] == 'combat' and not row.get('advanced_combat')]
                self.assertEqual(len(advanced_wards), 1)
                self.assertEqual(len(ordinary_side), 1)
                self.assertTrue(advanced_wards[0]['advanced_combat'])
                patterns.add(tuple(row['id'] for row in run))
                foes.add(tuple(row.get('monster_id') for row in run if row['type'] == 'combat'))
            self.assertGreaterEqual(len(patterns), 3, dungeon['id'])
            self.assertGreaterEqual(len(foes), 4, dungeon['id'])

    def test_saved_run_remains_stable_across_reload_and_portal_actions(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / 'guild.db')
            try:
                game = CrystalGuildEngine(db, self.data, rng=random.Random(2201), venture_cooldown_seconds=0,
                                          overlay_state_path=str(Path(folder) / 'overlay.json'))
                self.assertTrue(game.recruit('201', 'ranger201', 'Ranger').ok)
                self.assertTrue(game.choose_job('201', 'warrior').ok)
                db.execute('UPDATE players SET level=99,current_hp=1500 WHERE twitch_id=?', ('201',))
                for region_id in ('emerald_wilds', 'ashen_highlands', 'frostveil_reach', 'astral_scar'):
                    db.execute('INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES (?,?,90,10) ON CONFLICT(player_id,region_id) DO UPDATE SET progress=90', ('201',region_id))
                for i, dungeon in enumerate([*self.data.dungeons.values(), *self.data.ascension_dungeons.values()]):
                    result = game.dungeon_start('201', dungeon['id'])
                    self.assertTrue(result.ok, (dungeon['id'], result.messages))
                    saved = game._dungeon_load('201')
                    planned = saved['run_rooms']
                    self.assertTrue(planned)
                    current = game._dungeon_public('201')
                    self.assertTrue(current['variable_route'])
                    self.assertEqual(current['room_count'], len(planned))
                    self.assertTrue(game._portal_dungeon_state_matches('201', current['run_id'], current['room']['id'], current['revision']))
                    # Continue into the selected first branch using the real API.
                    progressed = game.portal_dungeon_continue('201', current['run_id'], current['room']['id'], current['revision'], f'variant_{i}')
                    self.assertTrue(progressed.ok, progressed.messages)
                    self.assertEqual(game._dungeon_load('201')['run_rooms'], planned)
                    other = CrystalGuildEngine(db, self.data, rng=random.Random(9999), venture_cooldown_seconds=0,
                                               overlay_state_path=str(Path(folder) / 'other.json'))
                    self.assertEqual(other._dungeon_load('201')['run_rooms'], planned)
                    pub = game._dungeon_public('201')
                    self.assertEqual(pub['room']['id'], planned[1]['id'])
                    if pub['status'] == 'decision':
                        choice = pub['choices'][0]
                        chosen = game.portal_dungeon_choice('201', pub['run_id'], pub['room']['id'], pub['revision'], choice['id'], f'choose_{i}')
                        self.assertTrue(chosen.ok, chosen.messages)
                    result = game.dungeon_retreat('201')
                    self.assertTrue(result.ok, result.messages)
                    self.assertIsNone(game._dungeon_load('201'))
                    # Each completed/retreated run now requires 10 minutes of rest.
                    self.assertGreater(game._cooldown_remaining('201', 'dungeon'), 0)
                    # Advance only this test's rest timer to examine the next dungeon.
                    db.execute("UPDATE cooldowns SET available_at=0 WHERE player_id='201' AND action='dungeon'")
            finally:
                db.close()

    def test_legacy_save_and_job_trial_keep_static_rooms(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Database(Path(folder) / 'guild.db')
            try:
                game=CrystalGuildEngine(db, self.data, rng=random.Random(22), venture_cooldown_seconds=0,
                                        overlay_state_path=str(Path(folder) / 'overlay.json'))
                game.recruit('202','legacy202','Legacy')
                game.choose_job('202','warrior')
                db.execute('UPDATE players SET level=99,current_hp=1500 WHERE twitch_id=?', ('202',))
                db.execute('INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES (?,?,90,10)', ('202','emerald_wilds'))
                self.assertTrue(game.dungeon_start('202','forgotten_ossuary').ok)
                state=game._dungeon_load('202')
                state.pop('run_rooms')
                game._dungeon_save('202',state)
                self.assertFalse(game._dungeon_public('202')['variable_route'])
                self.assertEqual(game._dungeon_public('202')['room_count'],len(self.data.dungeons['forgotten_ossuary']['rooms']))
                self.assertEqual(game._dungeon_for_run(state)['rooms'][1]['monster_id'],'skeleton')
            finally: db.close()

if __name__ == '__main__':
    unittest.main()

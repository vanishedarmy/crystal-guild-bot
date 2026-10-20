"""Alpha 12 Camp & Recovery gameplay contract and replay safety."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]

class CampAlpha12Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'guild.db')
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / 'data'), overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'))
        self.assertTrue(self.game.recruit('123', 'van', 'Van').ok)
        self.assertTrue(self.game.choose_job('123', 'warrior').ok)
        self.worker = PortalActionWorker(self.game, 'https://guild.example', 'sync-key')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def worker_action(self, kind, payload, action_id):
        return self.worker._execute({'id': action_id, 'type': kind, 'payload': payload,
                                     'twitch_id': '123', 'username': 'van', 'protocol_version': 39})

    def test_schema_and_craftable_or_purchasable_meal(self):
        self.assertEqual(self.db.schema_version(), 27)
        self.assertEqual(self.game.data.items['trail_rations']['shop'], True)
        recipe = self.game.data.recipes['trail_rations']
        self.assertEqual(recipe['output'], {'item_id': 'trail_rations', 'quantity': 2})
        self.assertEqual({x['item_id'] for x in recipe['materials']}, {'fish_scale', 'potion'})

    def test_zero_inventory_meal_is_rejected_without_partial_receipt(self):
        ok, message, result = self.worker_action('CAMP_EAT_MEAL', {}, 'camp-empty-001')
        self.assertFalse(ok)
        self.assertEqual(self.game._camp_plan_row('123')['meal_until'], 0)
        self.assertEqual(self.game._inventory_qty('123', 'trail_rations'), 0)

    def test_meal_consumes_one_once_and_saves_until_restart(self):
        self.game._change_item('123', 'trail_rations', 2, 'test')
        ok, message, result = self.worker_action('CAMP_EAT_MEAL', {}, 'camp-meal-001')
        self.assertTrue(ok, message)
        until = result['adventure_state']['camp']['preparation']['meal_until']
        self.assertTrue(2650 <= until - int(time.time()) <= 2710)
        ok, message2, result2 = self.worker_action('CAMP_EAT_MEAL', {}, 'camp-meal-001')
        self.assertTrue(ok)
        self.assertEqual(result2['adventure_state']['camp']['preparation']['meal_until'], until)
        self.assertEqual(self.game._inventory_qty('123', 'trail_rations'), 1)
        different = self.worker_action('CAMP_EAT_MEAL', {}, 'camp-meal-002')
        self.assertFalse(different[0])
        self.assertEqual(self.game._inventory_qty('123', 'trail_rations'), 1)
        self.db.close()
        self.db = Database(Path(self.tmp.name) / 'guild.db')
        self.assertEqual(self.db.schema_version(), 27)
        self.assertEqual(self.db.one('SELECT meal_until FROM player_camp_preparations WHERE player_id=?', ('123',))['meal_until'], until)

    def test_preparation_switches_and_rejects_unknown_ids(self):
        ok, message, _ = self.worker_action('CAMP_SET_PREPARATION', {'preparation': 'scout'}, 'camp-prep-001')
        self.assertTrue(ok, message)
        ok, message, _ = self.worker_action('CAMP_SET_PREPARATION', {'preparation': 'supplies'}, 'camp-prep-002')
        self.assertTrue(ok, message)
        self.assertEqual(self.game._camp_plan_row('123')['prep_id'], 'supplies')
        ok, message, _ = self.worker_action('CAMP_SET_PREPARATION', {'preparation': 'exploit'}, 'camp-prep-003')
        self.assertFalse(ok)
        self.assertEqual(self.game._camp_plan_row('123')['prep_id'], 'supplies')

    def test_meal_and_gear_check_stack_only_in_solo_and_are_consumed(self):
        self.game._change_item('123', 'trail_rations', 1, 'test')
        self.assertTrue(self.game.portal_camp_eat_meal('123', 'camp-stack-001').ok)
        self.assertTrue(self.game.portal_camp_choose_preparation('123', 'sharpen', 'camp-stack-002').ok)
        with patch.object(self.game.rng, 'random', return_value=0.99):
            result = self.game.portal_solo_venture('123', 'camp-stack-003')
        self.assertTrue(result.ok, result.messages)
        expedition = self.game._solo_expedition_load('123')
        self.assertTrue(expedition['camp_meal'])
        self.assertEqual(expedition['camp_preparation'], 'sharpen')
        hero = expedition['combat']['roster']['123']
        self.assertAlmostEqual(hero['effects']['damage_mult'], self.game._effects('123', 'warrior').get('damage_mult', 0)+.18)
        self.assertEqual(self.game._camp_plan_row('123'), {'meal_until': 0, 'prep_id': ''})
        self.assertFalse(self.game.portal_camp_choose_preparation('123', 'scout', 'camp-stack-004').ok)
        self.assertFalse(self.game.portal_camp_eat_meal('123', 'camp-stack-005').ok)

    def test_expired_meal_does_not_apply_to_next_run(self):
        self.db.execute('INSERT INTO player_camp_preparations(player_id,meal_until,prep_id) VALUES (?,?,?)',
                        ('123', int(time.time())-2, 'scout'))
        with patch.object(self.game.rng, 'random', return_value=0.99):
            result = self.game.solo_venture('123', bypass_cooldown=True)
        self.assertTrue(result.ok, result.messages)
        expedition = self.game._solo_expedition_load('123')
        self.assertFalse(expedition['camp_meal'])
        self.assertEqual(expedition['camp_preparation'], 'scout')

    def test_scout_increases_secured_stage_xp_and_jp(self):
        with patch.object(self.game.rng, 'random', return_value=0.99):
            result = self.game.solo_venture('123', bypass_cooldown=True)
        self.assertTrue(result.ok, result.messages)
        expedition = self.game._solo_expedition_load('123')
        monster = self.game.data.monsters[expedition['combat']['encounter']['monster_id']]
        with patch.object(self.game.rng, 'uniform', return_value=1):
            plain = self.game._solo_roll_stage_rewards('123', monster, 1)
            expedition['camp_preparation'] = 'scout'
            self.game._solo_expedition_save('123', expedition)
            boosted = self.game._solo_roll_stage_rewards('123', monster, 1)
        self.assertGreater(boosted['xp'], plain['xp'])
        self.assertGreater(boosted['jp'], plain['jp'])

    def test_pack_supplies_recovers_hp_and_job_resources_after_victory(self):
        self.assertTrue(self.game.portal_camp_choose_preparation('123', 'supplies', 'camp-supply-001').ok)
        with patch.object(self.game.rng, 'random', return_value=0.99):
            result = self.game.solo_venture('123', bypass_cooldown=True)
        self.assertTrue(result.ok, result.messages)
        expedition = self.game._solo_expedition_load('123')
        self.assertEqual(expedition['camp_preparation'], 'supplies')
        monster = self.game.data.monsters[expedition['combat']['encounter']['monster_id']]
        hero = expedition['combat']['roster']['123']
        original = {}
        for stat in ('hp', 'mp', 'ap'):
            maximum = int(hero.get(f'max_{stat}', 0))
            if maximum:
                hero[stat] = max(1, maximum // 2)
                original[stat] = hero[stat]
        self.assertTrue(original)
        finished = self.game._finish_solo_stage_victory('123', expedition, monster, hero, 1, [])
        self.assertTrue(finished.ok, finished.messages)
        for stat, before in original.items():
            maximum = int(hero[f'max_{stat}'])
            self.assertEqual(hero[stat], min(maximum, before + max(1, int(maximum * .1))), stat)

    def test_schema_23_upgrade_creates_verified_backup_and_keeps_hero(self):
        from sqlite3 import connect
        path = Path(self.tmp.name) / 'guild.db'
        self.db.close()
        with connect(path) as connection:
            connection.execute('DROP TABLE player_camp_preparations')
            connection.execute('DELETE FROM schema_migrations WHERE version=24')
            connection.execute('DROP TABLE trading_post_watchlist')
            connection.execute('DROP INDEX idx_trading_post_recent_sold')
            connection.execute('DROP INDEX idx_trading_post_sold_by_item')
            connection.execute('DELETE FROM schema_migrations WHERE version>=25')
        self.db = Database(path)
        self.assertEqual(self.db.schema_version(), 27)
        self.assertIsNotNone(self.db.one('SELECT twitch_id FROM players WHERE twitch_id=?', ('123',)))
        backups = sorted((path.parent / 'backups').glob('pre_schema_24_*.db'))
        self.assertTrue(backups, "The schema-24 migration must create a verified backup")
        with connect(backups[-1]) as connection:
            self.assertEqual(connection.execute('SELECT MAX(version) FROM schema_migrations').fetchone()[0], 23)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM players').fetchone()[0], 1)

    def test_meal_is_never_applied_to_other_encounters(self):
        self.game._change_item('123', 'trail_rations', 1, 'test')
        self.assertTrue(self.game.portal_camp_eat_meal('123', 'camp-other-001').ok)
        self.assertTrue(self.game.venture('123', bypass_cooldown=True).ok)
        self.assertEqual(self.game._camp_plan_row('123')['meal_until'] > int(time.time()), True)

    def test_small_board_payload_preserves_existing_size_guardrail(self):
        state = self.game.portal_adventure_state('123').data['adventure_state']
        plan = state['camp']['preparation']
        self.assertEqual(plan['preparation'], '')
        self.assertIn('can_prepare', plan)
        self.assertLess(len(__import__('json').dumps(state, separators=(',', ':'), ensure_ascii=False).encode()), 16 * 1024)

if __name__ == '__main__':
    unittest.main()

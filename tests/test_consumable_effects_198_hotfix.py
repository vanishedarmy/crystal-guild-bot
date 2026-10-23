"""v1.9.8: real item recovery/damage calculations and battle-message contracts."""
from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class ConsumableEffects198Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'items.db')
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / 'data'), rng=random.Random(17),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'),
        )
        self.assertTrue(self.game.recruit('1', 'tester', 'Tester').ok)
        self.assertTrue(self.game.choose_job('1', 'warrior').ok)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    @staticmethod
    def _hero(**overrides):
        row = {
            'name': 'Tester', 'hp': 17, 'max_hp': 177,
            'mp': 3, 'max_mp': 63, 'ap': 2, 'max_ap': 25,
            'healing': 0, 'damage': 0, 'best_hit': 0, 'items_used': 0,
            'statuses': {},
        }
        row.update(overrides)
        return row

    def test_percent_recovery_is_capped_and_small_pools_are_not_rounded_to_zero(self):
        calc = self.game._item_restored_value
        self.assertEqual(calc(1, 1200, {'fraction': 1.0}), 1200)
        self.assertEqual(calc(2, 40, {'fraction': 1.0}), 40)
        self.assertEqual(calc(1, 10, {'fraction': 0.4}), 5)
        self.assertEqual(calc(1, 1, {'fraction': 0.4}), 1)
        self.assertEqual(calc(0, 1, {'fraction': 0.4}), 1)
        self.assertEqual(calc(0, 0, {'fraction': 1.0}), 0)
        self.assertEqual(calc(100, 100, {'amount': 500}), 100)
        self.assertEqual(calc(17, 1000, {'amount': 200}), 217)

    def test_all_fixed_hp_field_restoratives_apply_exact_amount_up_to_cap(self):
        player = self.game._player('1')
        maximum = self.game._max_hp(player)
        for item_id, amount in [('potion', 50), ('hi_potion', 200),
                                ('mega_potion', 500), ('x_potion', 1000)]:
            with self.subTest(item=item_id):
                self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='1'")
                before_qty = self.game._inventory_qty('1', item_id)
                self.game._change_item('1', item_id, 1, 'audit')
                result = self.game.use_item('1', item_id)
                self.assertTrue(result.ok, result.messages)
                self.assertEqual(self.game._player('1')['current_hp'], min(maximum, 1 + amount))
                self.assertEqual(self.game._inventory_qty('1', item_id), before_qty)

    def test_field_mp_and_ap_potions_restore_correct_percentages(self):
        for job_id, resource_key, items in (
            ('blackmage', 'mp', [('ether', 0.40), ('hi_ether', 0.65), ('turbo_ether', 1.0)]),
            ('warrior', 'ap', [('stamina_draught', 0.40), ('warriors_tonic', 0.65), ('heros_brew', 1.0)]),
        ):
            self.assertTrue(self.game.choose_job('1', job_id).ok)
            p = self.game._player('1')
            maximum = self.game._resource_state_for(p)[f'max_{resource_key}']
            self.assertGreater(maximum, 0)
            for item_id, fraction in items:
                with self.subTest(job=job_id, item=item_id):
                    self.db.execute(f"UPDATE players SET current_{resource_key}=0 WHERE twitch_id='1'")
                    self.game._change_item('1', item_id, 1, 'audit')
                    result = self.game.use_item('1', item_id)
                    self.assertTrue(result.ok, result.messages)
                    p = self.game._player('1')
                    restored = self.game._resource_state_for(p)[resource_key]
                    expect = maximum if fraction == 1 else max(1, int(maximum * fraction))
                    self.assertEqual(restored, expect)
                    self.assertEqual(self.game._inventory_qty('1', item_id), 0)

    def test_full_hp_and_mp_does_not_consume_unneeded_megalixir(self):
        actor = self._hero(hp=177, mp=63, ap=25)
        self.game.encounter_roster = {'1': actor}
        self.game.active_encounter = {'state': 'combat', 'round': 1}
        self.game._change_item('1', 'megalixir', 1, 'audit')
        log = []
        self.game._resolve_active_item('1', actor, {'item_id': 'megalixir', 'target_id': 'party'}, log)
        self.assertIn('not consumed', ' '.join(log))
        self.assertEqual(self.game._inventory_qty('1', 'megalixir'), 1)

    def test_megalixir_sets_every_living_battle_target_to_max_with_clear_log(self):
        actor = self._hero()
        mage = self._hero(name='Mage', hp=2, max_hp=501, mp=0, max_mp=222, ap=0, max_ap=0)
        ko = self._hero(name='KO', hp=0, max_hp=199)
        self.game.encounter_roster = {'1': actor, '2': mage, '3': ko}
        self.game.active_encounter = {'state': 'combat', 'round': 1}
        self.game._change_item('1', 'megalixir', 1, 'audit')
        log = []
        self.game._resolve_active_item('1', actor, {'item_id': 'megalixir', 'target_id': 'party'}, log)
        self.assertEqual((actor['hp'], actor['mp'], actor['ap']), (177, 63, 25))
        self.assertEqual((mage['hp'], mage['mp'], mage['ap']), (501, 222, 0))
        self.assertEqual(ko['hp'], 0)
        self.assertIn('FULL HP at item resolution', ' '.join(log))
        self.assertIn('FULL MP', ' '.join(log))
        self.assertIn('FULL AP', ' '.join(log))
        self.assertEqual(self.game._inventory_qty('1', 'megalixir'), 0)

    def test_raid_megalixir_heals_at_resolution_not_post_boss_response(self):
        actor = self._hero()
        mage = self._hero(name='Mage', hp=2, max_hp=501, mp=0, max_mp=222, ap=0, max_ap=0)
        ko = self._hero(name='KO', hp=0)
        self.game.raid_roster = {'1': actor, '2': mage, '3': ko}
        self.game._change_item('1', 'megalixir', 1, 'audit')
        log = []
        dmg, heal = self.game._resolve_raid_item(
            '1', actor, {'item_id': 'megalixir', 'target_id': 'party'}, [], log)
        self.assertEqual(dmg, 0)
        self.assertEqual(heal, (177 - 17) + (501 - 2))
        self.assertEqual((actor['hp'], actor['mp'], actor['ap']), (177, 63, 25))
        self.assertEqual((mage['hp'], mage['mp']), (501, 222))
        self.assertEqual(ko['hp'], 0)
        self.assertIn('FULL HP at item resolution', ' '.join(log))
        self.assertEqual(self.game._inventory_qty('1', 'megalixir'), 0)
        # In the same raid round, later hostile damage can lower that HP again.
        actor['hp'] -= 25
        self.assertEqual(actor['hp'], 152)

    def test_damage_items_deal_catalog_amounts_and_respect_active_weakness(self):
        damages = {
            'bomb_fragment': (220, 'Fire'), 'arctic_wind': (300, 'Ice'),
            'lightning_marble': (300, 'Lightning'), 'water_gem': (450, 'Water'),
            'earth_drum': (450, 'Earth'), 'shadow_gem': (700, 'Dark'),
        }
        actor = self._hero()
        self.game.encounter_roster = {'1': actor}
        for item_id, (base, element) in damages.items():
            for weak in (False, True):
                with self.subTest(item=item_id, weakness=weak):
                    self.game.active_encounter = {
                        'state': 'combat', 'round': 1, 'monster_hp': 5000,
                        'monster_max_hp': 5000,
                        'monster_override': {'weakness': element if weak else 'None'},
                    }
                    self.game._change_item('1', item_id, 1, 'audit')
                    log = []
                    self.game._resolve_active_item('1', actor, {'item_id': item_id, 'target_id': 'monster'}, log)
                    expected = int(base * 1.30) if weak else base
                    self.assertEqual(self.game.active_encounter['monster_hp'], 5000 - expected)
                    self.assertIn(f'deals {expected}', ' '.join(log))
                    self.assertEqual(self.game._inventory_qty('1', item_id), 0)

    def test_damage_items_deal_exact_catalog_damage_in_raids(self):
        damages = {
            'bomb_fragment': 220, 'arctic_wind': 300,
            'lightning_marble': 300, 'water_gem': 450,
            'earth_drum': 450, 'shadow_gem': 700,
        }
        actor = self._hero()
        self.game.raid_roster = {'1': actor}
        for item_id, base in damages.items():
            with self.subTest(item=item_id):
                self.game.active_boss = {'name': 'Test Boss', 'current_hp': 10000, 'max_hp': 10000}
                self.game._change_item('1', item_id, 1, 'audit')
                log = []
                damage, heal = self.game._resolve_raid_item(
                    '1', actor, {'item_id': item_id, 'target_id': 'boss'}, [], log)
                self.assertEqual(damage, base)
                self.assertEqual(heal, 0)
                self.assertEqual(self.game.active_boss['current_hp'], 10000 - base)
                self.assertEqual(self.game._inventory_qty('1', item_id), 0)

    def test_all_full_restore_items_use_100_percent_hp_mp_and_ap_catalog_values(self):
        for item_id in ('tent', 'elixir', 'megalixir'):
            with self.subTest(item=item_id):
                effects = {effect['type']: effect for effect in self.game.data.items[item_id]['use']['effects']}
                for effect_type in ('heal_hp', 'restore_mp', 'restore_ap'):
                    self.assertEqual(effects[effect_type]['fraction'], 1.0)


if __name__ == '__main__':
    unittest.main()

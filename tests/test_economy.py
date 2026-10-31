from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.balance import (
    DAILY_GIL_CAP,
    daily_gil_range,
    hunt_repeat_rewards,
    jp_reward_factor,
    raid_reward_allocations,
    sell_value,
)
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.fellowship import WORKSHOP_EXCHANGES
from crystal_guild.retainer import RETAINER_ASSIGNMENTS

ROOT = Path(__file__).resolve().parents[1]


class EconomyBalanceTests(unittest.TestCase):
    def test_daily_income_scales_gently_and_is_capped(self):
        low1, high1 = daily_gil_range(1)
        low50, high50 = daily_gil_range(50)
        low99, high99 = daily_gil_range(99)
        self.assertLess(high1, 300)
        self.assertLess(low1, low50)
        self.assertLess(low50, low99)
        self.assertLessEqual(high99, DAILY_GIL_CAP)

    def test_job_jp_uses_active_job_not_character_level(self):
        # Swapping from an endgame character to a fresh Job must never inherit
        # the former character-level penalty or the 35% catch-up floor.
        self.assertEqual(jp_reward_factor(99, 1, 1), 1.0)
        self.assertEqual(jp_reward_factor(1, 1, 1), 1.0)
        self.assertEqual(jp_reward_factor(99, 1, 30), 1.5)
        self.assertEqual(jp_reward_factor(1, 1, 30), 1.5)
        self.assertEqual(jp_reward_factor(99, 50, 1), 0.05)
        self.assertEqual(jp_reward_factor(1, 50, 1), 0.05)
        self.assertLessEqual(jp_reward_factor(99, 1, 99), 1.5)

    def test_resale_ratios_preserve_material_value_without_full_refund(self):
        self.assertEqual(sell_value(1000, "material"), 700)
        self.assertEqual(sell_value(1000, "weapon"), 500)
        self.assertEqual(sell_value(1000, "consumable"), 400)

    def test_repeat_hunts_keep_seal_loop_but_reduce_general_rewards(self):
        first = hunt_repeat_rewards(1000, 100, 800, first_clear=True)
        repeat = hunt_repeat_rewards(1000, 100, 800, first_clear=False)
        self.assertEqual(first, (1000, 100, 800))
        self.assertEqual(repeat, (850, 85, 640))

    def test_raid_reward_pool_is_exact_and_headcount_bounded(self):
        for n in (1, 2, 5, 20):
            scores = {str(i): float(i + 1) for i in range(n)}
            rewards = raid_reward_allocations(scores, base_xp=1800, base_gil=6500)
            self.assertEqual(len(rewards), n)
            self.assertEqual(sum(xp for xp, _ in rewards.values()), 2430)
            self.assertEqual(sum(gil for _, gil in rewards.values()), 6500)
            self.assertTrue(all(xp >= 1 and gil >= 1 for xp, gil in rewards.values()))

    def test_equal_support_contribution_receives_equal_raid_reward(self):
        rewards = raid_reward_allocations({"damage": 1000, "healer": 1000}, 1800, 6500)
        self.assertEqual(rewards["damage"], rewards["healer"])

    def test_forge_currency_sink_rises_with_upgrade_tier(self):
        data = GameData(ROOT / "data")
        costs = [int(rule.get("gil", 0)) for rule in data.forge]
        self.assertEqual(costs, sorted(costs))
        self.assertTrue(all(b > a for a, b in zip(costs, costs[1:])))

    def test_direct_shop_to_craft_to_sell_has_no_guaranteed_gil_arbitrage(self):
        data = GameData(ROOT / "data")
        for recipe in data.recipes.values():
            materials = recipe.get("materials", [])
            if not materials or not all(data.items[m["item_id"]].get("shop") for m in materials):
                continue
            acquisition = int(recipe.get("gil", 0)) + sum(
                int(data.items[m["item_id"]].get("price", 0)) * int(m["quantity"])
                for m in materials
            )
            out = recipe["output"]
            item = data.items[out["item_id"]]
            liquidation = sell_value(item.get("price", 0), item["type"]) * int(out.get("quantity", 1))
            self.assertLessEqual(liquidation, acquisition, recipe["id"])


    def test_retainer_routes_do_not_print_gil_by_expected_npc_liquidation(self):
        data = GameData(ROOT / "data")
        for assignment in RETAINER_ASSIGNMENTS:
            pool = list(assignment.get("pool") or [])
            total_weight = sum(int(weight) for _item_id, weight in pool)
            expected_single = sum(
                sell_value(data.items[item_id].get("price", 0), data.items[item_id]["type"]) * int(weight)
                for item_id, weight in pool
            ) / total_weight
            low, high = assignment.get("quantity", (1, 1))
            expected_qty = (int(low) + int(high)) / 2.0
            expected = int(assignment.get("rolls", 1)) * expected_qty * expected_single
            rank = int(assignment.get("rank_required", 1))
            bonus_chance = min(0.10, 0.05 + rank * 0.01)
            expected += bonus_chance * expected_single
            self.assertLess(
                expected,
                int(assignment["cost_gil"]),
                f"{assignment['id']} expected NPC liquidation {expected:.2f} must stay below dispatch cost",
            )

    def test_workshop_material_exchanges_cannot_be_immediately_flipped_to_npc_for_profit(self):
        data = GameData(ROOT / "data")
        for exchange in WORKSHOP_EXCHANGES:
            input_item = data.items[exchange["input_id"]]
            output_item = data.items[exchange["output_id"]]
            input_value = sell_value(input_item.get("price", 0), input_item["type"]) * int(exchange["input_qty"])
            output_value = sell_value(output_item.get("price", 0), output_item["type"]) * int(exchange["output_qty"])
            total_cost = input_value + int(exchange.get("gil", 0))
            self.assertLessEqual(output_value, total_cost, exchange["id"])

    def test_shipping_item_prices_are_nonnegative(self):
        data = GameData(ROOT / "data")
        self.assertTrue(all(int(item.get("price", 0)) >= 0 for item in data.items.values()))


class EconomyRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0, venture_treasure_chance=0.0)
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_engine_sell_uses_gold_saucer_material_ratio(self):
        self.db.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES ('1','iron_ore',1)")
        before = self.game._player("1")["gil"]
        result = self.game.sell("1", "iron ore")
        self.assertTrue(result.ok)
        after = self.game._player("1")["gil"]
        self.assertEqual(after - before, sell_value(self.game.data.items["iron_ore"]["price"], "material"))

    def test_daily_uses_level_scaled_range(self):
        class LowRng:
            @staticmethod
            def randint(low, high):
                return low
        self.game.rng = LowRng()
        before = self.game._player("1")["gil"]
        result = self.game.daily("1")
        self.assertTrue(result.ok)
        low, _ = daily_gil_range(1)
        self.assertEqual(self.game._player("1")["gil"] - before, low)

    def test_economy_snapshot_groups_sources_and_sinks(self):
        self.db.execute("UPDATE players SET gil=gil+1000 WHERE twitch_id='1'")
        self.db.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES ('1','gil','gil',1000,'monster:goblin')")
        self.db.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES ('1','gil','gil',-250,'shop')")
        snap = self.db.economy_snapshot(7)
        self.assertGreaterEqual(snap["circulating_gil"], 1250)
        self.assertGreaterEqual(snap["earned_by_source"]["monster"], 1000)
        self.assertGreaterEqual(snap["spent_by_source"]["shop"], 250)

    def test_owner_economy_report_is_compact_and_readable(self):
        result = self.game.economy_report(7)
        self.assertTrue(result.ok)
        self.assertIn("GOLD SAUCER ECONOMY [7d]", result.messages[0])
        self.assertIn("Top source:", result.messages[1])


if __name__ == "__main__":
    unittest.main()

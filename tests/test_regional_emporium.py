from __future__ import annotations

import json
import random
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild.balance import sell_value
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.emporium import REGIONAL_SHOPS, STAPLES, eligible_stock, shop_context
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class RegionalEmporiumTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(self.db, self.data, rng=random.Random(196),
                                      overlay_state_path=str(Path(self.tmp.name) / "overlay.json"))
        for key, name in (("100", "van"), ("200", "buyer")):
            self.assertTrue(self.game.recruit(key, name, name.title()).ok)
        self.db.execute("UPDATE players SET gil=999999,level=99,current_job='warrior' WHERE twitch_id='100'")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def travel(self, region):
        self.db.execute("UPDATE players SET current_region=? WHERE twitch_id='100'", (region,))

    def give(self, item, qty):
        self.db.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES ('100',?,?) "
                        "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (item, qty))

    def test_every_region_and_job_obeys_local_limits_and_keeps_staples(self):
        for region, (cap, floor, ceiling, *_rest) in REGIONAL_SHOPS.items():
            self.travel(region)
            for job in self.data.jobs:
                with self.subTest(region=region, job=job):
                    self.db.execute("UPDATE players SET current_job=? WHERE twitch_id='100'", (job,))
                    state = self.game.portal_shop_state("100").data
                    stock = state["stock"]
                    self.assertTrue(stock)
                    self.assertLessEqual(len([item for item in stock if item["type"] == "weapon"]), 3 if cap >= 16 else 2)
                    self.assertLessEqual(len([item for item in stock if item["type"] == "armor"]), 3 if cap >= 16 else 2)
                    self.assertEqual({i["id"] for i in stock if i["type"] == "consumable"},
                                     {i["id"] for i in eligible_stock(self.game._player("100"), self.data.items,
                                                                shop_context(self.game._player("100"), self.data.regions))
                                      if i["type"] == "consumable"})
                    self.assertEqual(len(stock), len({item["id"] for item in stock}))
                    self.assertTrue(set(STAPLES) <= {item["id"] for item in stock})
                    for item in stock:
                        source = self.data.items[item["id"]]
                        self.assertLessEqual(max(source.get("shop_level", 1), source.get("min_level", 1)), ceiling)
                        self.assertTrue(not source.get("allowed_jobs") or job in source["allowed_jobs"])
                        if item["type"] in {"weapon", "armor"}:
                            self.assertGreaterEqual(source.get("shop_level", 1), floor)

    def test_location_changes_stock_and_revisit_keeps_rotation(self):
        first = self.game.portal_shop_state("100").data
        self.travel("sable_coast")
        coast = self.game.portal_shop_state("100").data
        self.assertNotEqual({x["id"] for x in first["stock"]}, {x["id"] for x in coast["stock"]})
        coast_weapon = next(x for x in coast["stock"] if x["type"] == "weapon")
        self.travel("greenwind_plains")
        self.assertFalse(self.game.portal_buy("100", coast_weapon["id"], 1, "stale-coast-card").ok)
        revisit = self.game.portal_shop_state("100").data
        self.assertEqual(first["stock"], revisit["stock"])
        self.assertEqual(first["expires_at"], revisit["expires_at"])
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_regional_shops")["n"], 2)

    def test_sparse_starter_shop_is_cached_and_invalid_cache_repairs(self):
        self.db.execute("UPDATE players SET level=1,current_job='adventurer' WHERE twitch_id='100'")
        first = self.game.portal_shop_state("100").data
        self.assertEqual(len(first["stock"]), first["stock_slots"])
        before = dict(self.db.one("SELECT * FROM player_regional_shops WHERE player_id='100'"))
        self.game.portal_shop_state("100")
        self.assertEqual(before, dict(self.db.one("SELECT * FROM player_regional_shops WHERE player_id='100'")))
        self.db.execute("UPDATE player_regional_shops SET stock_json='broken' WHERE player_id='100'")
        repaired = self.game.portal_shop_state("100")
        self.assertTrue(repaired.ok)
        self.assertTrue(set(STAPLES) <= {x["id"] for x in repaired.data["stock"]})

    def test_expiry_and_job_changes_are_independent_of_travel(self):
        original = self.game.portal_shop_state("100").data
        self.db.execute("UPDATE players SET current_job='blackmage' WHERE twitch_id='100'")
        mage = self.game.portal_shop_state("100").data
        self.assertNotEqual(original["stock"], mage["stock"])
        self.db.execute("UPDATE players SET current_job='warrior' WHERE twitch_id='100'")
        self.assertEqual(original["stock"], self.game.portal_shop_state("100").data["stock"])
        self.db.execute("UPDATE player_regional_shops SET expires_at=1 WHERE player_id='100'")
        self.assertGreater(self.game.portal_shop_state("100").data["expires_at"], int(time.time()))
        self.game.reset_all_player_timers()
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_regional_shops")["n"], 0)

    def test_annex_discount_changes_prices_without_reroll_and_is_replay_safe(self):
        first = self.game.portal_shop_state("100").data
        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='emporium_annex'")
        discounted = self.game.portal_shop_state("100").data
        self.assertEqual([x["id"] for x in first["stock"]], [x["id"] for x in discounted["stock"]])
        self.assertEqual(first["expires_at"], discounted["expires_at"])
        potion = next(x for x in discounted["stock"] if x["id"] == "potion")
        self.assertEqual(potion["price"], 45)
        self.assertEqual(potion["base_price"], 50)
        gil = self.game._player("100")["gil"]
        result = self.game.portal_buy("100", "potion", 3, "discount-buy")
        self.assertTrue(result.ok)
        self.assertEqual(result.data["cost"], 135)
        self.game.portal_buy("100", "potion", 3, "discount-buy")
        self.assertEqual(self.game._player("100")["gil"], gil - 135)
        self.assertTrue(self.game.buy("100", "potion", 2).ok)
        self.assertEqual(self.game._player("100")["gil"], gil - 225)
        self.assertIn("45g", " ".join(self.game.shop("100").messages))

    def test_shop_rejects_equipment_bulk_insufficient_gil_and_combat(self):
        state = self.game.portal_shop_state("100").data
        gear = next(x for x in state["stock"] if x["equipment"])
        self.assertFalse(self.game.portal_buy("100", gear["id"], 2, "bulk-gear").ok)
        self.db.execute("UPDATE players SET gil=0 WHERE twitch_id='100'")
        self.assertFalse(self.game.portal_buy("100", "potion", 1, "poor").ok)
        self.game.encounter_roster["100"] = {}
        self.assertFalse(self.game.portal_buy("100", "potion", 1, "combat").ok)

    def test_market_starts_open_caps_six_then_guild_perk_grants_ten(self):
        state = self.game.portal_trading_post_state("100").data
        self.assertTrue(state["unlocked"])
        self.assertEqual(state["active_limit"], 6)
        self.give("iron_ore", 20)
        for i in range(6):
            result = self.game.portal_trading_post_list("100", "iron_ore", 1, 100, f"base-list:{i}")
            self.assertTrue(result.ok, result.messages)
            self.assertEqual(result.data["listing_fee"], 2)
        self.assertFalse(self.game.portal_trading_post_list("100", "iron_ore", 1, 100, "base-limit").ok)
        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='trading_post'")
        for i in range(4):
            result = self.game.portal_trading_post_list("100", "iron_ore", 1, 100, f"perk-list:{i}")
            self.assertTrue(result.ok, result.messages)
            self.assertEqual(result.data["listing_fee"], 1)
        self.assertFalse(self.game.portal_trading_post_list("100", "iron_ore", 1, 100, "perk-limit").ok)
        self.db.execute("UPDATE players SET gil=1000 WHERE twitch_id='200'")
        bought = self.game.portal_trading_post_buy("200", result.data["listing_id"], "market-buy")
        self.assertTrue(bought.ok)
        self.assertEqual(bought.data["sale_tax"], 3)
        self.assertEqual(bought.data["seller_payout"], 97)

    def test_existing_over_limit_listings_can_be_cancelled_and_sold(self):
        self.give("iron_ore", 20)
        now = int(time.time())
        with self.db.tx() as conn:
            for _ in range(12):
                conn.execute("INSERT INTO trading_post_listings(seller_id,item_id,quantity,unit_price,listing_fee,status,created_at,expires_at) VALUES ('100','iron_ore',1,100,2,'active',?,?)", (now, now+3600))
        state = self.game.portal_trading_post_state("100").data
        self.assertEqual(state["active_count"], 12)
        self.assertEqual(len(state["my_listings"]), 12)
        self.assertFalse(self.game.portal_trading_post_list("100", "iron_ore", 1, 100, "grandfather-limit").ok)
        self.assertTrue(self.game.portal_trading_post_cancel("100", state["my_listings"][0]["id"], "grandfather-cancel").ok)
        self.db.execute("UPDATE players SET gil=1000 WHERE twitch_id='200'")
        self.assertTrue(self.game.portal_trading_post_buy("200", state["my_listings"][1]["id"], "grandfather-buy").ok)

    def test_discount_does_not_enable_guaranteed_shop_resale_or_crafting_profit(self):
        for item in self.data.items.values():
            if item.get("shop"):
                self.assertLessEqual(sell_value(item["price"], item["type"]), item["price"] * 90 // 100)
        for recipe in self.data.recipes.values():
            materials = recipe.get("materials", [])
            if not materials or not all(self.data.items[x["item_id"]].get("shop") for x in materials):
                continue
            acquisition = recipe.get("gil", 0) + sum(self.data.items[x["item_id"]]["price"] * 90 // 100 * x["quantity"] for x in materials)
            output = self.data.items[recipe["output"]["item_id"]]
            self.assertLessEqual(sell_value(output["price"], output["type"]) * recipe["output"].get("quantity", 1), acquisition, recipe["id"])

    def test_schema_26_upgrade_preserves_guild_inventory_and_verified_backup(self):
        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id IN ('emporium_annex','trading_post')")
        self.give("iron_ore", 9)
        self.db.execute("DROP TABLE player_regional_shops")
        self.db.execute("DELETE FROM schema_migrations WHERE version=27")
        self.db.close()
        self.db = Database(self.path)
        self.assertEqual(self.db.schema_version(), 27)
        self.assertTrue(self.db.pre_migration_backup_path.exists())
        with sqlite3.connect(self.db.pre_migration_backup_path) as backup:
            self.assertEqual(backup.execute("PRAGMA quick_check").fetchone()[0], "ok")
            self.assertEqual(backup.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0], 26)
        self.assertEqual(self.db.one("SELECT quantity FROM inventory WHERE player_id='100' AND item_id='iron_ore'")["quantity"], 9)
        repo = PortalRepository(self.path, ROOT / "data")
        services = repo.fellowship()["services"]
        self.assertEqual(services["emporium_annex"]["purchase_discount"], .10)
        self.assertEqual(services["trading_post"]["active_limit"], 10)
        self.db.close()
        self.db = Database(self.path)
        self.assertIsNone(self.db.pre_migration_backup_path)


if __name__ == "__main__":
    unittest.main()

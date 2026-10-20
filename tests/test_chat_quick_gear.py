"""Chat-only one-command gear purchase/equip safety tests."""
from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]
SLOTS = {"weapon": "weapon_id", "armor": "armor_id", "accessory": "accessory_id"}


class ChatQuickGearTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "quick-gear.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db, self.data, rng=random.Random(203),
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
        )
        self.assertTrue(self.game.recruit("chat", "viewer", "Viewer").ok)
        self.assertTrue(self.game.choose_job("chat", "warrior").ok)
        self.db.execute(
            "UPDATE players SET level=25,current_region='sable_coast',gil=99999 WHERE twitch_id='chat'"
        )

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def gil(self):
        return int(self.db.one("SELECT gil FROM players WHERE twitch_id='chat'")["gil"])

    def equipped(self, slot):
        return self.db.one(f"SELECT {SLOTS[slot]} AS id FROM equipment WHERE player_id='chat'")["id"]

    def qty(self, item_id):
        row = self.db.one("SELECT quantity FROM inventory WHERE player_id='chat' AND item_id=?", (item_id,))
        return int(row["quantity"]) if row else 0

    def test_purchase_equips_each_slot_and_charges_exactly_once(self):
        for slot in SLOTS:
            with self.subTest(slot=slot):
                before = self.gil()
                result = self.game.quick_buy_gear("chat", slot)
                self.assertTrue(result.ok, result.messages)
                self.assertTrue(result.data["equipped"])
                self.assertTrue(result.data["purchased"])
                self.assertIn("Purchased and equipped", result.messages[0])
                item_id = result.data["item_id"]
                self.assertEqual(self.equipped(slot), item_id)
                self.assertEqual(self.qty(item_id), 1)
                self.assertEqual(self.gil(), before - result.data["cost"])
                self.assertEqual(
                    int(self.db.one("SELECT COUNT(*) AS n FROM transactions WHERE player_id='chat' AND kind='gil' AND source='shop' AND amount=?", (-result.data["cost"],))["n"]),
                    1,
                )
                again = self.game.quick_buy_gear("chat", slot)
                self.assertTrue(again.ok)
                self.assertFalse(again.data["purchased"])
                self.assertEqual(self.gil(), before - result.data["cost"])
                self.assertEqual(self.qty(item_id), 1)

    def test_insufficient_gil_is_explicit_and_unchanged(self):
        self.db.execute("UPDATE players SET gil=0 WHERE twitch_id='chat'")
        for slot in SLOTS:
            with self.subTest(slot=slot):
                result = self.game.quick_buy_gear("chat", slot)
                self.assertFalse(result.ok, result.messages)
                self.assertIn("Not enough Gil", result.messages[0])
                self.assertIn("Need:", result.messages[0])
                self.assertGreater(result.data["shortfall"], 0)
                self.assertIsNone(self.equipped(slot))
                self.assertEqual(self.qty(result.data["item_id"]), 0)
                self.assertEqual(self.gil(), 0)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM transactions WHERE player_id='chat' AND source='shop'")["n"], 0)

    def test_owned_item_is_equipped_free_even_without_gil(self):
        self.db.execute("UPDATE players SET gil=0 WHERE twitch_id='chat'")
        blocked = self.game.quick_buy_gear("chat", "weapon")
        item_id = blocked.data["item_id"]
        self.db.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES ('chat',?,1)", (item_id,))
        result = self.game.quick_buy_gear("chat", "weapon")
        self.assertTrue(result.ok, result.messages)
        self.assertFalse(result.data["purchased"])
        self.assertEqual(self.equipped("weapon"), item_id)
        self.assertEqual(self.qty(item_id), 1)
        self.assertEqual(self.gil(), 0)

    def test_locks_and_missing_class_prevent_charge(self):
        self.game.encounter_roster["chat"] = {}
        result = self.game.quick_buy_gear("chat", "armor")
        self.assertFalse(result.ok)
        self.assertIn("active encounter", result.messages[0])
        self.game.encounter_roster.clear()
        self.db.execute("UPDATE players SET current_job='adventurer' WHERE twitch_id='chat'")
        result = self.game.quick_buy_gear("chat", "weapon")
        self.assertFalse(result.ok)
        self.assertIn("!job", result.messages[0])
        self.assertEqual(self.gil(), 99999)

    def test_no_suitable_accessories_does_not_charge(self):
        self.db.execute("UPDATE players SET level=1,current_region='greenwind_plains' WHERE twitch_id='chat'")
        result = self.game.quick_buy_gear("chat", "accessory")
        self.assertFalse(result.ok)
        self.assertIn("No suitable accessory", result.messages[0])
        self.assertEqual(self.gil(), 99999)

    def test_keeps_stronger_existing_equipment_without_spending(self):
        # A higher-level item must not be replaced by a lower-tier rotating offer.
        self.db.execute("UPDATE players SET current_region='greenwind_plains' WHERE twitch_id='chat'")
        stock = self.game._shop_stock("chat")[0]
        selected = [x for x in stock if x["type"] == "weapon"]
        self.assertTrue(selected)
        best_tier = max(max(int(x.get("shop_level", 1)), int(x.get("min_level", 1))) for x in selected)
        better = next(
            item for item in self.data.items.values()
            if item.get("type") == "weapon" and item.get("shop")
            and "warrior" in (item.get("allowed_jobs") or [])
            and int(item.get("min_level", 1)) <= 25
            and max(int(item.get("shop_level", 1)), int(item.get("min_level", 1))) > best_tier
        )
        self.db.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES ('chat',?,1)", (better["id"],))
        self.db.execute("UPDATE equipment SET weapon_id=? WHERE player_id='chat'", (better["id"],))
        before = self.gil()
        response = self.game.quick_buy_gear("chat", "weapon")
        self.assertTrue(response.ok, response.messages)
        self.assertFalse(response.data["purchased"])
        self.assertEqual(self.gil(), before)
        self.assertEqual(self.equipped("weapon"), better["id"])

    def test_selection_never_bypasses_personal_stock_or_job(self):
        stock_ids = {item["id"] for item in self.game._shop_stock("chat")[0]}
        for slot in SLOTS:
            response = self.game.quick_buy_gear("chat", slot)
            self.assertTrue(response.ok, response.messages)
            item = self.data.items[response.data["item_id"]]
            self.assertIn(item["id"], stock_ids)
            self.assertEqual(item["type"], slot)
            self.assertLessEqual(int(item.get("min_level", 1)), 25)
            self.assertTrue(not item.get("allowed_jobs") or "warrior" in item["allowed_jobs"])

    def test_unknown_slot_returns_friendly_error(self):
        result = self.game.quick_buy_gear("chat", "boots")
        self.assertFalse(result.ok)
        self.assertEqual(self.gil(), 99999)


if __name__ == "__main__":
    unittest.main()

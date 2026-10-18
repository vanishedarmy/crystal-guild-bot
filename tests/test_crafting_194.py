"""1.9.4 Crafting Reforged: catalog, compatibility, replay and equipment safety."""
from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from crystal_guild.crafting_catalog import CATEGORIES, recipe_category
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import PortalActionWorker, ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class CraftingCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GameData(ROOT / "data")

    def test_catalog_counts_and_existing_recipes_preserved(self):
        self.assertEqual(self.data.validate(), [])
        self.assertEqual(len(self.data.recipes), 183)
        counts = Counter(recipe_category(r, self.data.items[r["output"]["item_id"]]) for r in self.data.recipes.values())
        self.assertEqual(dict(counts), {"field": 37, "weapons": 82, "armor": 33, "accessories": 31})
        self.assertEqual(sum(not r.get("introduced_in") for r in self.data.recipes.values()), 26)
        self.assertEqual(sum(r.get("introduced_in") == "1.9.4" for r in self.data.recipes.values()), 157)

    def test_field_item_coverage_and_genuine_material_sources(self):
        consumables = {item["id"] for item in self.data.items.values() if item["type"] == "consumable"}
        crafted = {r["output"]["item_id"] for r in self.data.recipes.values()}
        # Seasonal caches are intentionally openable rewards, not recipes.
        self.assertEqual(consumables - crafted, {"spooky_supply_cache"})
        self.assertGreaterEqual(len(consumables), 33)
        inputs = {m["item_id"] for r in self.data.recipes.values() for m in r.get("materials", [])}
        self.assertEqual(inputs - set(self.data.crafting_sources), set())
        self.assertTrue(all(self.data.crafting_sources[i] for i in inputs))

    def test_equipment_progression_in_all_groups(self):
        for group in ("weapons", "armor", "accessories"):
            rows = [r for r in self.data.recipes.values() if r.get("category") == group]
            self.assertTrue(any(int(r["min_level"]) <= (10 if group == "accessories" else 8) for r in rows), group)
            self.assertTrue(any(int(r["min_level"]) >= 35 for r in rows), group)
        families = {self.data.items[r["output"]["item_id"]].get("gear_family") for r in self.data.recipes.values() if r.get("category") == "weapons"}
        self.assertGreaterEqual(len(families - {None, ""}), 10)


class CraftingTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
        )
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")
        self.db.execute("UPDATE players SET level=50,gil=100000,hunt_seals=500 WHERE twitch_id='100'")
        self.worker = PortalActionWorker(self.game, "https://guild.example", "sync-key")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def action(self, key, kind, payload):
        return {"id": key, "protocol_version": ACTION_PROTOCOL_VERSION, "twitch_id": "100", "username": "van", "type": kind, "payload": payload, "lease_token": "lease"}

    def test_new_and_legacy_state_and_transmission_size(self):
        legacy = self.game._portal_crafting_state_data("100")
        reforged = self.game._portal_crafting_state_data("100", mode="reforged")
        self.assertEqual(legacy["recipe_total"], 26)
        self.assertEqual(reforged["recipe_total"], 183)
        self.assertEqual(len(reforged["recipes"]), 176)
        self.assertTrue(any("source_hints" in m for r in reforged["recipes"] for m in r["materials"]))
        self.assertTrue(all(m.get("type") for r in reforged["recipes"] for m in r["materials"]))
        self.assertLess(len(json.dumps(legacy)), 16000)
        action = self.action("catalog-reforged", "CRAFTING_STATE", {"mode": "reforged"})
        status, _, data = self.worker._execute(action)
        self.assertTrue(status)
        self.assertEqual(data["crafting_state"]["recipe_total"], 183)

    def test_batch_craft_and_idempotent_replay(self):
        recipe = self.game.data.recipes["field_potion_pair"]
        for material in recipe["materials"]:
            self.game._change_item("100", material["item_id"], material["quantity"] * 3, "test")
        before = self.game._inventory_qty("100", "potion")
        result = self.game.portal_craft_recipe("100", recipe["id"], 3, "craft-replay-194")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game._inventory_qty("100", "potion"), before + 6)
        replay = self.game.portal_craft_recipe("100", recipe["id"], 3, "craft-replay-194")
        self.assertEqual(result.messages, replay.messages)
        self.assertEqual(self.game._inventory_qty("100", "potion"), before + 6)
        self.assertFalse(self.game.portal_craft_recipe("100", recipe["id"], 21, "overcap-194").ok)

    def test_missing_ingredients_are_atomic(self):
        before = self.db.one("SELECT gil,crafts FROM players WHERE twitch_id='100'")
        result = self.game.portal_craft_recipe("100", "field_potion_pair", 2, "missing-194")
        self.assertFalse(result.ok)
        after = self.db.one("SELECT gil,crafts FROM players WHERE twitch_id='100'")
        self.assertEqual((before["gil"], before["crafts"]), (after["gil"], after["crafts"]))

    def test_equipped_last_copy_is_protected(self):
        recipe = self.game.data.recipes["flame_tongue"]
        self.game._change_item("100", "mythril_sword", 1, "test")
        for ingredient in recipe["materials"]:
            if ingredient["item_id"] != "mythril_sword":
                self.game._change_item("100", ingredient["item_id"], ingredient["quantity"], "test")
        self.assertTrue(self.game.equip("100", "mythril_sword").ok)
        state = self.game._portal_crafting_state_data("100", mode="reforged")
        display = next(r for r in state["recipes"] if r["id"] == "flame_tongue")
        self.assertFalse(display["craftable"])
        self.assertTrue(any("Unequip" in reason for reason in display["missing_requirements"]))
        denied = self.game.portal_craft_recipe("100", "flame_tongue", 1, "equipped-194")
        self.assertFalse(denied.ok)
        self.assertIn("Unequip", " ".join(denied.messages))
        self.assertEqual(self.game._inventory_qty("100", "mythril_sword"), 1)


if __name__ == "__main__":
    unittest.main()

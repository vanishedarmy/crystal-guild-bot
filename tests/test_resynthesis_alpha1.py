from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class ResynthesisAlpha1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
        )
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")
        self.worker = PortalActionWorker(self.game, "https://guild.example", "sync-key")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def action(self, action_id: str, kind: str, payload: dict) -> dict:
        return {
            "id": action_id,
            "protocol_version": ACTION_PROTOCOL_VERSION,
            "twitch_id": "100",
            "username": "van",
            "type": kind,
            "payload": payload,
            "lease_token": "lease",
        }

    def test_protocol_advances_for_resynthesis(self):
        self.assertEqual(ACTION_PROTOCOL_VERSION, 36)

    def test_crafting_state_exposes_only_weapon_and_armor_resynthesis(self):
        self.game._change_item("100", "hunters_axe", 1, "test")
        self.game._change_item("100", "chain_mail", 1, "test")
        self.game._change_item("100", "magic_ring", 1, "test")
        self.game._change_item("100", "bravura_dormant", 1, "test")
        state = self.game._portal_crafting_state_data("100")
        ids = {entry["item_id"] for entry in state["resynthesis_items"]}
        self.assertIn("hunters_axe", ids)
        self.assertIn("chain_mail", ids)
        self.assertNotIn("magic_ring", ids)
        self.assertNotIn("bravura_dormant", ids)
        axe = next(entry for entry in state["resynthesis_items"] if entry["item_id"] == "hunters_axe")
        self.assertEqual(axe["recovery"], [{"item_id": "iron_ore", "name": "Iron Ore", "quantity": 1, "rarity": "common"}])

    def test_resynthesis_is_replay_safe_and_records_materials(self):
        self.game._change_item("100", "hunters_axe", 1, "test")
        before_iron = self.game._inventory_qty("100", "iron_ore")
        action = self.action("resynth-axe", "RESYNTHESIZE_ITEM", {"item_id": "hunters_axe"})
        first = self.worker._execute(action)
        self.assertTrue(first[0], first[1])
        self.assertEqual(self.game._inventory_qty("100", "hunters_axe"), 0)
        self.assertEqual(self.game._inventory_qty("100", "iron_ore"), before_iron + 1)
        self.assertEqual(first[2]["recovery"][0]["item_id"], "iron_ore")
        self.assertEqual(first[2]["crafting_state"]["resynthesis_count"], 1)

        replay = self.worker._execute(action)
        self.assertTrue(replay[0])
        self.assertEqual(replay[2], first[2])
        self.assertEqual(self.game._inventory_qty("100", "iron_ore"), before_iron + 1)

    def test_last_forged_copy_recovers_bounded_forge_materials_and_clears_upgrade(self):
        self.game._change_item("100", "hunters_axe", 1, "test")
        self.db.execute(
            "INSERT INTO item_upgrades(player_id,item_id,upgrade_level) VALUES ('100','hunters_axe',1) "
            "ON CONFLICT(player_id,item_id) DO UPDATE SET upgrade_level=1"
        )
        before_iron = self.game._inventory_qty("100", "iron_ore")
        result = self.game.resynthesize("100", "Hunter's Axe")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game._inventory_qty("100", "hunters_axe"), 0)
        self.assertEqual(self.game._inventory_qty("100", "iron_ore"), before_iron + 2)
        self.assertEqual(self.game._upgrade_level("100", "hunters_axe"), 0)

    def test_duplicate_forged_copy_does_not_duplicate_forge_refund(self):
        self.game._change_item("100", "hunters_axe", 2, "test")
        self.db.execute(
            "INSERT INTO item_upgrades(player_id,item_id,upgrade_level) VALUES ('100','hunters_axe',3) "
            "ON CONFLICT(player_id,item_id) DO UPDATE SET upgrade_level=3"
        )
        before_iron = self.game._inventory_qty("100", "iron_ore")
        first = self.game.resynthesize("100", "Hunter's Axe")
        self.assertTrue(first.ok)
        self.assertEqual(self.game._inventory_qty("100", "hunters_axe"), 1)
        self.assertEqual(self.game._inventory_qty("100", "iron_ore"), before_iron + 1)
        self.assertEqual(self.game._upgrade_level("100", "hunters_axe"), 3)

    def test_equipped_last_copy_and_protected_gear_are_blocked(self):
        self.game._change_item("100", "hunters_axe", 1, "test")
        self.assertTrue(self.game.equip("100", "hunters_axe").ok)
        blocked = self.game.resynthesize("100", "Hunter's Axe")
        self.assertFalse(blocked.ok)
        self.assertIn("Unequip", " ".join(blocked.messages))
        self.assertEqual(self.game._inventory_qty("100", "hunters_axe"), 1)

        self.game._change_item("100", "bravura_dormant", 1, "test")
        relic = self.game.resynthesize("100", "Bravura — Dormant")
        self.assertFalse(relic.ok)
        self.assertIn("protected", " ".join(relic.messages).lower())

        self.game._change_item("100", "magic_ring", 1, "test")
        accessory = self.game.resynthesize("100", "Magic Ring")
        self.assertFalse(accessory.ok)
        self.assertIn("weapons and armor", " ".join(accessory.messages).lower())

    def test_base_salvage_resale_never_beats_direct_gear_sale(self):
        for item in self.game.data.items.values():
            if self.game._resynthesis_block_reason(item):
                continue
            recovery = self.game._resynthesis_recovery(item, upgrade_level=0, owned=1)
            self.assertTrue(recovery, item["id"])
            gear_sale = int(item.get("price", 0) * 0.50)
            recovered_sale = 0
            for reward in recovery:
                material = self.game.data.items[reward["item_id"]]
                recovered_sale += int(material.get("price", 0) * 0.70) * int(reward["quantity"])
            self.assertLess(recovered_sale, gear_sale, item["id"])


if __name__ == "__main__":
    unittest.main()

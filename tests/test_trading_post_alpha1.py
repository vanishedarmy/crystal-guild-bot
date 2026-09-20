from __future__ import annotations

import random
import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class TradingPostAlpha1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(1901),
        )
        self.assertTrue(self.game.recruit("100", "seller", "Seller").ok)
        self.assertTrue(self.game.recruit("200", "buyer", "Buyer").ok)
        self.db.execute("UPDATE players SET gil=10000 WHERE twitch_id IN ('100','200')")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def unlock(self) -> None:
        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='trading_post'")

    def give(self, player_id: str, item_id: str, quantity: int) -> None:
        self.db.execute(
            "INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) "
            "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=excluded.quantity",
            (player_id, item_id, quantity),
        )

    def qty(self, player_id: str, item_id: str) -> int:
        row = self.db.one("SELECT quantity FROM inventory WHERE player_id=? AND item_id=?", (player_id, item_id))
        return int(row["quantity"] or 0) if row else 0

    def gil(self, player_id: str) -> int:
        return int(self.db.one("SELECT gil FROM players WHERE twitch_id=?", (player_id,))["gil"])

    def test_release_contract_and_schema(self):
        self.assertEqual(__version__, "1.9.0-economy-balance-alpha2")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 19)
        self.assertEqual(self.db.schema_version(), 19)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 36)
        table = self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='trading_post_listings'")
        self.assertIsNotNone(table)

    def test_level_one_project_requirements_and_public_service(self):
        available = {project["id"]: project for project in self.game.fellowship_system.available_projects()}
        self.assertIn("trading_post_t1", available)
        project = available["trading_post_t1"]
        self.assertEqual(int(project["required_level"]), 1)
        targets = {req["key"]: int(req["target"]) for req in project["requirements"]}
        self.assertEqual(targets, {
            "gil": 25_000,
            "item:mythril_ore": 3,
            "activity:venture_complete": 15,
            "fellowship_level": 1,
        })
        public = self.game.fellowship_system.public_snapshot()
        facility = next(item for item in public["facilities"] if item["id"] == "trading_post")
        self.assertEqual(int(facility["level"]), 0)
        self.assertFalse(public["services"]["trading_post"]["unlocked"])

    def test_state_is_locked_until_fellowship_builds_post(self):
        locked = self.game.portal_trading_post_state("100")
        self.assertTrue(locked.ok)
        self.assertFalse(locked.data["unlocked"])
        self.assertEqual(locked.data["listings"], [])
        self.unlock()
        opened = self.game.portal_trading_post_state("100")
        self.assertTrue(opened.ok)
        self.assertTrue(opened.data["unlocked"])
        self.assertEqual(opened.data["active_limit"], 24)
        self.assertEqual(opened.data["listing_seconds"], 48 * 60 * 60)

    def test_listing_and_atomic_purchase_transfer_item_and_net_gil(self):
        self.unlock()
        self.give("100", "iron_ore", 8)
        seller_before = self.gil("100")
        buyer_before = self.gil("200")

        listed = self.game.portal_trading_post_list("100", "iron_ore", 4, 125, "list:1")
        self.assertTrue(listed.ok, listed.messages)
        listing_id = int(listed.data["listing_id"])
        self.assertEqual(int(listed.data["listing_fee"]), 10)  # 2% of 500
        self.assertEqual(self.qty("100", "iron_ore"), 4)
        self.assertEqual(self.gil("100"), seller_before - 10)

        bought = self.game.portal_trading_post_buy("200", listing_id, "buy:1")
        self.assertTrue(bought.ok, bought.messages)
        self.assertEqual(int(bought.data["total_price"]), 500)
        self.assertEqual(int(bought.data["sale_tax"]), 25)
        self.assertEqual(int(bought.data["seller_payout"]), 475)
        self.assertEqual(self.qty("200", "iron_ore"), 4)
        self.assertEqual(self.gil("200"), buyer_before - 500)
        self.assertEqual(self.gil("100"), seller_before - 10 + 475)
        row = self.db.one("SELECT status,buyer_id,payout_gil,tax_gil FROM trading_post_listings WHERE id=?", (listing_id,))
        self.assertEqual(str(row["status"]), "sold")
        self.assertEqual(str(row["buyer_id"]), "200")

        # Replaying the same idempotency key must not charge or transfer twice.
        replay = self.game.portal_trading_post_buy("200", listing_id, "buy:1")
        self.assertTrue(replay.ok)
        self.assertEqual(self.qty("200", "iron_ore"), 4)
        self.assertEqual(self.gil("200"), buyer_before - 500)

    def test_self_purchase_is_rejected(self):
        self.unlock()
        self.give("100", "iron_ore", 2)
        listed = self.game.portal_trading_post_list("100", "iron_ore", 1, 100, "list:self")
        self.assertTrue(listed.ok)
        result = self.game.portal_trading_post_buy("100", int(listed.data["listing_id"]), "buy:self")
        self.assertFalse(result.ok)
        self.assertIn("own", result.messages[0].lower())

    def test_cancel_returns_item_but_listing_fee_is_not_refunded(self):
        self.unlock()
        self.give("100", "mythril_ore", 3)
        before = self.gil("100")
        listed = self.game.portal_trading_post_list("100", "mythril_ore", 2, 500, "list:cancel")
        self.assertTrue(listed.ok)
        fee = int(listed.data["listing_fee"])
        self.assertEqual(self.qty("100", "mythril_ore"), 1)
        cancelled = self.game.portal_trading_post_cancel("100", int(listed.data["listing_id"]), "cancel:1")
        self.assertTrue(cancelled.ok)
        self.assertEqual(self.qty("100", "mythril_ore"), 3)
        self.assertEqual(self.gil("100"), before - fee)

    def test_expired_listing_is_returned_on_next_state_read(self):
        self.unlock()
        self.give("100", "iron_ore", 2)
        listed = self.game.portal_trading_post_list("100", "iron_ore", 2, 100, "list:expire")
        self.assertTrue(listed.ok)
        listing_id = int(listed.data["listing_id"])
        self.db.execute("UPDATE trading_post_listings SET expires_at=? WHERE id=?", (int(time.time()) - 1, listing_id))
        self.assertEqual(self.qty("100", "iron_ore"), 0)
        state = self.game.portal_trading_post_state("100")
        self.assertTrue(state.ok)
        self.assertEqual(self.qty("100", "iron_ore"), 2)
        row = self.db.one("SELECT status FROM trading_post_listings WHERE id=?", (listing_id,))
        self.assertEqual(str(row["status"]), "expired")

    def test_relics_and_equipped_last_copies_cannot_be_listed(self):
        self.unlock()
        self.give("100", "chef_knife", 1)
        relic = self.game.portal_trading_post_list("100", "chef_knife", 1, 100, "list:relic")
        self.assertFalse(relic.ok)

        # Starter weapon is equipped after recruitment; one owned copy must remain protected.
        equip = self.db.one("SELECT weapon_id FROM equipment WHERE player_id='100'")
        self.assertIsNotNone(equip)
        weapon_id = str(equip["weapon_id"] or "")
        if weapon_id:
            self.give("100", weapon_id, 1)
            equipped = self.game.portal_trading_post_list("100", weapon_id, 1, 100, "list:equipped")
            self.assertFalse(equipped.ok)
            self.assertIn("unequipped", equipped.messages[0].lower())


if __name__ == "__main__":
    unittest.main()

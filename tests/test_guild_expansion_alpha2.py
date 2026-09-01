from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.fellowship import WEEKLY_ORDER_SET_REWARD

ROOT = Path(__file__).resolve().parents[1]


class GuildExpansionAlpha2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(41),
        )
        self.game.recruit("1", "van", "Van")
        self.db.execute("UPDATE fellowship_state SET level=6,renown=13000 WHERE singleton_id=1")
        self.game.fellowship_system.ensure_member("1")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_supply_drives_and_guild_objectives_are_unlocked_project_types(self):
        projects = {p["id"]: p for p in self.game.fellowship_system.available_projects()}
        self.assertEqual(projects["moogle_relief_shipment"]["project_type"], "supply_drive")
        self.assertEqual(projects["clear_the_roads"]["project_type"], "guild_objective")
        self.assertEqual(projects["chart_the_frontier"]["requirements"][0]["label"], "Expeditions completed")
        self.assertEqual(self.db.schema_version(), 13)

    def test_supply_drive_completes_once_without_changing_facility_tiers(self):
        before_tiers = self.game.fellowship_system.facility_tiers()
        self.db.execute("UPDATE players SET gil=gil+50000 WHERE twitch_id='1'")
        for item_id, qty in (("potion", 30), ("hi_potion", 15)):
            self.db.execute(
                "INSERT INTO inventory(player_id,item_id,quantity) VALUES ('1',?,?) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=excluded.quantity",
                (item_id, qty),
            )
        ok, _, _ = self.game.fellowship_system.set_active_project("moogle_relief_shipment")
        self.assertTrue(ok)
        self.assertTrue(self.game.fellowship_system.contribute("1", "gil 15000")[0])
        self.assertTrue(self.game.fellowship_system.contribute("1", "25 potion")[0])
        result = self.game.fellowship_system.contribute("1", "10 hi-potion")
        self.assertTrue(result[0])
        self.assertTrue(any("SUPPLY DRIVE COMPLETE" in note for note in result[2]))
        self.assertIsNone(self.game.fellowship_system.project_snapshot())
        self.assertEqual(before_tiers, self.game.fellowship_system.facility_tiers())
        self.assertIsNotNone(self.db.one("SELECT 1 FROM fellowship_events WHERE event_key='community_project_complete:moogle_relief_shipment'"))
        ids = {p["id"] for p in self.game.fellowship_system.available_projects()}
        self.assertNotIn("moogle_relief_shipment", ids)

    def test_gameplay_objectives_advance_automatically(self):
        ok, _, _ = self.game.fellowship_system.set_active_project("clear_the_roads")
        self.assertTrue(ok)
        notes = self.game.fellowship_system.record_activity(
            "1", "hunt_win", amount=30, event_key="alpha2:hunt-objective", renown=0
        )
        self.assertTrue(any("GUILD OBJECTIVE COMPLETE" in note for note in notes))
        self.assertIsNone(self.game.fellowship_system.project_snapshot())

        ok, _, _ = self.game.fellowship_system.set_active_project("chart_the_frontier")
        self.assertTrue(ok)
        notes = self.game.fellowship_system.record_activity(
            "1", "expedition_complete", amount=20, event_key="alpha2:expedition-objective", renown=0
        )
        self.assertTrue(any("GUILD OBJECTIVE COMPLETE" in note for note in notes))

    def test_order_completion_pays_each_participant_once(self):
        snapshot = self.game.fellowship_system.orders_snapshot()
        order = snapshot["orders"][0]
        period = snapshot["period"]
        self.db.execute(
            "UPDATE fellowship_orders SET progress=? WHERE period_key=? AND order_id=?",
            (int(order["target"]) - 1, period, order["id"]),
        )
        self.db.execute(
            "INSERT OR IGNORE INTO fellowship_order_members(period_key,order_id,player_id) VALUES (?,?,?)",
            (period, order["id"], "1"),
        )
        before_gil = int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"])
        before_member = int(self.db.one("SELECT renown FROM fellowship_members WHERE player_id='1'")["renown"])
        self.game.fellowship_system.record_activity(
            "1", order["activity"], event_key="alpha2:order-finish", renown=0
        )
        after_gil = int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"])
        after_member = int(self.db.one("SELECT renown FROM fellowship_members WHERE player_id='1'")["renown"])
        self.assertEqual(after_gil - before_gil, int(order["personal_gil"]))
        self.assertEqual(after_member - before_member, int(order["personal_renown"]))
        reward_events = self.db.all("SELECT event_key FROM fellowship_events WHERE event_key LIKE 'order_participant_reward:%'")
        self.assertEqual(len(reward_events), 1)
        # Re-finalizing cannot pay the same completed Order twice.
        self.game.fellowship_system._finalize_progress("1", 6, None)
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]), after_gil)

    def test_full_week_adds_one_participant_bonus(self):
        snapshot = self.game.fellowship_system.orders_snapshot()
        period = snapshot["period"]
        for order in snapshot["orders"]:
            self.db.execute(
                "UPDATE fellowship_orders SET progress=? WHERE period_key=? AND order_id=?",
                (int(order["target"]) - 1, period, order["id"]),
            )
            self.db.execute(
                "INSERT OR IGNORE INTO fellowship_order_members(period_key,order_id,player_id) VALUES (?,?,?)",
                (period, order["id"], "1"),
            )
            self.game.fellowship_system.record_activity(
                "1", order["activity"], event_key=f"alpha2:weekly:{order['id']}", renown=0
            )
        weekly_tx = self.db.all("SELECT amount FROM transactions WHERE player_id='1' AND source='fellowship_orders_week_reward'")
        self.assertEqual(len(weekly_tx), 1)
        self.assertEqual(int(weekly_tx[0]["amount"]), int(WEEKLY_ORDER_SET_REWARD["personal_gil"]))
        weekly_events = self.db.all("SELECT event_key FROM fellowship_events WHERE event_key LIKE 'weekly_order_participant_reward:%'")
        self.assertEqual(len(weekly_events), 1)
        orders = self.game.fellowship_system.orders_snapshot()
        self.assertEqual(orders["weekly_bonus"]["personal_renown"], 50)


if __name__ == "__main__":
    unittest.main()

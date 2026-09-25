"""Large-market relay and passive failure isolation in the Bot worker."""
import json
import random
import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import PortalActionWorker, ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class TradingPostQueueHotfixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"),
                                       overlay_state_path=str(Path(self.tmp.name) / "overlay.json"), rng=random.Random(13))
        self.assertTrue(self.game.recruit("100", "seller", "Seller").ok)
        self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id='trading_post'")
        now = int(time.time())
        with self.db.tx() as conn:
            conn.executemany(
                "INSERT INTO trading_post_listings(seller_id,item_id,quantity,unit_price,listing_fee,status,created_at,expires_at) "
                "VALUES ('100','iron_ore',1,100,1,'active',?,?)",
                [(now - i, now + 3600) for i in range(200)],
            )

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def actions(self):
        return [{"id": f"read-{kind}", "lease_token": f"lease-{kind}", "type": kind,
                 "payload": {}, "twitch_id": "100", "username": "seller", "protocol_version": ACTION_PROTOCOL_VERSION}
                for kind in ("TRADING_POST_STATE", "SHOP_STATE")]

    def test_large_market_exceeded_old_relay_result_cap(self):
        state = self.game.portal_trading_post_state("100")
        self.assertTrue(state.ok)
        size = len(json.dumps({"ok": True, "message": state.messages[0], "data": state.data},
                              separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode())
        self.assertGreater(size, 64 * 1024)
        self.assertLess(size, 500 * 1024)

    def test_old_relay_size_failure_does_not_starve_shop_actions(self):
        worker = PortalActionWorker(self.game, "https://example.invalid", "test")
        acked = []
        actions = self.actions()

        def fake_post(path, data):
            if path.endswith("/claim"):
                return {"ok": True, "protocol_version": ACTION_PROTOCOL_VERSION, "actions": actions, "long_poll": False}
            encoded = json.dumps({"ok": data["ok"], "message": data["message"], "data": data["data"]},
                                 separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode()
            if data["id"] == "read-TRADING_POST_STATE" and len(encoded) > 64 * 1024:
                raise RuntimeError('HTTP 400: {"error":"Action result is too large."}')
            acked.append(data.copy())
            return {"ok": True}

        worker._post = fake_post
        self.assertEqual(worker.poll_once(), 2)
        self.assertEqual([a["id"] for a in acked], ["read-TRADING_POST_STATE", "read-SHOP_STATE"])
        self.assertFalse(acked[0]["ok"])
        self.assertIn("matching Web hotfix", acked[0]["message"])
        self.assertTrue(acked[1]["ok"])

    def test_trading_post_exception_is_acknowledged_and_shop_still_runs(self):
        worker = PortalActionWorker(self.game, "https://example.invalid", "test")
        actions = self.actions()
        acked = []
        actual_execute = worker._execute

        def fake_execute(action):
            if action["type"] == "TRADING_POST_STATE":
                raise RuntimeError("simulated market-only error")
            return actual_execute(action)

        worker._execute = fake_execute
        worker._post = lambda path, data: (
            {"ok": True, "protocol_version": ACTION_PROTOCOL_VERSION, "actions": actions, "long_poll": False}
            if path.endswith("/claim") else (acked.append(data.copy()) or {"ok": True})
        )
        self.assertEqual(worker.poll_once(), 2)
        self.assertEqual([a["ok"] for a in acked], [False, True])


if __name__ == "__main__":
    unittest.main()

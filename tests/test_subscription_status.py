from __future__ import annotations

import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from crystal_guild.daily_provisions import daily_gil_with_perk, provision_preview, roll_daily_provisions, subscriber_perk
from crystal_guild.data import GameData
from crystal_guild.subscription_status import TwitchSubscriptionStatus
from crystal_guild.token_store import TwitchTokenStore

ROOT = Path(__file__).resolve().parents[1]


class _Probe(TwitchSubscriptionStatus):
    def __init__(self, rows):
        self.temp = tempfile.TemporaryDirectory()
        store = TwitchTokenStore(Path(self.temp.name) / "tokens.db")
        store.upsert("42", "owner-token", "refresh")
        super().__init__("cid", "42", store, cache_seconds=300, stale_seconds=900)
        self.rows = list(rows)
        self.calls = 0

    def _query(self, token: str, user_id: str):
        self.calls += 1
        value = self.rows.pop(0)
        if isinstance(value, BaseException):
            raise value
        return {"data": value}

    def close(self):
        self.temp.cleanup()


class SubscriptionStatusTests(unittest.TestCase):
    def test_twitch_tiers_are_normalized_and_cached(self):
        probe = _Probe([[{"tier": "2000", "is_gift": True}]])
        try:
            first = probe.refresh("100")
            second = probe.refresh("100")
            self.assertEqual(first["state"], "SUBSCRIBED")
            self.assertEqual(first["tier"], 2)
            self.assertTrue(first["is_gift"])
            self.assertEqual(probe.calls, 1)
            self.assertEqual(second["tier"], 2)
        finally:
            probe.close()

    def test_empty_subscription_list_is_not_subscribed(self):
        probe = _Probe([[]])
        try:
            status = probe.refresh("100")
            self.assertEqual(status["state"], "NOT_SUBSCRIBED")
            self.assertFalse(status["subscribed"])
            self.assertEqual(status["tier"], 0)
        finally:
            probe.close()

    def test_missing_scope_fails_soft_without_granting_perk(self):
        error = urllib.error.HTTPError(
            "https://api.twitch.tv/helix/subscriptions", 401, "Unauthorized", {}, io.BytesIO(b"{}")
        )
        probe = _Probe([error])
        try:
            status = probe.refresh("100", force=True)
            self.assertEqual(status["state"], "UNKNOWN")
            self.assertEqual(status["tier"], 0)
            self.assertTrue(status["scope_required"])
        finally:
            probe.close()

    def test_recent_confirmed_tier_survives_short_api_failure(self):
        probe = _Probe([[{"tier": "3000", "is_gift": False}], urllib.error.URLError("temporary")])
        try:
            with patch("crystal_guild.subscription_status.time.time", return_value=1000.0):
                first = probe.refresh("100", force=True)
            self.assertEqual(first["tier"], 3)
            with patch("crystal_guild.subscription_status.time.time", return_value=1100.0):
                second = probe.refresh("100", force=True)
            self.assertEqual(second["tier"], 3)
            self.assertEqual(second["state"], "SUBSCRIBED")
        finally:
            probe.close()


class DailyProvisionPerkTests(unittest.TestCase):
    def setUp(self):
        self.data = GameData(ROOT / "data")

    def test_subscriber_perk_table_is_monotonic(self):
        perks = [subscriber_perk(tier) for tier in range(4)]
        self.assertEqual([p["rolls"] for p in perks], [1, 2, 3, 4])
        self.assertEqual([p["gil_bonus_percent"] for p in perks], [0, 10, 20, 30])

    def test_daily_gil_range_applies_tier_multiplier(self):
        self.assertEqual(daily_gil_with_perk(100, 200, 0), (100, 200))
        self.assertEqual(daily_gil_with_perk(100, 200, 3), (130, 260))

    def test_random_provisions_are_level_appropriate_and_tier_controls_roll_count(self):
        import random
        standard = roll_daily_provisions(self.data.items, 1, random.Random(7), 0)
        tier3 = roll_daily_provisions(self.data.items, 1, random.Random(7), 3)
        self.assertGreaterEqual(sum(int(row["quantity"]) for row in standard), 1)
        self.assertGreaterEqual(sum(int(row["quantity"]) for row in tier3), 4)
        # Lv.1 should not receive higher-level shop consumables.
        for row in standard + tier3:
            item = self.data.items[row["item_id"]]
            if item["type"] == "consumable":
                self.assertLessEqual(int(item.get("shop_level") or 1), 1)
            if item["type"] == "material":
                self.assertIn(item.get("rarity"), {"common", "uncommon"})

    def test_preview_explains_subscriber_bonus(self):
        preview = provision_preview(25, 2)
        self.assertEqual(preview["provision_rolls"], 3)
        self.assertEqual(preview["subscriber_tier"], 2)
        self.assertEqual(preview["subscriber_gil_bonus_percent"], 20)


class SubscriberIntegrationSourceTests(unittest.TestCase):
    def test_cloud_auth_helper_requests_broadcaster_subscription_scope(self):
        auth = (ROOT / "open_twitch_authorization.bat").read_text(encoding="utf-8")
        self.assertIn("channel:read:subscriptions", auth)
        self.assertIn("channel:bot", auth)

    def test_twitch_adapter_exposes_substatus_and_daily_tier_lookup(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        self.assertIn("async def substatus", source)
        self.assertIn("self.bot.subscription_status.refresh", source)
        self.assertIn("self.game.daily(uid, int(status.get(\"tier\") or 0))", source)


if __name__ == "__main__":
    unittest.main()

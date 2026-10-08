import collections
from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker
from crystal_guild.seasonal_events import EDITION_ID, buy_reward, set_event_control
from crystal_guild.supply_cache import SPOOKY_CACHE_ID, SPOOKY_CACHE_TIERS, roll_spooky_cache

ROOT = Path(__file__).resolve().parents[1]


class FixedRoll:
    def __init__(self, roll, gil=100):
        self.roll, self.gil = roll, gil

    def randrange(self, upper):
        assert upper == 100
        return self.roll

    def choice(self, pool):
        return pool[0]

    def randint(self, low, high):
        assert (low, high) == (100, 750)
        return self.gil


class SpookyInventoryCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(self.db, self.data, overlay_state_path=Path(self.tmp.name) / "overlay.json")
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")
        with self.db.tx() as conn:
            set_event_control(conn, enabled=True, paused=False, activation_mode="manual")
            conn.execute("INSERT INTO player_seasonal_event_progress(player_id,edition_id,tokens) VALUES ('100',?,100)", (EDITION_ID,))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def give_cache(self, quantity=1):
        self.game._change_item("100", SPOOKY_CACHE_ID, quantity, "test")

    def test_portal_opens_owned_cache_with_missing_or_legacy_item_metadata(self):
        original = self.data.items[SPOOKY_CACHE_ID]
        for i, definition in enumerate((None, {key: value for key, value in original.items() if key != "use"},
                                        {**original, "use": {"field": False}})):
            with self.subTest(catalog_case=i):
                if definition is None:
                    self.data.items.pop(SPOOKY_CACHE_ID, None)
                else:
                    self.data.items[SPOOKY_CACHE_ID] = definition
                self.give_cache()
                self.game.rng = FixedRoll(85, 750)
                result = self.game.portal_use_field_item("100", SPOOKY_CACHE_ID, f"legacy-cache-{i}")
                self.assertTrue(result.ok, result.messages)
                self.assertEqual(result.data["cache_reward"], {"kind": "gil", "amount": 750})
                self.assertEqual(result.data["seasonal"]["caches"][0]["quantity"], 0)
                self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 0)
        self.data.items[SPOOKY_CACHE_ID] = original

    def test_cache_chat_name_and_action_replay_do_not_depend_on_catalog_metadata(self):
        self.data.items.pop(SPOOKY_CACHE_ID)
        self.give_cache(2)
        self.game.rng = FixedRoll(0)
        direct = self.game.use_item("100", "Spooky Supply Cache")
        self.assertTrue(direct.ok, direct.messages)
        action = {"id": "legacy-replay", "type": "USE_FIELD_ITEM", "payload": {"item_id": SPOOKY_CACHE_ID},
                  "twitch_id": "100", "username": "van", "protocol_version": ACTION_PROTOCOL_VERSION}
        worker = PortalActionWorker(self.game, "https://example.invalid", "test")
        result = worker._execute(action)
        self.assertTrue(result[0], result)
        with patch("crystal_guild.engine.roll_spooky_cache", side_effect=AssertionError("no reroll")):
            replay = worker._execute(action)
        self.assertEqual(result, replay)
        self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 0)

    def test_legacy_cache_keeps_combat_adventure_target_and_ownership_guards(self):
        self.data.items.pop(SPOOKY_CACHE_ID)
        self.give_cache()
        self.assertFalse(self.game.portal_use_field_item("100", SPOOKY_CACHE_ID, "legacy-target", target_query="van").ok)
        with patch.object(self.game, "_dungeon_load", return_value={"run_id": "test"}):
            self.assertFalse(self.game.portal_use_field_item("100", SPOOKY_CACHE_ID, "legacy-away").ok)
        self.game.encounter_roster["100"] = {}
        try:
            self.assertFalse(self.game.portal_use_field_item("100", SPOOKY_CACHE_ID, "legacy-combat").ok)
            self.assertFalse(self.game.use_item("100", SPOOKY_CACHE_ID).ok)
        finally:
            self.game.encounter_roster.pop("100", None)
        self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 1)
        self.assertFalse(self.game.portal_use_field_item("100", "iron_ore", "not-a-cache").ok)
        self.game._change_item("100", SPOOKY_CACHE_ID, -1, "test")
        self.assertFalse(self.game.portal_use_field_item("100", SPOOKY_CACHE_ID, "legacy-empty").ok)

    def test_all_100_buckets_match_published_odds_and_real_item_rarities(self):
        counts = collections.Counter()
        for roll in range(100):
            reward = roll_spooky_cache(FixedRoll(roll))
            counts[reward.get("rarity", reward["kind"])] += 1
        self.assertEqual(dict(counts), {rarity: weight for rarity, weight, _ in SPOOKY_CACHE_TIERS})
        for rarity, _, pool in SPOOKY_CACHE_TIERS:
            for item_id in pool:
                self.assertEqual(self.data.items[item_id]["rarity"], rarity)
        self.assertEqual(self.data.validate(), [])

    def test_purchase_adds_sealed_cache_without_opening_and_replay_is_free(self):
        before = {key: self.game._inventory_qty("100", key) for key in ("potion", "ether", "antidote")}
        first = self.game.portal_seasonal_buy("100", SPOOKY_CACHE_ID, "buy-cache-1")
        second = self.game.portal_seasonal_buy("100", SPOOKY_CACHE_ID, "buy-cache-1")
        self.assertTrue(first.ok)
        self.assertEqual(first.data, second.data)
        self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 1)
        self.assertEqual(self.db.one("SELECT tokens FROM player_seasonal_event_progress WHERE player_id='100'")["tokens"], 90)
        self.assertEqual(before, {key: self.game._inventory_qty("100", key) for key in before})
        with self.db.tx() as conn:
            self.assertTrue(buy_reward(conn, "100", SPOOKY_CACHE_ID)[0])
        self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 2)

    def test_failed_purchase_does_not_add_cache_or_claim(self):
        self.db.execute("UPDATE player_seasonal_event_progress SET tokens=9 WHERE player_id='100'")
        self.assertFalse(self.game.portal_seasonal_buy("100", SPOOKY_CACHE_ID, "poor").ok)
        self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 0)
        self.assertIsNone(self.db.one("SELECT * FROM player_seasonal_reward_claims WHERE player_id='100'"))

    def test_every_item_tier_consumes_one_cache_and_grants_exactly_one_item(self):
        self.give_cache(5)
        for roll in (0, 45, 70, 80, 84):
            self.game.rng = FixedRoll(roll)
            item_id = roll_spooky_cache(self.game.rng)["item_id"]
            before = self.game._inventory_qty("100", item_id)
            result = self.game.use_item("100", SPOOKY_CACHE_ID)
            self.assertTrue(result.ok, result.messages)
            self.assertEqual(self.game._inventory_qty("100", item_id), before + 1)
            self.assertIn(self.data.items[item_id]["name"], result.messages[0])
        self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 0)
        self.assertFalse(self.game.use_item("100", SPOOKY_CACHE_ID).ok)

    def test_gil_bounds_and_no_event_or_health_requirement(self):
        self.give_cache(2)
        self.db.execute("UPDATE players SET current_hp=0 WHERE twitch_id='100'")
        with self.db.tx() as conn:
            set_event_control(conn, enabled=False, paused=False, activation_mode="manual")
        before = self.game._player("100")["gil"]
        for amount in (100, 750):
            self.game.rng = FixedRoll(85, amount)
            result = self.game.use_item("100", "Spooky Supply Cache")
            self.assertTrue(result.ok)
            self.assertEqual(result.data["cache_reward"], {"kind": "gil", "amount": amount})
        self.assertEqual(self.game._player("100")["gil"], before + 850)

    def test_worker_open_replay_survives_restart_without_reroll_or_second_consumption(self):
        self.give_cache(2)
        self.game.rng = FixedRoll(84)
        action = {"id": "open-cache-1", "type": "USE_FIELD_ITEM", "payload": {"item_id": SPOOKY_CACHE_ID}, "twitch_id": "100", "username": "van", "protocol_version": ACTION_PROTOCOL_VERSION}
        first = PortalActionWorker(self.game, "https://example.invalid", "test")._execute(action)
        self.assertTrue(first[0], first)
        self.game = CrystalGuildEngine(self.db, self.data, overlay_state_path=Path(self.tmp.name) / "overlay.json")
        with patch("crystal_guild.engine.roll_spooky_cache", side_effect=AssertionError("must not reroll")):
            second = PortalActionWorker(self.game, "https://example.invalid", "test")._execute(action)
        self.assertEqual(first, second)
        self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 1)
        self.assertEqual(self.game._inventory_qty("100", "megalixir"), 1)

    def test_open_failure_rolls_back_consumption_reward_and_receipt(self):
        self.give_cache()
        with patch("crystal_guild.engine.roll_spooky_cache", side_effect=RuntimeError("grant failed")):
            with self.assertRaises(RuntimeError):
                self.game.portal_use_field_item("100", SPOOKY_CACHE_ID, "broken")
        self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 1)
        self.assertIsNone(self.game._portal_action_replay("broken"))

    def test_two_connections_cannot_open_the_same_last_cache(self):
        self.give_cache()
        other_db = Database(self.path)
        try:
            other_game = CrystalGuildEngine(other_db, self.data, overlay_state_path=Path(self.tmp.name) / "other-overlay.json")
            self.game.rng = other_game.rng = FixedRoll(85, 100)
            before = self.game._player("100")["gil"]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(game.portal_use_field_item, "100", SPOOKY_CACHE_ID, action_id) for game, action_id in ((self.game, "concurrent-a"), (other_game, "concurrent-b"))]
                results = [future.result() for future in futures]
            self.assertEqual(sum(result.ok for result in results), 1)
            self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 0)
            self.assertEqual(self.game._player("100")["gil"], before + 100)
        finally:
            other_db.close()

    def test_target_and_adventure_locks_preserve_cache_and_combat_catalog_excludes_it(self):
        self.give_cache()
        self.assertFalse(self.game.use_item("100", SPOOKY_CACHE_ID, target_query="van", stream_live=True).ok)
        self.assertIsNone(self.game._match_battle_item(SPOOKY_CACHE_ID)[0])
        with patch.object(self.game, "_dungeon_load", return_value={"run_id": "test"}):
            self.assertFalse(self.game.portal_use_field_item("100", SPOOKY_CACHE_ID, "away").ok)
        self.assertEqual(self.game._inventory_qty("100", SPOOKY_CACHE_ID), 1)

    def test_seasonal_tab_counts_update_on_purchase_and_open_with_receipt_replay(self):
        first = self.game.portal_seasonal_buy("100", SPOOKY_CACHE_ID, "seasonal-tab-buy")
        self.assertEqual(first.data["seasonal"]["caches"][0]["quantity"], 1)
        self.game.rng = FixedRoll(85, 750)
        opened = self.game.portal_use_field_item("100", SPOOKY_CACHE_ID, "seasonal-tab-open")
        self.assertTrue(opened.ok)
        self.assertEqual(opened.data["cache_reward"], {"kind": "gil", "amount": 750})
        self.assertEqual(opened.data["seasonal"]["caches"][0]["quantity"], 0)
        with patch("crystal_guild.engine.roll_spooky_cache", side_effect=AssertionError("no reroll")):
            replay = self.game.portal_use_field_item("100", SPOOKY_CACHE_ID, "seasonal-tab-open")
        self.assertEqual(opened.data, replay.data)
        repository = PortalRepository(self.path, ROOT / "data")
        try:
            snapshot = repository.seasonal("van")["seasonal"]
            self.assertEqual(snapshot["state"], "active")
            self.assertEqual(snapshot["caches"][0]["quantity"], 0)
            self.assertEqual(snapshot["tokens"], 90)
        finally:
            repository.close()

    def test_existing_display_and_candle_purchases_are_visible_in_hall_and_seasonal_after_event(self):
        self.assertTrue(self.game.portal_seasonal_buy("100", "hollow_crystal_display", "display").ok)
        self.assertTrue(self.game.portal_seasonal_buy("100", "haunted_candle", "candle").ok)
        # A legacy purchase can exist without a trophy row; project it from its receipt.
        with self.db.tx() as conn:
            conn.execute("DELETE FROM player_seasonal_trophies WHERE player_id='100' AND trophy_id='season_halloween_keeper'")
            set_event_control(conn, enabled=False)
        repository = PortalRepository(self.path, ROOT / "data")
        try:
            hall = repository.trophies("van")
            seasonal = repository.seasonal("van")["seasonal"]
            self.assertEqual({row["id"] for row in hall["keepsakes"]}, {"hollow_crystal_display", "haunted_candle"})
            self.assertEqual(hall["keepsakes"], seasonal["keepsakes"])
            self.assertEqual(len(hall["seasonal_trophies"]), 4)
            self.assertIn("season_halloween_keeper", {row["id"] for row in hall["unlocked"]})
            self.assertEqual(seasonal["state"], "disabled")
            self.assertEqual(self.db.one("SELECT tokens FROM player_seasonal_event_progress WHERE player_id='100'")["tokens"], 0)
            self.assertIsNone(self.db.one("SELECT * FROM player_seasonal_trophies WHERE player_id='100' AND trophy_id='season_halloween_keeper'"))
        finally:
            repository.close()

    def test_inventory_has_open_metadata_and_cache_is_not_recovery_recommendation(self):
        self.give_cache()
        inventory = PortalRepository(self.path, ROOT / "data").inventory("van")
        cache = next(x for x in inventory["items"] if x["id"] == SPOOKY_CACHE_ID)
        self.assertEqual(cache["use"]["effects"], [{"type": "open_cache"}])
        self.assertIn("15%", cache["description"])
        self.assertFalse(cache["sellable"])
        self.assertNotIn(SPOOKY_CACHE_ID, [x["id"] for x in self.game.portal_recovery_state("100").data["recovery_state"]["items"]])


if __name__ == "__main__":
    unittest.main()

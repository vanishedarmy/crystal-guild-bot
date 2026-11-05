from __future__ import annotations
import json
import random
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.database import Database
from crystal_guild.data import GameData
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.encounter_daemon import EncounterDaemon
from crystal_guild.stream_discoveries import MOOGLE_STATE_KEY, EXPLORE_COOLDOWN_SECONDS

ROOT = Path(__file__).resolve().parents[1]
T0 = 2_000_000_000


class StreamExploreMerchantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(self.db, self.data,
                                       overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
                                       rng=random.Random(77))
        for who in ("101", "102"):
            self.assertTrue(self.game.recruit(who, f"hero{who}", f"Hero {who}").ok)
            self.assertTrue(self.game.choose_job(who, "warrior").ok)
            self.db.execute("UPDATE players SET gil=100000, level=45 WHERE twitch_id=?", (who,))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_explore_rejects_offline_and_enforces_persistent_cooldown(self):
        self.assertFalse(self.game.stream_explore("101", stream_live=False, now=T0).ok)
        self.assertIsNone(self.db.one("SELECT available_at FROM cooldowns WHERE player_id='101' AND action='stream_explore'"))
        first = self.game.stream_explore("101", stream_live=True, now=T0)
        self.assertTrue(first.ok, first.messages)
        self.assertFalse(self.game.stream_explore("101", stream_live=True, now=T0+1).ok)
        self.assertTrue(self.game.stream_explore("101", stream_live=True, now=T0+EXPLORE_COOLDOWN_SECONDS).ok)
        same_database = CrystalGuildEngine(self.db, self.data, overlay_state_path=str(Path(self.tmp.name)/"overlay2.json"), rng=random.Random(10))
        self.assertFalse(same_database.stream_explore("101", stream_live=True, now=T0+EXPLORE_COOLDOWN_SECONDS+1).ok)

    def test_explore_wisdom_gives_xp_jp_and_is_not_repeatable(self):
        xp_before = int(self.db.one("SELECT xp FROM players WHERE twitch_id='101'")["xp"])
        jp_before = int(self.db.one("SELECT jp FROM player_jobs WHERE player_id='101' AND job_id='warrior'")["jp"])
        with patch.object(self.game.rng, "random", return_value=.70):
            result = self.game.stream_explore("101", stream_live=True, now=T0)
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(result.data["outcome"], "knowledge")
        self.assertGreater(result.data["xp"], 0)
        self.assertGreater(result.data["jp"], 0)
        self.assertEqual(int(self.db.one("SELECT xp FROM players WHERE twitch_id='101'")["xp"]), xp_before + result.data["xp"])
        job = self.db.one("SELECT level,jp FROM player_jobs WHERE player_id='101' AND job_id='warrior'")
        self.assertTrue(int(job["level"]) > 1 or int(job["jp"]) == jp_before + result.data["jp"])
        self.assertFalse(self.game.stream_explore("101", stream_live=True, now=T0).ok)

    def test_explore_item_reward_and_mishap_cannot_go_negative(self):
        with patch.object(self.game.rng, "random", return_value=.48):
            result = self.game.stream_explore("101", stream_live=True, now=T0)
        self.assertTrue(result.ok)
        self.assertEqual(result.data["outcome"], "supplies")
        row = self.db.one("SELECT quantity FROM inventory WHERE player_id='101' AND item_id=?", (result.data["item_id"],))
        self.assertGreaterEqual(int(row["quantity"]), int(result.data["quantity"]))
        self.db.execute("UPDATE players SET gil=2 WHERE twitch_id='102'")
        with patch.object(self.game.rng, "random", return_value=.89):
            result = self.game.stream_explore("102", stream_live=True, now=T0)
        self.assertTrue(result.ok)
        self.assertEqual(result.data["outcome"], "misfortune")
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='102'")["gil"]), 0)

    def test_explore_rejects_busy_player_without_cooldown(self):
        self.game.active_hunts["101"] = {"id": 1, "resolves_at": T0+999}
        denied = self.game.stream_explore("101", stream_live=True, now=T0)
        self.assertFalse(denied.ok)
        self.assertFalse(self.db.one("SELECT 1 FROM cooldowns WHERE player_id='101' AND action='stream_explore'"))

    def test_every_exploration_outcome_executes_without_stuck_state(self):
        rolls = [.05, .22, .46, .60, .72, .88, .93, .965, .99]
        expected = ["quiet", "gil", "supplies", "materials", "knowledge", "misfortune", "wound", "healing", "rare"]
        for index, (roll, kind) in enumerate(zip(rolls, expected)):
            now = T0 + index * EXPLORE_COOLDOWN_SECONDS
            with patch.object(self.game.rng, "random", return_value=roll):
                result = self.game.stream_explore("101", stream_live=True, now=now)
            self.assertTrue(result.ok, (kind, result.messages))
            self.assertEqual(result.data["outcome"], kind)
        self.assertGreaterEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='101'")["gil"]), 0)
        self.assertGreaterEqual(int(self.db.one("SELECT current_hp FROM players WHERE twitch_id='101'")["current_hp"]), 1)

    def test_twitch_command_and_help_registration(self):
        root = ROOT / "crystal_guild"
        commands = (root / "twitch_bot.py").read_text()
        self.assertIn('async def explore(self, ctx: commands.Context)', commands)
        self.assertIn('async def moogle(self, ctx: commands.Context', commands)
        self.assertIn('self._require_stream_live(ctx, "Wilderness exploration")', commands)
        self.assertIn('self._require_stream_live(ctx, "Traveling Moogle Merchant")', commands)
        from crystal_guild.help_system import help_messages
        self.assertIn("!explore", " ".join(help_messages("explore")))
        self.assertIn("!moogle", " ".join(help_messages("merchant")))

    def test_merchant_spawn_stock_persist_and_offline_close(self):
        self.assertFalse(self.game.maybe_spawn_traveling_moogle(stream_live=False, now=T0, force=True).data.get("merchant_spawned"))
        spawned = self.game.maybe_spawn_traveling_moogle(stream_live=True, now=T0, force=True)
        self.assertTrue(spawned.ok)
        self.assertTrue(spawned.data["merchant_spawned"])
        self.assertEqual(len(spawned.data["stock"]), 5)
        for offer in spawned.data["stock"]:
            item = self.data.items[offer["id"]]
            self.assertIn(item["type"], ("consumable", "material"))
            self.assertGreater(offer["price"], 0)
            self.assertGreater(offer["remaining"], 0)
            self.assertNotIn(item["type"], ("weapon", "armor", "accessory"))
        reloaded = CrystalGuildEngine(self.db, self.data, overlay_state_path=str(Path(self.tmp.name)/"overlay3.json"), rng=random.Random(9))
        self.assertEqual(reloaded.traveling_moogle_status(stream_live=True, now=T0).data["stock"], spawned.data["stock"])
        self.assertFalse(self.game.maybe_spawn_traveling_moogle(stream_live=False, now=T0+1).data.get("merchant_spawned"))
        self.assertFalse(self.game.traveling_moogle_buy("101", "1", stream_live=True, now=T0+2).ok)

    def test_stock_depletes_atomically_and_no_duplicate_purchase(self):
        spawned = self.game.maybe_spawn_traveling_moogle(stream_live=True, now=T0, force=True)
        self.assertTrue(spawned.data["merchant_spawned"])
        offer = spawned.data["stock"][3]
        slot, item_id, qty = offer["slot"], offer["id"], offer["remaining"]
        self.assertEqual(qty, 1)
        before_gil = int(self.db.one("SELECT gil FROM players WHERE twitch_id='101'")["gil"])
        bought = self.game.traveling_moogle_buy("101", str(slot), stream_live=True, now=T0)
        self.assertTrue(bought.ok, bought.messages)
        self.assertEqual(bought.data["remaining"], 0)
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='101'")["gil"]), before_gil-offer["price"])
        self.assertFalse(self.game.traveling_moogle_buy("102", str(slot), stream_live=True, now=T0).ok)
        self.assertFalse(self.game.traveling_moogle_buy("101", str(slot), stream_live=False, now=T0).ok)
        self.assertEqual(int(self.db.one("SELECT quantity FROM inventory WHERE player_id='101' AND item_id=?", (item_id,))["quantity"]), 1)
        self.assertEqual(int(self.db.one("SELECT COUNT(*) AS n FROM transactions WHERE player_id='101' AND source='traveling_moogle'")["n"]), 2)

    def test_competing_players_buy_last_item_using_independent_connections(self):
        offer = self.game.maybe_spawn_traveling_moogle(stream_live=True, now=T0, force=True).data["stock"][4]
        self.assertEqual(offer["remaining"], 1)
        second_db = Database(Path(self.tmp.name) / "guild.db")
        other = CrystalGuildEngine(second_db, self.data,
                                   overlay_state_path=str(Path(self.tmp.name) / "overlay-race.json"),
                                   rng=random.Random(91))
        barrier = threading.Barrier(2)
        results = []
        def buy(g, pid):
            barrier.wait(timeout=3)
            results.append(g.traveling_moogle_buy(pid, str(offer["slot"]), stream_live=True, now=T0))
        a = threading.Thread(target=buy, args=(self.game, "101"))
        b = threading.Thread(target=buy, args=(other, "102"))
        try:
            a.start(); b.start(); a.join(timeout=7); b.join(timeout=7)
            self.assertFalse(a.is_alive() or b.is_alive())
            self.assertEqual(sum(1 for r in results if r.ok), 1, [r.messages for r in results])
            qty_row = self.db.one("SELECT COALESCE(SUM(quantity),0) AS q FROM inventory WHERE item_id=? AND player_id IN ('101','102')", (offer["id"],))
            self.assertEqual(int(qty_row["q"]), 1)
            row = self.db.one("SELECT SUM(amount) AS total FROM transactions WHERE source='traveling_moogle' AND kind='gil'")
            self.assertEqual(int(row["total"]), -int(offer["price"]))
        finally:
            second_db.close()

    def test_merchant_visit_does_not_overwrite_live_encounter(self):
        before = self.game.active_encounter = {"id": 900, "state": "rally", "closes_at": T0+60}
        result = self.game.maybe_spawn_traveling_moogle(stream_live=True, now=T0, force=True)
        self.assertTrue(result.data["merchant_spawned"])
        self.assertEqual(self.game.active_encounter, before)

    def test_merchant_expiry_and_restart_never_extend_visit(self):
        spawned = self.game.maybe_spawn_traveling_moogle(stream_live=True, now=T0, force=True)
        self.assertTrue(spawned.ok)
        self.assertFalse(self.game.traveling_moogle_buy("101", "1", stream_live=True, now=T0+12*60).ok)
        departed = self.game.maybe_spawn_traveling_moogle(stream_live=True, now=T0+12*60)
        self.assertTrue(departed.data.get("merchant_departed"))
        self.assertFalse(self.game.maybe_spawn_traveling_moogle(stream_live=True, now=T0+12*60+1).data["merchant_spawned"])

    def test_no_merchant_schedule_while_offline_and_daemon_is_independent(self):
        sent = []
        daemon = EncounterDaemon(self.game, sent.append, stream_live_lookup=lambda: True)
        self.assertFalse(daemon._tick_traveling_moogle(float(T0)))  # initial grace
        self.assertFalse(self.game.traveling_moogle_status(stream_live=True, now=T0).data.get("stock"))
        self.assertTrue(self.db.runtime_state(MOOGLE_STATE_KEY))
        self.assertEqual(sent, [])
        self.assertFalse(daemon._tick_traveling_moogle(float(T0)+1)) # throttle


if __name__ == "__main__":
    unittest.main()

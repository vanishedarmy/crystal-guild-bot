"""Standalone Card Hall Triple Triad invariants and legacy save behavior."""
from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import gold_saucer_record_value
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class CardHallStandaloneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "guild.db"
        self.db = Database(self.db_path)
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(500),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_card_hall_does_not_initialize_or_reward_saucer(self):
        # Recruitment may initialize other systems, but Triad never modifies
        # Saucer points or creates an account on its own.
        before = self.db.one("SELECT points,lifetime_earned,lifetime_spent FROM player_gold_saucer WHERE player_id='100'")
        state = self.game.portal_triad_state("100")
        self.assertTrue(state.ok)
        self.assertNotIn("gold_saucer_state", state.data)
        self.assertTrue(state.data["triple_triad_state"]["unlimited_matches"])
        start = self.game.portal_triad_start("100", "saucer_attendant", "start:1")
        self.assertTrue(start.ok, start.messages)
        state = start.data["triple_triad_state"]
        for i in range(5):
            match = state["match"]
            card_id = match["player_hand"][0]["id"]
            cell = next(n for n, cell in enumerate(match["board"]) if cell is None)
            action = self.game.portal_triad_play("100", card_id, cell, f"move:{i}")
            self.assertTrue(action.ok, action.messages)
            state = action.data["triple_triad_state"]
        self.assertFalse(state["active"])
        after = self.db.one("SELECT points,lifetime_earned,lifetime_spent FROM player_gold_saucer WHERE player_id='100'")
        self.assertEqual(tuple(before) if before else None, tuple(after) if after else None)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE game='triple_triad' AND (wager != 0 OR payout != 0)")["n"], 0)
        self.assertTrue(self.game.portal_triad_start("100", "saucer_attendant", "start:2").ok)

    def test_gold_saucer_state_excludes_triad_but_keeps_progress(self):
        triad = self.game.portal_triad_state("100").data["triple_triad_state"]
        self.assertEqual(triad["owned_count"], 10)
        self.assertNotIn("card_shark", {p["id"] for p in self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["prizes"]})
        gold = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        self.assertNotIn("triple_triad", gold)
        self.assertNotIn("triple_triad", {entry["id"] for entry in gold["attractions"]})
        self.assertNotIn("triple_triad", {entry["game"] for entry in gold["history"]})
        self.assertNotIn("triad_circuit", {entry["game"] for entry in gold["history"]})
        self.assertEqual(gold_saucer_record_value(self.db.conn, "100", "triple_triad_best_streak"), 0)

    def test_legacy_streak_unlock_and_snapshot(self):
        self.game.portal_triad_state("100")
        self.db.execute("UPDATE player_triple_triad SET wins=4,best_streak=4 WHERE player_id='100'")
        response = self.game.portal_triad_state("100")
        self.assertTrue(response.ok)
        self.assertTrue(self.db.one("SELECT 1 FROM achievements WHERE player_id='100' AND achievement_id='triad_heart_of_cards'"))
        self.assertTrue(self.db.one("SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='triad_tactician'"))
        repo = PortalRepository(self.db_path, ROOT / "data")
        try:
            rows = {row["id"]: row for row in repo.achievements("van")["achievements"]}
            self.assertEqual(rows["triad_heart_of_cards"]["progress"]["raw_value"], 4)
            self.assertEqual(rows["triad_heart_of_cards"]["category"], "Card Hall")
        finally:
            repo.close()

    def test_old_paid_rows_do_not_count_as_saucer_attractions(self):
        self.game.portal_gold_saucer_state("100")
        self.db.execute("INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) VALUES ('100','triple_triad',30,120,'win','{}',1000)")
        self.assertEqual(gold_saucer_record_value(self.db.conn, "100", "unique_games"), 0)
        self.assertEqual(gold_saucer_record_value(self.db.conn, "100", "games_played"), 0)
        self.assertTrue(self.game.portal_triad_state("100").ok)


if __name__ == "__main__":
    unittest.main()

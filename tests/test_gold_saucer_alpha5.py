"""Historical Alpha-5 Triple Triad invariants under the v1.9.7 standalone Card Hall.

The card game moved out of Gold Saucer: these assertions protect deck ownership,
match replay, persistence, lock gates, score, and admin-reset isolation without
reintroducing the obsolete entry price or daily cap.
"""
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
from crystal_guild.gold_saucer import (
    TRIPLE_TRIAD_OPPONENTS_BY_ID,
    TRIPLE_TRIAD_STARTER_DECK,
    triple_triad_place,
)
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class GoldSaucerAlpha5TripleTriadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1605),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def state(self):
        result = self.game.portal_triad_state("100")
        self.assertTrue(result.ok, result.messages)
        return result.data["triple_triad_state"]

    def test_v197_contract_keeps_triad_in_standalone_card_hall(self):
        self.assertEqual(__version__, "1.9.7-queens-blood")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 27)
        self.assertEqual(self.db.schema_version(), DATABASE_SCHEMA_VERSION)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 39)
        state = self.state()
        gold = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        self.assertNotIn("triple_triad", gold)
        self.assertNotIn("triple_triad", {a["id"] for a in gold["attractions"]})
        self.assertEqual(state["deck"], list(TRIPLE_TRIAD_STARTER_DECK))
        self.assertEqual(state["owned_count"], 10)
        self.assertTrue(state["unlimited_matches"])
        self.assertFalse(state["active"])

    def test_basic_capture_rule_flips_adjacent_lower_side(self):
        board = [None] * 9
        triple_triad_place(board, 4, "flan", "npc")
        captured = triple_triad_place(board, 3, "chocobo", "player")
        self.assertEqual(captured, [4])
        self.assertEqual(board[4]["owner"], "player")

    def test_deck_validation_requires_owned_unique_five_cards(self):
        bad = self.game.portal_triad_set_deck("100", ["chocobo"] * 5, "triad-deck-bad")
        self.assertFalse(bad.ok)
        missing = self.game.portal_triad_set_deck("100", ["chocobo", "moogle", "cactuar", "bomb", "bahamut"], "triad-deck-missing")
        self.assertFalse(missing.ok)
        good = self.game.portal_triad_set_deck("100", list(reversed(TRIPLE_TRIAD_STARTER_DECK)), "triad-deck-good")
        self.assertTrue(good.ok)
        self.assertEqual(good.data["triple_triad_state"]["deck"], list(reversed(TRIPLE_TRIAD_STARTER_DECK)))

    def test_match_persists_progress_resolves_and_replay_is_exactly_once(self):
        gold_before = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["mgp"]
        started = self.game.portal_triad_start("100", "saucer_attendant", "triad-start-1")
        self.assertTrue(started.ok)
        self.assertEqual(self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["mgp"], gold_before)
        self.assertTrue(started.data["triple_triad_state"]["active"])
        first_card = started.data["triple_triad_state"]["match"]["player_hand"][0]["id"]
        first = self.game.portal_triad_play("100", first_card, 0, "triad-play-1")
        self.assertTrue(first.ok)
        replay = self.game.portal_triad_play("100", first_card, 0, "triad-play-1")
        self.assertEqual(replay.data.get("triple_triad_move"), first.data.get("triple_triad_move"))
        self.assertEqual(replay.data, first.data)

        result = first
        action_no = 2
        while result.data["triple_triad_state"]["active"]:
            match = result.data["triple_triad_state"]["match"]
            card = match["player_hand"][0]["id"]
            cell = next(index for index, row in enumerate(match["board"]) if row is None)
            result = self.game.portal_triad_play("100", card, cell, f"triad-play-{action_no}")
            self.assertTrue(result.ok, result.messages)
            action_no += 1
        triad = result.data["triple_triad_state"]
        self.assertFalse(triad["active"])
        self.assertEqual(triad["records"]["matches"], 1)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='triple_triad'")["n"], 1)
        self.assertEqual(self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["mgp"], gold_before)

    def test_unlimited_matches_and_opponent_unlock_gate(self):
        locked = self.game.portal_triad_start("100", "card_shark", "triad-locked")
        self.assertFalse(locked.ok)
        self.assertIn("previous Triple Triad circuit", " ".join(locked.messages))
        now = int(time.time())
        for index in range(20):
            self.db.execute(
                "INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) VALUES (?,'triple_triad',0,0,'loss','{}',?)",
                ("100", now + index),
            )
        started = self.game.portal_triad_start("100", "saucer_attendant", "triad-unlimited")
        self.assertTrue(started.ok, started.messages)
        self.assertTrue(started.data["triple_triad_state"]["unlimited_matches"])
        self.assertFalse(self.game.portal_triad_start("100", "saucer_attendant", "triad-already-active").ok)

    def test_match_score_includes_cards_in_hand_and_stays_on_ten_point_scale(self):
        started = self.game.portal_triad_start("100", "saucer_attendant", "triad-score-start")
        self.assertTrue(started.ok)
        match = started.data["triple_triad_state"]["match"]
        self.assertEqual((match["player_score"], match["npc_score"]), (5, 5))
        card = match["player_hand"][0]["id"]
        played = self.game.portal_triad_play("100", card, 0, "triad-score-play")
        self.assertTrue(played.ok)
        match = played.data["triple_triad_state"]["match"]
        self.assertEqual(match["player_score"] + match["npc_score"], 10)

    def test_saucer_reset_does_not_interrupt_independent_card_hall(self):
        deck = list(reversed(self.state()["deck"]))
        self.assertTrue(self.game.portal_triad_set_deck("100", deck, "triad-reset-deck").ok)
        self.assertTrue(self.game.portal_triad_start("100", "saucer_attendant", "triad-reset-start").ok)
        before = self.state()
        self.assertTrue(before["active"])
        reset = self.game.streamer_saucer_reset("van", action_id="triad-admin-reset")
        self.assertTrue(reset.ok)
        after = self.state()
        self.assertTrue(after["active"])
        self.assertEqual(after["match"]["id"], before["match"]["id"])
        self.assertEqual(after["deck"], deck)
        self.assertEqual(after["owned_count"], before["owned_count"])
        self.assertEqual(after["records"], before["records"])

    def test_worker_validates_triad_actions(self):
        worker = PortalActionWorker(self.game, "", "")
        base = {"protocol_version": ACTION_PROTOCOL_VERSION, "twitch_id": "100", "username": "van", "lease_token": "lease"}
        ok, _message, data = worker._execute({**base, "id": "triad-worker-start", "type": "TRIAD_START", "payload": {"opponent": "saucer_attendant"}})
        self.assertTrue(ok)
        self.assertTrue(data["triple_triad_state"]["active"])
        ok, message, _data = worker._execute({**base, "id": "triad-worker-bad", "type": "TRIAD_PLAY", "payload": {"card": "chocobo", "cell": 99}})
        self.assertFalse(ok)
        self.assertIn("cell", message.lower())


if __name__ == "__main__":
    unittest.main()

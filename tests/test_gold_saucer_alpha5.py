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
    TRIPLE_TRIAD_DAILY_MATCHES,
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
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1605),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def state(self):
        return self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]

    def test_alpha5_contract_opens_triple_triad_with_schema_13_protocol_29(self):
        self.assertEqual(__version__, "1.9.0-seasonal-events-alpha8")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 21)
        self.assertEqual(self.db.schema_version(), 21)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 37)
        state = self.state()
        attraction = next(row for row in state["attractions"] if row["id"] == "triple_triad")
        self.assertEqual(attraction["status"], "open")
        triad = state["triple_triad"]
        self.assertEqual(triad["deck"], list(TRIPLE_TRIAD_STARTER_DECK))
        self.assertEqual(triad["owned_count"], 5)
        self.assertEqual(triad["daily_matches"], TRIPLE_TRIAD_DAILY_MATCHES)
        self.assertFalse(triad["active"])

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
        self.assertEqual(good.data["gold_saucer_state"]["triple_triad"]["deck"], list(reversed(TRIPLE_TRIAD_STARTER_DECK)))

    def test_match_persists_progress_resolves_and_replay_is_exactly_once(self):
        before = self.state()["mgp"]
        opponent = TRIPLE_TRIAD_OPPONENTS_BY_ID["saucer_attendant"]
        started = self.game.portal_triad_start("100", "saucer_attendant", "triad-start-1")
        self.assertTrue(started.ok)
        self.assertEqual(started.data["gold_saucer_state"]["mgp"], before - int(opponent["cost"]))
        self.assertTrue(started.data["gold_saucer_state"]["triple_triad"]["active"])

        first_match = started.data["gold_saucer_state"]["triple_triad"]["match"]
        first_card = first_match["player_hand"][0]["id"]
        first = self.game.portal_triad_play("100", first_card, 0, "triad-play-1")
        self.assertTrue(first.ok)
        replay = self.game.portal_triad_play("100", first_card, 0, "triad-play-1")
        self.assertEqual(replay.data.get("triple_triad_move"), first.data.get("triple_triad_move"))

        result = first
        action_no = 2
        while result.data["gold_saucer_state"]["triple_triad"]["active"]:
            match = result.data["gold_saucer_state"]["triple_triad"]["match"]
            card = match["player_hand"][0]["id"]
            cell = next(index for index, row in enumerate(match["board"]) if row is None)
            result = self.game.portal_triad_play("100", card, cell, f"triad-play-{action_no}")
            self.assertTrue(result.ok)
            action_no += 1

        triad = result.data["gold_saucer_state"]["triple_triad"]
        self.assertFalse(triad["active"])
        self.assertEqual(triad["records"]["matches"], 1)
        self.assertEqual(triad["matches_today"], 1)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='triple_triad'")["n"], 1)

    def test_daily_limit_and_opponent_unlock_gate(self):
        locked = self.game.portal_triad_start("100", "card_shark", "triad-locked")
        self.assertFalse(locked.ok)
        self.assertIn("3 Triple Triad wins", " ".join(locked.messages))

        now = int(time.time())
        for index in range(TRIPLE_TRIAD_DAILY_MATCHES):
            self.db.execute(
                "INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) VALUES (?,'triple_triad',20,0,'loss','{}',?)",
                ("100", now + index),
            )
        blocked = self.game.portal_triad_start("100", "saucer_attendant", "triad-daily-block")
        self.assertFalse(blocked.ok)
        self.assertIn("all Triple Triad entries", " ".join(blocked.messages))

    def test_match_score_includes_cards_in_hand_and_stays_on_ten_point_scale(self):
        started = self.game.portal_triad_start("100", "saucer_attendant", "triad-score-start")
        self.assertTrue(started.ok)
        match = started.data["gold_saucer_state"]["triple_triad"]["match"]
        self.assertEqual(match["player_score"] + match["npc_score"], 10)
        self.assertEqual((match["player_score"], match["npc_score"]), (5, 5))
        card = match["player_hand"][0]["id"]
        played = self.game.portal_triad_play("100", card, 0, "triad-score-play")
        self.assertTrue(played.ok)
        match = played.data["gold_saucer_state"]["triple_triad"]["match"]
        self.assertEqual(match["player_score"] + match["npc_score"], 10)

    def test_streamer_reset_clears_active_match_but_preserves_triad_profile(self):
        state = self.state()
        deck = list(reversed(state["triple_triad"]["deck"]))
        self.assertTrue(self.game.portal_triad_set_deck("100", deck, "triad-reset-deck").ok)
        self.assertTrue(self.game.portal_triad_start("100", "saucer_attendant", "triad-reset-start").ok)
        before = self.state()["triple_triad"]
        self.assertTrue(before["active"])
        reset = self.game.streamer_saucer_reset("van", action_id="triad-admin-reset")
        self.assertTrue(reset.ok)
        after = self.state()["triple_triad"]
        self.assertFalse(after["active"])
        self.assertEqual(after["deck"], deck)
        self.assertEqual(after["owned_count"], before["owned_count"])
        self.assertEqual(after["records"], before["records"])

    def test_worker_validates_triad_actions(self):
        worker = PortalActionWorker(self.game, "", "")
        base = {"protocol_version": ACTION_PROTOCOL_VERSION, "twitch_id": "100", "username": "van", "lease_token": "lease"}
        ok, _message, data = worker._execute({**base, "id": "triad-worker-start", "type": "TRIAD_START", "payload": {"opponent": "saucer_attendant"}})
        self.assertTrue(ok)
        self.assertTrue(data["gold_saucer_state"]["triple_triad"]["active"])
        ok, message, _data = worker._execute({**base, "id": "triad-worker-bad", "type": "TRIAD_PLAY", "payload": {"card": "chocobo", "cell": 99}})
        self.assertFalse(ok)
        self.assertIn("cell", message.lower())


if __name__ == "__main__":
    unittest.main()

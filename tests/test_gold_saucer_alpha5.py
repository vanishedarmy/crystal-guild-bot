"""Card Hall Triple Triad compatibility tests replacing the retired Gold Saucer contract.

Gold Saucer is still responsible for Cactpot/Slots/Monster Toss/Racing, but it
MUST NOT own, charge, reset, or limit the Card Hall Triple Triad tables.
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
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker
from crystal_guild.triple_triad import (
    TRIPLE_TRIAD_CARDS_BY_ID, TRIPLE_TRIAD_OPPONENTS_BY_ID,
    TRIPLE_TRIAD_STARTER_DECK, triple_triad_place,
)

ROOT = Path(__file__).resolve().parents[1]


class CardHallTripleTriadContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"),
                                       overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
                                       rng=random.Random(1605))
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def state(self):
        result = self.game.portal_triad_state("100")
        self.assertTrue(result.ok, result.messages)
        return result.data["triple_triad_state"]

    def points(self):
        self.game.portal_gold_saucer_state("100")
        return int(self.db.one("SELECT points FROM player_gold_saucer WHERE player_id='100'")["points"])

    def test_card_hall_is_standalone_and_has_45_cards(self):
        self.assertEqual(__version__, "1.9.7-queens-blood")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 28)
        self.assertEqual(self.db.schema_version(), 28)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 39)
        saucer = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        self.assertNotIn("triple_triad", [a["id"] for a in saucer["attractions"]])
        self.assertNotIn("triple_triad", saucer)
        triad = self.state()
        self.assertEqual(triad["deck"], list(TRIPLE_TRIAD_STARTER_DECK))
        self.assertEqual(triad["owned_count"], 10)
        self.assertEqual(triad["total_cards"], 45)
        self.assertTrue(triad["unlimited_matches"])
        self.assertFalse(triad["active"])

    def test_basic_capture_flips_adjacent_weaker_card(self):
        board = [None] * 9
        triple_triad_place(board, 4, "flan", "npc")
        self.assertEqual(triple_triad_place(board, 3, "chocobo", "player"), [4])
        self.assertEqual(board[4]["owner"], "player")

    def test_deck_validation_requires_five_unique_owned_cards(self):
        self.assertFalse(self.game.portal_triad_set_deck("100", ["chocobo"] * 5, "deck-bad").ok)
        self.assertFalse(self.game.portal_triad_set_deck("100", ["chocobo", "moogle", "cactuar", "bomb", "bahamut"], "deck-unowned").ok)
        deck = list(reversed(TRIPLE_TRIAD_STARTER_DECK))
        result = self.game.portal_triad_set_deck("100", deck, "deck-good")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(result.data["triple_triad_state"]["deck"], deck)
        self.assertEqual(self.state()["deck"], deck)

    def test_match_move_replay_settlement_and_no_gold_saucer_mgp(self):
        start_mgp = self.points()
        started = self.game.portal_triad_start("100", "saucer_attendant", "start-1")
        self.assertTrue(started.ok, started.messages)
        self.assertEqual(self.points(), start_mgp)
        self.assertTrue(started.data["triple_triad_state"]["active"])
        self.assertEqual(self.game.portal_triad_start("100", "saucer_attendant", "start-1").data["triple_triad_match_id"], started.data["triple_triad_match_id"])
        result = started
        for i in range(5):
            match = result.data["triple_triad_state"]["match"]
            card = match["player_hand"][0]["id"]
            cell = next(n for n, entry in enumerate(match["board"]) if entry is None)
            result = self.game.portal_triad_play("100", card, cell, f"play-{i}")
            self.assertTrue(result.ok, result.messages)
            if i == 0:
                replay = self.game.portal_triad_play("100", card, cell, "play-0")
                self.assertEqual(replay.data["triple_triad_move"], result.data["triple_triad_move"])
        self.assertFalse(result.data["triple_triad_state"]["active"])
        self.assertEqual(result.data["triple_triad_state"]["records"]["matches"], 1)
        record = self.db.one("SELECT wager,payout FROM gold_saucer_history WHERE player_id='100' AND game='triple_triad'")
        self.assertIsNotNone(record)
        self.assertEqual((int(record["wager"]), int(record["payout"])), (0, 0))
        self.assertEqual(self.points(), start_mgp)

    def test_circuits_still_require_unlock_but_old_daily_cap_does_not_apply(self):
        denied = self.game.portal_triad_start("100", "moogle_dealer", "locked")
        self.assertFalse(denied.ok)
        self.assertIn("previous Triple Triad circuit", " ".join(denied.messages))
        now = int(time.time())
        for i in range(15):
            self.db.execute("INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) "
                            "VALUES (?,'triple_triad',0,0,'loss','{}',?)", ("100", now + i))
        started = self.game.portal_triad_start("100", "saucer_attendant", "unlimited")
        self.assertTrue(started.ok, started.messages)
        self.assertTrue(started.data["triple_triad_state"]["unlimited_matches"])

    def test_scores_count_cards_left_in_hand(self):
        state = self.game.portal_triad_start("100", "saucer_attendant", "score").data["triple_triad_state"]
        match = state["match"]
        self.assertEqual((match["player_score"], match["npc_score"]), (5, 5))
        card = match["player_hand"][0]["id"]
        played = self.game.portal_triad_play("100", card, 0, "score-play")
        self.assertTrue(played.ok)
        match = played.data["triple_triad_state"]["match"]
        self.assertEqual(match["player_score"] + match["npc_score"], 10)

    def test_gold_saucer_admin_reset_does_not_reset_card_hall(self):
        deck = list(reversed(self.state()["deck"]))
        self.assertTrue(self.game.portal_triad_set_deck("100", deck, "reset-deck").ok)
        self.assertTrue(self.game.portal_triad_start("100", "saucer_attendant", "reset-start").ok)
        before = self.state()
        self.assertTrue(before["active"])
        self.assertTrue(self.game.streamer_saucer_reset("van", action_id="saucer-reset").ok)
        after = self.state()
        self.assertTrue(after["active"])
        self.assertEqual(after["deck"], deck)
        self.assertEqual(after["match"]["id"], before["match"]["id"])
        self.assertEqual(after["owned_count"], before["owned_count"])

    def test_worker_routes_card_hall_actions_and_rejects_invalid_cell(self):
        worker = PortalActionWorker(self.game, "", "")
        base = {"protocol_version": ACTION_PROTOCOL_VERSION, "twitch_id": "100", "username": "van", "lease_token": "lease"}
        ok, _message, data = worker._execute({**base, "id": "worker-start", "type": "TRIAD_START", "payload": {"opponent": "saucer_attendant"}})
        self.assertTrue(ok)
        self.assertTrue(data["triple_triad_state"]["active"])
        ok, message, _data = worker._execute({**base, "id": "worker-bad", "type": "TRIAD_PLAY", "payload": {"card": "chocobo", "cell": 99}})
        self.assertFalse(ok)
        self.assertIn("cell", message.lower())


if __name__ == "__main__":
    unittest.main()

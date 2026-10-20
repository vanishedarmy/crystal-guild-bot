"""Phase 4: Card Hall restart, exactly-once receipts and player isolation."""
from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class CardHallPhase4PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self._open()
        for player, user in (("100", "van"), ("200", "other")):
            self.assertTrue(self.game.recruit(player, user, user).ok)
            self.assertTrue(self.game.choose_job(player, "warrior").ok)

    def _open(self):
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(197),
        )

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _state(self, player="100"):
        result = self.game.portal_triad_state(player)
        self.assertTrue(result.ok, result.messages)
        return result.data["triple_triad_state"]

    def test_restart_restores_mid_match_and_exact_move_replay(self):
        started = self.game.portal_triad_start("100", "saucer_attendant", "phase4-start")
        self.assertTrue(started.ok)
        match_id = started.data["triple_triad_match_id"]
        hand = self._state()["match"]["player_hand"]
        card = hand[0]["id"]
        first = self.game.portal_triad_play("100", card, 0, "phase4-first-move")
        self.assertTrue(first.ok)
        board = first.data["triple_triad_state"]["match"]["board"]
        self.db.close()
        self._open()
        current = self._state()
        self.assertTrue(current["active"])
        self.assertEqual(current["match"]["id"], match_id)
        self.assertEqual(current["match"]["board"], board)
        self.assertEqual(current["match"]["player_hand"], first.data["triple_triad_state"]["match"]["player_hand"])
        replay = self.game.portal_triad_play("100", card, 0, "phase4-first-move")
        self.assertTrue(replay.ok)
        self.assertEqual(replay.data, first.data)
        self.assertEqual(self._state()["match"]["board"], board)

    def test_restart_after_resolution_cannot_award_second_result(self):
        start = self.game.portal_triad_start("100", "saucer_attendant", "phase4-full-start")
        self.assertTrue(start.ok)
        final = None
        for i in range(5):
            match = self._state()["match"]
            card = match["player_hand"][0]["id"]
            cell = next(n for n, slot in enumerate(match["board"]) if slot is None)
            final = self.game.portal_triad_play("100", card, cell, f"phase4-full-move-{i}")
            self.assertTrue(final.ok, final.messages)
        self.assertFalse(self._state()["active"])
        records_before = self._state()["records"]
        rows_before = self.db.one("SELECT COUNT(*) n FROM gold_saucer_history WHERE player_id='100' AND game='triple_triad'")["n"]
        self.assertEqual(rows_before, 1)
        self.db.close()
        self._open()
        replay = self.game.portal_triad_play("100", card, cell, "phase4-full-move-4")
        self.assertTrue(replay.ok)
        self.assertEqual(replay.data, final.data)
        self.assertEqual(self._state()["records"], records_before)
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM gold_saucer_history WHERE player_id='100' AND game='triple_triad'")["n"], rows_before)

    def test_players_cannot_view_or_mutate_each_others_card_hall_state(self):
        a = self.game.portal_triad_start("100", "saucer_attendant", "phase4-a-start")
        self.assertTrue(a.ok)
        self.assertFalse(self._state("200")["active"])
        denied = self.game.portal_triad_play("200", self._state("100")["match"]["player_hand"][0]["id"], 0, "phase4-b-without-match")
        self.assertFalse(denied.ok)
        self.assertFalse(self._state("200")["active"])
        self.assertTrue(self._state("100")["active"])
        self.assertEqual(self._state("100")["records"]["matches"], 0)
        self.assertEqual(self._state("200")["records"]["matches"], 0)
        self.assertTrue(self.game.portal_triad_start("200", "saucer_attendant", "phase4-b-start").ok)
        self.assertNotEqual(self._state("100")["match"]["id"], self._state("200")["match"]["id"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import PRIZES_BY_ID, gold_saucer_record_value
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class TitleExpansionAlpha3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "guild.db"
        self.db = Database(self.db_path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self) -> None:
        self.db.close()
        self.temp.cleanup()

    def test_new_prize_counter_titles_are_affordable_vanity_options(self):
        self.assertEqual(PRIZES_BY_ID["one_more_spin"]["cost"], 750)
        self.assertEqual(PRIZES_BY_ID["probably_rigged"]["cost"], 1000)
        self.assertEqual(PRIZES_BY_ID["bird_is_the_word"]["cost"], 1250)
        self.assertNotIn("card_shark", PRIZES_BY_ID)
        state = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        ids = {row["id"] for row in state["prizes"]}
        self.assertTrue({"one_more_spin", "probably_rigged", "bird_is_the_word"}.issubset(ids))

    def test_gold_saucer_earned_titles_are_visible_as_challenges(self):
        state = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        challenges = {row["id"]: row for row in state["challenge_titles"]}
        self.assertIn("saucer_high_roller", challenges)
        self.assertIn("golden_saucer_mastery", challenges)
        self.assertIn("saucer_problem", challenges)
        self.assertEqual(challenges["saucer_problem"]["name"], "Secret Challenge")
        self.assertTrue(challenges["saucer_problem"]["progress"]["hidden"])

    def test_high_roller_unlocks_from_authoritative_mgp_lifetime(self):
        self.game.portal_gold_saucer_state("100")
        self.db.execute(
            "UPDATE player_gold_saucer SET lifetime_earned=5000,points=5000 WHERE player_id='100'"
        )
        result = self.game.portal_gold_saucer_state("100")
        self.assertTrue(any("High Roller" in msg for msg in result.messages))
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM achievements WHERE player_id='100' AND achievement_id='saucer_high_roller'"
        ))
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='high_roller'"
        ))
        challenge = next(row for row in result.data["gold_saucer_state"]["challenge_titles"] if row["id"] == "saucer_high_roller")
        self.assertTrue(challenge["unlocked"])

    def test_saucer_record_metrics_use_persistent_history(self):
        self.game.portal_gold_saucer_state("100")
        rows = [
            ("mini_cactpot", 10, 1250, "sum_6", {"sum": 6}),
            ("slots", 15, 800, "triple", {"reels": ["crystal", "crystal", "crystal"]}),
            ("monster_toss", 20, 80, "gold", {"score": 650, "hits": 4, "throws": 5}),
            ("chocobo_racing", 25, 120, "place_1", {"placement": 1}),
            ("triple_triad", 20, 100, "win", {"player_score": 6, "npc_score": 4}),
        ]
        for i, (game, wager, payout, outcome, details) in enumerate(rows):
            self.db.execute(
                "INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) VALUES (?,?,?,?,?,?,?)",
                ("100", game, wager, payout, outcome, json.dumps(details), 1000 + i),
            )
        self.db.execute(
            "INSERT INTO player_triple_triad(player_id,collection_json,deck_json,best_streak) VALUES ('100','[]','[]',3) "
            "ON CONFLICT(player_id) DO UPDATE SET best_streak=3"
        )
        conn = self.db.conn
        self.assertEqual(gold_saucer_record_value(conn, "100", "unique_games"), 4)
        self.assertEqual(gold_saucer_record_value(conn, "100", "cactpot_jackpots"), 1)
        self.assertEqual(gold_saucer_record_value(conn, "100", "slots_jackpots"), 1)
        self.assertEqual(gold_saucer_record_value(conn, "100", "monster_toss_gold_games"), 1)
        self.assertEqual(gold_saucer_record_value(conn, "100", "chocobo_race_wins"), 1)
        # Legacy Triad stats are not Gold Saucer metrics after separation.
        self.assertEqual(gold_saucer_record_value(conn, "100", "triple_triad_best_streak"), 0)

    def test_oh_hi_mark_is_secret_until_same_mark_is_cleared_three_times(self):
        locked = self.game.achievement("100", "oh hi mark")
        self.assertTrue(locked.ok)
        self.assertIn("SECRET ACHIEVEMENT", locked.messages[0])
        hunt_id = next(iter(self.game.data.hunts))
        self.db.execute(
            "INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100',?,3) "
            "ON CONFLICT(player_id,hunt_id) DO UPDATE SET clears=3",
            (hunt_id,),
        )
        listing = self.game.achievements("100", "secret")
        self.assertTrue(listing.ok)
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM achievements WHERE player_id='100' AND achievement_id='oh_hi_mark'"
        ))
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='oh_hi_mark'"
        ))
        revealed = self.game.achievement("100", "oh hi mark")
        self.assertIn("Oh hi Mark.", revealed.messages[0])

    def test_golden_saucer_unlocks_after_six_other_saucer_achievements(self):
        ids = [
            "saucer_high_roller",
            "cactpot_lucky_devil",
            "slots_jackpot",
            "toss_golden_arm",
            "race_chocobo_whisperer",
            "saucer_sampler",
        ]
        for achievement_id in ids:
            self.db.execute(
                "INSERT INTO achievements(player_id, achievement_id) VALUES ('100', ?)",
                (achievement_id,),
            )
        result = self.game.portal_gold_saucer_state("100")
        self.assertTrue(any("Golden Saucer" in msg for msg in result.messages))
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM achievements WHERE player_id='100' AND achievement_id='golden_saucer_mastery'"
        ))
        self.assertIsNotNone(self.db.one(
            "SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='golden_saucer'"
        ))

    def test_portal_snapshot_supports_new_progress_types(self):
        self.game.portal_gold_saucer_state("100")
        self.db.execute("UPDATE player_gold_saucer SET lifetime_earned=4321 WHERE player_id='100'")
        self.db.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES ('100','potion',50) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=50")
        repo = PortalRepository(self.db_path, ROOT / "data")
        payload = repo.achievements("van")
        by_id = {row["id"]: row for row in payload["achievements"]}
        self.assertEqual(by_id["saucer_high_roller"]["progress"]["raw_value"], 4321)
        self.assertEqual(by_id["triad_heart_of_cards"]["category"], "Card Hall")
        self.assertEqual(by_id["professional_hoarder"]["progress"]["raw_value"], 50)
        self.assertEqual(by_id["oh_hi_mark"]["name"], "Secret Achievement")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import (
    DAILY_ALLOWANCE_MGP, DAILY_REWARD_MGP, PRIZES_BY_ID,
    CHOCOBO_RACING_COURSES_BY_ID, TRIPLE_TRIAD_OPPONENTS_BY_ID,
)

ROOT = Path(__file__).resolve().parents[1]


class GoldSaucerAlpha2RebalanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), overlay_state_path=str(Path(self.temp.name) / "overlay.json"))
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_daily_reward_and_recovery_allowance_are_distinct_and_exactly_once(self):
        first = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        self.assertEqual(first["daily_reward_mgp"], 50)
        self.assertEqual(first["daily_allowance_mgp"], 125)
        self.assertEqual(first["mgp"], 550)
        first_day = int(self.db.one("SELECT created_at FROM gold_saucer_history WHERE player_id='100' AND game='daily_reward'")["created_at"])
        with self.db.tx(immediate=True) as conn:
            next_day = self.game._gold_saucer_state_sql(conn, "100", first_day + 86401)
            again = self.game._gold_saucer_state_sql(conn, "100", first_day + 86460)
        self.assertEqual(next_day["mgp"], 550 + DAILY_ALLOWANCE_MGP + DAILY_REWARD_MGP)
        self.assertEqual(again["mgp"], next_day["mgp"])
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='daily_reward'")["n"], 2)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='daily_allowance'")["n"], 1)

    def test_racing_triad_and_prize_counter_use_alpha2_values(self):
        self.assertEqual(CHOCOBO_RACING_COURSES_BY_ID["manderville_sprint"]["payouts"], {1: 120, 2: 70, 3: 35})
        self.assertEqual(CHOCOBO_RACING_COURSES_BY_ID["crystal_circuit"]["payouts"], {1: 190, 2: 105, 3: 50})
        self.assertEqual(CHOCOBO_RACING_COURSES_BY_ID["golden_gauntlet"]["payouts"], {1: 300, 2: 160, 3: 75})
        self.assertEqual(TRIPLE_TRIAD_OPPONENTS_BY_ID["saucer_attendant"]["win_payout"], 100)
        self.assertEqual(TRIPLE_TRIAD_OPPONENTS_BY_ID["card_shark"]["win_payout"], 150)
        self.assertEqual(TRIPLE_TRIAD_OPPONENTS_BY_ID["crystal_master"]["win_payout"], 240)
        self.assertEqual(PRIZES_BY_ID["saucer_regular"]["cost"], 500)
        self.assertEqual(PRIZES_BY_ID["card_hall_master"]["cost"], 9000)


if __name__ == "__main__":
    unittest.main()

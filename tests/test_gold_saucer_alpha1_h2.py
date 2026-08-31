from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.data import GameData
from crystal_guild.gold_saucer import CACTPOT_COST, SLOTS_THEORETICAL_RETURN_PCT


class GoldSaucerAlpha1H2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "cg.db")
        root = Path(__file__).resolve().parents[1]
        self.data = GameData(root / "data")
        self.game = CrystalGuildEngine(self.db, self.data, overlay_state_path=str(Path(self.temp.name) / "overlay.json"))
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_cactpot_new_ticket_resets_at_next_utc_boundary(self):
        now = 1_800_000_123
        with patch("crystal_guild.engine.time.time", return_value=now):
            result = self.game.portal_cactpot_start("100", "h2-cactpot-start")
        self.assertTrue(result.ok)
        row = self.db.one("SELECT available_at FROM cooldowns WHERE player_id='100' AND action='gold_saucer_cactpot'")
        self.assertEqual(int(row["available_at"]), (now - now % 86400) + 86400)
        self.assertEqual(result.data["gold_saucer_state"]["points"], 500 - CACTPOT_COST)

    def test_records_are_derived_without_schema_change(self):
        now = int(time.time())
        self.game.portal_gold_saucer_state("100")
        with self.db.tx(immediate=True) as conn:
            conn.execute("INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) VALUES ('100','slots',15,20,'pair','{}',?)", (now,))
            conn.execute("INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) VALUES ('100','slots',15,400,'triple','{}',?)", (now+1,))
            conn.execute("INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) VALUES ('100','mini_cactpot',10,1080,'sum_21','{}',?)", (now+2,))
            conn.execute("UPDATE player_gold_saucer SET slots_spins=2,slots_wins=2,cactpot_plays=1,cactpot_wins=1,lifetime_earned=lifetime_earned+1500,lifetime_spent=lifetime_spent+40 WHERE player_id='100'")
        state = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        self.assertEqual(self.db.schema_version(), 12)
        self.assertEqual(state["records"]["slots_triples"], 1)
        self.assertEqual(state["records"]["slots_pairs"], 1)
        self.assertEqual(state["records"]["cactpot_high_rolls"], 1)
        self.assertGreater(state["records"]["slots_realized_return_pct"], 1000)
        self.assertEqual(state["balance"]["slots_theoretical_return_pct"], SLOTS_THEORETICAL_RETURN_PCT)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import MONSTER_TOSS_THROWS
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class GoldSaucerRC1HardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(160601),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def state(self):
        return self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]

    def _finish_triad(self, prefix: str):
        result = self.state()["triple_triad"]
        step = 0
        while result["active"]:
            match = result["match"]
            card = match["player_hand"][0]["id"]
            cell = next(index for index, row in enumerate(match["board"]) if row is None)
            played = self.game.portal_triad_play("100", card, cell, f"{prefix}-{step}")
            self.assertTrue(played.ok, played.messages)
            result = played.data["gold_saucer_state"]["triple_triad"]
            step += 1
        return result

    def test_rc1_identity_freezes_schema_protocol_and_all_five_attractions(self):
        self.assertEqual(__version__, "1.8.2-elite-mercs")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 18)
        self.assertEqual(self.db.schema_version(), 18)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 35)
        attractions = self.state()["attractions"]
        self.assertEqual(
            [row["id"] for row in attractions],
            ["mini_cactpot", "crystal_slots", "monster_toss", "chocobo_racing", "triple_triad"],
        )
        self.assertTrue(all(row["status"] == "open" for row in attractions))

    def test_monster_toss_entry_counts_immediately_on_start(self):
        now = 1_800_057_600  # stable UTC day boundary multiple
        with patch("crystal_guild.engine.time.time", return_value=now + 3600):
            started = self.game.portal_monster_toss_start("100", "rc1-toss-start")
        self.assertTrue(started.ok)
        toss = started.data["gold_saucer_state"]["monster_toss"]
        self.assertEqual(toss["games_today"], 1)
        self.assertEqual(toss["games_remaining"], 2)

    def test_monster_toss_cross_midnight_entry_stays_on_start_day(self):
        day = 1_800_057_600
        start_at = day + 86_390
        resolve_at = day + 86_410
        with patch("crystal_guild.engine.time.time", return_value=start_at):
            self.assertTrue(self.game.portal_monster_toss_start("100", "rc1-toss-midnight-start").ok)
        with patch("crystal_guild.engine.time.time", return_value=resolve_at):
            final = None
            for index in range(MONSTER_TOSS_THROWS):
                final = self.game.portal_monster_toss_throw("100", "small_pot", "safe", f"rc1-toss-midnight-{index}")
                self.assertTrue(final.ok)
        row = self.db.one("SELECT created_at FROM gold_saucer_history WHERE player_id='100' AND game='monster_toss'")
        self.assertEqual(int(row["created_at"]), start_at)
        self.assertEqual(final.data["gold_saucer_state"]["monster_toss"]["games_today"], 0)

    def test_triad_entry_counts_immediately_and_cross_midnight_stays_on_start_day(self):
        day = 1_800_057_600
        start_at = day + 86_390
        resolve_at = day + 86_410
        with patch("crystal_guild.engine.time.time", return_value=start_at):
            started = self.game.portal_triad_start("100", "saucer_attendant", "rc1-triad-midnight-start")
        self.assertTrue(started.ok)
        triad = started.data["gold_saucer_state"]["triple_triad"]
        self.assertEqual(triad["matches_today"], 1)
        self.assertEqual(triad["matches_remaining"], 4)
        with patch("crystal_guild.engine.time.time", return_value=resolve_at):
            resolved = self._finish_triad("rc1-triad-midnight-play")
        self.assertFalse(resolved["active"])
        row = self.db.one("SELECT created_at FROM gold_saucer_history WHERE player_id='100' AND game='triple_triad'")
        self.assertEqual(int(row["created_at"]), start_at)
        with self.db.tx(immediate=True) as conn:
            next_day = self.game._gold_saucer_state_sql(conn, "100", resolve_at)
        self.assertEqual(next_day["triple_triad"]["matches_today"], 0)
        self.assertEqual(next_day["triple_triad"]["matches_remaining"], 5)


if __name__ == "__main__":
    unittest.main()

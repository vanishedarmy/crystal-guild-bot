from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import DAILY_ALLOWANCE_MGP, DAILY_REWARD_MGP, WELCOME_MGP
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class GoldSaucerAlpha3MGPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_alpha3_contract_keeps_schema_and_protocol_stable(self):
        self.assertEqual(__version__, "1.9.0-hall-of-trophies-alpha7")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 20)
        self.assertEqual(self.db.schema_version(), 20)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 36)

    def test_mgp_is_canonical_currency_without_resetting_legacy_balance(self):
        state = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        self.assertEqual(state["currency_name"], "MGP")
        self.assertEqual(state["currency_code"], "MGP")
        self.assertEqual(state["mgp"], WELCOME_MGP + DAILY_REWARD_MGP)
        self.assertEqual(state["welcome_mgp"], WELCOME_MGP)
        self.assertEqual(state["daily_allowance_mgp"], DAILY_ALLOWANCE_MGP)
        self.assertEqual(state["daily_reward_mgp"], DAILY_REWARD_MGP)
        # Alpha 2 keys remain additive compatibility aliases.
        self.assertEqual(state["points"], state["mgp"])
        self.assertEqual(state["account"]["points"], state["account"]["mgp"])
        self.assertEqual(state["records"]["net_points"], state["records"]["net_mgp"])

        self.db.execute("UPDATE player_gold_saucer SET points=1234 WHERE player_id='100'")
        refreshed = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        self.assertEqual(refreshed["mgp"], 1234)
        self.assertEqual(refreshed["points"], 1234)

    def test_player_facing_gold_saucer_copy_uses_mgp(self):
        cactpot = self.game.portal_cactpot_start("100", "a3-cactpot")
        self.assertTrue(cactpot.ok)
        self.assertIn("MGP", " ".join(cactpot.messages))
        self.assertNotIn("Saucer Points", " ".join(cactpot.messages))

        self.game.streamer_saucer_reset("van", action_id="a3-reset")
        toss = self.game.portal_monster_toss_start("100", "a3-toss")
        self.assertTrue(toss.ok)
        self.assertIn("MGP", " ".join(toss.messages))

    def test_streamer_grant_returns_canonical_mgp_and_legacy_alias(self):
        result = self.game.streamer_saucer_grant("van | 250", action_id="a3-grant")
        self.assertTrue(result.ok)
        self.assertEqual(result.data["mgp"], WELCOME_MGP + DAILY_REWARD_MGP + 250)
        self.assertEqual(result.data["points"], result.data["mgp"])
        self.assertIn("MGP", " ".join(result.messages))


if __name__ == "__main__":
    unittest.main()

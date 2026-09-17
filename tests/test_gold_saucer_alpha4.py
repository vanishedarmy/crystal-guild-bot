from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.chocobo import total_xp_floor_for_level
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import (
    CHOCOBO_RACING_COURSES_BY_ID,
    CHOCOBO_RACING_DAILY_RACES,
)
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class GoldSaucerAlpha4ChocoboRacingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1604),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def register_racer(self, level: int = 10, trait: str = "lucky_plume") -> None:
        xp = total_xp_floor_for_level(level)
        self.db.execute(
            "INSERT INTO player_chocobos(player_id,name,level,xp,registered_at,portrait_id) VALUES (?,?,?,?,CURRENT_TIMESTAMP,'classic_gold') "
            "ON CONFLICT(player_id) DO UPDATE SET name=excluded.name,level=excluded.level,xp=excluded.xp,registered_at=CURRENT_TIMESTAMP,portrait_id='classic_gold'",
            ("100", "Comet", level, xp),
        )
        self.db.execute("INSERT OR IGNORE INTO player_chocobo_traits(player_id,trait_id) VALUES (?,?)", ("100", trait))

    def test_alpha4_contract_opens_chocobo_racing_without_schema_migration(self):
        self.assertEqual(__version__, "1.8.0-merc-rc3")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 17)
        self.assertEqual(self.db.schema_version(), 17)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 34)
        state = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]
        attraction = next(row for row in state["attractions"] if row["id"] == "chocobo_racing")
        self.assertEqual(attraction["status"], "open")
        self.assertFalse(state["chocobo_racing"]["registered"])
        self.assertEqual(state["chocobo_racing"]["daily_races"], CHOCOBO_RACING_DAILY_RACES)

    def test_registered_chocobo_can_race_and_result_is_exactly_once(self):
        self.register_racer(level=10)
        before = self.game.portal_gold_saucer_state("100").data["gold_saucer_state"]["mgp"]
        course = CHOCOBO_RACING_COURSES_BY_ID["golden_gauntlet"]
        result = self.game.portal_chocobo_race("100", "golden_gauntlet", "balanced", "race-a4-1")
        self.assertTrue(result.ok)
        race = result.data["chocobo_race"]
        self.assertIn(race["placement"], range(1, 7))
        self.assertEqual(race["course_id"], "golden_gauntlet")
        self.assertEqual(race["chocobo_name"], "Comet")
        state = result.data["gold_saucer_state"]
        self.assertEqual(state["mgp"], before - int(course["cost"]) + int(race["payout"]))
        self.assertEqual(state["chocobo_racing"]["races_today"], 1)
        self.assertEqual(state["records"]["chocobo_races"], 1)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='chocobo_racing'")["n"], 1)

        replay = self.game.portal_chocobo_race("100", "golden_gauntlet", "balanced", "race-a4-1")
        self.assertTrue(replay.ok)
        self.assertEqual(replay.data["chocobo_race"], race)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='100' AND game='chocobo_racing'")["n"], 1)

    def test_course_level_gate_and_daily_race_limit(self):
        self.register_racer(level=1, trait="steady_strider")
        blocked = self.game.portal_chocobo_race("100", "crystal_circuit", "steady", "race-gate")
        self.assertFalse(blocked.ok)
        self.assertIn("Lv. 5", " ".join(blocked.messages))

        for index in range(CHOCOBO_RACING_DAILY_RACES):
            result = self.game.portal_chocobo_race("100", "manderville_sprint", "steady", f"race-daily-{index}")
            self.assertTrue(result.ok)
        fourth = self.game.portal_chocobo_race("100", "manderville_sprint", "steady", "race-daily-4")
        self.assertFalse(fourth.ok)
        self.assertIn("all Chocobo Racing entries", " ".join(fourth.messages))

    def test_racing_requires_registered_companion_and_worker_validates_payload(self):
        no_bird = self.game.portal_chocobo_race("100", "manderville_sprint", "balanced", "race-no-bird")
        self.assertFalse(no_bird.ok)
        self.assertIn("registered Chocobo", " ".join(no_bird.messages))

        self.register_racer(level=10)
        worker = PortalActionWorker(self.game, "", "")
        base = {"protocol_version": ACTION_PROTOCOL_VERSION, "twitch_id": "100", "username": "van", "lease_token": "lease"}
        ok, _message, data = worker._execute({**base, "id": "race-worker", "type": "CHOCOBO_RACE", "payload": {"course": "crystal_circuit", "strategy": "sprint"}})
        self.assertTrue(ok)
        self.assertEqual(data["chocobo_race"]["course_id"], "crystal_circuit")
        ok, message, _data = worker._execute({**base, "id": "race-worker-bad", "type": "CHOCOBO_RACE", "payload": {"course": "../../bad", "strategy": "sprint"}})
        self.assertFalse(ok)
        self.assertIn("invalid", message.lower())


if __name__ == "__main__":
    unittest.main()

"""1.9.4.6: active seasonal monsters appear in both Venture modes."""
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.seasonal_events import (
    EDITION_ID,
    SOLO_VENTURE_SEASONAL_CHANCE,
    STREAM_VENTURE_SEASONAL_CHANCE,
    SEASONAL_REPLACEMENT_CHANCE,
    event_state,
    set_event_control,
)

ROOT = Path(__file__).resolve().parents[1]


class SeasonalVentures1946Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1946),
        )
        self.assertTrue(self.game.recruit("42", "hero", "Hero").ok)
        self.assertTrue(self.game.choose_job("42", "warrior").ok)
        self.db.execute("UPDATE players SET level=25 WHERE twitch_id='42'")
        p = self.game._player("42")
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='42'", (self.game._max_hp(p),))
        # Most Venture tests explicitly opt into the event so inactive-state
        # behavior stays deterministic now that Halloween 2026 defaults live.
        with self.db.tx() as conn:
            set_event_control(conn, enabled=False, paused=False, activation_mode="manual")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def activate(self):
        with self.db.tx() as conn:
            set_event_control(conn, enabled=True, paused=False, activation_mode="manual")

    def start_solo(self):
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0):
            result = self.game.solo_venture("42", bypass_cooldown=True)
        self.assertTrue(result.ok, result.messages)
        return self.game._solo_expedition_load("42")

    def test_balanced_probability_per_encounter(self):
        self.assertEqual(SOLO_VENTURE_SEASONAL_CHANCE, 0.35)
        self.assertEqual(STREAM_VENTURE_SEASONAL_CHANCE, 0.40)
        self.assertEqual(SEASONAL_REPLACEMENT_CHANCE, STREAM_VENTURE_SEASONAL_CHANCE)
        self.activate()
        # A 37% roll is a stream replacement, but not a solo replacement.
        with patch.object(self.game.rng, "random", return_value=0.37):
            self.assertIsNone(self.game._roll_seasonal_venture_variant(max_monster_level=40, chance=SOLO_VENTURE_SEASONAL_CHANCE))
            self.assertIsNotNone(self.game._roll_seasonal_venture_variant(max_monster_level=40, chance=STREAM_VENTURE_SEASONAL_CHANCE))

    def test_disabled_paused_and_low_level_do_not_replace(self):
        self.assertIsNone(self.game._roll_seasonal_venture_variant(max_monster_level=40, chance=1.0))
        self.activate()
        self.assertIsNone(self.game._roll_seasonal_venture_variant(max_monster_level=1, chance=1.0))
        with self.db.tx() as conn:
            set_event_control(conn, paused=True)
        self.assertIsNone(self.game._roll_seasonal_venture_variant(max_monster_level=40, chance=1.0))
        with self.db.tx() as conn:
            set_event_control(conn, paused=False, activation_mode="scheduled")
            conn.execute("UPDATE seasonal_event_instances SET starts_at='2099-10-01T00:00:00Z' WHERE edition_id=?", (EDITION_ID,))
            self.assertFalse(event_state(conn)["active"])
        self.assertIsNone(self.game._roll_seasonal_venture_variant(max_monster_level=40, chance=1.0))

    def test_solo_seasonal_creature_persists_and_has_correct_portrait(self):
        self.activate()
        with patch("crystal_guild.engine.SOLO_VENTURE_SEASONAL_CHANCE", 1.0):
            state = self.start_solo()
        encounter = state["combat"]["encounter"]
        self.assertEqual(encounter["seasonal_event_id"], EDITION_ID)
        self.assertTrue(encounter["seasonal_variant_id"])
        self.assertEqual(encounter["monster_override"]["id"], encounter["monster_id"])
        self.assertLessEqual(encounter["monster_override"]["level"], 25 + 5)
        expected = encounter["monster_override"]
        public = self.game._solo_expedition_public("42")
        self.assertEqual(public["combat"]["enemy"]["name"], expected["name"])
        self.assertEqual(public["combat"]["enemy"]["art"], expected["art"])
        self.assertEqual(public["combat"]["enemy"]["seasonal_variant_id"], encounter["seasonal_variant_id"])
        # Every combat round reloads the override from SQLite; no global
        # monster registration or shared-state slots are required.
        second = CrystalGuildEngine(self.db, self.game.data, overlay_state_path=str(Path(self.temp.name)/"resume.json"), rng=random.Random(42))
        self.assertEqual(second._solo_expedition_public("42")["combat"]["enemy"]["art"], expected["art"])
        self.assertIsNone(second.active_encounter)

    def test_solo_without_active_event_keeps_normal_monster(self):
        state = self.start_solo()
        self.assertNotIn("seasonal_variant_id", state["combat"]["encounter"])
        self.assertIn(state["combat"]["encounter"]["monster_id"], self.game.data.monsters)
        self.assertFalse(self.game._solo_expedition_public("42")["combat"]["enemy"]["seasonal_variant_id"])

    def test_retreat_before_seasonal_victory_does_not_grant_tokens(self):
        self.activate()
        with patch("crystal_guild.engine.SOLO_VENTURE_SEASONAL_CHANCE", 1.0):
            state = self.start_solo()
        self.assertTrue(state["combat"]["encounter"]["seasonal_variant_id"])
        self.assertTrue(self.game.solo_expedition_retreat("42").ok)
        self.assertIsNone(self.db.one("SELECT * FROM player_seasonal_event_progress WHERE player_id='42' AND edition_id=?", (EDITION_ID,)))

    def test_solo_victory_grants_tokens_and_event_progress_once(self):
        self.activate()
        with patch("crystal_guild.engine.SOLO_VENTURE_SEASONAL_CHANCE", 1.0):
            state = self.start_solo()
        state["combat"]["encounter"]["monster_hp"] = 1
        self.game._solo_expedition_save("42", state)
        outcome = self.game.solo_expedition_action("42", "attack")
        self.assertTrue(outcome.ok, outcome.messages)
        after = self.game._solo_expedition_load("42")
        self.assertEqual(after["status"], "choice")
        self.assertTrue(after["last_stage"]["seasonal"]["variant_id"])
        self.assertGreaterEqual(int(after["last_stage"]["seasonal"]["tokens"]), 3)
        self.assertTrue(any("Moonlit Tokens" in event["label"] for event in after["history"]))
        clear = self.db.one("SELECT seasonal_kills,tokens FROM player_seasonal_event_progress WHERE player_id='42' AND edition_id=?", (EDITION_ID,))
        self.assertEqual(clear["seasonal_kills"], 1)
        self.assertGreaterEqual(clear["tokens"], 3)
        replay = self.game.solo_expedition_action("42", "attack")
        self.assertFalse(replay.ok)
        clear2 = self.db.one("SELECT seasonal_kills FROM player_seasonal_event_progress WHERE player_id='42' AND edition_id=?", (EDITION_ID,))
        self.assertEqual(clear2["seasonal_kills"], 1)
        returned = self.game.solo_expedition_return("42")
        self.assertTrue(returned.ok, returned.messages)
        completed = self.db.one("SELECT adventures FROM player_seasonal_event_progress WHERE player_id='42' AND edition_id=?", (EDITION_ID,))
        self.assertEqual(completed["adventures"], 1)

    def test_portal_receipt_includes_seasonal_name_and_art(self):
        self.activate()
        with (
            patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0),
            patch("crystal_guild.engine.SOLO_VENTURE_SEASONAL_CHANCE", 1.0),
        ):
            result = self.game.portal_solo_venture("42", "seasonal-portal-1946")
            replay = self.game.portal_solo_venture("42", "seasonal-portal-1946")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(result.data, replay.data)
        expedition = result.data["adventure_state"]["solo_venture"]["expedition"]
        enemy = expedition["combat"]["enemy"]
        self.assertTrue(enemy["seasonal_variant_id"])
        self.assertTrue(enemy["name"])
        self.assertTrue(enemy["art"].startswith("/seasonal/halloween-2026/"))

    def test_stream_spawn_and_normal_when_event_disabled(self):
        self.activate()
        with patch("crystal_guild.engine.SEASONAL_REPLACEMENT_CHANCE", 1.0):
            started = self.game.venture("42", bypass_cooldown=True)
        self.assertTrue(started.ok, started.messages)
        self.assertIn("seasonal_variant_id", self.game.active_encounter)
        self.assertEqual(self.game.active_encounter["monster_id"], self.game.active_encounter["monster_override"]["id"])
        with self.db.tx() as conn:
            set_event_control(conn, enabled=False)
        self.assertIsNone(self.game._roll_seasonal_venture_variant(max_monster_level=40, chance=1.0))


if __name__ == "__main__":
    unittest.main()

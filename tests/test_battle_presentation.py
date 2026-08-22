from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.battle_presentation import (
    compact_event,
    compact_number,
    percent,
    round_summary,
)
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.encounter_daemon import TwitchRESTChatSender, _packed_messages
from crystal_guild.engine import CrystalGuildEngine, GameResult

ROOT = Path(__file__).resolve().parents[1]


class BattlePresentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "battle-presentation.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            venture_cooldown_seconds=0, venture_treasure_chance=0.0,
            encounter_join_seconds=5,
            encounter_round_seconds=5,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(41),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def start(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        started = self.game.start_encounter_battle(opened.data["encounter_id"])
        self.assertTrue(started.ok)
        return opened

    def test_compact_numbers_and_percent_are_readable(self):
        self.assertEqual(compact_number(999), "999")
        self.assertEqual(compact_number(1250), "1.2K")
        self.assertEqual(compact_number(2_000_000), "2M")
        self.assertEqual(percent(25, 100), 25)
        self.assertEqual(percent(0, 0), 0)

    def test_common_round_events_are_compacted(self):
        self.assertEqual(compact_event("Van attacks for 123 [CRITICAL]."), "Van Attack -123 [CRITICAL]")
        self.assertEqual(compact_event("Van Defends and recovers 6 MP."), "Van Defend +6MP")
        self.assertEqual(compact_event("Goblin attacks Van for 42."), "Goblin → Van -42HP")
        self.assertEqual(compact_event("Van suffers 10 Poison damage."), "Van Poison -10HP")

    def test_round_summary_is_bounded_and_reports_omissions(self):
        events = [f"Hero{i} attacks for {100+i}." for i in range(12)]
        summary = round_summary(events, max_events=4, max_chars=150)
        self.assertLessEqual(len(summary), 150)
        self.assertIn("more", summary)

    def test_action_acknowledgement_is_short(self):
        self.start()
        result = self.game.battle_attack("1")
        self.assertTrue(result.ok)
        self.assertEqual(result.messages[0], "QUEUED R1 — Van: Attack.")
        self.assertLess(len(result.messages[0]), 80)

    def test_encounter_status_is_a_dashboard_with_action_label(self):
        self.start()
        self.game.battle_defend("1")
        result = self.game.encounter_status()
        text = " ".join(result.messages)
        self.assertIn("ACTIVE BATTLE", text)
        self.assertIn("Round 1", text)
        self.assertIn("actions 1/1", text)
        self.assertIn("HP", text)
        self.assertIn("AP", text)
        self.assertIn("[Defend]", text)

    def test_round_resolution_uses_two_message_automatic_budget(self):
        opened = self.start()
        # Keep the monster alive so we exercise the normal next-round path.
        self.game.active_encounter["monster_hp"] = max(50_000, int(self.game.active_encounter["monster_hp"]))
        self.game.active_encounter["monster_max_hp"] = self.game.active_encounter["monster_hp"]
        self.game.battle_defend("1")
        result = self.game.advance_encounter_round(opened.data["encounter_id"])
        self.assertTrue(result.ok)
        self.assertFalse(result.data.get("encounter_finished", False))
        self.assertEqual(result.data.get("notification_limit"), 2)
        self.assertEqual(len(result.messages), 2)
        self.assertIn("ROUND 1", result.messages[0])
        self.assertIn("NEXT R2", result.messages[1])
        self.assertTrue(all(len(m) < 480 for m in result.messages))

    def test_battlelog_retains_recent_rounds_and_last_finished_battle(self):
        opened = self.start()
        self.game.active_encounter["monster_hp"] = 50_000
        self.game.active_encounter["monster_max_hp"] = 50_000
        self.game.battle_defend("1")
        self.game.advance_encounter_round(opened.data["encounter_id"])
        active_log = self.game.battle_log()
        self.assertTrue(active_log.ok)
        self.assertIn("R1", " ".join(active_log.messages))

        # Finish the encounter and ensure the in-memory recap survives cleanup.
        self.game.active_encounter["monster_hp"] = 1
        self.game.battle_attack("1")
        finished = self.game.advance_encounter_round(opened.data["encounter_id"])
        self.assertTrue(finished.data.get("encounter_finished"))
        self.assertIsNone(self.game.active_encounter)
        recent = self.game.battle_log()
        self.assertTrue(recent.ok)
        self.assertIn("latest", recent.messages[0])
        self.assertIn("R2", " ".join(recent.messages))


    def test_battlelog_is_read_only_and_does_not_change_deadline(self):
        self.start()
        deadline = float(self.game.active_encounter["next_round_at"])
        round_no = int(self.game.active_encounter["round"])
        result = self.game.battle_log()
        self.assertTrue(result.ok)
        self.assertEqual(float(self.game.active_encounter["next_round_at"]), deadline)
        self.assertEqual(int(self.game.active_encounter["round"]), round_no)

    def test_twitch_exposes_battlelog_as_read_only_adapter(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        self.assertIn('aliases=["roundlog", "combatlog"]', source)
        block = source[source.index("async def battlelog"):source.index("# Active Battle commands")]
        self.assertIn("self.game.battle_log()", block)
        self.assertNotIn("advance_encounter_round", block)
        self.assertNotIn("encounter_daemon.wake", block)

    def test_notification_sender_honors_presentation_budget(self):
        class FakeSender(TwitchRESTChatSender):
            def __init__(self):
                self.sent = []

            def send(self, message: str) -> None:
                self.sent.append(message)

        sender = FakeSender()
        result = GameResult.success(
            "one " + "A" * 300,
            "two " + "B" * 300,
            "three " + "C" * 300,
            notification_limit=2,
        )
        sender.send_result(result)
        self.assertLessEqual(len(sender.sent), 2)
        self.assertTrue(all(len(message) <= 480 for message in sender.sent))

    def test_packed_automatic_round_output_stays_within_budget(self):
        messages = [
            "ROUND 8 — " + "A" * 260,
            "NEXT R9 · 20s | " + "B" * 260,
        ]
        packed = _packed_messages(messages, max_messages=2)
        self.assertLessEqual(len(packed), 2)
        self.assertTrue(all(len(message) <= 480 for message in packed))


if __name__ == "__main__":
    unittest.main()

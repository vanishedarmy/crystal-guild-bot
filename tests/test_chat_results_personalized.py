from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.encounter_daemon import TwitchRESTChatSender
from crystal_guild.engine import CrystalGuildEngine, GameResult

ROOT = Path(__file__).resolve().parents[1]


class PersonalizedChatResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "chat-results.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            venture_treasure_chance=0.0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(91),
        )
        self.game.recruit("1", "van", "Van")
        self.game.recruit("2", "mage", "Mage")
        self.game.choose_job("1", "warrior")
        self.game.choose_job("2", "black mage")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_rally_venture_finish_emits_one_mentioned_result_per_participant(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok, opened.messages)
        self.assertTrue(self.game.join_encounter("2", bypass_cooldown=True).ok)
        self.assertTrue(self.game.start_encounter_battle().ok)
        self.game.encounter_roster["1"].update({"damage": 321, "damage_taken": 44, "healing": 0})
        self.game.encounter_roster["2"].update({"damage": 210, "damage_taken": 22, "healing": 55})

        result = self.game._finish_active_encounter(True, round_no=3)
        self.assertTrue(result.ok, result.messages)
        self.assertIn("Personal results incoming", result.messages[0])
        personal = result.data.get("participant_result_messages") or []
        self.assertEqual(len(personal), 2)
        self.assertTrue(personal[0].startswith("@van — Venture victory"), personal)
        self.assertTrue(personal[1].startswith("@mage — Venture victory"), personal)
        self.assertIn("321 DMG", personal[0])
        self.assertIn("+", personal[0])
        self.assertNotIn("Van +", result.messages[0])

    def test_raid_round_finish_forwards_personal_results(self):
        self.assertTrue(self.game.spawn_boss("bomb king").ok)
        self.assertTrue(self.game.raid_join("1").ok)
        self.assertTrue(self.game.raid_join("2").ok)
        self.assertTrue(self.game.start_raid().ok)
        self.game.active_boss["current_hp"] = 1
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        self.assertTrue(result.data.get("raid_finished"))
        personal = result.data.get("participant_result_messages") or []
        self.assertEqual(len(personal), 2)
        self.assertTrue(any(line.startswith("@van — Raid victory") for line in personal), personal)
        self.assertTrue(any(line.startswith("@mage — Raid victory") for line in personal), personal)
        self.assertTrue(all(" XP" in line and " Gil" in line for line in personal), personal)
        self.assertTrue(any("Personal results incoming" in line for line in result.messages), result.messages)

    def test_sender_preserves_personal_message_boundaries(self):
        class FakeSender(TwitchRESTChatSender):
            def __init__(self):
                self.sent = []

            def send(self, message: str) -> None:
                self.sent.append(message)

        sender = FakeSender()
        result = GameResult.success(
            "RAID VICTORY — Test boss falls.",
            participant_result_messages=[
                "@van — Raid victory · 100 DMG · +200 XP",
                "@mage — Raid victory · 50 heal · +180 XP",
            ],
            participant_message_delay_seconds=0,
            notification_limit=1,
        )
        sender.send_result(result)
        self.assertEqual(sender.sent[0], "RAID VICTORY — Test boss falls.")
        self.assertEqual(sender.sent[1], "@van — Raid victory · 100 DMG · +200 XP")
        self.assertEqual(sender.sent[2], "@mage — Raid victory · 50 heal · +180 XP")

    def test_raid_configured_xp_is_raised_fifty_percent(self):
        # Bomb King was 1,800 configured Victory XP before this rebalance.
        self.assertEqual(int(self.game.data.bosses["bomb_king"]["xp"]), 2700)
        # Ifrit was 4,200 before the same rebalance.
        self.assertEqual(int(self.game.data.bosses["ifrit"]["xp"]), 6300)


if __name__ == "__main__":
    unittest.main()

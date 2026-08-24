from __future__ import annotations

import time
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.encounter_daemon import NotificationDispatcher
from crystal_guild.engine import GameResult

ROOT = Path(__file__).resolve().parents[1]


class _Sender:
    def __init__(self) -> None:
        self.sent = []

    def send_result(self, result) -> None:
        self.sent.append(result)


class ArsenalIITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = GameData(ROOT / "data")

    def test_core_casters_have_twelve_step_spellbooks(self):
        casters = {"blackmage", "whitemage", "redmage", "summoner", "bluemage", "timemage", "sage"}
        for job_id in casters:
            abilities = self.data.active_abilities[job_id]
            self.assertEqual(len(abilities), 12, job_id)
            self.assertEqual([a["level"] for a in abilities], [1, 5, 8, 12, 15, 18, 22, 26, 30, 35, 40, 45])
            expressive = sum(bool(a.get("element")) or any(effect.get("type") in {"status", "heal", "cleanse", "drain", "restore_mp", "restore_ap", "revive"} for effect in a.get("effects", [])) for a in abilities)
            self.assertGreaterEqual(expressive, 8, job_id)

    def test_every_non_caster_has_eight_active_abilities(self):
        casters = {"blackmage", "whitemage", "redmage", "summoner", "bluemage", "timemage", "sage"}
        for job_id in set(self.data.jobs) - casters:
            self.assertEqual(len(self.data.active_abilities[job_id]), 8, job_id)

    def test_offline_gate_suppresses_autonomous_twitch_delivery(self):
        sender = _Sender()
        dispatcher = NotificationDispatcher(sender, delivery_allowed=lambda: False)
        dispatcher.start()
        try:
            dispatcher.enqueue(GameResult.success("Portal action complete."))
            deadline = time.time() + 2
            while dispatcher.status()["suppressed_batches"] < 1 and time.time() < deadline:
                time.sleep(0.02)
            self.assertEqual(sender.sent, [])
            self.assertEqual(dispatcher.status()["suppressed_batches"], 1)
            self.assertEqual(dispatcher.status()["failed_batches"], 0)
        finally:
            dispatcher.stop()

    def test_live_gate_allows_autonomous_twitch_delivery(self):
        sender = _Sender()
        dispatcher = NotificationDispatcher(sender, delivery_allowed=lambda: True)
        dispatcher.start()
        try:
            dispatcher.enqueue(GameResult.success("Portal action complete."))
            deadline = time.time() + 2
            while not sender.sent and time.time() < deadline:
                time.sleep(0.02)
            self.assertEqual(len(sender.sent), 1)
        finally:
            dispatcher.stop()


if __name__ == "__main__":
    unittest.main()

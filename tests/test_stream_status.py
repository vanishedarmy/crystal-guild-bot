from __future__ import annotations

import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from crystal_guild.stream_status import TwitchStreamStatus


ROOT = Path(__file__).resolve().parents[1]


class _Probe(TwitchStreamStatus):
    def __init__(self, rows):
        super().__init__("cid", "secret", "123", cache_seconds=15, stale_seconds=90)
        self.rows = rows
        self.calls = 0

    def _get_app_token(self, *, force_refresh: bool = False) -> str:
        return "token"

    def _query_stream(self, token: str):
        self.calls += 1
        value = self.rows.pop(0)
        if isinstance(value, BaseException):
            raise value
        return {"data": value}


class StreamStatusTests(unittest.TestCase):
    def test_live_stream_is_detected_and_cached(self):
        probe = _Probe([[{"title": "Guild Night", "game_name": "Final Fantasy", "started_at": "2026-08-22T20:00:00Z"}]])
        first = probe.refresh()
        second = probe.refresh()
        self.assertEqual(first["state"], "LIVE")
        self.assertTrue(first["live"])
        self.assertEqual(first["title"], "Guild Night")
        self.assertEqual(probe.calls, 1)
        self.assertEqual(second["state"], "LIVE")

    def test_empty_stream_list_is_offline(self):
        probe = _Probe([[]])
        status = probe.refresh()
        self.assertEqual(status["state"], "OFFLINE")
        self.assertFalse(status["live"])

    def test_stale_success_fails_closed_after_probe_error(self):
        probe = _Probe([[{"title": "Live"}], urllib.error.URLError("temporary")])
        with patch("crystal_guild.stream_status.time.time", return_value=1000.0):
            live = probe.refresh(force=True)
        self.assertEqual(live["state"], "LIVE")
        with patch("crystal_guild.stream_status.time.time", return_value=1100.0):
            unknown = probe.refresh(force=True)
        self.assertEqual(unknown["state"], "UNKNOWN")
        self.assertFalse(unknown["live"])
        self.assertIn("URLError", unknown["last_error"])

    def test_twitch_adapter_gates_only_live_gameplay_mutations(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        for activity in (
            '"Rally Venture"',
            '"Rally participation"',
            '"Active Hunt"',
            '"Combat actions"',
            '"Raid participation"',
            '"Raid actions"',
        ):
            self.assertIn(f"_require_stream_live(ctx, {activity})", source)
        self.assertIn('in_timed_combat = (', source)
        self.assertIn('self.game.active_boss', source)
        self.assertIn('self.game.active_encounter', source)
        self.assertIn('if in_timed_combat and not await self._require_stream_live(ctx, "Combat actions")', source)
        # Read-only status/catalog commands and Portal actions are intentionally
        # not routed through this Twitch chat gate.
        self.assertIn("async def encounter(self", source)
        self.assertIn("async def bosses(self", source)
        self.assertIn("async def streamstatus(self", source)
        portal = (ROOT / "crystal_guild" / "portal_actions.py").read_text(encoding="utf-8")
        self.assertIn('action_type == "SOLO_VENTURE"', portal)
        self.assertIn('action_type == "CHALLENGE_HUNT"', portal)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.chat_ux import (
    FeedbackGate,
    canonical_command,
    command_usage,
    format_command_error,
    should_silence_command_error,
    is_crystal_guild_command,
    suggest_command,
)
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.help_system import help_messages
from crystal_guild.time_format import format_duration

ROOT = Path(__file__).resolve().parents[1]


class CommandUXTests(unittest.TestCase):
    def test_help_aliases_resolve_to_guild_front_door(self):
        for alias in ("rpghelp", "cghelp", "cgcommands", "rpg"):
            self.assertEqual(canonical_command(alias), "guild")
        self.assertEqual(command_usage("cghelp"), "!guild [topic]")
        for retired in ("help", "commands", "version"):
            self.assertFalse(is_crystal_guild_command(retired))

    def test_fellowship_commands_are_owned_and_aliases_resolve(self):
        for command in ("fellowship", "project", "contribute", "orders", "deeds", "facilities", "contributions", "rank", "fellowshipproject"):
            self.assertTrue(is_crystal_guild_command(command), command)
        self.assertEqual(canonical_command("guildinfo"), "fellowship")
        self.assertEqual(canonical_command("guildrecord"), "contributions")
        self.assertEqual(canonical_command("guildrank"), "rank")
        self.assertEqual(command_usage("guildrank"), "!rank")

    def test_unknown_typo_gets_useful_command_suggestion(self):
        self.assertEqual(suggest_command("inventroy"), "inventory")
        text = format_command_error("CommandNotFound", "inventroy")
        self.assertIn("!inventory", text)
        self.assertIn("!guild", text)

    def test_live_router_silences_unknown_foreign_commands(self):
        self.assertTrue(should_silence_command_error("CommandNotFound"))
        self.assertFalse(should_silence_command_error("MissingRequiredArgument"))
        self.assertFalse(should_silence_command_error("CommandOnCooldown"))
        foreign = ("lurk", "discord", "socials", "song", "uptime", "followage", "watchtime", "so", "permit", "quote", "8ball", "gamble", "points", "she", "commands", "help", "version")
        for name in foreign:
            self.assertFalse(is_crystal_guild_command(name), name)

    def test_twitch_adapter_drops_unknown_before_logging_or_feedback(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        block = source[source.index("async def event_command_error"):source.index("def main()")]
        guard = block.index("should_silence_command_error(error_name)")
        logger = block.index("LOGGER.error")
        formatter = block.index("format_command_error")
        self.assertLess(guard, logger)
        self.assertLess(guard, formatter)
        self.assertIn("if should_silence_command_error(error_name):\n            return", block)

    def test_missing_argument_feedback_includes_exact_usage(self):
        text = format_command_error("MissingRequiredArgument", "equip", "equip")
        self.assertIn("!equip <item>", text)
        self.assertIn("!guild equip", text)

    def test_cooldown_feedback_is_short_and_actionable(self):
        text = format_command_error("CommandOnCooldown", "venture", "venture", 12.8)
        self.assertIn("!venture", text)
        self.assertIn("12s", text)

    def test_canonical_timer_format_uses_week_day_hour_minute_second_ladder(self):
        self.assertEqual(format_duration(0), "0s")
        self.assertEqual(format_duration(62), "1m 2s")
        self.assertEqual(format_duration(3_602), "1h 0m 2s")
        self.assertEqual(format_duration(90_061), "1d 1h 1m 1s")
        self.assertEqual(format_duration(788_645), "1w 2d 3h 4m 5s")

    def test_feedback_gate_suppresses_repeat_noise_per_user_and_bucket(self):
        gate = FeedbackGate(cooldown_seconds=8)
        self.assertTrue(gate.allow("1", "unknown", now=100))
        self.assertFalse(gate.allow("1", "unknown", now=104))
        self.assertTrue(gate.allow("1", "owner", now=104))
        self.assertTrue(gate.allow("2", "unknown", now=104))
        self.assertTrue(gate.allow("1", "unknown", now=109))

    def test_general_help_is_compact_and_guides_to_guild(self):
        messages = help_messages()
        self.assertLessEqual(len(messages), 2)
        text = " ".join(messages)
        self.assertIn("MOGNET", text)
        self.assertIn("!guild", text)
        self.assertIn("!next", text)


class OnboardingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "command-ux.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0, venture_treasure_chance=0.0)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_recruitment_is_two_message_onboarding_with_help_escape_hatch(self):
        result = self.game.recruit("1", "van", "Van")
        self.assertTrue(result.ok)
        self.assertEqual(len(result.messages), 2)
        text = " ".join(result.messages)
        self.assertIn("!job warrior", text)
        self.assertIn("!venture", text)
        self.assertIn("!next", text)
        self.assertIn("!guild", text)

    def test_unregistered_command_feedback_points_to_start_guide(self):
        result = self.game.hero("missing")
        self.assertFalse(result.ok)
        self.assertIn("!recruit", result.messages[0])
        self.assertIn("!guild start", result.messages[0])

    def test_twitch_adapter_exposes_guild_and_reconnect_wake(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        self.assertIn('async def guild(', source)
        self.assertIn('"rpghelp"', source)
        event_ready = source[source.index("async def event_ready"):source.index("async def event_command_error")]
        self.assertIn("encounter_daemon.wake()", event_ready)
        self.assertIn("_ready_count += 1", event_ready)

    def test_owner_commands_use_shared_feedback_gate(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        self.assertIn("async def _owner_only", source)
        self.assertIn('feedback_gate.allow(uid, "owner-only")', source)
        self.assertNotIn("if uid != self.bot.settings.owner_id", source)

    def test_owner_recovery_commands_are_registered_and_owner_gated(self):
        twitch_source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        ux_source = (ROOT / "crystal_guild" / "chat_ux.py").read_text(encoding="utf-8")
        for command in ("readyall", "resettimers", "clearadventures"):
            self.assertIn(f'async def {command}(', twitch_source)
            block = twitch_source[twitch_source.index(f'async def {command}('):]
            next_decorator = block.find("@commands.command", 1)
            block = block[:next_decorator if next_decorator >= 0 else len(block)]
            self.assertIn("await self._owner_only(ctx)", block)
            self.assertIn(f'"{command}": "!{command}"', ux_source)

    def test_owner_inventory_admin_commands_are_registered_and_owner_gated(self):
        twitch_source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        ux_source = (ROOT / "crystal_guild" / "chat_ux.py").read_text(encoding="utf-8")
        for command in ("additem", "removeitem"):
            self.assertIn(f"async def {command}(", twitch_source)
            block = twitch_source[twitch_source.index(f"async def {command}("):]
            next_decorator = block.find("@commands.command", 1)
            block = block[:next_decorator if next_decorator >= 0 else len(block)]
            self.assertIn("await self._owner_only(ctx)", block)
            self.assertIn("streamer_item_admin", block)
            self.assertIn(f'"{command}": "!{command}', ux_source)

    def test_fellowship_project_command_is_owner_gated(self):
        twitch_source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        block = twitch_source[twitch_source.index("async def fellowshipproject("):]
        block = block[:block.index("@commands.command()", 1)]
        self.assertIn("await self._owner_only(ctx)", block)
        self.assertIn("set_fellowship_project", block)

    def test_local_simulator_mirrors_guild_front_door(self):
        source = (ROOT / "crystal_guild" / "simulator.py").read_text(encoding="utf-8")
        self.assertIn('"guild", "rpghelp", "rpg"', source)
        self.assertIn('format_command_error("CommandNotFound", cmd)', source)
        self.assertIn('show(game.next_step(uid))', source)


if __name__ == "__main__":
    unittest.main()

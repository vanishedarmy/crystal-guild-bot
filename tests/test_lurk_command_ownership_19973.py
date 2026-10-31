"""Protect stream-level !lurk from being claimed by Crystal Guild."""
from pathlib import Path
import re
import unittest

from crystal_guild.chat_ux import command_usage, is_crystal_guild_command, should_silence_command_error
from crystal_guild.help_system import ALIASES

ROOT = Path(__file__).resolve().parents[1]


class LurkCommandOwnershipTests(unittest.TestCase):
    def test_lurkmode_is_a_standalone_twitch_command_without_short_alias(self):
        source = (ROOT / "crystal_guild" / "twitch_bot.py").read_text(encoding="utf-8")
        self.assertRegex(source, r"@commands\.command\(\)\s*async def lurkmode\(")
        self.assertNotRegex(source, r"@commands\.command\(aliases=\[[^\]]*[\"']lurk[\"']")

    def test_short_lurk_is_not_owned_and_unknown_commands_remain_silent(self):
        self.assertTrue(is_crystal_guild_command("lurkmode"))
        self.assertFalse(is_crystal_guild_command("lurk"))
        self.assertNotIn("lurk", ALIASES)
        self.assertTrue(should_silence_command_error("CommandNotFound"))
        self.assertEqual(command_usage("lurkmode"), "!lurkmode on | off | status")


if __name__ == "__main__":
    unittest.main()

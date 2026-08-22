from __future__ import annotations

import unittest

from crystal_guild.help_system import help_messages


class HelpSystemTests(unittest.TestCase):
    def test_general_help_points_to_next_and_topics(self):
        text = " ".join(help_messages())
        self.assertIn("!next", text)
        self.assertIn("!cghelp jobs", text)

    def test_command_alias_resolves_to_topic(self):
        text = " ".join(help_messages("equipment"))
        self.assertIn("INVENTORY", text)
        self.assertIn("!gear", text)

    def test_unknown_topic_is_friendly(self):
        text = " ".join(help_messages("chocobo-tax-law"))
        self.assertIn("No help topic", text)


if __name__ == "__main__":
    unittest.main()

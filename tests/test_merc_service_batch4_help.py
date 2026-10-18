"""Merc Service help contracts, discoverable by unittest on Windows and Linux."""
import unittest

from crystal_guild.help_system import help_messages


class MercHelpTests(unittest.TestCase):
    def test_merc_help_topic_explains_hunt_seals_and_contract_rules(self):
        text = " ".join(help_messages("mercs"))
        self.assertIn("Hunt Seals", text)
        self.assertIn("other Guild services", text)
        self.assertNotIn("Hunt Marks", text)
        self.assertIn("consumed only when", text)
        self.assertIn("does not refund", text)

    def test_merc_help_aliases_route_to_same_topic(self):
        self.assertEqual(help_messages("merc"), help_messages("mercs"))


if __name__ == "__main__":
    unittest.main()

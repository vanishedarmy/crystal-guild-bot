from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from resolve_twitch_ids import _clean_login, _replace_env_values
from upgrade_crystal_guild import _upgrade_command_prefix, _upgrade_combat_timing_defaults

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


class SetupTests(unittest.TestCase):
    def test_login_cleanup(self):
        self.assertEqual(_clean_login(" @VanishedArmy "), "vanishedarmy")

    def test_env_id_replacement_preserves_other_values(self):
        source = "TWITCH_CLIENT_ID=abc\nTWITCH_BOT_ID=\nTWITCH_OWNER_ID=123\nBOT_PREFIX=!\n"
        result = _replace_env_values(source, {"TWITCH_BOT_ID": "456", "TWITCH_OWNER_ID": "789"})
        self.assertIn("TWITCH_CLIENT_ID=abc", result)
        self.assertIn("TWITCH_BOT_ID=456", result)
        self.assertIn("TWITCH_OWNER_ID=789", result)
        self.assertIn("BOT_PREFIX=!", result)


    def test_v115_upgrade_restores_experimental_ampersand_prefix_without_touching_other_env_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("TWITCH_CLIENT_ID=abc\nBOT_PREFIX=&\nPORTAL_SYNC_KEY=keep-me\n", encoding="utf-8")
            _upgrade_command_prefix(env_path)
            updated = env_path.read_text(encoding="utf-8")
            self.assertIn("BOT_PREFIX=!", updated)
            self.assertNotIn("BOT_PREFIX=&", updated)
            self.assertIn("PORTAL_SYNC_KEY=keep-me", updated)

    def test_v115_example_defaults_to_exclamation_command_prefix(self):
        example = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("BOT_PREFIX=!", example)

    def test_setup_helpers_are_packaged(self):
        self.assertTrue((ROOT / "resolve_twitch_ids.bat").exists())
        self.assertTrue((ROOT / "open_twitch_authorization.bat").exists())
        self.assertTrue((ROOT / "README_FIRST.txt").exists())

    def test_full_readme_contains_required_twitch_oauth_flow(self):
        readme = (ROOT / "FULL_SETUP_README.md").read_text(encoding="utf-8")
        self.assertIn("http://localhost:4343/oauth/callback", readme)
        self.assertIn("user:read:chat", readme)
        self.assertIn("user:write:chat", readme)
        self.assertIn("user:bot", readme)
        self.assertIn("channel:bot", readme)
        self.assertIn("https://dev.twitch.tv/console/apps", readme)

    def test_full_readme_contains_web_deploy_and_secret_separation(self):
        readme = (ROOT / "FULL_SETUP_README.md").read_text(encoding="utf-8")
        self.assertIn("https://dashboard.render.com", readme)
        self.assertIn("PORTAL_SYNC_KEY", readme)
        self.assertIn("PORTAL_PUBLIC_URL", readme)
        self.assertIn("Never put", readme)
        self.assertIn("crystal_guild.db", readme)

    def test_runtime_dependency_is_pinned_to_twitchio_3_2_2(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("twitchio==3.2.2", requirements.lower())


if __name__ == "__main__":
    unittest.main()

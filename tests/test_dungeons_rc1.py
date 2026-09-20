from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]

class DungeonsRC1Tests(unittest.TestCase):
    def test_rc1_identity_and_feature_freeze(self):
        self.assertEqual(__version__, "1.9.0-trading-post-alpha1")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 19)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 36)
        data = GameData(ROOT / "data")
        self.assertEqual(len(data.dungeons), 4)

    def test_rc1_shipping_tree_excludes_runtime_overlay_state_and_legacy_hotfix_notes(self):
        self.assertFalse((ROOT / "RELEASE_NOTES_HOTFIX4.md").exists())
        self.assertFalse((ROOT / "UPGRADE_GUIDE_HOTFIX4.md").exists())
        self.assertIn("overlay/state.json", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_project_metadata_and_deployment_docs_are_current(self):
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(pyproject["project"]["version"], "1.9.0a1")
        for name in ("FULL_SETUP_README.md", "RENDER_CLOUD_SETUP.md", "SIMPLE_RENDER_SETUP.md", "WEB_SYNC_SETUP.md"):
            text=(ROOT/name).read_text(encoding="utf-8")
            self.assertIn("1.9.0", text, name)
            self.assertNotIn("matching v1.1.16 Web", text, name)
        for name in ("run_maintenance.py", "run_stress_test.py", "prepare_render_migration.py", "setup_windows.bat", "run_selftest.bat", "run_stress_test.bat", "open_twitch_authorization.bat"):
            text=(ROOT/name).read_text(encoding="utf-8")
            self.assertIn("v1.9.0", text, name)
            self.assertNotIn("v1.1.16", text, name)
            self.assertNotIn("v1.1.17", text, name)

if __name__ == "__main__":
    unittest.main()

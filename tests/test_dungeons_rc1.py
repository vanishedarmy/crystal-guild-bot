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
        self.assertEqual(__version__, "1.9.7-queens-blood")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 27)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 39)
        data = GameData(ROOT / "data")
        self.assertEqual(len(data.dungeons), 4)

    def test_rc1_shipping_tree_excludes_runtime_overlay_state_and_legacy_hotfix_notes(self):
        self.assertFalse((ROOT / "RELEASE_NOTES_HOTFIX4.md").exists())
        self.assertFalse((ROOT / "UPGRADE_GUIDE_HOTFIX4.md").exists())
        self.assertIn("overlay/state.json", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_project_metadata_and_deployment_docs_are_current(self):
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(pyproject["project"]["version"], "1.9.7")
        # Current guidance is authoritative; older per-feature setup guides
        # retain historical release numbers for migration reference only.
        current = (ROOT / "README_FIRST.txt").read_text(encoding="utf-8")
        render = (ROOT / "RENDER_CLOUD_SETUP.md").read_text(encoding="utf-8")
        upgrade = (ROOT / "UPGRADE_GUIDE.md").read_text(encoding="utf-8")
        self.assertTrue(current.startswith("# Crystal Guild v1.9.7"))
        self.assertIn("Bot and hosted Web services", current)
        self.assertIn("schema stays **27**", current)
        self.assertIn("protocol stays **39**", current)
        self.assertTrue(render.startswith("# Current cloud setup — Crystal Guild v1.9.7"))
        self.assertIn("Bot schema: **27**", render)
        self.assertTrue(upgrade.startswith("# v1.9.7"))
        # Historical docs and runnable setup scripts must still ship, but
        # their original version labels do not define the current release.
        for name in ("FULL_SETUP_README.md", "SIMPLE_RENDER_SETUP.md", "WEB_SYNC_SETUP.md", "run_maintenance.py", "run_stress_test.py", "prepare_render_migration.py", "setup_windows.bat", "run_selftest.bat", "run_stress_test.bat", "open_twitch_authorization.bat"):
            self.assertTrue((ROOT / name).is_file(), name)

if __name__ == "__main__":
    unittest.main()

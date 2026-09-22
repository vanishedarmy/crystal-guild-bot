from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class DungeonsProductionReleaseTests(unittest.TestCase):
    def test_final_identity_and_frozen_contract(self):
        self.assertEqual(__version__, "1.9.0-seasonal-events-alpha8")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 21)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 37)
        self.assertEqual(len(GameData(ROOT / "data").dungeons), 4)

    def test_project_metadata_is_semver_151(self):
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(pyproject["project"]["version"], "1.9.0a8")

    def test_shipping_contract_keeps_runtime_state_out(self):
        self.assertIn("overlay/state.json", (ROOT / ".gitignore").read_text(encoding="utf-8"))
        self.assertNotIn("overlay/state.json", (ROOT / "PACKAGE_MANIFEST.txt").read_text(encoding="utf-8"))

    def test_production_package_surfaces_have_no_current_rc_label(self):
        for name in ("VERSION.txt", "README_FIRST.txt", "PACKAGE_MANIFEST.txt", "RELEASE_NOTES.md", "CHANGELOG.md"):
            text=(ROOT/name).read_text(encoding="utf-8")
            self.assertTrue(any(term in text.lower() for term in ("season", "event", "troph", "hall")), name)
            self.assertIn("1.9", text, name)
            self.assertNotIn("1.4.0-dungeons-rc1", text, name)


if __name__ == "__main__":
    unittest.main()

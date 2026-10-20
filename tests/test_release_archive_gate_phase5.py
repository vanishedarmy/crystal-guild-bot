"""Phase 5: ensure release ZIPs never contain runtime state or private credentials."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_archive_gate", ROOT / "tools" / "check_release_archive.py")
assert SPEC and SPEC.loader
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class ReleaseArchiveGateTests(unittest.TestCase):
    def check_entries(self, entries: list[str]) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "Bot.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                for name in entries:
                    zipped.writestr(name, "placeholder")
            return GATE.violations(str(archive))

    def test_safe_code_and_public_templates_allowed(self):
        self.assertEqual(self.check_entries([
            "Bot/run_bot.py", "Bot/overlay/raid_overlay.html", "Bot/.env.example",
            "Bot/data/items.json", "Bot/README_FIRST.txt",
        ]), [])

    def test_live_database_and_overlay_state_rejected(self):
        findings = self.check_entries([
            "Bot/overlay/state.json", "Bot/guild.db", "Bot/guild.db-wal", "Bot/twitch_tokens.db",
        ])
        self.assertEqual(len(findings), 4)
        self.assertTrue(any("live overlay state" in row for row in findings))

    def test_secrets_logs_and_caches_rejected(self):
        findings = self.check_entries([
            "Bot/.env", "Bot/.env.production", "Bot/.tio.tokens.json",
            "Bot/logs/bot.log", "Bot/__pycache__/engine.cpython-313.pyc",
        ])
        self.assertEqual(len(findings), 5)

    def test_unsafe_archive_paths_rejected(self):
        findings = self.check_entries(["../secret.txt", "Bot/../../escape", "Bot/run_bot.py"])
        self.assertEqual(len(findings), 2)


if __name__ == "__main__":
    unittest.main()

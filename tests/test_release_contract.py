from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_sync import SYNC_VERSION
from crystal_guild.player_snapshot import SNAPSHOT_VERSION
from run_stress_test import run_stress


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


class ReleaseReadinessTests(unittest.TestCase):
    def test_release_identity_is_final_guild_expansion_without_hosted_sync_schema_break(self):
        self.assertEqual(__version__, "1.7.0-retainer-a1")
        self.assertEqual(SYNC_VERSION, "1.1.15-wayfarer")
        self.assertEqual(SNAPSHOT_VERSION, "1.1.15-wayfarer")

    def test_database_integrity_report_checks_fk_and_runtime_pragmas(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, GameData(ROOT / "data"), overlay_state_path=str(Path(tmp) / "overlay.json"))
                self.assertTrue(game.recruit("1", "van", "Van").ok)
                report = db.integrity_report()
                self.assertTrue(report["ok"])
                self.assertEqual(report["quick_check"], [])
                self.assertEqual(report["foreign_key_violations"], [])
                self.assertEqual(report["journal_mode"], "wal")
                self.assertGreaterEqual(report["busy_timeout_ms"], 1000)
                self.assertEqual(report["players"], 1)
                self.assertEqual(db.schema_version(), 14)
                self.assertIsNotNone(db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='portal_adventure_results'"))
            finally:
                db.close()

    def test_non_destructive_recovery_drill_reopens_a_real_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "live.db"
            db = Database(db_path)
            try:
                game = CrystalGuildEngine(db, GameData(ROOT / "data"), overlay_state_path=str(Path(tmp) / "overlay.json"))
                game.recruit("1", "van", "Van")
                game.choose_job("1", "warrior")
                before = db.one("SELECT level, gil FROM players WHERE twitch_id='1'")
                before_pair = (int(before["level"]), int(before["gil"]))
            finally:
                db.close()

            env = os.environ.copy()
            env["DATABASE_PATH"] = str(db_path)
            env["DATA_DIR"] = str(ROOT / "data")
            result = subprocess.run(
                [sys.executable, "run_maintenance.py", "--recovery-drill"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS — non-destructive backup/restore drill", result.stdout)

            reopened = Database(db_path)
            try:
                after = reopened.one("SELECT level, gil FROM players WHERE twitch_id='1'")
                self.assertEqual((int(after["level"]), int(after["gil"])), before_pair)
            finally:
                reopened.close()

    def test_synthetic_stress_guardrails_hold(self):
        result = run_stress(players=30, operations=180, readers=1, seed=99)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["players"], 30)
        self.assertEqual(result["quick_check_failures"], 0)
        self.assertEqual(result["foreign_key_violations"], 0)
        self.assertEqual(result["negative_gil_rows"], 0)
        self.assertEqual(result["negative_inventory_rows"], 0)
        self.assertEqual(result["portal_read_errors"], 0)

    def test_control_panel_exposes_release_drills(self):
        panel = (ROOT / "CRYSTAL_GUILD_CONTROL_PANEL.bat").read_text(encoding="utf-8")
        self.assertIn("v1.7.0 - RETAINER SERVICE ALPHA 1", panel)
        self.assertIn("Run Non-Destructive Recovery Drill", panel)
        self.assertIn("Run Synthetic Stress Test", panel)
        self.assertIn("run_recovery_drill.bat", panel)
        self.assertIn("run_stress_test.bat", panel)

    def test_current_finalization_audit_matches_final_package_identity(self):
        audit = (ROOT / "FINALIZATION_AUDIT.md").read_text(encoding="utf-8")
        manifest = (ROOT / "PACKAGE_MANIFEST.txt").read_text(encoding="utf-8")
        self.assertIn("v1.7.0 Retainer Service Alpha 1", audit)
        self.assertIn("1.7.0-retainer-a1", audit)
        self.assertIn("Gold Saucer", manifest)
        self.assertNotIn("v1.1.19 — Retro Phase III RC1 Finalization Audit", audit)
        self.assertNotIn("Expeditions Alpha 2 Hotfix 1 Finalization", audit)

    def test_source_tree_has_no_superseded_hotfix_debris(self):
        # In the repository, release docs live one level above bot/. In the
        # standalone Bot archive they are copied into the package root.
        release_root = ROOT if (ROOT / "VALIDATION_REPORT.md").exists() else REPO
        forbidden_names = {
            "BESTIARY_ORDER_HOTFIX1.md",
            "CAMP_COUNTDOWN_HOTFIX.md",
            "CAMP_COUNTDOWN_HOTFIX2.md",
            "COMMAND_ROUTER_HOTFIX1.md",
            "GUIDE_INLINE_COMMAND_COPY_HOTFIX1.md",
            "GUIDE_ITEM_NOTES_HOTFIX1.md",
            "GUIDE_STATS_REFERENCE_HOTFIX1.md",
            "MP_AP_PERSISTENCE_HOTFIX.md",
            "REPOSITORY_MANIFEST.txt",
        }
        present = {path.name for path in release_root.rglob("*") if path.is_file()}
        self.assertTrue(forbidden_names.isdisjoint(present), forbidden_names & present)
        self.assertFalse((release_root / "web" / "Procfile").exists())
        self.assertFalse((release_root / "web" / "railway.toml").exists())

    def test_uses_one_canonical_release_validation_report(self):
        release_root = ROOT if (ROOT / "VALIDATION_REPORT.md").exists() else REPO
        reports = [path for path in release_root.rglob("VALIDATION_REPORT.md") if path.is_file()]
        self.assertEqual(reports, [release_root / "VALIDATION_REPORT.md"])



if __name__ == "__main__":
    unittest.main()

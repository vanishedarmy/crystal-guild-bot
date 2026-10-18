import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PackageCleanupTests(unittest.TestCase):
 def test_compact_release_docs_exist(self):
  for name in ('README.md','CHANGELOG.md','RELEASE_NOTES.md','UPGRADE_GUIDE.md','VALIDATION_REPORT.md','PACKAGE_MANIFEST.txt'):
   self.assertTrue((ROOT/name).is_file(),name)
  self.assertIn('1.9.7', (ROOT/'README.md').read_text())
  self.assertIn('39', (ROOT/'PORTAL_ACTIONS_SETUP.md').read_text())
 def test_historical_hotfix_docs_are_not_shipped(self):
  self.assertFalse((ROOT/'MERC_SERVICE_HOTFIX3.md').exists())
  self.assertFalse((ROOT/'FINALIZATION_AUDIT.md').exists())

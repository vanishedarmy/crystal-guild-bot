from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class ItemUsageCopyHotfix2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "item-copy-hotfix.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_capped_field_heal_uses_plain_restored_amount(self):
        self.game._max_hp = lambda _player: 5000
        self.db.execute("UPDATE players SET current_hp=4941 WHERE twitch_id='1'")
        self.game._change_item("1", "mega_potion", 1, "copy_hotfix")
        result = self.game.use_item("1", "mega_potion")
        self.assertTrue(result.ok)
        text = result.messages[0]
        self.assertIn("restores 59 HP", text)
        self.assertNotIn("potency", text.lower())
        self.assertNotIn("capped", text.lower())
        self.assertNotIn("HP 5000/5000", text)


if __name__ == "__main__":
    unittest.main()

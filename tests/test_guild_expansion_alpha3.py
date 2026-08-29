from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class GuildExpansionAlpha3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0, overlay_state_path=str(Path(self.tmp.name) / "overlay.json"), rng=random.Random(51))
        self.game.recruit("1", "van", "Van")
        self.game.fellowship_system.ensure_member("1")
        self.db.execute("UPDATE fellowship_state SET level=8,renown=27000 WHERE singleton_id=1")

    def tearDown(self) -> None:
        self.db.close(); self.tmp.cleanup()

    def set_facility(self, facility_id: str, level: int) -> None:
        self.db.execute("UPDATE fellowship_facilities SET tier=? WHERE facility_id=?", (level, facility_id))

    def test_services_scale_without_combat_stat_power(self):
        self.set_facility("chocobo_stable", 3)
        self.set_facility("archives", 3)
        effects = self.game.fellowship_system.effects()
        self.assertAlmostEqual(effects["chocobo_xp_bonus"], 0.15)
        self.assertAlmostEqual(effects["archive_rare_event_bonus"], 0.01)
        self.assertEqual(self.game.fellowship_system.effective_chocobo_xp(100), 115)
        self.assertAlmostEqual(self.game.fellowship_system.archive_rare_event_bonus(), 0.01)

    def test_workshop_level_two_refines_materials_with_fee(self):
        self.set_facility("workshop", 2)
        self.db.execute("UPDATE players SET gil=5000 WHERE twitch_id='1'")
        self.db.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES ('1','iron_ore',10) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=10")
        ok, message = self.game.fellowship_system.workshop_exchange("1", "refine_mythril", 2)
        self.assertTrue(ok, message)
        self.assertEqual(int(self.db.one("SELECT quantity FROM inventory WHERE player_id='1' AND item_id='iron_ore'")["quantity"]), 0)
        self.assertEqual(int(self.db.one("SELECT quantity FROM inventory WHERE player_id='1' AND item_id='mythril_ore'")["quantity"]), 2)
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]), 4500)

    def test_advanced_refining_requires_workshop_three(self):
        self.set_facility("workshop", 2)
        ok, message = self.game.fellowship_system.workshop_exchange("1", "press_adamantite", 1)
        self.assertFalse(ok)
        self.assertIn("Workshop Lv.3", message)

    def test_portal_refining_is_replay_safe(self):
        self.set_facility("workshop", 2)
        self.db.execute("UPDATE players SET gil=5000 WHERE twitch_id='1'")
        self.db.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES ('1','iron_ore',5) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=5")
        first = self.game.portal_workshop_exchange("1", "refine_mythril", 1, "alpha3:refine:1")
        second = self.game.portal_workshop_exchange("1", "refine_mythril", 1, "alpha3:refine:1")
        self.assertTrue(first.ok); self.assertTrue(second.ok)
        self.assertEqual(int(self.db.one("SELECT quantity FROM inventory WHERE player_id='1' AND item_id='mythril_ore'")["quantity"]), 1)
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]), 4750)

    def test_fellowship_state_exposes_workshop_services_and_protocol_21(self):
        self.set_facility("workshop", 3)
        state = self.game.portal_fellowship_state("1")
        self.assertTrue(state.ok)
        workshop = state.data["fellowship_state"]["services"]["workshop"]
        self.assertEqual(workshop["level"], 3)
        self.assertEqual(len([x for x in workshop["exchanges"] if x["unlocked"]]), 4)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 21)


if __name__ == "__main__":
    unittest.main()

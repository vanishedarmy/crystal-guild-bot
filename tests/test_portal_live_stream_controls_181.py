from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class PortalLiveStreamControls181Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "live-controls.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            venture_treasure_chance=0.0,
            encounter_join_seconds=90,
            encounter_round_seconds=60,
            raid_join_seconds=90,
            raid_round_seconds=60,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(1813),
        )
        for pid, login, name, job in (
            ("1", "van", "Van", "warrior"),
            ("2", "mira", "Mira", "whitemage"),
        ):
            self.game.recruit(pid, login, name)
            self.game.choose_job(pid, job)
            self.db.execute("UPDATE players SET level=45 WHERE twitch_id=?", (pid,))
            self.game.choose_job(pid, job)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_stream_venture_portal_join_and_round_actions_share_authoritative_battle(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok, opened.messages)
        encounter_id = str(opened.data["encounter_id"])

        before = self.game._portal_adventure_state_data("2", stream_live=True)
        self.assertTrue(before["encounter"]["can_join"])
        self.assertFalse(before["encounter"]["you_joined"])

        joined = self.game.portal_live_event_join("2", "venture", encounter_id, "portal-live-join-1", stream_live=True)
        self.assertTrue(joined.ok, joined.messages)
        self.assertTrue(joined.data["adventure_state"]["encounter"]["you_joined"])

        self.assertTrue(self.game.start_encounter_battle(int(encounter_id)).ok)
        combat = self.game._portal_adventure_state_data("2", stream_live=True)["encounter"]
        self.assertTrue(combat["web_combat_controls"])
        controls = combat["controls"]
        self.assertEqual(controls["event"], "venture")
        self.assertEqual(controls["event_id"], encounter_id)
        self.assertEqual(controls["round"], 1)
        self.assertTrue(any(row["id"] for row in controls["abilities"]))

        queued = self.game.portal_live_event_action("2", "venture", encounter_id, 1, "defend", "", "", "portal-live-action-1", stream_live=True)
        self.assertTrue(queued.ok, queued.messages)
        self.assertEqual(self.game.encounter_roster["2"]["action"]["kind"], "defend")
        self.assertEqual(queued.data["adventure_state"]["encounter"]["controls"]["queued_action"], "Defend")

        stale = self.game.portal_live_event_action("2", "venture", encounter_id, 2, "attack", "", "", "portal-live-stale-1", stream_live=True)
        self.assertFalse(stale.ok)
        self.assertTrue(stale.data.get("stale_live_event"))

    def test_live_controls_expose_owned_items_and_portal_item_targets_use_usernames(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        encounter_id = str(opened.data["encounter_id"])
        self.assertTrue(self.game.portal_live_event_join("2", "venture", encounter_id, "portal-live-join-item", stream_live=True).ok)
        self.assertTrue(self.game.start_encounter_battle(int(encounter_id)).ok)
        before_qty = self.game._inventory_qty("2", "potion")
        self.game._change_item("2", "potion", 2, "test")
        self.game.encounter_roster["1"]["hp"] = max(1, self.game.encounter_roster["1"]["max_hp"] // 2)

        state = self.game._portal_adventure_state_data("2", stream_live=True)
        items = state["encounter"]["controls"]["items"]
        potion = next(row for row in items if row["id"] == "potion")
        self.assertEqual(potion["category"], "healing")
        self.assertEqual(potion["quantity"], before_qty + 2)

        used = self.game.portal_live_event_action("2", "venture", encounter_id, 1, "item", "potion", "van", "portal-live-item-1", stream_live=True)
        self.assertTrue(used.ok, used.messages)
        action = self.game.encounter_roster["2"]["action"]
        self.assertEqual(action["kind"], "item")
        self.assertEqual(action["item_id"], "potion")
        self.assertEqual(action["target_id"], "1")

    def test_live_portal_commands_are_stream_gated(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        encounter_id = str(opened.data["encounter_id"])
        denied = self.game.portal_live_event_join("2", "venture", encounter_id, "portal-live-offline", stream_live=False)
        self.assertFalse(denied.ok)
        self.assertIn("LIVE", denied.messages[0])
        self.assertFalse(denied.data["adventure_state"]["stream_live"])

    def test_raid_portal_join_and_combat_action(self):
        self.assertTrue(self.game.spawn_boss("goblin_king").ok)
        raid_id = self.game._raid_instance_id(self.game.active_boss)
        state = self.game._portal_adventure_state_data("1", stream_live=True)
        self.assertEqual(state["raid"]["event_id"], raid_id)
        self.assertTrue(state["raid"]["can_join"])

        self.assertTrue(self.game.portal_live_event_join("1", "raid", raid_id, "portal-raid-join-1", stream_live=True).ok)
        self.assertTrue(self.game.portal_live_event_join("2", "raid", raid_id, "portal-raid-join-2", stream_live=True).ok)
        self.assertTrue(self.game.start_raid().ok)

        combat = self.game._portal_adventure_state_data("1", stream_live=True)["raid"]
        self.assertTrue(combat["you_joined"])
        self.assertTrue(combat["web_combat_controls"])
        self.assertEqual(combat["controls"]["round"], 1)
        queued = self.game.portal_live_event_action("1", "raid", raid_id, 1, "attack", "", "", "portal-raid-action-1", stream_live=True)
        self.assertTrue(queued.ok, queued.messages)
        self.assertEqual(self.game.raid_roster["1"]["action"]["kind"], "attack")
        self.assertEqual(queued.data["adventure_state"]["raid"]["controls"]["queued_action"], "Attack")


if __name__ == "__main__":
    unittest.main()

"""Raid Command overlay: streamed data must be up to date and contain no account identifiers."""
import json
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_sync import PortalSyncClient

ROOT = Path(__file__).resolve().parents[1]

class RaidOverlay1944Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.overlay = Path(self.tmp.name) / "overlay.json"
        self.db = Database(Path(self.tmp.name) / "game.db")
        self.engine = CrystalGuildEngine(
            self.db, GameData(ROOT / "data"), overlay_state_path=str(self.overlay),
            raid_join_seconds=90, raid_round_seconds=60, rng=random.Random(1944))
        for identity, name, job in (("1", "Van", "warrior"), ("2", "Mira", "whitemage")):
            self.assertTrue(self.engine.recruit(identity, name.lower(), name).ok)
            self.assertTrue(self.engine.choose_job(identity, job).ok)
            self.db.execute("UPDATE players SET level=70 WHERE twitch_id=?", (identity,))
            self.assertTrue(self.engine.choose_job(identity, job).ok)
        self.assertTrue(self.engine.spawn_boss("ifrit").ok)
        self.assertTrue(self.engine.raid_join("1").ok)
        self.assertTrue(self.engine.raid_join("2").ok)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_rally_roster_public_names_and_no_private_ids(self):
        payload = self.engine._overlay_payload()
        self.assertEqual(payload["raiders"], 2)
        self.assertEqual([m["name"] for m in payload["members"]], ["Van", "Mira"])
        self.assertEqual(payload["members"][0]["state"], "JOINED")
        self.assertGreater(payload["rally_closes_at"], 0)
        for forbidden in ("target_id", "twitch_id", "raid_instance_id", "raid_run", "ability_id"):
            self.assertNotIn(forbidden, json.dumps(payload))

    def test_combat_action_appears_in_overlay_file_immediately(self):
        self.assertTrue(self.engine.start_raid().ok)
        self.assertTrue(self.engine.battle_attack("1").ok)
        persisted = json.loads(self.overlay.read_text())
        actor = next(member for member in persisted["members"] if member["name"] == "Van")
        self.assertEqual(actor["state"], "READY")
        self.assertEqual(actor["action"], "Attack")
        self.assertEqual(actor["action_kind"], "attack")
        self.assertEqual(persisted["ready_actions"], 1)
        self.assertEqual(persisted["actionable_raiders"], 2)
        self.assertFalse(any("id" in member for member in persisted["members"]))

    def test_effect_icons_and_portal_projection(self):
        self.assertTrue(self.engine.start_raid().ok)
        self.engine.raid_roster["1"]["statuses"]["protect"] = {"turns": 3, "magnitude": 0.4}
        self.engine.active_boss["statuses"]["vulnerable"] = {"turns": 2, "magnitude": 0.25}
        self.engine._update_raid_overlay()
        client = PortalSyncClient(object(), "https://example.invalid", "secret", overlay_state_path=self.overlay)
        result = client.build_overlay_snapshot()
        members = result["overlay"]["members"]
        self.assertEqual(members[0]["statuses"], [{"id": "protect", "turns": 3}])
        self.assertEqual(result["overlay"]["boss_statuses"], [{"id": "vulnerable", "turns": 2}])
        encoded = json.dumps(result)
        for forbidden in ("raid_run", "target_id", "ability_id", "twitch_id", "magnitude"):
            self.assertNotIn(forbidden, encoded)

if __name__ == "__main__": unittest.main()

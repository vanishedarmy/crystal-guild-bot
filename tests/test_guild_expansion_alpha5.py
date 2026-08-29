from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.fellowship import LEGACY_ACCOMPLISHMENTS
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class GuildExpansionAlpha5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(81),
        )
        self.game.recruit("1", "van", "Van")
        self.game.fellowship_system.ensure_member("1")
        self.db.execute("UPDATE fellowship_members SET founding_member=1 WHERE player_id='1'")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_alpha5_keeps_schema9_and_protocol21(self):
        self.assertEqual(self.db.schema_version(), 9)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 21)
        self.assertEqual(len(LEGACY_ACCOMPLISHMENTS), 10)

    def test_retroactive_legacy_reward_is_granted_once(self):
        # Five established major facilities satisfy Foundations Laid.
        for facility_id in ("guild_hall", "workshop", "chocobo_stable", "archives", "airship_dock"):
            self.db.execute("UPDATE fellowship_facilities SET tier=1 WHERE facility_id=?", (facility_id,))
        before = int(self.db.one("SELECT renown FROM fellowship_state WHERE singleton_id=1")["renown"])
        notes = self.game.fellowship_system._settle_legacy_accomplishments()
        self.assertTrue(any("Foundations Laid" in note for note in notes), notes)
        after = int(self.db.one("SELECT renown FROM fellowship_state WHERE singleton_id=1")["renown"])
        self.assertEqual(after, before + 300)
        self.assertEqual(self.game.fellowship_system._settle_legacy_accomplishments(), [])
        self.assertEqual(int(self.db.one("SELECT renown FROM fellowship_state WHERE singleton_id=1")["renown"]), after)

    def test_legacy_snapshot_tracks_airship_and_stage(self):
        self.db.execute("UPDATE fellowship_airship_state SET built=1,missions_completed=25 WHERE singleton_id=1")
        for upgrade_id in ("hull", "engine", "cargo", "survey", "crystal_core"):
            self.db.execute("UPDATE fellowship_airship_upgrades SET tier=3 WHERE upgrade_id=?", (upgrade_id,))
        self.game.fellowship_system._settle_legacy_accomplishments()
        legacy = self.game.fellowship_system.legacy_snapshot()
        completed = {item["id"] for item in legacy["accomplishments"] if item["complete"]}
        self.assertIn("skybound_company", completed)
        self.assertIn("veteran_crew", completed)
        self.assertIn("master_shipwrights", completed)
        self.assertGreaterEqual(legacy["stage"], 2)
        self.assertIn("Airship Commission Plaque", legacy["decorations"])

    def test_personal_service_record_and_distinctions(self):
        self.db.execute("UPDATE fellowship_members SET projects_contributed=5,gil_donated=100000,orders_participated=10,deeds_assisted=5 WHERE player_id='1'")
        for i in range(25):
            self.game.fellowship_system.record_activity("1", "expedition_complete", event_key=f"a5:exp:{i}", renown=0)
        self.db.execute("INSERT INTO fellowship_airship_mission_members(run_id,player_id,contribution) VALUES ('r1','1',1)")
        self.db.execute("INSERT INTO fellowship_airship_mission_members(run_id,player_id,contribution) VALUES ('r2','1',1)")
        self.db.execute("INSERT INTO fellowship_airship_mission_members(run_id,player_id,contribution) VALUES ('r3','1',1)")
        self.db.execute("INSERT INTO fellowship_airship_mission_members(run_id,player_id,contribution) VALUES ('r4','1',1)")
        self.db.execute("INSERT INTO fellowship_airship_mission_members(run_id,player_id,contribution) VALUES ('r5','1',1)")
        member = self.game.fellowship_system.member_snapshot("1")
        self.assertEqual(member["service_record"]["expeditions_completed"], 25)
        self.assertEqual(member["service_record"]["airship_missions_supported"], 5)
        for distinction in ("Founding Member", "Guild Builder", "Guild Benefactor", "Order Veteran", "Deedkeeper", "Airship Crew", "Frontier Pathfinder"):
            self.assertIn(distinction, member["distinctions"])

    def test_public_snapshot_exposes_legacy(self):
        snapshot = self.game.fellowship_system.public_snapshot()
        self.assertIn("legacy", snapshot)
        self.assertEqual(snapshot["legacy"]["total"], 10)
        self.assertEqual(snapshot["legacy"]["stage_name"], "Founding Hall")

    def test_legacy_chat_command_is_player_facing(self):
        result = self.game.fellowship_legacy()
        self.assertTrue(result.ok)
        self.assertIn("GUILD LEGACY", result.messages[0])
        self.assertTrue(any("Next:" in message or "complete" in message.lower() for message in result.messages[1:]))


if __name__ == "__main__":
    unittest.main()

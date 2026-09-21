from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class TaskCompletionHardeningHotfix5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(57),
        )
        self.game.recruit("1", "progress", "Progress")
        self.assertTrue(self.game.choose_job("1", "warrior").ok)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def _prime_project_except_activity(self, project_id: str, activity_key: str, current: int) -> None:
        self.db.execute(
            "UPDATE fellowship_state SET level=10,renown=50000,active_project_id=? WHERE singleton_id=1",
            (project_id,),
        )
        project = self.game.fellowship_system.project_snapshot(project_id)
        self.assertIsNotNone(project)
        for req in project["requirements"]:
            if req["kind"] == "level":
                continue
            value = current if req["key"] == activity_key else int(req["target"])
            self.db.execute(
                "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES (?,?,?) "
                "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=excluded.current",
                (project_id, req["key"], value),
            )

    def test_monster_and_combat_semantics_match_player_facing_labels(self):
        semantics = self.game.fellowship_system._activity_semantics
        for source in ("encounter_win", "hunt_win", "monster_victory"):
            self.assertIn("monster_victory", semantics(source), source)
            self.assertIn("combat_victory", semantics(source), source)
        self.assertIn("combat_victory", semantics("raid_win"))
        self.assertNotIn("monster_victory", semantics("raid_win"))
        self.assertEqual(semantics("venture_complete"), {"venture_complete"})

    def test_archive_building_completes_from_non_hunt_monster_victory(self):
        project_id = "archives_t1"
        key = "activity:monster_victory"
        self._prime_project_except_activity(project_id, key, 19)
        notes = self.game.fellowship_system.record_activity(
            "1", "monster_victory", renown=0, event_key="dungeon-monster-victory:test"
        )
        tier = self.db.one("SELECT tier FROM fellowship_facilities WHERE facility_id='archives'")
        state = self.db.one("SELECT active_project_id FROM fellowship_state WHERE singleton_id=1")
        self.assertEqual(int(tier["tier"]), 1)
        self.assertIsNone(state["active_project_id"])
        self.assertTrue(any("PROJECT COMPLETE" in note for note in notes))

    def test_raid_victory_counts_for_combat_building_but_not_monster_building(self):
        self._prime_project_except_activity("training_hall_t1", "activity:combat_victory", 19)
        notes = self.game.fellowship_system.record_activity(
            "1", "raid_win", renown=0, event_key="raid-combat-victory:test"
        )
        tier = self.db.one("SELECT tier FROM fellowship_facilities WHERE facility_id='training_hall'")
        self.assertEqual(int(tier["tier"]), 1)
        self.assertTrue(any("PROJECT COMPLETE" in note for note in notes))

        # A Raid boss clear is a combat victory, but it is not a Bestiary monster
        # defeat and therefore must not satisfy the Archive's monster requirement.
        self.db.execute("UPDATE fellowship_facilities SET tier=0 WHERE facility_id='archives'")
        self._prime_project_except_activity("archives_t1", "activity:monster_victory", 19)
        self.game.fellowship_system.record_activity(
            "1", "raid_win", renown=0, event_key="raid-not-monster:test"
        )
        snap = self.game.fellowship_system.project_snapshot("archives_t1")
        req = next(row for row in snap["requirements"] if row["key"] == "activity:monster_victory")
        self.assertEqual(req["current"], 19)

    def test_solo_venture_monster_kill_emits_canonical_monster_victory(self):
        # Force a combat stage, then make the enemy a one-hit finish. The kill
        # must create the canonical Fellowship event even though it was not a Hunt.
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0):
            started = self.game.solo_venture("1", bypass_cooldown=True)
        self.assertTrue(started.ok, started.messages)
        state = self.game._solo_expedition_load("1")
        self.assertIsNotNone(state)
        self.assertEqual(state["status"], "combat")
        state["combat"]["encounter"]["monster_hp"] = 1
        self.game._solo_expedition_save("1", state)
        with patch.object(self.game, "_solo_resolve_enemy_intent", return_value=None):
            result = self.game.solo_expedition_action("1", "attack")
        self.assertTrue(result.ok, result.messages)
        event = self.db.one(
            "SELECT activity FROM fellowship_events WHERE player_id='1' AND event_key LIKE 'monster_victory:solo_venture:1:%'"
        )
        self.assertIsNotNone(event)
        self.assertEqual(str(event["activity"]), "monster_victory")

    def test_airship_aliases_use_strongest_weight_without_double_counting(self):
        self.db.execute("UPDATE fellowship_airship_state SET built=1 WHERE singleton_id=1")
        ok, message, active = self.game.fellowship_system.start_airship_mission("monster suppression")
        self.assertTrue(ok, message)
        self.assertEqual(active["id"], "monster_suppression")
        self.game.fellowship_system.record_activity(
            "1", "hunt_win", renown=0, event_key="suppression-hunt:test"
        )
        row = self.db.one("SELECT progress FROM fellowship_airship_state WHERE singleton_id=1")
        # Hunt wins are worth 2 for this mission. The combat-victory alias must
        # not stack a second +1 on top of the Hunt-specific weight.
        self.assertEqual(int(row["progress"]), 2)

    def test_replayed_canonical_monster_receipt_does_not_double_progress(self):
        self.db.execute(
            "UPDATE fellowship_state SET level=10,renown=50000,active_project_id='archives_t1' WHERE singleton_id=1"
        )
        self.db.execute(
            "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES ('archives_t1','activity:monster_victory',0) "
            "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=0"
        )
        self.game.fellowship_system.record_activity(
            "1", "monster_victory", renown=0, event_key="canonical-monster:once"
        )
        self.game.fellowship_system.record_activity(
            "1", "monster_victory", renown=0, event_key="canonical-monster:once"
        )
        row = self.db.one(
            "SELECT current FROM fellowship_project_progress WHERE project_id='archives_t1' AND requirement_key='activity:monster_victory'"
        )
        self.assertEqual(int(row["current"]), 1)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import random
import sqlite3
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class WayfarerSoloVentureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "wayfarer.db"
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(115),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET level=20 WHERE twitch_id='1'")
        p = self.game._player("1")
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='1'", (self.game._max_hp(p),))

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def begin_encounter(self):
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0):
            result = self.game.solo_venture("1", bypass_cooldown=True)
        self.assertTrue(result.ok, result.messages)
        state = self.game._solo_expedition_load("1")
        self.assertIsNotNone(state)
        self.assertEqual(state["status"], "combat")
        return state

    def keep_monster_alive(self, state, hp: int = 99999):
        state["combat"]["encounter"]["monster_hp"] = hp
        state["combat"]["encounter"]["monster_max_hp"] = hp
        self.game._solo_expedition_save("1", state)
        return state

    def test_schema_five_persists_solo_runs_and_migrates_schema_four_with_backup(self):
        self.assertEqual(self.db.schema_version(), 16)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='solo_expeditions'"))
        self.db.close()

        conn = sqlite3.connect(self.path)
        conn.execute("DROP TABLE solo_expeditions")
        conn.execute("DELETE FROM schema_migrations WHERE version=5")
        conn.commit()
        conn.close()

        migrated = Database(self.path)
        try:
            self.assertEqual(migrated.schema_version(), 16)
            self.assertIsNotNone(migrated.one("SELECT name FROM sqlite_master WHERE type='table' AND name='solo_expeditions'"))
            self.assertIsNotNone(migrated.pre_migration_backup_path)
            self.assertIn("pre_schema_5", Path(migrated.pre_migration_backup_path).name)
            verify = sqlite3.connect(migrated.pre_migration_backup_path)
            try:
                self.assertEqual(verify.execute("PRAGMA quick_check").fetchone()[0], "ok")
                self.assertIsNone(verify.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='solo_expeditions'").fetchone())
                self.assertIsNotNone(verify.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player_chocobos'").fetchone())
            finally:
                verify.close()
        finally:
            migrated.close()
        # tearDown expects a live handle; replace it with a harmless in-memory DB.
        self.db = Database(":memory:")

    def test_encounter_is_persistent_player_paced_and_does_not_occupy_global_battle(self):
        state = self.begin_encounter()
        public = self.game._solo_expedition_public("1")
        self.assertEqual(public["stage"], 1)
        self.assertEqual(public["status"], "combat")
        self.assertTrue(public["combat"]["enemy"]["intent"])
        self.assertEqual(public["combat"]["round"], 1)
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})

        self.keep_monster_alive(state)
        with patch.object(self.game, "_solo_resolve_enemy_intent", return_value=None):
            result = self.game.solo_expedition_action("1", "attack")
        self.assertTrue(result.ok, result.messages)
        after = self.game._solo_expedition_load("1")
        self.assertEqual(after["combat"]["encounter"]["round"], 2)
        self.assertEqual(after["last_round"]["round"], 1)

        # A fresh engine instance sees the same waiting round from SQLite.
        resumed = CrystalGuildEngine(
            self.db,
            self.game.data,
            overlay_state_path=str(Path(self.tmp.name) / "overlay-resume.json"),
            rng=random.Random(116),
        )
        resumed_public = resumed._solo_expedition_public("1")
        self.assertEqual(resumed_public["combat"]["round"], 2)
        self.assertEqual(resumed_public["stage"], 1)

    def test_solo_round_temporarily_borrows_combat_helpers_without_touching_live_global_state(self):
        state = self.keep_monster_alive(self.begin_encounter())
        monster_id = next(iter(self.game.data.monsters))
        global_encounter = {"id": 999, "kind": "venture", "state": "rally", "monster_id": monster_id}
        global_roster = {"999": {"name": "Other Hero", "username": "other", "job_id": "warrior"}}
        self.game.active_encounter = deepcopy(global_encounter)
        self.game.encounter_roster = deepcopy(global_roster)
        with patch.object(self.game, "_solo_resolve_enemy_intent", return_value=None):
            result = self.game.solo_expedition_action("1", "attack")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_encounter, global_encounter)
        self.assertEqual(self.game.encounter_roster, global_roster)

    def test_ability_spends_persistent_resource_and_defend_restores_resource(self):
        self.game._solo_expedition_delete("1")
        self.db.execute("DELETE FROM cooldowns WHERE player_id='1' AND action='solo_venture'")
        self.game.choose_job("1", "blackmage")
        state = self.keep_monster_alive(self.begin_encounter())
        before_mp = int(state["combat"]["roster"]["1"]["mp"])
        ability = next(row for row in self.game.data.active_abilities["blackmage"] if row["level"] <= 1)
        with patch.object(self.game, "_solo_resolve_enemy_intent", return_value=None):
            cast = self.game.solo_expedition_action("1", f"ability:{ability['id']}")
        self.assertTrue(cast.ok, cast.messages)
        persisted_mp = int(self.game._player("1")["current_mp"])
        self.assertLess(persisted_mp, before_mp)

        # Defend returns a little MP and still advances exactly one round.
        current = self.game._solo_expedition_load("1")
        current["combat"]["roster"]["1"]["mp"] = 0
        self.db.execute("UPDATE players SET current_mp=0 WHERE twitch_id='1'")
        self.game._solo_expedition_save("1", current)
        with patch.object(self.game, "_solo_resolve_enemy_intent", return_value=None):
            defended = self.game.solo_expedition_action("1", "defend")
        self.assertTrue(defended.ok, defended.messages)
        after = self.game._solo_expedition_load("1")
        self.assertGreater(int(after["combat"]["roster"]["1"]["mp"]), 0)

    def test_battle_item_consumes_only_through_solo_action_and_field_use_is_locked(self):
        state = self.keep_monster_alive(self.begin_encounter())
        self.game._change_item("1", "potion", 2, "test")
        meta = state["combat"]["roster"]["1"]
        meta["hp"] = max(1, int(meta["max_hp"]) // 2)
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='1'", (meta["hp"],))
        self.game._solo_expedition_save("1", state)
        before = self.game._inventory_qty("1", "potion")
        self.assertFalse(self.game.use_item("1", "potion").ok)
        self.assertEqual(self.game._inventory_qty("1", "potion"), before)
        with patch.object(self.game, "_solo_resolve_enemy_intent", return_value=None):
            used = self.game.solo_expedition_action("1", "item:potion")
        self.assertTrue(used.ok, used.messages)
        self.assertEqual(self.game._inventory_qty("1", "potion"), before - 1)

    def test_three_treasure_stages_bank_only_at_return_or_final_depth(self):
        before_items = sum(int(row["quantity"]) for row in self.db.all("SELECT quantity FROM inventory WHERE player_id='1'"))
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 1.0):
            first = self.game.solo_venture("1", bypass_cooldown=True)
            self.assertTrue(first.ok)
            stage1 = self.game._solo_expedition_public("1")
            self.assertEqual(stage1["status"], "choice")
            self.assertEqual(stage1["stage_bonus_percent"], 0)
            self.assertEqual(sum(int(row["quantity"]) for row in self.db.all("SELECT quantity FROM inventory WHERE player_id='1'")), before_items)

            second = self.game.solo_expedition_continue("1")
            self.assertTrue(second.ok)
            stage2 = self.game._solo_expedition_public("1")
            self.assertEqual(stage2["stage"], 2)
            self.assertEqual(stage2["stage_bonus_percent"], 15)
            self.assertEqual(len(stage2["spoils"]["items"]), 2)

            third = self.game.solo_expedition_continue("1")
            self.assertTrue(third.ok)
        self.assertIsNone(self.game._solo_expedition_load("1"))
        after_items = sum(int(row["quantity"]) for row in self.db.all("SELECT quantity FROM inventory WHERE player_id='1'"))
        self.assertEqual(after_items, before_items + 3)
        summary = third.data["solo_result"]
        self.assertEqual(summary["outcome"], "complete")
        self.assertEqual(summary["stages"], 3)
        event = self.db.one("SELECT renown FROM fellowship_events WHERE event_key LIKE 'solo_expedition:1:%'")
        self.assertEqual(int(event["renown"]), 6)

    def test_return_banks_stage_one_spoils_and_releases_activity_locks(self):
        self.db.execute("UPDATE players SET gil=999999 WHERE twitch_id='1'")
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 1.0):
            self.assertTrue(self.game.solo_venture("1", bypass_cooldown=True).ok)
        blocked = self.game.set_stance("1", "defensive")
        self.assertFalse(blocked.ok)
        self.assertIn("Solo Venture", " ".join(blocked.messages))
        self.assertFalse(self.game.daily("1").ok)
        self.assertFalse(self.game._portal_daily_state_data("1")["available"])
        self.assertIn("Solo Venture", self.game._portal_daily_state_data("1")["blocked_reason"])
        result = self.game.solo_expedition_return("1")
        self.assertTrue(result.ok, result.messages)
        self.assertIsNone(self.game._solo_expedition_load("1"))
        self.assertTrue(self.game.set_stance("1", "defensive").ok)

    def test_defeat_keeps_secured_progress_recovers_half_gil_and_loses_loose_items(self):
        state = self.begin_encounter()
        state["combat"]["encounter"]["monster_hp"] = 1
        self.game._solo_expedition_save("1", state)
        with patch.object(self.game, "_solo_resolve_enemy_intent", return_value=None):
            win = self.game.solo_expedition_action("1", "attack")
        self.assertTrue(win.ok)
        cleared = self.game._solo_expedition_load("1")
        secured_xp = int(self.game._player("1")["xp"])
        pending_gil = int(cleared["spoils"]["gil"])
        self.assertGreater(pending_gil, 0)

        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0):
            self.assertTrue(self.game.solo_expedition_continue("1").ok)
        stage2 = self.game._solo_expedition_load("1")
        stage2["combat"]["encounter"]["monster_hp"] = 99999
        stage2["combat"]["encounter"]["monster_max_hp"] = 99999
        stage2["combat"]["roster"]["1"]["hp"] = 1
        stage2["spoils"]["items"].append({"id": "potion", "name": "Potion", "quantity": 1, "kind": "drop"})
        self.game._solo_expedition_save("1", stage2)
        before_gil = int(self.game._player("1")["gil"])
        before_potion = self.game._inventory_qty("1", "potion")

        def knock_out(_monster, _encounter, log):
            self.game.encounter_roster["1"]["hp"] = 0
            log.append("The enemy finishes the fight.")

        with patch.object(self.game, "_solo_resolve_enemy_intent", side_effect=knock_out):
            lost = self.game.solo_expedition_action("1", "attack")
        self.assertTrue(lost.ok)
        self.assertIsNone(self.game._solo_expedition_load("1"))
        self.assertEqual(int(self.game._player("1")["xp"]), secured_xp)
        self.assertEqual(int(self.game._player("1")["gil"]), before_gil + int(pending_gil * 0.5))
        self.assertEqual(self.game._inventory_qty("1", "potion"), before_potion)
        self.assertEqual(lost.data["solo_result"]["lost_spoils"]["items"], ["Potion"])

    def test_round_safety_limit_ends_run_without_counting_a_character_death(self):
        state = self.keep_monster_alive(self.begin_encounter())
        encounter = state["combat"]["encounter"]
        encounter["round"] = int(encounter.get("max_rounds", 12))
        self.game._solo_expedition_save("1", state)
        before_deaths = int(self.game._player("1")["deaths"])
        with patch.object(self.game, "_solo_resolve_enemy_intent", return_value=None):
            result = self.game.solo_expedition_action("1", "attack")
        self.assertTrue(result.ok)
        self.assertEqual(int(self.game._player("1")["deaths"]), before_deaths)
        self.assertGreater(int(self.game._player("1")["current_hp"]), 0)

    def test_retreat_preserves_secured_progress_but_abandons_pending_spoils(self):
        state = self.begin_encounter()
        state["secured"] = {"xp": 123, "jp": 45}
        state["spoils"] = {"gil": 777, "items": [{"id": "potion", "name": "Potion", "quantity": 2}]}
        self.game._solo_expedition_save("1", state)
        before_gil = int(self.game._player("1")["gil"])
        before_potion = self.game._inventory_qty("1", "potion")
        result = self.game.solo_expedition_retreat("1")
        self.assertTrue(result.ok)
        self.assertEqual(int(self.game._player("1")["gil"]), before_gil)
        self.assertEqual(self.game._inventory_qty("1", "potion"), before_potion)
        self.assertEqual(result.data["solo_result"]["rewards"]["xp"], 123)
        self.assertEqual(result.data["solo_result"]["lost_spoils"]["gil"], 777)
        self.assertIsNone(self.game._solo_expedition_load("1"))


if __name__ == "__main__":
    unittest.main()

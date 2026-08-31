from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.expeditions import ROUTES, defeat_cache_keep, effective_travel_seconds, resource_yield_bonus
from crystal_guild.chocobo import expedition_specialization, total_xp_floor_for_level

ROOT = Path(__file__).resolve().parents[1]


class ExpeditionV12Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db, self.data,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(120),
        )
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='100'")
        p = self.game._player("100")
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='100'", (self.game._max_hp(p),))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def unlock(self, *traits: str):
        self.db.execute("UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1")
        self.db.execute(
            "INSERT INTO player_chocobos(player_id,name,registered_at) VALUES ('100','Biscuit',CURRENT_TIMESTAMP) "
            "ON CONFLICT(player_id) DO UPDATE SET name='Biscuit',registered_at=CURRENT_TIMESTAMP"
        )
        for trait in traits:
            self.db.execute(
                "INSERT OR IGNORE INTO player_chocobo_traits(player_id,trait_id) VALUES ('100',?)", (trait,)
            )

    def test_schema_and_five_regions_are_present(self):
        self.assertEqual(self.db.schema_version(), 12)
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_expeditions'"))
        self.assertIsNotNone(self.db.one("SELECT name FROM sqlite_master WHERE type='table' AND name='player_region_exploration'"))
        self.assertEqual(len(self.data.expedition_regions), 5)
        self.assertEqual(
            set(self.data.expedition_regions),
            {"emerald_wilds", "ashen_highlands", "mistfen_marshes", "frostveil_reach", "astral_scar"},
        )

    def test_launch_requires_board_and_registered_chocobo(self):
        result = self.game.expedition_start("100", "emerald_wilds", "scout")
        self.assertFalse(result.ok)
        self.assertIn("Expedition Board", " ".join(result.messages))
        self.db.execute("UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1")
        result = self.game.expedition_start("100", "emerald_wilds", "scout")
        self.assertFalse(result.ok)
        self.assertIn("registered Chocobo", " ".join(result.messages))
        self.unlock("fleet_feet")
        result = self.game.expedition_start("100", "emerald_wilds", "scout")
        self.assertTrue(result.ok, result.messages)
        state = self.game._expedition_load("100")
        self.assertEqual(state["status"], "travel")
        self.assertEqual(state["base_stages"], 3)
        self.assertEqual(state["max_stages"], 5)

    def test_fleet_feet_reduces_travel_and_run_persists(self):
        self.unlock("fleet_feet")
        self.assertEqual(effective_travel_seconds(240, {"fleet_feet"}), 204)
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        state = self.game._expedition_load("100")
        self.assertIsNotNone(state)
        self.assertEqual(int(state["travel_ready_at"]) - int(state["updated_at"]), 204)
        raw = self.db.one("SELECT state_json FROM player_expeditions WHERE player_id='100'")
        self.assertEqual(json.loads(raw["state_json"])["region_id"], "emerald_wilds")

    def test_stage_cannot_resolve_before_authoritative_timer(self):
        self.unlock()
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        result = self.game.expedition_resolve_stage("100")
        self.assertFalse(result.ok)
        self.assertIn("Travel completes", " ".join(result.messages))

    def test_resource_stage_progress_cache_and_safe_return(self):
        self.unlock("forager")
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        state = self.game._expedition_load("100")
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        with patch("crystal_guild.engine.expedition_event_weights", return_value=(["resource"], [1.0])):
            result = self.game.expedition_resolve_stage("100")
        self.assertTrue(result.ok, result.messages)
        state = self.game._expedition_load("100")
        self.assertEqual(state["status"], "choice")
        self.assertGreaterEqual(sum(int(row["quantity"]) for row in state["cache"]["items"]), 2)
        progress = self.game._expedition_progress("100", "emerald_wilds")
        self.assertGreaterEqual(progress["progress"], 1)
        before = sum(self.game._inventory_qty("100", row["id"]) for row in state["cache"]["items"])
        returned = self.game.expedition_return("100")
        self.assertTrue(returned.ok, returned.messages)
        self.assertIsNone(self.game._expedition_load("100"))
        after = sum(self.game._inventory_qty("100", row["id"]) for row in state["cache"]["items"])
        self.assertGreater(after, before)
        pending = self.game._pending_portal_adventure_results("100")
        self.assertTrue(any(row.get("kind") == "expedition" for row in pending))

    def test_route_continue_and_internal_camp(self):
        self.unlock()
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "journey").ok)
        state = self.game._expedition_load("100")
        state["status"] = "choice"
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        self.assertTrue(self.game.expedition_camp("100").ok)
        state = self.game._expedition_load("100")
        self.assertEqual(state["travel_penalty_seconds"], 120)
        continued = self.game.expedition_continue("100", "deep")
        self.assertTrue(continued.ok, continued.messages)
        state = self.game._expedition_load("100")
        self.assertEqual(state["stage"], 2)
        self.assertEqual(state["route"], "deep")
        self.assertEqual(state["status"], "travel")

    def test_chocobo_rescue_traits_raise_but_cap_cache_protection(self):
        self.assertAlmostEqual(defeat_cache_keep(set()), .70)
        self.assertAlmostEqual(defeat_cache_keep({"steady_strider"}), .80)
        self.assertAlmostEqual(defeat_cache_keep({"steady_strider", "lucky_plume"}), .85)

    def test_equipment_is_locked_for_active_expedition(self):
        self.unlock()
        self.game._change_item("100", "bronze_sword", 1, "test")
        self.assertTrue(self.game.equip("100", "bronze sword").ok)
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)

        equip = self.game.equip("100", "bronze sword")
        unequip = self.game.unequip("100", "weapon")
        self.assertFalse(equip.ok)
        self.assertFalse(unequip.ok)
        self.assertIn("Expedition", " ".join(equip.messages))
        self.assertIn("Expedition", " ".join(unequip.messages))


    def test_alpha2_region_objectives_mastery_and_boss_unlock(self):
        self.unlock()
        initial = self.game._expedition_progress("100", "emerald_wilds")
        self.assertEqual([row["threshold"] for row in initial["objectives"]], [25, 50, 75, 100])
        self.assertFalse(initial["boss_unlocked"])
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress) VALUES ('100','emerald_wilds',75) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=75"
        )
        progress = self.game._expedition_progress("100", "emerald_wilds")
        self.assertTrue(progress["boss_unlocked"])
        board = self.game._expedition_board_state("100")
        emerald = next(row for row in board["regions"] if row["id"] == "emerald_wilds")
        self.assertEqual(emerald["boss_name"], "Elder Ochu")
        self.assertTrue(emerald["progress"]["boss_unlocked"])

    def test_alpha2_regional_boss_contract_is_guaranteed_final_stage(self):
        self.unlock()
        locked = self.game.expedition_start("100", "emerald_wilds", "boss")
        self.assertFalse(locked.ok)
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress) VALUES ('100','emerald_wilds',75) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=75"
        )
        started = self.game.expedition_start("100", "emerald_wilds", "boss")
        self.assertTrue(started.ok, started.messages)
        state = self.game._expedition_load("100")
        self.assertTrue(state["boss_contract"])
        self.assertEqual(state["base_stages"], 4)
        self.assertEqual(state["max_stages"], 4)
        state["stage"] = 4
        state["status"] = "travel"
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        resolved = self.game.expedition_resolve_stage("100")
        self.assertTrue(resolved.ok, resolved.messages)
        state = self.game._expedition_load("100")
        self.assertEqual(state["status"], "combat")
        self.assertTrue(state["boss_encounter"])
        self.assertEqual(state["combat"]["encounter"]["monster_id"], "elder_ochu")

    def test_alpha2_regional_boss_clear_and_mastery_title(self):
        self.unlock()
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress) VALUES ('100','emerald_wilds',90) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=90"
        )
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "boss").ok)
        state = self.game._expedition_load("100")
        state["stage"] = 4; state["status"] = "travel"; state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        self.assertTrue(self.game.expedition_resolve_stage("100").ok)
        with patch.object(self.game, "_resolve_active_attack", side_effect=lambda actor, monster, log: self.game.active_encounter.__setitem__("monster_hp", 0)):
            result = self.game.expedition_combat_action("100", "attack")
        self.assertTrue(result.ok, result.messages)
        self.assertTrue(result.data.get("expedition_boss_victory"))
        progress = self.game._expedition_progress("100", "emerald_wilds")
        self.assertEqual(progress["boss_clears"], 1)
        self.assertEqual(progress["progress"], 100)
        self.assertTrue(progress["mastered"])
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='emerald_pathfinder'"))
        cache = self.game._expedition_load("100")["cache"]
        self.assertTrue(any(row["id"] == "ochu_vine" for row in cache["items"]))

    def test_alpha3_atlas_derives_rank_and_mastery_from_existing_schema8_progress(self):
        self.unlock()
        values = {
            "emerald_wilds": (100, 12, 3, 1),
            "ashen_highlands": (80, 10, 2, 0),
            "mistfen_marshes": (60, 8, 2, 0),
            "frostveil_reach": (40, 6, 1, 0),
            "astral_scar": (20, 4, 1, 0),
        }
        for region_id, (progress, stages, runs, clears) in values.items():
            self.db.execute(
                "INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared,completed_runs,boss_clears) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=excluded.progress,stages_cleared=excluded.stages_cleared,completed_runs=excluded.completed_runs,boss_clears=excluded.boss_clears",
                ("100", region_id, progress, stages, runs, clears),
            )
        atlas = self.game._expedition_atlas("100")
        self.assertEqual(atlas["overall_progress"], 60)
        self.assertEqual(atlas["rank_name"], "Surveyor")
        self.assertEqual(atlas["regions_mastered"], 1)
        self.assertEqual(atlas["legendary_contracts_unlocked"], 1)
        board = self.game._expedition_board_state("100")
        self.assertEqual(board["atlas"]["rank_name"], "Surveyor")
        emerald = next(row for row in board["regions"] if row["id"] == "emerald_wilds")
        self.assertTrue(emerald["progress"]["legendary_unlocked"])

    def test_alpha3_legendary_contract_requires_mastery_and_prior_boss_clear(self):
        self.unlock()
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress,boss_clears) VALUES ('100','emerald_wilds',100,0) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=100,boss_clears=0"
        )
        locked = self.game.expedition_start("100", "emerald_wilds", "legendary")
        self.assertFalse(locked.ok)
        self.assertIn("clearing", " ".join(locked.messages).lower())
        self.db.execute("UPDATE player_region_exploration SET boss_clears=1 WHERE player_id='100' AND region_id='emerald_wilds'")
        started = self.game.expedition_start("100", "emerald_wilds", "legendary")
        self.assertTrue(started.ok, started.messages)
        state = self.game._expedition_load("100")
        self.assertTrue(state["boss_contract"])
        self.assertTrue(state["legendary_contract"])
        self.assertEqual(state["base_stages"], 5)
        self.assertEqual(state["max_stages"], 5)
        self.assertGreater(float(state["contract_reward_mult"]), 1.35)
        self.assertGreater(int(state["contract_travel_seconds"]), 300)
        public = self.game._expedition_public("100")
        self.assertEqual(public["depth"]["id"], "legendary")
        self.assertTrue(public["legendary_contract"])

    def test_alpha3_legendary_final_boss_is_stronger_and_doubles_guaranteed_materials(self):
        self.unlock()
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress,boss_clears) VALUES ('100','emerald_wilds',100,1) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=100,boss_clears=1"
        )
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "legendary").ok)
        state = self.game._expedition_load("100")
        state["stage"] = state["base_stages"]
        state["status"] = "travel"
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        resolved = self.game.expedition_resolve_stage("100")
        self.assertTrue(resolved.ok, resolved.messages)
        state = self.game._expedition_load("100")
        encounter = state["combat"]["encounter"]
        self.assertAlmostEqual(encounter.get("enemy_pressure_mult"), 1.10)
        self.assertTrue(encounter.get("legendary_contract"))
        with patch.object(self.game, "_resolve_active_attack", side_effect=lambda actor, monster, log: self.game.active_encounter.__setitem__("monster_hp", 0)):
            result = self.game.expedition_combat_action("100", "attack")
        self.assertTrue(result.ok, result.messages)
        self.assertTrue(result.data.get("expedition_legendary_contract"))
        cache = self.game._expedition_load("100")["cache"]
        ochu = next(row for row in cache["items"] if row["id"] == "ochu_vine" and row.get("source") == "legendary_regional_boss")
        cloth = next(row for row in cache["items"] if row["id"] == "ancient_cloth" and row.get("source") == "legendary_regional_boss")
        self.assertEqual(ochu["quantity"], 6)
        self.assertEqual(cloth["quantity"], 2)

    def test_alpha3_all_region_mastery_unlocks_master_cartographer(self):
        self.unlock()
        for region_id in self.game.data.expedition_regions:
            self.db.execute(
                "INSERT INTO player_region_exploration(player_id,region_id,progress) VALUES (?,?,100) "
                "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=100",
                ("100", region_id),
            )
        unlocked = self.game._check_achievements("100")
        self.assertTrue(any("No Blank Spots Left" in row for row in unlocked), unlocked)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_titles WHERE player_id='100' AND title_id='master_cartographer'"))
        atlas = self.game._expedition_atlas("100")
        self.assertTrue(atlas["all_mastered"])
        self.assertEqual(atlas["rank_name"], "Master Cartographer")

    def test_alpha4_landmarks_derive_permanently_from_region_progress(self):
        self.unlock()
        initial = self.game._expedition_progress("100", "emerald_wilds")
        self.assertEqual(len(initial["landmarks"]), 4)
        self.assertEqual(initial["landmarks_found"], 0)
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress) VALUES ('100','emerald_wilds',40) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=40"
        )
        progress = self.game._expedition_progress("100", "emerald_wilds")
        self.assertEqual(progress["landmarks_found"], 2)
        self.assertEqual([row["name"] for row in progress["landmarks"] if row["discovered"]], ["Whisperroot Gate", "Silverfall Crossing"])
        atlas = self.game._expedition_atlas("100")
        self.assertEqual(atlas["landmarks_found"], 2)
        self.assertEqual(atlas["landmark_count"], 20)

    def test_alpha4_route_metadata_exposes_risk_and_rare_event_odds(self):
        self.unlock()
        board = self.game._expedition_board_state("100")
        routes = {row["id"]: row for row in board["routes"]}
        self.assertLess(routes["safe"]["rare_event_chance"], routes["unknown"]["rare_event_chance"])
        self.assertLess(routes["unknown"]["rare_event_chance"], routes["deep"]["rare_event_chance"])

    def test_alpha4_rare_regional_event_is_saved_to_journal(self):
        self.unlock("keen_eye")
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        state = self.game._expedition_load("100")
        state["travel_ready_at"] = 0
        state["route"] = "deep"
        self.game._expedition_save("100", state)
        with patch.object(self.game.rng, "random", return_value=0.0):
            result = self.game.expedition_resolve_stage("100")
        self.assertTrue(result.ok, result.messages)
        state = self.game._expedition_load("100")
        self.assertEqual(state["status"], "choice")
        self.assertEqual(state["event"]["type"], "rare")
        self.assertTrue(state["rare_events_seen"])
        self.assertEqual(state["history"][-1]["type"], "rare")
        public = self.game._expedition_public("100")
        self.assertEqual(public["history"][-1]["type"], "rare")

    def test_alpha4_normal_events_use_region_specific_copy(self):
        self.unlock("forager")
        self.assertTrue(self.game.expedition_start("100", "ashen_highlands", "scout").ok)
        state = self.game._expedition_load("100")
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        with patch.object(self.game.rng, "random", return_value=1.0), patch("crystal_guild.engine.expedition_event_weights", return_value=(["resource"], [1.0])):
            result = self.game.expedition_resolve_stage("100")
        self.assertTrue(result.ok, result.messages)
        label = self.game._expedition_load("100")["event"]["label"]
        regional = self.data.expedition_regions["ashen_highlands"]["regional_events"]["resource"]
        self.assertTrue(any(label.startswith(prefix) for prefix in regional), label)

    def test_alpha5_specialization_scales_from_existing_trait_and_bond_level(self):
        self.unlock("keen_eye")
        self.db.execute("UPDATE player_chocobos SET xp=? WHERE player_id='100'", (total_xp_floor_for_level(20),))
        spec = expedition_specialization({"keen_eye"}, 20)
        self.assertEqual(spec["name"], "Scout")
        self.assertEqual(spec["tier"], 5)
        self.assertTrue(spec["maxed"])
        board = self.game._expedition_board_state("100")
        self.assertEqual(board["chocobo"]["specialization"]["name"], "Scout")
        self.assertEqual(board["chocobo"]["specialization"]["tier"], 5)
        stable = self.game._chocobo_state_data("100")
        self.assertEqual(stable["companion"]["specialization"]["tier_name"], "Legendary Partner")

    def test_alpha5_bond_tier_improves_pathfinder_and_forager_effects(self):
        self.assertEqual(effective_travel_seconds(240, {"fleet_feet"}, 1), 204)
        self.assertEqual(effective_travel_seconds(240, {"fleet_feet"}, 20), 194)
        self.assertEqual(resource_yield_bonus({"forager"}, 1), 1)
        self.assertEqual(resource_yield_bonus({"forager"}, 15), 2)
        self.assertAlmostEqual(defeat_cache_keep({"steady_strider", "lucky_plume"}, 20), 0.90)

    def test_alpha5_completed_expedition_awards_existing_hunt_seal_stipend(self):
        self.unlock("fleet_feet")
        before = int(self.game._player("100")["hunt_seals"] or 0)
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
        state = self.game._expedition_load("100")
        state["stage"] = state["base_stages"]
        state["status"] = "choice"
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        result = self.game.expedition_return("100")
        self.assertTrue(result.ok, result.messages)
        after = int(self.game._player("100")["hunt_seals"] or 0)
        self.assertEqual(after - before, 2)
        self.assertEqual(result.data["expedition_result"]["rewards"]["seals"], 2)
        self.assertEqual(result.data["expedition_result"]["stipend_seals"], 2)
        metric = self.db.one("SELECT value FROM player_record_stats WHERE player_id='100' AND metric='expeditions_completed'")
        self.assertEqual(int(metric["value"]), 1)
        stable = self.game._chocobo_state_data("100")
        self.assertEqual(stable["companion"]["accomplishments"]["completed"], 1)

    def test_alpha5_contract_stipends_reward_repeat_play_without_new_currency(self):
        normal = {"depth": "deep"}
        boss = {"boss_contract": True}
        legendary = {"boss_contract": True, "legendary_contract": True}
        self.assertEqual(self.game._expedition_stipend(normal, "complete"), 7)
        self.assertEqual(self.game._expedition_stipend(boss, "complete"), 10)
        self.assertEqual(self.game._expedition_stipend(legendary, "complete"), 15)
        self.assertEqual(self.game._expedition_stipend(legendary, "defeat"), 0)


    def test_beta1_route_risk_changes_actual_pressure_not_only_event_labels(self):
        self.assertLess(float(ROUTES["safe"]["combat_pressure_mult"]), 1.0)
        self.assertLess(float(ROUTES["safe"]["hazard_damage_mult"]), 1.0)
        self.assertEqual(float(ROUTES["unknown"]["combat_pressure_mult"]), 1.0)
        self.assertEqual(float(ROUTES["unknown"]["hazard_damage_mult"]), 1.0)
        self.assertGreater(float(ROUTES["deep"]["combat_pressure_mult"]), 1.0)
        self.assertGreater(float(ROUTES["deep"]["hazard_damage_mult"]), 1.0)

    def test_beta1_safe_and_deep_routes_apply_combat_pressure_to_actual_encounters(self):
        self.unlock()
        for route_id, expected in (("safe", 0.90), ("deep", 1.10)):
            self.game._expedition_delete("100")
            p = self.game._player("100")
            self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='100'", (self.game._max_hp(p),))
            self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "scout").ok)
            state = self.game._expedition_load("100")
            state["route"] = route_id
            state["travel_ready_at"] = 0
            self.game._expedition_save("100", state)
            with patch("crystal_guild.engine.expedition_event_weights", return_value=(["combat"], [1.0])), patch.object(self.game, "_expedition_select_monster", return_value=self.data.monsters["goblin"]), patch.object(self.game.rng, "random", return_value=1.0):
                result = self.game.expedition_resolve_stage("100")
            self.assertTrue(result.ok, result.messages)
            combat_state = self.game._expedition_load("100")
            self.assertAlmostEqual(float(combat_state["combat"]["encounter"]["enemy_pressure_mult"]), expected)

    def test_beta1_legendary_scaling_is_challenging_without_alpha3_cliff(self):
        self.unlock()
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress,boss_clears) VALUES ('100','emerald_wilds',100,1) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=100,boss_clears=1"
        )
        self.assertTrue(self.game.expedition_start("100", "emerald_wilds", "legendary").ok)
        state = self.game._expedition_load("100")
        state["stage"] = state["base_stages"]
        state["route"] = "unknown"
        state["status"] = "travel"
        state["travel_ready_at"] = 0
        self.game._expedition_save("100", state)
        self.assertTrue(self.game.expedition_resolve_stage("100").ok)
        encounter = self.game._expedition_load("100")["combat"]["encounter"]
        base_hp = int(self.data.monsters["elder_ochu"]["hp"])
        self.assertEqual(int(encounter["monster_max_hp"]), int(round(base_hp * 1.20)))
        self.assertAlmostEqual(float(encounter["enemy_pressure_mult"]), 1.10)

    def test_adventure_state_exposes_compact_expedition_board(self):
        self.unlock("keen_eye")
        state = self.game._portal_adventure_state_data("100")
        board = state["expeditions"]
        self.assertTrue(board["ready"])
        self.assertEqual(len(board["regions"]), 5)
        self.assertEqual([row["id"] for row in board["depths"]], ["scout", "journey", "deep"])
        self.assertIn("keen_eye", board["traits_active"])
        encoded = json.dumps({"adventure_state": state}, separators=(",", ":")).encode()
        self.assertLess(len(encoded), 18 * 1024)


if __name__ == "__main__":
    unittest.main()

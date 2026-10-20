from __future__ import annotations

import os
import random
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from crystal_guild.config import Settings
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine, xp_to_next
from crystal_guild.encounter_daemon import (
    EncounterDaemon, NotificationDispatcher, TwitchChatDeliveryError,
    TwitchRESTChatSender, _packed_messages,
)


ROOT = Path(__file__).resolve().parents[1]


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0, venture_treasure_chance=0.0, overlay_state_path=str(Path(self.tmp.name) / "overlay.json"), rng=random.Random(7))
        self.game.recruit("1", "van", "Van")
        # Older engine-unit fixtures address monsters in the permanent catalog.
        # Seasonal encounter variants are exercised in their dedicated suite.
        self.game._roll_seasonal_venture_variant = lambda **_kwargs: None

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_recruit_is_persistent_and_duplicate_safe(self):
        self.assertFalse(self.game.recruit("1", "van", "Van").ok)
        self.assertIn("Lv.1", self.game.hero("1").messages[0])

    def test_choose_job_and_venture(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        result = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(result.ok)
        self.assertEqual(result.data.get("venture_event"), "encounter")
        self.assertTrue(result.messages[0].startswith("ENCOUNTER —"))
        self.assertNotIn("RANDOM ENCOUNTER", result.messages[0])
        row = self.db.one("SELECT ventures FROM players WHERE twitch_id='1'")
        self.assertEqual(row["ventures"], 1)

    def test_stream_venture_is_always_an_encounter_even_with_legacy_treasure_override(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        self.game.venture_treasure_chance = 1.0
        result = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(result.ok)
        self.assertIsNotNone(self.game.active_encounter)
        self.assertEqual(self.game.active_encounter.get("kind"), "venture")
        self.assertEqual(self.game.active_encounter.get("state"), "rally")
        self.assertNotEqual(result.data.get("venture_event"), "treasure")

    def test_venture_treasure_candidates_use_minus_five_plus_two_level_band(self):
        min_level, max_level, candidates = self.game._venture_treasure_candidates(1)
        self.assertEqual((min_level, max_level), (1, 3))
        self.assertFalse(candidates["accessory"])
        for category, rows in candidates.items():
            for item in rows:
                self.assertEqual(item["type"], category)
                level = self.game._venture_item_level(item)
                self.assertIsNotNone(level)
                self.assertGreaterEqual(level, 1)
                self.assertLessEqual(level, 3)

    def test_venture_never_rolls_more_than_ten_levels_above_starter(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        seen = []

        def choose_highest(population, weights=None, k=1):
            seen.extend(population)
            pick = max(
                population,
                key=lambda row: self.game.data.monsters[row["monster_id"]]["level"],
            )
            return [pick]

        with patch.object(self.game.rng, "choices", side_effect=choose_highest):
            result = self.game.venture("1", bypass_cooldown=True)

        self.assertTrue(result.ok, result.messages)
        self.assertTrue(seen)
        levels = [self.game.data.monsters[row["monster_id"]]["level"] for row in seen]
        self.assertLessEqual(max(levels), 11)
        monster = self.game.data.monsters[self.game.active_encounter["monster_id"]]
        self.assertLessEqual(monster["level"], 11)

    def test_ready_all_players_restores_hp_resources_and_clears_camp(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        self.assertTrue(self.game.recruit("2", "mage", "Mage").ok)
        self.assertTrue(self.game.choose_job("2", "black mage").ok)
        now = int(time.time())
        self.db.execute("UPDATE players SET level=17, xp=4321, gil=9876, current_hp=1, current_ap=0, camp_until=? WHERE twitch_id='1'", (now + 600,))
        self.db.execute("UPDATE players SET current_hp=0, current_mp=0, camp_until=? WHERE twitch_id='2'", (now + 900,))

        result = self.game.ready_all_players()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(result.data["players_reset"], 2)
        self.assertEqual(result.data["camps_cleared"], 2)
        self.assertEqual(result.data["ko_revived"], 1)

        preserved = self.db.one("SELECT level, xp, gil FROM players WHERE twitch_id='1'")
        self.assertEqual((preserved["level"], preserved["xp"], preserved["gil"]), (17, 4321, 9876))

        for player_id in ("1", "2"):
            row = self.db.one("SELECT * FROM players WHERE twitch_id=?", (player_id,))
            self.assertEqual(row["camp_until"], 0)
            self.assertEqual(row["current_hp"], self.game._max_hp(row))
            resources = self.game._resource_state_for(row, initialize=False)
            if resources["max_mp"] > 0:
                self.assertEqual(resources["mp"], resources["max_mp"])
            if resources["max_ap"] > 0:
                self.assertEqual(resources["ap"], resources["max_ap"])

    def test_ready_all_players_refuses_during_active_combat(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        started = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(started.ok)
        self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='1'")
        result = self.game.ready_all_players()
        self.assertFalse(result.ok)
        self.assertIn("active combat", result.messages[0].lower())
        self.assertEqual(self.db.one("SELECT current_hp FROM players WHERE twitch_id='1'")["current_hp"], 1)
        self.assertIsNotNone(self.game.active_encounter)

    def test_reset_all_player_timers_clears_cooldowns_camps_and_shop_refreshes(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        before_hp = self.db.one("SELECT current_hp FROM players WHERE twitch_id='1'")["current_hp"]
        self.game._set_cooldown("1", "venture", 600)
        self.game._set_cooldown("1", "daily", 86400)
        self.game._set_cooldown("1", "hunt:test", 1800)
        self.db.execute("UPDATE players SET camp_until=? WHERE twitch_id='1'", (int(time.time()) + 600,))
        self.game.shop("1")
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM cooldowns")["n"], 3)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_regional_shops WHERE player_id='1'"))

        result = self.game.reset_all_player_timers()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(result.data["cooldowns_cleared"], 3)
        self.assertEqual(result.data["camps_cleared"], 1)
        self.assertEqual(result.data["shops_cleared"], 1)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM cooldowns")["n"], 0)
        self.assertEqual(self.db.one("SELECT camp_until FROM players WHERE twitch_id='1'")["camp_until"], 0)
        self.assertIsNone(self.db.one("SELECT 1 FROM player_regional_shops WHERE player_id='1'"))
        self.assertEqual(self.db.one("SELECT current_hp FROM players WHERE twitch_id='1'")["current_hp"], before_hp)

    def test_clear_all_adventures_clears_field_hunts_and_solo_without_touching_raid_or_cooldowns(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        self.assertTrue(self.game.recruit("2", "aeris", "Aeris").ok)
        self.assertTrue(self.game.choose_job("2", "warrior").ok)

        # Shared field/Rally state.
        started = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(started.ok, started.messages)
        self.assertIsNotNone(self.game.active_encounter)

        # Personal timed Hunt state may coexist with the shared field slot.
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='2'")
        hunt = self.game.hunt("2", "red hot problem", bypass_cooldown=True)
        self.assertTrue(hunt.ok, hunt.messages)
        self.assertIn("2", self.game.active_hunts)

        # Persist a deliberately orphaned Solo Venture row. The recovery command
        # must be able to clear it even if Portal can no longer render it.
        self.game._solo_expedition_save("1", {
            "version": 1, "started_at": int(time.time()), "stage": 2,
            "status": "choice", "spoils": {"gil": 123, "items": []},
            "secured": {"xp": 50, "jp": 5}, "history": [],
        })
        self.assertIsNotNone(self.db.one("SELECT state_json FROM solo_expeditions WHERE player_id='1'"))

        # Persist a v1.2 Expedition row as well. Emergency recovery must clear
        # the authoritative run without touching exploration progression.
        self.game._expedition_save("2", {
            "version": 1, "started_at": int(time.time()), "region_id": "emerald_wilds",
            "depth": "scout", "stage": 2, "status": "travel", "cache": {"gil": 77, "items": []},
        })
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress,stages_cleared) VALUES ('2','emerald_wilds',12,3) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=12,stages_cleared=3"
        )
        self.assertIsNotNone(self.db.one("SELECT state_json FROM player_expeditions WHERE player_id='2'"))

        # Adventure cooldowns are intentionally not part of this emergency clear.
        self.game._set_cooldown("1", "solo_venture", 420)
        remaining_before = self.game._cooldown_remaining("1", "solo_venture")

        # Raids/world bosses use a separate state owner and must not be touched.
        self.game.active_boss = {"id": 999, "name": "Recovery Test Boss"}
        raid_before = dict(self.game.active_boss)

        result = self.game.clear_all_adventures()
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(result.data["encounters_cleared"], 1)
        self.assertEqual(result.data["hunts_cleared"], 1)
        self.assertEqual(result.data["solo_ventures_cleared"], 1)
        self.assertEqual(result.data["expeditions_cleared"], 1)
        self.assertEqual(result.data["adventures_cleared"], 4)
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})
        self.assertEqual(self.game.active_hunts, {})
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM solo_expeditions")["n"], 0)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_expeditions")["n"], 0)
        exploration = self.db.one("SELECT progress,stages_cleared FROM player_region_exploration WHERE player_id='2' AND region_id='emerald_wilds'")
        self.assertEqual((exploration["progress"], exploration["stages_cleared"]), (12, 3))
        self.assertEqual(self.game.active_boss, raid_before)
        self.assertGreater(self.game._cooldown_remaining("1", "solo_venture"), 0)
        self.assertLessEqual(self.game._cooldown_remaining("1", "solo_venture"), remaining_before)

        checkpoint = self.db.one("SELECT value_json FROM runtime_state WHERE state_key='combat'")
        self.assertIsNotNone(checkpoint)
        payload = __import__("json").loads(checkpoint["value_json"])
        self.assertIsNone(payload.get("active_encounter"))
        self.assertEqual(payload.get("active_hunts"), {})
        self.assertEqual(payload.get("active_boss", {}).get("name"), "Recovery Test Boss")

    def test_clear_all_adventures_is_safe_when_nothing_is_active(self):
        result = self.game.clear_all_adventures()
        self.assertTrue(result.ok)
        self.assertEqual(result.data["adventures_cleared"], 0)
        self.assertEqual(result.data["expeditions_cleared"], 0)
        self.assertIn("No active", result.messages[0])

    def test_reset_all_player_timers_does_not_advance_active_combat_deadlines(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        started = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(started.ok)
        encounter_id = self.game.active_encounter["id"]
        closes_at = self.game.active_encounter["closes_at"]
        result = self.game.reset_all_player_timers()
        self.assertTrue(result.ok)
        self.assertTrue(result.data["active_combat_unchanged"])
        self.assertEqual(self.game.active_encounter["id"], encounter_id)
        self.assertEqual(self.game.active_encounter["closes_at"], closes_at)

    def test_shop_purchase_and_equip(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        buy = self.game.buy("1", "bronze sword", 1)
        self.assertTrue(buy.ok)
        equip = self.game.equip("1", "bronze sword")
        self.assertTrue(equip.ok)
        self.assertIn("Bronze Sword", self.game.gear("1").messages[0])

    def test_level_processing(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET xp=? WHERE twitch_id='1'", (xp_to_next(1) + 1,))
        self.game._process_levels("1", "warrior")
        p = self.db.one("SELECT level FROM players WHERE twitch_id='1'")
        self.assertEqual(p["level"], 2)

    def test_sell_and_item_inspection(self):
        self.game.choose_job("1", "warrior")
        self.game.buy("1", "potion", 1)
        inspected = self.game.inspect_item("1", "potion")
        self.assertTrue(inspected.ok)
        before = self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]
        sold = self.game.sell("1", "potion", 1)
        self.assertTrue(sold.ok)
        after = self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]
        self.assertGreater(after, before)

    def test_data_references_are_valid(self):
        for region in self.game.data.regions.values():
            for encounter in region["encounters"]:
                self.assertIn(encounter["monster_id"], self.game.data.monsters)
                self.assertGreater(encounter["weight"], 0)
        for monster in self.game.data.monsters.values():
            for drop in monster.get("drops", []):
                self.assertIn(drop["item_id"], self.game.data.items)
                self.assertGreaterEqual(drop["chance"], 0)
                self.assertLessEqual(drop["chance"], 1)


    def test_v2_data_references_are_valid(self):
        for hunt in self.game.data.hunts.values():
            self.assertIn(hunt["rank"], {"C", "B", "A", "S", "S+"})
            self.assertIn(hunt["monster_id"], self.game.data.monsters)
            if hunt.get("first_clear_item"):
                self.assertIn(hunt["first_clear_item"], self.game.data.items)
            if hunt.get("first_clear_title"):
                self.assertIn(hunt["first_clear_title"], self.game.data.titles)
        for quest in self.game.data.quests.values():
            self.assertIn(quest["rewards"]["job"], self.game.data.jobs)
            self.assertIn(quest["rewards"]["title"], self.game.data.titles)
            for req in quest.get("requirements", []):
                if req["type"] == "job_level":
                    self.assertIn(req["job_id"], self.game.data.jobs)
                if req["type"] == "monster_kills":
                    self.assertIn(req["monster_id"], self.game.data.monsters)
                if req["type"] == "hunt_clear":
                    self.assertIn(req["hunt_id"], self.game.data.hunts)
        for achievement in self.game.data.achievements.values():
            if achievement.get("reward_title"):
                self.assertIn(achievement["reward_title"], self.game.data.titles)
        for job in self.game.data.jobs.values():
            self.assertIn("mastery", job)
            for ability in job.get("abilities", []):
                self.assertGreaterEqual(ability["level"], 1)
                self.assertLessEqual(ability["level"], 50)
            for req in job.get("unlock", []):
                if req["type"] == "job_level":
                    self.assertIn(req["job_id"], self.game.data.jobs)
                if req["type"] == "quest_complete":
                    self.assertIn(req["quest_id"], self.game.data.quests)
                if req["type"] == "hunt_clear":
                    self.assertIn(req["hunt_id"], self.game.data.hunts)

    def test_hunt_first_clear_awards_seals_item_and_title(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='1'")
        started = self.game.hunt("1", "red hot problem", bypass_cooldown=True)
        self.assertTrue(started.ok)
        self.assertTrue(started.data.get("hunt_started"))
        # Hunts award nothing at acceptance; rewards are committed only
        # when the rank timer's autonomous resolver records the result.
        self.assertIsNone(
            self.db.one(
                "SELECT clears FROM player_hunts WHERE player_id='1' AND hunt_id='red_hot_problem'"
            )
        )
        self.assertIsNone(self.game.active_encounter)
        result = self.game.resolve_hunt("1", started.data["hunt_run_id"], force=True)
        self.assertTrue(result.ok)
        self.assertTrue(result.data.get("hunt_finished"))
        hunt = self.db.one("SELECT clears FROM player_hunts WHERE player_id='1' AND hunt_id='red_hot_problem'")
        self.assertIsNotNone(hunt)
        self.assertGreaterEqual(hunt["clears"], 1)
        player = self.db.one("SELECT hunt_seals FROM players WHERE twitch_id='1'")
        self.assertGreater(player["hunt_seals"], 0)
        self.assertGreaterEqual(self.game._inventory_qty("1", "bomb_kings_fuse"), 1)
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_titles WHERE player_id='1' AND title_id='bomb_disposal_officer'"))

    def test_job_quest_unlocks_advanced_job(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE player_jobs SET level=20 WHERE player_id='1' AND job_id='warrior'")
        self.game.choose_job("1", "whitemage")
        self.db.execute("UPDATE player_jobs SET level=10 WHERE player_id='1' AND job_id='whitemage'")
        self.db.execute("UPDATE players SET level=30 WHERE twitch_id='1'")
        self.db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears,first_cleared_at,last_cleared_at) VALUES ('1','prince_of_the_tide',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
        quest = self.game.quest("1", "oath of light")
        self.assertTrue(quest.ok)
        paladin = self.game.choose_job("1", "paladin")
        self.assertTrue(paladin.ok)
        self.assertEqual(self.db.one("SELECT current_job FROM players WHERE twitch_id='1'")["current_job"], "paladin")

    def test_job_quest_requirements_reconcile_retroactively_on_job_change(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE player_jobs SET level=20 WHERE player_id='1' AND job_id='warrior'")
        self.db.execute("INSERT INTO bestiary(player_id,monster_id,defeats) VALUES ('1','skeleton',10)")
        self.db.execute("INSERT INTO bestiary(player_id,monster_id,defeats) VALUES ('1','tonberry',1)")
        before_gil = int(self.game._player("1")["gil"])

        result = self.game.choose_job("1", "darkknight")

        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game._player("1")["current_job"], "darkknight")
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_quests WHERE player_id='1' AND quest_id='abyssal_oath'"))
        self.assertIsNotNone(self.db.one("SELECT 1 FROM player_titles WHERE player_id='1' AND title_id='abyss_walker'"))
        self.assertEqual(int(self.game._player("1")["gil"]), before_gil + 1200)

        # Re-checking the same Job must not duplicate quest rewards.
        self.game.choose_job("1", "warrior")
        self.game.choose_job("1", "darkknight")
        self.assertEqual(int(self.game._player("1")["gil"]), before_gil + 1200)
        tx = self.db.one("SELECT COUNT(*) AS n FROM transactions WHERE player_id='1' AND source='quest:abyssal_oath' AND kind='gil'")
        self.assertEqual(int(tx["n"]), 1)

    def test_locked_job_reports_requirements(self):
        result = self.game.choose_job("1", "dragoon")
        self.assertFalse(result.ok)
        self.assertIn("locked", result.messages[0].lower())

    def test_mastery_slot_applies_cross_job_effect(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE player_jobs SET level=50 WHERE player_id='1' AND job_id='warrior'")
        result = self.game.mastery("1", "warrior", 1)
        self.assertTrue(result.ok)
        self.game.choose_job("1", "blackmage")
        effects = self.game._effects("1", "blackmage")
        self.assertGreaterEqual(effects.get("defense_mult", 0), 0.05)

    def test_job_abilities_change_effects(self):
        self.game.choose_job("1", "thief")
        self.db.execute("UPDATE player_jobs SET level=40 WHERE player_id='1' AND job_id='thief'")
        effects = self.game._effects("1", "thief")
        self.assertGreaterEqual(effects.get("loot_bonus", 0), 0.15)
        self.assertGreaterEqual(effects.get("crit_bonus", 0), 0.05)

    def test_titles_can_be_equipped_after_unlock(self):
        self.game._unlock_title("1", "needle_dodger")
        result = self.game.set_title("1", "needle dodger")
        self.assertTrue(result.ok)
        self.assertEqual(self.db.one("SELECT title FROM players WHERE twitch_id='1'")["title"], "Needle Dodger")


    def test_v3_data_references_are_valid(self):
        for recipe in self.game.data.recipes.values():
            self.assertIn(recipe["output"]["item_id"], self.game.data.items)
            for mat in recipe.get("materials", []):
                self.assertIn(mat["item_id"], self.game.data.items)
        for monster in self.game.data.monsters.values():
            for drop in monster.get("pity_drops", []):
                self.assertIn(drop["item_id"], self.game.data.items)
                self.assertGreater(drop["guarantee_after"], 0)
            for drop in monster.get("recipe_drops", []):
                self.assertIn(drop["recipe_id"], self.game.data.recipes)
                self.assertGreater(drop["guarantee_after"], 0)
        for entry in self.game.data.seal_shop.values():
            self.assertIn(entry["item_id"], self.game.data.items)
            self.assertGreater(entry["cost"], 0)
        for rule in self.game.data.forge:
            self.assertGreater(rule["level"], 0)
            for mat in rule.get("materials", []):
                self.assertIn(mat["item_id"], self.game.data.items)
        for relic in self.game.data.relics.values():
            self.assertIn(relic["job_id"], self.game.data.jobs)
            self.assertGreaterEqual(len(relic["stages"]), 3)
            for stage in relic["stages"]:
                self.assertIn(stage["reward_item"], self.game.data.items)
                for mat in stage.get("cost", {}).get("items", []):
                    self.assertIn(mat["item_id"], self.game.data.items)
                for req in stage.get("requirements", []):
                    if req["type"] == "job_level":
                        self.assertIn(req["job_id"], self.game.data.jobs)
                    elif req["type"] == "monster_kills":
                        self.assertIn(req["monster_id"], self.game.data.monsters)
                    elif req["type"] == "hunt_clear":
                        self.assertIn(req["hunt_id"], self.game.data.hunts)
        for region in self.game.data.regions.values():
            for encounter in region["encounters"]:
                self.assertIn(encounter["monster_id"], self.game.data.monsters)

    def test_crafting_consumes_materials_and_creates_output(self):
        self.db.execute("UPDATE players SET level=8 WHERE twitch_id='1'")
        before_potions = self.game._inventory_qty("1", "potion")
        self.assertEqual(before_potions, 3)
        result = self.game.craft("1", "hi-potion batch")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game._inventory_qty("1", "potion"), 0)
        self.assertEqual(self.game._inventory_qty("1", "hi_potion"), 2)
        self.assertEqual(self.db.one("SELECT crafts FROM players WHERE twitch_id='1'")["crafts"], 1)

    def test_forge_upgrade_changes_equipment_stats(self):
        self.game.choose_job("1", "warrior")
        self.game._change_item("1", "bronze_sword", 1, "test")
        self.game._change_item("1", "iron_ore", 3, "test")
        self.db.execute("UPDATE players SET gil=2000 WHERE twitch_id='1'")
        self.assertTrue(self.game.equip("1", "bronze sword").ok)
        p = self.game._player("1")
        job = self.game.data.jobs["warrior"]
        before = self.game._stats(p, job)["attack"]
        result = self.game.upgrade("1", "bronze sword")
        self.assertTrue(result.ok, result.messages)
        after = self.game._stats(self.game._player("1"), job)["attack"]
        self.assertEqual(self.game._upgrade_level("1", "bronze_sword"), 1)
        self.assertGreater(after, before)

    def test_seal_shop_spends_seals_and_grants_item(self):
        self.db.execute("UPDATE players SET level=50, hunt_seals=100 WHERE twitch_id='1'")
        result = self.game.sealbuy("1", "crystal shard", 2)
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game._inventory_qty("1", "crystal_shard"), 2)
        self.assertEqual(self.db.one("SELECT hunt_seals FROM players WHERE twitch_id='1'")["hunt_seals"], 60)

    def test_recipe_pity_guarantees_learning(self):
        source = self.game.data.monsters["death_machine"]
        key = "recipe:death_machine:magitek_edge"
        self.db.execute("INSERT INTO drop_pity(player_id,pity_key,attempts) VALUES ('1',?,17)", (key,))
        drops = self.game._roll_recipe_drops("1", source, "test")
        self.assertTrue(any("Magitek Edge" in d for d in drops))
        self.assertTrue(self.game._recipe_known("1", self.game.data.recipes["magitek_edge"]))

    def test_item_pity_guarantees_rare_material(self):
        source = self.game.data.monsters["crystal_golem"]
        key = "item:crystal_golem:crystal_core"
        self.db.execute("INSERT INTO drop_pity(player_id,pity_key,attempts) VALUES ('1',?,9)", (key,))
        drops = self.game._roll_pity_drops("1", source, "test")
        self.assertTrue(any("Crystal Core" in d for d in drops))
        self.assertEqual(self.game._inventory_qty("1", "crystal_core"), 1)

    def test_relic_stage_one_can_be_awakened(self):
        self.db.execute("UPDATE players SET level=65, gil=50000, hunt_seals=500 WHERE twitch_id='1'")
        self.db.execute("INSERT INTO player_jobs(player_id,job_id,level,jp) VALUES ('1','dragoon',50,0)")
        self.game._change_item("1", "mythril_ore", 8, "test")
        self.game._change_item("1", "crystal_shard", 4, "test")
        inspect = self.game.relic("1", "gae bolg")
        self.assertTrue(inspect.ok)
        result = self.game.awaken_relic("1", "gae bolg")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game._inventory_qty("1", "gae_bolg_dormant"), 1)
        self.assertEqual(self.db.one("SELECT stage FROM player_relics WHERE player_id='1' AND relic_id='gae_bolg'")["stage"], 1)


    def test_relic_can_reach_zenith_and_increment_completion(self):
        self.db.execute("UPDATE players SET level=70, gil=200000, hunt_seals=2000 WHERE twitch_id='1'")
        self.db.execute("INSERT INTO player_jobs(player_id,job_id,level,jp) VALUES ('1','dragoon',50,0)")
        for item_id, qty in {
            "mythril_ore": 8,
            "crystal_shard": 4,
            "crystal_core": 2,
            "rift_crystal": 2,
            "dark_matter": 1,
            "eidolon_shard": 1,
            "adamantite": 1,
        }.items():
            self.game._change_item("1", item_id, qty, "test")
        self.assertTrue(self.game.awaken_relic("1", "gae bolg").ok)
        self.db.execute("INSERT INTO bestiary(player_id,monster_id,defeats) VALUES ('1','wyrm',10)")
        self.db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears,first_cleared_at,last_cleared_at) VALUES ('1','dragon_beyond_the_veil',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
        self.assertTrue(self.game.awaken_relic("1", "gae bolg").ok)
        self.db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears,first_cleared_at,last_cleared_at) VALUES ('1','tyrant_of_the_rift',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
        result = self.game.awaken_relic("1", "gae bolg")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game._inventory_qty("1", "gae_bolg_zenith"), 1)
        self.assertEqual(self.db.one("SELECT relics_completed FROM players WHERE twitch_id='1'")["relics_completed"], 1)
        self.assertEqual(self.db.one("SELECT stage FROM player_relics WHERE player_id='1' AND relic_id='gae_bolg'")["stage"], 3)

    def test_relic_weapon_is_job_restricted(self):
        self.game.choose_job("1", "warrior")
        self.game._change_item("1", "gae_bolg_dormant", 1, "test")
        self.db.execute("UPDATE players SET level=65 WHERE twitch_id='1'")
        result = self.game.equip("1", "gae bolg dormant")
        self.assertFalse(result.ok)
        self.assertIn("only be wielded", result.messages[0])

    def test_bestiary_expansion_catalogs(self):
        self.assertGreaterEqual(len(self.game.data.monsters), 100)
        self.assertGreaterEqual(len(self.game.data.bosses), 30)
        self.assertIn("omega_weapon", self.game.data.bosses)
        self.assertIn("penance", self.game.data.bosses)
        self.assertIn("yiazmat", self.game.data.bosses)
        self.assertIn("omega_ruins", self.game.data.regions)
        self.assertTrue(self.game.monster_info("demonolith").ok)
        self.assertTrue(self.game.boss_info("omega weapon").ok)
        self.assertTrue(self.game.bosses("super").ok)

    def test_boss_drop_is_awarded_on_victory(self):
        self.game.choose_job("1", "warrior")
        self.assertTrue(self.game.spawn_boss("bomb king").ok)
        self.game.active_boss["current_hp"] = 1
        self.game.active_boss["max_hp"] = 1
        self.game.active_boss["drops"] = [{"item_id": "omega_core", "chance": 1.0}]
        self.assertTrue(self.game.raid_join("1").ok)
        result = self.game.resolve_boss()
        self.assertTrue(result.ok)
        self.assertGreaterEqual(self.game._inventory_qty("1", "omega_core"), 1)

    def test_boss_data_references_are_valid(self):
        valid_tiers = {"Primal Boss", "World Boss", "High Boss", "Superboss", "Ultimate Superboss"}
        for boss in self.game.data.bosses.values():
            self.assertIn(boss.get("tier"), valid_tiers)
            self.assertGreater(boss.get("recommended_level", 0), 0)
            self.assertGreater(boss["hp"], 0)
            for drop in boss.get("drops", []):
                self.assertIn(drop["item_id"], self.game.data.items)
                self.assertGreaterEqual(drop["chance"], 0)
                self.assertLessEqual(drop["chance"], 1)

    def test_admin_raid_resolver_watchdog_preserves_living_raid(self):
        from crystal_guild.engine import GameResult

        self.game.active_boss = {"id": "watchdog_boss", "name": "Watchdog Boss", "hp": 100, "current_hp": 100, "max_hp": 100, "state": "combat", "round": 1}
        self.game.raid_roster = {"1": {"name": "Van", "hp": 100, "max_hp": 100}}

        def no_terminal_raid_round(*args, **kwargs):
            self.game.active_boss["round"] = int(self.game.active_boss.get("round", 0)) + 1
            return GameResult.success("technical raid test round", raid_round=True)

        with patch("crystal_guild.engine.ADMIN_AUTOSIM_WATCHDOG_ROUNDS", 2), patch.object(
            self.game, "raid_round", side_effect=no_terminal_raid_round
        ):
            result = self.game.resolve_boss()

        self.assertTrue(result.ok, result.messages)
        self.assertFalse(result.data.get("raid_finished"))
        self.assertTrue(result.data.get("combat_continues"))
        self.assertIsNotNone(self.game.active_boss)
        self.assertGreater(int(self.game.raid_roster["1"]["hp"]), 0)

    def test_boss_lifecycle(self):
        self.game.choose_job("1", "blackmage")
        self.assertTrue(self.game.spawn_boss("bomb king").ok)
        self.assertTrue(self.game.raid_join("1").ok)
        result = self.game.resolve_boss()
        self.assertTrue(result.ok)
        self.assertIsNone(self.game.active_boss)


    def test_v4_1_resolution_exception_restores_last_committed_encounter(self):
        self.game.choose_job("1", "warrior")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        monster_id = self.game.active_encounter["monster_id"]
        original_hp = self.game.data.monsters[monster_id]["hp"]
        self.game.data.monsters[monster_id]["hp"] = 1
        try:
            with patch.object(self.game, "_award_victory", side_effect=RuntimeError("forced reward failure")):
                with self.assertRaises(RuntimeError):
                    self.game.resolve_encounter(opened.data["encounter_id"])
        finally:
            self.game.data.monsters[monster_id]["hp"] = original_hp
        # A failed atomic write no longer abandons a live battle after
        # reward transaction. It restores the last committed checkpoint so the
        # daemon/owner can retry safely without partial rewards.
        self.assertIsNotNone(self.game.active_encounter)
        self.assertEqual(self.game.active_encounter["id"], opened.data["encounter_id"])
        self.assertIn("1", self.game.encounter_roster)

    def test_shiva_overdue_encounter_status_is_read_only(self):
        self.game.choose_job("1", "warrior")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        self.game.active_encounter["closes_at"] = time.time() - 1
        before = dict(self.game.active_encounter)
        status = self.game.encounter_status()
        self.assertTrue(status.ok, status.messages)
        self.assertIn("RALLY CLOSED", status.messages[0])
        self.assertEqual(self.game.active_encounter.get("state"), "rally")
        self.assertEqual(self.game.active_encounter["id"], before["id"])
        self.assertNotIn("round", self.game.active_encounter)

    def test_shiva_late_join_does_not_start_overdue_encounter(self):
        self.game.choose_job("1", "warrior")
        self.game.recruit("2", "aeris", "Aeris")
        self.game.choose_job("2", "whitemage")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        self.game.active_encounter["closes_at"] = time.time() - 0.01
        joined = self.game.join_encounter("2", bypass_cooldown=True)
        self.assertFalse(joined.ok)
        self.assertIn("timer has closed", joined.messages[0])
        self.assertEqual(self.game.active_encounter.get("state"), "rally")
        self.assertNotIn("2", self.game.encounter_roster)

    def test_shiva_venture_after_rally_deadline_does_not_start_combat(self):
        self.game.choose_job("1", "warrior")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        self.game.active_encounter["closes_at"] = time.time() - 0.01
        result = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(result.ok)
        self.assertIn("RALLY CLOSED", result.messages[0])
        self.assertEqual(self.game.active_encounter.get("state"), "rally")

    def test_v4_1_owner_abort_helper_clears_encounter(self):
        self.game.choose_job("1", "warrior")
        self.assertTrue(self.game.venture("1", bypass_cooldown=True).ok)
        cleared = self.game.abort_encounter()
        self.assertTrue(cleared.ok)
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})

    def test_v4_job_assignment_initializes_full_hp(self):
        self.assertTrue(self.game.choose_job("1", "warrior").ok)
        p = self.game._player("1")
        self.assertGreater(p["current_hp"], 0)
        self.assertEqual(p["current_hp"], self.game._max_hp(p))

    def test_v4_random_encounter_is_joinable_and_resolves_as_party(self):
        self.game.choose_job("1", "warrior")
        self.game.recruit("2", "aeris", "Aeris")
        self.game.choose_job("2", "whitemage")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        self.assertTrue(opened.data.get("encounter_started"))
        self.assertEqual(len(self.game.encounter_roster), 1)
        joined = self.game.join_encounter("2", bypass_cooldown=True)
        self.assertTrue(joined.ok, joined.messages)
        self.assertEqual(len(self.game.encounter_roster), 2)
        monster_id = self.game.active_encounter["monster_id"]
        base_hp = self.game.data.monsters[monster_id]["hp"]
        original_hp = base_hp
        self.game.data.monsters[monster_id]["hp"] = 1
        try:
            result = self.game.resolve_encounter(opened.data["encounter_id"])
        finally:
            self.game.data.monsters[monster_id]["hp"] = original_hp
        self.assertTrue(result.ok, result.messages)
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(len(self.game.encounter_roster), 0)
        self.assertGreaterEqual(self.db.one("SELECT party_encounters FROM players WHERE twitch_id='1'")["party_encounters"], 1)
        self.assertGreaterEqual(self.db.one("SELECT party_encounters FROM players WHERE twitch_id='2'")["party_encounters"], 1)

    def test_v4_party_scaling_increases_monster_hp(self):
        self.game.choose_job("1", "warrior")
        self.game.recruit("2", "cloud", "Cloud")
        self.game.choose_job("2", "warrior")
        monster = dict(self.game.data.monsters["goblin"])
        battle = self.game._party_battle({"1":{"name":"Van"},"2":{"name":"Cloud"}}, monster)
        self.assertGreater(battle["monster_max_hp"], monster["hp"])

    def test_v4_camp_rest_blocks_activity_and_heals_after_offline_timer(self):
        self.game.choose_job("1", "warrior")
        p = self.game._player("1")
        max_hp = self.game._max_hp(p)
        self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='1'")
        rested = self.game.rest("1", stream_live=False)
        self.assertTrue(rested.ok, rested.messages)
        row = self.game._player("1")
        remaining = row["camp_until"] - int(time.time())
        self.assertGreaterEqual(remaining, 3598)
        self.assertLessEqual(remaining, 3600)
        blocked = self.game.venture("1", bypass_cooldown=True)
        self.assertFalse(blocked.ok)
        self.assertIn("resting at camp", blocked.messages[0])
        self.db.execute("UPDATE players SET camp_until=? WHERE twitch_id='1'", (int(time.time()) - 1,))
        completed = self.game.rest("1")
        self.assertTrue(completed.ok)
        self.assertEqual(self.game._player("1")["current_hp"], max_hp)
        self.assertEqual(self.game._player("1")["camp_until"], 0)

    def test_v4_camp_uses_shorter_online_timer(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='1'")
        result = self.game.rest("1", stream_live=True)
        self.assertTrue(result.ok, result.messages)
        remaining = int(self.game._player("1")["camp_until"]) - int(time.time())
        self.assertGreaterEqual(remaining, 898)
        self.assertLessEqual(remaining, 900)
        self.assertIn("15m", result.messages[0])

    def test_v4_tent_is_instant_full_recovery(self):
        self.game.choose_job("1", "warrior")
        self.game._change_item("1", "tent", 1, "test")
        max_hp = self.game._max_hp(self.game._player("1"))
        self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='1'")
        result = self.game.use_item("1", "tent")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game._player("1")["current_hp"], max_hp)
        self.assertEqual(self.game._inventory_qty("1", "tent"), 0)

    def test_v4_ko_hero_can_recover_at_camp(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET current_hp=0 WHERE twitch_id='1'")
        blocked = self.game.venture("1", bypass_cooldown=True)
        self.assertFalse(blocked.ok)
        self.assertIn("KO'd", blocked.messages[0])
        self.assertTrue(self.game.rest("1").ok)

    def test_v4_tent_and_new_achievement_references(self):
        self.assertIn("tent", self.game.data.items)
        self.assertTrue(self.game.data.items["tent"].get("shop"))
        self.assertIn("happy_camper", self.game.data.achievements)
        self.assertIn("certified_tent_inspector", self.game.data.titles)
        self.assertIn("party_people", self.game.data.achievements)
        self.assertIn("strength_in_numbers", self.game.data.titles)

    def test_v4_bosses_have_phase_and_enrage_profiles(self):
        for boss in self.game.data.bosses.values():
            self.assertGreaterEqual(len(boss.get("phases", [])), 3)
            self.assertGreater(boss.get("enrage_round", 0), 0)
            self.assertGreater(boss.get("attacks_per_round", 0), 0)

    def test_v4_live_raid_starts_in_rally_and_advances_rounds(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET level=60 WHERE twitch_id='1'")
        # Re-select to synchronize HP to the new level.
        self.game.choose_job("1", "warrior")
        spawned = self.game.spawn_boss("ifrit")
        self.assertTrue(spawned.ok)
        self.assertEqual(self.game.active_boss["state"], "rally")
        self.assertTrue(self.game.raid_join("1").ok)
        self.assertTrue(self.game.start_raid().ok)
        before = self.game.active_boss["current_hp"]
        result = self.game.raid_round()
        self.assertTrue(result.ok, result.messages)
        if self.game.active_boss:
            self.assertLess(self.game.active_boss["current_hp"], before)
            self.assertEqual(self.game.active_boss["round"], 1)

    def test_hotfix3_raid_accepts_and_resolves_queued_ability(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET level=60 WHERE twitch_id='1'")
        self.game.choose_job("1", "warrior")
        self.game.spawn_boss("ifrit")
        self.game.raid_join("1")
        self.game.start_raid()
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999
        self.game.active_boss["attacks_per_round"] = 0
        before_ap = self.game.raid_roster["1"]["ap"]

        queued = self.game.battle_ability("1", "Power Break")
        self.assertTrue(queued.ok, queued.messages)
        self.assertIn("RAID QUEUED R1", queued.messages[0])
        self.assertEqual(self.game.raid_roster["1"]["action"]["ability_id"], "power_break")

        resolved = self.game.raid_round()
        self.assertTrue(resolved.ok, resolved.messages)
        self.assertLess(self.game.raid_roster["1"]["ap"], before_ap)
        self.assertIsNone(self.game.raid_roster["1"]["action"])
        self.assertTrue(any("Power Break" in line for line in resolved.messages))
        self.assertIn("weaken", self.game.active_boss.get("statuses", {}))

    def test_hotfix3_recovered_legacy_raid_hydrates_before_accepting_actions(self):
        self.game.choose_job("1", "warrior")
        self.game.spawn_boss("ifrit")
        self.game.raid_join("1")
        self.game.start_raid()
        meta = self.game.raid_roster["1"]
        for key in ("stats", "effects", "job_level", "mp", "max_mp", "ap", "max_ap"):
            meta.pop(key, None)

        queued = self.game.battle_attack("1")
        self.assertTrue(queued.ok, queued.messages)
        self.assertIn("stats", self.game.raid_roster["1"])
        self.assertIn("effects", self.game.raid_roster["1"])
        self.assertEqual(self.game.raid_roster["1"]["action"]["kind"], "attack")

    def test_hotfix3_raid_use_queues_and_consumes_item_on_resolution(self):
        self.game.choose_job("1", "warrior")
        self.game._change_item("1", "potion", 1, "test")
        self.game.spawn_boss("ifrit")
        self.game.raid_join("1")
        self.game.start_raid()
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999
        self.game.active_boss["attacks_per_round"] = 0
        meta = self.game.raid_roster["1"]
        meta["hp"] = max(1, int(meta["max_hp"]) - 60)
        self.game._save_hp("1", meta["hp"])
        before_qty = self.game._inventory_qty("1", "potion")
        before_hp = meta["hp"]

        queued = self.game.use_item("1", "Potion")
        self.assertTrue(queued.ok, queued.messages)
        self.assertIn("RAID QUEUED R1", queued.messages[0])
        self.assertEqual(meta["action"]["kind"], "item")

        resolved = self.game.raid_round()
        self.assertTrue(resolved.ok, resolved.messages)
        self.assertEqual(self.game._inventory_qty("1", "potion"), before_qty - 1)
        self.assertGreater(meta["hp"], before_hp)
        self.assertIsNone(meta["action"])
        self.assertTrue(any("Potion" in line for line in resolved.messages))

    def test_hotfix3_raid_killing_ability_persists_resource_spend(self):
        self.game.choose_job("1", "warrior")
        self.game.spawn_boss("ifrit")
        self.game.raid_join("1")
        self.game.start_raid()
        self.game.active_boss["attacks_per_round"] = 0
        before_ap = int(self.game.raid_roster["1"]["ap"])
        queued = self.game.battle_ability("1", "Power Break")
        self.assertTrue(queued.ok, queued.messages)
        cost = int(self.game.raid_roster["1"]["action"]["cost"])
        self.game.active_boss["current_hp"] = 1
        self.game.active_boss["max_hp"] = 1

        resolved = self.game.raid_round()
        self.assertTrue(resolved.ok, resolved.messages)
        self.assertTrue(resolved.data.get("raid_finished"))
        self.assertIsNone(self.game.active_boss)
        self.assertEqual(int(self.game._player("1")["current_ap"]), before_ap - cost)

    def test_hotfix3_raid_defend_is_a_real_round_action(self):
        self.game.choose_job("1", "warrior")
        self.game.spawn_boss("ifrit")
        self.game.raid_join("1")
        self.game.start_raid()
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999
        self.game.active_boss["attacks_per_round"] = 0
        queued = self.game.battle_defend("1")
        self.assertTrue(queued.ok, queued.messages)
        self.assertEqual(self.game.raid_roster["1"]["action"]["kind"], "defend")
        resolved = self.game.raid_round()
        self.assertTrue(resolved.ok, resolved.messages)
        self.assertGreaterEqual(self.game.raid_roster["1"]["defends"], 1)
        self.assertIsNone(self.game.raid_roster["1"]["action"])
        self.assertTrue(any("Defends" in line for line in resolved.messages))

    def test_v4_limit_break_can_be_armed_and_used(self):
        self.game.choose_job("1", "warrior")
        self.db.execute("UPDATE players SET level=80 WHERE twitch_id='1'")
        self.game.choose_job("1", "warrior")
        self.game.spawn_boss("ifrit")
        self.game.raid_join("1")
        self.game.start_raid()
        self.game.raid_roster["1"]["limit"] = 100
        armed = self.game.limit_break("1")
        self.assertTrue(armed.ok, armed.messages)
        self.assertTrue(self.game.raid_roster["1"]["limit_armed"])
        self.game.active_boss["current_hp"] = 999999
        self.game.active_boss["max_hp"] = 999999
        self.game.raid_round()
        self.assertGreaterEqual(self.db.one("SELECT limit_breaks FROM players WHERE twitch_id='1'")["limit_breaks"], 1)

    def test_v4_raid_revive_consumes_phoenix_down(self):
        self.game.choose_job("1", "warrior")
        self.game.recruit("2", "aeris", "Aeris")
        self.game.choose_job("2", "whitemage")
        self.game._change_item("1", "phoenix_down", 1, "test")
        self.game.spawn_boss("ifrit")
        self.game.raid_join("1")
        self.game.raid_join("2")
        self.game.start_raid()
        self.game.raid_roster["2"]["hp"] = 0
        self.game._save_hp("2", 0)
        result = self.game.revive_raid("1", "Aeris")
        self.assertTrue(result.ok, result.messages)
        self.assertGreater(self.game.raid_roster["2"]["hp"], 0)
        self.assertEqual(self.db.one("SELECT raid_revives FROM players WHERE twitch_id='1'")["raid_revives"], 1)

    def test_v4_boss_clear_record_and_overlay_state(self):
        self.game.choose_job("1", "warrior")
        spawned = self.game.spawn_boss("bomb king")
        self.assertTrue(spawned.ok)
        self.assertTrue(Path(self.tmp.name, "overlay.json").exists())
        self.game.active_boss["current_hp"] = 1
        self.game.active_boss["max_hp"] = 1
        self.game.raid_join("1")
        result = self.game.resolve_boss()
        self.assertTrue(result.ok)
        clear = self.db.one("SELECT clears FROM player_boss_clears WHERE player_id='1' AND boss_id='bomb_king'")
        self.assertIsNotNone(clear)
        self.assertGreaterEqual(clear["clears"], 1)

    def test_new_raid_achievement_references(self):
        self.assertIn("battlefield_medic", self.game.data.achievements)
        self.assertIn("phoenix_wrangler", self.game.data.titles)
        self.assertIn("breaking_limits", self.game.data.achievements)
        self.assertIn("limit_break_enthusiast", self.game.data.titles)

    def test_shared_summon_gauge_can_arm_eidolon(self):
        self.game.choose_job("1", "warrior")
        self.game.spawn_boss("ifrit")
        self.game.raid_join("1")
        self.game.start_raid()
        self.game.active_boss["summon_gauge"] = 100
        result = self.game.summon_raid("1", "Shiva")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(self.game.active_boss["summon_gauge"], 0)
        self.assertEqual(self.game.active_boss["summon_armed"]["id"], "shiva")

    def test_bahamut_requires_summoner_or_sage(self):
        self.game.choose_job("1", "warrior")
        self.game.spawn_boss("ifrit")
        self.game.raid_join("1")
        self.game.start_raid()
        self.game.active_boss["summon_gauge"] = 100
        result = self.game.summon_raid("1", "Bahamut")
        self.assertFalse(result.ok)
        self.assertIn("Summoner or Sage", result.messages[0])

    def test_daemon_wait_targets_the_actual_encounter_deadline(self):
        self.game.choose_job("1", "warrior")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        self.game.active_encounter["closes_at"] = time.time() + 0.12
        daemon = EncounterDaemon(self.game, lambda result: None, poll_interval=0.75)
        timeout = daemon._wait_timeout(self.game.combat_snapshot())
        self.assertGreater(timeout, 0)
        self.assertLess(timeout, 0.20)
        self.assertLess(timeout, daemon.poll_interval)

    def test_shiva_daemon_does_not_start_rally_before_deadline(self):
        self.game.choose_job("1", "warrior")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        deadline = time.time() + 0.12
        self.game.active_encounter["closes_at"] = deadline
        notices = []
        started_at = []
        started = threading.Event()

        def notify(result):
            notices.append(result)
            if result.data.get("battle_started"):
                started_at.append(time.time())
                started.set()

        daemon = EncounterDaemon(self.game, notify, poll_interval=0.75)
        try:
            daemon.start()
            time.sleep(0.05)
            self.assertEqual(self.game.active_encounter.get("state"), "rally")
            self.assertTrue(started.wait(timeout=1.0), "daemon never started the rally")
        finally:
            daemon.stop()

        self.assertGreaterEqual(started_at[0] + 0.01, deadline)
        self.assertEqual(self.game.active_encounter.get("state"), "combat")
        self.assertEqual(daemon.status()["last_deadline"], "encounter-rally")

    def test_v4_5_daemon_advances_quiet_active_battle_without_followup_commands(self):
        self.game.choose_job("1", "warrior")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        monster_id = self.game.active_encounter["monster_id"]
        original_hp = self.game.data.monsters[monster_id]["hp"]
        self.game.data.monsters[monster_id]["hp"] = 1
        self.game.encounter_round_seconds = 0.05
        self.game.active_encounter["closes_at"] = time.time() + 0.05
        received = []
        finished = threading.Event()

        def notify(result):
            received.append(result)
            if result.data.get("encounter_finished"):
                finished.set()

        daemon = EncounterDaemon(self.game, notify, poll_interval=0.02)
        try:
            daemon.start()
            self.assertTrue(finished.wait(timeout=2.0), "daemon never completed the quiet Active Battle")
        finally:
            daemon.stop()
            self.game.data.monsters[monster_id]["hp"] = original_hp

        self.assertTrue(any(r.data.get("battle_started") for r in received))
        self.assertTrue(any(r.data.get("encounter_finished") for r in received))
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(daemon.last_resolved_id, opened.data["encounter_id"])

    def test_v4_5_notification_failure_cannot_keep_finished_active_battle_stuck(self):
        self.game.choose_job("1", "warrior")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        monster_id = self.game.active_encounter["monster_id"]
        original_hp = self.game.data.monsters[monster_id]["hp"]
        self.game.data.monsters[monster_id]["hp"] = 1
        self.game.encounter_round_seconds = 0.05
        self.game.active_encounter["closes_at"] = time.time() + 0.05
        finished = threading.Event()

        def broken_notify(result):
            if result.data.get("encounter_finished"):
                finished.set()
            raise RuntimeError("simulated Twitch outage")

        daemon = EncounterDaemon(self.game, broken_notify, poll_interval=0.02)
        try:
            daemon.start()
            self.assertTrue(finished.wait(timeout=2.0))
        finally:
            daemon.stop()
            self.game.data.monsters[monster_id]["hp"] = original_hp

        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})
        self.assertIn("notify RuntimeError", daemon.last_error or "")


    def test_v4_5_direct_sender_uses_twitch_helix_chat_endpoint(self):
        calls = []

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def read(self):
                return self.payload

        def fake_urlopen(request, timeout=0):
            calls.append(request)
            if "id.twitch.tv/oauth2/token" in request.full_url:
                return FakeResponse(b'{"access_token":"app-token","expires_in":3600}')
            self.assertEqual(request.full_url, "https://api.twitch.tv/helix/chat/messages")
            self.assertEqual(request.headers.get("Client-id"), "cid")
            self.assertEqual(request.headers.get("Authorization"), "Bearer app-token")
            body = request.data.decode("utf-8")
            self.assertIn('"broadcaster_id": "owner"', body)
            self.assertIn('"sender_id": "bot"', body)
            self.assertIn('"message": "hello"', body)
            return FakeResponse(b'{"data":[{"message_id":"1","is_sent":true}]}')

        sender = TwitchRESTChatSender("cid", "secret", "bot", "owner")
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            sender.send("hello")

        self.assertEqual(len(calls), 2)


    def test_v5_database_uses_wal_and_busy_timeout(self):
        self.assertTrue(self.db.health_check())
        self.assertEqual(self.db.one("PRAGMA journal_mode")[0].lower(), "wal")
        self.assertGreaterEqual(int(self.db.one("PRAGMA busy_timeout")[0]), 10000)

    def test_v5_database_close_is_idempotent(self):
        extra = Database(Path(self.tmp.name) / "close-test.db")
        self.assertTrue(extra.health_check())
        extra.close()
        extra.close()
        self.assertFalse(extra.health_check())

    def test_v5_game_data_startup_validation(self):
        data = GameData(ROOT / "data")
        self.assertEqual(data.validate(), [])
        region = data.regions["greenwind_plains"]
        original = region["encounters"][0]["monster_id"]
        region["encounters"][0]["monster_id"] = "definitely_missing"
        try:
            errors = data.validate()
            self.assertTrue(any("definitely_missing" in error for error in errors))
            with self.assertRaises(ValueError):
                data.validate_or_raise()
        finally:
            region["encounters"][0]["monster_id"] = original

    def test_v5_combat_snapshot_is_isolated_copy(self):
        self.game.choose_job("1", "warrior")
        self.game.venture("1", bypass_cooldown=True)
        snapshot = self.game.combat_snapshot()
        snapshot["encounter"]["monster_id"] = "changed"
        self.assertNotEqual(self.game.active_encounter["monster_id"], "changed")

    def test_v5_concurrent_encounter_resolution_only_awards_once(self):
        self.game.choose_job("1", "warrior")
        opened = self.game.venture("1", bypass_cooldown=True)
        encounter_id = opened.data["encounter_id"]
        monster_id = self.game.active_encounter["monster_id"]
        original_hp = self.game.data.monsters[monster_id]["hp"]
        self.game.data.monsters[monster_id]["hp"] = 1
        results = []
        barrier = threading.Barrier(3)

        def worker():
            barrier.wait()
            results.append(self.game.resolve_encounter(encounter_id))

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        try:
            t1.start(); t2.start(); barrier.wait(); t1.join(); t2.join()
        finally:
            self.game.data.monsters[monster_id]["hp"] = original_hp
        self.assertEqual(sum(1 for r in results if r.ok), 1)
        self.assertEqual(self.db.one("SELECT monsters_defeated FROM players WHERE twitch_id='1'")["monsters_defeated"], 1)
        self.assertIsNone(self.game.active_encounter)

    def test_v5_direct_sender_detects_twitch_drop_reason(self):
        class FakeResponse:
            def __init__(self, payload): self.payload = payload
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return self.payload

        responses = [
            FakeResponse(b'{"access_token":"app-token","expires_in":3600}'),
            FakeResponse(b'{"data":[{"message_id":"","is_sent":false,"drop_reason":{"code":"automod_held","message":"held"}}]}'),
        ]
        sender = TwitchRESTChatSender("cid", "secret", "bot", "owner", max_attempts=1)
        with patch("urllib.request.urlopen", side_effect=lambda *a, **k: responses.pop(0)):
            with self.assertRaises(TwitchChatDeliveryError):
                sender.send("hello")

    def test_v5_token_request_does_not_put_client_secret_in_url(self):
        calls = []
        class FakeResponse:
            def __init__(self, payload): self.payload = payload
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return self.payload
        def fake_urlopen(request, timeout=0):
            calls.append(request)
            if request.full_url == "https://id.twitch.tv/oauth2/token":
                self.assertNotIn("secret", request.full_url)
                self.assertIn(b"client_secret=secret", request.data)
                return FakeResponse(b'{"access_token":"app-token","expires_in":3600}')
            return FakeResponse(b'{"data":[{"message_id":"1","is_sent":true}]}')
        sender = TwitchRESTChatSender("cid", "secret", "bot", "owner")
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            sender.send("hello")
        self.assertEqual(len(calls), 2)

    def test_v5_notification_dispatcher_is_nonblocking(self):
        delivered = threading.Event()
        class SlowSender:
            def send_result(self, result):
                time.sleep(0.15)
                delivered.set()
        dispatcher = NotificationDispatcher(SlowSender())
        dispatcher.start()
        try:
            started = time.monotonic()
            dispatcher.enqueue(self.game.hero("1"))
            elapsed = time.monotonic() - started
            self.assertLess(elapsed, 0.05)
            self.assertTrue(delivered.wait(timeout=1.0))
            self.assertEqual(dispatcher.status()["sent_batches"], 1)
        finally:
            dispatcher.stop()

    def test_v5_packed_messages_reduce_network_calls(self):
        packed = _packed_messages(["alpha", "beta", "gamma"], max_length=50, max_messages=4)
        self.assertEqual(packed, ["alpha | beta | gamma"])
        self.assertTrue(all(len(message) <= 50 for message in packed))

    def test_v5_daemon_starts_and_advances_raid_without_chat(self):
        self.game.choose_job("1", "warrior")
        spawned = self.game.spawn_boss("bomb king")
        self.assertTrue(spawned.ok)
        self.assertTrue(self.game.raid_join("1").ok)
        with self.game._state_lock:
            self.game.active_boss["closes_at"] = time.time() + 0.05
        notices = []
        daemon = EncounterDaemon(self.game, notices.append, poll_interval=0.02)
        daemon.start()
        try:
            deadline = time.time() + 1.0
            while time.time() < deadline:
                snap = self.game.combat_snapshot()
                if snap["boss"] and snap["boss"]["state"] == "combat":
                    break
                time.sleep(0.01)
            self.assertEqual(self.game.combat_snapshot()["boss"]["state"], "combat")
            with self.game._state_lock:
                self.game.active_boss["next_round_at"] = time.time() + 0.05
            deadline = time.time() + 1.0
            while time.time() < deadline:
                boss = self.game.combat_snapshot()["boss"]
                if boss is None or int(boss.get("round", 0)) >= 1:
                    break
                time.sleep(0.01)
            boss = self.game.combat_snapshot()["boss"]
            self.assertTrue(boss is None or int(boss.get("round", 0)) >= 1)
            self.assertGreaterEqual(len(notices), 2)
        finally:
            daemon.stop()



    def test_v5_settings_reject_non_numeric_twitch_ids(self):
        env = {
            "TWITCH_CLIENT_ID": "cid", "TWITCH_CLIENT_SECRET": "secret",
            "TWITCH_BOT_ID": "botname", "TWITCH_OWNER_ID": "123",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError):
                Settings.from_env()

    def test_v5_settings_reject_invalid_timers(self):
        env = {
            "TWITCH_CLIENT_ID": "cid", "TWITCH_CLIENT_SECRET": "secret",
            "TWITCH_BOT_ID": "123", "TWITCH_OWNER_ID": "456",
            "ENCOUNTER_JOIN_SECONDS": "oops",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError):
                Settings.from_env()



    def test_v081_next_guides_unassigned_hero_to_job(self):
        result = self.game.next_step("1")
        self.assertTrue(result.ok)
        self.assertIn("Choose your first Job", result.messages[0])

    def test_v081_next_guides_new_job_to_activity(self):
        self.game.choose_job("1", "warrior")
        result = self.game.next_step("1")
        self.assertTrue(result.ok)
        self.assertTrue(any(word in result.messages[0] for word in ("Hunt", "adventuring", "rally")))

    def test_v081_inventory_filters_consumables(self):
        self.game._change_item("1", "iron_ore", 2, "test")
        result = self.game.inventory("1", "consumable")
        self.assertTrue(result.ok)
        text = " ".join(result.messages)
        self.assertIn("Potion", text)
        self.assertNotIn("Iron Ore", text)

    def test_v081_inventory_rejects_unknown_filter(self):
        result = self.game.inventory("1", "banana")
        self.assertFalse(result.ok)
        self.assertIn("filter", result.messages[0].lower())

    def test_v081_gear_reports_active_stats(self):
        self.game.choose_job("1", "warrior")
        result = self.game.gear("1")
        self.assertTrue(result.ok)
        self.assertTrue(any("Active Stats" in message for message in result.messages))


if __name__ == "__main__":
    unittest.main()

# Shop rotation expansion regression tests are attached dynamically below so the
# existing test class remains grouped with the original engine regression coverage.
def _test_v6_shop_stock_is_persistent_and_job_appropriate(self):
    self.assertTrue(self.game.choose_job("1", "warrior").ok)
    self.db.execute("UPDATE players SET level=35,gil=999999 WHERE twitch_id='1'")
    first = self.game.shop("1")
    second = self.game.shop("1")
    self.assertTrue(first.ok)
    self.assertEqual(first.data["stock"], second.data["stock"])
    self.assertGreaterEqual(len(first.data["stock"]), 7)
    for item_id in first.data["stock"]:
        item = self.game.data.items[item_id]
        if item["type"] in {"weapon", "armor", "accessory"} and item.get("allowed_jobs"):
            self.assertIn("warrior", item["allowed_jobs"])


def _test_v6_job_change_invalidates_personal_shop(self):
    self.game.choose_job("1", "warrior")
    self.db.execute("UPDATE players SET level=35,gil=999999 WHERE twitch_id='1'")
    warrior_stock = self.game.shop("1").data["stock"]
    # White Mage is a starter Job and therefore can be selected immediately.
    self.assertTrue(self.game.choose_job("1", "whitemage").ok)
    white_stock = self.game.shop("1").data["stock"]
    self.assertNotEqual(warrior_stock, white_stock)
    for item_id in white_stock:
        item = self.game.data.items[item_id]
        if item["type"] in {"weapon", "armor", "accessory"} and item.get("allowed_jobs"):
            self.assertIn("whitemage", item["allowed_jobs"])


def _test_v6_buy_only_accepts_current_rotation_and_slot_numbers(self):
    self.game.choose_job("1", "warrior")
    self.db.execute("UPDATE players SET level=35,gil=999999 WHERE twitch_id='1'")
    shop = self.game.shop("1")
    stock = [self.game.data.items[item_id] for item_id in shop.data["stock"]]
    gear_slot = next(i + 1 for i, item in enumerate(stock) if item["type"] in {"weapon", "armor", "accessory"})
    gear = stock[gear_slot - 1]
    bought = self.game.buy("1", str(gear_slot), 1)
    self.assertTrue(bought.ok, bought.messages)
    self.assertGreaterEqual(self.game._inventory_qty("1", gear["id"]), 1)
    off_job = next(
        item for item in self.game.data.items.values()
        if item.get("shop") and item.get("allowed_jobs") and "warrior" not in item["allowed_jobs"]
    )
    rejected = self.game.buy("1", off_job["name"], 1)
    self.assertFalse(rejected.ok)
    self.assertIn("current", rejected.messages[0].lower())


def _test_v6_shop_expansion_has_broad_job_gear_coverage(self):
    shop_gear = [
        item for item in self.game.data.items.values()
        if item.get("shop") and item["type"] in {"weapon", "armor"}
    ]
    self.assertGreaterEqual(len(shop_gear), 80)
    for job_id in self.game.data.jobs:
        weapons = [
            item for item in shop_gear
            if item["type"] == "weapon" and job_id in item.get("allowed_jobs", [])
        ]
        armors = [
            item for item in shop_gear
            if item["type"] == "armor" and job_id in item.get("allowed_jobs", [])
        ]
        self.assertGreaterEqual(len(weapons), 3, job_id)
        self.assertGreaterEqual(len(armors), 3, job_id)


EngineTests.test_v6_shop_stock_is_persistent_and_job_appropriate = _test_v6_shop_stock_is_persistent_and_job_appropriate
EngineTests.test_v6_job_change_invalidates_personal_shop = _test_v6_job_change_invalidates_personal_shop
EngineTests.test_v6_buy_only_accepts_current_rotation_and_slot_numbers = _test_v6_buy_only_accepts_current_rotation_and_slot_numbers
EngineTests.test_v6_shop_expansion_has_broad_job_gear_coverage = _test_v6_shop_expansion_has_broad_job_gear_coverage

class H9FieldSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "h9.db")
        self.game = CrystalGuildEngine(self.db, GameData(ROOT / "data"), venture_cooldown_seconds=0, overlay_state_path=str(Path(self.tmp.name) / "overlay.json"), rng=random.Random(11))
        self.game.recruit("1", "van", "Van")
        self.game.recruit("2", "cloud", "Cloud")
        self.game.choose_job("1", "warrior")
        self.game.choose_job("2", "warrior")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_h9_requested_combat_timer_defaults(self):
        self.assertEqual(self.game.encounter_join_seconds, 60)
        self.assertEqual(self.game.encounter_round_seconds, 30)
        self.assertEqual(self.game.raid_join_seconds, 90)
        self.assertEqual(self.game.raid_round_seconds, 60)

    def test_h9_field_item_can_support_other_player_while_live(self):
        self.game._change_item("1", "potion", 1, "test")
        target_max = self.game._max_hp(self.game._player("2"))
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='2'", (max(1, target_max - 25),))
        before_qty = self.game._inventory_qty("1", "potion")
        result = self.game.use_item("1", "potion", target_query="cloud", stream_live=True)
        self.assertTrue(result.ok, result.messages)
        self.assertIn("on Cloud", result.messages[0])
        self.assertGreater(int(self.game._player("2")["current_hp"]), max(1, target_max - 25))
        self.assertEqual(self.game._inventory_qty("1", "potion"), before_qty - 1)

    def test_h9_field_item_other_player_fails_closed_while_offline(self):
        self.game._change_item("1", "potion", 1, "test")
        target_max = self.game._max_hp(self.game._player("2"))
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='2'", (max(1, target_max - 25),))
        before_qty = self.game._inventory_qty("1", "potion")
        before_hp = int(self.game._player("2")["current_hp"])
        result = self.game.use_item("1", "potion", target_query="cloud", stream_live=False)
        self.assertFalse(result.ok)
        self.assertIn("only while the stream is LIVE", result.messages[0])
        self.assertEqual(self.game._inventory_qty("1", "potion"), before_qty)
        self.assertEqual(int(self.game._player("2")["current_hp"]), before_hp)

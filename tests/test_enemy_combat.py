from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.active_battle import apply_status
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.enemy_combat import choose_enemy_action, effective_special_chance
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class EnemyCombatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "enemy-combat.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            venture_cooldown_seconds=0, venture_treasure_chance=0.0,
            encounter_join_seconds=5,
            encounter_round_seconds=5,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(29),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")
        # Ordinary combat tests must not be replaced by a calendar-active event.
        # Seasonal replacement is exercised in its dedicated integration suite.
        self.game._roll_seasonal_venture_variant = lambda **_kwargs: None

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def start_monster(self, monster_id: str):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        self.game.active_encounter["monster_id"] = monster_id
        started = self.game.start_encounter_battle(opened.data["encounter_id"])
        self.assertTrue(started.ok)
        return opened

    def test_shipping_enemy_catalog_covers_every_monster(self):
        self.data.validate_or_raise()
        self.assertEqual(set(self.data.monsters), set(self.data.enemy_actions))
        self.assertGreaterEqual(len(self.data.enemy_profiles), 6)
        self.assertGreaterEqual(
            sum(bool(row.get("ability")) for row in self.data.enemy_actions.values()),
            90,
        )

    def test_all_named_enemy_skills_resolve_through_generic_engine_path(self):
        self.start_monster("goblin")
        actor = self.game.encounter_roster["1"]
        resolved = 0
        for monster_id, behavior in self.data.enemy_actions.items():
            ability = behavior.get("ability")
            if not ability:
                continue
            monster = self.data.monsters[monster_id]
            actor["hp"] = actor["max_hp"]
            actor["statuses"] = {}
            actor["defending"] = False
            self.game.active_encounter["monster_hp"] = 10000
            self.game.active_encounter["monster_max_hp"] = 10000
            self.game.active_encounter["monster_statuses"] = {}
            log: list[str] = []
            try:
                self.game._resolve_enemy_special(
                    monster,
                    self.data.enemy_profiles[behavior["profile"]],
                    ability,
                    log,
                )
            except Exception as exc:  # pragma: no cover - assertion context matters
                self.fail(f"{monster_id}/{ability.get('name')} failed generic resolution: {exc}")
            self.assertTrue(log, f"{monster_id}/{ability.get('name')} produced no combat log")
            resolved += 1
        self.assertGreaterEqual(resolved, 90)

    def test_legacy_monster_specials_remain_available_for_non_active_resolvers(self):
        malboro = self.data.monsters["malboro"]
        self.assertEqual(malboro["special"]["name"], "Bad Breath")
        self.assertIn("multiplier", malboro["special"])
        active = self.data.enemy_actions["malboro"]["ability"]
        self.assertEqual(active["name"], "Bad Breath")
        self.assertIn("effects", active)

    def test_controller_profile_increases_but_caps_special_frequency(self):
        ability = {"chance": 0.40}
        profile = {"ability_bias": 2.0}
        self.assertEqual(effective_special_chance(ability, profile), 0.45)

    def test_basic_enemy_response_targets_only_one_party_member(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.game.recruit("2", "cloud", "Cloud")
        self.game.choose_job("2", "warrior")
        self.game.recruit("3", "aeris", "Aeris")
        self.game.choose_job("3", "whitemage")
        self.game.recruit("4", "zidane", "Zidane")
        self.game.choose_job("4", "thief")
        for pid in ("2", "3", "4"):
            self.assertTrue(self.game.join_encounter(pid, bypass_cooldown=True).ok)
        self.game.active_encounter["monster_id"] = "goblin"  # no named Active Skill
        self.assertTrue(self.game.start_encounter_battle(opened.data["encounter_id"]).ok)
        before = {pid: row["hp"] for pid, row in self.game.encounter_roster.items()}
        log = []
        self.game._active_enemy_turn(self.data.monsters["goblin"], log)
        damaged = [
            pid for pid, row in self.game.encounter_roster.items()
            if row["hp"] < before[pid]
        ]
        self.assertEqual(len(damaged), 1, log)

    def test_party_enemy_skill_can_still_hit_multiple_targets(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.game.recruit("2", "cloud", "Cloud")
        self.game.choose_job("2", "warrior")
        self.assertTrue(self.game.join_encounter("2", bypass_cooldown=True).ok)
        self.game.active_encounter["monster_id"] = "mandragora"
        self.assertTrue(self.game.start_encounter_battle(opened.data["encounter_id"]).ok)
        behavior = self.data.enemy_actions["mandragora"]
        ability = behavior["ability"]
        self.assertEqual(ability["target"], "party")
        before = {pid: row["hp"] for pid, row in self.game.encounter_roster.items()}
        log = []
        self.game._resolve_enemy_special(
            self.data.monsters["mandragora"],
            self.data.enemy_profiles[behavior["profile"]],
            ability,
            log,
        )
        damaged = [
            pid for pid, row in self.game.encounter_roster.items()
            if row["hp"] < before[pid]
        ]
        self.assertEqual(set(damaged), {"1", "2"}, log)

    def test_special_cooldown_is_round_based(self):
        behavior = {"ability": {"chance": 1.0, "name": "Test"}}
        profile = {"ability_bias": 1.0, "utility": {}}
        rng = random.Random(1)
        waiting = choose_enemy_action(
            behavior,
            profile,
            hp_ratio=1.0,
            round_no=2,
            special_ready_round=3,
            monster_statuses={},
            rng=rng,
        )
        ready = choose_enemy_action(
            behavior,
            profile,
            hp_ratio=1.0,
            round_no=3,
            special_ready_round=3,
            monster_statuses={},
            rng=rng,
        )
        self.assertEqual(waiting["kind"], "attack")
        self.assertEqual(ready["kind"], "special")

    def test_bad_breath_can_damage_and_apply_new_statuses(self):
        self.start_monster("malboro")
        behavior = self.data.enemy_actions["malboro"]
        ability = behavior["ability"]
        # Force every status rider to land for a deterministic resolver test.
        forced = dict(ability)
        forced["effects"] = [
            dict(effect, chance=1.0) if effect.get("type") == "status" else dict(effect)
            for effect in ability["effects"]
        ]
        target = self.game.encounter_roster["1"]
        before = target["hp"]
        log: list[str] = []
        self.game._resolve_enemy_special(
            self.data.monsters["malboro"],
            dict(self.data.enemy_profiles[behavior["profile"]], status_bonus=0.0),
            forced,
            log,
        )
        self.assertLess(target["hp"], before)
        self.assertIn("poison", target["statuses"])
        self.assertIn("weaken", target["statuses"])
        self.assertIn("silence", target["statuses"])
        self.assertTrue(any("Bad Breath" in line for line in log))

    def test_silence_blocks_mp_abilities_but_not_basic_actions(self):
        self.game.choose_job("1", "blackmage")
        self.start_monster("malboro")
        actor = self.game.encounter_roster["1"]
        apply_status(actor["statuses"], "silence", 2)
        ability = self.game.battle_ability("1", "fire")
        attack = self.game.battle_attack("1")
        self.assertFalse(ability.ok)
        self.assertIn("Silenced", ability.messages[0])
        self.assertTrue(attack.ok)

    def test_poison_ticks_at_round_end(self):
        opened = self.start_monster("goblin")
        actor = self.game.encounter_roster["1"]
        actor["hp"] = actor["max_hp"]
        apply_status(actor["statuses"], "poison", 2, 0.05)
        before = actor["hp"]
        # Disable enemy pressure so the exact observed loss is Poison.
        self.game._active_enemy_turn = lambda monster, log: None
        self.game.battle_defend("1")
        self.game.advance_encounter_round(opened.data["encounter_id"])
        if self.game.active_encounter:
            after = self.game.encounter_roster["1"]["hp"]
            self.assertEqual(before - after, max(1, int(actor["max_hp"] * 0.05)))

    def test_status_items_have_specific_item_effects(self):
        self.start_monster("malboro")
        actor = self.game.encounter_roster["1"]
        apply_status(actor["statuses"], "poison", 3, 0.05)
        apply_status(actor["statuses"], "silence", 2)
        apply_status(actor["statuses"], "weaken", 2, 0.10)
        self.game._change_item("1", "antidote", 1, "test")
        self.game._change_item("1", "echo_herbs", 1, "test")
        log: list[str] = []
        self.game._resolve_active_item("1", actor, {"item_id": "antidote", "target_id": "1"}, log)
        self.assertNotIn("poison", actor["statuses"])
        self.assertIn("silence", actor["statuses"])
        self.game._resolve_active_item("1", actor, {"item_id": "echo_herbs", "target_id": "1"}, log)
        self.assertNotIn("silence", actor["statuses"])
        self.assertIn("weaken", actor["statuses"])

    def test_mighty_guard_is_a_real_self_buff_in_active_battle(self):
        self.start_monster("ironclad")
        behavior = self.data.enemy_actions["ironclad"]
        ability = behavior["ability"]
        self.assertEqual(ability["target"], "self")
        log: list[str] = []
        with patch.object(self.game.rng, "random", return_value=0.0):
            self.game._resolve_enemy_special(
                self.data.monsters["ironclad"],
                self.data.enemy_profiles[behavior["profile"]],
                ability,
                log,
            )
        statuses = self.game.active_encounter["monster_statuses"]
        self.assertIn("protect", statuses)
        self.assertIn("power_up", statuses)

    def test_self_destruct_recoil_can_finish_the_enemy(self):
        self.start_monster("bomb")
        behavior = self.data.enemy_actions["bomb"]
        ability = behavior["ability"]
        self.game.active_encounter["monster_hp"] = max(
            1, int(self.game.active_encounter["monster_max_hp"] * 0.20)
        )
        log: list[str] = []
        self.game._resolve_enemy_special(
            self.data.monsters["bomb"],
            self.data.enemy_profiles[behavior["profile"]],
            ability,
            log,
        )
        self.assertEqual(self.game.active_encounter["monster_hp"], 0)
        self.assertTrue(any("recoil" in line for line in log))

    def test_encounter_status_shows_enemy_profile_and_statuses(self):
        self.start_monster("malboro")
        apply_status(self.game.active_encounter["monster_statuses"], "protect", 2, 0.2)
        result = self.game.encounter_status()
        text = " ".join(result.messages)
        self.assertIn("Controller", text)
        self.assertIn("Protect", text)

    def test_defensive_profile_can_choose_utility_when_wounded(self):
        behavior = {"ability": None}
        profile = {
            "utility": {
                "chance": 1.0,
                "hp_below": 0.55,
                "name": "Brace",
                "status": "protect",
                "turns": 2,
                "magnitude": 0.25,
            }
        }
        action = choose_enemy_action(
            behavior,
            profile,
            hp_ratio=0.40,
            round_no=3,
            special_ready_round=1,
            monster_statuses={},
            rng=random.Random(2),
        )
        self.assertEqual(action["kind"], "utility")


if __name__ == "__main__":
    unittest.main()

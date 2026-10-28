from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.active_battle import (
    action_priority,
    apply_status,
    battle_ap,
    battle_mp,
    incoming_vulnerability_multiplier,
    player_outgoing_status_multiplier,
)
from crystal_guild.balance import (
    BATTLE_AP_MAX,
    BATTLE_AP_MIN,
    BATTLE_MP_MAX,
    BATTLE_MP_MIN,
    STUN_RESIST_ROUNDS_AFTER_SUCCESS,
    active_hunt_status_chance,
    defend_mp_restore,
)
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class ZeroRng:
    """Deterministic combat RNG for status/control edge-case tests."""

    def random(self) -> float:
        return 0.0

    def uniform(self, _low: float, _high: float) -> float:
        return 1.0

    def choices(self, population, weights=None, k=1):
        return [population[0]] * k

    def choice(self, sequence):
        return sequence[0]


class CombatBalanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "bahamut.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            venture_cooldown_seconds=0, venture_treasure_chance=0.0,
            encounter_join_seconds=2,
            encounter_round_seconds=2,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(95),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def _start_venture(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        started = self.game.start_encounter_battle(opened.data["encounter_id"])
        self.assertTrue(started.ok)
        self.assertIsNotNone(self.game.active_encounter)
        return opened

    def test_battle_mp_curve_is_bounded_and_no_longer_linear(self):
        early = battle_mp({"mag": 12, "spr": 12})
        veteran = battle_mp({"mag": 180, "spr": 180})
        extreme = battle_mp({"mag": 5000, "spr": 5000})
        self.assertGreaterEqual(early, BATTLE_MP_MIN)
        self.assertLessEqual(early, 18)
        self.assertLess(veteran, 80)
        self.assertEqual(extreme, BATTLE_MP_MAX)
        self.assertLess(early, veteran)

    def test_battle_ap_curve_is_bounded_for_physical_jobs(self):
        early = battle_ap({"str": 12, "dex": 12})
        veteran = battle_ap({"str": 180, "dex": 180})
        extreme = battle_ap({"str": 5000, "dex": 5000})
        self.assertGreaterEqual(early, BATTLE_AP_MIN)
        self.assertLessEqual(early, 18)
        self.assertLess(veteran, 75)
        self.assertEqual(extreme, BATTLE_AP_MAX)

    def test_defend_restores_predictable_fraction_of_bounded_pool(self):
        self.assertEqual(defend_mp_restore(40), 2)
        self.assertEqual(defend_mp_restore(100), 6)
        self.assertEqual(defend_mp_restore(120), 7)

    def test_player_status_semantics_are_symmetric(self):
        statuses = {}
        apply_status(statuses, "power_up", 2, 0.10)
        apply_status(statuses, "weaken", 2, 0.12)
        apply_status(statuses, "slow", 2, 0.10)
        mult = player_outgoing_status_multiplier(statuses)
        # Power Up helps, while Weaken/Slow materially counter it.
        self.assertLess(mult, 1.0)
        self.assertGreater(mult, 0.65)
        apply_status(statuses, "vulnerable", 2, 0.16)
        self.assertAlmostEqual(incoming_vulnerability_multiplier(statuses), 1.16)

    def test_slow_and_haste_change_action_priority_in_opposite_directions(self):
        action = {"kind": "attack"}
        self.assertEqual(action_priority(action, {}), 40)
        fast = {"haste": {"turns": 2, "magnitude": 0.10}}
        slow = {"slow": {"turns": 2, "magnitude": 0.10}}
        both = {**fast, **slow}
        self.assertEqual(action_priority(action, fast), 37)
        self.assertEqual(action_priority(action, slow), 43)
        self.assertEqual(action_priority(action, both), 40)

    def test_higher_rank_hunts_resist_debuffs_without_immunity(self):
        self.assertEqual(active_hunt_status_chance(1.0, "C", "weaken"), 1.0)
        self.assertAlmostEqual(active_hunt_status_chance(1.0, "S", "weaken"), 0.88)
        self.assertAlmostEqual(active_hunt_status_chance(1.0, "S", "stun"), 0.66)
        self.assertGreater(active_hunt_status_chance(0.20, "S", "stun"), 0.0)

    def test_player_stun_now_consumes_the_action(self):
        opened = self._start_venture()
        actor = self.game.encounter_roster["1"]
        apply_status(actor["statuses"], "stun", 1, 1.0)
        before = int(self.game.active_encounter["monster_hp"])
        self.game.battle_attack("1")
        result = self.game.advance_encounter_round(opened.data["encounter_id"])
        self.assertTrue(result.ok)
        self.assertEqual(int(actor["damage"]), 0)
        self.assertEqual(int(self.game.active_encounter["monster_hp"]), before)
        self.assertIn("stunned", " ".join(result.messages).lower())

    def test_monster_evasion_is_no_longer_display_only(self):
        self._start_venture()
        actor = self.game.encounter_roster["1"]
        monster = self.data.monsters[self.game.active_encounter["monster_id"]]
        apply_status(self.game.active_encounter["monster_statuses"], "evade", 2, 0.40)
        self.game.rng = ZeroRng()
        damage, critical = self.game._basic_active_damage(actor, monster, scaling="physical")
        self.assertEqual(damage, 0)
        self.assertFalse(critical)

    def test_monster_focus_and_player_vulnerable_affect_enemy_damage(self):
        self._start_venture()
        actor = self.game.encounter_roster["1"]
        monster = self.data.monsters[self.game.active_encounter["monster_id"]]
        behavior = self.data.enemy_actions.get(monster["id"], {"profile": "balanced"})
        profile = self.data.enemy_profiles[behavior.get("profile", "balanced")]

        self.game.rng = random.Random(901)
        base = self.game._enemy_damage_against(monster, actor, profile)

        apply_status(self.game.active_encounter["monster_statuses"], "focus", 2, 0.10)
        apply_status(actor["statuses"], "vulnerable", 2, 0.16)
        self.game.rng = random.Random(901)
        pressured = self.game._enemy_damage_against(monster, actor, profile)
        self.assertGreater(pressured, base)

    def test_successful_stun_creates_one_round_control_resistance(self):
        self._start_venture()
        actor = self.game.encounter_roster["1"]
        actor["job_id"] = "paladin"
        actor["job_level"] = 50
        actor["mp"] = actor["max_mp"] = 100
        monster = self.data.monsters[self.game.active_encounter["monster_id"]]
        action = {"kind": "ability", "ability_id": "shield_bash", "target_id": "monster"}
        self.game.rng = ZeroRng()

        first_log = []
        self.game._resolve_active_ability(actor, action, monster, first_log)
        self.assertIn("stun", self.game.active_encounter["monster_statuses"])
        self.assertEqual(
            int(self.game.active_encounter["monster_stun_resist_until"]),
            int(self.game.active_encounter["round"]) + STUN_RESIST_ROUNDS_AFTER_SUCCESS,
        )

        # Simulate the Stun aging out and the next round beginning. The follow-up
        # Shield Bash must be resisted even with an RNG that would otherwise hit.
        self.game.active_encounter["monster_statuses"].pop("stun", None)
        self.game.active_encounter["round"] += 1
        second_log = []
        self.game._resolve_active_ability(actor, action, monster, second_log)
        self.assertNotIn("stun", self.game.active_encounter["monster_statuses"])
        self.assertIn("resisted", " ".join(second_log).lower())

    def test_shipping_ability_and_enemy_data_meet_balance_guardrails(self):
        self.assertEqual(self.data.validate(), [])
        self.assertEqual(sum(len(v) for v in self.data.active_abilities.values()), 341)
        aetherflow = next(a for a in self.data.active_abilities["summoner"] if a["id"] == "aetherflow")
        fraction = next(e["fraction"] for e in aetherflow["effects"] if e["type"] == "restore_mp")
        self.assertLessEqual(float(fraction), 0.25)

    def test_all_341_player_abilities_resolve_after_resource_tuning(self):
        self._start_venture()
        monster = self.data.monsters[self.game.active_encounter["monster_id"]]
        actor = self.game.encounter_roster["1"]
        ally = dict(actor)
        ally.update({
            "name": "Ally", "username": "ally", "hp": 5000, "max_hp": 5000,
            "mp": 1000, "max_mp": 1000, "ap": 1000, "max_ap": 1000, "statuses": {}, "action": None,
            "damage": 0, "healing": 0, "damage_taken": 0, "best_hit": 0,
            "actions": 0, "abilities_used": 0, "items_used": 0, "defends": 0,
        })
        self.game.encounter_roster["2"] = ally

        resolved = 0
        for job_id, abilities in self.data.active_abilities.items():
            actor["job_id"] = job_id
            actor["job_level"] = 50
            actor["mp"] = actor["max_mp"] = 1000
            actor["ap"] = actor["max_ap"] = 1000
            actor["hp"] = max(1, int(actor["max_hp"]) // 2)
            actor["statuses"] = {}
            for ability in abilities:
                self.game.active_encounter["monster_hp"] = self.game.active_encounter["monster_max_hp"] = 1_000_000
                self.game.active_encounter["monster_statuses"] = {}
                self.game.active_encounter["monster_stun_resist_until"] = 0
                ally["hp"] = 0 if any(e.get("type") == "revive" for e in ability.get("effects", [])) else int(ally["max_hp"]) // 2
                ally["statuses"] = {}
                actor["mp"] = 1000
                actor["ap"] = 1000
                target_type = ability.get("target")
                target_id = "monster" if target_type == "enemy" else ("party" if target_type == "party" else ("1" if target_type == "self" else "2"))
                log = []
                self.game.rng = random.Random(9500 + resolved)
                self.game._resolve_active_ability(
                    actor,
                    {"kind": "ability", "ability_id": ability["id"], "target_id": target_id},
                    monster,
                    log,
                )
                self.assertTrue(log, f"{job_id}:{ability['id']} produced no resolver log")
                self.assertIn(ability["name"], log[-1])
                resolved += 1
        self.assertEqual(resolved, 341)

    def test_repeated_battles_leave_only_bounded_presentation_state(self):
        for index in range(20):
            opened = self._start_venture()
            for round_no in range(1, 8):
                self.game._remember_round(round_no, [f"Synthetic event {index}-{round_no}"])
            self.assertLessEqual(len(self.game.active_encounter.get("round_history", [])), 4)
            finished = self.game._finish_active_encounter(True, reason="Combat soak cleanup.")
            self.assertTrue(finished.ok)
            self.assertIsNone(self.game.active_encounter)
            self.assertEqual(self.game.encounter_roster, {})
            self.assertLessEqual(len(self.game._last_battle_history.get("history", [])), 4)


if __name__ == "__main__":
    unittest.main()

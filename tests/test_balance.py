from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.balance import (
    critical_chance,
    encounter_reward_factor,
    jp_reward_factor,
    party_enemy_attacks,
    rally_venture_reward_multiplier,
    party_monster_hp,
    raid_contribution_score,
    xp_to_next,
)
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class BalanceTests(unittest.TestCase):
    def test_progression_curve_preserves_existing_early_xp(self):
        self.assertEqual(xp_to_next(1), 100)
        self.assertEqual(xp_to_next(10), 2661)

    def test_overlevel_reward_factor_discourages_trivial_farming(self):
        self.assertEqual(encounter_reward_factor(50, 50), 1.0)
        self.assertEqual(encounter_reward_factor(50, 1), 0.05)
        self.assertEqual(encounter_reward_factor(10, 30), 1.5)


    def test_rally_venture_reward_bonus_scales_with_personal_risk(self):
        self.assertEqual(rally_venture_reward_multiplier(20, 20), 1.0)
        self.assertEqual(rally_venture_reward_multiplier(20, 25), 1.25)
        self.assertEqual(rally_venture_reward_multiplier(20, 30), 1.50)
        self.assertEqual(rally_venture_reward_multiplier(20, 40), 1.50)

    def test_rally_venture_reward_bonus_is_applied_to_xp_jp_and_gil(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, GameData(ROOT / "data"), venture_cooldown_seconds=0, venture_treasure_chance=0.0)
                for pid, name in (("1", "Van"), ("2", "Ally")):
                    game.recruit(pid, name.lower(), name)
                    game.choose_job(pid, "warrior")
                    db.execute("UPDATE players SET level=1 WHERE twitch_id=?", (pid,))
                monster = dict(game.data.monsters["spriggan"])
                self.assertEqual(int(monster["level"]), 11)
                monster.update({"drops": [], "pity_drops": [], "recipe_drops": []})
                class FixedRng:
                    @staticmethod
                    def uniform(_a, _b): return 1.0
                    @staticmethod
                    def random(): return 1.0
                game.rng = FixedRng()
                normal = game._award_victory("1", game._player("1"), monster)
                rally = game._award_victory("2", game._player("2"), monster, rally_venture=True)
                self.assertEqual(rally["rally_bonus_pct"], 50)
                self.assertGreater(rally["xp"], normal["xp"])
                self.assertGreater(rally["jp"], normal["jp"])
                self.assertGreater(rally["gil"], normal["gil"])
            finally:
                db.close()

    def test_overlevel_award_scales_xp_jp_and_gil(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, GameData(ROOT / "data"), venture_cooldown_seconds=0, venture_treasure_chance=0.0)
                game.recruit("1", "van", "Van")
                game.choose_job("1", "warrior")
                db.execute("UPDATE players SET level=50 WHERE twitch_id='1'")
                p = game._player("1")
                monster = dict(game.data.monsters["goblin"])
                monster.update({"drops": [], "pity_drops": [], "recipe_drops": []})
                class FixedRng:
                    @staticmethod
                    def uniform(_a, _b): return 1.0
                    @staticmethod
                    def random(): return 1.0
                game.rng = FixedRng()
                award = game._award_victory("1", p, monster)
                self.assertEqual(award["xp"], max(5, int(monster["xp"] * 0.05)))
                # JP tracks the active Job (JLv.1), not this Lv.50 character.
                self.assertEqual(award["jp"], max(2, int(monster["jp"] * jp_reward_factor(50, 1, monster["level"]))))
                self.assertEqual(award["gil"], max(1, int(monster["gil"] * 0.05)))
            finally:
                db.close()

    def test_party_scaling_is_predictable_and_bounded(self):
        self.assertEqual(party_monster_hp(1000, 1), 1000)
        self.assertEqual(party_monster_hp(1000, 2), 1620)
        self.assertEqual(party_monster_hp(1000, 4), 2860)
        self.assertEqual([party_enemy_attacks(n) for n in range(1, 9)], [1] * 8)

    def test_critical_chance_has_a_safety_cap(self):
        self.assertAlmostEqual(critical_chance(0), 0.05)
        self.assertEqual(critical_chance(999, 1.0, 1.0), 0.45)

    def test_raid_contribution_values_support_roles(self):
        pure_damage = raid_contribution_score(damage=1000)
        healer = raid_contribution_score(damage=300, healing=1000)
        tank = raid_contribution_score(damage=650, mitigation=1000)
        self.assertEqual(pure_damage, healer)
        self.assertEqual(pure_damage, tank)

    def test_shipping_game_data_passes_balance_guardrails(self):
        self.assertEqual(GameData(ROOT / "data").validate(), [])

    def test_party_combat_applies_critical_and_double_strike_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, GameData(ROOT / "data"), venture_cooldown_seconds=0, venture_treasure_chance=0.0)
                game.recruit("1", "van", "Van")
                game.choose_job("1", "warrior")
                monster = dict(game.data.monsters["goblin"])
                monster.update({"hp": 99999, "attack": 0, "defense": 0, "spirit": 0})
                with patch.object(game, "_effects", return_value={"double_strike_chance": 1.0}), \
                     patch("crystal_guild.engine.critical_chance", return_value=1.0):
                    battle = game._party_battle({"1": {"name": "Van", "job_id": "warrior"}}, monster)
                self.assertTrue(any("critical chain" in line for line in battle["log"]))
            finally:
                db.close()

    def test_raid_reward_split_uses_support_contribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, GameData(ROOT / "data"), overlay_state_path=str(Path(tmp) / "overlay.json"))
                game.recruit("1", "damage", "Damage")
                game.choose_job("1", "warrior")
                game.recruit("2", "healer", "Healer")
                game.choose_job("2", "whitemage")
                boss = dict(next(iter(game.data.bosses.values())))
                boss.update({"round": 3, "current_hp": 0, "max_hp": boss["hp"], "drops": []})
                game.active_boss = boss
                game.raid_roster = {
                    "1": {"name": "Damage", "job_id": "warrior", "hp": 100, "damage": 1000, "healing": 0, "mitigation": 0, "damage_taken": 0, "best_hit": 100},
                    "2": {"name": "Healer", "job_id": "whitemage", "hp": 100, "damage": 300, "healing": 1000, "mitigation": 0, "damage_taken": 0, "best_hit": 50},
                }
                before = {pid: db.one("SELECT gil FROM players WHERE twitch_id=?", (pid,))["gil"] for pid in ("1", "2")}
                result = game._finish_raid(True)
                self.assertTrue(result.ok)
                after = {pid: db.one("SELECT gil FROM players WHERE twitch_id=?", (pid,))["gil"] for pid in ("1", "2")}
                self.assertEqual(after["1"] - before["1"], after["2"] - before["2"])
            finally:
                db.close()


class StabilityTests(unittest.TestCase):
    def test_database_backup_is_consistent_and_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = Database(root / "guild.db")
            db.execute("INSERT INTO players(twitch_id,username,display_name) VALUES ('1','van','Van')")
            target = db.backup(root / "backup.db")
            self.assertEqual(db.quick_check(), [])
            db.close()

            backup = Database(target)
            try:
                self.assertEqual(backup.quick_check(), [])
                self.assertEqual(backup.one("SELECT display_name FROM players WHERE twitch_id='1'")["display_name"], "Van")
            finally:
                backup.close()

    def test_portal_export_can_hold_one_wal_read_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "guild.db"
            db = Database(path)
            data = GameData(ROOT / "data")
            game = CrystalGuildEngine(db, data, venture_cooldown_seconds=0, venture_treasure_chance=0.0)
            game.recruit("1", "van", "Van")
            game.choose_job("1", "warrior")
            repo = PortalRepository(path, ROOT / "data")
            try:
                with repo.consistent_read():
                    first = repo.overview("van")
                    db.execute("UPDATE players SET gil=9999 WHERE twitch_id='1'")
                    second = repo.overview("van")
                third = repo.overview("van")
                self.assertEqual(first["identity"]["gil"], second["identity"]["gil"])
                self.assertEqual(third["identity"]["gil"], 9999)
            finally:
                repo.close()
                db.close()


if __name__ == "__main__":
    unittest.main()

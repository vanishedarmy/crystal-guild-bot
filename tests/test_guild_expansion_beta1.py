from __future__ import annotations

import unittest

from crystal_guild.database import DATABASE_SCHEMA_VERSION
from crystal_guild.fellowship import PROJECTS, ORDER_DEFINITIONS, WEEKLY_ORDER_SET_REWARD
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION
from tools.simulate_guild_balance import run_matrix


class GuildExpansionBeta1Tests(unittest.TestCase):
    def test_beta1_keeps_schema9_and_protocol21(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 14)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 30)

    def test_airship_dock_and_launch_costs_are_tuned(self):
        expected = {
            "airship_dock_t1": (60_000, 25, 4),
            "airship_dock_t2": (100_000, 35, 6),
            "airship_dock_t3": (170_000, 55, 9),
        }
        for project_id, (gil, coins, raids) in expected.items():
            req = {row["key"]: int(row["target"]) for row in PROJECTS[project_id]["requirements"]}
            self.assertEqual(req["gil"], gil)
            self.assertEqual(req["item:ancient_coin"], coins)
            self.assertEqual(req["activity:raid_clear"], raids)

        airship = {row["key"]: int(row["target"]) for row in PROJECTS["crystal_guild_airship"]["requirements"]}
        self.assertEqual(airship["gil"], 140_000)
        self.assertEqual(airship["item:mythril_ore"], 35)
        self.assertEqual(airship["item:wyvern_scale"], 18)
        self.assertEqual(airship["item:elemental_crystal"], 20)
        self.assertEqual(airship["activity:raid_clear"], 6)

    def test_airship_upgrade_requirements_scale_by_material_rarity(self):
        # Tier III demonstrates the intended curve: artifact tracks require fewer
        # pieces than common-material tracks, while all tracks share the same
        # tuned Gil/raid requirement.
        hull = {row["key"]: int(row["target"]) for row in PROJECTS["airship_hull_t3"]["requirements"]}
        core = {row["key"]: int(row["target"]) for row in PROJECTS["airship_crystal_core_t3"]["requirements"]}
        engine = {row["key"]: int(row["target"]) for row in PROJECTS["airship_engine_t3"]["requirements"]}
        cargo = {row["key"]: int(row["target"]) for row in PROJECTS["airship_cargo_t3"]["requirements"]}
        survey = {row["key"]: int(row["target"]) for row in PROJECTS["airship_survey_t3"]["requirements"]}
        self.assertEqual(hull["item:adamantite"], 6)
        self.assertEqual(core["item:dark_matter"], 6)
        self.assertEqual(engine["item:magitek_capacitor"], 8)
        self.assertEqual(cargo["item:mythril_ore"], 10)
        self.assertEqual(survey["item:elemental_crystal"], 10)
        for req in (hull, core, engine, cargo, survey):
            self.assertEqual(req["gil"], 95_000)
            self.assertEqual(req["activity:raid_clear"], 2)

    def test_weekly_order_rewards_remain_unchanged(self):
        self.assertEqual(WEEKLY_ORDER_SET_REWARD, {"guild_renown": 500, "personal_gil": 1000, "personal_renown": 50})
        rewards = {(row["personal_gil"], row["personal_renown"]) for row in ORDER_DEFINITIONS}
        self.assertIn((500, 25), rewards)
        self.assertIn((750, 30), rewards)

    def test_fixed_seed_guild_simulation_hits_beta1_guardrails(self):
        report = run_matrix(10, 1301)
        self.assertEqual(report["total_runs"], 30)
        by_id = {row["id"]: row for row in report["profiles"]}
        core_airship = by_id["core"]["airship_week"]["median"]
        active_airship = by_id["active"]["airship_week"]["median"]
        core_facilities = by_id["core"]["facilities_week"]["median"]
        self.assertIsNotNone(core_airship)
        self.assertIsNotNone(active_airship)
        self.assertIsNotNone(core_facilities)
        self.assertGreaterEqual(core_airship, 8.0)
        self.assertLessEqual(core_airship, 20.0)
        self.assertLess(active_airship, core_airship)
        self.assertLessEqual(core_facilities, 32.0)


if __name__ == "__main__":
    unittest.main()

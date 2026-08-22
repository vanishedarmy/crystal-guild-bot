from __future__ import annotations

import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data"


class ItemProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.items = json.loads((DATA / "items.json").read_text(encoding="utf-8"))
        cls.jobs = json.loads((DATA / "jobs.json").read_text(encoding="utf-8"))

    def test_early_game_equipment_has_dense_level_bands(self):
        equipment = [item for item in self.items if item["type"] in {"weapon", "armor"} and item.get("shop")]
        required_levels = {1, 5, 8, 12, 16, 20, 25, 30, 35, 40, 45, 50}
        for item_type in ("weapon", "armor"):
            levels = {
                int(item.get("min_level", item.get("shop_level", 1)))
                for item in equipment
                if item["type"] == item_type
            }
            self.assertTrue(required_levels.issubset(levels), f"{item_type} missing early tiers: {sorted(required_levels - levels)}")

    def test_every_job_has_weapon_and_armor_options_through_level_50(self):
        equipment = [item for item in self.items if item["type"] in {"weapon", "armor"} and item.get("shop")]
        levels = (1, 5, 8, 12, 16, 20, 25, 30, 35, 40, 45, 50)
        for job in self.jobs:
            job_id = job["id"]
            for level in levels:
                for item_type in ("weapon", "armor"):
                    matches = [
                        item for item in equipment
                        if item["type"] == item_type
                        and int(item.get("min_level", item.get("shop_level", 1))) == level
                        and job_id in item.get("allowed_jobs", [])
                    ]
                    self.assertTrue(matches, f"{job_id} has no {item_type} at Lv.{level}")

    def test_shop_equipment_carries_family_metadata(self):
        equipment = [item for item in self.items if item["type"] in {"weapon", "armor"} and item.get("shop")]
        self.assertTrue(equipment)
        for item in equipment:
            self.assertTrue(item.get("gear_family"), item["id"])


if __name__ == "__main__":
    unittest.main()

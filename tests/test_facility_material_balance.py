from __future__ import annotations

import json
import unittest
from pathlib import Path

from crystal_guild.fellowship import FACILITIES


ROOT = Path(__file__).resolve().parents[1]


class FacilityMaterialBalanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.monsters = json.loads((ROOT / "data" / "monsters.json").read_text(encoding="utf-8"))
        cls.items = {
            item["id"]: item
            for item in json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
        }
        cls.sources: dict[str, list[tuple[int, str, float]]] = {}
        for facility in FACILITIES.values():
            item_id = str(facility.get("material") or "")
            if not item_id:
                continue
            rows: list[tuple[int, str, float]] = []
            for monster in cls.monsters:
                for drop in monster.get("drops", []):
                    if drop.get("item_id") == item_id:
                        rows.append((int(monster["level"]), str(monster["id"]), float(drop["chance"])))
            cls.sources[item_id] = sorted(rows)

    def test_every_facility_material_has_multiple_monster_sources(self):
        for item_id, rows in self.sources.items():
            with self.subTest(item_id=item_id):
                self.assertGreaterEqual(len(rows), 3, f"{item_id} must not depend on one monster")

    def test_every_facility_material_has_an_early_access_source(self):
        # A new hero's normal Venture can roll enemies up to +10 levels. Keeping
        # the earliest source at L11 or below prevents a Fellowship Tier I/II
        # project from being hard-gated behind mid/endgame combat.
        for item_id, rows in self.sources.items():
            with self.subTest(item_id=item_id):
                earliest = min(rows, key=lambda row: row[0])
                self.assertLessEqual(earliest[0], 11, f"{item_id} earliest source is L{earliest[0]}")
                self.assertGreaterEqual(earliest[2], 0.10, f"{item_id} early source rate is too low")

    def test_facility_material_drop_rates_remain_bounded(self):
        for item_id, rows in self.sources.items():
            with self.subTest(item_id=item_id):
                for level, monster_id, chance in rows:
                    self.assertGreater(chance, 0.0, f"{monster_id}:{item_id}")
                    self.assertLessEqual(chance, 0.80, f"{monster_id}:{item_id}")

    def test_expected_thematic_early_sources_are_present(self):
        expected = {
            "ancient_coin": "ossuary_knight",
            "hi_potion": "goblin_chieftain",
            "mythril_ore": "spriggan",
            "wyvern_scale": "cockatrice",
            "elemental_crystal": "flan",
            "demon_horn": "imp",
        }
        for item_id, monster_id in expected.items():
            with self.subTest(item_id=item_id):
                self.assertIn(monster_id, {row[1] for row in self.sources[item_id]})

    def test_facility_material_ids_remain_valid_items(self):
        for item_id in self.sources:
            with self.subTest(item_id=item_id):
                self.assertIn(item_id, self.items)


if __name__ == "__main__":
    unittest.main()

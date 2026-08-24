from __future__ import annotations

import unittest
from pathlib import Path

from crystal_guild.data import GameData

ROOT = Path(__file__).resolve().parents[1]


class ArsenalExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = GameData(ROOT / "data")

    def test_arsenal_ii_expands_every_job_and_deepens_core_casters(self):
        self.assertEqual(len(self.data.jobs), 18)
        self.assertEqual(sum(len(rows) for rows in self.data.active_abilities.values()), 172)
        caster_jobs = {"blackmage", "whitemage", "redmage", "summoner", "bluemage", "timemage", "sage"}
        for job_id in self.data.jobs:
            rows = self.data.active_abilities[job_id]
            levels = [int(row["level"]) for row in rows]
            if job_id in caster_jobs:
                self.assertEqual(levels, [1, 5, 8, 12, 15, 18, 22, 26, 30, 35, 40, 45], job_id)
            else:
                self.assertEqual(levels, [1, 8, 12, 15, 22, 30, 35, 40], job_id)

    def test_every_job_has_elemental_or_special_effect_identity(self):
        for job_id, rows in self.data.active_abilities.items():
            expressive = 0
            for ability in rows:
                special = bool(ability.get("element"))
                for effect in ability.get("effects", []):
                    if effect.get("type") in {"status", "heal", "cleanse", "drain", "restore_mp", "restore_ap", "revive"}:
                        special = True
                    if effect.get("type") == "damage" and (effect.get("pierce") or effect.get("crit_bonus")):
                        special = True
                expressive += int(special)
            self.assertGreaterEqual(expressive, 3, f"{job_id} needs a clearer elemental/effect identity")

    def test_new_hunt_curve_starts_before_original_level_ten_marks(self):
        early = sorted((h for h in self.data.hunts.values() if int(h["min_level"]) < 10), key=lambda h: h["min_level"])
        self.assertEqual([int(h["min_level"]) for h in early], [2, 4, 6, 8])
        self.assertTrue(all(h["rank"] == "C" for h in early))
        self.assertTrue(all(self.data.monsters[h["monster_id"]].get("hunt_only") for h in early))

    def test_new_world_bosses_create_a_pre_bomb_king_progression(self):
        early = sorted((b for b in self.data.bosses.values() if int(b.get("recommended_level", 999)) < 20), key=lambda b: b["recommended_level"])
        self.assertEqual([int(b["recommended_level"]) for b in early], [6, 10, 14, 18])
        self.assertTrue(all(b["tier"] == "World Boss" for b in early))

    def test_low_level_crafting_expansion_outputs_practical_consumables(self):
        ids = {
            "field_hi_potion", "antidote_satchel", "echo_herb_bundle", "stamina_draught_mix",
            "ether_distillation", "iron_tonic_mix", "smoke_bomb_kit", "remedy_kit",
        }
        recipes = [self.data.recipes[row_id] for row_id in ids]
        self.assertTrue(all(int(row["min_level"]) <= 15 for row in recipes))
        self.assertTrue(all(self.data.items[row["output"]["item_id"]]["type"] == "consumable" for row in recipes))

    def test_full_data_validation_remains_clean(self):
        self.assertEqual(self.data.validate(), [])


if __name__ == "__main__":
    unittest.main()

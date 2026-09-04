from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.balance import RANDOM_ENCOUNTER_MIN_VARIETY
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class EncounterVarietyHotfixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
        )
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_magic_pot_is_not_the_only_solo_candidate_in_whispering_caverns(self):
        region = self.game.data.regions["whispering_caverns"]
        player = {"twitch_id": "100", "level": 25}
        captured = {}

        def choose(population, weights=None, k=1):
            captured["ids"] = [str(monster["id"]) for monster in population]
            captured["weights"] = list(weights or [])
            return [population[0]]

        with patch.object(self.game.rng, "choices", side_effect=choose):
            self.game._solo_select_monster(player, region, stage=1)

        self.assertIn("magic_pot", captured["ids"])
        self.assertGreaterEqual(len(captured["ids"]), RANDOM_ENCOUNTER_MIN_VARIETY)
        magic_index = captured["ids"].index("magic_pot")
        total = sum(float(value) for value in captured["weights"])
        self.assertLess(float(captured["weights"][magic_index]) / total, 0.30)

    def test_solo_pool_keeps_minimum_variety_across_every_region_when_available(self):
        for region in self.game.data.regions.values():
            region_id = str(region["id"])
            for level in range(int(region.get("min_level", 1)), 100):
                maximum = level + 5
                eligible_count = sum(
                    1
                    for entry in region.get("encounters", [])
                    if int(self.game.data.monsters[entry["monster_id"]]["level"]) <= maximum
                )
                if not eligible_count:
                    continue
                captured = {}

                def choose(population, weights=None, k=1):
                    captured["count"] = len(population)
                    return [population[0]]

                with patch.object(self.game.rng, "choices", side_effect=choose):
                    self.game._solo_select_monster({"twitch_id": "100", "level": level}, region, stage=2)
                self.assertGreaterEqual(
                    int(captured["count"]),
                    min(RANDOM_ENCOUNTER_MIN_VARIETY, eligible_count),
                    msg=f"{region_id} Lv.{level} collapsed to too few Solo Venture monsters",
                )

    def test_recent_repeat_is_heavily_suppressed(self):
        region_id = "whispering_caverns"
        candidates = [
            self.game.data.monsters["magic_pot"],
            self.game.data.monsters["black_flan"],
            self.game.data.monsters["piscodemon"],
        ]
        key = self.game._encounter_variety_key("100", region_id)
        self.game._recent_random_monsters[key] = ["black_flan", "magic_pot"]
        adjusted = self.game._encounter_variety_weights("100", region_id, candidates, [1.0, 5.0, 6.0])
        self.assertAlmostEqual(adjusted[0], 0.10, places=6)
        self.assertGreater(adjusted[1], adjusted[0])
        self.assertGreater(adjusted[2], adjusted[0])

    def test_third_identical_encounter_is_blocked_when_an_alternative_exists(self):
        region_id = "whispering_caverns"
        candidates = [
            self.game.data.monsters["magic_pot"],
            self.game.data.monsters["black_flan"],
        ]
        key = self.game._encounter_variety_key("100", region_id)
        self.game._recent_random_monsters[key] = ["magic_pot", "magic_pot"]
        adjusted = self.game._encounter_variety_weights("100", region_id, candidates, [1.0, 5.0])
        self.assertEqual(adjusted[0], 0.0)
        self.assertGreater(adjusted[1], 0.0)


if __name__ == "__main__":
    unittest.main()

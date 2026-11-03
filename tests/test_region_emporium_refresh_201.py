"""V2.0.1 regional ecology and guaranteed basic vendor progression."""
from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.emporium import (REGIONAL_SHOPS, eligible_stock, shop_context,
                                    shop_authorized_legendary)
from crystal_guild.world_events import WORLD_EVENTS

ROOT = Path(__file__).resolve().parents[1]


class RegionalEcologyVendorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GameData(ROOT / "data")

    def test_normal_encounter_regions_and_bestiary_habitats_agree(self):
        self.assertEqual(self.data.validate(), [])
        banned = {event["base_monster_id"] for event in WORLD_EVENTS if event.get("tier") == "elite"}
        for region in self.data.regions.values():
            self.assertGreaterEqual(len(region["encounters"]), 2)
            self.assertEqual(len({e["monster_id"] for e in region["encounters"]}), len(region["encounters"]))
            self.assertTrue(all(e["weight"] > 0 for e in region["encounters"]))
            for encounter in region["encounters"]:
                mid = encounter["monster_id"]
                self.assertNotIn(mid, banned)
                m = self.data.monsters[mid]
                if region["min_level"] != 99:
                    self.assertLessEqual(region["min_level"], m["level"])
                    self.assertLessEqual(m["level"], region["recommended_max_level"])
                entry = self.data.bestiary_research["entries"][mid]
                if entry.get("habitat_provenance") == "region_encounters":
                    self.assertIn(region["id"], entry["habitats"])

    def test_relocated_enemies_match_terrain_and_level(self):
        expected = {
            "bat": ("whispering_caverns", 10),
            "skeleton": ("whispering_caverns", 11),
            "sahagin": ("sable_coast", 20),
            "killer_fish": ("sable_coast", 21),
            "zu": ("sable_coast", 22),
            "magitek_drone": ("magitek_wastes", 31),
        }
        for mid, (rid, level) in expected.items():
            with self.subTest(monster=mid):
                self.assertEqual(self.data.monsters[mid]["level"], level)
                actual = [region["id"] for region in self.data.regions.values()
                          if mid in {e["monster_id"] for e in region["encounters"]}]
                self.assertEqual(actual, [rid])
                self.assertEqual(self.data.bestiary_research["entries"][mid]["habitats"], [rid])

    def test_each_current_job_can_buy_a_weapon_and_armor_at_start_middle_and_end(self):
        self.assertEqual(set(REGIONAL_SHOPS), set(self.data.regions))
        for rid, region in self.data.regions.items():
            minimum = region["min_level"]
            maximum = region["recommended_max_level"]
            for level in sorted({minimum, (minimum + maximum)//2, maximum}):
                for job in self.data.jobs:
                    with self.subTest(region=rid, level=level, job=job):
                        p = {"current_region": rid, "current_job": job, "level": level}
                        ctx = shop_context(p, self.data.regions)
                        stock = eligible_stock(p, self.data.items, ctx)
                        for kind in ("weapon", "armor"):
                            pool = [item for item in stock if item["type"] == kind]
                            self.assertTrue(pool, (rid, job, level, kind))
                        self.assertFalse(any(i.get("relic_id") or i.get("unsellable") for i in stock))
                        self.assertFalse(any(i["id"].startswith("paragon_") for i in stock))

    def test_real_rotating_shop_has_weapon_and_armor_for_every_job_at_each_region_checkpoint(self):
        """Test the actual cached shop output, not just theoretical eligible inventory."""
        with tempfile.TemporaryDirectory() as temp:
            db = Database(Path(temp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, self.data, rng=random.Random(201),
                                          overlay_state_path=str(Path(temp) / "overlay.json"))
                self.assertTrue(game.recruit("shopper", "shopper", "Shopper").ok)
                for region in self.data.regions.values():
                    levels = sorted({int(region["min_level"]),
                                     (int(region["min_level"]) + int(region["recommended_max_level"])) // 2,
                                     int(region["recommended_max_level"])})
                    for level in levels:
                        for job in self.data.jobs:
                            with self.subTest(region=region["id"], level=level, job=job):
                                db.execute("UPDATE players SET level=?,current_region=?,current_job=? WHERE twitch_id='shopper'",
                                           (level, region["id"], job))
                                stock, _expires = game._shop_stock("shopper")
                                types = {item["type"] for item in stock}
                                self.assertIn("weapon", types)
                                self.assertIn("armor", types)
                                self.assertFalse(any(i.get("relic_id") or i.get("unsellable") for i in stock))
            finally:
                db.close()

    def test_exactly_intended_premium_shop_grade_is_authorized(self):
        for prefix, level in (("ascendant_", 90), ("singularity_", 95)):
            gear = [i for i in self.data.items.values() if i["id"].startswith(prefix)
                    and i["type"] in ("weapon", "armor")]
            self.assertTrue(gear)
            self.assertTrue(all(i.get("shop") and i.get("shop_level") == level
                                and shop_authorized_legendary(i) for i in gear))
        self.assertFalse(shop_authorized_legendary({**self.data.items["paragon_titan_axe"], "shop": True, "shop_level": 99}))
        self.assertFalse(shop_authorized_legendary({**self.data.items["ultimate_warrior_eternal"], "shop": True}))

    def test_premium_weapon_purchase_works_in_portal_and_twitch(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Database(Path(temp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, self.data, rng=random.Random(295),
                                          overlay_state_path=str(Path(temp) / "overlay.json"))
                self.assertTrue(game.recruit("buyer", "buyer", "Buyer").ok)
                db.execute("UPDATE players SET gil=500000,level=90,current_region='astral_threshold',current_job='warrior' WHERE twitch_id='buyer'")
                state = game.portal_shop_state("buyer").data
                weapon = next(item for item in state["stock"] if item["type"] == "weapon" and item["id"].startswith("ascendant_"))
                res = game.portal_buy("buyer", weapon["id"], 1, "regional-201-portal")
                self.assertTrue(res.ok, res.messages)
                self.assertEqual(db.one("SELECT quantity FROM inventory WHERE player_id='buyer' AND item_id=?", (weapon["id"],))["quantity"], 1)
                self.assertTrue(game.portal_buy("buyer", weapon["id"], 1, "regional-201-portal").ok)
                self.assertEqual(db.one("SELECT quantity FROM inventory WHERE player_id='buyer' AND item_id=?", (weapon["id"],))["quantity"], 1)
                db.execute("UPDATE players SET level=99,current_region='eclipsed_singularity_citadel' WHERE twitch_id='buyer'")
                state = game.portal_shop_state("buyer").data
                weapon = next(item for item in state["stock"] if item["type"] == "weapon" and item["id"].startswith("singularity_"))
                self.assertTrue(game.buy("buyer", weapon["id"], 1).ok)
                self.assertEqual(db.one("SELECT quantity FROM inventory WHERE player_id='buyer' AND item_id=?", (weapon["id"],))["quantity"], 1)
            finally:
                db.close()

    def test_cached_empty_weapon_rotation_is_repaired_and_exclusives_stay_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Database(Path(temp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, self.data, rng=random.Random(201),
                                          overlay_state_path=str(Path(temp) / "overlay.json"))
                self.assertTrue(game.recruit("shopper", "shopper", "Shopper").ok)
                for region, level in (("whispering_caverns", 10),
                                      ("shattered_frontier", 60),
                                      ("astral_threshold", 90),
                                      ("astral_threshold", 95),
                                      ("eclipsed_singularity_citadel", 99)):
                    db.execute("UPDATE players SET level=?,current_region=?,current_job='warrior' WHERE twitch_id='shopper'", (level, region))
                    with self.subTest(region=region, level=level):
                        state = game.portal_shop_state("shopper").data
                        weapons = [item for item in state["stock"] if item["type"] == "weapon"]
                        self.assertTrue(weapons)
                        self.assertEqual(len(state["stock"]), len({item["id"] for item in state["stock"]}))
                        for item in state["stock"]:
                            self.assertFalse(item["id"].startswith("paragon_"))
                            self.assertFalse(item["id"].startswith("ultimate_"))
                        if level >= 90:
                            prefix = "ascendant_" if level == 90 else "singularity_"
                            self.assertTrue(any(item["id"].startswith(prefix) for item in weapons))
                        ctx = shop_context(game._player("shopper"), self.data.regions)
                        eligible = eligible_stock(game._player("shopper"), self.data.items, ctx)
                        supplies = [item["id"] for item in eligible if item["type"] == "consumable"]
                        # Simulate a previously-valid legacy cache that omitted all weapons.
                        db.execute("UPDATE player_regional_shops SET stock_json=? WHERE player_id='shopper' AND region_id=? AND job_id='warrior'",
                                   (json.dumps(supplies), region))
                        repaired = game.portal_shop_state("shopper").data
                        self.assertTrue(any(item["type"] == "weapon" for item in repaired["stock"]))
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()

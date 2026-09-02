from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class ItemExpansionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "items-expansion.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            venture_cooldown_seconds=0, venture_treasure_chance=0.0,
            encounter_join_seconds=5,
            encounter_round_seconds=5,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(41),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def _start(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        self.assertTrue(self.game.start_encounter_battle(opened.data["encounter_id"]).ok)
        # Keep item-effect tests from ending on an incidental low-level monster.
        self.game.active_encounter["monster_hp"] = 5000
        self.game.active_encounter["monster_max_hp"] = 5000
        return opened.data["encounter_id"]

    def test_catalog_expands_to_435_items_and_validates(self):
        self.assertEqual(len(self.data.items), 435)
        self.data.validate_or_raise()

    def test_potion_ladder_is_locked_to_fixed_recovery_values(self):
        expected = {
            "potion": 50,
            "hi_potion": 200,
            "mega_potion": 500,
            "x_potion": 1000,
        }
        for item_id, amount in expected.items():
            item = self.data.items[item_id]
            heal = next(effect for effect in item["use"]["effects"] if effect["type"] == "heal_hp")
            self.assertEqual(heal["amount"], amount, item_id)
            self.assertNotIn("fraction", heal, item_id)

    def test_every_job_has_shop_weapon_and_armor_at_level_40_and_45(self):
        gear = [item for item in self.data.items.values() if item.get("shop") and item["type"] in {"weapon", "armor"}]
        for job_id in self.data.jobs:
            for level in (40, 45):
                for item_type in ("weapon", "armor"):
                    matches = [
                        item for item in gear
                        if item["type"] == item_type
                        and int(item.get("min_level", item.get("shop_level", 1))) == level
                        and job_id in item.get("allowed_jobs", [])
                    ]
                    self.assertTrue(matches, f"{job_id} lacks Lv.{level} {item_type}")

    def test_mp_and_ap_recovery_items_are_resource_specific(self):
        ether = self.data.items["hi_ether"]["use"]["effects"][0]
        stamina = self.data.items["stamina_draught"]["use"]["effects"][0]
        self.assertEqual(ether, {"type": "restore_mp", "fraction": 0.65})
        self.assertEqual(stamina, {"type": "restore_ap", "fraction": 0.4})

    def test_status_accessories_expose_real_combat_traits(self):
        star = self.data.items["star_pendant"]
        ribbon = self.data.items["ribbon"]
        self.assertIn("poison", star["status_immune"])
        self.assertEqual(
            set(ribbon["status_immune"]),
            {"vulnerable", "weaken", "slow", "stun", "poison", "silence", "blind"},
        )

    def test_fixed_potion_recovery_resolves_in_active_battle(self):
        encounter_id = self._start()
        self.game._change_item("1", "mega_potion", 1, "test")
        actor = self.game.encounter_roster["1"]
        actor["hp"] = 1
        before = actor["hp"]
        self.assertTrue(self.game.use_item("1", "mega potion").ok)
        self.game.advance_encounter_round(encounter_id)
        if self.game.active_encounter:
            actor = self.game.encounter_roster["1"]
            # Enemy response may deal damage afterward, but the battle ledger
            # must record the exact 500-point recovery before that response.
            self.assertEqual(actor["healing"], min(500, actor["max_hp"] - before))
        self.assertEqual(self.game._inventory_qty("1", "mega_potion"), 0)

    def test_fixed_potion_field_recovery_uses_full_potency_until_max_hp(self):
        self.game._max_hp = lambda _player: 5000
        expected = {
            "potion": 50,
            "hi_potion": 200,
            "mega_potion": 500,
            "x_potion": 1000,
        }
        for item_id, amount in expected.items():
            self.db.execute("UPDATE players SET current_hp=1000 WHERE twitch_id='1'")
            self.game._change_item("1", item_id, 1, "potency_audit")
            result = self.game.use_item("1", item_id)
            self.assertTrue(result.ok, item_id)
            self.assertEqual(int(self.game._player("1")["current_hp"]), 1000 + amount, item_id)

        self.db.execute("UPDATE players SET current_hp=4941 WHERE twitch_id='1'")
        self.game._change_item("1", "mega_potion", 1, "potency_cap_audit")
        capped = self.game.use_item("1", "mega_potion")
        self.assertTrue(capped.ok)
        self.assertEqual(int(self.game._player("1")["current_hp"]), 5000)
        self.assertIn("59 HP from 500 HP potency", capped.messages[0])
        self.assertIn("capped at maximum HP", capped.messages[0])

    def test_fractional_restoratives_resolve_declared_percentages_in_active_battle(self):
        expected = {
            "ether": ("mp", 400),
            "hi_ether": ("mp", 650),
            "turbo_ether": ("mp", 1000),
            "stamina_draught": ("ap", 400),
            "warriors_tonic": ("ap", 650),
            "heros_brew": ("ap", 1000),
        }
        for item_id, (resource, restored) in expected.items():
            self.game._change_item("1", item_id, 1, "restorative_audit")
            actor = {
                "name": "Van", "hp": 1000, "max_hp": 5000,
                "mp": 0, "max_mp": 1000, "ap": 0, "max_ap": 1000,
                "damage": 0, "healing": 0, "best_hit": 0, "items_used": 0, "statuses": {},
            }
            self.game.encounter_roster = {"1": actor}
            self.game.active_encounter = {"monster_id": next(iter(self.data.monsters)), "monster_hp": 5000}
            log: list[str] = []
            self.game._resolve_active_item("1", actor, {"item_id": item_id, "target_id": "1"}, log)
            self.assertEqual(int(actor[resource]), restored, item_id)
            self.assertEqual(self.game._inventory_qty("1", item_id), 0, item_id)

    def test_offensive_item_uses_data_driven_damage(self):
        self._start()
        self.game._change_item("1", "arctic_wind", 1, "test")
        actor = self.game.encounter_roster["1"]
        before = int(self.game.active_encounter["monster_hp"])
        log: list[str] = []
        self.game._resolve_active_item(
            "1", actor, {"item_id": "arctic_wind", "target_id": "monster"}, log
        )
        self.assertEqual(before - int(self.game.active_encounter["monster_hp"]), 300)
        self.assertEqual(self.game._inventory_qty("1", "arctic_wind"), 0)
        self.assertTrue(any("300 Ice damage" in row for row in log))

    def test_equipped_status_immunity_is_loaded_into_battle_state(self):
        self.db.execute("UPDATE players SET level=10 WHERE twitch_id='1'")
        self.game._change_item("1", "star_pendant", 1, "test")
        self.assertTrue(self.game.equip("1", "star pendant").ok)
        self._start()
        actor = self.game.encounter_roster["1"]
        self.assertIn("poison", actor["status_immune"])
        self.assertEqual(self.game._player_status_chance(actor, "poison", 1.0), 0.0)


if __name__ == "__main__":
    unittest.main()

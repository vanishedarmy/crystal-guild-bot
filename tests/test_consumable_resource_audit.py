"""Regression coverage for resource-aware use of the entire consumables catalog."""
from __future__ import annotations

import random
import re
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class ConsumableResourceAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "consumable-resource-audit.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            venture_cooldown_seconds=0,
            venture_treasure_chance=0.0,
            encounter_join_seconds=5,
            encounter_round_seconds=5,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(20),
        )
        self.assertTrue(self.game.recruit("1", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("1", "warrior").ok)

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def _set_job(self, job_id: str) -> None:
        # Paladin is normally quest-locked; test the dual-resource execution
        # without bypassing its unlock rules in production code.
        if job_id == "paladin":
            self.db.execute("UPDATE players SET current_job=? WHERE twitch_id='1'", (job_id,))
        else:
            self.assertTrue(self.game.choose_job("1", job_id).ok)

    def _open_active_battle(self) -> dict:
        started = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(started.ok, started.messages)
        self.assertTrue(self.game.start_encounter_battle(started.data["encounter_id"]).ok)
        return self.game.encounter_roster["1"]

    def test_consumable_catalog_descriptions_agree_with_actual_effect_types(self) -> None:
        known = {"heal_hp", "restore_mp", "restore_ap", "revive", "cleanse", "status", "damage", "open_cache"}
        catalog = [x for x in self.data.items.values() if x.get("type") == "consumable"]
        self.assertEqual(len(catalog), 34)
        for item in catalog:
            with self.subTest(item=item["id"]):
                use = item.get("use") or {}
                effects = list(use.get("effects") or [])
                if item["id"] == "trail_rations":
                    # Camp meals use their own dedicated meal/preparation action.
                    self.assertFalse(effects)
                    self.assertIn("Camp", item["description"])
                    continue
                self.assertTrue(effects, "Combat/field consumable has no effects")
                types = {e.get("type") for e in effects}
                self.assertTrue(types <= known)
                description = str(item.get("description") or "")
                self.assertTrue(description.strip())
                # Explicit numerical/stat resource claims cannot exceed the
                # item data; the reverse is checked for each resource effect.
                for name, effect_type in (("HP", "heal_hp"), ("MP", "restore_mp"), ("AP", "restore_ap")):
                    if re.search(rf"\b{name}\b", description):
                        self.assertTrue(effect_type in types or (name == "HP" and "revive" in types))
                    if effect_type in types:
                        self.assertRegex(description, rf"\b{name}\b")
                if "revive" in types:
                    self.assertRegex(description.lower(), "reviv")
                if "damage" in types:
                    self.assertRegex(description.lower(), "damage")
                if "open_cache" in types:
                    self.assertRegex(description.lower(), "open")
        # Multiple resource effects are intentional, not alternative item
        # variants. The unused Job pool must be ignored when consumed.
        for item_id in ("tent", "elixir", "megalixir"):
            self.assertEqual(
                {x["type"] for x in self.data.items[item_id]["use"]["effects"]},
                {"heal_hp", "restore_mp", "restore_ap"},
            )
            self.assertIn("applicable", self.data.items[item_id]["description"])

    def test_resource_only_items_are_usable_only_on_matching_jobs(self) -> None:
        for job_id, valid, invalid in (
            ("warrior", "stamina_draught", "ether"),
            ("blackmage", "ether", "stamina_draught"),
        ):
            with self.subTest(job=job_id):
                self._set_job(job_id)
                self.game._change_item("1", valid, 1, "resource_test")
                self.game._change_item("1", invalid, 1, "resource_test")
                meta = self.game._resource_state_for(self.game._player("1"))
                meta = {**meta, "hp": 10}
                availability = {row["id"]: row for row in self.game._solo_owned_battle_items("1", meta)}
                self.assertTrue(availability[valid]["usable"])
                self.assertFalse(availability[invalid]["usable"])

    def test_mixed_recovery_items_appear_on_all_job_modes_in_solo_interfaces(self) -> None:
        for job_id in ("warrior", "blackmage", "paladin"):
            with self.subTest(job=job_id):
                self._set_job(job_id)
                for item_id in ("elixir", "megalixir"):
                    self.game._change_item("1", item_id, 1, "solo_audit")
                meta = {**self.game._resource_state_for(self.game._player("1")), "hp": 10}
                availability = {row["id"]: row for row in self.game._solo_owned_battle_items("1", meta)}
                self.assertTrue(availability["elixir"]["usable"])
                self.assertTrue(availability["megalixir"]["usable"])

    def test_elixir_restores_hp_and_correct_job_resource_in_active_battle(self) -> None:
        for job_id in ("warrior", "blackmage", "paladin"):
            with self.subTest(job=job_id):
                self._set_job(job_id)
                # Rather than forcing a re-entry, exercise every resource
                # configuration on the shared active-item resolver.
                self.game._change_item("1", "elixir", 1, "battle_audit")
                meta = {**self.game._resource_state_for(self.game._player("1")),
                        "name": "Van", "hp": 1, "max_hp": 100, "healing": 0,
                        "items_used": 0, "action": None}
                meta["mp"] = 0
                meta["ap"] = 0
                self.game.encounter_roster = {"1": meta}
                self.game.active_encounter = {"round": 1, "state": "combat"}
                queued = self.game.battle_item("1", "elixir")
                self.assertTrue(queued.ok, queued.messages)
                self.game._resolve_active_item("1", meta, meta["action"], [])
                self.assertEqual(meta["hp"], 100)
                for key in ("mp", "ap"):
                    self.assertEqual(meta[key], meta[f"max_{key}"] if meta[f"max_{key}"] else 0)
                self.assertEqual(self.game._inventory_qty("1", "elixir"), 0)
                self.game.active_encounter = None
                self.game.encounter_roster = {}

    def test_megalixir_restores_every_living_hero_without_requiring_dual_resource(self) -> None:
        self._set_job("blackmage")
        meta = self._open_active_battle()
        self.assertGreater(int(meta["max_mp"]), 0)
        self.assertEqual(int(meta["max_ap"]), 0)
        self.game._change_item("1", "megalixir", 1, "battle_audit")
        meta["hp"] = max(1, int(meta["max_hp"]) - 15)
        meta["mp"] = 0
        log = []
        queued = self.game.battle_item("1", "megalixir")
        self.assertTrue(queued.ok, queued.messages)
        self.game._resolve_active_item("1", meta, meta["action"], log)
        self.assertEqual(meta["hp"], meta["max_hp"])
        self.assertEqual(meta["mp"], meta["max_mp"])
        self.assertEqual(meta["ap"], 0)
        self.assertEqual(self.game._inventory_qty("1", "megalixir"), 0)
        self.assertTrue(any("MP" in message for message in log))

    def test_megalixir_recovers_mixed_party_and_skips_knocked_out_heroes(self) -> None:
        self.game._change_item("1", "megalixir", 1, "party_audit")
        ap_hero = {"name": "Warrior", "hp": 10, "max_hp": 100, "mp": 0, "max_mp": 0,
                   "ap": 0, "max_ap": 25, "healing": 0, "items_used": 0}
        mp_hero = {"name": "Mage", "hp": 20, "max_hp": 80, "mp": 1, "max_mp": 40,
                   "ap": 0, "max_ap": 0}
        ko_hero = {"name": "KO Mage", "hp": 0, "max_hp": 80, "mp": 1, "max_mp": 40,
                   "ap": 0, "max_ap": 0}
        self.game.encounter_roster = {"1": ap_hero, "2": mp_hero, "3": ko_hero}
        self.game.active_encounter = {"round": 1, "state": "combat"}
        queue = self.game.battle_item("1", "megalixir")
        self.assertTrue(queue.ok, queue.messages)
        self.game._resolve_active_item("1", ap_hero, ap_hero["action"], [])
        self.assertEqual((ap_hero["hp"], ap_hero["ap"]), (100, 25))
        self.assertEqual((mp_hero["hp"], mp_hero["mp"]), (80, 40))
        self.assertEqual((ko_hero["hp"], ko_hero["mp"]), (0, 1))
        self.assertEqual(self.game._inventory_qty("1", "megalixir"), 0)

    def test_raid_megalixir_recovers_mp_and_ap_party_members(self) -> None:
        self.game._change_item("1", "megalixir", 1, "raid_audit")
        warrior = {"name": "Warrior", "hp": 2, "max_hp": 80, "mp": 0, "max_mp": 0,
                   "ap": 0, "max_ap": 20, "healing": 0, "items_used": 0}
        mage = {"name": "Mage", "hp": 2, "max_hp": 70, "mp": 0, "max_mp": 35,
                "ap": 0, "max_ap": 0}
        self.game.raid_roster = {"1": warrior, "2": mage}
        log = []
        self.game._resolve_raid_item("1", warrior, {"item_id": "megalixir", "target_id": "party"}, [], log)
        self.assertEqual((warrior["hp"], warrior["ap"]), (80, 20))
        self.assertEqual((mage["hp"], mage["mp"]), (70, 35))
        self.assertEqual(self.game._inventory_qty("1", "megalixir"), 0)

    def test_field_elixir_heals_mp_caster_and_does_not_touch_unrelated_ap(self) -> None:
        self._set_job("blackmage")
        p = self.game._player("1")
        self.db.execute("UPDATE players SET current_mp=0,current_ap=3,current_hp=? WHERE twitch_id='1'", (max(1, self.game._max_hp(p) - 10),))
        self.game._change_item("1", "elixir", 1, "field_audit")
        result = self.game.use_item("1", "elixir")
        self.assertTrue(result.ok, result.messages)
        refreshed = self.game._player("1")
        self.assertEqual(int(refreshed["current_hp"]), self.game._max_hp(refreshed))
        self.assertEqual(self.game._resource_state_for(refreshed)["mp"], self.game._resource_state_for(refreshed)["max_mp"])
        self.assertEqual(int(refreshed["current_ap"]), 3)
        self.assertEqual(self.game._inventory_qty("1", "elixir"), 0)


if __name__ == "__main__":
    unittest.main()

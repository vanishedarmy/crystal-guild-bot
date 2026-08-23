from __future__ import annotations

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PortalActionWorker

ROOT = Path(__file__).resolve().parents[1]


class PortalActionWorkerTests(unittest.TestCase):
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
        self.game._change_item("100", "hunters_axe", 1, "test")
        self.game._change_item("100", "copper_pistol", 1, "test")
        self.game._change_item("100", "chain_mail", 1, "test")
        self.worker = PortalActionWorker(self.game, "https://guild.example", "sync-key")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def action(self, **overrides):
        action = {
            "id": "pa_test",
            "protocol_version": ACTION_PROTOCOL_VERSION,
            "twitch_id": "100",
            "username": "van",
            "type": "PING",
            "payload": {},
            "lease_token": "lease-token",
        }
        action.update(overrides)
        return action

    def test_ping_verifies_authoritative_numeric_twitch_identity(self):
        ok, message, data = self.worker._execute(self.action())
        self.assertTrue(ok)
        self.assertIn("Portal link verified", message)
        self.assertEqual(data["username"], "van")

        ok, message, _ = self.worker._execute(self.action(username="someoneelse"))
        self.assertFalse(ok)
        self.assertIn("ownership", message.lower())

        ok, message, _ = self.worker._execute(self.action(twitch_id="999"))
        self.assertFalse(ok)
        self.assertIn("no longer exists", message.lower())

    def test_phase_two_equips_and_unequips_owned_compatible_gear(self):
        ok, message, data = self.worker._execute(self.action(type="EQUIP_ITEM", payload={"item_id": "hunters_axe"}))
        self.assertTrue(ok)
        self.assertIn("equipped", message.lower())
        self.assertEqual(data["slot"], "weapon")
        row = self.db.one("SELECT weapon_id FROM equipment WHERE player_id='100'")
        self.assertEqual(row["weapon_id"], "hunters_axe")

        ok, message, data = self.worker._execute(self.action(type="UNEQUIP_SLOT", payload={"slot": "weapon"}))
        self.assertTrue(ok)
        self.assertIn("unequipped", message.lower())
        self.assertEqual(data["slot"], "weapon")
        row = self.db.one("SELECT weapon_id FROM equipment WHERE player_id='100'")
        self.assertIsNone(row["weapon_id"])

    def test_phase_two_revalidates_job_and_rejects_unsafe_action_types(self):
        ok, message, _ = self.worker._execute(self.action(type="EQUIP_ITEM", payload={"item_id": "copper_pistol"}))
        self.assertFalse(ok)
        self.assertIn("only be wielded", message.lower())
        for kind in ("COMMAND", "READYALL", "RAID"):
            ok, message, data = self.worker._execute(self.action(type=kind))
            self.assertFalse(ok)
            self.assertIn("not supported", message.lower())
            self.assertEqual(data, {})

    def test_phase_three_shop_state_buy_and_sell_are_authoritative(self):
        self.db.execute("UPDATE players SET gil=999999 WHERE twitch_id='100'")
        ok, message, data = self.worker._execute(self.action(id="pa_shop", type="SHOP_STATE", payload={}))
        self.assertTrue(ok)
        self.assertIn("stock ready", message.lower())
        self.assertTrue(data["stock"])
        offer = data["stock"][0]
        before_qty = self.game._inventory_qty("100", offer["id"])
        before_gil = int(self.game._player("100")["gil"])

        ok, message, purchase = self.worker._execute(self.action(
            id="pa_buy", type="BUY_ITEM", payload={"item_id": offer["id"], "quantity": 1}
        ))
        self.assertTrue(ok)
        self.assertIn("purchased", message.lower())
        self.assertEqual(self.game._inventory_qty("100", offer["id"]), before_qty + 1)
        self.assertEqual(int(self.game._player("100")["gil"]), before_gil - int(offer["price"]))
        self.assertEqual(purchase["gil"], before_gil - int(offer["price"]))

        ok, message, sale = self.worker._execute(self.action(
            id="pa_sell", type="SELL_ITEM", payload={"item_id": offer["id"], "quantity": 1}
        ))
        self.assertTrue(ok)
        self.assertIn("sold", message.lower())
        self.assertEqual(self.game._inventory_qty("100", offer["id"]), before_qty)
        self.assertGreaterEqual(sale["gil"], purchase["gil"])

    def test_phase_three_purchase_is_replay_safe_after_acknowledgement_loss(self):
        self.db.execute("UPDATE players SET gil=999999 WHERE twitch_id='100'")
        _, _, state = self.worker._execute(self.action(id="pa_shop_replay", type="SHOP_STATE", payload={}))
        offer = state["stock"][0]
        before_qty = self.game._inventory_qty("100", offer["id"])
        before_gil = int(self.game._player("100")["gil"])
        action = self.action(id="pa_buy_replay", type="BUY_ITEM", payload={"item_id": offer["id"], "quantity": 1})
        first = self.worker._execute(action)
        second = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertEqual(first[2], second[2])
        self.assertEqual(self.game._inventory_qty("100", offer["id"]), before_qty + 1)
        self.assertEqual(int(self.game._player("100")["gil"]), before_gil - int(offer["price"]))

    def test_phase_three_cannot_sell_last_equipped_copy_or_trade_during_combat(self):
        equipped = self.game.equip("100", "hunters_axe")
        self.assertTrue(equipped.ok)
        ok, message, _ = self.worker._execute(self.action(
            id="pa_sell_equipped", type="SELL_ITEM", payload={"item_id": "hunters_axe", "quantity": 1}
        ))
        self.assertFalse(ok)
        self.assertIn("unequip", message.lower())
        self.assertEqual(self.game._inventory_qty("100", "hunters_axe"), 1)

        self.game.encounter_roster["100"] = {"hp": 100}
        _, _, state = self.worker._execute(self.action(id="pa_shop_combat", type="SHOP_STATE", payload={}))
        self.assertTrue(state["combat_locked"])
        offer = state["stock"][0]
        ok, message, _ = self.worker._execute(self.action(
            id="pa_buy_combat", type="BUY_ITEM", payload={"item_id": offer["id"], "quantity": 1}
        ))
        self.assertFalse(ok)
        self.assertIn("active encounter or raid", message.lower())

    def test_phase_four_character_state_and_job_change_are_authoritative(self):
        ok, message, state = self.worker._execute(self.action(id="pa_char_state", type="CHARACTER_STATE", payload={}))
        self.assertTrue(ok)
        self.assertIn("character options", message.lower())
        self.assertEqual(state["current_job_id"], "warrior")
        self.assertEqual(state["stance"], "balanced")
        self.assertEqual(len(state["mastery_slots"]), 2)
        locked = [job for job in state["jobs"] if job.get("tier") != "starter" and not job["unlocked"]]
        self.assertTrue(locked)
        self.assertTrue(any(job["requirements"] for job in locked))

        ok, message, _ = self.worker._execute(self.action(
            id="pa_locked_job", type="CHANGE_JOB", payload={"job_id": "paladin"}
        ))
        self.assertFalse(ok)
        self.assertIn("locked", message.lower())
        self.assertEqual(self.game._player("100")["current_job"], "warrior")

        ok, message, changed = self.worker._execute(self.action(
            id="pa_job_change", type="CHANGE_JOB", payload={"job_id": "monk"}
        ))
        self.assertTrue(ok)
        self.assertIn("now a monk", message.lower())
        self.assertEqual(self.game._player("100")["current_job"], "monk")
        self.assertEqual(changed["character_state"]["current_job_id"], "monk")

    def test_phase_four_character_state_stays_within_hosted_result_limit(self):
        for job_id in self.game.data.jobs:
            self.db.execute(
                "INSERT INTO player_jobs(player_id,job_id,level,jp) VALUES ('100',?,50,0) "
                "ON CONFLICT(player_id,job_id) DO UPDATE SET level=50",
                (job_id,),
            )
        ok, _, state = self.worker._execute(self.action(id="pa_max_state", type="CHARACTER_STATE", payload={}))
        self.assertTrue(ok)
        encoded = json.dumps(state, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertLess(len(encoded), 16 * 1024)

    def test_phase_four_stance_and_mastery_management(self):
        ok, _, changed = self.worker._execute(self.action(
            id="pa_stance", type="SET_STANCE", payload={"stance": "defensive"}
        ))
        self.assertTrue(ok)
        self.assertEqual(self.game._player("100")["stance"], "defensive")
        self.assertEqual(changed["character_state"]["stance"], "defensive")

        self.db.execute("UPDATE player_jobs SET level=50 WHERE player_id='100' AND job_id='warrior'")
        ok, message, changed = self.worker._execute(self.action(
            id="pa_mastery", type="SET_MASTERY", payload={"job_id": "warrior", "slot": 1}
        ))
        self.assertTrue(ok)
        self.assertIn("mastery slot 1", message.lower())
        slot = self.db.one("SELECT job_id FROM mastery_slots WHERE player_id='100' AND slot=1")
        self.assertEqual(slot["job_id"], "warrior")
        self.assertEqual(changed["character_state"]["mastery_slots"][0]["job_id"], "warrior")

        ok, message, changed = self.worker._execute(self.action(
            id="pa_mastery_clear", type="CLEAR_MASTERY", payload={"slot": 1}
        ))
        self.assertTrue(ok)
        self.assertIn("cleared", message.lower())
        self.assertIsNone(self.db.one("SELECT job_id FROM mastery_slots WHERE player_id='100' AND slot=1"))
        self.assertIsNone(changed["character_state"]["mastery_slots"][0]["job_id"] )

    def test_phase_four_mutations_are_replay_safe_and_do_not_reapply_old_choices(self):
        action = self.action(id="pa_replay_job", type="CHANGE_JOB", payload={"job_id": "monk"})
        first = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertEqual(self.game._player("100")["current_job"], "monk")
        self.assertTrue(self.game.choose_job("100", "warrior").ok)
        self.assertEqual(self.game._player("100")["current_job"], "warrior")
        replay = self.worker._execute(action)
        self.assertTrue(replay[0])
        self.assertEqual(replay[2]["character_state"]["current_job_id"], "monk")
        self.assertEqual(self.game._player("100")["current_job"], "warrior")

    def test_phase_four_character_changes_refuse_active_combat(self):
        self.game.encounter_roster["100"] = {"hp": 100}
        for kind, payload in (
            ("CHANGE_JOB", {"job_id": "monk"}),
            ("SET_STANCE", {"stance": "defensive"}),
            ("CLEAR_MASTERY", {"slot": 1}),
        ):
            ok, message, _ = self.worker._execute(self.action(id=f"pa_lock_{kind.lower()}", type=kind, payload=payload))
            self.assertFalse(ok)
            self.assertIn("active encounter or raid", message.lower())


    def test_phase_five_recovery_state_exposes_live_resources_and_field_items(self):
        self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='100'")
        before_qty = self.game._inventory_qty("100", "potion")
        self.game._change_item("100", "potion", 2, "test")
        ok, message, data = self.worker._execute(self.action(id="pa_recovery_state", type="RECOVERY_STATE", payload={}))
        self.assertTrue(ok)
        self.assertIn("recovery", message.lower())
        state = data["recovery_state"]
        self.assertEqual(state["state"], "ready")
        self.assertEqual(state["hp"]["current"], 1)
        self.assertGreater(state["hp"]["max"], 1)
        potion = next(item for item in state["items"] if item["id"] == "potion")
        self.assertEqual(potion["quantity"], before_qty + 2)
        self.assertTrue(potion["field_usable"])
        self.assertTrue(potion["usable_now"])
        self.assertIn("HP", potion["preview"])

    def test_phase_five_field_item_use_is_replay_safe_and_refreshes_state(self):
        self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='100'")
        self.game._change_item("100", "potion", 2, "test")
        action = self.action(id="pa_use_potion", type="USE_FIELD_ITEM", payload={"item_id": "potion"})
        before_qty = self.game._inventory_qty("100", "potion")
        first = self.worker._execute(action)
        first_hp = int(self.game._player("100")["current_hp"])
        second = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertEqual(first[2], second[2])
        self.assertEqual(self.game._inventory_qty("100", "potion"), before_qty - 1)
        self.assertEqual(int(self.game._player("100")["current_hp"]), first_hp)
        self.assertEqual(first[2]["recovery_state"]["hp"]["current"], first_hp)

    def test_phase_five_camp_uses_absolute_deadline_and_is_replay_safe(self):
        self.db.execute("UPDATE players SET current_hp=1 WHERE twitch_id='100'")
        action = self.action(id="pa_start_rest", type="START_REST", payload={})
        first = self.worker._execute(action)
        self.assertTrue(first[0])
        state = first[2]["recovery_state"]
        self.assertEqual(state["state"], "resting")
        self.assertGreater(state["camp_until"], 0)
        rests = int(self.game._player("100")["rests"])
        second = self.worker._execute(action)
        self.assertTrue(second[0])
        self.assertEqual(second[2], first[2])
        self.assertEqual(int(self.game._player("100")["rests"]), rests)

    def test_phase_five_recovery_payload_is_bounded_and_battle_cures_remain_read_only(self):
        for item in self.game.data.items.values():
            if item.get("type") == "consumable":
                self.game._change_item("100", item["id"], 1, "test")
        ok, _, data = self.worker._execute(self.action(id="pa_recovery_bound", type="RECOVERY_STATE", payload={}))
        self.assertTrue(ok)
        state = data["recovery_state"]
        encoded = json.dumps(state, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertLess(len(encoded), 16 * 1024)
        antidote = next(item for item in state["items"] if item["id"] == "antidote")
        self.assertTrue(antidote["combat_only"])
        self.assertFalse(antidote["field_usable"])

    def test_phase_five_portal_recovery_refuses_field_item_during_combat(self):
        self.game._change_item("100", "potion", 1, "test")
        self.game.encounter_roster["100"] = {"hp": 1, "statuses": {}}
        ok, _, data = self.worker._execute(self.action(id="pa_recovery_combat", type="RECOVERY_STATE", payload={}))
        self.assertTrue(ok)
        self.assertTrue(data["recovery_state"]["combat_locked"])
        ok, message, _ = self.worker._execute(self.action(id="pa_use_combat", type="USE_FIELD_ITEM", payload={"item_id": "potion"}))
        self.assertFalse(ok)
        self.assertIn("active combat", message.lower())

    def test_phase_six_fellowship_state_exposes_only_live_project_resources(self):
        selected = self.game.set_fellowship_project("infirmary")
        self.assertTrue(selected.ok)
        self.db.execute("UPDATE players SET gil=12345 WHERE twitch_id='100'")
        self.game._change_item("100", "hi_potion", 4, "test")

        ok, message, data = self.worker._execute(self.action(
            id="pa_fellowship_state", type="FELLOWSHIP_STATE", payload={}
        ))
        self.assertTrue(ok)
        self.assertIn("contribution options", message.lower())
        state = data["fellowship_state"]
        self.assertEqual(state["gil"], 12345)
        self.assertEqual(state["project"]["facility_id"], "infirmary")
        gil_req = next(req for req in state["project"]["requirements"] if req["kind"] == "gil")
        item_req = next(req for req in state["project"]["requirements"] if req["kind"] == "item")
        activity_req = next(req for req in state["project"]["requirements"] if req["kind"] == "activity")
        self.assertEqual(gil_req["owned"], 12345)
        self.assertEqual(item_req["asset_id"], "hi_potion")
        self.assertEqual(item_req["owned"], 4)
        self.assertTrue(gil_req["contributable"] and item_req["contributable"] )
        self.assertFalse(activity_req["contributable"] )
        self.assertNotIn("twitch_id", json.dumps(state))

    def test_phase_six_gil_contribution_caps_refreshes_and_is_replay_safe(self):
        self.assertTrue(self.game.set_fellowship_project("infirmary").ok)
        self.db.execute("UPDATE players SET gil=10000 WHERE twitch_id='100'")
        action = self.action(id="pa_fellowship_gil", type="CONTRIBUTE_GIL", payload={"amount": 7000})

        first = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertIn("only 5,000 was needed", first[1].lower())
        self.assertEqual(int(self.game._player("100")["gil"]), 5000)
        state = first[2]["fellowship_state"]
        gil_req = next(req for req in state["project"]["requirements"] if req["kind"] == "gil")
        self.assertTrue(gil_req["complete"] )
        self.assertEqual(state["member"]["gil_donated"], 5000)

        replay = self.worker._execute(action)
        self.assertTrue(replay[0])
        self.assertEqual(replay[2], first[2])
        self.assertEqual(int(self.game._player("100")["gil"]), 5000)
        contributions = self.db.one("SELECT COUNT(*) AS c FROM fellowship_contributions WHERE player_id='100' AND kind='gil'")
        self.assertEqual(int(contributions["c"]), 1)

    def test_phase_six_material_contribution_uses_existing_transactional_path(self):
        self.assertTrue(self.game.set_fellowship_project("infirmary").ok)
        self.game._change_item("100", "hi_potion", 6, "test")
        action = self.action(
            id="pa_fellowship_item", type="CONTRIBUTE_ITEM", payload={"item_id": "hi_potion", "quantity": 3}
        )
        first = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertEqual(self.game._inventory_qty("100", "hi_potion"), 3)
        state = first[2]["fellowship_state"]
        item_req = next(req for req in state["project"]["requirements"] if req["asset_id"] == "hi_potion")
        self.assertEqual(item_req["current"], 3)
        self.assertEqual(item_req["owned"], 3)
        self.assertEqual(state["member"]["materials_donated"], 3)

        replay = self.worker._execute(action)
        self.assertTrue(replay[0])
        self.assertEqual(self.game._inventory_qty("100", "hi_potion"), 3)
        self.assertEqual(replay[2], first[2])

    def test_phase_six_contribution_payload_stays_within_hosted_result_limit(self):
        self.assertTrue(self.game.set_fellowship_project("infirmary").ok)
        ok, _, data = self.worker._execute(self.action(id="pa_fellowship_bound", type="FELLOWSHIP_STATE", payload={}))
        self.assertTrue(ok)
        encoded = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertLess(len(encoded), 16 * 1024)

    def test_phase_seven_crafting_state_compares_live_materials_and_forge_costs(self):
        self.db.execute("UPDATE players SET level=30,gil=50000,hunt_seals=500 WHERE twitch_id='100'")
        before_potions = self.game._inventory_qty("100", "potion")
        self.game._change_item("100", "potion", 6, "test")
        self.game._change_item("100", "iron_ore", 3, "test")
        ok, message, data = self.worker._execute(self.action(id="pa_crafting_state", type="CRAFTING_STATE", payload={}))
        self.assertTrue(ok)
        self.assertIn("blacksmith options", message.lower())
        state = data["crafting_state"]
        recipe = next(entry for entry in state["recipes"] if entry["id"] == "hi_potion_batch")
        self.assertGreaterEqual(recipe["max_quantity"], 2)
        potion = next(entry for entry in recipe["materials"] if entry["item_id"] == "potion")
        self.assertEqual(potion["owned"], before_potions + 6)
        forge = next(entry for entry in state["forge_rules"] if entry["current_upgrade"] == 0)
        self.assertEqual(forge["next_upgrade"], 1)
        self.assertTrue(any(entry["item_id"] == "iron_ore" for entry in forge["materials"]))
        self.assertNotIn("twitch_id", json.dumps(state))
        encoded = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertLess(len(encoded), 16 * 1024)

    def test_phase_seven_craft_is_replay_safe_and_refreshes_blacksmith_state(self):
        self.db.execute("UPDATE players SET level=30,gil=50000 WHERE twitch_id='100'")
        before_potions = self.game._inventory_qty("100", "potion")
        before_hi_potions = self.game._inventory_qty("100", "hi_potion")
        self.game._change_item("100", "potion", 6, "test")
        before_gil = int(self.game._player("100")["gil"])
        action = self.action(id="pa_craft_replay", type="CRAFT_RECIPE", payload={"recipe_id": "hi_potion_batch", "quantity": 2})
        first = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertEqual(self.game._inventory_qty("100", "potion"), before_potions)
        self.assertEqual(self.game._inventory_qty("100", "hi_potion"), before_hi_potions + 4)
        self.assertEqual(int(self.game._player("100")["gil"]), before_gil - 240)
        self.assertIn("crafting_state", first[2])
        replay = self.worker._execute(action)
        self.assertTrue(replay[0])
        self.assertEqual(replay[2], first[2])
        self.assertEqual(self.game._inventory_qty("100", "hi_potion"), before_hi_potions + 4)
        self.assertEqual(int(self.game._player("100")["crafts"]), 2)

    def test_phase_seven_forge_is_replay_safe_and_combat_locked(self):
        self.db.execute("UPDATE players SET gil=50000 WHERE twitch_id='100'")
        self.game._change_item("100", "iron_ore", 6, "test")
        action = self.action(id="pa_forge_replay", type="FORGE_ITEM", payload={"item_id": "hunters_axe"})
        first = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertEqual(self.game._upgrade_level("100", "hunters_axe"), 1)
        self.assertEqual(self.game._inventory_qty("100", "iron_ore"), 3)
        replay = self.worker._execute(action)
        self.assertTrue(replay[0])
        self.assertEqual(replay[2], first[2])
        self.assertEqual(self.game._upgrade_level("100", "hunters_axe"), 1)
        self.assertEqual(self.game._inventory_qty("100", "iron_ore"), 3)

        self.game.encounter_roster["100"] = {"hp": 100}
        blocked = self.worker._execute(self.action(id="pa_forge_combat", type="FORGE_ITEM", payload={"item_id": "hunters_axe"}))
        self.assertFalse(blocked[0])
        self.assertIn("active encounter or raid", blocked[1].lower())

    def test_portal_recruit_creates_one_authoritative_character_and_is_replay_safe(self):
        action = self.action(
            id="pa_recruit_web", twitch_id="300", username="newhero",
            type="RECRUIT", payload={"display_name": "New Hero"},
        )
        first = self.worker._execute(action)
        second = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertEqual(first[2], second[2])
        self.assertTrue(first[2]["recruited"])
        self.assertEqual(first[2]["username"], "newhero")
        player = self.game._player("300")
        self.assertIsNotNone(player)
        self.assertEqual(player["username"], "newhero")
        self.assertEqual(player["display_name"], "New Hero")
        self.assertEqual(int(player["gil"]), 250)
        self.assertEqual(self.game._inventory_qty("300", "potion"), 3)
        self.assertEqual(
            int(self.db.one("SELECT COUNT(*) AS n FROM transactions WHERE player_id='300' AND source='recruitment'")["n"]),
            1,
        )
        self.assertIsNotNone(self.db.one("SELECT player_id FROM fellowship_members WHERE player_id='300'"))

    def test_portal_recruit_announces_once_to_twitch_after_acknowledgement(self):
        announcements = []
        worker = PortalActionWorker(
            self.game, "https://guild.example", "sync-key", notify_result=announcements.append
        )
        action = self.action(
            id="pa_recruit_chat", twitch_id="301", username="webhero",
            type="RECRUIT", payload={"display_name": "Web Hero"},
        )
        result_attempts = 0

        def fake_post(path, payload):
            nonlocal result_attempts
            if path == "/api/actions/claim":
                return {"ok": True, "protocol_version": ACTION_PROTOCOL_VERSION, "actions": [action]}
            if path == "/api/actions/result":
                result_attempts += 1
                if result_attempts == 1:
                    raise RuntimeError("simulated acknowledgement loss")
                return {"ok": True}
            raise AssertionError(path)

        worker._post = fake_post
        with self.assertRaises(RuntimeError):
            worker.poll_once()
        self.assertEqual(announcements, [])
        self.assertEqual(worker.poll_once(), 1)
        self.assertEqual(len(announcements), 1)
        self.assertTrue(any("joined the Crystal Guild" in message for message in announcements[0].messages))
        self.assertEqual(self.game._inventory_qty("301", "potion"), 3)
        self.assertEqual(
            int(self.db.one("SELECT COUNT(*) AS n FROM transactions WHERE player_id='301' AND source='recruitment'")["n"]),
            1,
        )

    def test_phase_nine_adventure_state_is_live_player_safe_and_bounded(self):
        self.db.execute("UPDATE players SET level=35 WHERE twitch_id='100'")
        ok, message, data = self.worker._execute(self.action(id="pa_adventure_state", type="ADVENTURE_STATE", payload={}))
        self.assertTrue(ok)
        self.assertIn("adventure board", message.lower())
        state = data["adventure_state"]
        self.assertEqual(state["current_region"]["id"], "greenwind_plains")
        self.assertTrue(any(region["id"] == "sable_coast" and region["unlocked"] for region in state["regions"]))
        self.assertEqual(len(state["hunts"]), len(self.game.data.hunts))
        self.assertTrue(any(hunt["challengeable"] for hunt in state["hunts"]))
        self.assertNotIn("twitch_id", json.dumps(state))
        encoded = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertLess(len(encoded), 16 * 1024)

    def test_adventure_board_travel_remains_replay_safe(self):
        self.db.execute("UPDATE players SET level=20 WHERE twitch_id='100'")
        travel = self.action(id="pa_travel_sable", type="TRAVEL_REGION", payload={"region_id": "sable_coast"})
        first = self.worker._execute(travel)
        second = self.worker._execute(travel)
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertEqual(first[2], second[2])
        self.assertEqual(self.game._player("100")["current_region"], "sable_coast")

    def test_v112_rally_venture_start_and_join_are_twitch_only(self):
        for kind in ("VENTURE", "JOIN_ENCOUNTER"):
            ok, message, data = self.worker._execute(self.action(id=f"pa_{kind.lower()}", type=kind, payload={}))
            self.assertFalse(ok)
            self.assertIn("not supported", message.lower())
            self.assertEqual(data, {})

    def test_v112_adventure_state_marks_rally_venture_as_twitch_only(self):
        ok, _, data = self.worker._execute(self.action(id="pa_board_contract", type="ADVENTURE_STATE", payload={}))
        self.assertTrue(ok)
        venture = data["adventure_state"]["venture"]
        self.assertFalse(venture["portal_start_enabled"])
        self.assertFalse(venture["portal_join_enabled"])
        self.assertEqual(venture["encounter_chance_percent"], 70)
        self.assertEqual(venture["treasure_chance_percent"], 30)
        self.assertEqual(venture["max_enemy_levels_above_player"], 10)
        self.assertEqual(venture["rally_reward_bonus_per_level_percent"], 5)
        self.assertEqual(venture["rally_reward_bonus_max_percent"], 50)

    def test_phase_nine_hunt_acceptance_is_replay_safe_and_keeps_web_combat_read_only(self):
        self.db.execute("UPDATE players SET level=99 WHERE twitch_id='100'")
        hunt = next(iter(self.game.data.hunts.values()))
        action = self.action(id="pa_hunt_accept", type="CHALLENGE_HUNT", payload={"hunt_id": hunt["id"]})
        first = self.worker._execute(action)
        second = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertEqual(first[2], second[2])
        self.assertEqual(self.game.active_encounter["kind"], "hunt")
        self.assertEqual(self.game.active_encounter["hunt_id"], hunt["id"])
        self.assertFalse(first[2]["adventure_state"]["encounter"]["web_combat_controls"])
        cooldown = self.db.one("SELECT available_at FROM cooldowns WHERE player_id='100' AND action=?", (f"hunt:{hunt['id']}",))
        self.assertIsNotNone(cooldown)

    def test_phase_seven_daily_claim_is_replay_safe_and_uses_randomized_24_hour_reward(self):
        before_gil = int(self.game._player("100")["gil"])
        state_ok, _, state_data = self.worker._execute(self.action(id="pa_daily_state", type="DAILY_STATE", payload={}))
        self.assertTrue(state_ok)
        self.assertTrue(state_data["daily_state"]["available"])
        self.assertEqual(state_data["daily_state"]["provision_rolls"], 1)

        action = self.action(id="pa_daily_claim", type="CLAIM_DAILY", payload={})
        first = self.worker._execute(action)
        self.assertTrue(first[0])
        reward = int(first[2]["claimed_gil"])
        self.assertGreaterEqual(reward, int(state_data["daily_state"]["gil_min"]))
        self.assertLessEqual(reward, int(state_data["daily_state"]["gil_max"]))
        self.assertEqual(int(self.game._player("100")["gil"]), before_gil + reward)
        self.assertTrue(first[2]["provisions"])
        for provision in first[2]["provisions"]:
            self.assertGreaterEqual(self.game._inventory_qty("100", provision["item_id"]), int(provision["quantity"]))
        self.assertFalse(first[2]["daily_state"]["available"])

        quantities_after_first = {
            row["item_id"]: self.game._inventory_qty("100", row["item_id"]) for row in first[2]["provisions"]
        }
        replay = self.worker._execute(action)
        self.assertTrue(replay[0])
        self.assertEqual(replay[2], first[2])
        self.assertEqual(int(self.game._player("100")["gil"]), before_gil + reward)
        self.assertEqual(
            quantities_after_first,
            {item_id: self.game._inventory_qty("100", item_id) for item_id in quantities_after_first},
        )

        second_claim = self.worker._execute(self.action(id="pa_daily_claim_again", type="CLAIM_DAILY", payload={}))
        self.assertFalse(second_claim[0])
        self.assertIn("already claimed", second_claim[1].lower())
        self.assertFalse(second_claim[2]["daily_state"]["available"])

    def test_daily_portal_resolves_twitch_subscriber_tier_for_perks(self):
        self.worker.subscription_lookup = lambda _uid: {"tier": 3, "state": "SUBSCRIBED"}
        ok, _, data = self.worker._execute(self.action(id="pa_daily_sub", type="DAILY_STATE", payload={}))
        self.assertTrue(ok)
        self.assertEqual(data["daily_state"]["subscriber_tier"], 3)
        self.assertEqual(data["daily_state"]["provision_rolls"], 4)
        self.assertEqual(data["daily_state"]["subscriber_gil_bonus_percent"], 30)

    def test_equipment_actions_are_replay_safe(self):
        first = self.worker._execute(self.action(type="EQUIP_ITEM", payload={"item_id": "hunters_axe"}))
        second = self.worker._execute(self.action(type="EQUIP_ITEM", payload={"item_id": "hunters_axe"}))
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertFalse(second[2]["changed"])
        first = self.worker._execute(self.action(type="UNEQUIP_SLOT", payload={"slot": "weapon"}))
        second = self.worker._execute(self.action(type="UNEQUIP_SLOT", payload={"slot": "weapon"}))
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertFalse(second[2]["changed"])


    def test_equipment_actions_refuse_players_committed_to_active_combat(self):
        self.game.encounter_roster["100"] = {"hp": 100}
        ok, message, _ = self.worker._execute(self.action(type="EQUIP_ITEM", payload={"item_id": "hunters_axe"}))
        self.assertFalse(ok)
        self.assertIn("active encounter or raid", message.lower())
        row = self.db.one("SELECT weapon_id FROM equipment WHERE player_id='100'")
        self.assertIsNone(row["weapon_id"])

    def test_unequip_clamps_persistent_hp_after_losing_hp_bonus(self):
        result = self.game.equip("100", "chain_mail")
        self.assertTrue(result.ok)
        equipped_player = self.game._player("100")
        equipped_max = self.game._max_hp(equipped_player)
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='100'", (equipped_max,))
        ok, _, _ = self.worker._execute(self.action(type="UNEQUIP_SLOT", payload={"slot": "armor"}))
        self.assertTrue(ok)
        player = self.game._player("100")
        self.assertLessEqual(int(player["current_hp"]), self.game._max_hp(player))
        self.assertLess(int(player["current_hp"]), equipped_max)


    def test_v115_wayfarer_state_exposes_interactive_solo_rules(self):
        ok, message, data = self.worker._execute(self.action(id="pa_solo_state", type="ADVENTURE_STATE", payload={}))
        self.assertTrue(ok)
        self.assertIn("adventure board", message.lower())
        solo = data["adventure_state"]["solo_venture"]
        self.assertTrue(solo["portal_only"])
        self.assertTrue(solo["interactive"])
        self.assertEqual(solo["cooldown_seconds"], 420)
        self.assertEqual(solo["encounter_chance_percent"], 60)
        self.assertEqual(solo["treasure_chance_percent"], 40)
        self.assertEqual(solo["max_enemy_levels_above_player"], 3)
        self.assertEqual(solo["max_stages"], 3)
        self.assertEqual(solo["stage_bonus_percent"], 15)
        self.assertFalse(solo["resolves_immediately"])
        self.assertEqual(data["adventure_state"]["venture"]["max_enemy_levels_above_player"], 10)

    def test_v111h1_regular_venture_allows_enemy_up_to_plus_ten(self):
        self.db.execute("UPDATE players SET level=1, current_region='greenwind_plains' WHERE twitch_id='100'")
        with patch.object(self.game.rng, "random", return_value=0.99), \
             patch.object(self.game.rng, "choices", side_effect=lambda population, weights=None, k=1: [population[-1]]):
            result = self.game.venture("100", bypass_cooldown=True)
        self.assertTrue(result.ok)
        self.assertEqual(self.game.active_encounter["monster_id"], "spriggan")
        self.assertEqual(int(self.game.data.monsters["spriggan"]["level"]), 11)

    def test_v115_solo_treasure_is_replay_safe_and_stays_unbanked_until_return(self):
        self.db.execute("UPDATE players SET level=20 WHERE twitch_id='100'")
        before_ventures = int(self.game._player("100")["ventures"])
        before_items = sum(int(row["quantity"]) for row in self.db.all("SELECT quantity FROM inventory WHERE player_id='100'"))
        action = self.action(id="pa_solo_treasure", type="SOLO_VENTURE", payload={})
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 1.0):
            first = self.worker._execute(action)
            replay = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertEqual(first[2], replay[2])
        expedition = first[2]["adventure_state"]["solo_venture"]["expedition"]
        self.assertEqual(expedition["status"], "choice")
        self.assertEqual(expedition["stage"], 1)
        self.assertEqual(len(expedition["spoils"]["items"]), 1)
        self.assertEqual(int(self.game._player("100")["ventures"]), before_ventures + 1)
        after_start_items = sum(int(row["quantity"]) for row in self.db.all("SELECT quantity FROM inventory WHERE player_id='100'"))
        self.assertEqual(after_start_items, before_items)
        self.assertIsNone(self.db.one("SELECT renown FROM fellowship_events WHERE event_key LIKE 'solo_expedition:100:%'"))

        returned = self.worker._execute(self.action(id="pa_solo_return", type="SOLO_EXPEDITION_RETURN", payload={}))
        self.assertTrue(returned[0])
        after_return_items = sum(int(row["quantity"]) for row in self.db.all("SELECT quantity FROM inventory WHERE player_id='100'"))
        self.assertEqual(after_return_items, before_items + 1)
        event = self.db.one("SELECT renown,amount FROM fellowship_events WHERE event_key LIKE 'solo_expedition:100:%'")
        self.assertIsNotNone(event)
        self.assertEqual(int(event["renown"]), 4)
        self.assertGreater(self.game._cooldown_remaining("100", "solo_venture"), 0)
        self.assertEqual(self.game._cooldown_remaining("100", "venture"), 0)

    def test_v115_solo_encounter_is_player_paced_and_action_replay_safe(self):
        self.db.execute("UPDATE players SET level=20 WHERE twitch_id='100'")
        refreshed = self.game._player("100")
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id='100'", (self.game._max_hp(refreshed),))
        action = self.action(id="pa_solo_encounter", type="SOLO_VENTURE", payload={})
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0):
            first = self.worker._execute(action)
            replay = self.worker._execute(action)
        self.assertTrue(first[0])
        self.assertEqual(first[2], replay[2])
        expedition = first[2]["adventure_state"]["solo_venture"]["expedition"]
        self.assertEqual(expedition["status"], "combat")
        self.assertEqual(expedition["combat"]["round"], 1)
        self.assertLessEqual(int(expedition["combat"]["enemy"]["level"]), 23)
        self.assertTrue(expedition["combat"]["enemy"]["intent"])
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})

        # Keep the monster alive so one Portal action demonstrably resolves one round.
        state = self.game._solo_expedition_load("100")
        state["combat"]["encounter"]["monster_hp"] = max(99999, int(state["combat"]["encounter"]["monster_hp"]))
        state["combat"]["encounter"]["monster_max_hp"] = max(99999, int(state["combat"]["encounter"]["monster_max_hp"]))
        self.game._solo_expedition_save("100", state)
        attack = self.action(id="pa_solo_attack", type="SOLO_EXPEDITION_ACTION", payload={"action": "attack"})
        with patch.object(self.game, "_solo_resolve_enemy_intent", return_value=None):
            acted = self.worker._execute(attack)
            acted_replay = self.worker._execute(attack)
        self.assertTrue(acted[0])
        self.assertEqual(acted[2], acted_replay[2])
        after = acted[2]["adventure_state"]["solo_venture"]["expedition"]
        self.assertEqual(after["combat"]["round"], 2)
        self.assertEqual(after["last_round"]["round"], 1)

    def test_v1112h1_solo_venture_stays_silent_and_needs_no_scheduler_wake(self):
        self.db.execute("UPDATE players SET level=5 WHERE twitch_id='100'")
        announcements = []
        wakes = []
        worker = PortalActionWorker(
            self.game, "https://guild.example", "sync-key",
            notify_result=announcements.append, wake_encounter=lambda: wakes.append("wake"),
        )
        action = self.action(id="pa_solo_silent", type="SOLO_VENTURE", payload={})
        def fake_post(path, payload):
            if path == "/api/actions/claim":
                return {"ok": True, "protocol_version": ACTION_PROTOCOL_VERSION, "actions": [action]}
            if path == "/api/actions/result":
                return {"ok": True}
            raise AssertionError(path)
        worker._post = fake_post
        with patch("crystal_guild.engine.SOLO_VENTURE_TREASURE_CHANCE", 0.0):
            self.assertEqual(worker.poll_once(), 1)
        self.assertEqual(announcements, [])
        self.assertEqual(wakes, [])
        self.assertIsNone(self.game.active_encounter)


    def test_poll_once_claims_then_acknowledges_exact_lease(self):
        calls = []

        def fake_post(path, payload):
            calls.append((path, payload))
            if path == "/api/actions/claim":
                return {
                    "ok": True,
                    "protocol_version": ACTION_PROTOCOL_VERSION,
                    "actions": [self.action()],
                }
            if path == "/api/actions/result":
                return {"ok": True}
            raise AssertionError(path)

        self.worker._post = fake_post
        self.assertEqual(self.worker.poll_once(), 1)
        self.assertEqual(calls[0][0], "/api/actions/claim")
        self.assertEqual(calls[1][0], "/api/actions/result")
        result = calls[1][1]
        self.assertEqual(result["id"], "pa_test")
        self.assertEqual(result["lease_token"], "lease-token")
        self.assertTrue(result["ok"])

    def test_worker_is_disabled_without_both_relay_settings(self):
        self.assertFalse(PortalActionWorker(self.game, "", "sync-key").enabled)
        self.assertFalse(PortalActionWorker(self.game, "https://guild.example", "").enabled)
        self.assertTrue(self.worker.enabled)

    def test_protocol_mismatch_is_rejected_before_execution(self):
        ok, message, _ = self.worker._execute(self.action(protocol_version=999))
        self.assertFalse(ok)
        self.assertIn("protocol mismatch", message.lower())


if __name__ == "__main__":
    unittest.main()

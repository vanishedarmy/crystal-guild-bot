from __future__ import annotations

import random
import tempfile
import time
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class ActiveBattleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "active.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            venture_cooldown_seconds=0, venture_treasure_chance=0.0,
            encounter_join_seconds=5,
            encounter_round_seconds=5,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(11),
        )
        self.game.recruit("1", "van", "Van")
        self.game.choose_job("1", "warrior")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def start(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.assertTrue(opened.ok)
        started = self.game.start_encounter_battle(opened.data["encounter_id"])
        self.assertTrue(started.ok)
        return opened

    def add_white_mage(self):
        self.game.recruit("2", "aeris", "Aeris")
        self.game.choose_job("2", "whitemage")
        self.assertTrue(self.game.join_encounter("2", bypass_cooldown=True).ok)

    def test_catalog_has_active_abilities_for_every_job(self):
        self.data.validate_or_raise()
        self.assertEqual(set(self.data.jobs), set(self.data.active_abilities))
        self.assertTrue(all(len(rows) >= 3 for rows in self.data.active_abilities.values()))

    def test_rally_transitions_to_active_combat_with_hp_and_ap_for_warrior(self):
        opened = self.start()
        self.assertEqual(self.game.active_encounter["state"], "combat")
        self.assertEqual(self.game.active_encounter["round"], 1)
        actor = self.game.encounter_roster["1"]
        self.assertGreater(actor["hp"], 0)
        self.assertEqual(actor["mp"], 0)
        self.assertEqual(actor["max_mp"], 0)
        self.assertGreater(actor["ap"], 0)
        self.assertEqual(actor["ap"], actor["max_ap"])
        self.assertEqual(opened.data["encounter_id"], self.game.active_encounter["id"])

    def test_rally_venture_continues_past_legacy_round_12_while_party_and_enemy_live(self):
        opened = self.start()
        self.game.active_encounter["round"] = 12
        self.game.active_encounter["max_rounds"] = 0
        self.game.active_encounter["monster_hp"] = 99999
        self.game.active_encounter["monster_max_hp"] = 99999
        actor = self.game.encounter_roster["1"]
        actor["hp"] = max(1, int(actor["hp"]))
        self.assertTrue(self.game.battle_attack("1").ok)
        from unittest.mock import patch
        with patch.object(self.game, "_resolve_active_attack", return_value=None), patch.object(self.game, "_active_enemy_turn", return_value=None):
            result = self.game.advance_encounter_round(opened.data["encounter_id"])
        self.assertTrue(result.ok, result.messages)
        self.assertIsNotNone(self.game.active_encounter)
        self.assertEqual(int(self.game.active_encounter["round"]), 13)
        self.assertGreater(int(self.game.encounter_roster["1"]["hp"]), 0)
        self.assertGreater(int(self.game.active_encounter["monster_hp"]), 0)

    def test_attack_can_be_queued_and_replaced_before_resolution(self):
        self.start()
        first = self.game.battle_attack("1")
        self.assertTrue(first.ok)
        self.assertEqual(self.game.encounter_roster["1"]["action"]["kind"], "attack")
        second = self.game.battle_defend("1")
        self.assertTrue(second.ok)
        self.assertEqual(self.game.encounter_roster["1"]["action"]["kind"], "defend")

    def test_missing_action_defaults_to_attack(self):
        opened = self.start()
        monster_id = self.game.active_encounter["monster_id"]
        before = self.game.active_encounter["monster_hp"]
        result = self.game.advance_encounter_round(opened.data["encounter_id"])
        self.assertTrue(result.ok)
        if self.game.active_encounter:
            self.assertLess(self.game.active_encounter["monster_hp"], before)
        else:
            # A very low-level monster may have died to the fallback attack.
            self.assertTrue(result.data.get("encounter_finished"))
        self.assertIn(monster_id, self.data.monsters)

    def test_unlocked_physical_ability_spends_ap_only_when_round_resolves(self):
        opened = self.start()
        actor = self.game.encounter_roster["1"]
        before = actor["ap"]
        queued = self.game.battle_ability("1", "power break")
        self.assertTrue(queued.ok, queued.messages)
        self.assertIn("4AP", queued.messages[0])
        self.assertEqual(actor["ap"], before)
        self.game.advance_encounter_round(opened.data["encounter_id"])
        if self.game.active_encounter:
            self.assertEqual(self.game.encounter_roster["1"]["ap"], before - 4)
            self.assertEqual(self.game.encounter_roster["1"]["mp"], 0)

    def test_locked_active_ability_is_rejected(self):
        self.start()
        result = self.game.battle_ability("1", "armor break")
        self.assertFalse(result.ok)
        self.assertIn("not found or not unlocked", result.messages[0])

    def test_all_actions_queued_does_not_shorten_round_timer(self):
        self.game.recruit("2", "cloud", "Cloud")
        self.game.choose_job("2", "warrior")
        opened = self.game.venture("1", bypass_cooldown=True)
        self.game.join_encounter("2", bypass_cooldown=True)
        self.game.start_encounter_battle(opened.data["encounter_id"])
        scheduled = float(self.game.active_encounter["next_round_at"])
        first = self.game.battle_attack("1")
        self.assertFalse(first.data.get("all_actions_queued", False))
        second = self.game.battle_attack("2")
        self.assertTrue(second.data.get("all_actions_queued", False))
        self.assertEqual(float(self.game.active_encounter["next_round_at"]), scheduled)

    def test_action_after_round_deadline_is_rejected_without_resolving(self):
        opened = self.start()
        before_round = self.game.active_encounter["round"]
        before_hp = self.game.active_encounter["monster_hp"]
        self.game.active_encounter["next_round_at"] = time.time() - 0.01
        result = self.game.battle_attack("1")
        self.assertFalse(result.ok)
        self.assertIn("timer has closed", result.messages[0])
        self.assertEqual(self.game.active_encounter["round"], before_round)
        self.assertEqual(self.game.active_encounter["monster_hp"], before_hp)
        self.assertEqual(self.game.active_encounter["id"], opened.data["encounter_id"])

    def test_status_after_round_deadline_is_read_only(self):
        self.start()
        self.game.active_encounter["next_round_at"] = time.time() - 0.01
        before_round = self.game.active_encounter["round"]
        result = self.game.encounter_status()
        self.assertTrue(result.ok)
        self.assertIn("timer closed", " ".join(result.messages).lower())
        self.assertEqual(self.game.active_encounter["round"], before_round)

    def test_white_mage_cure_can_target_an_ally(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.add_white_mage()
        self.game.start_encounter_battle(opened.data["encounter_id"])
        warrior = self.game.encounter_roster["1"]
        warrior["hp"] = max(1, warrior["hp"] // 3)
        before = warrior["hp"]
        queued = self.game.battle_ability("2", "cure Van")
        self.assertTrue(queued.ok, queued.messages)
        self.game.battle_defend("1")
        self.game.advance_encounter_round(opened.data["encounter_id"])
        if self.game.active_encounter:
            self.assertGreater(self.game.encounter_roster["1"]["hp"], before)

    def test_battle_item_is_not_consumed_until_resolution(self):
        opened = self.start()
        actor = self.game.encounter_roster["1"]
        actor["hp"] = max(1, actor["hp"] // 2)
        before_qty = self.game._inventory_qty("1", "potion")
        queued = self.game.use_item("1", "potion")
        self.assertTrue(queued.ok, queued.messages)
        self.assertEqual(self.game._inventory_qty("1", "potion"), before_qty)
        self.game.advance_encounter_round(opened.data["encounter_id"])
        self.assertEqual(self.game._inventory_qty("1", "potion"), before_qty - 1)

    def test_phoenix_down_requires_ko_target_when_actor_is_alive(self):
        self.start()
        self.game._change_item("1", "phoenix_down", 1, "test")
        result = self.game.use_item("1", "phoenix down")
        self.assertFalse(result.ok)
        self.assertIn("KO'd ally target", result.messages[0])

    def test_active_battle_records_action_metrics(self):
        opened = self.start()
        monster_id = self.game.active_encounter["monster_id"]
        original_hp = self.data.monsters[monster_id]["hp"]
        # State HP is already scaled, so force the current battle target low.
        self.game.active_encounter["monster_hp"] = 1
        self.game.battle_attack("1")
        result = self.game.advance_encounter_round(opened.data["encounter_id"])
        self.data.monsters[monster_id]["hp"] = original_hp
        self.assertTrue(result.data.get("encounter_finished"))
        row = self.db.one("SELECT value FROM player_record_stats WHERE player_id='1' AND metric='active_actions'")
        self.assertIsNotNone(row)
        self.assertGreaterEqual(row["value"], 1)

    def test_encounter_status_exposes_round_hp_resource_and_action_count(self):
        self.start()
        result = self.game.encounter_status()
        text = " ".join(result.messages)
        self.assertIn("ACTIVE BATTLE", text)
        self.assertIn("Round 1", text)
        self.assertIn("HP", text)
        self.assertIn("AP", text)
        self.assertIn("actions", text)


    def test_raise_rejects_a_living_target_without_spending_mp(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        self.game.recruit("2", "aeris", "Aeris")
        self.game.choose_job("2", "whitemage")
        self.db.execute("UPDATE player_jobs SET level=30 WHERE player_id='2' AND job_id='whitemage'")
        self.db.execute("UPDATE players SET level=30, current_mp=NULL WHERE twitch_id='2'")
        self.assertTrue(self.game.join_encounter("2", bypass_cooldown=True).ok)
        self.game.start_encounter_battle(opened.data["encounter_id"])
        before = self.game.encounter_roster["2"]["mp"]
        result = self.game.battle_ability("2", "raise Van")
        self.assertFalse(result.ok)
        self.assertIn("KO'd ally", result.messages[0])
        self.assertEqual(self.game.encounter_roster["2"]["mp"], before)

    def test_stun_skips_the_enemy_turn(self):
        self.start()
        actor = self.game.encounter_roster["1"]
        before = actor["hp"]
        self.game.active_encounter["monster_statuses"] = {
            "stun": {"turns": 1, "magnitude": 0.0}
        }
        log = []
        monster = self.data.monsters[self.game.active_encounter["monster_id"]]
        self.game._active_enemy_turn(monster, log)
        self.assertEqual(actor["hp"], before)
        self.assertTrue(any("stunned" in line.lower() for line in log))

    def test_battle_ap_persists_into_the_next_encounter(self):
        opened = self.start()
        first_max = self.game.encounter_roster["1"]["max_ap"]
        self.assertTrue(self.game.battle_ability("1", "power break").ok)
        self.game.advance_encounter_round(opened.data["encounter_id"])
        spent_ap = int(self.db.one("SELECT current_ap FROM players WHERE twitch_id='1'")["current_ap"])
        self.assertLess(spent_ap, first_max)
        if self.game.active_encounter:
            self.game.abort_encounter()
        next_open = self.game.venture("1", bypass_cooldown=True)
        self.game.start_encounter_battle(next_open.data["encounter_id"])
        actor = self.game.encounter_roster["1"]
        self.assertEqual(actor["ap"], spent_ap)
        self.assertEqual(actor["max_ap"], first_max)

    def test_magic_job_uses_mp_and_not_ap(self):
        self.game.choose_job("1", "blackmage")
        opened = self.start()
        actor = self.game.encounter_roster["1"]
        self.assertGreater(actor["mp"], 0)
        self.assertEqual(actor["mp"], actor["max_mp"])
        self.assertEqual(actor["ap"], 0)
        before = actor["mp"]
        queued = self.game.battle_ability("1", "fire")
        self.assertTrue(queued.ok, queued.messages)
        self.assertIn("5MP", queued.messages[0])
        self.game.advance_encounter_round(opened.data["encounter_id"])
        if self.game.active_encounter:
            self.assertEqual(self.game.encounter_roster["1"]["mp"], before - 5)

    def test_silence_blocks_mp_but_not_ap_abilities(self):
        self.start()
        actor = self.game.encounter_roster["1"]
        actor["statuses"] = {"silence": {"turns": 2, "magnitude": 0.0}}
        physical = self.game.battle_ability("1", "power break")
        self.assertTrue(physical.ok, physical.messages)

        self.game.abort_encounter()
        self.game.choose_job("1", "blackmage")
        self.start()
        mage = self.game.encounter_roster["1"]
        mage["statuses"] = {"silence": {"turns": 2, "magnitude": 0.0}}
        magical = self.game.battle_ability("1", "fire")
        self.assertFalse(magical.ok)
        self.assertIn("Silenced", magical.messages[0])

    def test_defend_restores_ap_for_physical_jobs(self):
        opened = self.start()
        actor = self.game.encounter_roster["1"]
        actor["ap"] = max(0, actor["max_ap"] - 20)
        before = actor["ap"]
        self.assertTrue(self.game.battle_defend("1").ok)
        result = self.game.advance_encounter_round(opened.data["encounter_id"])
        self.assertTrue(result.ok)
        if self.game.active_encounter:
            self.assertGreater(self.game.encounter_roster["1"]["ap"], before)

    def test_full_hp_potion_action_does_not_consume_the_item(self):
        opened = self.start()
        before = self.game._inventory_qty("1", "potion")
        self.assertTrue(self.game.use_item("1", "potion").ok)
        self.game.advance_encounter_round(opened.data["encounter_id"])
        self.assertEqual(self.game._inventory_qty("1", "potion"), before)

    def test_admin_resolver_watchdog_preserves_living_battle(self):
        from unittest.mock import patch
        from crystal_guild.engine import GameResult

        opened = self.game.venture("1", bypass_cooldown=True)
        self.game.start_encounter_battle(opened.data["encounter_id"])
        actor = self.game.encounter_roster["1"]
        self.assertGreater(int(actor["hp"]), 0)
        self.assertGreater(int(self.game.active_encounter["monster_hp"]), 0)

        def no_terminal_round(_encounter_id=None):
            self.game.active_encounter["round"] = int(self.game.active_encounter.get("round", 1)) + 1
            return GameResult.success("technical test round", round_resolved=True)

        with patch("crystal_guild.engine.ADMIN_AUTOSIM_WATCHDOG_ROUNDS", 2), patch.object(
            self.game, "advance_encounter_round", side_effect=no_terminal_round
        ):
            result = self.game.resolve_encounter(opened.data["encounter_id"])

        self.assertTrue(result.ok, result.messages)
        self.assertFalse(result.data.get("encounter_finished"))
        self.assertTrue(result.data.get("combat_continues"))
        self.assertIsNotNone(self.game.active_encounter)
        self.assertGreater(int(self.game.encounter_roster["1"]["hp"]), 0)
        self.assertGreater(int(self.game.active_encounter["monster_hp"]), 0)

    def test_admin_resolver_uses_active_battle_and_clears_state(self):
        opened = self.game.venture("1", bypass_cooldown=True)
        result = self.game.resolve_encounter(opened.data["encounter_id"])
        self.assertTrue(result.ok)
        self.assertTrue(result.data.get("encounter_finished"))
        self.assertIsNone(self.game.active_encounter)
        self.assertEqual(self.game.encounter_roster, {})


if __name__ == "__main__":
    unittest.main()

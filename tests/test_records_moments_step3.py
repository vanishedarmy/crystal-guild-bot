"""Step 3: transactionally settled Moments, verified history and live producer hooks."""
from __future__ import annotations

import json
import random
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from crystal_guild.active_battle import apply_status

from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import CACTPOT_COST
from crystal_guild.moments import EVENT_FACTS
from crystal_guild.moments_progress import (award_settlement, best_record,
    reconcile_all_verified_history, reconcile_verified_history)
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class RecordsMomentsStep3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "game.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(self.db, self.data, rng=random.Random(1923),
                                      overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
                                      venture_cooldown_seconds=0)
        for pid, user in [("1", "van"), ("2", "mira"), ("3", "cid")]:
            self.assertTrue(self.game.recruit(pid, user, user.title()).ok)
            self.assertTrue(self.game.choose_job(pid, "warrior").ok)
        self.assertEqual(DATABASE_SCHEMA_VERSION, 23)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def unlocks(self, pid="1"):
        return {row["moment_id"] for row in self.db.all(
            "SELECT moment_id FROM player_moment_unlocks WHERE player_id=?", (pid,))}

    def event(self, moment_id, **overrides):
        moment = self.data.moments[moment_id]
        event_type = moment["trigger"]
        facts = {name: (False if typ is bool else 0 if typ is int else 0.0 if typ is float else "")
                 for name, typ in EVENT_FACTS[event_type].items()}
        # Synthetic settled-event fixtures must still describe a possible
        # party after Step 6 introduced semantic consistency checks.
        if event_type == "world_event_victory":
            facts.update(participant_count=2, living_party_count=1)
        if event_type == "raid_victory":
            facts.update(party_size_at_start=2, living_party_count=1)
        facts.update(event=event_type, settled=True)
        for rule in moment["condition"]["rules"]:
            if rule["op"] == "gte_multiple":
                facts[rule["other_field"]] = 10
                facts[rule["field"]] = 10 * rule["multiplier"]
            else:
                facts[rule["field"]] = rule["value"]
        facts.update(overrides)
        return facts

    def test_schema_23_additive_and_independent_existing_tables(self):
        self.assertEqual(self.db.schema_version(), 24)
        for table in ("player_moment_unlocks", "player_moment_reconciliation", "player_record_events",
                      "player_bestiary_mastery", "player_titles"):
            self.assertIsNotNone(self.db.one("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)))
        self.assertEqual(self.db.quick_check(), [])

    def test_once_only_moment_unlock_and_reserved_title_atomic(self):
        facts = self.event("moment_technically_alive")
        with self.db.tx() as conn:
            self.assertEqual(award_settlement(conn, self.data, "1", "battle:A", facts), ["Technically Alive"])
            self.assertEqual(award_settlement(conn, self.data, "1", "battle:A", facts), [])
            self.assertEqual(award_settlement(conn, self.data, "1", "battle:B", facts), [])
        self.assertEqual(self.unlocks(), {"moment_technically_alive"})
        row = self.db.one("SELECT * FROM player_moment_unlocks WHERE player_id='1'")
        self.assertEqual(row["event_key"], "battle:A")
        self.assertEqual(json.loads(row["evidence_json"])["final_hp"], 1)
        self.assertEqual(row["historical"], 0)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_titles WHERE player_id='1' AND title_id=?",
                         (row["title_id"],))["n"], 1)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM achievements WHERE player_id='1'")["n"], 0)

    def test_same_moment_is_independent_across_players(self):
        facts = self.event("moment_technically_alive")
        with self.db.tx() as conn:
            self.assertEqual(len(award_settlement(conn, self.data, "1", "same-event", facts)), 1)
            self.assertEqual(len(award_settlement(conn, self.data, "2", "same-event", facts)), 1)
        self.assertEqual(len(self.unlocks("1")), 1)
        self.assertEqual(len(self.unlocks("2")), 1)
        self.assertEqual(len(self.unlocks("3")), 0)

    def test_reject_unsettled_partial_fake_or_wrong_type_evidence(self):
        valid = self.event("moment_technically_alive")
        invalid = [dict(valid, settled=False), {"event": "combat_victory", "settled": True},
                   dict(valid, final_hp=True), dict(valid, event="unknown"),
                   dict(valid, player_alive=1)]
        for index, facts in enumerate(invalid):
            with self.subTest(index=index):
                with self.assertRaises(ValueError), self.db.tx() as conn:
                    award_settlement(conn, self.data, "1", f"fake:{index}", facts)
        self.assertFalse(self.unlocks())

    def test_moment_and_title_rollback_with_source_transaction(self):
        facts = self.event("moment_technically_alive")
        with self.assertRaises(RuntimeError):
            with self.db.tx() as conn:
                award_settlement(conn, self.data, "1", "rolled-back", facts)
                raise RuntimeError("source battle settlement failed")
        self.assertEqual(self.unlocks(), set())
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_titles WHERE player_id='1' AND title_id LIKE 'moment_title_%'")["n"], 0)

    def test_all_twelve_catalog_contracts_award_only_matching_settled_events(self):
        with self.db.tx() as conn:
            for moment_id in self.data.moments:
                facts = self.event(moment_id)
                unlocked = award_settlement(conn, self.data, "1", f"type:{moment_id}", facts)
                self.assertIn(self.data.moments[moment_id]["name"], unlocked, moment_id)
        self.assertEqual(self.unlocks(), set(self.data.moments))
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_titles WHERE player_id='1' AND title_id LIKE 'moment_title_%'")["n"], 12)

    def test_hp_percentage_boundary_cannot_unlock_at_11_percent(self):
        with self.db.tx() as conn:
            hi_venture = self.event("moment_should_have_packed_a_tent", final_hp_pct_pre_recovery_raw=11.0)
            self.assertEqual(award_settlement(conn, self.data, "1", "venture:11pct", hi_venture), [])
            low_venture = self.event("moment_should_have_packed_a_tent", final_hp_pct_pre_recovery_raw=10.0)
            self.assertIn("Should Have Packed a Tent", award_settlement(conn, self.data, "1", "venture:10pct", low_venture))
            hi_world = self.event("moment_a_little_too_close", highest_survivor_hp_pct_raw=11.0)
            self.assertEqual(award_settlement(conn, self.data, "2", "world:11pct", hi_world), [])
            low_world = self.event("moment_a_little_too_close", highest_survivor_hp_pct_raw=10.0)
            self.assertIn("A Little Too Close", award_settlement(conn, self.data, "2", "world:10pct", low_world))

    def test_only_two_verified_historical_backfills_once(self):
        for index, payout in enumerate((0, 5, 0, 0, 5), start=1):
            self.db.execute("INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) "
                            "VALUES ('1','mini_cactpot',10,?,'test','{}',?)", (payout, index))
        self.db.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source,created_at) "
                        "VALUES ('1','gil','gil',-25000,'shop',1)")
        self.db.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source,created_at) "
                        "VALUES ('2','gil','gil',-100000,'forge',1)")
        with self.db.tx() as conn:
            first = reconcile_verified_history(conn, self.data, "1")
            again = reconcile_verified_history(conn, self.data, "1")
            other = reconcile_verified_history(conn, self.data, "2")
        self.assertCountEqual(first, ["The House Sends Another Letter", "Retail Therapy"])
        self.assertEqual(again, [])
        self.assertEqual(other, [])
        self.assertEqual(self.unlocks(), {"moment_retail_therapy", "moment_five_cactpot_losses"})
        self.assertTrue(all(row["historical"] == 1 for row in self.db.all(
            "SELECT historical FROM player_moment_unlocks WHERE player_id='1'")))
        self.assertEqual(reconcile_all_verified_history(self.db, self.data)["moments_unlocked"], 0)

    def test_historical_draw_breaks_streak_and_nonshop_expenses_do_not_backfill(self):
        for index, payout in enumerate((0, 5, 0, 10, 0, 0, 0, 0), start=1):
            self.db.execute("INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) "
                            "VALUES ('1','mini_cactpot',10,?,'test','{}',?)", (payout, index))
        self.db.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) "
                        "VALUES ('1','gil','gil',-999999,'forge')")
        with self.db.tx() as conn:
            self.assertEqual(reconcile_verified_history(conn, self.data, "1"), [])
        self.assertFalse(self.unlocks())

    def test_best_records_store_only_better_real_values_per_player(self):
        with self.db.tx() as conn:
            self.assertTrue(best_record(conn, "1", "closest_victory", 11, "fight1", lower_is_better=True))
            self.assertFalse(best_record(conn, "1", "closest_victory", 30, "fight2", lower_is_better=True))
            self.assertTrue(best_record(conn, "1", "closest_victory", 3, "fight3", lower_is_better=True,
                                        context={"monster": "Behemoth"}))
            self.assertTrue(best_record(conn, "2", "closest_victory", 2, "fight4", lower_is_better=True))
            self.assertTrue(best_record(conn, "1", "longest_venture", 60, "venture1"))
            self.assertTrue(best_record(conn, "1", "longest_venture", 70, "venture2"))
            self.assertFalse(best_record(conn, "1", "longest_venture", 59, "venture3"))
        self.assertEqual(self.db.one("SELECT best_value FROM player_record_events WHERE player_id='1' AND record_id='closest_victory'")["best_value"], 3)
        repo = PortalRepository(self.path, ROOT / "data")
        try:
            records = {r["id"]: r for r in repo.records("van")["personal_records"]["records"]}
            self.assertEqual(records["closest_victory"]["value"], 3)
            self.assertEqual(records["closest_victory"]["context"]["monster"], "Behemoth")
            self.assertEqual(records["longest_venture"]["value"], 70)
            self.assertEqual(records["closest_world_event"]["status"], "awaiting_tracking")
        finally:
            repo.close()

    def test_shop_actual_single_purchase_awards_retail_therapy(self):
        self.db.execute("UPDATE players SET gil=100000 WHERE twitch_id='1'")
        item = dict(self.data.items["potion"], price=26000)
        self.game._find_shop_offer = lambda _pid, _query: (item, None)
        self.assertTrue(self.game.buy("1", "potion", 1).ok)
        self.assertEqual(self.unlocks(), {"moment_retail_therapy"})
        self.assertEqual(self.db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"], 74000)
        self.assertTrue(self.game.buy("1", "potion", 1).ok)
        self.assertEqual(self.unlocks(), {"moment_retail_therapy"})

    def test_real_cactpot_settlement_awards_fifth_loss_and_action_replay_is_safe(self):
        # Four fully persisted paid losses; the real Portal ticket is fifth.
        for index in range(4):
            self.db.execute("INSERT INTO gold_saucer_history(player_id,game,wager,payout,outcome,details_json,created_at) "
                            "VALUES ('1','mini_cactpot',10,5,'sum_7','{}',?)", (1000 + index,))
        self.assertTrue(self.game.portal_cactpot_start("1", "ticket-test").ok)
        self.db.execute("UPDATE gold_saucer_cactpot SET grid_json=?,revealed_json=?,state='line' WHERE player_id='1'",
                        (json.dumps([1, 2, 4, 3, 5, 6, 7, 8, 9]), json.dumps([0, 1, 2, 3])))
        result = self.game.portal_cactpot_line("1", 0, "ticket-line-test")
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(result.data["cactpot_payout"], 5)
        self.assertIn("moment_five_cactpot_losses", self.unlocks())
        again = self.game.portal_cactpot_line("1", 0, "ticket-line-test")
        self.assertTrue(again.ok)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id='1' AND game='mini_cactpot'")["n"], 5)
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_moment_unlocks WHERE player_id='1'")["n"], 1)

    def test_venture_final_hp_percentage_and_genuine_closest_victory(self):
        self.assertTrue(self.game.venture("1", bypass_cooldown=True).ok)
        self.assertTrue(self.game.start_encounter_battle().ok)
        actor = self.game.encounter_roster["1"]
        actor["hp"] = max(1, int(actor["max_hp"]) // 2)
        actor["items_used"] = 0
        self.assertTrue(self.game._finish_active_encounter(True).ok)
        self.assertNotIn("moment_should_have_packed_a_tent", self.unlocks())
        first = self.db.one("SELECT best_value FROM player_record_events WHERE player_id='1' AND record_id='closest_victory'")
        self.assertGreater(first["best_value"], 1)
        self.assertTrue(self.game.venture("1", bypass_cooldown=True).ok)
        self.assertTrue(self.game.start_encounter_battle().ok)
        self.game.encounter_roster["1"].update(hp=1, items_used=0)
        self.assertTrue(self.game._finish_active_encounter(True).ok)
        self.assertIn("moment_should_have_packed_a_tent", self.unlocks())
        self.assertIn("moment_technically_alive", self.unlocks())
        self.assertEqual(self.db.one("SELECT best_value FROM player_record_events WHERE player_id='1' AND record_id='closest_victory'")["best_value"], 1)

    def test_live_raid_last_survivor_revived_final_blow_and_repeat_finish(self):
        for pid in ("1", "2", "3"):
            self.db.execute("UPDATE players SET level=70 WHERE twitch_id=?", (pid,))
        self.assertTrue(self.game.spawn_boss("ifrit").ok)
        for pid in ("1", "2", "3"):
            self.assertTrue(self.game.raid_join(pid).ok)
        self.assertTrue(self.game.start_raid().ok)
        self.assertEqual(self.game.active_boss["moment_party_size_at_start"], 3)
        for pid in ("2", "3"):
            self.game.raid_roster[pid]["hp"] = 0
        self.game.raid_roster["1"].update(hp=1, _moment_revived_during_raid=True)
        self.game.active_boss["current_hp"] = 1
        dealt = self.game._raid_damage_boss("1", self.game.raid_roster["1"], 300, [], use_limit=False)
        self.assertEqual(dealt, 1)
        self.assertTrue(self.game._finish_raid(True).ok)
        self.assertIn("moment_last_one_standing", self.unlocks())
        self.assertIn("moment_back_on_the_payroll", self.unlocks())
        self.assertIn("moment_technically_alive", self.unlocks())
        self.assertEqual(self.unlocks("2") & {"moment_last_one_standing", "moment_back_on_the_payroll"}, set())
        self.assertEqual(self.db.one("SELECT COUNT(*) AS n FROM player_moment_unlocks WHERE player_id='1'")["n"], len(self.unlocks()))


    def test_world_event_final_hp_threshold_uses_percent_not_fraction(self):
        for pid, level in (("1", 42), ("2", 57)):
            self.db.execute("UPDATE players SET level=? WHERE twitch_id=?", (level, pid))
        started = self.game.maybe_spawn_world_event(stream_live=True, now=time.time(), force=True)
        self.assertTrue(started.ok, started.messages)
        eid = str(started.data["encounter_id"])
        for pid in ("1", "2"):
            joined = self.game.portal_live_event_join(pid, "world_event", eid,
                    f"test-world-join-{pid}", stream_live=True)
            self.assertTrue(joined.ok, joined.messages)
        self.assertTrue(self.game.start_encounter_battle(int(eid)).ok)
        # One survivor at 11% disqualifies the entire party, even if another is at 1%.
        first = self.game.encounter_roster["1"]
        other = self.game.encounter_roster["2"]
        first["hp"] = 1
        other["hp"] = max(1, int(other["max_hp"]) * 11 // 100 + 1)
        self.assertTrue(self.game._finish_active_encounter(True).ok)
        self.assertNotIn("moment_a_little_too_close", self.unlocks("1"))
        self.assertNotIn("moment_a_little_too_close", self.unlocks("2"))
        self.assertIsNotNone(self.db.one("SELECT best_value FROM player_record_events WHERE player_id='1' AND record_id='closest_world_event'"))


    def test_two_nearly_dead_world_event_survivors_unlock_secret_once(self):
        for pid, level in (("1", 42), ("2", 57)):
            self.db.execute("UPDATE players SET level=? WHERE twitch_id=?", (level, pid))
        started = self.game.maybe_spawn_world_event(stream_live=True, now=time.time(), force=True)
        self.assertTrue(started.ok, started.messages)
        eid = str(started.data["encounter_id"])
        for pid in ("1", "2"):
            self.assertTrue(self.game.portal_live_event_join(pid, "world_event", eid,
                            f"secret-world-join-{pid}", stream_live=True).ok)
        self.assertTrue(self.game.start_encounter_battle(int(eid)).ok)
        for pid in ("1", "2"):
            self.game.encounter_roster[pid]["hp"] = 1
        self.assertTrue(self.game._finish_active_encounter(True).ok)
        for pid in ("1", "2"):
            self.assertIn("moment_a_little_too_close", self.unlocks(pid))
            self.assertEqual(self.db.one("SELECT best_value FROM player_record_events "
                  "WHERE player_id=? AND record_id='closest_world_event'", (pid,))["best_value"], 1)

    def test_live_finishing_hit_while_poisoned_awards_two_distinct_moments(self):
        self.assertTrue(self.game.venture("1", bypass_cooldown=True).ok)
        self.assertTrue(self.game.start_encounter_battle().ok)
        actor = self.game.encounter_roster["1"]
        apply_status(actor.setdefault("statuses", {}), "poison", 2, 0.05)
        self.game.active_encounter["monster_max_hp"] = 100
        self.game.active_encounter["monster_hp"] = 1
        self.game._moment_field_direct_hit(actor, 200, 1)
        self.assertTrue(self.game._finish_active_encounter(True).ok)
        self.assertIn("moment_a_toxic_relationship", self.unlocks())
        self.assertIn("moment_overkill_enthusiast", self.unlocks())

    def test_first_enemy_attack_ko_after_expensive_item_awards_two_moments(self):
        self.assertTrue(self.game.venture("1", bypass_cooldown=True).ok)
        self.assertTrue(self.game.start_encounter_battle().ok)
        actor = self.game.encounter_roster["1"]
        actor.update(hp=5, actions=0, _moment_last_self_item={
            "price": 1200, "actions_at_item": 0, "hostile_action_serial": 0,
        })
        self.game.active_encounter["_moment_hostile_serial"] = 1
        monster = self.game._encounter_monster(self.game.active_encounter)
        with patch.object(self.game, "_enemy_damage_against", return_value=10):
            self.assertEqual(self.game._apply_enemy_hit(monster, actor, {}, scaling="physical", power=1), 10)
        self.assertEqual(actor["hp"], 0)
        self.assertTrue(self.game._finish_active_encounter(False).ok)
        self.assertIn("moment_early_checkout", self.unlocks())
        self.assertIn("moment_money_well_wasted", self.unlocks())

    def test_existing_schema_22_upgrades_to_23_with_verified_backup_and_no_reset(self):
        self.db.execute("INSERT INTO player_bestiary_mastery(player_id,monster_id,research_points,source_defeats) "
                        "VALUES ('1','goblin',1,20)")
        self.db.close()
        with sqlite3.connect(self.path) as conn:
            for table in ("player_moment_unlocks", "player_moment_reconciliation", "player_record_events"):
                conn.execute(f"DROP TABLE {table}")
            conn.execute("DELETE FROM schema_migrations WHERE version=23")
        self.db = Database(self.path)
        self.assertEqual(self.db.schema_version(), 24)
        self.assertIsNotNone(self.db.pre_migration_backup_path)
        self.assertIn("pre_schema_23_", self.db.pre_migration_backup_path.name)
        with sqlite3.connect(self.db.pre_migration_backup_path) as backup:
            self.assertEqual(backup.execute("PRAGMA quick_check").fetchone()[0], "ok")
            self.assertEqual(backup.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0], 22)
        self.assertEqual(self.db.one("SELECT source_defeats FROM player_bestiary_mastery WHERE player_id='1' AND monster_id='goblin'")["source_defeats"], 20)
        self.assertEqual(self.db.quick_check(), [])


if __name__ == "__main__":
    unittest.main()

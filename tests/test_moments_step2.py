"""Step 2 Moments: complete trigger contracts, secrecy and no premature rewards."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.moments import matches_settlement, public_moments_view, validate_moment_catalog
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class MomentsStep2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GameData(ROOT / "data")

    def event(self, suffix: str, **changed):
        moment = self.data.moments[f"moment_{suffix}"]
        facts = {"event": moment["trigger"], "settled": True}
        multiple_rules = []
        for rule in moment["condition"]["rules"]:
            if rule["op"] == "gte_multiple":
                multiple_rules.append(rule)
            else:
                facts[rule["field"]] = rule["value"]
        for rule in multiple_rules:
            facts.setdefault(rule["other_field"], 10)
            facts[rule["field"]] = facts[rule["other_field"]] * rule["multiplier"]
        facts.update(changed)
        return facts

    def check(self, suffix: str, expected: bool = True, **changed):
        moment = self.data.moments[f"moment_{suffix}"]
        self.assertIs(matches_settlement(moment, self.event(suffix, **changed)), expected)

    def test_catalog_is_distinct_complete_and_validated_with_existing_data(self):
        self.assertEqual(len(self.data.moments), 12)
        self.assertEqual(len(self.data.moment_titles), 12)
        self.assertEqual(self.data.validate(), [])
        self.assertEqual(len(self.data.achievements), 89)
        self.assertEqual(len(self.data.titles), 122)
        self.assertEqual(sum(bool(m["secret"]) for m in self.data.moments.values()), 7)
        self.assertEqual(sum(m["backfill"] == "verified_saved_history"
                             for m in self.data.moments.values()), 2)
        self.assertEqual({m["condition"]["record_id"] for m in self.data.moments.values()
                          if m["backfill"] == "verified_saved_history"},
                         {"longest_cactpot_loss_streak", "biggest_purchase"})
        self.assertNotIn("moment_title_five_cactpot_losses", self.data.titles)
        self.assertIn("house_always_wins", self.data.achievements)

    def test_each_of_the_twelve_moments_matches_only_settled_trusted_shape(self):
        for moment in self.data.moments.values():
            suffix = moment["id"].removeprefix("moment_")
            with self.subTest(moment=suffix):
                self.check(suffix)
                self.check(suffix, False, settled=False)
                self.check(suffix, False, event="unrelated_event")
                self.check(suffix, False, **{moment["condition"]["rules"][0]["field"]: None})

    def test_fatal_item_misfortune_requires_exact_next_hostile_action(self):
        self.check("money_well_wasted", False, self_item_shop_price_gil=999)
        self.check("money_well_wasted", False, next_hostile_action_caused_ko=False)
        self.check("money_well_wasted", False, player_actions_since_item=1)
        self.check("money_well_wasted", False, same_battle=False)
        self.check("money_well_wasted", False, item_targeted_self=False)
        self.check("money_well_wasted", False, self_item_consumed=False)
        self.check("money_well_wasted", False, self_item_restorative=False)
        self.check("money_well_wasted", False, ko_source="poison_tick")
        self.check("money_well_wasted", True, self_item_shop_price_gil=1000)
        self.check("early_checkout", False, player_actions_completed=1)
        self.check("early_checkout", False, first_hostile_action_of_encounter=False)
        self.check("early_checkout", False, ko_source="self_damage")

    def test_combat_and_group_battle_boundaries(self):
        self.check("technically_alive", False, final_hp=2)
        self.check("technically_alive", False, player_alive=False)
        self.check("a_toxic_relationship", False, poison_active_at_hit=False)
        self.check("a_toxic_relationship", False, direct_hit=False)
        self.check("overkill_enthusiast", True, target_hp_before_hit=10, damage_dealt=100)
        self.check("overkill_enthusiast", False, target_hp_before_hit=10, damage_dealt=99)
        self.check("overkill_enthusiast", False, target_max_hp=99)
        self.check("a_little_too_close", False, highest_survivor_hp_pct_raw=10.001)
        self.check("a_little_too_close", False, living_party_count=1)
        self.check("against_better_judgment", False, boss_effective_level_gap=9)
        self.check("against_better_judgment", False, merc_assisted=True)
        self.check("last_one_standing", False, party_size_at_start=2)
        self.check("last_one_standing", False, living_party_count=2)
        self.check("last_one_standing", False, player_contribution_eligible=False)
        self.check("back_on_the_payroll", False, player_revived_during_raid=False)
        self.check("back_on_the_payroll", False, player_dealt_final_blow=False)

    def test_record_thresholds_cannot_be_awarded_by_unrelated_events(self):
        self.check("five_cactpot_losses", False, record_value=4)
        self.check("five_cactpot_losses", False, paid_net_loss=False)
        self.check("five_cactpot_losses", False, game="slots")
        self.check("five_cactpot_losses", False, record_id="longest_saucer_loss_streak")
        self.check("retail_therapy", False, record_value=24999)
        self.check("retail_therapy", False, qualifying_shop_purchase=False)
        self.check("retail_therapy", False, single_transaction=False)
        self.check("retail_therapy", True, record_value=25000)
        self.check("should_have_packed_a_tent", False, final_hp_pct_pre_recovery_raw=10.01)
        self.check("should_have_packed_a_tent", False, consumables_used=1)

    def test_secret_projection_does_not_leak_locked_names_ids_rules_or_titles(self):
        anonymous = public_moments_view(self.data.moments, self.data.moment_titles, set())
        self.assertEqual(len(anonymous), 12)
        raw = json.dumps(anonymous, ensure_ascii=False).casefold()
        for moment in self.data.moments.values():
            if not moment["secret"]:
                continue
            title = self.data.moment_titles[moment["reward"]["title_id"]]
            self.assertNotIn(moment["name"].casefold(), raw)
            self.assertNotIn(moment["id"].casefold(), raw)
            self.assertNotIn(title["name"].casefold(), raw)
            self.assertNotIn(moment["reward"]["badge_id"].casefold(), raw)
            self.assertNotIn(moment["trigger"].casefold(), raw)
        self.assertEqual(sum(r["name"] == "Undiscovered Moment" for r in anonymous), 7)
        self.assertEqual(sum(r["unlocked"] for r in anonymous), 0)

    def test_secret_unlocks_are_player_specific_and_the_title_reveals_only_on_unlock(self):
        unlocked = {"moment_technically_alive"}
        a = public_moments_view(self.data.moments, self.data.moment_titles, unlocked)
        b = public_moments_view(self.data.moments, self.data.moment_titles, set())
        self.assertEqual(sum(r["unlocked"] for r in a), 1)
        self.assertEqual(sum(r["unlocked"] for r in b), 0)
        self.assertIn("Too Stubborn to Die", [r["reward_title"] for r in a])
        self.assertNotIn("Too Stubborn to Die", [r["reward_title"] for r in b])
        self.assertEqual(sum(r["name"] == "Undiscovered Moment" for r in a), 6)

    def test_catalog_validation_rejects_collisions_and_unverifiable_moments(self):
        titles = copy.deepcopy(self.data.moment_titles)
        moments = copy.deepcopy(self.data.moments)
        target = moments["moment_five_cactpot_losses"]
        target["condition"]["record_id"] = "closest_victory"
        errors = validate_moment_catalog(moments, titles, self.data.achievements, self.data.titles)
        self.assertTrue(any("no proven saved-history" in issue for issue in errors))
        titles["moment_title_technically_alive"]["name"] = "Certified Floor Inspector"
        errors = validate_moment_catalog(moments, titles, self.data.achievements, self.data.titles)
        self.assertTrue(any("duplicates a live title name" in issue for issue in errors))
        moments["moment_technically_alive"]["condition"]["rules"][1]["value"] = True
        errors = validate_moment_catalog(moments, titles, self.data.achievements, self.data.titles)
        self.assertTrue(any("value has wrong type" in issue for issue in errors))

    def test_records_moments_projection_and_achievement_reads_do_not_award_new_titles(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "guild.db"
            db = Database(db_path)
            engine = CrystalGuildEngine(db, self.data)
            self.assertTrue(engine.recruit("moments-a", "moment_a", "Moment A").ok)
            repo = PortalRepository(db_path, ROOT / "data")
            try:
                before_achievements = db.one("SELECT COUNT(*) AS n FROM achievements WHERE player_id=?", ("moments-a",))["n"]
                before_titles = db.one("SELECT COUNT(*) AS n FROM player_titles WHERE player_id=?", ("moments-a",))["n"]
                for _ in range(3):
                    records = repo.records("moment_a")
                    old_achievements = repo.achievements("moment_a")
                    public_moments_view(self.data.moments, self.data.moment_titles, set())
                    matches_settlement(self.data.moments["moment_technically_alive"], self.event("technically_alive"))
                self.assertEqual(db.one("SELECT COUNT(*) AS n FROM achievements WHERE player_id=?", ("moments-a",))["n"], before_achievements)
                self.assertEqual(db.one("SELECT COUNT(*) AS n FROM player_titles WHERE player_id=?", ("moments-a",))["n"], before_titles)
                self.assertIn("moments", records)
                self.assertEqual(records["moments"]["summary"], {"unlocked": 0, "total": 12})
                self.assertEqual(sum(row["name"] == "Undiscovered Moment" for row in records["moments"]["entries"]), 7)
                self.assertNotIn("moments", old_achievements)
                self.assertEqual(old_achievements["summary"]["total"], 89)
            finally:
                repo.close()
                db.close()


if __name__ == "__main__":
    unittest.main()

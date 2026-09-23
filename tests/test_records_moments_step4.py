"""Step 4: read-only spoiler-safe Portal view and genuinely owned Title selection."""
from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.moments_progress import award_settlement, reconcile_verified_history
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class RecordsMomentsStep4Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "game.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db, self.data, rng=random.Random(44),
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
        )
        for pid, username in (("1", "van"), ("2", "mira")):
            self.assertTrue(self.game.recruit(pid, username, username.title()).ok)
        self.repo = PortalRepository(self.db.path, ROOT / "data")

    def tearDown(self):
        self.repo.close()
        self.db.close()
        self.tmp.cleanup()

    def unlock_1hp(self, player_id="1", historical=False):
        with self.db.tx() as conn:
            return award_settlement(conn, self.data, player_id, f"battle:{player_id}", {
                "event": "combat_victory", "settled": True,
                "player_alive": True, "final_hp": 1,
            }, historical=historical)

    def test_no_moments_spoiler_or_new_titles_before_ownership(self):
        payload = self.repo.records("van")
        self.assertEqual(payload["moments"]["summary"], {"unlocked": 0, "total": 12})
        self.assertEqual(len(payload["moments"]["entries"]), 12)
        self.assertEqual(len([m for m in payload["moments"]["entries"] if m["secret"] and not m["unlocked"]]), 7)
        raw = json.dumps(payload["moments"], ensure_ascii=False)
        self.assertNotIn("Too Stubborn to Die", raw)
        self.assertNotIn("moment_technically_alive", raw)
        self.assertNotIn("moment_title_technically_alive", raw)
        self.assertNotIn("moment_badge_technically_alive", raw)
        self.assertNotIn("trophy_candidate_id", raw)
        self.assertNotIn("event_key", raw)
        self.assertNotIn("evidence_json", raw)
        titles = self.repo.achievements("van")
        self.assertEqual(len(titles["titles"]), len(self.data.titles))
        self.assertNotIn("Too Stubborn to Die", json.dumps(titles))

    def test_one_players_unlock_stays_private_from_another_profile(self):
        self.unlock_1hp()
        van = self.repo.records("van")["moments"]
        mira = self.repo.records("mira")["moments"]
        self.assertEqual(van["summary"]["unlocked"], 1)
        self.assertEqual(mira["summary"]["unlocked"], 0)
        owned = next(m for m in van["entries"] if m["id"] == "moment_technically_alive")
        self.assertEqual(owned["reward_title"], "Too Stubborn to Die")
        self.assertTrue(owned["unlocked"])
        self.assertIsNotNone(owned["unlocked_at"])
        self.assertNotIn("Too Stubborn to Die", json.dumps(mira))
        self.assertEqual(len([m for m in mira["entries"] if m["name"] == "Undiscovered Moment"]), 7)

    def test_achievement_title_tab_lists_only_owned_moment_titles(self):
        baseline = self.repo.achievements("van")
        self.unlock_1hp()
        payload = self.repo.achievements("van")
        gained = [t for t in payload["titles"] if t["source"] == "Moment"]
        self.assertEqual(len(gained), 1)
        self.assertEqual(gained[0]["name"], "Too Stubborn to Die")
        self.assertTrue(gained[0]["unlocked"])
        self.assertEqual(payload["summary"]["titles_total"], baseline["summary"]["titles_total"] + 1)
        self.assertEqual(payload["summary"]["titles_unlocked"], baseline["summary"]["titles_unlocked"] + 1)
        self.assertEqual(self.repo.achievements("mira")["summary"]["titles_total"], baseline["summary"]["titles_total"])

    def test_twitch_and_portal_title_path_accepts_owned_moment_only(self):
        self.assertFalse(self.game.set_title("1", "Too Stubborn to Die").ok)
        self.assertNotIn("Too Stubborn to Die", str(self.game.titles("1").messages))
        self.unlock_1hp()
        response = self.game.set_title("1", "Too Stubborn to Die")
        self.assertTrue(response.ok)
        self.assertEqual(self.repo.achievements("van")["summary"]["equipped_title"], "Too Stubborn to Die")
        self.assertTrue(next(t for t in self.repo.achievements("van")["titles"] if t["source"] == "Moment")["equipped"])
        self.assertFalse(self.game.set_title("2", "Too Stubborn to Die").ok)
        self.assertNotIn("Too Stubborn to Die", str(self.game.titles("2").messages))

    def test_records_read_has_no_settlement_or_reconciliation_side_effects(self):
        baseline = {table: self.db.one(f"SELECT COUNT(*) AS n FROM {table}")["n"]
                    for table in ("player_moment_unlocks", "player_moment_reconciliation", "player_record_events", "player_titles")}
        for _ in range(3):
            self.repo.records("van")
            self.repo.achievements("van")
        actual = {table: self.db.one(f"SELECT COUNT(*) AS n FROM {table}")["n"]
                  for table in baseline}
        self.assertEqual(actual, baseline)

    def test_legacy_records_and_achievement_totals_unchanged(self):
        before = self.repo.records("van")
        old_achievements = self.repo.achievements("van")
        self.unlock_1hp()
        after = self.repo.records("van")
        new_achievements = self.repo.achievements("van")
        for key in ("career", "combat", "economy", "progression", "rivalries", "trial_summary", "personal_records"):
            self.assertEqual(before[key], after[key], key)
        self.assertEqual(old_achievements["summary"]["total"], new_achievements["summary"]["total"])
        self.assertEqual(len(old_achievements["achievements"]), len(new_achievements["achievements"]))

    def test_historical_flag_visible_only_after_real_unlock(self):
        self.db.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) "
                        "VALUES ('1','gil','gil',-25000,'shop')")
        with self.db.tx() as conn:
            self.assertIn("Retail Therapy", reconcile_verified_history(conn, self.data, "1"))
        van = self.repo.records("van")["moments"]
        owned = next(m for m in van["entries"] if m["id"] == "moment_retail_therapy")
        self.assertTrue(owned["historical"])
        self.assertTrue(all(not m["historical"] and m["unlocked_at"] is None for m in van["entries"] if not m["unlocked"]))

if __name__ == "__main__":
    unittest.main()

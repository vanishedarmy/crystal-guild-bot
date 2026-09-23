"""Step 6 release gates: historical saves, visibility, isolation and once-only rewards."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from crystal_guild.bestiary_progress import mastery_threshold, progress_for, reconcile_mastery
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.seasonal_events import EDITION_ID

ROOT = Path(__file__).resolve().parents[1]


class BestiaryHardeningStep6(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.engine = CrystalGuildEngine(self.db, self.data, venture_cooldown_seconds=0,
                                          venture_treasure_chance=0.0)
        self.assertTrue(self.engine.recruit("100", "van", "Van").ok)
        self.assertTrue(self.engine.recruit("200", "terra", "Terra").ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def set_count(self, monster, value, player="100"):
        self.db.execute("INSERT INTO bestiary(player_id,monster_id,defeats) VALUES (?,?,?) "
                        "ON CONFLICT(player_id,monster_id) DO UPDATE SET defeats=excluded.defeats",
                        (player, monster, value))

    def snapshot(self, name="van"):
        repo = PortalRepository(self.path, ROOT / "data")
        try:
            return repo.bestiary(name)
        finally:
            repo.close()

    def test_threshold_edges_and_next_milestone_all_categories(self):
        checks = {"goblin": (1, 3, 5, 10, 15, 20),
                  "goblin_chieftain": (1, 2, 3, 5),
                  "elder_ochu": (1, 2, 3)}
        for monster, thresholds in checks.items():
            with self.subTest(monster=monster):
                self.assertEqual(mastery_threshold(self.data, monster), thresholds[-1])
                self.assertEqual(progress_for(self.data, monster, 0)["stage_index"], 0)
                for index, at in enumerate(thresholds):
                    before = progress_for(self.data, monster, at - 1)
                    reached = progress_for(self.data, monster, at)
                    self.assertEqual(before["stage_index"], index)
                    self.assertEqual(before["next_milestone"]["remaining"], 1)
                    self.assertEqual(reached["stage_index"], index + 1)
                self.assertTrue(progress_for(self.data, monster, thresholds[-1])["mastered"])
                self.assertIsNone(progress_for(self.data, monster, 1000000)["next_milestone"])

    def test_per_player_milestones_and_receipts_never_cross_players(self):
        self.set_count("goblin", 20)
        self.set_count("goblin", 1, "200")
        self.assertEqual(reconcile_mastery(self.db, self.data, "100")["masteries_added"], 1)
        self.assertEqual(reconcile_mastery(self.db, self.data, "200")["masteries_added"], 0)
        van, terra = self.snapshot(), self.snapshot("terra")
        self.assertEqual(van["summary"]["research_points"], 1)
        self.assertEqual(terra["summary"]["research_points"], 0)
        own = next(r for r in van["monsters"] if r["id"] == "goblin")
        other = next(r for r in terra["monsters"] if r["id"] == "goblin")
        self.assertTrue(own["mastery_reward"]["seal"])
        self.assertFalse(other["mastery_reward"]["seal"])
        self.assertIsNone(other["weakness"])
        self.assertEqual(other["drops"], [])

    def test_reconciliation_survives_restart_and_replayed_callbacks(self):
        self.set_count("goblin", 29)
        self.set_count("goblin_chieftain", 11)
        self.set_count("elder_ochu", 4)
        first = reconcile_mastery(self.db, self.data, "100")
        self.assertEqual((first["masteries_added"], first["research_points_added"]), (3, 3))
        for _ in range(5):
            self.assertEqual(reconcile_mastery(self.db, self.data, "100")["masteries_added"], 0)
        self.db.close()
        self.db = Database(self.path)
        self.assertEqual(reconcile_mastery(self.db, self.data, "100")["masteries_added"], 0)
        rows = self.db.all("SELECT monster_id,research_points,source_defeats FROM player_bestiary_mastery WHERE player_id='100'")
        self.assertEqual(len(rows), 3)
        self.assertEqual(sum(int(r["research_points"]) for r in rows), 3)
        self.assertEqual({r["monster_id"]: r["source_defeats"] for r in rows},
                         {"goblin": 29, "goblin_chieftain": 11, "elder_ochu": 4})

    def test_locked_base_and_external_fields_fail_closed(self):
        self.set_count("goblin", 1)
        snap = self.snapshot()
        core = next(x for x in snap["monsters"] if x["id"] == "goblin")
        for key in ("weakness", "lore", "combat_profile", "active_skill"):
            self.assertIsNone(core[key], key)
        self.assertEqual(core["habitats"], [])
        self.assertEqual(core["drops"], [])
        for scoped in ("boss:ifrit", "world_event:notorious_behemoth",
                       f"seasonal:{EDITION_ID}:jack_o_bomb"):
            with self.subTest(scoped=scoped):
                row = next(x for x in snap["monsters"] if x["id"] == scoped)
                self.assertEqual(row["name"], "???")
                self.assertIsNone(row["weakness"])
                self.assertIsNone(row["lore"])
                self.assertEqual(row["drops"], [])
                self.assertFalse(row["mastery_reward"]["seal"])

    def test_external_clears_do_not_grant_base_mastery_or_cross_players(self):
        self.db.execute("INSERT INTO player_boss_clears(player_id,boss_id,clears,best_damage) VALUES (?,?,?,?)",
                        ("100", "ifrit", 2, 2000))
        self.db.execute("INSERT INTO player_world_event_clears(player_id,world_event_id,clears) VALUES (?,?,?)",
                        ("100", "notorious_behemoth", 3))
        self.db.execute("INSERT INTO player_seasonal_monster_clears(player_id,edition_id,variant_id,clears) VALUES (?,?,?,?)",
                        ("100", EDITION_ID, "jack_o_bomb", 1))
        van, terra = self.snapshot(), self.snapshot("terra")
        for scoped in ("boss:ifrit", "world_event:notorious_behemoth",
                       f"seasonal:{EDITION_ID}:jack_o_bomb"):
            own = next(x for x in van["monsters"] if x["id"] == scoped)
            other = next(x for x in terra["monsters"] if x["id"] == scoped)
            self.assertTrue(own["research"]["mastered"])
            self.assertFalse(own["mastery_reward"]["seal"])
            self.assertEqual(own["mastery_reward"]["research_points"], 0)
            self.assertFalse(other["discovered"])
        self.assertEqual(van["summary"]["mastery_seals"], 0)
        self.assertEqual(reconcile_mastery(self.db, self.data)["masteries_added"], 0)

    def test_seasonal_edition_isolation_and_inactive_history(self):
        self.db.execute("INSERT INTO player_seasonal_monster_clears(player_id,edition_id,variant_id,clears) VALUES (?,?,?,?)",
                        ("100", "halloween_2027", "jack_o_bomb", 99))
        scoped = f"seasonal:{EDITION_ID}:jack_o_bomb"
        self.assertFalse(next(x for x in self.snapshot()["monsters"] if x["id"] == scoped)["discovered"])
        self.db.execute("INSERT INTO player_seasonal_monster_clears(player_id,edition_id,variant_id,clears) VALUES (?,?,?,?)",
                        ("100", EDITION_ID, "jack_o_bomb", 1))
        self.db.execute("UPDATE seasonal_event_instances SET enabled=0 WHERE edition_id=?", (EDITION_ID,))
        self.assertTrue(next(x for x in self.snapshot()["monsters"] if x["id"] == scoped)["discovered"])

    def test_historical_schema21_upgrade_preserves_progress_and_verified_backup(self):
        self.set_count("goblin", 25)
        self.db.execute("INSERT INTO player_seasonal_monster_clears(player_id,edition_id,variant_id,clears) VALUES (?,?,?,?)",
                        ("100", EDITION_ID, "jack_o_bomb", 2))
        self.db.close()
        # Synthetic legacy fixture: revert schema-22 and schema-23 metadata, leaving all
        # historical schema-21 gameplay and seasonal data intact.
        with sqlite3.connect(self.path) as conn:
            conn.execute("DROP TABLE player_bestiary_mastery")
            conn.execute("DELETE FROM schema_migrations WHERE version IN (22,23)")
            self.assertEqual(conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0], 21)
        self.db = Database(self.path)
        self.assertEqual(self.db.schema_version(), 23)
        backup = self.db.pre_migration_backup_path
        self.assertIsNotNone(backup)
        self.assertTrue(backup.is_file())
        # Latest backup now belongs to schema 23; schema 22 still retains its
        # own migration backup with the original schema-21 snapshot.
        original_backup = sorted((self.path.parent / "backups").glob("pre_schema_22_*.db"))
        self.assertTrue(original_backup)
        with sqlite3.connect(original_backup[-1]) as older:
            self.assertEqual(older.execute("PRAGMA quick_check").fetchone()[0], "ok")
            self.assertEqual(older.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0], 21)
            self.assertEqual(older.execute("SELECT defeats FROM bestiary WHERE player_id='100' AND monster_id='goblin'").fetchone()[0], 25)
        self.assertEqual(self.db.one("SELECT defeats FROM bestiary WHERE player_id='100' AND monster_id='goblin'")["defeats"], 25)
        self.assertEqual(reconcile_mastery(self.db, self.data, "100")["masteries_added"], 1)
        self.assertEqual(reconcile_mastery(self.db, self.data, "100")["masteries_added"], 0)
        self.assertTrue(next(x for x in self.snapshot()["monsters"] if x["id"] == f"seasonal:{EDITION_ID}:jack_o_bomb")["discovered"])

    def test_unknown_future_monster_and_unseen_player_safe(self):
        self.set_count("unreleased_monster_id", 999)
        self.assertEqual(reconcile_mastery(self.db, self.data, "100")["masteries_added"], 0)
        self.assertEqual(progress_for(self.data, "unreleased_monster_id", 999)["stage"], "undiscovered")
        self.assertIsNone(self.snapshot("absent"))


if __name__ == "__main__":
    unittest.main()

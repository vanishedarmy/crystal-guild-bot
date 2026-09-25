"""v1.9.2 Relic Arsenal: detailed snapshot without changing the game rules."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class RelicOverhaulTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "guild.db"
        self.db = Database(self.path)
        self.data = GameData(ROOT / "data")
        self.engine = CrystalGuildEngine(self.db, self.data)
        self.assertTrue(self.engine.recruit("100", "relichero", "Relic Hero").ok)
        self.assertTrue(self.engine.choose_job("100", "warrior").ok)
        self.assertTrue(self.engine.recruit("200", "other", "Other").ok)
        self.relic = self.data.relics["bravura"]
        self.repo = PortalRepository(self.path, ROOT / "data")

    def tearDown(self):
        self.repo.close()
        self.db.close()
        self.tmp.cleanup()

    def view(self):
        result = self.repo.relics("relichero")
        self.assertIsNotNone(result)
        return result

    def own(self):
        return next(row for row in self.view()["relics"] if row["id"] == "bravura")

    def supply(self, index: int):
        step = self.relic["stages"][index]
        self.db.execute("UPDATE players SET gil=100000,hunt_seals=1000,level=99 WHERE twitch_id='100'")
        self.db.execute("UPDATE player_jobs SET level=99 WHERE player_id='100' AND job_id='warrior'")
        for material in step["cost"]["items"]:
            self.db.execute(
                "INSERT INTO inventory(player_id,item_id,quantity) VALUES ('100',?,?) "
                "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=excluded.quantity",
                (material["item_id"], material["quantity"]),
            )

    def test_complete_catalog_and_fixed_query_budget(self):
        statements = []
        with self.repo.connect() as conn:
            conn.set_trace_callback(statements.append)
        payload = self.view()
        with self.repo.connect() as conn:
            conn.set_trace_callback(None)
        self.assertEqual(payload["summary"]["total"], 18)
        self.assertEqual(payload["summary"]["total_stages"], 54)
        self.assertEqual(payload["summary"]["complete"], 0)
        self.assertEqual(len(payload["relics"]), 18)
        self.assertTrue(all(len(row["path"]) == 3 for row in payload["relics"]))
        self.assertEqual(len([sql for sql in statements if sql.strip().upper().startswith("SELECT")]), 6)
        for row in payload["relics"]:
            self.assertEqual(row["stages"], [step["name"] for step in row["path"]])
            self.assertEqual(row["final_reward"]["id"], self.data.relics[row["id"]]["stages"][-1]["reward_item"])
            self.assertTrue(all(step["reward"]["bonuses"] for step in row["path"]))
            self.assertTrue(all(step["reward"]["allowed_job_names"] for step in row["path"]))

    def test_readiness_requires_exact_objectives_and_all_materials(self):
        before = self.own()
        self.assertEqual(before["status"], "not_started")
        self.assertFalse(before["ready"])
        self.supply(0)
        ready = self.own()
        self.assertEqual(ready["job_level"], 99)
        self.assertTrue(ready["ready"])
        self.assertEqual(ready["status"], "ready")
        self.assertTrue(ready["path"][0]["requirements_met"])
        self.assertTrue(ready["path"][0]["costs_met"])
        self.assertEqual(ready["path"][0]["state"], "current")
        self.assertFalse(ready["path"][1]["ready"])
        self.assertEqual(ready["path"][1]["state"], "upcoming")
        result = self.engine.awaken_relic("100", "Bravura")
        self.assertTrue(result.ok, result)
        earned = self.own()
        self.assertEqual(earned["stage"], 1)
        self.assertEqual(earned["path"][0]["state"], "completed")
        self.assertEqual(earned["current_reward"], self.data.items[self.relic["stages"][0]["reward_item"]]["name"])
        self.assertEqual(self.view()["summary"]["earned_stages"], 1)

    def test_unique_rank_clears_are_distinct_hunts_not_repeat_farming(self):
        self.db.execute("INSERT INTO player_relics(player_id,relic_id,stage) VALUES ('100','bravura',2)")
        self.supply(2)
        s_hunts = [hunt["id"] for hunt in self.data.hunts.values() if hunt["rank"] == "S"]
        self.assertGreaterEqual(len(s_hunts), 2)
        self.db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100',?,50)", (s_hunts[0],))
        stage = self.own()["path"][2]
        rank_req = next(req for req in stage["requirements"] if req["type"] == "hunt_rank_clears")
        self.assertEqual(rank_req["current"], 1)
        self.assertFalse(stage["ready"])
        self.db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100',?,1)", (s_hunts[1],))
        self.assertTrue(self.own()["path"][2]["ready"])

    def test_other_players_resources_never_leak(self):
        self.supply(0)
        first = self.own()
        other = next(row for row in self.repo.relics("other")["relics"] if row["id"] == "bravura")
        self.assertTrue(first["ready"])
        self.assertFalse(other["ready"])
        self.assertEqual(other["path"][0]["cost"]["materials"][0]["owned"], 0)
        self.assertEqual(other["job_level"], 0)


if __name__ == "__main__":
    unittest.main()

"""Relic Arsenal v1.5.1 data integrity under unittest discovery."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RelicArsenalTests(unittest.TestCase):
    def test_every_job_has_exactly_one_relic_line(self):
        jobs = json.loads((ROOT / "data/jobs.json").read_text(encoding="utf-8"))
        relics = json.loads((ROOT / "data/relics.json").read_text(encoding="utf-8"))
        self.assertEqual(len(jobs), 18)
        self.assertEqual(len(relics), 18)
        by_job = {}
        for relic in relics:
            by_job.setdefault(relic["job_id"], []).append(relic)
        self.assertEqual(set(by_job), {job["id"] for job in jobs})
        for job_id, rows in by_job.items():
            with self.subTest(job_id=job_id):
                self.assertEqual(len(rows), 1)

    def test_all_relics_have_three_stage_items_for_own_job(self):
        relics = json.loads((ROOT / "data/relics.json").read_text(encoding="utf-8"))
        items = {
            item["id"]: item
            for item in json.loads((ROOT / "data/items.json").read_text(encoding="utf-8"))
        }
        for relic in relics:
            with self.subTest(relic=relic["id"]):
                self.assertEqual([stage["stage"] for stage in relic["stages"]], [1, 2, 3])
            for stage in relic["stages"]:
                with self.subTest(relic=relic["id"], stage=stage["stage"]):
                    item = items[stage["reward_item"]]
                    self.assertEqual(item["relic_id"], relic["id"])
                    self.assertEqual(item["relic_stage"], stage["stage"])
                    self.assertIn(relic["job_id"], item["allowed_jobs"])
                    self.assertIs(item["unsellable"], True)

    def test_151_missing_jobs_are_completed(self):
        relics = {
            relic["job_id"]: relic["id"]
            for relic in json.loads((ROOT / "data/relics.json").read_text(encoding="utf-8"))
        }
        self.assertTrue(relics)
        expected = {
            "warrior": "bravura", "redmage": "murgleis", "ninja": "yoshimitsu",
            "summoner": "veil_of_wiyu", "bluemage": "almace", "timemage": "chronos",
            "bard": "artemis_bow", "machinist": "armageddon",
            "beastmaster": "guttler", "sage": "astral_codex",
        }
        for job, relic in expected.items():
            with self.subTest(job=job):
                self.assertEqual(relics[job], relic)


if __name__ == "__main__":
    unittest.main()

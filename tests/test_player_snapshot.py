from __future__ import annotations

import tempfile
from contextlib import ExitStack
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]


class PlayerSnapshotTests(unittest.TestCase):
    def test_snapshot_repository_tracks_live_player_data(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as cleanup:
            path = Path(tmp) / "guild.db"
            db = Database(path)
            cleanup.callback(db.close)
            data = GameData(ROOT / "data")
            engine = CrystalGuildEngine(db, data, venture_cooldown_seconds=0, venture_treasure_chance=0.0)
            engine.recruit("100", "van", "Van")
            engine.choose_job("100", "warrior")
            repo = PortalRepository(path, ROOT / "data")
            cleanup.callback(repo.close)
            profile = repo.overview("van")
            self.assertIsNotNone(profile)
            self.assertEqual(profile["identity"]["display_name"], "Van")
            self.assertEqual(profile["job"]["name"], "Warrior")
            self.assertEqual(profile["resources"]["mode"], "ap")
            self.assertGreater(profile["resources"]["ap"]["max"], 0)
            self.assertEqual(profile["resources"]["ap"]["current"], profile["resources"]["ap"]["max"])
            self.assertEqual(profile["resources"]["mp"]["max"], 0)
            db.execute("UPDATE players SET level=12, gil=4321 WHERE twitch_id='100'")
            updated = repo.overview("van")
            self.assertEqual(updated["identity"]["level"], 12)
            self.assertEqual(updated["identity"]["gil"], 4321)
            bestiary = repo.bestiary("van")
            self.assertTrue(bestiary["monsters"])
            self.assertEqual(bestiary["summary"]["discovered"], 0)
            self.assertTrue(all(entry["name"] == "???" for entry in bestiary["monsters"]))
            self.assertTrue(all(entry["level"] is None for entry in bestiary["monsters"]))
            self.assertTrue(all(entry["combat_profile"] is None for entry in bestiary["monsters"]))
            self.assertTrue(all(entry["active_skill"] is None for entry in bestiary["monsters"]))


    def test_snapshot_reads_full_rest_sentinel_at_selected_job_maximum(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as cleanup:
            path = Path(tmp) / "guild.db"
            db = Database(path)
            cleanup.callback(db.close)
            data = GameData(ROOT / "data")
            engine = CrystalGuildEngine(db, data, venture_cooldown_seconds=0, venture_treasure_chance=0.0)
            engine.recruit("100", "van", "Van")
            engine.choose_job("100", "blackmage")
            black = engine._resource_state_for(engine._player("100"))
            engine._full_refresh_player_row(engine._player("100"), clear_camp=True)
            self.assertTrue(engine.choose_job("100", "whitemage").ok)
            white = engine._resource_state_for(engine._player("100"), initialize=False)
            self.assertGreater(int(white["max_mp"]), int(black["max_mp"]))

            repo = PortalRepository(path, ROOT / "data")
            cleanup.callback(repo.close)
            profile = repo.overview("van")
            self.assertEqual(profile["resources"]["mp"]["current"], profile["resources"]["mp"]["max"] )
            self.assertEqual(profile["resources"]["mp"]["max"], int(white["max_mp"]))


    def test_snapshot_resource_bars_follow_live_battle_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as cleanup:
            path = Path(tmp) / "guild.db"
            db = Database(path)
            cleanup.callback(db.close)
            data = GameData(ROOT / "data")
            engine = CrystalGuildEngine(db, data, venture_cooldown_seconds=0, venture_treasure_chance=0.0)
            engine.recruit("100", "van", "Van")
            engine.choose_job("100", "warrior")
            opened = engine.venture("100", bypass_cooldown=True)
            engine.start_encounter_battle(opened.data["encounter_id"])
            actor = engine.encounter_roster["100"]
            actor["ap"] = max(0, int(actor["max_ap"]) - 9)
            engine._persist_runtime_state()

            repo = PortalRepository(path, ROOT / "data")
            cleanup.callback(repo.close)
            profile = repo.overview("van")
            self.assertTrue(profile["resources"]["live_battle"])
            self.assertEqual(profile["resources"]["ap"]["current"], actor["ap"])
            self.assertEqual(profile["resources"]["mp"]["max"], 0)



    def test_resting_snapshot_includes_absolute_camp_deadline(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as cleanup:
            path = Path(tmp) / "guild.db"
            db = Database(path)
            cleanup.callback(db.close)
            data = GameData(ROOT / "data")
            engine = CrystalGuildEngine(db, data, venture_cooldown_seconds=0, venture_treasure_chance=0.0)
            engine.recruit("100", "timerhero", "Timer Hero")
            engine.choose_job("100", "blackmage")
            import time
            until = int(time.time()) + 600
            db.execute("UPDATE players SET camp_until=? WHERE twitch_id='100'", (until,))

            repo = PortalRepository(path, ROOT / "data")
            cleanup.callback(repo.close)
            profile = repo.overview("timerhero")
            self.assertEqual(profile["status"]["state"], "resting")
            self.assertEqual(profile["status"]["until"], until)
            self.assertGreater(profile["status"]["remaining_seconds"], 0)


if __name__ == "__main__":
    unittest.main()

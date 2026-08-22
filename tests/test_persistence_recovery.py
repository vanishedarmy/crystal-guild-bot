from __future__ import annotations

import json
import random
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_sync import PortalSyncClient


ROOT = Path(__file__).resolve().parents[1]


class DatabaseTransactionTests(unittest.TestCase):
    def test_nested_helper_write_rolls_back_with_outer_transaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, GameData(ROOT / "data"), overlay_state_path=str(Path(tmp) / "overlay.json"))
                game.recruit("1", "van", "Van")
                before = db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]
                with self.assertRaises(RuntimeError):
                    with db.tx() as conn:
                        conn.execute("UPDATE players SET gil=gil+1 WHERE twitch_id='1'")
                        db.execute("UPDATE players SET gil=gil+100 WHERE twitch_id='1'")
                        raise RuntimeError("force outer rollback")
                after = db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]
                self.assertEqual(after, before)
                self.assertGreaterEqual(db.transaction_stats()["rollbacks"], 1)
            finally:
                db.close()

    def test_inner_savepoint_can_roll_back_without_losing_outer_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            try:
                game = CrystalGuildEngine(db, GameData(ROOT / "data"), overlay_state_path=str(Path(tmp) / "overlay.json"))
                game.recruit("1", "van", "Van")
                before = db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]
                with db.tx() as conn:
                    conn.execute("UPDATE players SET gil=gil+2 WHERE twitch_id='1'")
                    try:
                        with db.tx() as nested:
                            nested.execute("UPDATE players SET gil=gil+100 WHERE twitch_id='1'")
                            raise ValueError("rollback savepoint only")
                    except ValueError:
                        pass
                    conn.execute("UPDATE players SET gil=gil+3 WHERE twitch_id='1'")
                after = db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]
                self.assertEqual(after, before + 5)
                self.assertGreaterEqual(db.transaction_stats()["savepoint_rollbacks"], 1)
            finally:
                db.close()


class RuntimeRecoveryTests(unittest.TestCase):
    def _open(self, tmp: str):
        db = Database(Path(tmp) / "guild.db")
        game = CrystalGuildEngine(
            db,
            GameData(ROOT / "data"),
            venture_cooldown_seconds=0, venture_treasure_chance=0.0,
            overlay_state_path=str(Path(tmp) / "overlay.json"),
            rng=random.Random(11),
        )
        return db, game

    def test_active_encounter_survives_database_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            db, game = self._open(tmp)
            game.recruit("1", "van", "Van")
            game.choose_job("1", "warrior")
            opened = game.venture("1", bypass_cooldown=True)
            self.assertTrue(opened.ok)
            encounter_id = opened.data["encounter_id"]
            stored = db.runtime_state("combat")
            self.assertIsNotNone(stored)
            db.close()

            db2, game2 = self._open(tmp)
            try:
                self.assertEqual(game2.active_encounter["id"], encounter_id)
                self.assertIn("1", game2.encounter_roster)
                self.assertTrue(game2.runtime_status()["recovered"])
                game2.abort_encounter()
            finally:
                db2.close()

            db3, game3 = self._open(tmp)
            try:
                self.assertIsNone(game3.active_encounter)
                self.assertEqual(game3.encounter_roster, {})
            finally:
                db3.close()

    def test_reward_failure_rolls_back_database_and_combat_state_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            db, game = self._open(tmp)
            try:
                game.recruit("1", "van", "Van")
                game.choose_job("1", "warrior")
                opened = game.venture("1", bypass_cooldown=True)
                game.start_encounter_battle(opened.data["encounter_id"])
                before_gil = db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"]
                before_state = game._capture_runtime_state()

                def kill_enemy(_meta, _monster, _log):
                    game.active_encounter["monster_hp"] = 0

                def broken_award(player_id, _player, _monster, **kwargs):
                    db.execute("UPDATE players SET gil=gil+999 WHERE twitch_id=?", (player_id,))
                    raise RuntimeError("simulated crash during reward persistence")

                with patch.object(game, "_resolve_active_attack", side_effect=kill_enemy), patch.object(game, "_award_victory", side_effect=broken_award):
                    with self.assertRaises(RuntimeError):
                        game.advance_encounter_round(opened.data["encounter_id"])

                self.assertEqual(db.one("SELECT gil FROM players WHERE twitch_id='1'")["gil"], before_gil)
                self.assertEqual(game._capture_runtime_state(), before_state)
                persisted = json.loads(db.runtime_state("combat")["value_json"])
                self.assertEqual(persisted, before_state)
            finally:
                db.close()

    def test_active_raid_combat_survives_database_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            db, game = self._open(tmp)
            game.recruit("1", "van", "Van")
            game.choose_job("1", "warrior")
            boss = next(iter(game.data.bosses.values()))
            opened = game.spawn_boss(boss["id"])
            self.assertTrue(opened.ok)
            joined = game.raid_join("1")
            self.assertTrue(joined.ok)
            boss_id = game.active_boss["id"]
            started = game.start_raid(boss_id)
            self.assertTrue(started.ok)
            self.assertEqual(game.active_boss["state"], "combat")
            db.close()

            db2, game2 = self._open(tmp)
            try:
                self.assertEqual(game2.active_boss["id"], boss_id)
                self.assertEqual(game2.active_boss["state"], "combat")
                self.assertIn("1", game2.raid_roster)
                self.assertTrue(game2.runtime_status()["recovered"])
            finally:
                db2.close()

    def test_corrupt_runtime_checkpoint_does_not_brick_startup(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "guild.db")
            db.set_runtime_state("combat", "{not-json")
            db.close()
            db2, game = self._open(tmp)
            try:
                self.assertIsNone(game.active_encounter)
                self.assertEqual(game.runtime_status()["active"], "idle")
                self.assertNotEqual(game.runtime_status()["recovery_error"], "none")
                self.assertIsNone(db2.runtime_state("combat"))
            finally:
                db2.close()


class PortalSyncRecoveryTests(unittest.TestCase):
    def test_partial_sync_retry_resumes_without_reuploading_successes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "source.db"
            db_path.write_bytes(b"x")

            class Repo:
                database_path = db_path

                def list_players(self):
                    return [{"username": "alpha"}, {"username": "beta"}]

                def twitch_id_for(self, username):
                    return {"alpha": "1001", "beta": "1002"}[username]

                @contextmanager
                def consistent_read(self):
                    yield

            repo = Repo()
            for module in ("overview", "jobs", "inventory", "hunts", "bestiary", "relics", "achievements", "records"):
                setattr(repo, module, lambda username, module=module: {"module": module, "username": username})

            class Client(PortalSyncClient):
                def __init__(self):
                    super().__init__(repo, "https://example.invalid", "key")
                    self.player_posts = []
                    self.failed_beta = False

                def _post(self, path, payload):
                    if path == "/api/sync/player":
                        username = payload["username"]
                        self.player_posts.append(username)
                        if username == "beta" and not self.failed_beta:
                            self.failed_beta = True
                            raise RuntimeError("temporary host failure")
                        return {"ok": True}
                    return {"ok": True, "removed": 0, "missing": []}

            client = Client()
            with self.assertRaises(RuntimeError):
                client.sync_once()
            result = client.sync_once()
            self.assertEqual(client.player_posts, ["alpha", "beta", "beta"])
            self.assertEqual(result["changed"], 1)
            self.assertFalse(client._force_full)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import time
import unittest
from contextlib import contextmanager
from pathlib import Path

from crystal_guild.portal_sync import PortalSyncClient


class CloudContinuitySyncTests(unittest.TestCase):
    def make_client(self, root: Path):
        db_path = root / "guild.db"
        db_path.write_bytes(b"db")
        overlay_path = root / "state.json"
        overlay_path.write_text(json.dumps({"active": False, "status": "IDLE"}), encoding="utf-8")

        class Repo:
            database_path = db_path

            def list_players(self):
                return []

            @contextmanager
            def consistent_read(self):
                yield

            def fellowship(self):
                return {"level": 4, "level_label": "LVL 4", "member_count": 12}

        class Client(PortalSyncClient):
            def __init__(self):
                super().__init__(
                    Repo(), "https://example.invalid", "key",
                    interval=5, heartbeat_seconds=5, overlay_state_path=overlay_path,
                )
                self.posts = []

            def _post(self, path, payload):
                self.posts.append((path, payload))
                if path == "/api/sync/manifest":
                    return {"ok": True, "removed": 0, "missing": []}
                return {"ok": True}

        return Client(), overlay_path

    def test_heartbeat_republishes_fellowship_and_overlay_for_web_restart_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            client, _ = self.make_client(Path(tmp))
            client.sync_once()
            client.posts.clear()
            client._last_heartbeat = time.monotonic() - 10
            client.sync_once()
            paths = [path for path, _ in client.posts]
            self.assertIn("/api/sync/fellowship", paths)
            self.assertIn("/api/sync/overlay", paths)
            self.assertIn("/api/sync/manifest", paths)

    def test_overlay_file_change_syncs_without_database_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            client, overlay_path = self.make_client(Path(tmp))
            client.sync_once()
            client.posts.clear()
            client._last_heartbeat = time.monotonic()
            time.sleep(0.002)
            overlay_path.write_text(json.dumps({
                "active": True,
                "status": "COMBAT",
                "boss": "Behemoth King",
                "hp": 1200,
                "max_hp": 2000,
                "top": [{"name": "Van", "damage": 600, "healing": 20}],
            }), encoding="utf-8")
            client.sync_once()
            paths = [path for path, _ in client.posts]
            self.assertEqual(paths, ["/api/sync/overlay"])
            payload = client.posts[0][1]["overlay"]
            self.assertEqual(payload["boss"], "Behemoth King")
            self.assertEqual(payload["top"][0]["name"], "Van")

    def test_render_blueprint_keeps_disk_without_unsupported_shutdown_delay(self):
        render_yaml = (Path(__file__).resolve().parents[1] / "render.yaml").read_text(encoding="utf-8")
        self.assertIn("mountPath: /var/data", render_yaml)
        self.assertNotIn("maxShutdownDelaySeconds", render_yaml)


if __name__ == "__main__":
    unittest.main()

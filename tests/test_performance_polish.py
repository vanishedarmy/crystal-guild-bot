"""Guard against regressions in the Portal action/snapshot fast path."""
import unittest
from unittest.mock import Mock

from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION, PASSIVE_PORTAL_ACTIONS, PortalActionWorker
from crystal_guild.portal_sync import PortalSyncWorker


class ActionFastPathTests(unittest.TestCase):
    def test_state_actions_are_passive_including_retainer_and_merc_service(self):
        for kind in ("RETAINER_STATE", "MERC_STATE", "DAILY_STATE", "PING", "SEASONAL_STATE"):
            self.assertIn(kind, PASSIVE_PORTAL_ACTIONS)

    def test_only_mutations_wake_sync_after_host_acknowledges_result(self):
        worker = PortalActionWorker(Mock(), "https://guild.example", "sync-key")
        wakes = []
        posted = []
        worker.wake_sync = lambda: wakes.append("woke")
        worker._player_title_ids = lambda _user: set()
        worker._execute = lambda _action: (True, "OK", {})
        state = {"kind": "RETAINER_STATE"}
        def fake_post(path, data):
            if path == "/api/actions/claim":
                return {"protocol_version": ACTION_PROTOCOL_VERSION, "actions": [{
                    "id": "pa_1", "type": state["kind"], "twitch_id": "123",
                    "username": "van", "lease_token": "signed-token", "payload": {},
                }], "long_poll": True}
            posted.append(path)
            self.assertFalse(wakes, "must not wake before hosted acknowledgement")
            return {"ok": True}
        worker._post = fake_post
        self.assertEqual(worker.poll_once(), 1)
        self.assertEqual(wakes, [])
        self.assertEqual(posted, ["/api/actions/result"])
        state["kind"] = "SET_TITLE"
        posted.clear()
        self.assertEqual(worker.poll_once(), 1)
        self.assertEqual(wakes, ["woke"])
        self.assertEqual(posted, ["/api/actions/result"])

    def test_wake_during_snapshot_sync_is_not_lost(self):
        calls = []
        class Client:
            interval = 60
            def sync_once(self, **_kwargs):
                calls.append(1)
                if len(calls) == 1:
                    worker.wake()
                else:
                    worker._stop.set(); worker._wake.set()
                return {"changed": 0}
        worker = PortalSyncWorker(Client())
        worker._run()
        self.assertEqual(len(calls), 2)

if __name__ == "__main__":
    unittest.main()

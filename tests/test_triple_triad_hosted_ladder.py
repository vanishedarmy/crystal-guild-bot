"""Combined-release regression: browser HTTP -> Web queue -> Bot -> result.

Run from Bot with Web beside it. Finished-board fixtures isolate circuit
progression from random NPC moves; no production player data is touched.
"""
from __future__ import annotations

import importlib.util
import json
import random
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.portal_actions import PortalActionWorker
from crystal_guild.triple_triad import TRIPLE_TRIAD_OPPONENTS, TRIPLE_TRIAD_STARTER_DECK

BOT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = BOT_ROOT.parent / "Web"


@unittest.skipUnless((WEB_ROOT / "crystal_guild/hosted_portal.py").is_file(), "Combined Bot + Web release required")
class HostedTripleTriadLadderTests(unittest.TestCase):
    def setUp(self):
        # Separate namespaces let both deployment services be tested together.
        name = "triad_test_web"
        if name not in sys.modules:
            spec = importlib.util.spec_from_file_location(
                name, WEB_ROOT / "crystal_guild/__init__.py",
                submodule_search_locations=[str(WEB_ROOT / "crystal_guild")],
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        self.web = __import__(name + ".hosted_portal", fromlist=["HostedPortalStore"])
        auth = __import__(name + ".portal_auth", fromlist=["TwitchOAuthConfig"])
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = Database(root / "guild.db")
        self.game = CrystalGuildEngine(
            self.db, GameData(BOT_ROOT / "data"),
            overlay_state_path=str(root / "overlay.json"), rng=random.Random(500),
        )
        self.game.recruit("100", "van", "Van")
        self.game.choose_job("100", "warrior")
        self.game.portal_gold_saucer_state("100")
        with self.db.tx() as conn:
            conn.execute("UPDATE player_gold_saucer SET points=10000 WHERE player_id='100'")
        self.store = self.web.HostedPortalStore(root / "mirror.db")
        self.store.upsert_player({
            "schema_version": 1, "username": "van", "player_twitch_id": "100",
            "snapshot": {"overview": {"identity": {"username": "van", "display_name": "Van", "level": 12},
                "job": {"name": "Warrior"}, "status": {"state": "ready", "label": "Ready"}},
                **{key: {} for key in ("jobs", "inventory", "hunts", "bestiary", "relics", "achievements", "records")}},
        })
        self.store.apply_manifest(["van"], "100")
        self.token, self.csrf = self.store.create_session(
            {"twitch_id": "100", "login": "van", "display_name": "Van"}, 3600,
        )
        static = root / "dist"
        static.mkdir()
        (static / "index.html").write_text("<html>Triple Triad test</html>")
        config = auth.TwitchOAuthConfig(
            client_id="test-client", client_secret="test-secret",
            redirect_uri="https://guild.example/auth/twitch/callback", cookie_secure=False,
        )
        self.server = self.web.HostedPortalHTTPServer(
            ("127.0.0.1", 0), self.web.HostedPortalHandler, self.store, static,
            "triad-test-key", oauth_config=config,
            oauth_client=auth.TwitchOAuthClient(config), actions_enabled=True,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.worker = PortalActionWorker(self.game, self.base, "triad-test-key")
        self.now = int(time.time())
        self.serial = 0

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.db.close()
        self.temp.cleanup()

    def request(self, path, payload=None, headers=None):
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(self.base + path, data=data, headers={
            "Content-Type": "application/json", **(headers or {}),
        })
        with urllib.request.urlopen(req, timeout=3) as response:
            return json.load(response)

    def action(self, kind, payload):
        self.serial += 1
        queued = self.request("/api/actions", {"type": kind, "payload": payload}, {
            "Cookie": f"cg_session={self.token}", "X-Crystal-Guild-CSRF": self.csrf,
            "Idempotency-Key": f"triad-ladder-{self.serial}",
        })
        # Run the real relay against the local hosted service. Advancing the
        # engine clock allows the second day's entries without changing limits.
        with patch("crystal_guild.engine.time.time", return_value=self.now):
            self.assertEqual(self.worker.poll_once(), 1)
        completed = self.request("/api/actions/" + queued["action"]["id"], headers={
            "Cookie": f"cg_session={self.token}",
        })["action"]
        return completed

    def finish_with_win(self, opponent):
        cards = list(TRIPLE_TRIAD_STARTER_DECK[:4]) + opponent["deck"][:4]
        board = [{"card_id": card, "owner": "player" if i < 7 else "npc"} for i, card in enumerate(cards)] + [None]
        last_card = TRIPLE_TRIAD_STARTER_DECK[-1]
        with self.db.tx() as conn:
            conn.execute(
                "UPDATE gold_saucer_triple_triad SET board_json=?,player_hand_json=?,npc_hand_json=? WHERE player_id='100'",
                (json.dumps(board), json.dumps([last_card]), json.dumps([opponent["deck"][-1]])),
            )
        completed = self.action("TRIAD_PLAY", {"card": last_card, "cell": 8})
        self.assertEqual(completed["status"], "completed", completed)
        state = completed["result"]["data"]["triple_triad_state"]
        self.assertEqual(state["match"]["result"], "win")
        return state

    def test_all_ten_tables_clear_five_circuits_through_the_hosted_relay(self):
        self.assertEqual(
            (BOT_ROOT / "crystal_guild/triple_triad_catalog.json").read_bytes(),
            (WEB_ROOT / "crystal_guild/triple_triad_catalog.json").read_bytes(),
        )
        for index, opponent in enumerate(TRIPLE_TRIAD_OPPONENTS):
            started = self.action("TRIAD_START", {"opponent": opponent["id"]})
            self.assertEqual(started["status"], "completed", started)
            state = self.finish_with_win(opponent)
            self.assertEqual(next(o["wins"] for o in state["opponents"] if o["id"] == opponent["id"]), 1)
            circuit_index = index // 2
            if index % 2:
                self.assertTrue(state["circuits"][circuit_index]["cleared"])
                self.assertTrue(state["circuits"][circuit_index]["bonus_paid"])
                if circuit_index < 4:
                    self.assertTrue(state["circuits"][circuit_index + 1]["unlocked"])
            elif circuit_index < 4:
                self.assertFalse(state["circuits"][circuit_index + 1]["unlocked"])
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM gold_saucer_history WHERE game='triad_circuit'")["n"], 5)
        self.assertEqual(state["records"]["wins"], 10)
        # Every table remains available after ten matches in the same day.
        self.assertEqual(self.action("TRIAD_START", {"opponent": "saucer_attendant"})["status"], "completed")
        self.assertEqual(state["unlimited_matches"], True)
        self.assertEqual(self.db.one("SELECT COALESCE(SUM(payout),0) value FROM gold_saucer_history WHERE game='triple_triad'")["value"], 0)

    def test_web_accepts_new_id_but_bot_still_enforces_the_lock(self):
        completed = self.action("TRIAD_START", {"opponent": "moogle_dealer"})
        self.assertEqual(completed["status"], "failed")
        self.assertIn("previous Triple Triad circuit", completed["result"]["message"])
        self.assertIsNone(self.db.one("SELECT * FROM gold_saucer_triple_triad WHERE player_id='100'"))


if __name__ == "__main__":
    unittest.main()

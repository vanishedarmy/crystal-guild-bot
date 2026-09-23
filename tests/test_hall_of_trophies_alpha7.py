import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.trophies import TROPHY_CATALOG, reconcile_player_trophies, record_world_event_clear


class HallOfTrophiesAlpha7Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "guild.db")
        self.conn = self.db.conn
        self.player = "p1"
        self.conn.execute(
            "INSERT INTO players(twitch_id,username,display_name) VALUES (?,?,?)",
            (self.player, "player", "Player"),
        )
        self.conn.commit()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def owned(self):
        return {r["trophy_id"] for r in self.conn.execute("SELECT trophy_id FROM player_trophies WHERE player_id=?", (self.player,))}

    def test_catalog_contract_and_schema(self):
        self.assertEqual(DATABASE_SCHEMA_VERSION, 23)
        self.assertEqual(self.db.schema_version(), 23)
        self.assertEqual(len(TROPHY_CATALOG), 32)
        self.assertEqual(len({t["id"] for t in TROPHY_CATALOG}), 32)
        self.assertEqual(Counter(t["category"] for t in TROPHY_CATALOG), {
            "world_events": 12, "raids": 6, "hunts": 4, "triple_triad": 4, "fellowship": 6,
        })

    def test_world_events_require_exact_variant_history_and_reconcile_idempotently(self):
        self.assertEqual(reconcile_player_trophies(self.conn, self.player), [])
        self.assertNotIn("we_notorious_behemoth", self.owned())
        world_ids = [t["unlock"]["id"] for t in TROPHY_CATALOG if t["unlock"]["kind"] == "world_event"]
        for world_id in world_ids:
            record_world_event_clear(self.conn, self.player, world_id)
        first = reconcile_player_trophies(self.conn, self.player, source="test")
        self.assertEqual(len(first), 11)
        self.assertIn("we_all_phase1", self.owned())
        self.assertEqual(reconcile_player_trophies(self.conn, self.player, source="test"), [])

    def test_raid_hunt_and_triad_retroactive_evaluation(self):
        for boss in ["ifrit", "shiva", "ramuh", "garuda_prime", "titan", "leviathan", "bahamut"]:
            self.conn.execute("INSERT INTO player_boss_clears(player_id,boss_id,clears) VALUES (?,?,1)", (self.player, boss))
        for hunt in ["tyrant_of_the_rift", "the_mountain_moves", "dragon_beyond_the_veil"]:
            self.conn.execute("INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES (?,?,1)", (self.player, hunt))
        cards = ["chocobo","moogle","cactuar","bomb","flan","tonberry","coeurl","ahriman","malboro","ifrit","shiva","ramuh","leviathan","bahamut","odin"]
        self.conn.execute(
            "INSERT INTO player_triple_triad(player_id,collection_json,wins,current_streak,best_streak) VALUES (?,?,?,?,?)",
            (self.player, json.dumps(cards), 12, 1, 4),
        )
        reconcile_player_trophies(self.conn, self.player, source="retroactive")
        owned = self.owned()
        self.assertTrue({"raid_ifrit","raid_shiva","raid_titan","raid_bahamut","raid_primals"}.issubset(owned))
        self.assertTrue({"hunt_tyrant","hunt_mountain","hunt_veilscale","hunt_srank_all"}.issubset(owned))
        self.assertTrue({"tt_first_win","tt_streak_3","tt_cards_10","tt_cards_all"}.issubset(owned))

    def test_fellowship_requires_actual_contributor(self):
        projects = [
            ("guild_hall_t3","guild_hall",3,"fellowship_guildhall_3"),
            ("workshop_t3","workshop",3,"fellowship_workshop_3"),
            ("archives_t3","archives",3,"fellowship_archive_3"),
            ("airship_dock_t3","airship_dock",3,"fellowship_airship_3"),
            ("emporium_annex_t1","emporium_annex",1,"fellowship_annex"),
            ("trading_post_t1","trading_post",1,"fellowship_trading_post"),
        ]
        for project_id, facility_id, tier, _ in projects:
            self.conn.execute("INSERT OR REPLACE INTO fellowship_facilities(facility_id,tier) VALUES (?,?)", (facility_id,tier))
        reconcile_player_trophies(self.conn, self.player)
        self.assertFalse(any(trophy_id.startswith("fellowship_") for trophy_id in self.owned()))
        for project_id, _, _, _ in projects:
            self.conn.execute("INSERT INTO fellowship_project_members(project_id,player_id) VALUES (?,?)", (project_id,self.player))
        reconcile_player_trophies(self.conn, self.player, source="fellowship:test")
        self.assertTrue({row[3] for row in projects}.issubset(self.owned()))


if __name__ == "__main__":
    unittest.main()

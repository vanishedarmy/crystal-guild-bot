from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild import __version__
from crystal_guild.active_battle import has_status
from crystal_guild.data import GameData
from crystal_guild.database import DATABASE_SCHEMA_VERSION, Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.mercenary import HEROES_BY_ID
from crystal_guild.portal_actions import ACTION_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[1]


class EliteMercs182Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "guild.db")
        self.game = CrystalGuildEngine(
            self.db,
            GameData(ROOT / "data"),
            overlay_state_path=str(Path(self.temp.name) / "overlay.json"),
            rng=random.Random(1820),
        )
        self.assertTrue(self.game.recruit("100", "van", "Van").ok)
        self.assertTrue(self.game.choose_job("100", "warrior").ok)
        self.db.execute("UPDATE players SET level=60,hunt_seals=999,gil=1000000 WHERE twitch_id='100'")
        self.db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100','chieftains_challenge',30)")
        self.db.execute(
            "INSERT INTO player_dungeon_progress(player_id,dungeon_id,clears,defeats,retreats,best_rooms,last_outcome,last_completed_at) "
            "VALUES ('100','forgotten_ossuary',10,0,0,5,'complete',1)"
        )

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_release_contract_and_elite_registry(self):
        self.assertEqual(__version__, "1.9.3-guild-initiatives")
        self.assertEqual(DATABASE_SCHEMA_VERSION, 26)
        self.assertEqual(ACTION_PROTOCOL_VERSION, 39)
        state = self.game.portal_merc_state("100").data["merc_state"]
        self.assertEqual(len(state["heroes"]), 18)
        self.assertEqual(state["registry"], {"recruited": 6, "total": 18})
        elite = {hero["id"]: hero for hero in state["heroes"] if hero.get("tier") == "elite"}
        self.assertEqual(set(elite), {"lightning", "sephiroth", "rikku", "yshtola", "noctis", "cid"})
        self.assertTrue(all(hero["art_set"] == "a3" for hero in elite.values()))
        self.assertTrue(all(not hero["recruited"] for hero in elite.values()))

    def test_elite_recruitment_is_expensive_and_persistent(self):
        hero = HEROES_BY_ID["lightning"]
        cost = int(hero["recruitment"]["gil_cost"])
        before = int(self.db.one("SELECT gil FROM players WHERE twitch_id='100'")["gil"])
        result = self.game.portal_merc_recruit("100", "lightning", "elite-recruit-lightning")
        self.assertTrue(result.ok)
        self.assertEqual(result.data["gil_paid"], cost)
        self.assertEqual(int(self.db.one("SELECT gil FROM players WHERE twitch_id='100'")["gil"]), before - cost)
        lightning = next(h for h in result.data["merc_state"]["heroes"] if h["id"] == "lightning")
        self.assertTrue(lightning["recruited"])
        self.assertTrue(lightning["available"])
        self.assertEqual(lightning["fee_seals"], 18)

    def test_elite_damage_outscales_standard_burst(self):
        meta = {"stats": {"str": 180, "mag": 80}, "job_level": 40}
        cloud = self.game._merc_active_damage(meta, hero_id="cloud", enemy_max_hp=100000, raid=False)
        lightning = self.game._merc_active_damage(meta, hero_id="lightning", enemy_max_hp=100000, raid=False)
        sephiroth = self.game._merc_active_damage(meta, hero_id="sephiroth", enemy_max_hp=100000, raid=False)
        self.assertGreater(lightning, cloud)
        self.assertGreater(sephiroth, lightning)

    def test_yshtola_grand_recovery_heals_cleanses_and_buffs(self):
        meta = {
            "name": "Van", "hp": 250, "max_hp": 1000, "job_level": 40,
            "stats": {"str": 100, "mag": 160},
            "statuses": {"poison": {"turns": 3, "magnitude": 0.05}, "silence": {"turns": 2, "magnitude": 0}},
            "merc_contract": {"hero_id": "yshtola", "hero_name": "Y'shtola", "signature": "Aetherial Recovery"},
        }
        self.game.active_encounter = {"monster_hp": 1000, "monster_max_hp": 1000}
        log = []
        _, healing = self.game._merc_apply_active_assist("100", meta, {"hp": 1000}, log)
        self.assertGreaterEqual(healing, 400)
        self.assertFalse(has_status(meta["statuses"], "poison"))
        self.assertFalse(has_status(meta["statuses"], "silence"))
        self.assertTrue(has_status(meta["statuses"], "regen"))
        self.assertTrue(has_status(meta["statuses"], "protect"))

    def test_rikku_and_cid_double_bonus_merc_spoils(self):
        drops = [{"item_id": "potion", "chance": 1.0, "min": 1, "max": 1}]
        if "potion" not in self.game.data.items:
            self.skipTest("Potion fixture not available")
        for hero_id in ("rikku", "cid"):
            meta = {"merc_contract": {"hero_id": hero_id, "hero_name": hero_id.title(), "signature": HEROES_BY_ID[hero_id]["signature"]}}
            bonus = self.game._merc_bonus_loot("100", meta, drops, source=f"test:{hero_id}", grant=False)
            self.assertIsNotNone(bonus)
            self.assertEqual(bonus["quantity"], 2)


if __name__ == "__main__":
    unittest.main()

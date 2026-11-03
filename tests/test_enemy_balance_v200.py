"""V2.0.0 non-invasive enemy, raid and live-event balance regression suite."""
from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.balance import party_monster_hp
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.encounter_balance import (
    raid_combat_attacks, raid_combat_hp, world_event_combat_hp,
)
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]


class EnemyBalanceMathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GameData(ROOT / 'data')

    def test_all_38_bosses_have_scaled_group_budgets_and_nonzero_hp(self):
        self.assertEqual(len(self.data.bosses), 38)
        for boss in self.data.bosses.values():
            hp1 = raid_combat_hp(boss, 1)
            hp4 = raid_combat_hp(boss, 4)
            hp8 = raid_combat_hp(boss, 8)
            hp20 = raid_combat_hp(boss, 20)
            self.assertTrue(0 < hp1 < hp4 < hp8 < hp20, boss['id'])
            self.assertTrue(raid_combat_attacks(boss, 1) <= raid_combat_attacks(boss, 8))
            self.assertLessEqual(raid_combat_attacks(boss, 50), boss['attacks_per_round'])
            self.assertGreaterEqual(boss['enrage_round'], 10)

    def test_tier_progression_and_crafted_endgame_are_sensible(self):
        bosses=self.data.bosses
        self.assertLess(raid_combat_hp(bosses['goblin_king'],4),raid_combat_hp(bosses['ifrit'],4))
        self.assertLess(raid_combat_hp(bosses['ifrit'],4),raid_combat_hp(bosses['bahamut'],4))
        self.assertLess(raid_combat_hp(bosses['bahamut'],4),raid_combat_hp(bosses['omega'],4))
        self.assertLess(raid_combat_hp(bosses['omega'],4),raid_combat_hp(bosses['eclipse_sovereign'],4))
        self.assertGreater(raid_combat_hp(bosses['eclipse_sovereign'],4),90000)

    def test_elite_world_events_bounded_against_ordinary_party_curve(self):
        for level in (10,35,65,95,109):
            monster={'level':level}
            for roster in (1,2,4,8,20):
                regular=party_monster_hp(2000,roster)
                notorious=world_event_combat_hp(monster,combatants=roster,tier='notorious',threat='Extreme',ordinary_party_hp=regular)
                elite=world_event_combat_hp(monster,combatants=roster,tier='elite',threat='Apex',ordinary_party_hp=regular)
                self.assertGreater(notorious,0)
                self.assertLessEqual(elite,round(regular*2.15))
                self.assertGreaterEqual(elite,notorious)


class EnemyBalanceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Database(Path(self.tmp.name)/'balance.db')
        self.game=CrystalGuildEngine(self.db,GameData(ROOT/'data'),rng=random.Random(1723),
                overlay_state_path=str(Path(self.tmp.name)/'overlay.json'))
        for i in (1,2,3,4):
            pid=str(i)
            self.assertTrue(self.game.recruit(pid,'guild'+pid,'Guild'+pid).ok)
            self.assertTrue(self.game.choose_job(pid,'warrior').ok)
            self.db.execute('UPDATE players SET level=25 WHERE twitch_id=?',(pid,))
            self.game._save_hp(pid,self.game._max_hp(self.game._player(pid)))

    def tearDown(self):
        self.db.close();self.tmp.cleanup()

    def test_live_raid_roster_freezes_hp_once(self):
        self.assertTrue(self.game.spawn_boss('ifrit').ok)
        for i in (1,2,3,4):self.assertTrue(self.game.raid_join(str(i)).ok)
        self.assertTrue(self.game.start_raid().ok)
        boss=self.game.active_boss
        self.assertEqual(boss['balanced_party_size'],4)
        self.assertEqual(boss['max_hp'],raid_combat_hp(self.game.data.bosses['ifrit'],4))
        self.assertEqual(boss['current_hp'],boss['max_hp'])
        self.game.raid_roster['4']['hp']=0
        self.assertEqual(boss['max_hp'],raid_combat_hp(self.game.data.bosses['ifrit'],4))

    def test_manual_raid_hp_override_preserved(self):
        self.assertTrue(self.game.spawn_boss('goblin king').ok)
        self.game.active_boss['max_hp']=17
        self.game.active_boss['current_hp']=17
        self.assertTrue(self.game.raid_join('1').ok)
        self.assertTrue(self.game.start_raid().ok)
        self.assertEqual(self.game.active_boss['current_hp'],17)

    def test_world_event_hp_uses_party_budget_not_ordinary_venture(self):
        from crystal_guild.seasonal_events import set_event_control
        with self.db.tx() as conn:
            set_event_control(conn,enabled=False,paused=False,activation_mode='manual')
        spawn=self.game.maybe_spawn_world_event(stream_live=True,force=True)
        self.assertTrue(spawn.data['world_event_spawned'])
        for i in (1,2,3,4):
            self.assertTrue(self.game.join_encounter(str(i)).ok)
        monster=self.game._encounter_monster(self.game.active_encounter)
        ordinary=party_monster_hp(monster['hp'],4)
        self.assertTrue(self.game.start_encounter_battle().ok)
        self.assertEqual(self.game.active_encounter['monster_max_hp'],world_event_combat_hp(
            monster,combatants=4,
            tier=self.game.active_encounter['world_event_tier'],
            threat=self.game.world_event_catalog()[next(i for i,e in enumerate(self.game.world_event_catalog()) if e['id']==self.game.active_encounter['world_event_id'])]['threat'],
            ordinary_party_hp=ordinary))

if __name__=='__main__': unittest.main()

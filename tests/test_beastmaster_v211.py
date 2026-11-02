"""V2.11: verified pet participation -> persistent, one-time Bond XP and Portal visibility."""
from __future__ import annotations
import random
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from crystal_guild.beastmaster import award_companion_bond, bond_level_from_xp, bond_progress, companion_reward_xp, pet_damage_bonus
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

ROOT = Path(__file__).resolve().parents[1]

class BeastmasterBondTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GameData(ROOT / 'data')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'guild.sqlite'
        self.db = Database(self.path)
        self.game = CrystalGuildEngine(self.db, self.data, overlay_state_path=str(Path(self.tmp.name)/'overlay.json'), rng=random.Random(6))
        self.game.recruit('b','beast','Beast')
        self.db.execute("UPDATE players SET level=99,current_job='beastmaster',current_hp=600 WHERE twitch_id='b'")
        self.db.execute("INSERT OR REPLACE INTO player_jobs(player_id,job_id,level,jp) VALUES ('b','beastmaster',99,0)")
        self.db.execute("INSERT OR REPLACE INTO bestiary(player_id,monster_id,defeats) VALUES('b','wolf',3)")
        self.assertTrue(self.game.tame_beast('b','wolf').ok)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _meta(self, assists=1):
        return {'job_id':'beastmaster','_tamed_companion':self.game._selected_tamed_companion('b'), '_pet_assists':assists}

    def _grant(self, key='field:one', meta=None, enemy_level=25):
        with self.db.tx(immediate=True) as conn:
            return award_companion_bond(conn, 'b', self._meta() if meta is None else meta, key, enemy_level)

    def test_new_schema_and_rank_math(self):
        self.assertEqual(self.db.schema_version(),30)
        self.assertEqual(bond_progress(0)['rank'],1)
        self.assertEqual(bond_progress(25)['rank'],2)
        self.assertEqual(bond_progress(9025)['rank'],20)
        self.assertEqual(bond_progress(10_000_000)['rank'],20)
        self.assertEqual(bond_progress(9025)['xp_next'],0)
        self.assertLessEqual(companion_reward_xp(99_999),200)

    def test_award_once_per_encounter(self):
        first=self._grant()
        self.assertEqual(first['awarded'],70)
        self.assertIsNone(self._grant())
        row=self.db.one("SELECT bond_xp,bond_assists FROM beastmaster_companions WHERE player_id='b'")
        self.assertEqual((row['bond_xp'],row['bond_assists']),(70,1))
        self.assertEqual(self.db.one('SELECT COUNT(*) AS n FROM beastmaster_bond_receipts')['n'],1)

    def test_no_reward_without_valid_persisted_owned_companion(self):
        for meta in [self._meta(0), {'job_id':'warrior',**{k:v for k,v in self._meta().items() if k != 'job_id'}},
                     {'job_id':'beastmaster','_pet_assists':2, '_tamed_companion':{'monster_id':'coeurl'}},
                     {'job_id':'beastmaster','_pet_assists':2, '_tamed_companion':{'monster_id':'goblin'}}]:
            self.assertIsNone(self._grant('field:denied', meta))
        self.assertIsNone(self._grant('',self._meta()))
        self.assertEqual(self.db.one("SELECT bond_xp FROM beastmaster_companions WHERE player_id='b'")['bond_xp'],0)

    def test_rollback_and_retry_are_atomic(self):
        with self.assertRaises(RuntimeError):
            with self.db.tx(immediate=True) as conn:
                award_companion_bond(conn, 'b', self._meta(), 'raid:rollback', 50)
                raise RuntimeError('simulated crash')
        self.assertEqual(self.db.one('SELECT COUNT(*) AS n FROM beastmaster_bond_receipts')['n'],0)
        self.assertEqual(self._grant('raid:rollback', enemy_level=50)['awarded'],120)
        self.assertIsNone(self._grant('raid:rollback'))

    def test_portal_roster_is_sanitized_and_updates(self):
        self._grant()
        repository=PortalRepository(self.path, ROOT/'data')
        overview=repository.overview('beast')
        roster=overview['companions']['roster']
        self.assertEqual(overview['companions']['owned'],1)
        self.assertEqual(roster[0]['id'],'wolf')
        self.assertTrue(roster[0]['active'])
        self.assertEqual(roster[0]['xp'],70)
        self.assertGreater(roster[0]['bonus_pct'],0)
        self.assertNotIn('player_id',str(roster))
        repository.close()

    def test_restart_keeps_training_and_selection(self):
        self._grant()
        self.db.close();self.db=Database(self.path)
        self.game=CrystalGuildEngine(self.db,self.data,overlay_state_path=str(Path(self.tmp.name)/'overlay.json'),rng=random.Random(6))
        self.assertEqual(self.game._selected_tamed_companion('b')['bond_rank'],2)
        self.assertEqual(self.db.schema_version(),30)

    def test_bond_bonus_is_limited_and_requires_owned_species(self):
        a={'monster_id':'wolf','level':2,'bond_rank':1}
        b={'monster_id':'wolf','level':2,'bond_rank':20}
        self.assertGreater(pet_damage_bonus(b),pet_damage_bonus(a))
        self.assertLessEqual(pet_damage_bonus({'monster_id':'wolf','level':10_000,'bond_rank':999}),.12)
        self.assertEqual(pet_damage_bonus({'monster_id':'unknown','bond_rank':20}),0)

    def test_successful_raid_ability_marks_pet_assist(self):
        self.game.raid_roster={'b':{'name':'Beast','job_id':'beastmaster'}}
        self.game.active_boss={'id':'goblin','state':'combat','statuses':{},'current_hp':10000,
                               'max_hp':10000, 'round':1}
        self.game._initialize_raid_combat()
        meta=self.game.raid_roster['b']
        meta['ap']=max(100, int(meta.get('ap',0)))
        with patch.object(self.game,'_raid_base_damage',return_value=100):
            self.game._resolve_raid_ability('b',meta,{'ability_id':'call_beast','target_id':'boss'},0.0,[],[])
        self.assertEqual(meta.get('_pet_assists'),1)

    def test_real_field_reward_path_updates_pet_in_same_transaction(self):
        p = self.game._player('b')
        wolf=self.data.monsters['wolf']
        m=self._meta()
        first=self.game._award_victory('b', p, wolf, companion_meta=m,
                                        encounter_key='field:verified-victory')
        self.assertGreater(first['xp'],0)
        xp=self.db.one("SELECT bond_xp FROM beastmaster_companions WHERE player_id='b'")['bond_xp']
        self.assertGreater(xp,0)
        self.assertIsNone(self._grant('field:verified-victory'))
        self.assertEqual(self.db.one("SELECT bond_xp FROM beastmaster_companions WHERE player_id='b'")['bond_xp'],xp)

    def test_successful_active_ability_marks_pet_assist(self):
        self.game.encounter_roster={'b':{'name':'Beast','job_id':'beastmaster'}}
        self.game._initialize_active_combat({'kind':'venture','monster_id':'goblin'})
        meta=self.game.encounter_roster['b']
        self.assertIsNotNone(meta.get('_tamed_companion'))
        meta['ap']=max(100,int(meta.get('ap',0)))
        monster=self.data.monsters['goblin']
        self.game.active_encounter={'kind':'venture','monster_id':'goblin','monster_hp':100_000,'round':1}
        self.game._resolve_active_ability(meta,{'ability_id':'call_beast','target_id':'monster'},monster,[])
        self.assertEqual(meta.get('_pet_assists'),1)

if __name__ == '__main__':unittest.main()

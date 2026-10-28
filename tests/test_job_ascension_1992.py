"""v1.9.92 Job Ascension: persistent JLv.99, legacy mastery and new spell tiers."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.active_battle import match_ability, unlocked_abilities
from crystal_guild.balance import jp_to_next
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

DATA = Path(__file__).resolve().parents[1] / 'data'


class JobAscensionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / 'test.db')
        self.data = GameData(DATA)
        self.engine = CrystalGuildEngine(self.db, self.data, rng=random.Random(7), overlay_state_path=str(Path(self.temp.name) / 'overlay.json'))
        self.assertTrue(self.engine.recruit('100', 'ascended', 'Ascended').ok)
        self.assertTrue(self.engine.choose_job('100', 'whitemage').ok)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_every_job_has_new_unlocks_through_99(self):
        self.assertEqual(self.data.validate(), [])
        self.assertEqual(len(self.data.jobs), 18)
        for job_id, job in self.data.jobs.items():
            for level in (55, 65, 75, 85, 95):
                self.assertTrue(any(a['level'] == level for a in job['abilities']), (job_id, level))
            for level in (52, 58, 64, 70, 76, 82, 88, 94, 99):
                self.assertTrue(any(a['level'] == level for a in self.data.active_abilities[job_id]), (job_id, level))

    def test_classic_magic_spells_and_legacy_cure_ii_alias(self):
        black = self.data.active_abilities['blackmage']
        white = self.data.active_abilities['whitemage']
        for spell in ('Firaga', 'Blizzaga', 'Thundaga', 'Firaja', 'Blizzaja', 'Thundaja', 'Meteor'):
            self.assertIn(spell, [a['name'] for a in black])
        for spell in ('Curaga', 'Curaja', 'Protectra', 'Shellra', 'Arise', 'Holyga'):
            self.assertIn(spell, [a['name'] for a in white])
        self.assertIsNone(match_ability(unlocked_abilities(white, 50), 'Curaja')[0])
        self.assertEqual(match_ability(unlocked_abilities(white, 52), 'Curaja')[0]['id'], 'curaja')
        self.assertEqual(match_ability(white, 'cure ii Ascended')[0]['id'], 'cure_ii')
        self.assertEqual(match_ability(white, 'Cura Ascended')[0]['id'], 'cure_ii')

    def test_job_levels_continue_after_mastery_without_reset(self):
        # JLv.50 is still the mastery threshold; pre-existing JLv.50 characters can advance.
        amount = sum(jp_to_next(lvl) for lvl in range(50, 55))
        self.db.execute("UPDATE player_jobs SET level=50,jp=? WHERE player_id='100' AND job_id='whitemage'", (amount,))
        msg = self.engine._process_levels('100', 'whitemage')
        state = self.db.one("SELECT level,jp FROM player_jobs WHERE player_id='100' AND job_id='whitemage'")
        self.assertEqual(state['level'], 55)
        self.assertEqual(state['jp'], 0)
        self.assertTrue(any('Curaja' in message for message in msg))
        self.assertTrue(any('Healing Grace' in message for message in msg))
        self.assertTrue(self.engine._job_level('100', 'whitemage') >= 50)

    def test_99_cap_does_not_consume_extra_jp(self):
        amount = jp_to_next(98) + 111
        self.db.execute("UPDATE player_jobs SET level=98,jp=? WHERE player_id='100' AND job_id='whitemage'", (amount,))
        self.engine._process_levels('100', 'whitemage')
        state = self.db.one("SELECT level,jp FROM player_jobs WHERE player_id='100' AND job_id='whitemage'")
        self.assertEqual((state['level'],state['jp']), (99,111))
        portal = self.engine._portal_character_state_data('100')
        white = next(job for job in portal['jobs'] if job['id'] == 'whitemage')
        self.assertEqual((white['level'],white['jp_next'],white['mastered']), (99,0,True))
        self.engine._process_levels('100', 'whitemage')
        self.assertEqual(self.db.one("SELECT level FROM player_jobs WHERE player_id='100' AND job_id='whitemage'")['level'], 99)

    def test_arise_is_true_full_health_revive(self):
        arise = next(a for a in self.data.active_abilities['whitemage'] if a['id']=='arise')
        self.assertEqual(arise['target'],'ally')
        self.assertEqual(arise['effects'], [{'type':'revive','fraction':1.0}])

if __name__ == '__main__':
    unittest.main()

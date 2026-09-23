"""Step 5: physical art, secret Hall slots and atomic Moment trophy receipts."""
from __future__ import annotations
import json
import random
import tempfile
import unittest
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.moments import EVENT_FACTS
from crystal_guild.moments_progress import award_settlement
from crystal_guild.player_snapshot import PortalRepository
from crystal_guild.trophies import TROPHY_CATALOG, reconcile_player_trophies

ROOT=Path(__file__).resolve().parents[1]
PAIR={
    'moment_a_little_too_close':'moment_trophy_world_event_close_call',
    'moment_last_one_standing':'moment_trophy_raid_last_survivor',
}

class Step5MomentTrophyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Database(Path(self.tmp.name)/'game.db')
        self.data=GameData(ROOT/'data')
        self.engine=CrystalGuildEngine(self.db,self.data,rng=random.Random(10),overlay_state_path=str(Path(self.tmp.name)/'overlay.json'))
        for pid,name in [('1','van'),('2','mira')]:
            self.assertTrue(self.engine.recruit(pid,name,name.title()).ok)
        self.repo=PortalRepository(self.db.path,ROOT/'data')
    def tearDown(self):
        self.repo.close();self.db.close();self.tmp.cleanup()
    def proof(self,moment_id):
        moment=self.data.moments[moment_id];trigger=moment['trigger']
        facts={name:(False if kind is bool else 0 if kind is int else 0.0 if kind is float else '') for name,kind in EVENT_FACTS[trigger].items()}
        facts.update(event=trigger,settled=True)
        for rule in moment['condition']['rules']:
            if rule['op']=='gte_multiple':
                facts[rule['other_field']]=10;facts[rule['field']]=10*rule['multiplier']
            else: facts[rule['field']]=rule['value']
        return facts
    def trophy_rows(self,pid):
        return [dict(row) for row in self.db.all('SELECT * FROM player_trophies WHERE player_id=? AND trophy_id LIKE ?', (pid,'moment_trophy_%'))]
    def award(self,moment_id,player='1',event=None):
        with self.db.tx() as conn:
            return award_settlement(conn,self.data,player,event or f'event:{moment_id}',self.proof(moment_id))

    def test_two_new_trophies_belong_only_to_their_exact_secret_moments(self):
        rows=[r for r in TROPHY_CATALOG if r['unlock']['kind']=='moment']
        self.assertEqual(len(rows),2)
        self.assertEqual({r['id'] for r in rows},set(PAIR.values()))
        self.assertTrue(all(r['secret'] and r['art']!=r['locked_art'] for r in rows))
        self.assertEqual(self.trophy_rows('1'),[])

    def test_ownership_is_atomic_once_only_and_does_not_reset_old_trophies(self):
        self.award('moment_a_little_too_close')
        self.assertEqual([r['trophy_id'] for r in self.trophy_rows('1')],[PAIR['moment_a_little_too_close']])
        self.assertEqual(self.award('moment_a_little_too_close',event='second-round'),[])
        self.assertEqual(len(self.trophy_rows('1')),1)
        self.award('moment_last_one_standing')
        self.assertEqual({r['trophy_id'] for r in self.trophy_rows('1')},set(PAIR.values()))
        self.assertEqual(self.trophy_rows('2'),[])

    def test_moment_title_and_trophy_roll_back_with_failed_source_event(self):
        with self.assertRaisesRegex(RuntimeError,'cancel'):
            with self.db.tx() as conn:
                award_settlement(conn,self.data,'1','event:rolledback',self.proof('moment_last_one_standing'))
                raise RuntimeError('cancel')
        self.assertEqual(self.trophy_rows('1'),[])
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM player_titles WHERE player_id='1' AND title_id LIKE 'moment_title_%'")['n'],0)
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM player_moment_unlocks WHERE player_id='1'")['n'],0)

    def test_step3_existing_ownership_can_reconcile_new_trophy_with_no_fabricated_moment(self):
        self.award('moment_a_little_too_close')
        self.db.execute('DELETE FROM player_trophies WHERE player_id=? AND trophy_id=?',('1',PAIR['moment_a_little_too_close']))
        self.assertEqual([*reconcile_player_trophies(self.db.conn,'1')],['The Close Call'])
        self.assertEqual(reconcile_player_trophies(self.db.conn,'1'),[])
        self.assertEqual(self.trophy_rows('2'),[])
        self.assertFalse(self.trophy_rows('1')[0]['trophy_id']==PAIR['moment_last_one_standing'])

    def test_undiscovered_hall_slots_hide_real_ids_names_art_and_categories(self):
        view=self.repo.trophies('van');slots=view['moment_slots']
        self.assertEqual(len(slots),2)
        self.assertTrue(all(slot['category']=='mystery' and slot['art'] is None and slot['id'].startswith('sealed_trophy_slot_') for slot in slots))
        self.assertNotIn('The Close Call',json.dumps(view));self.assertNotIn('The Last Standing',json.dumps(view))
        self.award('moment_a_little_too_close')
        view=self.repo.trophies('van');owned=next(slot for slot in view['moment_slots'] if slot['earned'])
        self.assertEqual(owned['id'],PAIR['moment_a_little_too_close'])
        self.assertTrue(owned['art'].endswith('/world-event-close-call.webp'))
        entry=next(m for m in self.repo.records('van')['moments']['entries'] if m['id']=='moment_a_little_too_close')
        self.assertEqual(entry['trophy_reward']['name'],'The Close Call')
        self.assertNotIn('The Close Call',json.dumps(self.repo.records('mira')))
        self.assertEqual(sum(not slot['earned'] for slot in view['moment_slots']),1)
        self.assertTrue(all(not slot['earned'] for slot in self.repo.trophies('mira')['moment_slots']))

    def test_records_remain_spoiler_safe_and_do_not_claim_unowned_trophies(self):
        self.assertEqual(len(self.repo.records('van')['moments']['entries']),12)
        self.assertNotIn('moment_trophy_world_event_close_call',json.dumps(self.repo.records('van')))
        self.assertEqual(self.trophy_rows('1'),[])
        self.repo.trophies('van');self.repo.records('van')
        self.assertEqual(self.trophy_rows('1'),[])

if __name__=='__main__':unittest.main()

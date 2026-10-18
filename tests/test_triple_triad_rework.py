from __future__ import annotations
import json,random,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.triple_triad import *
ROOT=Path(__file__).resolve().parents[1]
class TripleTriadReworkTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.db=Database(Path(self.temp.name)/'guild.db')
  self.game=CrystalGuildEngine(self.db,GameData(ROOT/'data'),overlay_state_path=str(Path(self.temp.name)/'overlay.json'),rng=random.Random(500))
  self.game.recruit('100','van','Van');self.game.choose_job('100','warrior')
 def tearDown(self):self.db.close();self.temp.cleanup()
 def state(self):return self.game.portal_triad_state('100').data['triple_triad_state']
 def settle(self,opponent='saucer_attendant',outcome='win',suffix='x'):
  result=self.game.portal_triad_start('100',opponent,'start-'+suffix);self.assertTrue(result.ok,result.messages)
  cards=self.state()['deck']+TRIPLE_TRIAD_OPPONENTS_BY_ID[opponent]['deck'][:4]
  pc={'win':6,'draw':5,'loss':3}[outcome]
  board=[{'card_id':c,'owner':'player' if i<pc else 'npc'} for i,c in enumerate(cards)]
  match=self.db.one("SELECT * FROM gold_saucer_triple_triad WHERE player_id='100'")
  with self.db.tx(immediate=True) as conn:
   self.game._triple_triad_resolve_sql(conn,'100',match,board,[],[TRIPLE_TRIAD_OPPONENTS_BY_ID[opponent]['deck'][-1]],2000000000)
  return self.state()
 def test_catalog_reachable_and_bounded(self):
  self.assertEqual(len(TRIPLE_TRIAD_CARDS),45)
  self.assertEqual([sum(c['rarity']==r for c in TRIPLE_TRIAD_CARDS) for r in range(1,6)],[15,10,8,7,5])
  reachable=set(TRIPLE_TRIAD_STARTER_COLLECTION);caps={'Novice':52,'Standard':75,'Skilled':95,'Expert':118,'Master':150}
  for o in TRIPLE_TRIAD_OPPONENTS:
   self.assertEqual(len(set(o['deck'])),5);self.assertLessEqual(triple_triad_power(o['deck']),caps[o['difficulty']]);reachable.update(o['rewards'])
  self.assertEqual(reachable,set(TRIPLE_TRIAD_CARDS_BY_ID))
 def test_upgrade_preserves_collection_deck_records_once(self):
  self.state();owned=list(TRIPLE_TRIAD_STARTER_DECK)+['tonberry','bahamut'];deck=['bahamut','tonberry','bomb','moogle','cactuar']
  with self.db.tx() as conn:
   conn.execute("DELETE FROM gold_saucer_history WHERE game='triad_collection'")
   conn.execute("UPDATE player_triple_triad SET collection_json=?,deck_json=?,wins=8,best_streak=4 WHERE player_id='100'",(json.dumps(owned),json.dumps(deck)))
  state=self.state();self.assertEqual(state['owned_count'],12);self.assertEqual(state['deck'],deck);self.assertEqual(state['records']['best_streak'],4)
  self.assertTrue(all(o['unlocked'] for o in state['opponents']));self.state()
  self.assertEqual(self.db.one("SELECT COUNT(*) n FROM gold_saucer_history WHERE game='triad_collection'")['n'],1)
 def test_novice_weaker_deck_and_open_hand(self):
  state=self.state();self.assertEqual(state['owned_count'],10);self.assertLess(state['opponents'][0]['deck_power'],state['deck_power'])
  a=self.game.portal_triad_start('100','saucer_attendant','open');self.assertTrue(a.ok)
  self.assertEqual(len(a.data['triple_triad_state']['match']['npc_hand']),5)
 def test_circuit_requires_both_opponents_and_bonus_once(self):
  a=self.settle(suffix='a');self.assertEqual(a['circuits'][0]['defeated'],1);self.assertFalse(a['circuits'][1]['unlocked'])
  self.assertFalse(self.game.portal_triad_start('100','moogle_dealer','locked').ok)
  a=self.settle('chocobo_breeder',suffix='b');self.assertTrue(a['circuits'][0]['cleared']);self.assertTrue(a['circuits'][1]['unlocked'])
  self.assertEqual(a['match']['rewards']['circuit_cleared'],True);self.settle(suffix='c')
  self.assertEqual(self.db.one("SELECT COUNT(*) n FROM gold_saucer_history WHERE game='triad_circuit'")['n'],1)
 def test_missing_first_and_duplicate_quantities(self):
  ids=[]
  for i in range(4):
   state=self.settle(suffix=str(i));ids.append(state['match']['rewards']['card_reward'])
  self.assertEqual(len(set(ids[:3])),3)
  self.assertEqual(next(c for c in state['collection'] if c['id']==ids[-1])['quantity'],2)
 def test_draw_loss_keep_cards_without_currency(self):
  count=self.state()['owned_count']
  with patch.object(self.game.rng,'random',return_value=.99):
   a=self.settle(outcome='draw',suffix='d');self.assertEqual(a['owned_count'],count);self.assertNotIn('payout',a['match']['rewards'])
   a=self.settle(outcome='loss',suffix='l');self.assertEqual(a['owned_count'],count);self.assertNotIn('payout',a['match']['rewards'])
 def test_card_pity_on_fourth_win(self):
  self.state()
  with self.db.tx() as conn:conn.execute("UPDATE player_triple_triad SET wins=8 WHERE player_id='100'")
  with patch.object(self.game.rng,'random',return_value=.99):
   for i in range(3):self.assertIsNone(self.settle('crystal_master',suffix='miss'+str(i))['match']['rewards']['card_reward'])
   a=self.settle('crystal_master',suffix='guarantee');self.assertIsNotNone(a['match']['rewards']['card_reward']);self.assertTrue(a['match']['rewards']['guaranteed_card'])
 def test_start_move_retry_refresh_no_duplicates(self):
  a=self.game.portal_triad_start('100','saucer_attendant','once');b=self.game.portal_triad_start('100','saucer_attendant','once')
  self.assertEqual(a.data['triple_triad_match_id'],b.data['triple_triad_match_id'])
  c=a.data['triple_triad_state']['match']['player_hand'][0]['id']
  a=self.game.portal_triad_play('100',c,0,'move');b=self.game.portal_triad_play('100',c,0,'move')
  self.assertTrue(a.ok);self.assertEqual(a.data['triple_triad_move'],b.data['triple_triad_move']);self.assertEqual(len(self.state()['match']['player_hand']),4)
 def test_real_match_total_ten_settles_once(self):
  state=self.game.portal_triad_start('100','saucer_attendant','real').data['triple_triad_state']
  for i in range(5):
   m=state['match'];c=m['player_hand'][0]['id'];cell=next(i for i,c in enumerate(m['board']) if c is None)
   a=self.game.portal_triad_play('100',c,cell,'real'+str(i));self.assertTrue(a.ok);state=a.data['triple_triad_state']
  self.assertFalse(state['active']);self.assertEqual(state['match']['player_score']+state['match']['npc_score'],10)
  self.assertEqual(self.db.one("SELECT COUNT(*) n FROM gold_saucer_history WHERE game='triple_triad'")['n'],1)
 def test_legacy_active_match_no_new_payout(self):
  self.state();a=self.game.portal_triad_start('100','saucer_attendant','old')
  with self.db.tx() as conn:conn.execute("DELETE FROM gold_saucer_history WHERE game='triad_collection'")
  self.assertEqual(self.state()['match']['id'],a.data['triple_triad_match_id'])
  match=self.db.one("SELECT * FROM gold_saucer_triple_triad WHERE player_id='100'")
  board=[{'card_id':'goblin','owner':'player' if i<5 else 'npc'} for i in range(9)]
  with self.db.tx(immediate=True) as conn:_,d=self.game._triple_triad_resolve_sql(conn,'100',match,board,[],['bat'],2000000000)
  self.assertNotIn('payout',d);self.assertEqual(self.db.one("SELECT wager FROM gold_saucer_history WHERE game='triple_triad'")['wager'],0)
if __name__=='__main__':unittest.main()

"""Stream Venture party Mist support safety, pricing and persistence."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.help_system import help_messages

ROOT = Path(__file__).resolve().parents[1]

class VentureMistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'mist.db'
        self.db = Database(self.path)
        self.data = GameData(ROOT / 'data')
        self.game = self.create_game(self.db)
        for pid, job in [('a', 'warrior'), ('b', 'whitemage'), ('c', 'blackmage')]:
            self.assertTrue(self.game.recruit(pid, pid, pid.upper()).ok)
            self.assertTrue(self.game.choose_job(pid, job).ok)
            self.db.execute('UPDATE players SET gil=2000 WHERE twitch_id=?', (pid,))

    def create_game(self, db):
        return CrystalGuildEngine(db, self.data, rng=random.Random(202),
            venture_cooldown_seconds=0, encounter_join_seconds=5,
            encounter_round_seconds=60, overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'))

    def tearDown(self):
        self.db.close(); self.tmp.cleanup()

    def gil(self, pid='a'):
        return int(self.db.one('SELECT gil FROM players WHERE twitch_id=?', (pid,))['gil'])

    def receipts(self, pid='a'):
        return self.db.all("SELECT amount FROM transactions WHERE player_id=? AND source='venture_party_heal'", (pid,))

    def launch(self, with_ally=True):
        started = self.game.venture('a', bypass_cooldown=True)
        self.assertTrue(started.ok, started.messages)
        if with_ally:
            self.assertTrue(self.game.join_encounter('b', bypass_cooldown=True).ok)
        self.assertTrue(self.game.start_encounter_battle(started.data['encounter_id']).ok)
        return started.data['encounter_id']

    def damage(self):
        for meta in self.game.encounter_roster.values():
            meta['hp'] = max(1, int(meta['max_hp'])-500)
            if int(meta['max_mp']) > 0:
                meta['mp'] = 0

    def test_four_tiers_use_catalog_strengths_and_correct_prices(self):
        for tier, cost, hp_item, ether_item in [
            (1,100,'potion','ether'), (2,250,'hi_potion','ether'),
            (3,500,'mega_potion','hi_ether'), (4,1000,'x_potion','hi_ether'),
        ]:
            with self.subTest(tier=tier):
                self.launch()
                self.damage()
                before={k:dict(v) for k,v in self.game.encounter_roster.items()}
                original=self.gil()
                result=self.game.heal_venture_party('a',str(tier) if tier != 1 else None)
                self.assertTrue(result.ok,result.messages)
                self.assertEqual(self.gil(),original-cost)
                self.assertEqual(self.receipts('a')[-1]['amount'],-cost)
                self.assertEqual(result.data['tier'],tier)
                self.assertEqual(result.data['cost'],cost)
                hp_total=mp_total=0
                for pid, prev in before.items():
                    curr=self.game.encounter_roster[pid]
                    hp_effect=self.data.items[hp_item]['use']['effects'][0]
                    amount=max(int(hp_effect.get('amount',0)),int(prev['max_hp']*float(hp_effect.get('fraction',0))))
                    expected_hp=min(prev['max_hp'],prev['hp']+amount)
                    mp_effect=self.data.items[ether_item]['use']['effects'][0]
                    restore=max(int(mp_effect.get('amount',0)),int(prev['max_mp']*float(mp_effect.get('fraction',0))))
                    expected_mp=min(prev['max_mp'],prev['mp']+restore)
                    hp_total+=expected_hp-prev['hp'];mp_total+=expected_mp-prev['mp']
                    self.assertEqual(curr['hp'],expected_hp)
                    self.assertEqual(curr['mp'],expected_mp)
                    self.assertEqual(curr['ap'],prev['ap'])
                self.assertEqual(result.data['hp_restored'],hp_total)
                self.assertEqual(result.data['mp_restored'],mp_total)
                self.game._clear_encounter(self.game.active_encounter['id'])

    def test_once_per_player_even_on_different_tier_and_other_can_help(self):
        self.launch(); self.damage()
        self.assertTrue(self.game.heal_venture_party('a',1).ok)
        money=self.gil()
        for tier in [1,2,3,4]:
            result=self.game.heal_venture_party('a',tier)
            self.assertFalse(result.ok)
            self.assertIn('already used',result.messages[0])
        self.assertEqual(self.gil(),money)
        self.assertEqual(len(self.receipts('a')),1)
        self.damage()
        self.assertTrue(self.game.heal_venture_party('b',2).ok)
        self.assertEqual(self.gil('b'),1750)
        self.assertEqual(len(self.receipts('b')),1)

    def test_no_charge_if_insufficient_then_can_try_again(self):
        self.launch(); self.damage()
        self.db.execute("UPDATE players SET gil=99 WHERE twitch_id='a'")
        failed=self.game.heal_venture_party('a')
        self.assertFalse(failed.ok)
        self.assertIn('need 1 more',failed.messages[0]); self.assertEqual(self.gil(),99)
        self.assertFalse(self.game.encounter_roster['a'].get('mist_heal_used'))
        self.assertFalse(self.receipts())
        self.db.execute("UPDATE players SET gil=100 WHERE twitch_id='a'")
        self.assertTrue(self.game.heal_venture_party('a').ok)
        self.assertEqual(self.gil(),0)

    def test_no_battle_nonmember_rally_and_bad_tier(self):
        self.assertFalse(self.game.heal_venture_party('a').ok)
        opened=self.game.venture('a', bypass_cooldown=True)
        self.assertFalse(self.game.heal_venture_party('a').ok)
        self.assertTrue(self.game.start_encounter_battle(opened.data['encounter_id']).ok)
        self.assertFalse(self.game.heal_venture_party('c').ok)
        self.assertFalse(self.game.heal_venture_party('a','5').ok)
        self.assertFalse(self.game.heal_venture_party('a','garbage').ok)
        self.assertEqual(self.gil(),2000)
        self.assertFalse(self.receipts())

    def test_full_party_no_charge_and_ko_not_revived(self):
        self.launch()
        self.assertFalse(self.game.heal_venture_party('a').ok)
        self.assertEqual(self.gil(),2000)
        self.assertFalse(self.game.encounter_roster['a'].get('mist_heal_used'))
        self.game.encounter_roster['b']['hp']=0
        self.game.encounter_roster['a']['hp']=1
        self.assertTrue(self.game.heal_venture_party('a',4).ok)
        self.assertEqual(self.game.encounter_roster['b']['hp'],0)
        self.assertEqual(self.gil(),1000)

    def test_ko_actor_cannot_use(self):
        self.launch();self.damage()
        self.game.encounter_roster['a']['hp']=0
        self.assertFalse(self.game.heal_venture_party('a').ok)
        self.assertEqual(self.gil(),2000)

    def test_restart_replay_protection(self):
        self.launch();self.damage()
        self.assertTrue(self.game.heal_venture_party('a',3).ok)
        other_db=Database(self.path)
        try:
            other_game=self.create_game(other_db)
            self.assertEqual(other_game.encounter_roster['a']['mist_heal_used'],3)
            self.assertFalse(other_game.heal_venture_party('a',1).ok)
            self.assertEqual(self.gil(),1500)
            self.assertEqual(len(self.receipts()),1)
        finally:other_db.close()

    def test_two_bot_connections_cannot_charge_same_player_twice(self):
        self.launch(); self.damage()
        other_db=Database(self.path)
        try:
            stale=self.create_game(other_db)
            self.assertTrue(self.game.heal_venture_party('a',1).ok)
            self.assertFalse(stale.heal_venture_party('a',4).ok)
            self.assertEqual(self.gil(),1900)
            self.assertEqual(len(self.receipts()),1)
            self.assertEqual(stale.encounter_roster['a']['mist_heal_used'],1)
        finally:other_db.close()

    def test_checkpoint_failure_rolls_back_charge_and_healing(self):
        from unittest.mock import patch
        self.launch(); self.damage()
        original=self.game.encounter_roster['a']['hp']
        with patch.object(self.game, '_persist_runtime_state', side_effect=RuntimeError('checkpoint failure')):
            with self.assertRaisesRegex(RuntimeError,'checkpoint failure'):
                self.game.heal_venture_party('a',1)
        self.assertEqual(self.gil(),2000)
        self.assertFalse(self.receipts())
        self.assertEqual(self.game.encounter_roster['a']['hp'],original)
        self.assertFalse(self.game.encounter_roster['a'].get('mist_heal_used'))

    def test_separate_venture_resets_use(self):
        self.launch(with_ally=False);self.damage()
        self.assertTrue(self.game.heal_venture_party('a').ok)
        self.game._clear_encounter(self.game.active_encounter['id'])
        self.launch(with_ally=False);self.damage()
        self.assertTrue(self.game.heal_venture_party('a').ok)
        self.assertEqual(len(self.receipts()),2)
        self.assertEqual(self.gil(),1800)

    def test_help_topics_and_command_adapter_exist(self):
        self.assertIn('!healparty', ' '.join(help_messages('healparty')))
        source = (ROOT / "crystal_guild/twitch_bot.py").read_text()
        self.assertIn("async def healparty(self, ctx:", source)
        self.assertIn("self.game.heal_party(uid, tier)", source)

if __name__=='__main__': unittest.main()

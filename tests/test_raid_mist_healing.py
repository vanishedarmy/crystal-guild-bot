"""Stream Mist !healparty supports Raids with independent per-run receipts."""
from __future__ import annotations
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.help_system import help_messages

ROOT = Path(__file__).resolve().parents[1]

class RaidMistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'raid_mist.db'
        self.db = Database(self.path)
        self.data = GameData(ROOT / 'data')
        self.game = self.create_game(self.db)
        for pid, job in [('a','warrior'), ('b','whitemage'), ('c','blackmage')]:
            self.assertTrue(self.game.recruit(pid, pid, pid.upper()).ok)
            self.assertTrue(self.game.choose_job(pid, job).ok)
            self.db.execute('UPDATE players SET gil=3000 WHERE twitch_id=?', (pid,))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def create_game(self, db):
        return CrystalGuildEngine(db, self.data, rng=random.Random(17),
            raid_join_seconds=90, raid_round_seconds=90,
            venture_cooldown_seconds=0, encounter_join_seconds=5,
            overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'))

    def gil(self, pid='a'):
        return int(self.db.one('SELECT gil FROM players WHERE twitch_id=?',(pid,))['gil'])

    def receipts(self,pid='a'):
        return self.db.all("SELECT amount, source FROM transactions WHERE player_id=? AND source IN ('raid_party_heal','venture_party_heal')",(pid,))

    def begin(self,with_ally=True):
        self.assertTrue(self.game.spawn_boss('goblin_king').ok)
        self.assertTrue(self.game.raid_join('a').ok)
        if with_ally:
            self.assertTrue(self.game.raid_join('b').ok)
        self.assertTrue(self.game.start_raid().ok)
        return self.game.active_boss['raid_instance_id']

    def damage(self):
        for meta in self.game.raid_roster.values():
            meta['hp'] = max(1,int(meta['max_hp'])-500)
            if int(meta['max_mp'])>0:meta['mp']=0

    def test_all_raid_tiers_restore_party_using_item_catalog(self):
        for tier,cost,hp_id,mp_id in [
            (1,100,'potion','ether'), (2,250,'hi_potion','ether'),
            (3,500,'mega_potion','hi_ether'), (4,1000,'x_potion','hi_ether')]:
            with self.subTest(tier=tier):
                self.begin();self.damage()
                before={pid:dict(row) for pid,row in self.game.raid_roster.items()}
                original=self.gil()
                result=self.game.heal_party('a',tier)
                self.assertTrue(result.ok,result.messages)
                self.assertEqual(result.data['activity'],'raid')
                self.assertEqual(result.data['tier'],tier)
                self.assertEqual(result.data['cost'],cost)
                self.assertEqual(self.gil(),original-cost)
                self.assertEqual(self.receipts()[-1]['amount'],-cost)
                self.assertEqual(self.receipts()[-1]['source'],'raid_party_heal')
                hp_effect=self.data.items[hp_id]['use']['effects'][0]
                mp_effect=self.data.items[mp_id]['use']['effects'][0]
                total_hp=total_mp=0
                for pid,prev in before.items():
                    row=self.game.raid_roster[pid]
                    hp_amount=max(int(hp_effect.get('amount',0)),int(prev['max_hp']*float(hp_effect.get('fraction',0))))
                    mp_amount=max(int(mp_effect.get('amount',0)),int(prev['max_mp']*float(mp_effect.get('fraction',0))))
                    expected_hp=min(prev['max_hp'],prev['hp']+hp_amount)
                    expected_mp=min(prev['max_mp'],prev['mp']+mp_amount)
                    self.assertEqual((row['hp'],row['mp']),(expected_hp,expected_mp))
                    self.assertEqual(row['ap'],prev['ap'])
                    total_hp+=expected_hp-prev['hp'];total_mp+=expected_mp-prev['mp']
                self.assertEqual((result.data['hp_restored'],result.data['mp_restored']),(total_hp,total_mp))
                self.assertEqual(self.game.raid_roster['a']['healing'],total_hp)
                self.game._finish_raid(False,reason='test raid reset')

    def test_once_per_player_per_raid_other_raider_can_heal(self):
        self.begin();self.damage()
        self.assertTrue(self.game.heal_party('a',1).ok)
        balance=self.gil()
        for tier in (1,2,3,4):
            result=self.game.heal_party('a',tier)
            self.assertFalse(result.ok)
            self.assertIn('already used',result.messages[0])
        self.assertEqual(self.gil(),balance)
        self.assertEqual(len(self.receipts()),1)
        self.damage()
        self.assertTrue(self.game.heal_party('b',2).ok)
        self.assertEqual(self.gil('b'),2750)

    def test_raid_replay_after_restart_and_two_bot_instances(self):
        self.begin();self.damage()
        other_db=Database(self.path)
        try:
            stale=self.create_game(other_db)
            self.assertTrue(self.game.heal_party('a',4).ok)
            self.assertFalse(stale.heal_party('a',1).ok)
            self.assertEqual(stale.raid_roster['a']['mist_heal_used'],4)
            self.assertEqual(self.gil(),2000)
            self.assertEqual(len(self.receipts()),1)
            # Persistence is not merely in-memory on the initiating Bot.
            third=self.create_game(other_db)
            self.assertFalse(third.heal_party('a',2).ok)
        finally:
            other_db.close()

    def test_raid_rally_and_nonparticipant_rejected_no_charge(self):
        self.assertFalse(self.game.heal_party('a',1).ok)
        self.assertTrue(self.game.spawn_boss('goblin_king').ok)
        self.assertTrue(self.game.raid_join('a').ok)
        self.assertFalse(self.game.heal_party('a',1).ok)
        self.assertTrue(self.game.start_raid().ok)
        self.assertFalse(self.game.heal_party('c',1).ok)
        self.assertFalse(self.game.heal_party('a',5).ok)
        self.assertEqual(self.gil(),3000)
        self.assertEqual(self.receipts(),[])

    def test_insufficient_gil_does_not_consume_use(self):
        self.begin();self.damage()
        self.db.execute("UPDATE players SET gil=249 WHERE twitch_id='a'")
        result=self.game.heal_party('a',2)
        self.assertFalse(result.ok)
        self.assertIn('need 1 more',result.messages[0])
        self.assertFalse(self.game.raid_roster['a'].get('mist_heal_used'))
        self.assertEqual(self.gil(),249)
        self.assertFalse(self.receipts())
        self.db.execute("UPDATE players SET gil=250 WHERE twitch_id='a'")
        self.assertTrue(self.game.heal_party('a',2).ok)

    def test_full_raid_no_charge_and_ko_not_revived(self):
        self.begin()
        result=self.game.heal_party('a',1)
        self.assertFalse(result.ok)
        self.assertEqual(self.gil(),3000)
        self.assertFalse(self.game.raid_roster['a'].get('mist_heal_used'))
        self.game.raid_roster['b']['hp']=0
        self.game.raid_roster['a']['hp']=1
        self.assertTrue(self.game.heal_party('a',1).ok)
        self.assertEqual(self.game.raid_roster['b']['hp'],0)
        self.assertEqual(self.gil(),2900)

    def test_ko_actor_cannot_use(self):
        self.begin();self.damage();self.game.raid_roster['a']['hp']=0
        self.assertFalse(self.game.heal_party('a',1).ok)
        self.assertEqual(self.gil(),3000)

    def test_failed_checkpoint_rolls_back_charge_and_raid_state(self):
        self.begin();self.damage()
        hp=self.game.raid_roster['a']['hp']
        with patch.object(self.game,'_persist_runtime_state',side_effect=RuntimeError('raid checkpoint failure')):
            with self.assertRaisesRegex(RuntimeError,'raid checkpoint failure'):
                self.game.heal_party('a',1)
        self.assertEqual(self.gil(),3000)
        self.assertFalse(self.receipts())
        self.assertEqual(self.game.raid_roster['a']['hp'],hp)
        self.assertFalse(self.game.raid_roster['a'].get('mist_heal_used'))

    def test_new_raid_and_venture_each_has_own_allowance(self):
        self.begin(with_ally=False);self.damage()
        self.assertTrue(self.game.heal_party('a',1).ok)
        self.game._finish_raid(False,reason='first raid over')
        self.begin(with_ally=False);self.damage()
        self.assertTrue(self.game.heal_party('a',1).ok)
        self.game._finish_raid(False,reason='second raid over')
        start=self.game.venture('a',bypass_cooldown=True)
        self.assertTrue(start.ok,start.messages)
        self.assertTrue(self.game.start_encounter_battle(start.data['encounter_id']).ok)
        row=self.game.encounter_roster['a'];row['hp']=1
        self.assertTrue(self.game.heal_party('a',1).ok)
        self.assertEqual(len(self.receipts()),3)
        self.assertEqual([r['source'] for r in self.receipts()],['raid_party_heal','raid_party_heal','venture_party_heal'])

    def test_help_and_command_adapter_show_both(self):
        raid_help=' '.join(help_messages('raids'))
        adventure_help=' '.join(help_messages('healparty'))
        self.assertIn('!healparty',raid_help)
        self.assertIn('Raid',adventure_help)
        source=(ROOT/'crystal_guild/twitch_bot.py').read_text()
        self.assertIn('self.game.heal_party(uid, tier)',source)

if __name__=='__main__':unittest.main()

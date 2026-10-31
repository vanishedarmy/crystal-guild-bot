"""Lurk Mode: opt-in, human-led rallies, conservative actions, and persistence."""
import random
import tempfile
import unittest
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]

class LurkModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'lurk.db')
        self.data = GameData(ROOT / 'data')
        self.game = CrystalGuildEngine(self.db, self.data, venture_cooldown_seconds=0,
            raid_join_seconds=90, encounter_join_seconds=90, encounter_round_seconds=90,
            overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'), rng=random.Random(91))
        self.game._roll_seasonal_venture_variant = lambda **kwargs: None
        for pid, job in [('human','warrior'),('lurk','whitemage'),('lurk2','blackmage')]:
            self.assertTrue(self.game.recruit(pid,pid,pid).ok)
            self.assertTrue(self.game.choose_job(pid,job).ok)
        self.assertTrue(self.game.lurk_mode('lurk','on').ok)
        self.assertTrue(self.game.lurk_mode('lurk2','on').ok)

    def tearDown(self):
        self.db.close(); self.tmp.cleanup()

    def test_persistent_setting_and_disable(self):
        self.assertTrue(self.game._lurk_enabled('lurk'))
        restarted = CrystalGuildEngine(self.db, self.data, overlay_state_path=str(Path(self.tmp.name) / 'overlay.json'))
        self.assertTrue(restarted._lurk_enabled('lurk'))
        self.assertTrue(self.game.lurk_mode('lurk','off').ok)
        self.assertFalse(restarted._lurk_enabled('lurk'))
        self.assertFalse(self.game.lurk_mode('lurk','nonsense').ok)
        self.assertTrue(self.game.lurk_mode('lurk','status').ok)

    def test_human_led_venture_autojoin_and_disable_no_exit(self):
        self.assertEqual(len(self.game.encounter_roster), 0)
        self.assertTrue(self.game.venture('human').ok)
        self.assertEqual(set(self.game.encounter_roster), {'human','lurk','lurk2'})
        self.assertTrue(self.game.encounter_roster['lurk'].get('lurk_joined'))
        self.assertTrue(self.game.lurk_mode('lurk','off').ok)
        self.assertIn('lurk',self.game.encounter_roster)
        self.assertFalse(self.game._lurk_enabled('lurk'))

    def test_raid_never_self_starts_and_only_human_join(self):
        self.assertTrue(self.game.spawn_boss('goblin_king').ok)
        self.assertFalse(self.game.raid_roster)
        self.assertTrue(self.game.raid_join('human').ok)
        self.assertEqual(set(self.game.raid_roster), {'human','lurk','lurk2'})
        self.assertTrue(self.game.start_raid().ok)
        self.assertTrue(self.game._lurk_enabled('lurk'))
        self.assertTrue(self.game.battle_defend('lurk').ok)
        action = dict(self.game.raid_roster['lurk']['action'])
        self.game._lurk_automate_round(raid=True,round_no=1)
        self.assertEqual(self.game.raid_roster['lurk']['action'], action)

    def test_no_world_event_auto_join_without_human_and_level_gates(self):
        # Same join gate, but no automatic participation if nobody manually accepts.
        self.game.active_encounter={'kind':'world_event','state':'rally','id':42,'world_event_id':'frostveil_tempest',
                                    'closes_at':9999999999,'monster_id':'behemoth'}
        self.game.encounter_roster={}
        self.game._lurk_fill_rally()
        self.assertEqual(len(self.game.encounter_roster),0)
        # Test the eligibility gate via real join method, not bypassing it.
        self.assertFalse(self.game.join_encounter('human').ok)

    def test_world_event_joins_only_after_a_real_player(self):
        self.game.active_encounter = {
            'kind':'world_event','state':'rally','id':44,
            'world_event_id':'notorious_behemoth', 'closes_at':9999999999,
            'monster_id':'behemoth', 'region_id':'world_event',
        }
        self.game.encounter_roster = {}
        self.game._lurk_fill_rally()
        self.assertFalse(self.game.encounter_roster)
        result = self.game.join_encounter('human')
        self.assertTrue(result.ok, result.messages)
        self.assertEqual(set(self.game.encounter_roster), {'human','lurk','lurk2'})

    def test_portal_toggle_returns_authoritative_state(self):
        before = self.game.portal_adventure_state('lurk')
        self.assertTrue(before.data['adventure_state']['lurk_mode']['enabled'])
        result = self.game.portal_lurk_mode('lurk', False, 'mode-action-off-0001')
        self.assertTrue(result.ok, result.messages)
        self.assertFalse(result.data['adventure_state']['lurk_mode']['enabled'])
        self.assertFalse(self.game._lurk_enabled('lurk'))
        same = self.game.portal_lurk_mode('lurk', False, 'mode-action-off-0001')
        self.assertTrue(same.ok)
        self.assertFalse(self.game._lurk_enabled('lurk'))

    def test_automatic_mist_only_when_party_in_danger_and_wealthy(self):
        self.assertTrue(self.game.spawn_boss('goblin_king').ok)
        self.assertTrue(self.game.raid_join('human').ok)
        self.assertTrue(self.game.start_raid().ok)
        for pid in ('human','lurk','lurk2'):
            self.db.execute('UPDATE players SET gil=20000 WHERE twitch_id=?', (pid,))
        before_gil = int(self.game._player('lurk')['gil'])
        self.game._lurk_automate_round(raid=True, round_no=1)
        self.assertEqual(int(self.game._player('lurk')['gil']), before_gil)
        # Ensure a group emergency can trigger one and only one automatic Mist.
        for meta in self.game.raid_roster.values():
            meta['hp'] = max(1, int(meta['max_hp']) // 5)
        self.game._lurk_automate_round(raid=True, round_no=1)
        self.assertTrue(self.game.active_boss.get('lurk_mist_used'))
        spent = before_gil - int(self.game._player('lurk')['gil'])
        self.assertEqual(spent, 500)
        self.game._lurk_automate_round(raid=True, round_no=2)
        self.assertEqual(int(self.game._player('lurk')['gil']), before_gil - spent)
        self.assertTrue(self.game.raid_roster['lurk'].get('mist_heal_used'))

    def test_healer_uses_a_low_cost_spell_when_ally_is_critical(self):
        self.assertTrue(self.game.venture('human').ok)
        self.assertTrue(self.game.start_encounter_battle().ok)
        mage = self.game.encounter_roster['lurk']
        ally = self.game.encounter_roster['human']
        ally['hp'] = max(1, ally['max_hp'] // 4)
        mage['mp'] = mage['max_mp'] = 150
        mage['hp'] = mage['max_hp']
        choice = self.game._lurk_plan_action('lurk', mage, self.game.encounter_roster, raid=False, round_no=3)
        self.assertEqual(choice['kind'], 'ability', choice)
        self.assertEqual(choice['target_id'], 'human', choice)
        self.assertGreaterEqual(mage['mp'] - choice['cost'], mage['max_mp'] * .35)

    def test_conservative_action_reserves_resources_and_items(self):
        self.assertTrue(self.game.venture('human').ok)
        self.assertTrue(self.game.start_encounter_battle().ok)
        meta=self.game.encounter_roster['lurk']
        meta['hp']=meta['max_hp']
        meta['mp']=0
        meta['ap']=0
        a=self.game._lurk_plan_action('lurk',meta,self.game.encounter_roster,raid=False,round_no=3)
        self.assertEqual(a['kind'],'attack')
        meta['hp']=max(1,meta['max_hp']//10)
        a=self.game._lurk_plan_action('lurk',meta,self.game.encounter_roster,raid=False,round_no=4)
        self.assertIn(a['kind'], {'defend','item'})  # may spend stocked emergency Potion
        self.assertFalse(self.game._lurk_enabled('human'))

if __name__ == '__main__':
    unittest.main()

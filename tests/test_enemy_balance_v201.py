"""V2.0.1 multi-axis encounter balance tests; deterministic and no live accounts."""
from __future__ import annotations

import copy
import random
import tempfile
import unittest
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.encounter_balance import (
    raid_incoming_damage, raid_outgoing_pressure,
    world_event_behavior, world_event_pressure,
)
from crystal_guild.world_events import WORLD_EVENTS, WORLD_EVENTS_BY_ID

ROOT = Path(__file__).resolve().parents[1]


class BossProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = GameData(ROOT / "data")

    def test_complete_raid_profiles_are_bounded(self):
        self.assertEqual(len(self.data.bosses), 38)
        for boss in self.data.bosses.values():
            self.assertTrue(0.80 <= boss["balance_attack_weight"] <= 1.25, boss["id"])
            self.assertTrue(0.65 <= boss["balance_aoe_weight"] <= 1.20, boss["id"])
            self.assertTrue(0 <= boss["balance_guard"] <= 0.22, boss["id"])
            self.assertTrue(3 <= boss["aoe_every"] <= 4, boss["id"])
            self.assertTrue(10 <= boss["enrage_round"] <= 20, boss["id"])
        self.assertNotEqual(self.data.bosses['tonberry_king']['balance_attack_weight'],
                            self.data.bosses['atomos']['balance_attack_weight'])

    def test_boss_armor_penalizes_early_not_last_stand(self):
        b = copy.deepcopy(self.data.bosses['long_gui'])
        b.update(max_hp=10000, current_hp=8500)
        early = raid_incoming_damage(b, 1000)
        b['current_hp'] = 2000
        late = raid_incoming_damage(b, 1000)
        self.assertLess(early, late)
        self.assertLessEqual(late, 1000)
        self.assertEqual(raid_incoming_damage(b, 0), 0)

    def test_incoming_no_guard_for_legacy_boss(self):
        self.assertEqual(raid_incoming_damage({'max_hp': 100, 'current_hp': 100}, 1000),1000)

    def test_aoe_and_single_target_threat_are_distinct(self):
        tank=self.data.bosses['long_gui']
        self.assertLess(raid_outgoing_pressure(tank,raidwide=True),
                        raid_outgoing_pressure(tank,raidwide=False))
        caster=self.data.bosses['ozma']
        self.assertGreater(raid_outgoing_pressure(caster,raidwide=True),
                           raid_outgoing_pressure(caster,raidwide=False))

    def test_signature_control_is_soft_and_only_for_unscripted_bosses(self):
        legal={'weaken','slow','vulnerable'}
        for boss in self.data.bosses.values():
            if boss.get('raid_script'):
                self.assertNotIn('balance_signature_status',boss)
            else:
                self.assertIn(boss.get('balance_signature_status'),legal)
                self.assertTrue(0<boss['balance_signature_chance']<0.2)

    def test_monster_ids_and_rewards_untouched_vs_previous_stable_identities(self):
        monsters=self.data.monsters
        self.assertEqual(len(monsters),126)
        self.assertEqual(monsters['cactuar']['hp'],95)
        self.assertEqual(monsters['dominion_sentinel']['attack'],193)
        self.assertEqual(monsters['tempest_roc']['attack'],167)
        self.assertEqual(monsters['emberglass_wyrm']['attack'],314)


class WorldEventProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=GameData(ROOT/'data')

    def test_all_13_world_events_have_meaningful_combat_profiles(self):
        self.assertEqual(len(WORLD_EVENTS),13)
        for event in WORLD_EVENTS:
            for key in ('combat_pressure','special_frequency','special_power','status_frequency','physical_armor','magic_armor'):
                self.assertGreater(float(event[key]),0)
            self.assertTrue(0.80 <= event['combat_pressure'] <= 1.25)
        self.assertNotEqual(WORLD_EVENTS_BY_ID['elder_adamantoise']['physical_armor'],
                            WORLD_EVENTS_BY_ID['savage_coeurl']['physical_armor'])

    def test_event_action_is_copy_never_mutate_default_monster(self):
        base=self.data.enemy_actions['malboro']
        original=copy.deepcopy(base)
        tuned=world_event_behavior(base,WORLD_EVENTS_BY_ID['tainted_malboro'],4)
        self.assertEqual(base,original)
        self.assertIsNot(tuned,base)
        self.assertNotEqual(tuned['ability']['chance'],base['ability']['chance'])
        self.assertNotEqual(tuned['ability']['power'],base['ability']['power'])

    def test_aoe_safety_for_large_stream_roster(self):
        base=self.data.enemy_actions['behemoth']
        event=WORLD_EVENTS_BY_ID['notorious_behemoth']
        small=world_event_behavior(base,event,4)['ability']['power']
        crowded=world_event_behavior(base,event,20)['ability']['power']
        self.assertGreater(small,crowded)
        self.assertGreater(crowded,0)
        self.assertEqual(base['ability']['target'],'party')

    def test_no_event_mass_hard_disable(self):
        for event in WORLD_EVENTS:
            base=self.data.enemy_actions[event['base_monster_id']]
            ability=world_event_behavior(base,event,20).get('ability',{})
            for effect in ability.get('effects',[]):
                if effect.get('type')=='status' and effect.get('status') in {'stun','silence'}:
                    self.assertLessEqual(effect['chance'],0.22)

    def test_event_soft_enrage_bounded(self):
        for event in WORLD_EVENTS:
            first=world_event_pressure(event,round_no=1)
            later=world_event_pressure(event,round_no=30)
            self.assertGreaterEqual(later,first)
            self.assertLessEqual(later,first*1.301)
            start=16 if event.get('tier')=='elite' else 12
            self.assertEqual(world_event_pressure(event,round_no=start),first)
            self.assertGreater(world_event_pressure(event,round_no=start+1),first)


class EncounterIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Database(Path(self.tmp.name)/'v201.db')
        self.game=CrystalGuildEngine(self.db,GameData(ROOT/'data'),rng=random.Random(301),
                                     overlay_state_path=str(Path(self.tmp.name)/'overlay.json'))
        for n in (1,2,3,4):
            pid=str(n)
            self.assertTrue(self.game.recruit(pid,'cg'+pid,'CG'+pid).ok)
            self.assertTrue(self.game.choose_job(pid,'warrior').ok)
            self.db.execute('UPDATE players SET level=95 WHERE twitch_id=?',(pid,))
            self.game._save_hp(pid,self.game._max_hp(self.game._player(pid)))
    def tearDown(self):
        self.db.close();self.tmp.cleanup()

    def test_armored_boss_takes_reduced_raw_damage(self):
        self.assertTrue(self.game.spawn_boss('long gui').ok)
        for n in (1,2,3,4): self.assertTrue(self.game.raid_join(str(n)).ok)
        self.assertTrue(self.game.start_raid().ok)
        boss=self.game.active_boss
        starting=boss['current_hp']
        dealt,_=self.game._raid_apply_enemy_damage(1000)
        self.assertEqual(dealt,raid_incoming_damage({'max_hp':starting,'current_hp':starting,'balance_guard':boss['balance_guard']},1000))
        self.assertEqual(starting-boss['current_hp'],dealt)

    def test_raid_signature_can_apply_soft_debuff(self):
        self.assertTrue(self.game.spawn_boss('goblin king').ok)
        for n in (1,2,3,4): self.assertTrue(self.game.raid_join(str(n)).ok)
        self.assertTrue(self.game.start_raid().ok)
        boss=self.game.active_boss
        boss['current_hp']=999999
        boss['max_hp']=999999
        boss['aoe_every']=1
        boss['balance_signature_chance']=1.0
        out=self.game.raid_round()
        self.assertTrue(out.ok,out.messages)
        self.assertTrue(any('signature afflicts' in line for line in out.messages),out.messages)
        self.assertTrue(any('weaken' in meta.get('statuses',{}) for meta in self.game.raid_roster.values()))
        self.assertFalse(any('stun' in meta.get('statuses',{}) for meta in self.game.raid_roster.values()))

    def test_scaled_event_monster_uses_identity_armor_not_base_mutation(self):
        event=WORLD_EVENTS_BY_ID['elder_adamantoise']
        base=copy.deepcopy(self.game.data.monsters[event['base_monster_id']])
        scaled=self.game._scaled_world_event_monster(event)
        self.assertGreater(scaled['defense'],int(base['defense']*.75))
        self.assertEqual(self.game.data.monsters[event['base_monster_id']],base)
        self.assertEqual(scaled['name'],'Elder Adamantoise')

    def test_existing_rewards_and_live_only_event_rules_unchanged(self):
        self.assertFalse(self.game.maybe_spawn_world_event(stream_live=False,force=True).data.get('world_event_spawned'))
        self.assertEqual(self.game.data.validate(),[])


if __name__=='__main__':
    unittest.main()

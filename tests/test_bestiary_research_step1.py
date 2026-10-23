"""Step 1: canonical Bestiary overlay is complete without changing combat data."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from crystal_guild.bestiary_research import validate_research_overlay
from crystal_guild.data import GameData

DATA = Path(__file__).resolve().parents[1] / 'data'


class BestiaryResearchStep1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = GameData(DATA)
        cls.overlay = cls.game.bestiary_research

    def validate(self, overlay):
        return validate_research_overlay(
            overlay,
            monsters=self.game.monsters,
            regions=self.game.regions,
            expeditions=self.game.expedition_regions,
            hunts=self.game.hunts,
        )

    def test_catalog_validates_with_all_existing_game_data(self):
        self.assertEqual(self.validate(self.overlay), [])
        self.assertEqual(self.game.validate(), [])
        self.assertEqual(set(self.overlay['entries']), set(self.game.monsters))

    def test_roster_exactly_matches_three_gameplay_domains(self):
        from collections import Counter
        counts = Counter(row['category'] for row in self.overlay['entries'].values())
        self.assertEqual(dict(counts), {'regional': 92, 'hunt': 17, 'expedition': 11})
        self.assertEqual(self.overlay['entries']['rift_dragon']['category'], 'hunt')
        self.assertEqual(self.overlay['entries']['elder_ochu']['category'], 'expedition')

    def test_every_entry_has_lore_and_family(self):
        families = self.overlay['families']
        self.assertTrue(all(entry['family'] in families and len(entry['lore']) > 19
                            for entry in self.overlay['entries'].values()))
        self.assertTrue(all(any(entry['family'] == family for entry in self.overlay['entries'].values())
                            for family in families))

    def test_mastery_requires_20_5_or_3_wins(self):
        stages = self.overlay['tiers']
        for category, expected in [('regional', (1, 3, 5, 10, 15, 20)),
                                   ('hunt', (1, 2, 3, 5)),
                                   ('expedition', (1, 2, 3))]:
            with self.subTest(category=category):
                self.assertEqual(tuple(x['defeats'] for x in stages[category]['milestones']), expected)
                self.assertEqual(stages[category]['milestones'][-1]['reveal'], ['mastery'])

    def test_no_gameplay_values_are_duplicated_or_modified(self):
        before = (DATA / 'monsters.json').read_bytes()
        for row in self.overlay['entries'].values():
            self.assertFalse({'weakness', 'resistance', 'resistances', 'drops', 'level', 'name'} & set(row))
        self.assertEqual(before, (DATA / 'monsters.json').read_bytes())
        self.assertFalse(self.overlay['rewards']['material_drop_bonus_enabled'])

    def test_all_regional_habitats_are_actual_encounter_regions(self):
        for id, entry in self.overlay['entries'].items():
            if entry['category'] != 'regional':
                continue
            actual = {region_id for region_id, region in self.game.regions.items()
                      if any(x.get('monster_id') == id for x in region['encounters'])}
            self.assertEqual(set(entry['habitats']), actual, id)
            self.assertEqual(entry['habitat_provenance'], 'region_encounters')

    def test_hunt_habitats_are_editorial_not_spawn_claims(self):
        hunts = [entry for entry in self.overlay['entries'].values() if entry['category'] == 'hunt']
        self.assertEqual(len(hunts), 17)
        for entry in hunts:
            self.assertEqual(entry['habitat_provenance'], 'guild_survey')
            self.assertTrue(set(entry['habitats']) <= set(self.game.regions))

    def test_missing_monster_fails_closed(self):
        changed = copy.deepcopy(self.overlay)
        del changed['entries']['goblin']
        self.assertTrue(any('missing entries' in e for e in self.validate(changed)))

    def test_category_drift_fails_closed(self):
        changed = copy.deepcopy(self.overlay)
        changed['entries']['goblin']['category'] = 'hunt'
        self.assertTrue(any('expected regional' in e for e in self.validate(changed)))

    def test_region_drift_fails_closed(self):
        changed = copy.deepcopy(self.overlay)
        changed['entries']['goblin']['habitats'] = ['sable_coast']
        self.assertTrue(any('region habitat drift' in e for e in self.validate(changed)))

    def test_combat_value_duplication_fails_closed(self):
        changed = copy.deepcopy(self.overlay)
        changed['entries']['goblin']['weakness'] = 'Ice'
        self.assertTrue(any('duplicated gameplay fields' in e for e in self.validate(changed)))

    def test_hunt_provenance_fails_closed(self):
        changed = copy.deepcopy(self.overlay)
        changed['entries']['goblin_chieftain']['habitat_provenance'] = 'region_encounters'
        self.assertTrue(any('Hunt habitats must be marked guild_survey' in e
                            for e in self.validate(changed)))

    def test_unknown_resistance_is_not_offered(self):
        reveals = [field for tier in self.overlay['tiers'].values()
                   for milestone in tier['milestones'] for field in milestone['reveal']]
        self.assertNotIn('resistance', reveals)
        self.assertNotIn('resistances', reveals)


if __name__ == '__main__':
    unittest.main()

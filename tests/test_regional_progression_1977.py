"""v1.9.97.7: world-region and Classic Relic material regression tests."""
import json, unittest, tempfile, random
from pathlib import Path
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.emporium import REGIONAL_SHOPS, eligible_stock

ROOT = Path(__file__).resolve().parents[1]

class RegionalProgression1977Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=GameData(ROOT/'data')

    def test_catalog_is_valid(self):
        self.assertEqual(self.data.validate(), [])

    def test_level_bands_and_legacy_identifiers(self):
        regions=sorted(self.data.regions.values(), key=lambda r:r['min_level'])
        self.assertEqual([r['min_level'] for r in regions], [1,10,20,30,40,50,60,70,80,90,99])
        self.assertIn('shattered_frontier',self.data.regions)
        self.assertIn('astral_threshold',self.data.regions)
        self.assertEqual(regions[5]['id'],'riftlands')
        self.assertEqual(regions[7]['id'],'interdimensional_rift')

    def test_habitat_alignment_and_level_appropriate_encounters(self):
        entries=self.data.bestiary_research['entries']
        for r in self.data.regions.values():
            lower=r['min_level'];upper=r['recommended_max_level']
            for e in r['encounters']:
                level=self.data.monsters[e['monster_id']]['level']
                self.assertTrue((lower<=level<=upper) or (lower==99 and 96<=level<=103), (r['id'],e['monster_id'],level))
                v=entries[e['monster_id']]
                if v['habitat_provenance']=='region_encounters':
                    self.assertIn(r['id'],v['habitats'])

    def test_materials_available_at_classic_relic_levels(self):
        for material, cap in [('crystal_core',49),('eidolon_shard',69)]:
            candidates=[(r['id'],self.data.monsters[e['monster_id']]['level']) for r in self.data.regions.values() for e in r['encounters'] if self.data.monsters[e['monster_id']]['level']<=cap and any(d['item_id']==material for d in self.data.monsters[e['monster_id']].get('drops',[]))]
            self.assertTrue(candidates,(material,cap))
        for r in self.data.relics.values():
            if r.get('tier')=='classic':
                self.assertIn('crystal_core',{c['item_id'] for c in r['stages'][1]['cost']['items']})
                self.assertIn('eidolon_shard',{c['item_id'] for c in r['stages'][2]['cost']['items']})

    def test_legacy_saved_region_no_longer_allows_underlevel_farming(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Database(Path(folder)/"guild.db")
            try:
                game=CrystalGuildEngine(db, self.data, rng=random.Random(17), overlay_state_path=str(Path(folder)/"overlay.json"))
                self.assertTrue(game.recruit('saved','saved','Saved').ok)
                db.execute("UPDATE players SET current_job='warrior',level=97,current_hp=100,current_region='eclipsed_singularity_citadel' WHERE twitch_id='saved'")
                self.assertFalse(game.venture('saved').ok)
                self.assertFalse(game.solo_venture('saved').ok)
                self.assertTrue(game.travel('saved','omega_ruins').ok)
            finally: db.close()

    def test_shops_cover_each_region_without_free_relics(self):
        self.assertEqual(set(REGIONAL_SHOPS),set(self.data.regions))
        for rid, row in REGIONAL_SHOPS.items():
            self.assertLessEqual(row[1],row[2])
        player={'level':99,'current_job':'paladin'}
        for rid, row in REGIONAL_SHOPS.items():
            context={'stock_level_cap':row[2], 'gear_floor':row[1]}
            stock=eligible_stock(player,self.data.items,context)
            self.assertFalse(any(x.get('relic_id') or x.get('unsellable') for x in stock))

if __name__=='__main__': unittest.main()

"""v1.9.10 expansion: equipment coverage and Ultimate Relic progression."""
import tempfile
from pathlib import Path
from collections import Counter

import pytest
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.player_snapshot import PortalRepository

DATA=Path(__file__).resolve().parents[1]/'data'

@pytest.fixture
def setup():
    temp=tempfile.TemporaryDirectory()
    db=Database(Path(temp.name)/'test.db')
    data=GameData(DATA)
    engine=CrystalGuildEngine(db,data)
    repo=PortalRepository(Path(temp.name)/'test.db',DATA)
    assert engine.recruit('100','endgamehero','Endgame Hero').ok
    assert engine.choose_job('100','warrior').ok
    yield db,data,engine,repo
    repo.close();db.close();temp.cleanup()


def set_player(db,level):
    db.execute("UPDATE players SET level=?,gil=1000000,hunt_seals=10000,current_region=? WHERE twitch_id='100'",(level,'interdimensional_rift' if level < 82 else 'omega_ruins'))
    db.execute("UPDATE player_jobs SET level=50 WHERE player_id='100' AND job_id='warrior'")


def stock_materials(db,entries):
    for mat in entries:
        db.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES ('100',?,?) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=excluded.quantity",(mat['item_id'],max(5,mat['quantity'])))


def test_equip_tiers_every_job_and_recipe_integrity(setup):
    _,data,_,_=setup
    assert data.validate()==[]
    assert len(data.relics)==36
    jobs=set(data.jobs)
    for level in (70,75,80,85,90,95,99):
        gear=[v for v in data.items.values() if v.get('introduced_in')=='1.9.10' and v.get('min_level')==level and v['type']!='material' and not v.get('relic_id')]
        assert len(gear)==17
        assert {v['type'] for v in gear}=={'weapon','armor','accessory'}
        for job in jobs:
            assert any(x['type']=='weapon' and job in x.get('allowed_jobs',[]) for x in gear), (level,job)
            assert any(x['type']=='armor' and job in x.get('allowed_jobs',[]) for x in gear), (level,job)
    assert all(len(r['stages'])==3 for r in data.relics.values())
    for job in jobs:
        ultimate=data.relics['ultimate_'+job]
        assert ultimate['tier']=='ultimate'
        assert [data.items[s['reward_item']]['min_level'] for s in ultimate['stages']]==[90,95,99]
        assert ultimate['stages'][0]['requirements'][2]['type']=='relic_complete'
        for s in ultimate['stages']:
            assert data.items[s['reward_item']]['allowed_jobs']==[job]
            assert not data.items[s['reward_item']]['shop']


def test_shop_upgrade_at_level_70_and_no_premature_equipping(setup):
    db,data,engine,_=setup
    set_player(db,70)
    stock=engine._roll_shop_stock(engine._player('100'))
    options=[data.items[item] for item in stock if data.items[item]['type']=='weapon']
    assert any(x.get('min_level',1)==70 for x in options)
    assert not any(x.get('min_level',1)>70 for x in options)
    purchase=engine.quick_buy_gear('100','weapon')
    assert purchase.ok, purchase.messages
    current=db.one("SELECT weapon_id FROM equipment WHERE player_id='100'")['weapon_id']
    assert data.items[current]['min_level']==70
    set_player(db,69)
    high=[item for item in data.items.values() if item.get('min_level')==70 and item['type']=='weapon'][0]
    assert not engine.equip('100',high['id']).ok


def test_ultimate_requires_zenith_and_stage_costs_and_eclipse_boss(setup):
    db,data,engine,repo=setup
    relic=data.relics['ultimate_warrior']
    set_player(db,90)
    stage0=relic['stages'][0]
    stock_materials(db,stage0['cost']['items'])
    denied=engine.awaken_relic('100',relic['name'])
    assert not denied.ok
    assert 'Bravura' in ' '.join(denied.messages)
    before=next(x for x in repo.relics('endgamehero')['relics'] if x['id']==relic['id'])
    assert not before['ready']
    assert any(x['type']=='relic_complete' and not x['met'] for x in before['path'][0]['requirements'])
    db.execute("INSERT INTO player_relics(player_id,relic_id,stage) VALUES ('100','bravura',3)")
    start=next(x for x in repo.relics('endgamehero')['relics'] if x['id']==relic['id'])
    assert start['ready']
    assert engine.awaken_relic('100',relic['name']).ok
    assert data.items[stage0['reward_item']]['min_level']==90
    result=engine.equip('100',stage0['reward_item'])
    assert result.ok, result.messages
    assert db.one("SELECT weapon_id FROM equipment WHERE player_id='100'")['weapon_id']==stage0['reward_item']
    # Stage 2 cannot skip character level or unique S-rank hunts.
    stage1=relic['stages'][1]
    stock_materials(db,stage1['cost']['items'])
    assert not engine.awaken_relic('100',relic['name']).ok
    set_player(db,95)
    s_hunts=[h['id'] for h in data.hunts.values() if h['rank']=='S'][:3]
    for hunt in s_hunts:
        db.execute("INSERT INTO player_hunts(player_id,hunt_id,clears) VALUES ('100',?,1)",(hunt,))
    assert engine.awaken_relic('100',relic['name']).ok
    set_player(db,99)
    stage2=relic['stages'][2]
    stock_materials(db,stage2['cost']['items'])
    last_before=next(x for x in repo.relics('endgamehero')['relics'] if x['id']==relic['id'])
    assert not last_before['ready']
    assert any(x['type']=='boss_clear' and not x['met'] for x in last_before['path'][2]['requirements'])
    db.execute("INSERT INTO player_boss_clears(player_id,boss_id,clears) VALUES ('100','eclipse_sovereign',1)")
    assert engine.awaken_relic('100',relic['name']).ok
    final=next(x for x in repo.relics('endgamehero')['relics'] if x['id']==relic['id'])
    assert final['completed'] and final['tier']=='ultimate' and final['stage']==3
    assert final['final_reward']['min_level']==99


def test_endgame_paragon_crafting_requires_level_and_materials(setup):
    db,data,engine,_=setup
    recipe=data.recipes['endgame_paragon_crystal_sword']
    set_player(db,95)
    stock_materials(db,recipe['materials'])
    denied=engine.craft('100',recipe['id'])
    assert not denied.ok
    set_player(db,99)
    success=engine.craft('100',recipe['id'])
    assert success.ok, success.messages
    row=db.one("SELECT quantity FROM inventory WHERE player_id='100' AND item_id='paragon_crystal_sword'")
    assert row and int(row['quantity'])==1

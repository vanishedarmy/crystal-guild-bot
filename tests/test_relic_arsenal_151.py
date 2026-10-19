import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_every_job_has_exactly_one_relic_line():
    jobs=json.loads((ROOT/'data/jobs.json').read_text())
    relics=json.loads((ROOT/'data/relics.json').read_text())
    assert len(jobs)==18
    assert len(relics)==18
    by_job={}
    for relic in relics:
        by_job.setdefault(relic['job_id'],[]).append(relic)
    assert set(by_job)=={j['id'] for j in jobs}
    assert all(len(rows)==1 for rows in by_job.values())

def test_all_relics_have_three_stage_items_for_own_job():
    relics=json.loads((ROOT/'data/relics.json').read_text())
    items={x['id']:x for x in json.loads((ROOT/'data/items.json').read_text())}
    for relic in relics:
        assert [s['stage'] for s in relic['stages']]==[1,2,3]
        for stage in relic['stages']:
            item=items[stage['reward_item']]
            assert item['relic_id']==relic['id']
            assert item['relic_stage']==stage['stage']
            assert relic['job_id'] in item['allowed_jobs']
            assert item['unsellable'] is True

def test_151_missing_jobs_are_completed():
    relics={x['job_id']:x['id'] for x in json.loads((ROOT/'data/relics.json').read_text())}
    assert relics | {}
    expected={'warrior':'bravura','redmage':'murgleis','ninja':'yoshimitsu','summoner':'veil_of_wiyu','bluemage':'almace','timemage':'chronos','bard':'artemis_bow','machinist':'armageddon','beastmaster':'guttler','sage':'astral_codex'}
    for job,relic in expected.items(): assert relics[job]==relic

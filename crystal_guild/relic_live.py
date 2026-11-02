"""Bounded, server-snapshot Relic and equipment integrations for Crystal Guild.

This adapter never accepts a client-supplied equipment entitlement. Only the
engine's _equipment_traits database snapshot populates relic_trait/signature.
Advanced mechanics without a supported live action hook remain inactive.
"""
from __future__ import annotations

import math
from typing import Any

RELIC_JOB_KEYS = {
    'warrior':'guard_to_strike', 'monk':'combo_momentum', 'thief':'master_pickpocket',
    'blackmage':'overcharge', 'whitemage':'gentle_benediction', 'redmage':'dual_harmony',
    'paladin':'sacred_guard', 'darkknight':'blood_resolve', 'dragoon':'skyward_mastery',
    'ninja':'shadow_step', 'samurai':'perfect_form', 'summoner':'resonance',
    'bluemage':'mimic_insight', 'timemage':'chronal_guard', 'bard':'sustained_melody',
    'machinist':'calibrated_shot', 'beastmaster':'pack_coordination',
    'sage':'measured_wisdom',
}
JUMP_ABILITIES = {'jump','high_jump','stardiver','dragonfire_dive','spineshatter_dive','dragonheart'}
DARK_ABILITIES = {'souleater','unleash','flood_of_darkness','abyssal_drain','quietus',
                  'dark_passenger','salted_earth','shadowbringer','eventide','abyssal_eclipse','living_shadow_prime'}
SUMMON_ABILITIES = {'grand_summon','egi_assault','megaflare','teraflare', 'inferno',
                    'diamond_dust','judgment_bolt','tidal_wave','earthen_fury','aerial_blast'}
# Only actual server-side enemy actions may teach a matching Blue technique.
# These are mastery bonuses and never remove job-level ability unlocks.
ENEMY_BLUE_MEMORIES = {
    '1000_needles': 'thousand_needles',
    'aqua_breath': 'aqua_breath',
    'bad_breath': 'bad_breath',
    'mighty_guard': 'mighty_guard',
}

BLUE_ABILITIES = {'goblin_punch','vampire','bomb_toss','thousand_needles','bad_breath','glower',
                  'aqua_breath','flamethrower','aqua_cannon','night','dragon_breath','matra_magic',
                  'level_5_flare','grand_delta','bad_breath_ii'}


def eligible_relic(item: dict[str, Any], job_id: str) -> bool:
    trait = item.get('relic_trait') or {}
    return (item.get('type') == 'weapon' and item.get('relic_id') and
            item.get('rarity') == 'relic' and
            trait.get('key') == RELIC_JOB_KEYS.get(job_id) and
            (not item.get('allowed_jobs') or job_id in item['allowed_jobs']))


def trait(meta: dict[str, Any], key: str) -> float:
    t = meta.get('relic_trait') or {}
    return float(t.get('value',0)) if t.get('key') == key else 0.0


def signature(meta: dict[str, Any], key: str) -> float:
    s = meta.get('relic_signature') or {}
    return float(s.get('value',0)) if s.get('key') == key else 0.0


def is_dragon(monster: dict[str, Any]) -> bool:
    family = str(monster.get('family') or monster.get('species') or '').lower()
    if family in {'dragon','dragonkin','drake','wyrm'}:
        return True
    name = (str(monster.get('id',''))+' '+str(monster.get('name',''))).lower()
    return any(x in name for x in ('dragon','wyrm','drake','wyvern'))


def relic_resistance(equipped: dict[str, Any], resistance: dict[str,float]) -> dict[str,float]:
    result = dict(resistance)
    if (equipped.get('relic_trait') or {}).get('key') == 'chronal_guard':
        x = float(equipped['relic_trait'].get('value',0))
        result['slow'] = 1 - (1-result.get('slow',0))*(1-x)
    return result


def adjusted_cost(meta: dict[str, Any], base: int, ability_id: str = '') -> int:
    if base <= 0:
        return 0
    discount = 0.0
    if meta.get('accessory_id') == 'sages_emblem':
        discount += 0.05
    if meta.get('job_id') == 'summoner':
        discount += trait(meta,'resonance')
    if meta.get('job_id') == 'sage':
        discount += trait(meta,'measured_wisdom')
    return max(1, math.ceil(base * (1-min(0.40,discount))))


def heal_multiplier(actor: dict[str,Any], target: dict[str,Any]) -> float:
    job = actor.get('job_id')
    m = 1.0
    if job == 'whitemage':
        m += trait(actor,'gentle_benediction')
        if int(target.get('hp',0)) * 2 <= int(target.get('max_hp',1)):
            m *= 1+signature(actor,'lifewave')
    elif job == 'redmage':
        m += trait(actor,'dual_harmony')
    elif job == 'sage' and int(target.get('hp',0))*2 <= int(target.get('max_hp',1)):
        m += signature(actor,'arcane_mercy')
    return min(m,1.75)


def damage_multiplier(meta: dict[str,Any], *, action: str = '', critical: bool = False,
                      element: str | None = None, monster: dict[str,Any] | None = None,
                      statuses: dict | None = None, boss: bool=False) -> float:
    monster = monster or {}
    statuses = statuses or {}
    job = meta.get('job_id')
    val = 1.0
    dragon = is_dragon(monster)
    if dragon and meta.get('weapon_id') == 'dragon_slayer':
        val *= 1.12
    if job == 'dragoon' and action in JUMP_ABILITIES:
        val *= 1 + trait(meta,'skyward_mastery')
        if meta.get('accessory_id') == 'dragoon_boots':
            val *= 1.08
        if dragon:
            val *= 1 + signature(meta,'dragonfall')
    if job == 'warrior' and meta.get('_relic_guard_ready'):
        if trait(meta,'guard_to_strike'):
            val *= 1 + trait(meta,'guard_to_strike')
            meta['_relic_guard_ready'] = False
    if job == 'redmage' and action:
        val *= 1 + trait(meta,'dual_harmony')
    if job == 'blackmage' and action and element:
        if critical:
            val *= 1 + trait(meta,'overcharge')
        if str(monster.get('weakness','')).lower() == str(element).lower():
            val *= 1 + signature(meta,'astral_surge')
    if job == 'darkknight' and action in DARK_ABILITIES and 'vulnerable' in statuses:
        val *= 1 + signature(meta,'doom_harvest')
    if job == 'samurai' and action == 'iaijutsu' and critical:
        val *= 1 + signature(meta,'zanshin')
    if job == 'monk' and action in {'hundred_fists','phantom_rush'} and int(meta.get('_relic_monk_combo_count',0)) == 2:
        val *= 1 + signature(meta,'fiststorm')
    if job == 'summoner' and action in SUMMON_ABILITIES and boss:
        val *= 1 + signature(meta,'grand_convergence')
    if job == 'bluemage' and action in BLUE_ABILITIES:
        if action in meta.get('_blue_memories', ()):
            val *= 1.05  # Studied enemy technique, not an unearned generic buff.
        val *= 1 + signature(meta,'adaptive_memory')
    if job == 'timemage' and action and 'slow' in statuses:
        val *= 1 + signature(meta,'fate_unbound')
    if job == 'beastmaster' and action in {'call_beast','king_of_beasts'}:
        # The engine supplies this snapshot from the persisted owned/selected
        # roster, never from an untrusted Twitch action payload.
        pet = meta.get('_tamed_companion')
        if isinstance(pet, dict) and pet.get('monster_id'):
            from .beastmaster import pet_damage_bonus
            val *= 1 + pet_damage_bonus(pet)
            val *= 1 + trait(meta,'pack_coordination')
            if boss:
                val *= 1 + signature(meta,'alpha_pact')
    return min(val,2.5)


def bonus_crit(meta: dict[str,Any], action: str) -> float:
    if meta.get('job_id') == 'samurai' and action == 'iaijutsu':
        return trait(meta,'perfect_form')
    return 0.0


def artisan_salvage_candidates(recipe: dict[str, Any], items: dict[str, dict[str, Any]]) -> list[str]:
    """Material-only inputs safe for the 5% Artisan's Hammer salvage roll.

    Epic/Legendary/Unique/Exotic quest inputs are excluded to avoid bypassing
    the game's endgame material economy. Never return an equipment output.
    """
    allowed = {"common", "uncommon", "rare"}
    return sorted({str(entry.get("item_id") or "")
        for entry in recipe.get("materials", [])
        if (items.get(str(entry.get("item_id") or ""), {}).get("type") == "material"
            and str(items[str(entry["item_id"])].get("rarity") or "").lower() in allowed)})


def monk_combo_hit(meta: dict[str,Any], damage: int) -> int:
    """Track three actual damaging Monk hits; restore AP on the third only.

    No bonus is granted for empty, missed, or unrelated-job actions. The
    encounter-local counter is never supplied by Twitch client commands.
    """
    if meta.get('job_id') != 'monk' or trait(meta, 'combo_momentum') <= 0:
        return 0
    if int(damage) <= 0:
        meta['_relic_monk_combo_count'] = 0
        return 0
    count = int(meta.get('_relic_monk_combo_count', 0)) + 1
    if count < 3:
        meta['_relic_monk_combo_count'] = count
        return 0
    meta['_relic_monk_combo_count'] = 0
    maximum = max(0, int(meta.get('max_ap', 0)))
    before = max(0, min(maximum, int(meta.get('ap', 0))))
    restored = min(maximum-before, max(0, int(trait(meta, 'combo_momentum'))))
    meta['ap'] = before + restored
    return restored


def relic_guard_hit(meta: dict[str,Any], damage: int) -> int:
    """Consume a Paladin's earned Sacred Guard on a landed direct hit.

    Only a surviving defender receives an Aegis Reprisal charge.
    """
    damage = max(0,int(damage))
    if damage <= 0 or meta.get('job_id') != 'paladin':
        return damage
    guard = max(0.0,min(0.40,float(meta.pop('_relic_cover_guard_ready',0.0) or 0.0)))
    if not guard:
        return damage
    reduced = max(1,int(damage * (1.0 - guard)))
    if int(meta.get('hp',0)) > reduced and signature(meta,'aegis_reprisal') > 0:
        meta['_relic_reprisal_ready'] = True
    return reduced

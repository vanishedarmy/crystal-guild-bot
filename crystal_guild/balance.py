"""Shared numeric rules for progression, economy, combat resources, Hunts, and raids.

Keep content-specific numbers in JSON and cross-cutting formulas/safety limits here.
"""

from __future__ import annotations

import math


# ---------------------------------------------------------------------------
# Character progression
# ---------------------------------------------------------------------------
XP_BASE = 75
XP_EXPONENT = 1.55
JP_BASE = 35
JP_EXPONENT = 1.35

ENCOUNTER_REWARD_MIN = 0.05
ENCOUNTER_REWARD_MAX = 1.50

# Rally Ventures are Twitch-live, higher-risk encounters. A victory against an
# enemy above a hero's level earns an additional XP/JP/Gil danger bonus of 5%
# per level, capped at +50% at the regular Venture +10 enemy ceiling. Solo
# Venture and Hunts do not use this bonus.
RALLY_VENTURE_REWARD_PER_LEVEL = 0.05
RALLY_VENTURE_REWARD_MAX_BONUS = 0.50

# Progression/economy guardrails. Character XP uses the established level factor.
# JP uses a catch-up floor based on Character
# Level so switching to a fresh Job at high level is viable without turning a
# Lv.1 Job into an unrestricted endgame power-level exploit.
JP_CATCHUP_CHARACTER_FLOOR = 0.35

# Passive income should help a viewer return to play, not replace adventuring.
# Daily provisions scale gently with level and remain below a typical
# level-appropriate combat payout through most of progression.
DAILY_GIL_BASE = 125
DAILY_GIL_PER_LEVEL = 8
DAILY_GIL_VARIANCE = 0.12
DAILY_GIL_CAP = 1000

# Selling is a recovery valve, not a second reward multiplier. Materials retain
# the strongest resale value because they are the Guild's trade goods; finished
# supplies lose more value, which also prevents craft->sell loops.
MATERIAL_SELL_RATIO = 0.70
GEAR_SELL_RATIO = 0.50
CONSUMABLE_SELL_RATIO = 0.40
DEFAULT_SELL_RATIO = 0.50

# Repeat Hunts remain the best repeatable source of Hunt Seals, but their
# general-purpose XP/JP/gil emission eases after the first clear.
HUNT_REPEAT_PROGRESSION_MULTIPLIER = 0.85
HUNT_REPEAT_GIL_MULTIPLIER = 0.80

# Raid rewards are budgeted so larger raid groups do not multiply boss XP
# before contribution, causing total XP issuance to grow linearly with roster
# size. One bounded pool blends participation with
# contribution so tanks/healers still count without multiplying the economy.
RAID_XP_POOL_MULTIPLIER = 1.35
RAID_GIL_POOL_MULTIPLIER = 1.00
RAID_PARTICIPATION_WEIGHT = 0.25


# ---------------------------------------------------------------------------
# Shared encounter pressure
# ---------------------------------------------------------------------------
PARTY_HP_PER_EXTRA_HERO = 0.62
# Soft targeting: ordinary Venture/Hunt enemy responses resolve exactly one
# action per round. Named enemy abilities can still explicitly target the party.
ENEMY_ACTIONS_PER_ROUND = 1
# A random Venture may roll at most this many levels above the initiating hero.
VENTURE_MAX_LEVEL_ABOVE_PLAYER = 10

# Random encounter variety guardrails. Region data still defines the base rarity
# curve; these constants only prevent a narrow level band or an unlucky RNG
# streak from making one monster dominate repeated Ventures.
RANDOM_ENCOUNTER_MIN_VARIETY = 5
RANDOM_ENCOUNTER_RECENT_WINDOW = 5
RANDOM_ENCOUNTER_REPEAT_WEIGHT = 0.10
RANDOM_ENCOUNTER_RECENT_WEIGHT = 0.65
RANDOM_ENCOUNTER_HARD_REPEAT_LIMIT = 2
RANDOM_ENCOUNTER_MAX_WEIGHT_SHARE = 0.45

# Portal-only Solo Venture remains lower-risk and more frequent than the shared
# rally Venture. It has its own cooldown and a 50/50 encounter/treasure split.
# Regular Venture accepts substantially higher encounter risk for live-stream
# rally play, while Solo Venture keeps its tighter +5 enemy ceiling.
SOLO_VENTURE_MAX_LEVEL_ABOVE_PLAYER = 5
SOLO_VENTURE_COOLDOWN_SECONDS = 7 * 60
SOLO_VENTURE_TREASURE_CHANCE = 0.20
SOLO_VENTURE_FELLOWSHIP_RENOWN = 4
SOLO_EXPEDITION_MAX_STAGES = 3
SOLO_EXPEDITION_STAGE_BONUS = 0.15
SOLO_EXPEDITION_DEFEAT_GIL_KEEP = 0.50

# Ventures are now event-driven rather than guaranteed combat. Combat remains
# the primary result, but treasure discoveries are common enough to make
# exploration feel meaningfully different from simply opening a battle.
VENTURE_TREASURE_CHANCE = 0.0

# Treasure is level-aware. A chest may contain a slightly aspirational item,
# but it should never hand a low-level player an endgame reward or waste a roll
# on starter trash far below their current progression band.
VENTURE_TREASURE_LEVEL_BELOW_PLAYER = 5
VENTURE_TREASURE_LEVEL_ABOVE_PLAYER = 2

# Category weights are evaluated only across categories that actually have an
# eligible item in the current level band. Materials are intentionally omitted:
# Venture chests are for immediately useful equipment/supplies, while monster
# drops, crafting, Hunts, and other systems remain the primary material sources.
VENTURE_TREASURE_CATEGORY_WEIGHTS = {
    "consumable": 40,
    "armor": 25,
    "weapon": 20,
    "accessory": 15,
}

# Rare equipment may appear in a chest, but the category roll must not turn
# every treasure event into an artifact dispenser. Relic quest weapons are
# excluded separately in the engine so this weighting cannot bypass progression.
VENTURE_TREASURE_RARITY_WEIGHTS = {
    "common": 100,
    "uncommon": 55,
    "rare": 20,
    "epic": 7,
    "relic": 2,
    "artifact": 0.5,
    "legendary": 0.1,
}
MAX_CRIT_CHANCE = 0.45


# ---------------------------------------------------------------------------
# Active Battle resource economy
# ---------------------------------------------------------------------------
# MP/AP are persistent adventure resources. The early-game pool is deliberately
# tight so Lv.1 abilities are choices rather than effectively free actions, while
# square-root stat growth still gives veteran Jobs a larger tactical reserve.
# A typical Lv.1 caster lands around 16-17 MP and a Lv.50 caster around 42-50 MP
# before equipment/mastery modifiers.
BATTLE_MP_BASE = 3
BATTLE_MP_STAT_SCALE = 2.8
BATTLE_MP_MIN = 15
BATTLE_MP_MAX = 75

# Physical AP follows the same philosophy, with a slightly flatter curve because
# most martial techniques cost a little less than the strongest spells.
BATTLE_AP_BASE = 4
BATTLE_AP_STAT_SCALE = 2.6
BATTLE_AP_MIN = 15
BATTLE_AP_MAX = 70

# Defend remains a pressure-valve inside battle, not a full refill loop. At low
# level it usually returns one point; larger pools recover modestly more.
DEFEND_MP_RESTORE_FRACTION = 0.06
DEFEND_AP_RESTORE_FRACTION = 0.08

# Hard control is disproportionately strong in Crystal Guild because normal
# Active Battles have one enemy. A successful Stun therefore grants one full
# follow-up round of resistance so parties cannot permanently lock a monster.
STUN_RESIST_ROUNDS_AFTER_SUCCESS = 1

# Hunt marks gradually resist player-applied debuffs while retaining the same
# player ability vocabulary. This is chance scaling, not blanket immunity.
HUNT_STATUS_CHANCE_MULTIPLIERS = {"C": 1.00, "B": 0.96, "A": 0.92, "S": 0.88, "S+": 0.84, "SS": 0.80}
HUNT_STUN_CHANCE_MULTIPLIERS = {"C": 0.90, "B": 0.82, "A": 0.74, "S": 0.66, "S+": 0.58, "SS": 0.54}


# ---------------------------------------------------------------------------
# Raid contribution
# ---------------------------------------------------------------------------
RAID_HEAL_WEIGHT = 0.70
RAID_MITIGATION_WEIGHT = 0.35


# ---------------------------------------------------------------------------
# Active Hunt scaling
# ---------------------------------------------------------------------------
# Hunt monsters already carry bespoke stats in monsters.json; these
# multipliers compensate for the richer active-action system without rewriting
# the Hunt catalog itself.
HUNT_HP_MULTIPLIERS = {"C": 1.00, "B": 1.08, "A": 1.16, "S": 1.24, "S+": 1.30, "SS": 1.38}
HUNT_PRESSURE_MULTIPLIERS = {"C": 1.00, "B": 1.04, "A": 1.08, "S": 1.12, "S+": 1.15, "SS": 1.20}
HUNT_MAX_ROUNDS = {"C": 12, "B": 14, "A": 16, "S": 18, "S+": 20, "SS": 22}


def xp_to_next(level: int) -> int:
    level = max(1, int(level))
    return max(100, round(XP_BASE * (level ** XP_EXPONENT)))


def jp_to_next(level: int) -> int:
    level = max(1, int(level))
    return max(40, round(JP_BASE * (level ** JP_EXPONENT)))


def encounter_reward_factor(player_level: int, monster_level: int) -> float:
    """Reward level-appropriate adventuring and sharply reduce trivial farming."""
    player = max(1, int(player_level))
    enemy = max(1, int(monster_level))
    gap = player - enemy
    # FF-style level bands: nearby foes award their full value, while fights
    # more than 10-25 levels below the adventurer become poor XP/JP farms.
    # Preserve the legacy +50% ceiling for genuinely dangerous encounters.
    if gap <= 0:
        return min(ENCOUNTER_REWARD_MAX, enemy / player)
    if gap <= 3:
        return max(0.85, 1.0 - 0.05 * gap)
    if gap <= 10:
        return 0.85 - (gap - 3) * (0.50 / 7.0)
    if gap <= 20:
        return 0.35 - (gap - 10) * 0.025
    return max(ENCOUNTER_REWARD_MIN, 0.10 - (gap - 20) * 0.005)


def dungeon_repeat_bonus_factor(player_level: int, recommended_level: int) -> float:
    """Scale *repeat* dungeon completion payouts to the current level band.

    First-clears are achievements and keep their full one-time bonus; this
    factor applies only to repeat completion XP/JP/Gil, not crafting materials.
    """
    return encounter_reward_factor(player_level, recommended_level)


def rally_venture_reward_multiplier(player_level: int, monster_level: int) -> float:
    """Return the extra live-Rally reward multiplier for higher-level enemies.

    The bonus is deliberately tied to actual personal risk: equal- or lower-level
    enemies receive no Rally bonus, while each enemy level above the hero adds
    5% XP/JP/Gil up to a +50% cap at the +10 Venture ceiling.
    """
    gap = max(0, int(monster_level) - max(1, int(player_level)))
    bonus = min(RALLY_VENTURE_REWARD_MAX_BONUS, gap * RALLY_VENTURE_REWARD_PER_LEVEL)
    return 1.0 + bonus


def jp_reward_factor(character_level: int, job_level: int, monster_level: int) -> float:
    """Return the JP factor with bounded catch-up for newly changed Jobs."""
    char_level = max(1, int(character_level))
    current_job_level = max(1, int(job_level))
    catchup_floor = max(1, int(math.ceil(char_level * JP_CATCHUP_CHARACTER_FLOOR)))
    effective_level = max(current_job_level, catchup_floor)
    return encounter_reward_factor(effective_level, monster_level)


def daily_gil_range(level: int) -> tuple[int, int]:
    """Return a gentle level-scaled daily provision range."""
    target = min(DAILY_GIL_CAP, DAILY_GIL_BASE + max(1, int(level)) * DAILY_GIL_PER_LEVEL)
    low = max(50, int(round(target * (1 - DAILY_GIL_VARIANCE))))
    high = min(DAILY_GIL_CAP, max(low, int(round(target * (1 + DAILY_GIL_VARIANCE)))))
    return low, high


def sell_value(price: int, item_type: str) -> int:
    """Return one item's bounded Guild resale value."""
    value = max(0, int(price))
    kind = str(item_type).lower()
    if kind == "material":
        ratio = MATERIAL_SELL_RATIO
    elif kind in {"weapon", "armor", "accessory"}:
        ratio = GEAR_SELL_RATIO
    elif kind == "consumable":
        ratio = CONSUMABLE_SELL_RATIO
    else:
        ratio = DEFAULT_SELL_RATIO
    return max(1, int(math.floor(value * ratio))) if value else 0


def hunt_repeat_rewards(xp: int, jp: int, gil: int, *, first_clear: bool) -> tuple[int, int, int]:
    """Scale repeat Hunt progression while preserving first-clear rewards."""
    if first_clear:
        return max(0, int(xp)), max(0, int(jp)), max(0, int(gil))
    return (
        max(1, int(round(int(xp) * HUNT_REPEAT_PROGRESSION_MULTIPLIER))),
        max(1, int(round(int(jp) * HUNT_REPEAT_PROGRESSION_MULTIPLIER))),
        max(1, int(round(int(gil) * HUNT_REPEAT_GIL_MULTIPLIER))),
    )


def raid_reward_allocations(scores: dict[str, float], base_xp: int, base_gil: int) -> dict[str, tuple[int, int]]:
    """Allocate bounded raid XP/gil pools across all participating raiders.

    A small equal-share component rewards participation while the remainder uses
    the existing damage/healing/mitigation contribution score. Integer remainder
    is assigned deterministically by contribution so the emitted totals never
    exceed the configured pools and do not grow with roster size.
    """
    if not scores:
        return {}
    ids = list(scores)
    n = len(ids)
    positive = {pid: max(0.0, float(scores[pid])) for pid in ids}
    total = sum(positive.values())
    if total <= 0:
        contribution = {pid: 1.0 / n for pid in ids}
    else:
        contribution = {pid: positive[pid] / total for pid in ids}
    equal = 1.0 / n
    weights = {
        pid: RAID_PARTICIPATION_WEIGHT * equal + (1.0 - RAID_PARTICIPATION_WEIGHT) * contribution[pid]
        for pid in ids
    }

    xp_pool = max(n, int(round(max(0, int(base_xp)) * RAID_XP_POOL_MULTIPLIER)))
    gil_pool = max(n, int(round(max(0, int(base_gil)) * RAID_GIL_POOL_MULTIPLIER)))

    def allocate(pool: int) -> dict[str, int]:
        # Reserve one unit for every participant first, then distribute the
        # remainder by blended weight. This guarantees exact pool accounting.
        remaining = max(0, pool - n)
        raw_extra = {pid: remaining * weights[pid] for pid in ids}
        out = {pid: 1 + int(math.floor(raw_extra[pid])) for pid in ids}
        remainder = pool - sum(out.values())
        if remainder > 0:
            order = sorted(
                ids,
                key=lambda pid: (raw_extra[pid] - math.floor(raw_extra[pid]), positive[pid], pid),
                reverse=True,
            )
            for pid in order[:remainder]:
                out[pid] += 1
        return out

    xp = allocate(xp_pool)
    gil = allocate(gil_pool)
    return {pid: (xp[pid], gil[pid]) for pid in ids}


def party_monster_hp(base_hp: int, party_size: int) -> int:
    size = max(1, int(party_size))
    return max(1, int(round(int(base_hp) * (1 + PARTY_HP_PER_EXTRA_HERO * (size - 1)))))


def party_enemy_attacks(party_size: int) -> int:
    """Return the single ordinary enemy action slot used by field battles.

    The argument is retained for compatibility with balance/simulator callers.
    Party size still scales monster HP; it no longer grants extra basic attacks.
    Multi-target pressure is reserved for abilities explicitly marked ``party``.
    """
    max(1, int(party_size))  # normalize legacy/custom callers without changing behavior
    return ENEMY_ACTIONS_PER_ROUND


def critical_chance(luck: int, job_bonus: float = 0.0, effect_bonus: float = 0.0) -> float:
    chance = 0.05 + max(0, int(luck)) * 0.0015 + float(job_bonus) + float(effect_bonus)
    return max(0.0, min(MAX_CRIT_CHANCE, chance))


def battle_mp_pool(mag: int, spr: int) -> int:
    """Return a bounded persistent MP maximum from magical stats.

    Square-root scaling preserves Job/stat identity while stopping late-game MP
    from outgrowing fixed ability costs by an order of magnitude.
    """
    stat_total = max(1, int(mag) + int(spr))
    value = round(BATTLE_MP_BASE + math.sqrt(stat_total) * BATTLE_MP_STAT_SCALE)
    return max(BATTLE_MP_MIN, min(BATTLE_MP_MAX, int(value)))


def battle_ap_pool(strength: int, dexterity: int) -> int:
    """Return a bounded persistent AP maximum from physical stats."""
    stat_total = max(1, int(strength) + int(dexterity))
    value = round(BATTLE_AP_BASE + math.sqrt(stat_total) * BATTLE_AP_STAT_SCALE)
    return max(BATTLE_AP_MIN, min(BATTLE_AP_MAX, int(value)))


def defend_mp_restore(max_mp: int) -> int:
    """Return the Defend MP recovery amount for one Active round."""
    pool = max(1, int(max_mp))
    return max(1, int(round(pool * DEFEND_MP_RESTORE_FRACTION)))


def defend_ap_restore(max_ap: int) -> int:
    """Return the Defend AP recovery amount for one Active round."""
    pool = max(1, int(max_ap))
    return max(1, int(round(pool * DEFEND_AP_RESTORE_FRACTION)))


def active_hunt_status_chance(base_chance: float, rank: str, status_id: str) -> float:
    """Scale player debuff chance against a Hunt mark without hard immunities."""
    base = max(0.0, min(1.0, float(base_chance)))
    rank_key = str(rank).upper()
    table = HUNT_STUN_CHANCE_MULTIPLIERS if str(status_id) == "stun" else HUNT_STATUS_CHANCE_MULTIPLIERS
    return max(0.0, min(1.0, base * float(table.get(rank_key, 1.0))))


def raid_contribution_score(*, damage: int = 0, healing: int = 0, mitigation: int = 0) -> float:
    """Reward raid support work without minting a larger reward pool."""
    return max(
        0.0,
        float(max(0, int(damage)))
        + float(max(0, int(healing))) * RAID_HEAL_WEIGHT
        + float(max(0, int(mitigation))) * RAID_MITIGATION_WEIGHT,
    )


def active_hunt_hp(base_hp: int, rank: str) -> int:
    """Return the solo Active Hunt HP target for a Hunt rank."""
    mult = HUNT_HP_MULTIPLIERS.get(str(rank).upper(), 1.0)
    return max(1, int(round(int(base_hp) * mult)))


def active_hunt_pressure(rank: str) -> float:
    """Return the bounded enemy-pressure multiplier for an Active Hunt."""
    return float(HUNT_PRESSURE_MULTIPLIERS.get(str(rank).upper(), 1.0))


def active_hunt_round_limit(rank: str) -> int:
    """Higher Hunt ranks get more tactical room before the safety timeout."""
    return int(HUNT_MAX_ROUNDS.get(str(rank).upper(), 12))

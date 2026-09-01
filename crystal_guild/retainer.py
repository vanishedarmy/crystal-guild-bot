from __future__ import annotations

from typing import Any

# v1.7.0 Alpha 1 — Retainer Service
# Retainers are deliberately lightweight procurement agents. They do not hold
# gear, equip items, enter combat, or replace Expeditions/Hunts. Every listed
# reward is an existing crafting/material item and the reward roll is committed
# when dispatch begins so reconnecting cannot reroll the haul.

RETAINER_DEFAULT_NAME = "Guild Retainer"
RETAINER_MAX_RANK = 5
RETAINER_RANKS = (
    {"rank": 1, "name": "Novice", "xp_floor": 0},
    {"rank": 2, "name": "Proven", "xp_floor": 100},
    {"rank": 3, "name": "Veteran", "xp_floor": 300},
    {"rank": 4, "name": "Expert", "xp_floor": 700},
    {"rank": 5, "name": "Master", "xp_floor": 1400},
)

# pool entries are (item_id, weight). No relic/artifact materials are available
# in Alpha 1; prestigious materials remain tied to their normal content.
RETAINER_ASSIGNMENTS = (
    {
        "id": "field_gathering",
        "name": "Field Gathering",
        "description": "Sweep nearby roads and low-risk gathering grounds for dependable common crafting materials.",
        "rank_required": 1,
        "duration_seconds": 30 * 60,
        "cost_gil": 100,
        "xp": 20,
        "rolls": 2,
        "quantity": (1, 2),
        "pool_label": "Common field materials",
        "pool": (
            ("iron_ore", 18), ("bone_chip", 15), ("wolf_fang", 15), ("fish_scale", 12),
            ("bomb_fragment", 12), ("imp_wing", 10), ("cockatrice_pinion", 10), ("goblin_medallion", 8),
        ),
    },
    {
        "id": "monster_salvage",
        "name": "Monster Salvage",
        "description": "Follow old hunt trails and recover useful hides, scales, fangs, vines, and monster components.",
        "rank_required": 1,
        "duration_seconds": 60 * 60,
        "cost_gil": 250,
        "xp": 35,
        "rolls": 3,
        "quantity": (1, 2),
        "pool_label": "Common and uncommon monster materials",
        "pool": (
            ("wolf_fang", 14), ("bone_chip", 12), ("fish_scale", 10), ("imp_wing", 9),
            ("cockatrice_pinion", 9), ("ochu_vine", 9), ("goblin_medallion", 8),
            ("coeurl_whisker", 7), ("chimera_scale", 6), ("lamia_scale", 6), ("antlion_mandible", 5), ("sandworm_fang", 5),
        ),
    },
    {
        "id": "mineral_survey",
        "name": "Mineral Survey",
        "description": "Prospect old workings and Magitek debris fields for ore, scrap, and crystalline crafting stock.",
        "rank_required": 2,
        "duration_seconds": 2 * 60 * 60,
        "cost_gil": 500,
        "xp": 65,
        "rolls": 3,
        "quantity": (1, 2),
        "pool_label": "Ore, Magitek scrap, and crystals",
        "pool": (
            ("iron_ore", 25), ("magitek_scrap", 18), ("crystal_shard", 14), ("mythril_ore", 12),
            ("death_claw_pincer", 8), ("magitek_capacitor", 7), ("mimic_lock", 6), ("ironclad_plate", 5), ("iron_giant_plate", 5),
        ),
    },
    {
        "id": "regional_procurement",
        "name": "Regional Procurement",
        "description": "Travel farther afield for a broader haul of uncommon and rare materials used by advanced recipes.",
        "rank_required": 3,
        "duration_seconds": 4 * 60 * 60,
        "cost_gil": 900,
        "xp": 110,
        "rolls": 4,
        "quantity": (1, 2),
        "pool_label": "Uncommon and rare regional materials",
        "pool": (
            ("coeurl_whisker", 12), ("chimera_scale", 11), ("malboro_tendril", 10), ("magitek_scrap", 10),
            ("death_claw_pincer", 9), ("antlion_mandible", 8), ("sandworm_fang", 8), ("ancient_coin", 7),
            ("wyvern_scale", 6), ("ahriman_lens", 6), ("morbol_spore", 5), ("mythril_ore", 5), ("ancient_cloth", 3),
        ),
    },
    {
        "id": "specialist_acquisition",
        "name": "Specialist Acquisition",
        "description": "Commission an expert procurement route for difficult rare materials without touching relic or artifact drops.",
        "rank_required": 4,
        "duration_seconds": 8 * 60 * 60,
        "cost_gil": 1500,
        "xp": 180,
        "rolls": 4,
        "quantity": (1, 2),
        "pool_label": "Rare specialist crafting materials",
        "pool": (
            ("mythril_ore", 12), ("mindflayer_tentacle", 9), ("garuda_feather", 8), ("wyvern_scale", 8),
            ("demon_horn", 8), ("elemental_crystal", 8), ("magitek_capacitor", 8), ("mimic_lock", 7),
            ("iron_giant_plate", 7), ("ironclad_plate", 7), ("dragon_fang", 6), ("behemoth_hide", 6),
            ("bomb_kings_fuse", 4), ("morbol_bulb", 2),
        ),
    },
)
RETAINER_ASSIGNMENTS_BY_ID = {row["id"]: row for row in RETAINER_ASSIGNMENTS}


def retainer_rank(total_xp: int) -> dict[str, Any]:
    xp = max(0, int(total_xp))
    current = RETAINER_RANKS[0]
    for row in RETAINER_RANKS:
        if xp >= int(row["xp_floor"]):
            current = row
        else:
            break
    rank = int(current["rank"])
    next_row = RETAINER_RANKS[rank] if rank < RETAINER_MAX_RANK else None
    floor = int(current["xp_floor"])
    next_floor = int(next_row["xp_floor"]) if next_row else floor
    return {
        "rank": rank,
        "rank_name": str(current["name"]),
        "xp": xp,
        "xp_into_rank": max(0, xp - floor),
        "xp_to_next": max(0, next_floor - floor) if next_row else 0,
        "next_rank_xp": next_floor if next_row else None,
        "max_rank": rank >= RETAINER_MAX_RANK,
    }


def _weighted_pick(pool: tuple[tuple[str, int], ...], rng: Any) -> str:
    ids = [str(item_id) for item_id, _weight in pool]
    weights = [max(1, int(weight)) for _item_id, weight in pool]
    # random.Random.choices is available on every supported Python runtime.
    return str(rng.choices(ids, weights=weights, k=1)[0])


def roll_retainer_rewards(assignment: dict[str, Any], rank: int, rng: Any) -> dict[str, Any]:
    pool = tuple(assignment.get("pool") or ())
    low, high = assignment.get("quantity", (1, 1))
    aggregated: dict[str, int] = {}
    for _ in range(max(1, int(assignment.get("rolls", 1)))):
        item_id = _weighted_pick(pool, rng)
        qty = int(rng.randint(max(1, int(low)), max(1, int(high))))
        aggregated[item_id] = aggregated.get(item_id, 0) + qty

    # Small bonus-find chance, improving slightly with Retainer Rank. This is
    # intentionally modest; the main haul remains the predictable value source.
    bonus: dict[str, Any] | None = None
    bonus_chance = min(0.10, 0.05 + (max(1, int(rank)) * 0.01))
    if float(rng.random()) < bonus_chance:
        item_id = _weighted_pick(pool, rng)
        bonus = {"item_id": item_id, "quantity": 1}

    return {
        "items": [{"item_id": item_id, "quantity": quantity} for item_id, quantity in sorted(aggregated.items())],
        "bonus": bonus,
        "bonus_chance": bonus_chance,
    }

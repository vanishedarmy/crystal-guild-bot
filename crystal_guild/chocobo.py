from __future__ import annotations

import math
from typing import Any

CHOC_MAX_LEVEL = 20
WRIT_COST_GIL = 500
WRIT_ACTIVATION_SECONDS = 60 * 60
STABLE_FACILITY_ID = "chocobo_stable"
QUEST_ID = "a_chocobo_of_your_own"
QUEST_NAME = "A Chocobo of Your Own"
QUEST_DESCRIPTION = (
    "Prove you can handle the road before the Stable hands you responsibility for a very large bird."
)
QUEST_REWARD_GIL = 250

DEFAULT_PORTRAIT_ID = "classic_gold"
PORTRAITS: dict[str, dict[str, str]] = {
    "classic_gold": {"name": "Classic Gold"},
    "midnight_black": {"name": "Midnight"},
    "celestial_white": {"name": "Celestial"},
    "ember_red": {"name": "Ember"},
    "verdant_green": {"name": "Verdant"},
    "cobalt_blue": {"name": "Cobalt"},
    "arcane_violet": {"name": "Arcane"},
    "desert_gold": {"name": "Sandrunner"},
    "frost_silver": {"name": "Frost"},
    "rose_pink": {"name": "Rose"},
}

QUEST_REQUIREMENTS: list[dict[str, Any]] = [
    {"type": "character_level", "amount": 10},
    {"type": "ventures", "amount": 10},
    {"type": "hunt_rank_total", "rank": "C", "amount": 1},
]

TRAITS: dict[str, dict[str, str]] = {
    "steady_strider": {
        "name": "Steady Strider",
        "description": "Calm footing reduces Expedition hazard risk and improves cache recovery after a rescue.",
    },
    "keen_eye": {
        "name": "Keen Eye",
        "description": "Notices what others miss, improving Expedition discovery events.",
    },
    "fleet_feet": {
        "name": "Fleet Feet",
        "description": "Built to move, reducing Expedition travel time by 15%.",
    },
    "forager": {
        "name": "Forager",
        "description": "Has a suspicious talent for finding useful things, improving Expedition material finds and yield.",
    },
    "lucky_plume": {
        "name": "Lucky Plume",
        "description": "Improves Expedition treasure and Chocobo events and slightly improves cache recovery after rescue.",
    },
}


BOND_TIERS: tuple[dict[str, Any], ...] = (
    {"tier": 5, "min_level": 20, "name": "Legendary Partner"},
    {"tier": 4, "min_level": 15, "name": "Veteran Partner"},
    {"tier": 3, "min_level": 10, "name": "Proven Partner"},
    {"tier": 2, "min_level": 5, "name": "Trailwise Partner"},
    {"tier": 1, "min_level": 1, "name": "New Partner"},
)

SPECIALIZATIONS: dict[str, dict[str, str]] = {
    "steady_strider": {
        "id": "guardian",
        "name": "Guardian",
        "summary": "Keeps the party steady through hazards and protects more of the Expedition Cache during rescue.",
    },
    "keen_eye": {
        "id": "scout",
        "name": "Scout",
        "summary": "Finds discoveries and rare regional opportunities more often.",
    },
    "fleet_feet": {
        "id": "pathfinder",
        "name": "Pathfinder",
        "summary": "Cuts travel time and gets the party between Expedition stages faster.",
    },
    "forager": {
        "id": "forager",
        "name": "Forager",
        "summary": "Improves resource-event weighting and the amount of regional material gathered.",
    },
    "lucky_plume": {
        "id": "treasure_hunter",
        "name": "Treasure Hunter",
        "summary": "Improves treasure opportunities, rare events, and Chocobo rescue cache protection.",
    },
}


def bond_tier_for_level(level: int) -> dict[str, Any]:
    level = max(1, min(CHOC_MAX_LEVEL, int(level)))
    current = next(row for row in BOND_TIERS if level >= int(row["min_level"]))
    higher = sorted((row for row in BOND_TIERS if int(row["min_level"]) > level), key=lambda row: int(row["min_level"]))
    return {
        "tier": int(current["tier"]),
        "name": str(current["name"]),
        "min_level": int(current["min_level"]),
        "next_level": int(higher[0]["min_level"]) if higher else None,
        "maxed": not higher,
    }


def expedition_specialization(traits: set[str] | list[str] | tuple[str, ...], level: int) -> dict[str, Any] | None:
    trait_set = {str(value) for value in traits}
    trait_id = next((value for value in TRAITS if value in trait_set and value in SPECIALIZATIONS), None)
    if not trait_id:
        return None
    tier = bond_tier_for_level(level)
    tier_no = int(tier["tier"])
    spec = SPECIALIZATIONS[trait_id]
    if trait_id == "steady_strider":
        effects = [
            f"Hazard damage -{35 + (tier_no - 1) * 3}%",
            f"Rescue cache protection +{10 + (tier_no - 1)} pts",
        ]
    elif trait_id == "keen_eye":
        effects = [
            f"Discovery weighting +{25 + (tier_no - 1) * 3}%",
            f"Rare-event chance +{1.5 + (tier_no - 1) * 0.25:.1f} pts",
        ]
    elif trait_id == "fleet_feet":
        effects = [f"Travel time -{15 + (tier_no - 1)}%", "Route boosts remain 20% faster"]
    elif trait_id == "forager":
        effects = [
            f"Resource weighting +{25 + (tier_no - 1) * 3}%",
            f"Regional material yield +{2 if tier_no >= 4 else 1}",
        ]
    else:
        effects = [
            f"Treasure weighting +{15 + (tier_no - 1) * 2.5:.0f}%",
            f"Rare-event chance +{1.0 + (tier_no - 1) * 0.25:.1f} pts",
        ]
    return {
        "id": str(spec["id"]),
        "name": str(spec["name"]),
        "trait_id": trait_id,
        "trait_name": str(TRAITS[trait_id]["name"]),
        "summary": str(spec["summary"]),
        "tier": tier_no,
        "tier_name": str(tier["name"]),
        "next_tier_level": tier["next_level"],
        "maxed": bool(tier["maxed"]),
        "effects": effects,
    }


def xp_required_for_level(level: int) -> int:
    """XP needed to advance from *level* to the next Chocobo level."""
    level = max(1, min(CHOC_MAX_LEVEL, int(level)))
    if level >= CHOC_MAX_LEVEL:
        return 0
    return max(40, int(round(45 * (level ** 1.32))))


def level_from_total_xp(total_xp: int) -> tuple[int, int, int]:
    """Return (level, xp_into_level, xp_to_next) from cumulative Bond XP."""
    remaining = max(0, int(total_xp))
    level = 1
    while level < CHOC_MAX_LEVEL:
        need = xp_required_for_level(level)
        if remaining < need:
            return level, remaining, need
        remaining -= need
        level += 1
    return CHOC_MAX_LEVEL, 0, 0


def total_xp_floor_for_level(level: int) -> int:
    level = max(1, min(CHOC_MAX_LEVEL, int(level)))
    return sum(xp_required_for_level(current) for current in range(1, level))


def trait_for_player(player_id: str) -> str:
    """Stable deterministic starter trait so registration retries cannot reroll."""
    ids = tuple(sorted(TRAITS))
    seed = sum((index + 1) * ord(char) for index, char in enumerate(str(player_id)))
    return ids[seed % len(ids)]

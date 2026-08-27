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
        "description": "Calm footing and good instincts. Planned to reduce Expedition mishap risk.",
    },
    "keen_eye": {
        "name": "Keen Eye",
        "description": "Notices what others miss. Planned to improve Expedition discovery checks.",
    },
    "fleet_feet": {
        "name": "Fleet Feet",
        "description": "Built to move. Planned to improve Expedition travel efficiency.",
    },
    "forager": {
        "name": "Forager",
        "description": "Has a suspicious talent for finding useful things. Planned to improve material finds.",
    },
    "lucky_plume": {
        "name": "Lucky Plume",
        "description": "The Guild cannot prove this feather is lucky, which has never stopped anyone before.",
    },
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

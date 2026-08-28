from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Shared Fellowship progression intentionally uses a simple numeric label in v1.1.
# Names can be layered on later without changing stored level values.
FELLOWSHIP_LEVEL_THRESHOLDS = [
    0,
    1_000,
    2_500,
    5_000,
    8_500,
    13_000,
    19_000,
    27_000,
    37_000,
    50_000,
]

# Personal Guild standing follows the familiar Grand-Company-style cadence while
# remaining Crystal Guild-wide rather than tying players to a faction.
GUILD_RANKS = [
    {"name": "Recruit", "renown": 0},
    {"name": "Private Third Class", "renown": 100},
    {"name": "Private Second Class", "renown": 250},
    {"name": "Private First Class", "renown": 500},
    {"name": "Corporal", "renown": 900},
    {"name": "Sergeant Third Class", "renown": 1_500},
    {"name": "Sergeant Second Class", "renown": 2_400},
    {"name": "Sergeant First Class", "renown": 3_600},
    {"name": "Chief Sergeant", "renown": 5_200},
    {"name": "Second Lieutenant", "renown": 7_500},
    {"name": "First Lieutenant", "renown": 10_000},
    {"name": "Captain", "renown": 14_000},
]

FACILITIES: dict[str, dict[str, Any]] = {
    "guild_hall": {
        "name": "Guild Hall",
        "description": "The heart of the Fellowship. Higher tiers unlock larger Guild projects and future systems.",
        "max_tier": 5,
        "benefits": [
            "Fellowship established",
            "Tier II projects unlocked",
            "Tier III projects unlocked",
            "Tier IV projects unlocked",
            "Guild project capacity maximized",
        ],
        "material": "ancient_coin",
        "activity": "raid_clear",
    },
    "infirmary": {
        "name": "Infirmary",
        "description": "Improves free camp recovery for every adventurer.",
        "max_tier": 5,
        "benefits": [
            "Camp recovery 4% faster",
            "Camp recovery 8% faster",
            "Camp recovery 12% faster",
            "Camp recovery 16% faster",
            "Camp recovery 20% faster",
        ],
        "material": "hi_potion",
        "activity": "venture_complete",
    },
    "workshop": {
        "name": "Workshop",
        "description": "Reduces the Gil service fee charged when forging equipment.",
        "max_tier": 5,
        "benefits": [
            "Forge Gil fees 2% lower",
            "Forge Gil fees 4% lower",
            "Forge Gil fees 6% lower",
            "Forge Gil fees 8% lower",
            "Forge Gil fees 10% lower",
        ],
        "material": "mythril_ore",
        "activity": "forge",
    },
    "training_hall": {
        "name": "Training Hall",
        "description": "Adds a modest JP training bonus to successful combat rewards.",
        "max_tier": 5,
        "benefits": [
            "Combat JP +1%",
            "Combat JP +2%",
            "Combat JP +3%",
            "Combat JP +4%",
            "Combat JP +5%",
        ],
        "material": "wyvern_scale",
        "activity": "combat_victory",
    },
    "archives": {
        "name": "Archives",
        "description": "Expands Guild-wide Bestiary knowledge and collection reporting.",
        "max_tier": 5,
        "benefits": [
            "Guild Bestiary records established",
            "Expanded monster knowledge",
            "Weakness research highlighted",
            "Completion reporting expanded",
            "Master Archivist milestone enabled",
        ],
        "material": "elemental_crystal",
        "activity": "monster_victory",
    },
    "chocobo_stable": {
        "name": "Chocobo Stable",
        "description": "Provides safe boarding, registration, and training space for Fellowship Chocobos.",
        "max_tier": 1,
        "benefits": [
            "Chocobo registration and companion training unlocked",
        ],
        "material": "",
        "activity": "venture_complete",
    },
    "quartermaster": {
        "name": "Quartermaster",
        "description": "Improves personal shop logistics without replacing the normal Gil economy.",
        "max_tier": 5,
        "benefits": [
            "Shop refresh 3% faster",
            "Shop refresh 6% faster",
            "Shop refresh 9% faster",
            "Shop refresh 12% faster",
            "Shop refresh 15% faster",
        ],
        "material": "demon_horn",
        "activity": "craft",
    },
}


def _project_requirements(facility_id: str, tier: int) -> list[dict[str, Any]]:
    facility = FACILITIES[facility_id]
    if facility_id == "chocobo_stable":
        return [
            {"key": "gil", "kind": "gil", "asset_id": "gil", "target": 5_000, "label": "Gil"},
            {"key": "activity:venture_complete", "kind": "activity", "asset_id": "venture_complete", "target": 10, "label": "Ventures completed"},
            {"key": "fellowship_level", "kind": "level", "asset_id": "level", "target": 2, "label": "Fellowship LVL"},
        ]
    if facility_id == "guild_hall":
        level_req = max(1, tier)
        activity_target = max(2, (tier - 1) * 3)
    else:
        level_req = max(1, tier * 2 - 1)
        activity_target = (20, 45, 80, 125, 180)[tier - 1]
    gil_target = (5_000, 15_000, 35_000, 75_000, 150_000)[tier - 1]
    material_target = (10, 20, 35, 55, 80)[tier - 1]
    return [
        {"key": "gil", "kind": "gil", "asset_id": "gil", "target": gil_target, "label": "Gil"},
        {
            "key": f"item:{facility['material']}",
            "kind": "item",
            "asset_id": facility["material"],
            "target": material_target,
            "label": facility["material"].replace("_", " ").title(),
        },
        {
            "key": f"activity:{facility['activity']}",
            "kind": "activity",
            "asset_id": facility["activity"],
            "target": activity_target,
            "label": _activity_label(facility["activity"]),
        },
        {"key": "fellowship_level", "kind": "level", "asset_id": "level", "target": level_req, "label": "Fellowship LVL"},
    ]


def _activity_label(activity: str) -> str:
    labels = {
        "venture_complete": "Ventures completed",
        "combat_victory": "Combat victories",
        "monster_victory": "Monsters defeated",
        "hunt_win": "Hunts won",
        "raid_win": "Raid wins",
        "raid_clear": "Guild raids won",
        "craft": "Items crafted",
        "forge": "Forge upgrades",
        "job_mastery": "Jobs mastered",
        "treasure": "Treasure chests found",
        "project_complete": "Projects completed",
    }
    return labels.get(activity, activity.replace("_", " ").title())


PROJECTS: dict[str, dict[str, Any]] = {}
for _facility_id, _facility in FACILITIES.items():
    start_tier = 2 if _facility_id == "guild_hall" else 1
    for _tier in range(start_tier, int(_facility["max_tier"]) + 1):
        project_id = f"{_facility_id}_t{_tier}"
        PROJECTS[project_id] = {
            "id": project_id,
            "facility_id": _facility_id,
            "tier": _tier,
            "name": f"{_facility['name']} — Tier {_tier}",
            "description": _facility["description"],
            "required_level": 2 if _facility_id == "chocobo_stable" else max(1, _tier if _facility_id == "guild_hall" else _tier * 2 - 1),
            "requirements": _project_requirements(_facility_id, _tier),
        }

# v1.2 Expeditions: the shared Expedition Board becomes available at Fellowship LVL 6 once Guild Hall Tier 1 is established.
# Completing the Board is the Fellowship-wide launch gate for distant contracts.
PROJECTS["expedition_board"] = {
    "id": "expedition_board",
    "facility_id": "guild_hall",
    "tier": 1,
    "name": "Expedition Board",
    "description": "Prepare the Guild Hall for distant contracts. Completing this Board unlocks Expeditions for adventurers with a registered Chocobo.",
    "required_level": 6,
    "required_hall_tier": 1,
    "teaser": True,
    "requirements": [
        {"key": "gil", "kind": "gil", "asset_id": "gil", "target": 200_000, "label": "Gil"},
        {"key": "item:ancient_coin", "kind": "item", "asset_id": "ancient_coin", "target": 100, "label": "Ancient Coin"},
        {"key": "activity:raid_clear", "kind": "activity", "asset_id": "raid_clear", "target": 5, "label": "Guild raids won"},
        {"key": "fellowship_level", "kind": "level", "asset_id": "level", "target": 6, "label": "Fellowship LVL"},
    ],
}

ORDER_DEFINITIONS = [
    {"id": "into_the_wilds", "name": "Into the Wilds", "activity": "venture_complete", "target": 75, "renown": 300, "description": "Complete Ventures together."},
    {"id": "monster_hunters", "name": "Monster Hunters", "activity": "combat_victory", "target": 40, "renown": 350, "description": "Win normal encounters or Hunts."},
    {"id": "bounty_board", "name": "Bounty Board", "activity": "hunt_win", "target": 15, "renown": 400, "description": "Defeat Hunt marks."},
    {"id": "hammer_and_tongs", "name": "Hammer & Tongs", "activity": "craft_forge", "target": 35, "renown": 300, "description": "Craft items or complete forge upgrades."},
    {"id": "treasure_seekers", "name": "Treasure Seekers", "activity": "treasure", "target": 25, "renown": 300, "description": "Discover Venture treasure chests."},
    {"id": "stand_together", "name": "Stand Together", "activity": "raid_participation", "target": 20, "renown": 450, "description": "Participate in resolved Guild raids."},
]

DEEDS = [
    {"id": "adventure_begins", "name": "The Adventure Begins", "activity": "venture_complete", "target": 100, "renown": 250, "description": "Complete 100 Ventures."},
    {"id": "road_warriors", "name": "Road Warriors", "activity": "venture_complete", "target": 1_000, "renown": 750, "description": "Complete 1,000 Ventures."},
    {"id": "treasure_hunters", "name": "Treasure Hunters", "activity": "treasure", "target": 250, "renown": 600, "description": "Find 250 Venture treasure chests."},
    {"id": "bounty_board", "name": "Bounty Board", "activity": "hunt_win", "target": 100, "renown": 600, "description": "Defeat 100 Hunt marks."},
    {"id": "giant_killers", "name": "Giant Killers", "activity": "raid_clear", "target": 25, "renown": 1_000, "description": "Win 25 Guild raids."},
    {"id": "master_artisans", "name": "Master Artisans", "activity": "craft", "target": 500, "renown": 650, "description": "Craft 500 items."},
    {"id": "tempered_steel", "name": "Tempered Steel", "activity": "forge", "target": 500, "renown": 650, "description": "Complete 500 forge upgrades."},
    {"id": "many_paths", "name": "Many Paths", "activity": "job_mastery", "target": 25, "renown": 750, "description": "Master 25 Jobs across the Fellowship."},
]


def fellowship_level_for_renown(renown: int) -> int:
    renown = max(0, int(renown))
    level = 1
    for index, threshold in enumerate(FELLOWSHIP_LEVEL_THRESHOLDS, start=1):
        if renown >= threshold:
            level = index
        else:
            break
    return min(level, len(FELLOWSHIP_LEVEL_THRESHOLDS))


def fellowship_level_progress(renown: int) -> dict[str, int | bool]:
    renown = max(0, int(renown))
    level = fellowship_level_for_renown(renown)
    current_threshold = FELLOWSHIP_LEVEL_THRESHOLDS[level - 1]
    if level >= len(FELLOWSHIP_LEVEL_THRESHOLDS):
        return {"level": level, "current": renown, "start": current_threshold, "next": current_threshold, "maxed": True}
    next_threshold = FELLOWSHIP_LEVEL_THRESHOLDS[level]
    return {"level": level, "current": renown, "start": current_threshold, "next": next_threshold, "maxed": False}


def guild_rank_for_renown(renown: int) -> dict[str, Any]:
    renown = max(0, int(renown))
    rank_index = 0
    for index, rank in enumerate(GUILD_RANKS):
        if renown >= int(rank["renown"]):
            rank_index = index
        else:
            break
    rank = GUILD_RANKS[rank_index]
    next_rank = GUILD_RANKS[rank_index + 1] if rank_index + 1 < len(GUILD_RANKS) else None
    return {
        "index": rank_index,
        "name": rank["name"],
        "renown": renown,
        "threshold": int(rank["renown"]),
        "next_name": next_rank["name"] if next_rank else None,
        "next_threshold": int(next_rank["renown"]) if next_rank else None,
        "maxed": next_rank is None,
    }


def weekly_period_key(timestamp: float | None = None) -> str:
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp is not None else datetime.now(timezone.utc)
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def weekly_orders(period_key: str) -> list[dict[str, Any]]:
    # Stable deterministic rotation; no database RNG state is required.
    seed = sum(ord(char) for char in period_key)
    count = len(ORDER_DEFINITIONS)
    start = seed % count
    picks: list[dict[str, Any]] = []
    used: set[int] = set()
    step = 2 if count % 2 else 1
    index = start
    while len(picks) < min(3, count):
        if index not in used:
            picks.append(dict(ORDER_DEFINITIONS[index]))
            used.add(index)
        index = (index + step) % count
        if index in used:
            index = (index + 1) % count
    return picks


def facility_effects(facility_tiers: dict[str, int]) -> dict[str, float]:
    infirmary = max(0, min(5, int(facility_tiers.get("infirmary", 0))))
    workshop = max(0, min(5, int(facility_tiers.get("workshop", 0))))
    training = max(0, min(5, int(facility_tiers.get("training_hall", 0))))
    quartermaster = max(0, min(5, int(facility_tiers.get("quartermaster", 0))))
    return {
        "camp_reduction": infirmary * 0.04,
        "forge_discount": workshop * 0.02,
        "jp_bonus": training * 0.01,
        "shop_refresh_reduction": quartermaster * 0.03,
    }

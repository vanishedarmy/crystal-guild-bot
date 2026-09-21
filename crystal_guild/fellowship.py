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
    # v1.3 Guild Expansion presents five major facilities on the public Guild Board.
    # Legacy support facilities remain defined below so existing upgrades/effects and
    # in-progress v1.2 projects are never discarded during an in-place upgrade.
    "guild_hall": {
        "name": "Guild Hall",
        "description": "The heart of the Fellowship and the anchor for major Guild construction.",
        "max_tier": 5,
        "guild_expansion": True,
        "max_level": 3,
        "level_benefits": [
            "Guild operations established; the Expedition Board can be built once the Fellowship reaches LVL 6.",
            "Advanced Guild construction projects become available.",
            "Guild Hall expansion complete; the Fellowship is ready for future Legacy projects.",
        ],
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
        "description": "Legacy support facility retained from the original Fellowship program.",
        "max_tier": 5,
        "benefits": [
            "Camp recovery 4% faster", "Camp recovery 8% faster", "Camp recovery 12% faster",
            "Camp recovery 16% faster", "Camp recovery 20% faster",
        ],
        "material": "hi_potion", "activity": "venture_complete", "legacy": True,
    },
    "workshop": {
        "name": "Workshop",
        "description": "The Guild's shared forge and construction workshop.",
        "max_tier": 5,
        "guild_expansion": True,
        "max_level": 3,
        "level_benefits": [
            "Forge Gil service fees 2% lower.",
            "Forge Gil service fees 4% lower; basic material refining is available.",
            "Forge Gil service fees 6% lower; advanced material refining is available.",
        ],
        "benefits": [
            "Forge Gil fees 2% lower", "Forge Gil fees 4% lower", "Forge Gil fees 6% lower",
            "Forge Gil fees 8% lower", "Forge Gil fees 10% lower",
        ],
        "material": "mythril_ore", "activity": "forge",
    },
    "emporium_annex": {
        "name": "Moogle Emporium Annex",
        "description": "A compact Guild-funded storefront expansion that gives every adventurer more choices in each personal Moogle Emporium rotation.",
        "max_tier": 1,
        "max_level": 1,
        "guild_service": True,
        "level_benefits": [
            "Annex stock is fixed at +2 Weapons, +4 Armor/Accessories, and +6 Items per personal rotation.",
        ],
        "benefits": [
            "Emporium Annex adds +2 Weapons, +4 Armor/Accessories, +6 Items",
        ],
        "material": "mythril_ore", "activity": "craft",
    },
    "trading_post": {
        "name": "Moogle Trading Post",
        "description": "A Fellowship-built player market attached to the Moogle Emporium where adventurers can list eligible gear, materials, and supplies for one another.",
        "max_tier": 1,
        "max_level": 1,
        "guild_service": True,
        "level_benefits": [
            "Player-to-player fixed-price listings unlock in the Moogle Emporium.",
        ],
        "benefits": [
            "Player Trading Post unlocked",
        ],
        "material": "mythril_ore", "activity": "venture_complete",
    },
    "training_hall": {
        "name": "Training Hall",
        "description": "Legacy support facility retained from the original Fellowship program.",
        "max_tier": 5,
        "benefits": ["Combat JP +1%", "Combat JP +2%", "Combat JP +3%", "Combat JP +4%", "Combat JP +5%"],
        "material": "wyvern_scale", "activity": "combat_victory", "legacy": True,
    },
    "archives": {
        "name": "Guild Archive",
        "description": "A shared record of monsters, discoveries, bosses, and Guild accomplishments.",
        "max_tier": 5,
        "guild_expansion": True,
        "max_level": 3,
        "level_benefits": [
            "Guild Bestiary and discovery records established.",
            "Research grants +0.5% rare Expedition event chance.",
            "Research grants +1.0% rare Expedition event chance.",
        ],
        "benefits": [
            "Guild Bestiary records established", "Expanded monster knowledge", "Weakness research highlighted",
            "Completion reporting expanded", "Master Archivist milestone enabled",
        ],
        "material": "elemental_crystal", "activity": "monster_victory",
    },
    "chocobo_stable": {
        "name": "Chocobo Stables",
        "description": "Shared boarding and training grounds for the Fellowship's Chocobo companions.",
        "max_tier": 3,
        "guild_expansion": True,
        "max_level": 3,
        "level_benefits": [
            "Stable training grants +5% Chocobo Bond XP.",
            "Expanded training grants +10% Chocobo Bond XP.",
            "Grand Stable training grants +15% Chocobo Bond XP.",
        ],
        "benefits": [
            "Chocobo registration and companion training unlocked",
            "Expanded Chocobo training grounds established",
            "Grand Stable expansion complete",
        ],
        "material": "wyvern_scale", "activity": "venture_complete",
    },
    "quartermaster": {
        "name": "Quartermaster",
        "description": "Legacy support facility retained from the original Fellowship program.",
        "max_tier": 5,
        "benefits": [
            "Shop refresh 3% faster", "Shop refresh 6% faster", "Shop refresh 9% faster",
            "Shop refresh 12% faster", "Shop refresh 15% faster",
        ],
        "material": "demon_horn", "activity": "craft", "legacy": True,
    },
    "airship_dock": {
        "name": "Airship Dock",
        "description": "The construction and service dock for the Crystal Guild Airship.",
        "max_tier": 3,
        "guild_expansion": True,
        "max_level": 3,
        "future_locked": False,
        "level_benefits": [
            "Airship construction berth established; the Crystal Guild Airship can be built.",
            "Expanded service gantry enables Tier II Airship upgrades.",
            "Grand Airship Dock enables Tier III Airship upgrades.",
        ],
        "benefits": ["Airship construction berth established", "Tier II Airship upgrades enabled", "Tier III Airship upgrades enabled"],
        "material": "ancient_coin", "activity": "raid_clear",
    },
}

GUILD_EXPANSION_FACILITY_IDS = ("guild_hall", "workshop", "chocobo_stable", "archives", "airship_dock")
# Alpha 3 keeps Legacy's original five-major-facility contract intact while
# adding the smaller Emporium Annex to the public Guild construction board.
PUBLIC_GUILD_FACILITY_IDS = ("guild_hall", "workshop", "emporium_annex", "trading_post", "chocobo_stable", "archives", "airship_dock")

# Alpha 3 — Guild Services & Workshop. Material exchanges are intentionally
# lossy and carry a modest Gil service fee so they recycle surplus common
# materials without replacing monster drops, crafting, or the normal economy.
WORKSHOP_EXCHANGES = [
    {"id": "refine_mythril", "name": "Refine Mythril", "min_level": 2, "input_id": "iron_ore", "input_qty": 5, "output_id": "mythril_ore", "output_qty": 1, "gil": 250, "description": "Refine five Iron Ore into one Mythril Ore."},
    {"id": "temper_dragon_scale", "name": "Temper Dragon Scale", "min_level": 2, "input_id": "wyvern_scale", "input_qty": 4, "output_id": "dragon_scale", "output_qty": 1, "gil": 300, "description": "Temper four Wyvern Scales into one Dragon Scale."},
    {"id": "press_adamantite", "name": "Press Adamantite", "min_level": 3, "input_id": "mythril_ore", "input_qty": 6, "output_id": "adamantite", "output_qty": 1, "gil": 1600, "description": "Press six Mythril Ore into one Adamantite."},
    {"id": "condense_dark_matter", "name": "Condense Dark Matter", "min_level": 3, "input_id": "elemental_crystal", "input_qty": 10, "output_id": "dark_matter", "output_qty": 1, "gil": 1000, "description": "Condense ten Elemental Crystals into one Dark Matter."},
]


# Alpha 4 — Guild Airship. Missions are shared deployments whose progress is
# supplied by ordinary Guild play while the Airship is away. The active run is
# persistent in schema 9; rewards resolve once the return timer expires.
AIRSHIP_MISSIONS = [
    {
        "id": "merchant_escort", "name": "Merchant Escort", "required_core": 0,
        "duration_hours": 24, "target": 50, "activities": {"venture_complete": 1},
        "guild_renown": 600, "personal_gil": 750, "personal_renown": 25,
        "description": "Keep trade lanes moving. Normal Ventures supply escort progress while the Airship carries a merchant convoy.",
    },
    {
        "id": "monster_suppression", "name": "Monster Suppression", "required_core": 0,
        "duration_hours": 30, "target": 30, "activities": {"hunt_win": 2, "combat_victory": 1, "encounter_win": 1},
        "guild_renown": 700, "personal_gil": 850, "personal_renown": 30,
        "description": "Support the Airship patrol by defeating dangerous monsters and Hunt marks across the Guild's routes.",
    },
    {
        "id": "aether_survey", "name": "Aether Survey", "required_core": 0,
        "duration_hours": 36, "target": 15, "activities": {"expedition_complete": 1},
        "guild_renown": 800, "personal_gil": 900, "personal_renown": 35,
        "description": "Feed Expedition route data to an airborne aether survey of the frontier.",
    },
    {
        "id": "salvage_run", "name": "Salvage Run", "required_core": 1,
        "duration_hours": 30, "target": 35, "activities": {"treasure": 1, "forge": 1, "craft": 1},
        "guild_renown": 900, "personal_gil": 1100, "personal_renown": 40,
        "description": "Search old ruins and wreckage. Treasure finds and artisan work keep the salvage crew supplied.",
    },
    {
        "id": "crystal_resonance", "name": "Crystal Resonance Survey", "required_core": 1,
        "duration_hours": 42, "target": 20, "activities": {"expedition_complete": 1, "raid_win": 1},
        "guild_renown": 1000, "personal_gil": 1200, "personal_renown": 45,
        "description": "Map unstable crystal currents using Expedition discoveries and raid-combat telemetry.",
    },
    {
        "id": "relic_recovery", "name": "Relic Recovery", "required_core": 2,
        "duration_hours": 48, "target": 24, "activities": {"raid_participation": 1, "expedition_complete": 2},
        "guild_renown": 1250, "personal_gil": 1500, "personal_renown": 55,
        "description": "Back a difficult recovery operation with raid deployments and deep Expedition fieldwork.",
    },
]

AIRSHIP_UPGRADES = {
    "hull": {"name": "Hull", "description": "Reinforced plating gives dangerous missions a larger success margin."},
    "engine": {"name": "Engine", "description": "Improved engines shorten Airship mission travel time."},
    "cargo": {"name": "Cargo Hold", "description": "Expanded cargo capacity increases participant Gil rewards."},
    "survey": {"name": "Survey Array", "description": "Better instruments increase Fellowship Renown earned from Airship missions."},
    "crystal_core": {"name": "Crystal Core", "description": "A stronger core unlocks advanced Airship missions."},
}


def _project_requirements(facility_id: str, tier: int) -> list[dict[str, Any]]:
    facility = FACILITIES[facility_id]
    if facility_id == "airship_dock":
        # Beta 1 balance pass: the Dock remains a major late-Guild investment,
        # but the Alpha raid/Ancient Coin stack pushed ordinary communities into
        # a multi-month stall before they could meaningfully improve the Airship.
        dock_targets = {
            1: (60_000, 25, 4, 7),
            2: (100_000, 35, 6, 8),
            3: (170_000, 55, 9, 9),
        }
        gil_target, coin_target, raid_target, level_req = dock_targets[tier]
        return [
            {"key": "gil", "kind": "gil", "asset_id": "gil", "target": gil_target, "label": "Gil"},
            {"key": "item:ancient_coin", "kind": "item", "asset_id": "ancient_coin", "target": coin_target, "label": "Ancient Coin"},
            {"key": "activity:raid_clear", "kind": "activity", "asset_id": "raid_clear", "target": raid_target, "label": "Guild raids won"},
            {"key": "fellowship_level", "kind": "level", "asset_id": "level", "target": level_req, "label": "Fellowship LVL"},
        ]
    if facility_id == "emporium_annex":
        return [
            {"key": "gil", "kind": "gil", "asset_id": "gil", "target": 20_000, "label": "Gil"},
            {"key": "item:mythril_ore", "kind": "item", "asset_id": "mythril_ore", "target": 12, "label": "Mythril Ore"},
            {"key": "activity:craft", "kind": "activity", "asset_id": "craft", "target": 20, "label": "Items crafted"},
            {"key": "fellowship_level", "kind": "level", "asset_id": "level", "target": 3, "label": "Fellowship LVL"},
        ]
    if facility_id == "trading_post":
        return [
            {"key": "gil", "kind": "gil", "asset_id": "gil", "target": 25_000, "label": "Gil"},
            {"key": "item:mythril_ore", "kind": "item", "asset_id": "mythril_ore", "target": 3, "label": "Mythril Ore"},
            {"key": "activity:venture_complete", "kind": "activity", "asset_id": "venture_complete", "target": 15, "label": "Ventures completed"},
            {"key": "fellowship_level", "kind": "level", "asset_id": "level", "target": 1, "label": "Fellowship LVL"},
        ]
    if facility_id == "chocobo_stable":
        stable_targets = {
            1: (5_000, 0, 10, 2),
            2: (15_000, 12, 30, 4),
            3: (40_000, 25, 75, 6),
        }
        gil_target, material_target, activity_target, level_req = stable_targets[tier]
        requirements = [
            {"key": "gil", "kind": "gil", "asset_id": "gil", "target": gil_target, "label": "Gil"},
        ]
        if material_target:
            requirements.append({
                "key": "item:wyvern_scale", "kind": "item", "asset_id": "wyvern_scale",
                "target": material_target, "label": "Wyvern Scale",
            })
        requirements.extend([
            {"key": "activity:venture_complete", "kind": "activity", "asset_id": "venture_complete", "target": activity_target, "label": "Ventures completed"},
            {"key": "fellowship_level", "kind": "level", "asset_id": "level", "target": level_req, "label": "Fellowship LVL"},
        ])
        return requirements
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
        "expedition_complete": "Expeditions completed",
    }
    return labels.get(activity, activity.replace("_", " ").title())


PROJECTS: dict[str, dict[str, Any]] = {}
for _facility_id, _facility in FACILITIES.items():
    if _facility.get("future_locked"):
        continue
    start_tier = 2 if _facility_id == "guild_hall" else 1
    for _tier in range(start_tier, int(_facility["max_tier"]) + 1):
        is_major = _facility_id in GUILD_EXPANSION_FACILITY_IDS
        is_service = bool(_facility.get("guild_service"))
        is_legacy_step = bool(_facility.get("legacy")) or (is_major and _tier > int(_facility.get("max_level", 3)))
        project_id = f"{_facility_id}_t{_tier}"
        PROJECTS[project_id] = {
            "id": project_id,
            "facility_id": _facility_id,
            "tier": _tier,
            "level": min(_tier, int(_facility.get("max_level", _facility["max_tier"]))),
            "name": f"{_facility['name']} — {'Lv. ' if (is_major or is_service) and not is_legacy_step else 'Tier '}{_tier}",
            "description": _facility["description"],
            "required_level": 1 if _facility_id == "trading_post" else (3 if _facility_id == "emporium_annex" else (2 if _facility_id == "chocobo_stable" and _tier == 1 else max(1, _tier if _facility_id == "guild_hall" else _tier * 2 - 1))),
            "requirements": _project_requirements(_facility_id, _tier),
            "legacy": is_legacy_step,
            "project_type": "construction",
        }


for _tier, _level_req, _hall_req in ((1, 7, 2), (2, 8, 3), (3, 9, 3)):
    _dock_project = PROJECTS.get(f"airship_dock_t{_tier}")
    if _dock_project:
        _dock_project["required_level"] = _level_req
        _dock_project["required_hall_tier"] = _hall_req



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
    "project_type": "construction",
    "requirements": [
        {"key": "gil", "kind": "gil", "asset_id": "gil", "target": 200_000, "label": "Gil"},
        {"key": "item:ancient_coin", "kind": "item", "asset_id": "ancient_coin", "target": 100, "label": "Ancient Coin"},
        {"key": "activity:raid_clear", "kind": "activity", "asset_id": "raid_clear", "target": 5, "label": "Guild raids won"},
        {"key": "fellowship_level", "kind": "level", "asset_id": "level", "target": 6, "label": "Fellowship LVL"},
    ],
}

# Guild Projects II adds shorter one-time initiatives alongside permanent facility construction.
# They intentionally reuse the existing project ledger so the current Guild Expansion line remains schema-compatible.
COMMUNITY_PROJECTS: dict[str, dict[str, Any]] = {
    "moogle_relief_shipment": {
        "id": "moogle_relief_shipment", "facility_id": "community", "tier": 0, "level": 0, "name": "Moogle Relief Shipment", "project_type": "supply_drive",
        "description": "Pack a compact relief shipment for wandering merchants and field crews.",
        "required_level": 2, "reward_renown": 300,
        "requirements": [
            {"key": "gil", "kind": "gil", "asset_id": "gil", "target": 15000, "label": "Gil"},
            {"key": "item:potion", "kind": "item", "asset_id": "potion", "target": 25, "label": "Potion"},
            {"key": "item:hi_potion", "kind": "item", "asset_id": "hi_potion", "target": 10, "label": "Hi-Potion"},
        ],
    },
    "forge_stockpile": {
        "id": "forge_stockpile", "facility_id": "community", "tier": 0, "level": 0, "name": "Forge Stockpile", "project_type": "supply_drive",
        "description": "Build a reserve of construction-grade materials for the Guild Workshop.",
        "required_level": 4, "reward_renown": 400,
        "requirements": [
            {"key": "gil", "kind": "gil", "asset_id": "gil", "target": 20000, "label": "Gil"},
            {"key": "item:mythril_ore", "kind": "item", "asset_id": "mythril_ore", "target": 20, "label": "Mythril Ore"},
            {"key": "item:elemental_crystal", "kind": "item", "asset_id": "elemental_crystal", "target": 10, "label": "Elemental Crystal"},
        ],
    },
    "frontier_stores": {
        "id": "frontier_stores", "facility_id": "community", "tier": 0, "level": 0, "name": "Frontier Stores", "project_type": "supply_drive",
        "description": "Stock the Guild for distant travel with field supplies and salvage currency.",
        "required_level": 5, "reward_renown": 450,
        "requirements": [
            {"key": "gil", "kind": "gil", "asset_id": "gil", "target": 30000, "label": "Gil"},
            {"key": "item:ancient_coin", "kind": "item", "asset_id": "ancient_coin", "target": 20, "label": "Ancient Coin"},
            {"key": "item:tent", "kind": "item", "asset_id": "tent", "target": 8, "label": "Tent"},
        ],
    },
    "clear_the_roads": {
        "id": "clear_the_roads", "facility_id": "community", "tier": 0, "level": 0, "name": "Clear the Roads", "project_type": "guild_objective",
        "description": "Thin out dangerous marks so merchants and adventurers can travel safely.",
        "required_level": 3, "reward_renown": 450,
        "requirements": [
            {"key": "activity:hunt_win", "kind": "activity", "asset_id": "hunt_win", "target": 30, "label": "Hunts won"},
        ],
    },
    "chart_the_frontier": {
        "id": "chart_the_frontier", "facility_id": "community", "tier": 0, "level": 0, "name": "Chart the Frontier", "project_type": "guild_objective",
        "description": "Complete distant Expeditions and return fresh route data to the Guild Archive.",
        "required_level": 4, "reward_renown": 500,
        "requirements": [
            {"key": "activity:expedition_complete", "kind": "activity", "asset_id": "expedition_complete", "target": 20, "label": "Expeditions completed"},
        ],
    },
    "raid_preparedness": {
        "id": "raid_preparedness", "facility_id": "community", "tier": 0, "level": 0, "name": "Raid Preparedness", "project_type": "guild_objective",
        "description": "Prove the Fellowship can repeatedly field a raid-ready force.",
        "required_level": 5, "reward_renown": 600,
        "requirements": [
            {"key": "activity:raid_clear", "kind": "activity", "asset_id": "raid_clear", "target": 8, "label": "Guild raids won"},
        ],
    },
}
PROJECTS.update(COMMUNITY_PROJECTS)


# The Airship itself is a one-time Fellowship construction project after the
# first Dock level. Upgrade tracks then use the same contribution ledger as
# ordinary construction, with their final tier capped by Airship Dock level.
PROJECTS["crystal_guild_airship"] = {
    "id": "crystal_guild_airship", "facility_id": "airship", "tier": 0, "level": 0,
    "name": "Crystal Guild Airship", "project_type": "airship_construction",
    "description": "Construct the Fellowship's shared Airship and open Guild-scale deployments.",
    "required_level": 8, "required_dock_level": 1, "reward_renown": 1500,
    "requirements": [
        {"key": "gil", "kind": "gil", "asset_id": "gil", "target": 140_000, "label": "Gil"},
        {"key": "item:mythril_ore", "kind": "item", "asset_id": "mythril_ore", "target": 35, "label": "Mythril Ore"},
        {"key": "item:wyvern_scale", "kind": "item", "asset_id": "wyvern_scale", "target": 18, "label": "Wyvern Scale"},
        {"key": "item:elemental_crystal", "kind": "item", "asset_id": "elemental_crystal", "target": 20, "label": "Elemental Crystal"},
        {"key": "item:ancient_coin", "kind": "item", "asset_id": "ancient_coin", "target": 10, "label": "Ancient Coin"},
        {"key": "activity:raid_clear", "kind": "activity", "asset_id": "raid_clear", "target": 6, "label": "Guild raids won"},
        {"key": "fellowship_level", "kind": "level", "asset_id": "level", "target": 8, "label": "Fellowship LVL"},
    ],
}

def _airship_upgrade_requirements(upgrade_id: str, tier: int) -> list[dict[str, Any]]:
    # Track-specific materials keep each improvement thematic while the common
    # Gil/raid requirements preserve the communal construction loop.
    material = {
        "hull": "adamantite",
        "engine": "magitek_capacitor",
        "cargo": "mythril_ore",
        "survey": "elemental_crystal",
        "crystal_core": "dark_matter",
    }[upgrade_id]
    # Beta 1 balance pass: upgrade tracks are long-term progression, but the
    # original identical 5/10/18 material curve made artifact tracks (Adamantite
    # and Dark Matter) vastly more expensive than common-material tracks. Keep
    # those rare resources prestigious without requiring dozens of weeks of a
    # single drop family.
    gil = (25_000, 55_000, 95_000)[tier - 1]
    if material in {"adamantite", "dark_matter"}:
        qty = (2, 4, 6)[tier - 1]
    elif material == "magitek_capacitor":
        qty = (3, 5, 8)[tier - 1]
    else:
        qty = (4, 7, 10)[tier - 1]
    raids = (1, 2, 2)[tier - 1]
    return [
        {"key": "gil", "kind": "gil", "asset_id": "gil", "target": gil, "label": "Gil"},
        {"key": f"item:{material}", "kind": "item", "asset_id": material, "target": qty, "label": material.replace("_", " ").title()},
        {"key": "activity:raid_clear", "kind": "activity", "asset_id": "raid_clear", "target": raids, "label": "Guild raids won"},
    ]

for _upgrade_id, _upgrade in AIRSHIP_UPGRADES.items():
    for _tier in range(1, 4):
        _project_id = f"airship_{_upgrade_id}_t{_tier}"
        PROJECTS[_project_id] = {
            "id": _project_id, "facility_id": "airship", "tier": _tier, "level": _tier,
            "upgrade_id": _upgrade_id, "name": f"Airship {_upgrade['name']} — Tier {_tier}",
            "project_type": "airship_upgrade", "description": _upgrade["description"],
            "required_level": 8, "required_dock_level": _tier, "reward_renown": 300 * _tier,
            "requirements": _airship_upgrade_requirements(_upgrade_id, _tier),
        }


ORDER_DEFINITIONS = [
    {"id": "into_the_wilds", "name": "Into the Wilds", "activity": "venture_complete", "target": 75, "renown": 300, "personal_gil": 500, "personal_renown": 25, "description": "Complete Ventures together."},
    {"id": "monster_hunters", "name": "Monster Hunters", "activity": "combat_victory", "target": 40, "renown": 350, "personal_gil": 500, "personal_renown": 25, "description": "Win normal encounters or Hunts."},
    {"id": "bounty_board", "name": "Bounty Board", "activity": "hunt_win", "target": 15, "renown": 400, "personal_gil": 600, "personal_renown": 25, "description": "Defeat Hunt marks."},
    {"id": "hammer_and_tongs", "name": "Hammer & Tongs", "activity": "craft_forge", "target": 35, "renown": 300, "personal_gil": 500, "personal_renown": 25, "description": "Craft items or complete forge upgrades."},
    {"id": "treasure_seekers", "name": "Treasure Seekers", "activity": "treasure", "target": 25, "renown": 300, "personal_gil": 500, "personal_renown": 25, "description": "Discover Venture treasure chests."},
    {"id": "stand_together", "name": "Stand Together", "activity": "raid_participation", "target": 20, "renown": 450, "personal_gil": 750, "personal_renown": 30, "description": "Participate in resolved Guild raids."},
]

WEEKLY_ORDER_SET_REWARD = {"guild_renown": 500, "personal_gil": 1000, "personal_renown": 50}

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


# Alpha 5 — Guild Legacy & Accomplishments. These are long-term Fellowship
# achievements derived from existing persistent state. Completion receipts use
# fellowship_events, so no additional schema is required and retroactive
# accomplishments can be granted safely once when an older Guild upgrades.
LEGACY_ACCOMPLISHMENTS = [
    {"id": "foundations_laid", "name": "Foundations Laid", "metric": "major_facilities_built", "target": 5, "renown": 300, "trophy": "Founders' Standard", "description": "Establish all five major Guild facilities."},
    {"id": "grand_fellowship", "name": "Grand Fellowship", "metric": "major_facilities_complete", "target": 5, "renown": 1000, "trophy": "Crystal Guild Banner", "description": "Raise every major Guild facility to Lv. 3."},
    {"id": "million_gil_guild", "name": "A Million Gil Later", "metric": "gil_donated", "target": 1_000_000, "renown": 750, "trophy": "Golden Ledger", "description": "Contribute 1,000,000 Gil to Fellowship projects."},
    {"id": "frontier_cartographers", "name": "Frontier Cartographers", "metric": "expeditions_completed", "target": 100, "renown": 750, "trophy": "Frontier Map Wall", "description": "Complete 100 Expeditions across the Fellowship."},
    {"id": "raid_vanguard", "name": "Raid Vanguard", "metric": "raids_won", "target": 100, "renown": 900, "trophy": "Vanguard Crest", "description": "Win 100 Guild raids."},
    {"id": "skybound_company", "name": "Skybound Company", "metric": "airship_built", "target": 1, "renown": 300, "trophy": "Airship Commission Plaque", "description": "Complete the Crystal Guild Airship."},
    {"id": "veteran_crew", "name": "Veteran Crew", "metric": "airship_missions_completed", "target": 25, "renown": 750, "trophy": "Veteran Crew Pennant", "description": "Complete 25 successful Airship missions."},
    {"id": "master_shipwrights", "name": "Master Shipwrights", "metric": "airship_upgrade_tiers", "target": 15, "renown": 1000, "trophy": "Master Shipwright Model", "description": "Complete every Airship upgrade track through Tier III."},
    {"id": "living_archive", "name": "Living Archive", "metric": "deeds_complete", "target": 8, "renown": 800, "trophy": "Chronicle of Deeds", "description": "Complete every current permanent Fellowship Deed."},
    {"id": "seasoned_fellowship", "name": "Seasoned Fellowship", "metric": "weekly_sets_completed", "target": 12, "renown": 750, "trophy": "Twelve-Week Service Ribbon", "description": "Complete the full set of Weekly Fellowship Orders twelve times."},
]




def legacy_metric_values(conn: Any) -> dict[str, int]:
    tiers = {str(row["facility_id"]): int(row["tier"] or 0) for row in conn.execute("SELECT facility_id,tier FROM fellowship_facilities").fetchall()}
    event_totals = {str(row["activity"]): int(row["amount"] or 0) for row in conn.execute("SELECT activity,COALESCE(SUM(amount),0) AS amount FROM fellowship_events GROUP BY activity").fetchall()}
    totals = conn.execute("SELECT COALESCE(SUM(gil_donated),0) AS gil FROM fellowship_members").fetchone()
    deeds = conn.execute("SELECT COUNT(*) AS n FROM fellowship_deeds WHERE completed_at IS NOT NULL").fetchone()
    airship = conn.execute("SELECT built,missions_completed FROM fellowship_airship_state WHERE singleton_id=1").fetchone()
    upgrade_total = conn.execute("SELECT COALESCE(SUM(tier),0) AS n FROM fellowship_airship_upgrades").fetchone()
    return {
        "major_facilities_built": sum(1 for facility_id in GUILD_EXPANSION_FACILITY_IDS if int(tiers.get(facility_id, 0)) >= 1),
        "major_facilities_complete": sum(1 for facility_id in GUILD_EXPANSION_FACILITY_IDS if int(tiers.get(facility_id, 0)) >= 3),
        "gil_donated": int(totals["gil"] if totals else 0),
        "expeditions_completed": int(event_totals.get("expedition_complete", 0)),
        "raids_won": int(event_totals.get("raid_clear", 0)),
        "airship_built": 1 if airship and int(airship["built"] or 0) else 0,
        "airship_missions_completed": int(airship["missions_completed"] or 0) if airship else 0,
        "airship_upgrade_tiers": int(upgrade_total["n"] if upgrade_total else 0),
        "deeds_complete": int(deeds["n"] if deeds else 0),
        "weekly_sets_completed": int(event_totals.get("weekly_orders_complete", 0)),
    }


def legacy_snapshot_from_connection(conn: Any) -> dict[str, Any]:
    metrics = legacy_metric_values(conn)
    receipt_rows = conn.execute("SELECT event_key,created_at FROM fellowship_events WHERE activity='legacy_accomplishment'").fetchall()
    receipts = {str(row["event_key"]): row["created_at"] for row in receipt_rows}
    accomplishments = []
    for item in LEGACY_ACCOMPLISHMENTS:
        progress = max(0, int(metrics.get(str(item["metric"]), 0)))
        target = max(1, int(item["target"]))
        key = f"legacy_accomplishment:{item['id']}"
        complete = progress >= target
        accomplishments.append({**item, "progress": min(progress, target), "raw_progress": progress, "complete": complete, "completed_at": receipts.get(key)})
    completed = [item for item in accomplishments if item["complete"]]
    count = len(completed)
    if count >= 9:
        stage, stage_name = 4, "Legendary Guild Hall"
    elif count >= 6:
        stage, stage_name = 3, "Hall of Heroes"
    elif count >= 3:
        stage, stage_name = 2, "Bannered Hall"
    else:
        stage, stage_name = 1, "Founding Hall"
    incomplete = [item for item in accomplishments if not item["complete"]]
    incomplete.sort(key=lambda item: (-(float(item["raw_progress"]) / max(1, int(item["target"]))), int(item["target"])))
    return {
        "stage": stage,
        "stage_name": stage_name,
        "completed": count,
        "total": len(accomplishments),
        "accomplishments": accomplishments,
        "decorations": [item["trophy"] for item in completed],
        "next_accomplishment": incomplete[0] if incomplete else None,
    }

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
    stable = max(0, min(3, int(facility_tiers.get("chocobo_stable", 0))))
    archives = max(0, min(3, int(facility_tiers.get("archives", 0))))
    return {
        "camp_reduction": infirmary * 0.04,
        "forge_discount": workshop * 0.02,
        "jp_bonus": training * 0.01,
        "shop_refresh_reduction": quartermaster * 0.03,
        "chocobo_xp_bonus": stable * 0.05,
        "archive_rare_event_bonus": max(0, archives - 1) * 0.005,
    }

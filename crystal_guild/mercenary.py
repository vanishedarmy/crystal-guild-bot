from __future__ import annotations

from typing import Any

MERC_SERVICE_NAME = "Hero Merc Service"
MERC_PROPRIETOR = "Cloud Strife"
MERC_MISSION_TYPES = {"hunt", "venture", "raid"}
FOUNDER_HERO_IDS = {"aerith", "tifa", "zidane", "yuna", "balthier", "cloud"}

# Hero Merc contracts use the existing Hunt Seal economy.
# Hunts already award Hunt Seals; Merc Service does not add a second Hunt currency.
# v1.8.1 adds permanent recruitment for expansion Heroes. Founding Heroes keep their
# original progression availability so existing players never lose access.

HEROES: tuple[dict[str, Any], ...] = (
    {
        "id": "aerith", "name": "Aerith Gainsborough", "origin": "Final Fantasy VII",
        "role": "Support", "specialty": "Healing / Recovery", "weapon": "Staff",
        "fee_seals": 5, "min_level": 8, "required_hunt_clears": 2,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Healing Wind",
        "catchphrase": "I'll help.", "art_set": "a1",
        "effect_summary": "Healing Wind restores HP and grants short regeneration.",
        "recruitment": {"kind": "founding", "name": "Founding Roster"},
    },
    {
        "id": "tifa", "name": "Tifa Lockhart", "origin": "Final Fantasy VII",
        "role": "Striker", "specialty": "Critical Burst", "weapon": "Gloves",
        "fee_seals": 6, "min_level": 10, "required_hunt_clears": 3,
        "mission_types": ("hunt", "raid"), "signature": "Beat Rush",
        "catchphrase": "Leave it to me.", "art_set": "a1",
        "effect_summary": "Beat Rush opens the mission with a critical burst of damage.",
        "recruitment": {"kind": "founding", "name": "Founding Roster"},
    },
    {
        "id": "zidane", "name": "Zidane Tribal", "origin": "Final Fantasy IX",
        "role": "Scavenger", "specialty": "Extra Finds", "weapon": "Daggers",
        "fee_seals": 5, "min_level": 7, "required_hunt_clears": 2,
        "mission_types": ("venture", "hunt"), "signature": "Treasure Hunter",
        "catchphrase": "Let's make this fun.", "art_set": "a1",
        "effect_summary": "Treasure Hunter secures one additional monster drop on a victory.",
        "recruitment": {"kind": "founding", "name": "Founding Roster"},
    },
    {
        "id": "yuna", "name": "Yuna", "origin": "Final Fantasy X",
        "role": "Support", "specialty": "Protection / Recovery", "weapon": "Staff",
        "fee_seals": 7, "min_level": 12, "required_hunt_clears": 5,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Guardian's Grace",
        "catchphrase": "I can help.", "art_set": "a1",
        "effect_summary": "Guardian's Grace restores HP and grants temporary protection.",
        "recruitment": {"kind": "founding", "name": "Founding Roster"},
    },
    {
        "id": "balthier", "name": "Balthier", "origin": "Final Fantasy XII",
        "role": "Specialist", "specialty": "Rare Spoils", "weapon": "Gun",
        "fee_seals": 9, "min_level": 15, "required_hunt_clears": 7,
        "mission_types": ("venture", "hunt", "raid"), "signature": "Leading Man",
        "catchphrase": "Leave the leading man to it.", "art_set": "a1",
        "effect_summary": "Leading Man fires an opening shot and makes a rare-spoil attempt on victory.",
        "recruitment": {"kind": "founding", "name": "Founding Roster"},
    },
    {
        "id": "cloud", "name": "Cloud Strife", "origin": "Final Fantasy VII",
        "role": "Striker", "specialty": "Heavy Burst", "weapon": "Buster Sword",
        "fee_seals": 12, "min_level": 30, "required_hunt_clears": 15,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Braver",
        "catchphrase": "Let's finish this.", "art_set": "a1",
        "effect_summary": "Braver opens the mission with a heavy burst of damage.",
        "recruitment": {"kind": "founding", "name": "Founding Roster"},
    },
    {
        "id": "auron", "name": "Auron", "origin": "Final Fantasy X",
        "role": "Hunt Specialist", "specialty": "Boss Hunts / Finisher", "weapon": "Greatsword",
        "fee_seals": 13, "min_level": 20, "required_hunt_clears": 10,
        "mission_types": ("hunt", "raid"), "signature": "Bushido",
        "catchphrase": "Stay focused.", "art_set": "a2",
        "effect_summary": "Bushido delivers a heavy opening strike built for elite and boss targets.",
        "recruitment": {
            "kind": "quest", "name": "The Guardian's Test", "required_level": 20,
            "required_hunt_clears": 10, "required_dungeon_clears": 0,
            "hint": "Prove the Guild can survive dangerous Hunts, then offer Auron a permanent place on the roster.",
        },
    },
    {
        "id": "vivi", "name": "Vivi", "origin": "Final Fantasy IX",
        "role": "Black Mage", "specialty": "Elemental Burst", "weapon": "Rod",
        "fee_seals": 8, "min_level": 15, "required_hunt_clears": 4,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Elemental Burst",
        "catchphrase": "I'll do my best.", "art_set": "a2",
        "effect_summary": "Elemental Burst opens battle with a powerful magic strike.",
        "recruitment": {
            "kind": "quest", "name": "Trial of the Elements", "required_level": 15,
            "required_hunt_clears": 4, "required_dungeon_clears": 1,
            "hint": "Complete a Dungeon and build enough Hunt experience to earn Vivi's confidence.",
        },
    },
    {
        "id": "cecil", "name": "Cecil", "origin": "Final Fantasy IV",
        "role": "Paladin", "specialty": "Protection / Guard", "weapon": "Sword",
        "fee_seals": 9, "min_level": 20, "required_hunt_clears": 5,
        "mission_types": ("hunt", "raid"), "signature": "Paladin's Guard",
        "catchphrase": "I will protect you.", "art_set": "a2",
        "effect_summary": "Paladin's Guard grants a strong protective ward at the start of battle.",
        "recruitment": {
            "kind": "quest", "name": "A Paladin's Oath", "required_level": 20,
            "required_hunt_clears": 5, "required_dungeon_clears": 2,
            "hint": "Demonstrate discipline in Hunts and Dungeons before asking Cecil to join the Guild.",
        },
    },
    {
        "id": "terra", "name": "Terra", "origin": "Final Fantasy VI",
        "role": "Magitek", "specialty": "Arcane Burst", "weapon": "Sword",
        "fee_seals": 11, "min_level": 24, "required_hunt_clears": 0,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Arcane Burst",
        "catchphrase": "We'll find a way.", "art_set": "a2",
        "effect_summary": "Arcane Burst unleashes a high-powered magic strike as the assignment begins.",
        "recruitment": {
            "kind": "contract", "name": "Magitek Accord", "required_level": 24,
            "required_hunt_clears": 0, "required_dungeon_clears": 0, "gil_cost": 75000,
            "hint": "Fund a permanent Magitek Accord once the Guild is established enough to support her.",
        },
    },
    {
        "id": "tidus", "name": "Tidus", "origin": "Final Fantasy X",
        "role": "Vanguard", "specialty": "Speed / Momentum", "weapon": "Sword",
        "fee_seals": 9, "min_level": 18, "required_hunt_clears": 0,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Quick Hit",
        "catchphrase": "Let's keep moving.", "art_set": "a2",
        "effect_summary": "Quick Hit grants Haste at the start of the assignment, accelerating combat momentum.",
        "recruitment": {
            "kind": "contract", "name": "Blitz Ace Contract", "required_level": 18,
            "required_hunt_clears": 0, "required_dungeon_clears": 0, "gil_cost": 50000,
            "hint": "Offer a permanent Guild contract once you have the experience and Gil to back it up.",
        },
    },
    {
        "id": "ramza", "name": "Ramza", "origin": "Final Fantasy Tactics",
        "role": "Tactician", "specialty": "Party Support", "weapon": "Sword",
        "fee_seals": 10, "min_level": 30, "required_hunt_clears": 12,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Shout",
        "catchphrase": "Think, then strike.", "art_set": "a2",
        "effect_summary": "Shout opens the assignment with coordinated offense and protection.",
        "recruitment": {
            "kind": "quest", "name": "A Leader's Path", "required_level": 30,
            "required_hunt_clears": 12, "required_dungeon_clears": 3,
            "hint": "Prove your leadership across Hunts and Dungeons to earn Ramza's allegiance.",
        },
    },
)

HEROES_BY_ID = {row["id"]: row for row in HEROES}


def recruitment_public_state(
    hero: dict[str, Any], *, player_level: int, hunt_clears: int, dungeon_clears: int,
    player_gil: int, recruited: bool,
) -> dict[str, Any]:
    spec = dict(hero.get("recruitment") or {})
    kind = str(spec.get("kind") or "founding")
    founder = kind == "founding" or str(hero.get("id") or "") in FOUNDER_HERO_IDS
    permanently_recruited = bool(recruited or founder)
    required_level = max(1, int(spec.get("required_level", hero.get("min_level", 1)) or 1))
    required_hunts = max(0, int(spec.get("required_hunt_clears", 0) or 0))
    required_dungeons = max(0, int(spec.get("required_dungeon_clears", 0) or 0))
    gil_cost = max(0, int(spec.get("gil_cost", 0) or 0))
    objectives: list[dict[str, Any]] = []
    if not founder:
        objectives.append({"id": "level", "label": "Character Level", "current": max(1, int(player_level)), "required": required_level, "met": int(player_level) >= required_level})
        if required_hunts:
            objectives.append({"id": "hunts", "label": "Hunt Clears", "current": max(0, int(hunt_clears)), "required": required_hunts, "met": int(hunt_clears) >= required_hunts})
        if required_dungeons:
            objectives.append({"id": "dungeons", "label": "Dungeon Clears", "current": max(0, int(dungeon_clears)), "required": required_dungeons, "met": int(dungeon_clears) >= required_dungeons})
    prereqs_met = founder or all(bool(row["met"]) for row in objectives)
    affordable = int(player_gil) >= gil_cost
    ready = permanently_recruited or (prereqs_met and (kind != "contract" or affordable))
    if permanently_recruited:
        status = "recruited"
    elif prereqs_met and kind == "contract" and not affordable:
        status = "payment_required"
    elif prereqs_met:
        status = "ready"
    else:
        status = "locked"
    return {
        "required": not founder,
        "kind": kind,
        "name": str(spec.get("name") or ("Founding Roster" if founder else "Recruitment")),
        "hint": str(spec.get("hint") or ""),
        "recruited": permanently_recruited,
        "status": status,
        "ready": ready,
        "prereqs_met": prereqs_met,
        "gil_cost": gil_cost,
        "affordable": affordable,
        "objectives": objectives,
    }


def public_hero(
    hero: dict[str, Any], *, player_level: int, hunt_clears: int,
    dungeon_clears: int = 0, player_gil: int = 0, recruited: bool = False,
) -> dict[str, Any]:
    min_level = int(hero.get("min_level", 1))
    required_clears = int(hero.get("required_hunt_clears", 0))
    level_ok = int(player_level) >= min_level
    clears_ok = int(hunt_clears) >= required_clears
    progression_available = level_ok and clears_ok
    recruitment = recruitment_public_state(
        hero, player_level=player_level, hunt_clears=hunt_clears,
        dungeon_clears=dungeon_clears, player_gil=player_gil, recruited=recruited,
    )
    available = progression_available and bool(recruitment["recruited"])
    reasons: list[str] = []
    if not recruitment["recruited"]:
        reasons.append(f"Recruit via {recruitment['name']}")
    if not level_ok:
        reasons.append(f"Requires level {min_level}")
    if not clears_ok:
        reasons.append(f"Requires {required_clears} Hunt clears")
    return {
        "id": str(hero["id"]),
        "name": str(hero["name"]),
        "origin": str(hero["origin"]),
        "role": str(hero["role"]),
        "specialty": str(hero.get("specialty") or ""),
        "weapon": str(hero.get("weapon") or ""),
        "fee_seals": int(hero["fee_seals"]),
        "min_level": min_level,
        "required_hunt_clears": required_clears,
        "available": available,
        "progression_available": progression_available,
        "locked_reason": None if available else " · ".join(reasons),
        "mission_types": list(hero.get("mission_types") or ()),
        "signature": str(hero.get("signature") or ""),
        "catchphrase": str(hero.get("catchphrase") or ""),
        "effect_summary": str(hero.get("effect_summary") or ""),
        "art_set": str(hero.get("art_set") or "a1"),
        "recruitment": recruitment,
        "recruited": bool(recruitment["recruited"]),
    }

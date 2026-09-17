from __future__ import annotations

from typing import Any

MERC_SERVICE_NAME = "Hero Merc Service"
MERC_PROPRIETOR = "Cloud Strife"
MERC_MISSION_TYPES = {"hunt", "venture", "raid"}

# Hero Merc contracts use the existing Hunt Seal economy.
# Hunts already award Hunt Seals; Merc Service does not add a second Hunt currency.

HEROES: tuple[dict[str, Any], ...] = (
    {
        "id": "aerith", "name": "Aerith Gainsborough", "origin": "Final Fantasy VII",
        "role": "Support", "specialty": "Healing / Recovery", "weapon": "Staff",
        "fee_seals": 5, "min_level": 8, "required_hunt_clears": 2,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Healing Wind",
        "catchphrase": "I'll help.",
        "effect_summary": "Healing Wind restores HP and grants short regeneration.",
    },
    {
        "id": "tifa", "name": "Tifa Lockhart", "origin": "Final Fantasy VII",
        "role": "Striker", "specialty": "Critical Burst", "weapon": "Gloves",
        "fee_seals": 6, "min_level": 10, "required_hunt_clears": 3,
        "mission_types": ("hunt", "raid"), "signature": "Beat Rush",
        "catchphrase": "Leave it to me.",
        "effect_summary": "Beat Rush opens the mission with a critical burst of damage.",
    },
    {
        "id": "zidane", "name": "Zidane Tribal", "origin": "Final Fantasy IX",
        "role": "Scavenger", "specialty": "Extra Finds", "weapon": "Daggers",
        "fee_seals": 5, "min_level": 7, "required_hunt_clears": 2,
        "mission_types": ("venture", "hunt"), "signature": "Treasure Hunter",
        "catchphrase": "Let's make this fun.",
        "effect_summary": "Treasure Hunter secures one additional monster drop on a victory.",
    },
    {
        "id": "yuna", "name": "Yuna", "origin": "Final Fantasy X",
        "role": "Support", "specialty": "Protection / Recovery", "weapon": "Staff",
        "fee_seals": 7, "min_level": 12, "required_hunt_clears": 5,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Guardian's Grace",
        "catchphrase": "I can help.",
        "effect_summary": "Guardian's Grace restores HP and grants temporary protection.",
    },
    {
        "id": "balthier", "name": "Balthier", "origin": "Final Fantasy XII",
        "role": "Specialist", "specialty": "Rare Spoils", "weapon": "Gun",
        "fee_seals": 9, "min_level": 15, "required_hunt_clears": 7,
        "mission_types": ("venture", "hunt", "raid"), "signature": "Leading Man",
        "catchphrase": "Leave the leading man to it.",
        "effect_summary": "Leading Man fires an opening shot and makes a rare-spoil attempt on victory.",
    },
    {
        "id": "cloud", "name": "Cloud Strife", "origin": "Final Fantasy VII",
        "role": "Striker", "specialty": "Heavy Burst", "weapon": "Buster Sword",
        "fee_seals": 12, "min_level": 30, "required_hunt_clears": 15,
        "mission_types": ("hunt", "venture", "raid"), "signature": "Braver",
        "catchphrase": "Let's finish this.",
        "effect_summary": "Braver opens the mission with a heavy burst of damage.",
    },
)

HEROES_BY_ID = {row["id"]: row for row in HEROES}


def public_hero(hero: dict[str, Any], *, player_level: int, hunt_clears: int) -> dict[str, Any]:
    min_level = int(hero.get("min_level", 1))
    required_clears = int(hero.get("required_hunt_clears", 0))
    level_ok = int(player_level) >= min_level
    clears_ok = int(hunt_clears) >= required_clears
    available = level_ok and clears_ok
    reasons: list[str] = []
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
        "locked_reason": None if available else " · ".join(reasons),
        "mission_types": list(hero.get("mission_types") or ()),
        "signature": str(hero.get("signature") or ""),
        "catchphrase": str(hero.get("catchphrase") or ""),
        "effect_summary": str(hero.get("effect_summary") or ""),
    }

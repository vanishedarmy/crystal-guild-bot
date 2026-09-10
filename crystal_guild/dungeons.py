from __future__ import annotations

from typing import Any

DUNGEON_CACHE_RETREAT_RATIO = 0.50
DUNGEON_CACHE_DEFEAT_RATIO = 0.25


def room_kind_label(room: dict[str, Any]) -> str:
    kind = str(room.get("type") or "room").strip().lower()
    return {
        "entrance": "Entrance",
        "combat": "Encounter",
        "treasure": "Treasure",
        "hazard": "Hazard",
        "event": "Dungeon Event",
        "choice": "Crossroads",
        "miniboss": "Miniboss",
        "sanctuary": "Sanctuary",
        "boss": "Boss",
    }.get(kind, kind.replace("_", " ").title() or "Room")

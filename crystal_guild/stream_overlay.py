"""Public read-only Venture / World Event HUD protocol.

Only server-authorized, deliberately bounded display data may enter the hosted
Portal. Never copy a full runtime encounter or roster into the broadcast feed.
"""
from __future__ import annotations
import re
from typing import Any

ALLOWED_ELEMENTS = frozenset({"fire", "ice", "lightning", "water", "wind", "earth", "holy", "dark"})
ALLOWED_KINDS = frozenset({"venture", "world_event"})
ALLOWED_STATUS = frozenset({
    "poison", "blind", "silence", "sleep", "stun", "slow", "haste", "protect",
    "shell", "regen", "brave", "focus", "reflect", "evade", "barrier",
    "strength_up", "magic_up", "power_up", "taunt", "weaken", "vulnerable", "burn", "bleed",
    "paralyze", "curse", "doom", "defense_down", "attack_down",
})


def clean_stream_overlay(raw: dict[str, Any]) -> dict[str, Any]:
    if not bool(raw.get("active")) or raw.get("kind") not in ALLOWED_KINDS:
        return {"active": False, "status": "IDLE", "updated_at": max(0, int(raw.get("updated_at") or 0))}
    def bounded(text: Any, length: int) -> str:
        return str(text or "")[:length]
    def number(value: Any, cap: int) -> int:
        return max(0, min(cap, int(value or 0)))
    def tokens(field: str, allowed: frozenset[str], length: int) -> list[str]:
        rows = raw.get(field) or []
        if not isinstance(rows, list):
            return []
        return list(dict.fromkeys(str(v).strip().lower() for v in rows[:length]
            if isinstance(v, str) and str(v).strip().lower() in allowed))
    maximum = max(1, number(raw.get("max_hp"), 10_000_000_000))
    art = bounded(raw.get("art"), 200)
    if art and (not art.startswith("/") or art.startswith("//") or ".." in art or not re.fullmatch(r"/[a-zA-Z0-9_./-]+", art)):
        art = ""
    return {
        "active": True,
        "kind": raw["kind"],
        "status": bounded(raw.get("status") or "RALLY", 12),
        "monster": bounded(raw.get("monster"), 80),
        "monster_id": bounded(raw.get("monster_id"), 80),
        "art": art,
        "hp": min(number(raw.get("hp"), maximum), maximum),
        "max_hp": maximum,
        "attack": bounded(raw.get("attack") or "Attack", 80),
        "attack_kind": bounded(raw.get("attack_kind") or "rally", 16),
        "weaknesses": tokens("weaknesses", ALLOWED_ELEMENTS, 8),
        "buffs": tokens("buffs", ALLOWED_STATUS, 12),
        "debuffs": tokens("debuffs", ALLOWED_STATUS, 12),
        "joined": number(raw.get("joined"), 64),
        "round": number(raw.get("round"), 10_000),
        "next_round_at": number(raw.get("next_round_at"), 10_000_000_000),
        "updated_at": number(raw.get("updated_at"), 10_000_000_000),
    }

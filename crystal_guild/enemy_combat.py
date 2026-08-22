"""Data-driven enemy decision helpers for Active Battle.

This module deliberately contains *policy*, not persistence or chat I/O.
Enemy profiles and monster skills live in JSON; the game engine owns damage,
status application and authoritative state changes. Keeping selection here makes
AI tuning testable without growing ``engine.py`` into a monster-specific tree.
"""
from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def enemy_damage_multiplier(profile: dict[str, Any], hp_ratio: float, scaling: str) -> float:
    """Return profile pressure without changing the monster's catalog stats."""
    multiplier = float(profile.get("damage_mult", 1.0))
    if scaling == "magic":
        multiplier *= float(profile.get("magic_mult", 1.0))
    if hp_ratio <= 0.40:
        multiplier *= 1.0 + float(profile.get("low_hp_damage_bonus", 0.0))
    return max(0.25, multiplier)


def effective_special_chance(ability: dict[str, Any], profile: dict[str, Any]) -> float:
    """Apply AI profile bias while keeping skill frequency bounded/readable."""
    chance = float(ability.get("chance", 0.0)) * float(profile.get("ability_bias", 1.0))
    return _clamp(chance, 0.0, 0.45)


def effective_status_chance(effect: dict[str, Any], profile: dict[str, Any]) -> float:
    """Controllers gain a modest status edge; no effect can exceed 90%."""
    chance = float(effect.get("chance", 1.0)) + float(profile.get("status_bonus", 0.0))
    return _clamp(chance, 0.0, 0.90)


def choose_enemy_action(
    behavior: dict[str, Any],
    profile: dict[str, Any],
    *,
    hp_ratio: float,
    round_no: int,
    special_ready_round: int,
    monster_statuses: dict[str, dict[str, Any]],
    rng: Any,
) -> dict[str, Any]:
    """Choose the enemy's one round action: special, utility, or basic attack.

    Field battles resolve one enemy action per round. Target breadth belongs to
    the selected ability (single vs party), not to party-size attack scaling.
    Cooldowns use absolute round numbers so there is no fragile decrement
    bookkeeping across skipped turns.
    """
    ability = behavior.get("ability") or None
    if ability and round_no >= int(special_ready_round):
        if rng.random() < effective_special_chance(ability, profile):
            return {"kind": "special", "ability": ability}

    utility = profile.get("utility") or {}
    if utility and hp_ratio <= float(utility.get("hp_below", 0.0)):
        status_id = str(utility.get("status", ""))
        already_active = bool(
            status_id
            and status_id in monster_statuses
            and int(monster_statuses[status_id].get("turns", 0)) > 0
        )
        if not already_active and rng.random() < float(utility.get("chance", 0.0)):
            return {"kind": "utility", "utility": utility}

    return {"kind": "attack"}

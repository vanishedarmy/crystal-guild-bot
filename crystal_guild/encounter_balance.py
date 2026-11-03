"""Party-aware balance budgets for broadcast raids and live World Events.

Catalog HP remains the authored reference. An encounter's *combat* HP is
resolved once, after the rally roster closes; it never changes mid-fight.
These rules do not affect Ventures, Hunts, Trials, Dungeons, or rewards.
"""
from __future__ import annotations

import math
from typing import Any

RAID_ROUNDS = {
    "World Boss": 8,
    "Primal Boss": 11,
    "High Boss": 12,
    "Superboss": 14,
    "Ultimate Superboss": 16,
}


def raid_combat_hp(boss: dict[str, Any], combatants: int) -> int:
    """Tune sustained raid damage against party size and intended boss tier.

    Min two-player HP equivalent prevents a lone participant from deleting a
    social boss. Diminishing group scaling means extra players always help.
    Values approximate normal level-appropriate equipment, not overpowered
    Eternal Relics, so rare gear retains meaningful progression benefits.
    """
    level = max(1, min(99, int(boss.get("recommended_level", 1))))
    party = max(1, int(combatants))
    heroes = max(2.0, party ** 0.94)
    rounds = RAID_ROUNDS.get(str(boss.get("tier", "World Boss")), 10)
    expected_hit = 105 + 13 * level
    weight = max(0.7, min(1.6, float(boss.get("balance_hp_weight", 1.0))))
    # V2.0.1 adds meaningful boss armor, so offset most of that EHP here.
    # Otherwise high-armor fights would turn into a new HP sponge problem.
    guard = max(0.0, min(0.25, float(boss.get("balance_guard", 0.0))))
    weight *= 1.0 - 0.65 * guard
    return max(100, int(round(expected_hit * heroes * rounds * weight / 50) * 50))


def raid_combat_attacks(boss: dict[str, Any], combatants: int) -> int:
    """Prevent a six-swing boss from instantly chain-KOing a tiny roster.

    Its normal maximum remains for sufficiently large raids. Signature AoEs,
    telegraphs and scripted mechanics retain their original behavior.
    """
    original = max(0, int(boss.get("attacks_per_round", 1)))
    if not original:
        return 0
    party = max(1, int(combatants))
    return min(original, max(1, int(math.ceil(party * 0.75))))


def world_event_combat_hp(monster: dict[str, Any], *, combatants: int,
                          tier: str, threat: str, ordinary_party_hp: int) -> int:
    """Make live bosses longer than regular mobs, without 40-round elites.

    The event's already-scaled monster level is retained (including the +10
    maximum above the Guild's highest character). This only sets battle HP.
    """
    level = max(1, int(monster.get("level", 1)))
    party = max(1, int(combatants))
    heroes = max(1.3, party ** 0.94)
    elite = tier == "elite"
    rounds = 14 if elite else 10
    threat_weight = {
        "Dangerous": 0.90, "Severe": 1.0, "Extreme": 1.12,
        "Elite": 1.20, "Apex": 1.35,
    }.get(str(threat), 1.0)
    expected_hit = 60 + 4.5 * min(level, 110)
    budget = int(round(expected_hit * heroes * rounds * threat_weight))
    # At low levels some event templates downscale heavily. Cap the increase
    # relative to the ordinary party HP so new players can still participate.
    return max(1, min(budget, int(round(max(1, ordinary_party_hp) * 2.15))))


def raid_incoming_damage(boss: dict[str, Any], damage: int) -> int:
    """Apply a modest, deterministic armor budget only to boss HP (not adds)."""
    damage = max(0, int(damage))
    guard = max(0.0, min(0.25, float(boss.get("balance_guard", 0.0))))
    # Shells crack below 30% HP: players can feel a late push, not an HP wall.
    hp_ratio = int(boss.get("current_hp", 1)) / max(1, int(boss.get("max_hp", 1)))
    if hp_ratio <= 0.30:
        guard *= 0.65
    return max(1, int(damage * (1.0 - guard))) if damage else 0


def raid_outgoing_pressure(boss: dict[str, Any], *, raidwide: bool = False) -> float:
    """Boss personality drives attack threat; mechanics remain scripted."""
    attack = max(0.60, min(1.35, float(boss.get("balance_attack_weight", 1.0))))
    if raidwide:
        attack *= max(0.65, min(1.25, float(boss.get("balance_aoe_weight", 1.0))))
    return attack


def world_event_behavior(behavior: dict[str, Any], event: dict[str, Any],
                         combatants: int) -> dict[str, Any]:
    """Tune event signature ability, keeping the base monster/skill untouched."""
    from copy import deepcopy
    tuned = deepcopy(behavior)
    ability = tuned.get("ability")
    if not ability:
        return tuned
    ability["chance"] = min(0.38, max(0.0, float(ability.get("chance", 0.0))
                                              * float(event.get("special_frequency", 1.0))))
    power = float(ability.get("power", 1.0)) * float(event.get("special_power", 1.0))
    if ability.get("target") == "party":
        # AoE's total output grows naturally with party size. Prevent giant
        # crowds from receiving the same per-target burst as a four-person raid.
        power *= max(0.68, 1.0 - 0.025 * max(0, int(combatants) - 4))
    ability["power"] = max(0.20, min(1.55, power))
    for effect in ability.get("effects", []):
        if effect.get("type") == "status":
            chance = float(effect.get("chance", 1.0)) * float(event.get("status_frequency", 1.0))
            if effect.get("status") in {"stun", "silence"}:
                chance = min(chance, 0.22)
            effect["chance"] = min(0.65, max(0.0, chance))
    return tuned


def world_event_pressure(event: dict[str, Any], *, round_no: int) -> float:
    """A gentle soft enrage avoids infinite turtle while giving time to heal."""
    start = 16 if str(event.get("tier", "notorious")) == "elite" else 12
    later = max(0, int(round_no) - start)
    return float(event.get("combat_pressure", 1.0)) * (1.0 + min(0.30, 0.04 * later))

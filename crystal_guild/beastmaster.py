"""Beastmaster roster rules. Only server-verified Bestiary defeats can tame."""
from __future__ import annotations
from typing import Any
from math import isqrt

# Explicitly exclude bosses, quest guardians, and raid/event enemies. Expand the
# list after encounter-source QA; never tame arbitrary monster identifiers.
TAMEABLE_MONSTERS = frozenset({
    "wolf", "mandragora", "bat", "cactuar", "flan", "sahagin",
    "coeurl", "chimera", "sea_serpent", "behemoth", "crystal_wolf",
    "rift_hound", "rift_drake", "inferno_drake", "frost_behemoth",
    "tempest_roc", "master_coeurl", "red_dragon", "blue_dragon",
    "gold_dragon", "holy_dragon", "storm_dragon", "crystal_dragon",
})
MAX_COMPANIONS = 5
MIN_DEFEATS = 3
MAX_BOND_LEVEL = 20


def bond_level_from_xp(xp: int) -> int:
    """A slow, bounded rank progression. Rank 20 requires 9,025 Bond XP."""
    return min(MAX_BOND_LEVEL, 1 + isqrt(max(0, int(xp)) // 25))


def bond_progress(xp: int) -> dict[str, int]:
    xp = max(0, int(xp))
    rank = bond_level_from_xp(xp)
    start = 25 * (rank - 1) ** 2
    following = 25 * rank ** 2 if rank < MAX_BOND_LEVEL else start
    return {"rank": rank, "xp": xp, "xp_current": min(xp - start, following - start),
            "xp_next": following - start}


def companion_reward_xp(enemy_level: int) -> int:
    return min(200, max(20, 20 + max(1, int(enemy_level)) * 2))


def award_companion_bond(conn: Any, player_id: str, combat_meta: dict[str, Any],
                         event_key: str, enemy_level: int) -> dict[str, int] | None:
    """Award only for a verified damaging pet action during a won encounter.

    The caller owns the authoritative combat transaction and provides its real
    encounter key. A persisted receipt guarantees one reward per encounter.
    """
    if (combat_meta.get('job_id') != 'beastmaster'
            or int(combat_meta.get('_pet_assists', 0)) <= 0):
        return None
    pet = combat_meta.get('_tamed_companion') or {}
    species = str(pet.get('monster_id') or '')
    if species not in TAMEABLE_MONSTERS or not event_key or len(event_key) > 200:
        return None
    if not conn.execute('SELECT 1 FROM beastmaster_companions WHERE player_id=? AND monster_id=?',
                        (str(player_id),species)).fetchone():
        return None
    gained = companion_reward_xp(enemy_level)
    receipt = conn.execute("INSERT OR IGNORE INTO beastmaster_bond_receipts (event_key,player_id,monster_id,xp_awarded) VALUES (?,?,?,?)",
        (str(event_key),str(player_id),species,gained))
    if receipt.rowcount != 1:
        return None
    conn.execute('UPDATE beastmaster_companions SET bond_xp=bond_xp+?, bond_assists=bond_assists+1 WHERE player_id=? AND monster_id=?',
                 (gained,str(player_id),species))
    row = conn.execute('SELECT bond_xp FROM beastmaster_companions WHERE player_id=? AND monster_id=?',
                       (str(player_id),species)).fetchone()
    return {**bond_progress(row['bond_xp']), 'awarded':gained}



def is_tameable(monster_id: str, monsters: dict[str, Any]) -> bool:
    return monster_id in TAMEABLE_MONSTERS and monster_id in monsters


def pet_damage_bonus(companion: dict[str, Any] | None) -> float:
    """Small companion-specific contribution, before conditional Relic perks."""
    if not companion or str(companion.get("monster_id") or "") not in TAMEABLE_MONSTERS:
        return 0.0
    level = max(1, min(99, int(companion.get("level", 1))))
    return min(0.12, 0.02 + level * 0.0006 + max(0, min(19, int(companion.get("bond_rank", 1)) - 1)) * 0.002)

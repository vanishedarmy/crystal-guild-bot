"""Reusable primitives for Crystal Guild's active encounter loop.

Keep this module deliberately small and data-oriented.  The engine owns I/O,
player persistence and reward handling; this file owns battle vocabulary and
pure helpers.  Future combat edits should generally start with data files and
these helpers before adding more branching to ``engine.py``.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

from .balance import battle_ap_pool, battle_mp_pool



# Persistent resource sentinel used by full-character Rest.  A concrete MP/AP
# amount is shared across Jobs, whose maxima can differ.  -1 means the family
# is fully refreshed regardless of which Job is selected next; consumers must
# present it as that Job's current maximum.
FULL_RESOURCE_SENTINEL = -1

# ---------------------------------------------------------------------------
# Battle vocabulary
# ---------------------------------------------------------------------------
# Status ids are intentionally stable save-independent keys. Active encounter
# state is in memory only, so changing durations/magnitudes is safe between
# releases, but renaming ids requires updating active_abilities.json.
STATUS_LABELS = {
    "protect": "Protect",
    "taunt": "Taunt",
    "evade": "Evasion",
    "power_up": "Power Up",
    "focus": "Focus",
    "haste": "Haste",
    "regen": "Regen",
    "vulnerable": "Vulnerable",
    "weaken": "Weaken",
    "slow": "Slow",
    "stun": "Stun",
    "poison": "Poison",
    "silence": "Silence",
    "blind": "Blind",
}

HARMFUL_PLAYER_STATUSES = {"vulnerable", "weaken", "slow", "stun", "poison", "silence", "blind"}


def battle_mp(stats: dict[str, int]) -> int:
    """Return the bounded per-encounter MP pool from magical stats."""
    return battle_mp_pool(int(stats.get("mag", 0)), int(stats.get("spr", 0)))


def battle_ap(stats: dict[str, int]) -> int:
    """Return the bounded per-encounter AP pool from physical stats."""
    return battle_ap_pool(int(stats.get("str", 0)), int(stats.get("dex", 0)))


def job_resource_mode(job: dict[str, Any] | None) -> str:
    """Return the Job's configured Active Battle resource mode.

    Legacy data without ``resource_mode`` falls back to combat_type so old
    custom Job files remain usable after the MP/AP split.
    """
    if not job:
        return "none"
    configured = str(job.get("resource_mode", "")).lower().strip()
    if configured in {"mp", "ap", "dual"}:
        return configured
    combat_type = str(job.get("combat_type", "physical")).lower()
    return "mp" if combat_type == "magic" else "ap" if combat_type == "physical" else "dual"


def battle_resource_pools(stats: dict[str, int], job: dict[str, Any] | None) -> dict[str, int]:
    """Return the current Job's maximum MP/AP pools."""
    mode = job_resource_mode(job)
    return {
        "max_mp": battle_mp(stats) if mode in {"mp", "dual"} else 0,
        "max_ap": battle_ap(stats) if mode in {"ap", "dual"} else 0,
    }


def ability_resource(ability: dict[str, Any], job: dict[str, Any] | None = None) -> str:
    """Return ``mp`` or ``ap`` for an active ability with legacy fallback."""
    configured = str(ability.get("resource", "")).lower().strip()
    if configured in {"mp", "ap"}:
        return configured
    mode = job_resource_mode(job)
    return "mp" if mode == "mp" else "ap" if mode == "ap" else "mp"


def ability_cost(ability: dict[str, Any]) -> int:
    """Return the generic Active Battle resource cost.

    ``mp`` is accepted as a compatibility fallback for older custom ability
    catalogs, but shipping data uses the neutral ``cost`` field.
    """
    return max(0, int(ability.get("cost", ability.get("mp", 0))))


def normalize_action_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def unlocked_abilities(abilities: Iterable[dict[str, Any]], job_level: int) -> list[dict[str, Any]]:
    return [ability for ability in abilities if int(ability.get("level", 1)) <= int(job_level)]


def match_ability(abilities: Iterable[dict[str, Any]], query: str) -> tuple[dict[str, Any] | None, str]:
    """Match the longest ability id/name prefix and return leftover target text.

    This lets chat use natural commands such as ``!ability power break`` or
    ``!ability cure Cloud`` without requiring punctuation or ids.
    """
    normalized = normalize_action_text(query)
    if not normalized:
        return None, ""
    matches: list[tuple[int, dict[str, Any], str]] = []
    for ability in abilities:
        for key in {ability.get("id", ""), ability.get("name", ""), *(ability.get("aliases") or [])}:
            token = normalize_action_text(str(key))
            if not token:
                continue
            if normalized == token:
                matches.append((len(token), ability, ""))
            elif normalized.startswith(token + " "):
                matches.append((len(token), ability, normalized[len(token):].strip()))
    if not matches:
        return None, ""
    _, ability, remainder = max(matches, key=lambda row: row[0])
    return ability, remainder


def status_magnitude(statuses: dict[str, dict[str, Any]], status_id: str) -> float:
    row = statuses.get(status_id) or {}
    return float(row.get("magnitude", 0.0))


def has_status(statuses: dict[str, dict[str, Any]], status_id: str) -> bool:
    row = statuses.get(status_id)
    return bool(row and int(row.get("turns", 0)) > 0)


def apply_status(statuses: dict[str, dict[str, Any]], status_id: str, turns: int, magnitude: float = 0.0) -> None:
    """Apply/refresh a status, keeping the stronger magnitude and duration."""
    current = statuses.get(status_id) or {}
    statuses[status_id] = {
        "turns": max(int(current.get("turns", 0)), max(1, int(turns))),
        "magnitude": max(float(current.get("magnitude", 0.0)), float(magnitude)),
    }


def tick_statuses(statuses: dict[str, dict[str, Any]]) -> None:
    expired: list[str] = []
    for status_id, row in statuses.items():
        row["turns"] = int(row.get("turns", 0)) - 1
        if row["turns"] <= 0:
            expired.append(status_id)
    for status_id in expired:
        statuses.pop(status_id, None)


def cleanse(
    statuses: dict[str, dict[str, Any]],
    count: int = 1,
    *,
    allowed: set[str] | None = None,
) -> list[str]:
    """Remove harmful statuses, optionally restricted to a specific remedy set."""
    removed: list[str] = []
    for status_id in list(statuses):
        if status_id not in HARMFUL_PLAYER_STATUSES:
            continue
        if allowed is not None and status_id not in allowed:
            continue
        statuses.pop(status_id, None)
        removed.append(status_id)
        if len(removed) >= max(1, int(count)):
            break
    return removed


def format_statuses(statuses: dict[str, dict[str, Any]], *, limit: int = 4) -> str:
    visible = []
    for status_id, row in statuses.items():
        if int(row.get("turns", 0)) <= 0:
            continue
        label = STATUS_LABELS.get(status_id, status_id.replace("_", " ").title())
        visible.append(f"{label}:{int(row['turns'])}")
    if not visible:
        return "—"
    return ", ".join(visible[:limit])


def action_priority(action: dict[str, Any], actor_statuses: dict[str, dict[str, Any]]) -> int:
    """Lower values resolve first.

    Defending and recovery happen before attacks. Haste/Slow shift ordering but
    never grant or remove an action; Stun is handled by the authoritative round
    resolver so it can explicitly report the lost turn.
    """
    kind = action.get("kind")
    base = {"defend": 10, "item": 20, "ability": 30, "attack": 40}.get(kind, 50)
    if has_status(actor_statuses, "haste"):
        base -= 3
    if has_status(actor_statuses, "slow"):
        base += 3
    return base


def player_outgoing_status_multiplier(statuses: dict[str, dict[str, Any]]) -> float:
    """Return the shared outgoing-damage modifier from temporary statuses.

    The same status vocabulary is meaningful on both sides of the
    fight. Haste/Power Up help; Weaken/Slow reduce pressure. The lower bounds
    prevent stacked debuffs from reducing a player to effectively zero damage.
    """
    positive = 1.0 + status_magnitude(statuses, "power_up") + status_magnitude(statuses, "haste")
    weaken = max(0.65, 1.0 - status_magnitude(statuses, "weaken"))
    slow = max(0.80, 1.0 - status_magnitude(statuses, "slow") * 0.50)
    return max(0.50, positive * weaken * slow)


def incoming_vulnerability_multiplier(statuses: dict[str, dict[str, Any]]) -> float:
    """Return incoming-damage pressure from Vulnerable with a safety cap."""
    return 1.0 + min(0.35, max(0.0, status_magnitude(statuses, "vulnerable")))

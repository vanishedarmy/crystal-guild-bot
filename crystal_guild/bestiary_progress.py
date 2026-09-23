"""Bestiary discovery-stage computation and once-only mastery reconciliation.

The existing ``bestiary.defeats`` table remains the canonical kill history.
Research stages are derived from that count on read.  Only the permanent
mastery reward requires new state, stored in ``player_bestiary_mastery`` as an
idempotent receipt (one row per player/monster).
"""
from __future__ import annotations

from typing import Any


def _research_entry(data: Any, monster_id: str) -> dict[str, Any] | None:
    overlay = getattr(data, "bestiary_research", None) or {}
    entry = (overlay.get("entries") or {}).get(monster_id)
    return entry if isinstance(entry, dict) else None


def _milestones(data: Any, monster_id: str) -> list[dict[str, Any]]:
    entry = _research_entry(data, monster_id)
    if not entry:
        return []
    tiers = (getattr(data, "bestiary_research", None) or {}).get("tiers") or {}
    config = tiers.get(entry.get("category")) or {}
    rows = config.get("milestones") or []
    return [row for row in rows if isinstance(row, dict)]


def mastery_threshold(data: Any, monster_id: str) -> int | None:
    rows = _milestones(data, monster_id)
    if not rows:
        return None
    try:
        return int(rows[-1]["defeats"])
    except (KeyError, TypeError, ValueError):
        return None


def progress_for(data: Any, monster_id: str, defeats: int) -> dict[str, Any]:
    """Return server-authoritative research visibility for one base monster."""
    defeats = max(0, int(defeats or 0))
    entry = _research_entry(data, monster_id)
    rows = _milestones(data, monster_id)
    if not entry or not rows:
        return {
            "category": None,
            "family_id": None,
            "family": None,
            "stage": "undiscovered",
            "stage_index": 0,
            "stage_count": 0,
            "visible_fields": [],
            "next_milestone": None,
            "mastered": False,
            "mastery_threshold": None,
        }

    reached = [row for row in rows if defeats >= int(row.get("defeats", 0) or 0)]
    visible: list[str] = []
    for row in reached:
        for field in row.get("reveal") or []:
            if field not in visible:
                visible.append(str(field))
    next_row = next((row for row in rows if defeats < int(row.get("defeats", 0) or 0)), None)
    family_id = str(entry.get("family") or "")
    family_row = ((getattr(data, "bestiary_research", None) or {}).get("families") or {}).get(family_id) or {}
    threshold = int(rows[-1].get("defeats", 0) or 0)
    current = reached[-1] if reached else None
    return {
        "category": entry.get("category"),
        "family_id": family_id,
        "family": family_row.get("name") or family_id,
        "stage": str(current.get("key")) if current else "undiscovered",
        "stage_index": len(reached),
        "stage_count": len(rows),
        "visible_fields": visible,
        "next_milestone": (
            {
                "key": str(next_row.get("key")),
                "defeats": int(next_row.get("defeats", 0) or 0),
                "remaining": max(0, int(next_row.get("defeats", 0) or 0) - defeats),
            }
            if next_row else None
        ),
        "mastered": defeats >= threshold,
        "mastery_threshold": threshold,
    }


def reconcile_mastery(db: Any, data: Any, player_id: str | None = None) -> dict[str, int]:
    """Grant retroactive/new mastery receipts exactly once.

    This intentionally grants no loot/drop-rate modifier.  A receipt itself is
    the permanent Mastery Seal and carries one Research Point, making the
    aggregate point total deterministic and impossible to double-award.
    """
    sql = "SELECT player_id, monster_id, defeats FROM bestiary"
    params: tuple[Any, ...] = ()
    if player_id is not None:
        sql += " WHERE player_id=?"
        params = (str(player_id),)
    rows = db.all(sql, params)
    candidates: list[tuple[str, str, int]] = []
    for row in rows:
        monster_id = str(row["monster_id"])
        threshold = mastery_threshold(data, monster_id)
        defeats = int(row["defeats"] or 0)
        if threshold is not None and defeats >= threshold:
            candidates.append((str(row["player_id"]), monster_id, defeats))

    added = 0
    points_each = max(0, int(((data.bestiary_research.get("rewards") or {}).get("research_points", 1)) or 0))
    with db.tx(immediate=True) as conn:
        for pid, monster_id, defeats in candidates:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO player_bestiary_mastery(
                    player_id, monster_id, research_points, source_defeats
                ) VALUES (?,?,?,?)
                """,
                (pid, monster_id, points_each, defeats),
            )
            added += max(0, int(cursor.rowcount or 0))
    return {"eligible": len(candidates), "masteries_added": added, "research_points_added": added * points_each}

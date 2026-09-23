"""Read-only Personal Records projection (Records & Moments, Step 1).

This module does not award achievements, mutate rows, or infer absent history.
A record with ``tracking_required=True`` is deliberately unavailable until a
future event settlement writes the evidence needed for it.
"""
from __future__ import annotations

import json
from typing import Any

from .world_events import WORLD_EVENTS_BY_ID


RECORD_SPECS = (
    ("highest_hit", "Best Single Hit", "combat", "damage", "tracked"),
    ("closest_victory", "Closest Victory", "combat", "hp", "new_event"),
    ("biggest_purchase", "Biggest Shopping Spree", "economy", "gil", "historical"),
    ("biggest_expense", "Largest Single Gil Expense", "economy", "gil", "historical"),
    ("biggest_sale", "Biggest Sale", "economy", "gil", "historical"),
    ("highest_world_event_threat", "Highest World Event Threat", "world_events", "threat", "historical"),
    ("closest_world_event", "Narrowest World Event Victory", "world_events", "hp", "new_event"),
    ("longest_venture", "Longest Completed Venture", "ventures", "seconds", "new_event"),
    ("biggest_venture_haul", "Biggest Venture Haul", "ventures", "gil", "new_event"),
    ("biggest_raid_payout", "Biggest Raid Gil Payout", "raids", "gil", "historical"),
    ("fastest_trial", "Fastest Trial Clear", "raids", "rounds", "historical"),
    ("biggest_saucer_payout", "Biggest Saucer Payout", "gold_saucer", "mgp", "historical"),
    ("biggest_saucer_loss", "Biggest Single Saucer Loss", "gold_saucer", "mgp", "historical"),
    ("longest_saucer_loss_streak", "Longest Saucer Losing Streak", "gold_saucer", "plays", "historical"),
    ("longest_cactpot_loss_streak", "Longest Cactpot Losing Streak", "gold_saucer", "plays", "historical"),
)

CATEGORY_LABELS = {
    "combat": "Combat",
    "economy": "Economy",
    "world_events": "World Events",
    "ventures": "Ventures",
    "raids": "Raids & Trials",
    "gold_saucer": "Gold Saucer",
}
_SAUCER_PAID_GAMES = frozenset({"mini_cactpot", "slots", "monster_toss", "chocobo_racing", "triple_triad"})
_SHOP_SOURCES = frozenset({"shop", "portal_shop", "trading_post_buy"})
_SALE_SOURCES = frozenset({"sell", "portal_sell", "trading_post_sale"})
_THREAT_ORDER = {"Dangerous": 1, "Severe": 2, "Extreme": 3}


def _record(spec: tuple[str, str, str, str, str]) -> dict[str, Any]:
    record_id, title, category, unit, coverage = spec
    return {
        "id": record_id,
        "title": title,
        "category": category,
        "unit": unit,
        "coverage": coverage,
        "status": "awaiting_tracking" if coverage == "new_event" else "not_set",
        "value": None,
        "context": None,
        "occurred_at": None,
    }


def _set(target: dict[str, dict[str, Any]], key: str, value: int | str,
         *, context: dict[str, Any] | None = None, occurred_at: int | str | None = None) -> None:
    row = target[key]
    row["status"] = "recorded"
    row["value"] = value
    row["context"] = context
    row["occurred_at"] = occurred_at


def _loss_streak(rows: list[dict[str, Any]], game: str | None = None) -> tuple[int, dict[str, Any] | None]:
    """Count strictly consecutive losses. Ties keep the first achieved streak."""
    best = 0
    current = 0
    current_last: dict[str, Any] | None = None
    winner: dict[str, Any] | None = None
    for row in rows:
        if game is not None and row["game"] != game:
            continue
        if row.get("_invalid"):
            current = 0
            continue
        # Unpaid attractions are not a gambling loss (or a free way to break a streak).
        if int(row["wager"]) <= 0:
            continue
        if int(row["payout"]) < int(row["wager"]):
            current += 1
            current_last = row
            if current > best:
                best = current
                winner = current_last
        else:
            # A draw breaks an unbroken sequence, just as an actual win does.
            current = 0
    if not best or winner is None:
        return 0, None
    return best, {"last_game": winner["game"], "last_history_id": winner["id"]}


def project_personal_records(conn: Any, player_id: str, data: Any,
                             stats: dict[str, int]) -> dict[str, Any]:
    """Project saved, per-player evidence without fabricating earlier Moments."""
    records = {spec[0]: _record(spec) for spec in RECORD_SPECS}
    best_hit = max(0, int(stats.get("best_hit", 0) or 0))
    if best_hit:
        matching_monster = conn.execute(
            "SELECT monster_id FROM player_monster_records "
            "WHERE player_id=? AND best_hit=? ORDER BY monster_id LIMIT 1",
            (player_id, best_hit),
        ).fetchone()
        monster = data.monsters.get(matching_monster["monster_id"]) if matching_monster else None
        context = ({"monster": monster["name"] if monster else matching_monster["monster_id"]}
                   if matching_monster else None)
        _set(records, "highest_hit", best_hit, context=context)

    # One debit/credit is a single transaction, not the total of an entire visit.
    # Restrict 'purchase' to actual storefront sources; fees and crafting are expenses.
    money = conn.execute(
        "SELECT id, amount, source, created_at FROM transactions "
        "WHERE player_id=? AND kind='gil' AND amount<>0 ORDER BY id",
        (player_id,),
    ).fetchall()
    for row in money:
        amount = int(row["amount"])
        source = str(row["source"])
        if amount < 0:
            value = -amount
            if (records["biggest_expense"]["value"] or 0) < value:
                _set(records, "biggest_expense", value, context={"source": source},
                     occurred_at=row["created_at"])
            if source in _SHOP_SOURCES and (records["biggest_purchase"]["value"] or 0) < value:
                _set(records, "biggest_purchase", value, context={"source": source},
                     occurred_at=row["created_at"])
        elif source in _SALE_SOURCES and (records["biggest_sale"]["value"] or 0) < amount:
            _set(records, "biggest_sale", amount, context={"source": source},
                 occurred_at=row["created_at"])
        elif source.startswith("boss:") and (records["biggest_raid_payout"]["value"] or 0) < amount:
            boss_id = source.partition(":")[2]
            boss = data.bosses.get(boss_id)
            # Trials have their own records; don't call their rewards Raid payouts.
            if boss and str(boss.get("encounter_type") or "").lower() != "trial":
                _set(records, "biggest_raid_payout", amount,
                     context={"boss_id": boss_id, "boss": boss["name"]},
                     occurred_at=row["created_at"])

    world_rows = conn.execute(
        "SELECT world_event_id, clears, last_cleared_at FROM player_world_event_clears "
        "WHERE player_id=? AND clears>0 ORDER BY world_event_id", (player_id,),
    ).fetchall()
    known = [(WORLD_EVENTS_BY_ID[row["world_event_id"]], row) for row in world_rows
             if row["world_event_id"] in WORLD_EVENTS_BY_ID]
    if known:
        max_rank = max(_THREAT_ORDER.get(event["threat"], 0) for event, _ in known)
        highest = [(event, row) for event, row in known
                   if _THREAT_ORDER.get(event["threat"], 0) == max_rank]
        if highest:
            _set(records, "highest_world_event_threat", highest[0][0]["threat"],
                 context={"events": [event["name"] for event, _ in highest],
                          "event_ids": [event["id"] for event, _ in highest],
                          "meaning": "published_threat_tier_not_dynamic_boss_level"})

    # Only trials with a genuine historical fastest-round sample qualify.
    fastest: tuple[int, str] | None = None
    for boss_id, boss in data.bosses.items():
        if str(boss.get("encounter_type") or "").lower() != "trial":
            continue
        value = int(stats.get(f"trial_{boss_id}_fastest_rounds", 0) or 0)
        cleared = conn.execute(
            "SELECT clears FROM player_boss_clears WHERE player_id=? AND boss_id=?",
            (player_id, boss_id),
        ).fetchone()
        if value > 0 and cleared and int(cleared["clears"]) > 0:
            if fastest is None or value < fastest[0]:
                fastest = (value, boss_id)
    if fastest:
        _set(records, "fastest_trial", fastest[0],
             context={"boss_id": fastest[1], "boss": data.bosses[fastest[1]]["name"]})

    # Gold Saucer history was added in local schema 11. Use resolved paid rounds.
    history = conn.execute(
        "SELECT id, game, wager, payout, created_at FROM gold_saucer_history "
        "WHERE player_id=? ORDER BY created_at, id", (player_id,),
    ).fetchall()
    paid = []
    for row in history:
        if row["game"] not in _SAUCER_PAID_GAMES:
            continue
        try:
            wager, payout = int(row["wager"]), int(row["payout"])
        except (TypeError, ValueError, OverflowError):
            # Skip a damaged historical row without taking the whole Records
            # page down or counting it toward a verified loss streak. Retain a
            # reset sentinel so losses either side are never joined together.
            paid.append({**dict(row), "_invalid": True})
            continue
        if wager <= 0 or payout < 0:
            if payout < 0:
                paid.append({**dict(row), "_invalid": True})
            continue
        paid.append({**dict(row), "wager": wager, "payout": payout})
    for row in paid:
        if row.get("_invalid"):
            continue
        payout = int(row["payout"])
        wager = int(row["wager"])
        if payout > (records["biggest_saucer_payout"]["value"] or 0):
            _set(records, "biggest_saucer_payout", payout,
                 context={"game": row["game"], "history_id": row["id"]},
                 occurred_at=row["created_at"])
        if wager > payout and wager - payout > (records["biggest_saucer_loss"]["value"] or 0):
            _set(records, "biggest_saucer_loss", wager - payout,
                 context={"game": row["game"], "history_id": row["id"]},
                 occurred_at=row["created_at"])
    for key, game in (("longest_saucer_loss_streak", None),
                      ("longest_cactpot_loss_streak", "mini_cactpot")):
        value, context = _loss_streak(paid, game)
        if value:
            _set(records, key, value, context=context)

    # These four records did not have reliable historical evidence before
    # schema 23. Show only actual post-upgrade, server-settled samples.
    for row in conn.execute(
        "SELECT record_id,best_value,event_key,context_json,occurred_at "
        "FROM player_record_events WHERE player_id=?", (player_id,),
    ).fetchall():
        if row["record_id"] in records and records[row["record_id"]]["coverage"] == "new_event":
            try:
                parsed = json.loads(row["context_json"] or "{}")
                context = parsed if isinstance(parsed, dict) else None
            except (ValueError, TypeError):
                # Preserve the verified numeric best. Corrupt optional display
                # context should not make the entire player's Records unavailable.
                context = None
            _set(records, row["record_id"], int(row["best_value"]),
                 context=context, occurred_at=row["occurred_at"])

    return {
        "categories": [{"id": category, "title": title} for category, title in CATEGORY_LABELS.items()],
        "records": list(records.values()),
        "scope_note": "Saved history only. Unrecorded battle outcomes and earlier event details cannot be reconstructed.",
    }

"""Guild Initiatives 1.9.3: deterministic rotations on top of Fellowship's event receipts.

Do not call progress_event before fellowship_events successfully inserts its event_key.
The caller must be inside the same Database.tx() as that insertion and the
original authoritative gameplay settlement. No client may write these tables.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from .fellowship import weekly_period_key

# One objective from each category is available per rotation. Alternate variants
# make objectives rotate without a random seed or new per-player state.
CONTRACTS = {
    "combat": (
        {"id": "guild_monsters", "name": "Monster Suppression", "description": "Defeat 30 monsters together.", "activities": ("combat_victory",), "target": 30, "reward": {"gil": 300}},
        {"id": "guild_hunts", "name": "Hunt Patrol", "description": "Win 12 Hunts together.", "activities": ("hunt_win",), "target": 12, "reward": {"gil": 350}},
    ),
    "economy": (
        {"id": "guild_crafts", "name": "Supply the Workshop", "description": "Craft 24 items together.", "activities": ("craft",), "target": 24, "reward": {"gil": 220, "item_id": "iron_ore", "quantity": 2}},
        {"id": "guild_forges", "name": "Hammer and Anvil", "description": "Complete 10 Forge upgrades together.", "activities": ("forge",), "target": 10, "reward": {"gil": 260, "item_id": "iron_ore", "quantity": 3}},
    ),
    "activity": (
        {"id": "guild_ventures", "name": "Ventures for the Guild", "description": "Complete 8 Ventures together.", "activities": ("venture_complete",), "target": 8, "reward": {"gil": 250, "item_id": "potion", "quantity": 2}},
        {"id": "guild_expeditions", "name": "The Open Road", "description": "Complete 5 Expeditions together.", "activities": ("expedition_complete",), "target": 5, "reward": {"gil": 300, "item_id": "potion", "quantity": 2}},
    ),
}

DAILIES = {
    "combat": (
        {"id": "daily_monsters", "name": "Monster Patrol", "description": "Defeat 5 monsters.", "activities": ("combat_victory",), "target": 5, "reward": {"gil": 200}},
        {"id": "daily_hunts", "name": "Bounty Hunter", "description": "Win 2 Hunts.", "activities": ("hunt_win",), "target": 2, "reward": {"gil": 230}},
    ),
    "economy": (
        {"id": "daily_crafts", "name": "A Little Craftsmanship", "description": "Craft 3 items.", "activities": ("craft",), "target": 3, "reward": {"gil": 150, "item_id": "iron_ore", "quantity": 1}},
        {"id": "daily_forges", "name": "Forge Duty", "description": "Complete one Forge upgrade.", "activities": ("forge",), "target": 1, "reward": {"gil": 160, "item_id": "iron_ore", "quantity": 1}},
    ),
    "activity": (
        {"id": "daily_ventures", "name": "A Day's Adventure", "description": "Complete 2 Ventures.", "activities": ("venture_complete",), "target": 2, "reward": {"gil": 200, "item_id": "potion", "quantity": 1}},
        {"id": "daily_expedition", "name": "Find New Horizons", "description": "Complete an Expedition.", "activities": ("expedition_complete",), "target": 1, "reward": {"gil": 220, "item_id": "potion", "quantity": 1}},
    ),
}

WEEKLIES = {
    "combat": (
        {"id": "weekly_monsters", "name": "Experienced Hunter", "description": "Defeat 35 monsters.", "activities": ("combat_victory",), "target": 35, "reward": {"gil": 1200}},
        {"id": "weekly_hunts", "name": "Mark of the Hunter", "description": "Win 10 Hunts.", "activities": ("hunt_win",), "target": 10, "reward": {"gil": 1300}},
    ),
    "economy": (
        {"id": "weekly_crafts", "name": "Workshop Commission", "description": "Craft 18 items.", "activities": ("craft",), "target": 18, "reward": {"gil": 700, "item_id": "mythril_ore", "quantity": 2}},
        {"id": "weekly_forges", "name": "The Guild Smith", "description": "Complete 5 Forge upgrades.", "activities": ("forge",), "target": 5, "reward": {"gil": 750, "item_id": "mythril_ore", "quantity": 2}},
    ),
    "activity": (
        {"id": "weekly_ventures", "name": "The Adventurer's Path", "description": "Complete 10 Ventures.", "activities": ("venture_complete",), "target": 10, "reward": {"gil": 650, "gear": True}},
        {"id": "weekly_expeditions", "name": "Wayfarer's Commission", "description": "Complete 7 Expeditions.", "activities": ("expedition_complete",), "target": 7, "reward": {"gil": 650, "gear": True}},
    ),
}


def daily_period_key(timestamp: float | None = None) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat() if timestamp is not None else datetime.now(timezone.utc).date().isoformat()


def selected(catalog: dict[str, tuple[dict, ...]], period: str) -> list[dict[str, Any]]:
    """Stable independent choice for each category; no RNG state required."""
    result = []
    for category, variants in catalog.items():
        digest = hashlib.sha256(f"guild-initiatives:1:{period}:{category}".encode()).digest()
        result.append({**variants[int.from_bytes(digest[:4], "big") % len(variants)], "category": category})
    return result


def _gear_reward(conn: Any, data: Any, player_id: str, period: str, objective_id: str) -> str | None:
    player = conn.execute("SELECT level FROM players WHERE twitch_id=?", (player_id,)).fetchone()
    if not player:
        return None
    level = max(1, int(player["level"]))
    # Shop-stock equipment only: no relics, exclusives or high-tier bypasses.
    options = sorted(item["id"] for item in data.items.values()
                     if item.get("shop") and item.get("type") in {"weapon", "armor", "accessory"}
                     and int(item.get("min_level") or 1) <= level
                     and int(item.get("min_level") or 1) >= max(1, level - 12)
                     and int(item.get("price") or 0) <= 3500)
    if not options:
        return None
    digest = hashlib.sha256(f"{player_id}:{period}:{objective_id}:gear".encode()).digest()
    return options[int.from_bytes(digest[:8], "big") % len(options)]


def _grant(conn: Any, data: Any, player_id: str, scope: str, period: str, definition: dict[str, Any]) -> bool:
    """Grant exactly once in the caller's event transaction; receipt precedes money."""
    oid = definition["id"]
    inserted = conn.execute(
        "INSERT OR IGNORE INTO guild_initiative_rewards(scope,period_key,objective_id,player_id) VALUES (?,?,?,?)",
        (scope, period, oid, player_id),
    ).rowcount
    if not inserted:
        return False
    reward = definition["reward"]
    gil = int(reward.get("gil", 0))
    source = f"guild_initiative:{scope}:{period}:{oid}"
    if gil:
        conn.execute("UPDATE players SET gil=gil+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (gil, player_id))
        conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,?)", (player_id, gil, source))
    item_id = str(reward.get("item_id") or "")
    quantity = int(reward.get("quantity", 0))
    if reward.get("gear"):
        item_id = _gear_reward(conn, data, player_id, period, oid)
        if not item_id:
            item_id, quantity = "mythril_ore", 2
        else:
            quantity = 1
    if item_id and quantity > 0 and item_id in data.items:
        conn.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) "
                     "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (player_id, item_id, quantity))
        conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'item',?,?,?)", (player_id, item_id, quantity, source))
    return True


def _prune_expired(conn: Any, *, timestamp: float | None = None) -> None:
    """Bound objective storage, at most once per UTC week, in the event transaction.

    Audit transactions and the authoritative fellowship_events receipt log are
    deliberately never pruned. Recent progress and rewards outlive resets to
    ensure delayed syncs cannot erase evidence of completed objectives.
    """
    now = datetime.fromtimestamp(timestamp, timezone.utc) if timestamp is not None else datetime.now(timezone.utc)
    week = weekly_period_key(now.timestamp())
    if not conn.execute("INSERT OR IGNORE INTO guild_initiative_maintenance(week_key) VALUES (?)", (week,)).rowcount:
        return
    old_day = (now - timedelta(days=45)).date().isoformat()
    old_week = weekly_period_key((now - timedelta(weeks=18)).timestamp())
    conn.execute("DELETE FROM guild_initiative_player_progress WHERE (scope='daily' AND period_key<?) OR (scope='weekly' AND period_key<?)", (old_day, old_week))
    conn.execute("DELETE FROM guild_initiative_contributions WHERE period_key<?", (old_week,))
    conn.execute("DELETE FROM guild_initiative_contracts WHERE period_key<?", (old_week,))
    conn.execute("DELETE FROM guild_initiative_rewards WHERE (scope='daily' AND period_key<?) OR (scope IN ('weekly','contract') AND period_key<?)", (old_day, old_week))
    conn.execute("DELETE FROM guild_initiative_maintenance WHERE week_key<?", (week,))


def progress_event(conn: Any, data: Any, player_id: str, activity_semantics: set[str], amount: int,
                   *, timestamp: float | None = None) -> list[str]:
    """Call exclusively after the authoritative fellowship_events unique insert.

    This function never creates or trusts a client event. It advances each
    category at most once per verified event even when semantic aliases overlap.
    """
    if not player_id or amount < 1:
        return []
    _prune_expired(conn, timestamp=timestamp)
    daily, weekly = daily_period_key(timestamp), weekly_period_key(timestamp)
    notes: list[str] = []
    for scope, period, catalog in (("contract", weekly, CONTRACTS),
                                    ("daily", daily, DAILIES),
                                    ("weekly", weekly, WEEKLIES)):
        for definition in selected(catalog, period):
            if not activity_semantics.intersection(definition["activities"]):
                continue
            oid, target = definition["id"], definition["target"]
            if scope == "contract":
                conn.execute("INSERT OR IGNORE INTO guild_initiative_contracts(period_key,objective_id,target) VALUES (?,?,?)",
                             (period, oid, target))
                row = conn.execute("SELECT progress,completed_at FROM guild_initiative_contracts WHERE period_key=? AND objective_id=?", (period, oid)).fetchone()
                if row["completed_at"]:
                    continue
                delta = min(amount, target - int(row["progress"]))
                if delta < 1:
                    continue
                conn.execute("UPDATE guild_initiative_contracts SET progress=progress+?, completed_at=CASE WHEN progress+?>=target THEN CURRENT_TIMESTAMP ELSE NULL END WHERE period_key=? AND objective_id=?",
                             (delta, delta, period, oid))
                conn.execute("INSERT INTO guild_initiative_contributions(period_key,objective_id,player_id,amount) VALUES (?,?,?,?) "
                             "ON CONFLICT(period_key,objective_id,player_id) DO UPDATE SET amount=amount+excluded.amount", (period, oid, player_id, delta))
                if int(row["progress"]) + delta >= target:
                    # Freeze the eligible membership at completion: newly
                    # recruited players cannot retroactively collect the payout.
                    members = conn.execute("SELECT m.player_id FROM fellowship_members m JOIN players p ON p.twitch_id=m.player_id ORDER BY m.player_id").fetchall()
                    for member in members:
                        _grant(conn, data, str(member["player_id"]), scope, period, definition)
                    conn.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'guild_contract',?,?)",
                                 (definition["name"], len(members)))
                    notes.append(f"FELLOWSHIP CONTRACT COMPLETE — {definition['name']}; {len(members)} member rewards delivered.")
            else:
                conn.execute("INSERT OR IGNORE INTO guild_initiative_player_progress(player_id,scope,period_key,objective_id,target) VALUES (?,?,?,?,?)",
                             (player_id, scope, period, oid, target))
                row = conn.execute("SELECT progress,completed_at FROM guild_initiative_player_progress WHERE player_id=? AND scope=? AND period_key=? AND objective_id=?", (player_id, scope, period, oid)).fetchone()
                if row["completed_at"]:
                    continue
                delta = min(amount, target - int(row["progress"]))
                if delta < 1:
                    continue
                conn.execute("UPDATE guild_initiative_player_progress SET progress=progress+?,completed_at=CASE WHEN progress+?>=target THEN CURRENT_TIMESTAMP ELSE NULL END WHERE player_id=? AND scope=? AND period_key=? AND objective_id=?",
                             (delta, delta, player_id, scope, period, oid))
                if int(row["progress"]) + delta >= target and _grant(conn, data, player_id, scope, period, definition):
                    notes.append(f"GUILD BOARD — {definition['name']} complete; rewards delivered.")
    return notes


def contract_view(conn: Any, *, timestamp: float | None = None) -> dict[str, Any]:
    period = weekly_period_key(timestamp)
    rows = {str(r["objective_id"]): r for r in conn.execute("SELECT * FROM guild_initiative_contracts WHERE period_key=?", (period,))}
    entries = []
    for definition in selected(CONTRACTS, period):
        row = rows.get(definition["id"])
        contributors = []
        if row:
            contributors = [{"display_name": r["display_name"], "amount": int(r["amount"])} for r in conn.execute(
                "SELECT p.display_name,c.amount FROM guild_initiative_contributions c JOIN players p ON p.twitch_id=c.player_id "
                "WHERE c.period_key=? AND c.objective_id=? ORDER BY c.amount DESC,p.display_name LIMIT 5", (period, definition["id"]))]
        entries.append({**definition, "progress": int(row["progress"]) if row else 0,
                        "complete": bool(row and row["completed_at"]), "completed_at": row["completed_at"] if row else None,
                        "contributors": contributors})
    return {"period": period, "objectives": entries, "completed": sum(e["complete"] for e in entries), "total": len(entries)}


def board_view(conn: Any, player_id: str, *, timestamp: float | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for scope, period, catalog in (("daily", daily_period_key(timestamp), DAILIES),
                                    ("weekly", weekly_period_key(timestamp), WEEKLIES)):
        rows = {str(r["objective_id"]): r for r in conn.execute(
            "SELECT * FROM guild_initiative_player_progress WHERE player_id=? AND scope=? AND period_key=?", (player_id, scope, period))}
        items = []
        for definition in selected(catalog, period):
            row = rows.get(definition["id"])
            reward = dict(definition["reward"])
            if reward.get("gear"):
                reward = {"gil": reward["gil"], "gear": True}
            items.append({**definition, "reward": reward, "progress": int(row["progress"]) if row else 0,
                          "complete": bool(row and row["completed_at"]),
                          "completed_at": row["completed_at"] if row else None})
        result[scope] = {"period": period, "objectives": items,
                         "completed": sum(e["complete"] for e in items), "total": len(items)}
    return result

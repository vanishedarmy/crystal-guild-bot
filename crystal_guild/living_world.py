"""Living World LW-1: durable, offline-first Verdant Wilds exploration."""
from __future__ import annotations

import re
import sqlite3
import time
from typing import Any

SLUG = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
SOURCES = frozenset({"solo_venture", "stream_venture", "expedition", "hunt", "world_event", "discovery", "fellowship"})
REGION = "verdant_wilds"


def validate_catalog(regions: list[dict[str, Any]], config: dict[str, Any], art: dict[str, Any], discoveries: list[dict[str, Any]] | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(regions, list) or len(regions) != 8:
        errors.append("Living World requires exactly eight ordered regions")
        regions = regions if isinstance(regions, list) else []
    seen: set[str] = set()
    for i, region in enumerate(regions):
        if not isinstance(region, dict):
            errors.append(f"Living World region {i}: must be an object")
            continue
        key = region.get("id")
        if not isinstance(key, str) or not SLUG.fullmatch(key) or key in seen:
            errors.append(f"Living World region {i}: invalid or duplicate ID")
        else:
            seen.add(key)
        if region.get("order") != i + 1:
            errors.append(f"Living World region {i}: invalid ordering")
        if not isinstance(region.get("name"), str) or not region["name"].strip():
            errors.append(f"Living World region {i}: missing name")
    if not isinstance(config, dict):
        return errors + ["Living World config must be an object"]
    if config.get("offline_completion_required") is not True or config.get("fellowship_is_optional") is not True:
        errors.append("Living World progression must be completable offline without mandatory Fellowship")
    if set(config.get("activity_sources", [])) != SOURCES:
        errors.append("Living World activity-source registry does not match approved sources")
    flags = config.get("feature_flags") or {}
    if not isinstance(flags, dict):
        errors.append("Living World feature flags must be an object")
        flags = {}
    enabled = config.get("milestone") == "LW-1"
    expected = {"enabled": enabled, "playable": enabled, "venture_hooks_enabled": enabled, "direct_reward_grants_enabled": enabled,
                "world_event_hooks_enabled": False}
    for key, value in expected.items():
        if config.get(key) is not value:
            errors.append(f"Living World {key} must equal {value} for {config.get('milestone')}")
    for flag, value in {"atlas_ui": enabled, "exploration": enabled, "bestiary": False,
                        "world_events": False, "aftermaths": False, "fellowship_contracts": False}.items():
        if flags.get(flag) is not value:
            errors.append(f"Living World flag {flag} invalid for {config.get('milestone')}")
    if enabled and config.get("intro_source_region") != "greenwind_plains":
        errors.append("Verdant Wilds must map to the existing Greenwind Plains travel region")
    slots = art.get("slots", []) if isinstance(art, dict) else []
    paths = [s.get("path") for s in slots if isinstance(s, dict)]
    if len(paths) != 20 or len(paths) != len(set(paths)) or any(not isinstance(p, str) or not p.startswith("living-world/") or ".." in p for p in paths):
        errors.append("Living World artwork slots invalid (expected 20 unique safe paths)")
    if enabled:
        if not isinstance(discoveries, list) or len(discoveries) != 4:
            errors.append("LW-1 requires four Verdant Wilds discoveries")
        else:
            ids: set[str] = set()
            for row in discoveries:
                if (not isinstance(row, dict) or not SLUG.fullmatch(str(row.get("id", ""))) or row.get("id") in ids
                        or row.get("region_id") != REGION or not isinstance(row.get("name"), str)
                        or not row.get("name") or not isinstance(row.get("description"), str)
                        or not row.get("description") or type(row.get("reward_gil")) is not int
                        or not 0 <= row["reward_gil"] <= 250):
                    errors.append("Invalid or duplicate Verdant Wilds discovery")
                if isinstance(row, dict):
                    ids.add(row.get("id"))
    return errors


def receipt_once(db: Any, player_id: str, source: str, activity_id: str) -> bool:
    """Unique receipt. Caller must compose this with progress/reward in one db.tx."""
    if source not in SOURCES:
        raise ValueError("Unknown Living World activity source")
    if not isinstance(activity_id, str) or not (1 <= len(activity_id) <= 180) or not activity_id.strip():
        raise ValueError("A non-empty stable activity ID (max 180 chars) is required")
    if not isinstance(player_id, str) or not player_id.strip():
        raise ValueError("Player ID required")
    with db.tx() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO lw_activity_receipts (player_id,source,activity_id,received_at) VALUES (?,?,?,?)",
            (player_id, source, activity_id, int(time.time())),
        )
        return cursor.rowcount == 1


def record_solo_bank(db: Any, player_id: str, expedition: dict[str, Any], discoveries: list[dict[str, Any]], *,
                     source_region: str = "greenwind_plains") -> dict[str, Any] | None:
    """Award at most one unique discovery for a banked, cleared Greenwind Solo Venture.

    Deterministic progression (no combat/loot RNG perturbation); never claim
    at start, retreat, or defeat. Receipt, discovery and currency are atomic.
    """
    if expedition.get("region_id") != source_region or expedition.get("status") != "choice":
        return None
    history = expedition.get("history") or []
    if not any(x.get("type") in ("victory", "treasure") for x in history if isinstance(x, dict)):
        return None
    activity_id = str(expedition.get("lw_activity_id") or f"legacy:{player_id}:{int(expedition.get('started_at',0))}")
    now = int(time.time())
    with db.tx(immediate=True) as conn:
        known = {str(row[0]) for row in conn.execute("SELECT discovery_id FROM lw_discoveries WHERE player_id=? AND region_id=?", (player_id,REGION))}
        chosen = next((row for row in discoveries if row["id"] not in known), None)
        if chosen is None:
            return None
        if not receipt_once(db, str(player_id), "solo_venture", activity_id):
            return None
        conn.execute("INSERT INTO lw_discoveries(player_id,discovery_id,region_id,source,discovered_at) VALUES (?,?,?,?,?)",
                     (player_id, chosen["id"], REGION, "solo_venture", now))
        count = len(known)+1
        conn.execute("INSERT INTO lw_region_progress(player_id,region_id,progress,updated_at) VALUES (?,?,?,?) "
                     "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=excluded.progress,updated_at=excluded.updated_at",
                     (player_id, REGION, count*25, now))
        award = max(0,int(chosen["reward_gil"]))
        if award:
            unique_reward = f"lw1:discovery:{chosen['id']}"
            result = conn.execute("INSERT OR IGNORE INTO lw_reward_receipts(player_id,reward_key,source,granted_at) VALUES (?,?,?,?)",
                                  (player_id,unique_reward,"discovery",now))
            if result.rowcount:
                conn.execute("UPDATE players SET gil=gil+? WHERE twitch_id=?",(award,player_id))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,'living_world_discovery')",(player_id,award))
            else:
                award=0
        return {"id": chosen["id"], "name": chosen["name"], "description": chosen["description"],
                "reward_gil": award, "discovered_count": count, "total": len(discoveries)}


def empty_snapshot(regions: list[dict[str, Any]], *, sync_pending: bool = False) -> dict[str, Any]:
    return {"milestone":"LW-0","enabled":False,"playable":False,"sync_pending":bool(sync_pending),
            "offline_completion_required":True,"fellowship_is_optional":True,
            "regions":[{"id":r["id"],"name":r["name"],"order":r["order"],"biome":r.get("biome",""),
                        "status":"locked","unlocked":False,"discovery_count":0,"progress":0} for r in regions],
            "summary":{"regions_unlocked":0,"discoveries":0,"world_events_active":0},"events":[]}


def player_snapshot(conn: sqlite3.Connection, player_id: str, regions: list[dict[str, Any]],
                    config: dict[str, Any] | None = None, discoveries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Read-only public projection; no private player IDs or planned rewards in undiscovered entries."""
    result = empty_snapshot(regions)
    enabled = (config or {}).get("milestone") == "LW-1" and (config or {}).get("enabled") is True
    result.update(milestone="LW-1" if enabled else "LW-0",enabled=enabled,playable=enabled)
    try:
        rows=conn.execute("SELECT region_id,COUNT(*) FROM lw_discoveries WHERE player_id=? GROUP BY region_id",(player_id,)).fetchall()
        counts={str(r[0]):int(r[1]) for r in rows}
        seen={str(r[0]) for r in conn.execute("SELECT discovery_id FROM lw_discoveries WHERE player_id=? AND region_id=?",(player_id,REGION)).fetchall()}
        for entry in result["regions"]:
            entry["discovery_count"]=counts.get(entry["id"],0)
            if enabled and entry["id"]==REGION:
                entry.update(status="completed" if len(seen)==len(discoveries or []) and seen else "available",
                             unlocked=True,progress=min(100,len(seen)*25),total_discoveries=len(discoveries or []),
                             banner="/living-world/regions/verdant_wilds/banner.webp",
                             thumbnail="/living-world/regions/verdant_wilds/thumbnail.webp",
                             source_region_name="Greenwind Plains",source_region_id="greenwind_plains",
                             discoveries=[{"id":r["id"],"name":r["name"] if r["id"] in seen else "Undiscovered location",
                                           "description":r["description"] if r["id"] in seen else "Complete a Solo Venture in Greenwind Plains to discover this place.",
                                           "discovered":r["id"] in seen} for r in discoveries or []])
        result["summary"].update(regions_unlocked=1 if enabled else 0, discoveries=sum(counts.values()))
        result["how_to_explore"]="Travel to Greenwind Plains, clear a Solo Venture stage, then return safely to the Guild. Each successfully banked venture reveals one new Verdant Wilds discovery."
        result["events"]=[]
    except sqlite3.OperationalError:
        result=empty_snapshot(regions,sync_pending=True)
    return result

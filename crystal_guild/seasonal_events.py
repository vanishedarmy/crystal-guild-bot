from __future__ import annotations

import copy
import json
import time
from datetime import datetime, timezone
from typing import Any

EVENT_ID = "night_of_the_hollow_crystal"
EDITION_ID = "halloween_2026"
EVENT_NAME = "Night of the Hollow Crystal"
TOKEN_NAME = "Moonlit Tokens"
TOKEN_DAILY_KILL_CAP = 5
TOKEN_PER_SEASONAL_KILL = 3
HOLLOW_WARDEN_FIRST_CLEAR_TOKENS = 15
# Per *combat encounter*, not per completed Venture. Solo Ventures retain
# their independent Encounter/Treasure stage roll. Off-stream/Solo Ventures
# now use a stronger event presence, while Stream/Rally Ventures retain a
# modest five-point advantage so live encounters still feel slightly richer.
SOLO_VENTURE_SEASONAL_CHANCE = 0.35
STREAM_VENTURE_SEASONAL_CHANCE = 0.40
# Retain the old public name for compatibility with existing integrations.
SEASONAL_REPLACEMENT_CHANCE = STREAM_VENTURE_SEASONAL_CHANCE
HOLLOW_WARDEN_WORLD_EVENT_WEIGHT = 0.25

# Halloween 2026 is now the live edition. Existing installs receive this
# schedule once via EVENT_CONFIG_REVISION, after which owner controls remain
# authoritative and are not overwritten on later state reads.
EVENT_CONFIG_REVISION = 2
DEFAULT_EVENT_CONFIG = {
    "event_id": EVENT_ID,
    "edition_id": EDITION_ID,
    "name": EVENT_NAME,
    "enabled": True,
    "activation_mode": "scheduled",
    "starts_at": "2026-10-01T00:00:00Z",
    "ends_at": "2026-11-02T23:59:59Z",
    "redemption_ends_at": "2026-11-05T23:59:59Z",
    "paused": False,
    "config_revision": EVENT_CONFIG_REVISION,
}

SEASONAL_VARIANTS = (
    {"id":"jack_o_bomb","name":"Jack-o'-Bomb","base_monster_id":"bomb","element":"Fire / Explosive","art":"/seasonal/halloween-2026/jack-o-bomb.webp","locked_art":"/seasonal/halloween-2026/jack-o-bomb-locked.webp"},
    {"id":"graveyard_coeurl","name":"Graveyard Coeurl","base_monster_id":"coeurl","element":"Lightning / Shadow","art":"/seasonal/halloween-2026/graveyard-coeurl.webp","locked_art":"/seasonal/halloween-2026/graveyard-coeurl-locked.webp"},
    {"id":"lantern_tonberry","name":"Lantern Tonberry","base_monster_id":"tonberry","element":"Shadow / Physical","art":"/seasonal/halloween-2026/lantern-tonberry.webp","locked_art":"/seasonal/halloween-2026/lantern-tonberry-locked.webp"},
    {"id":"wraith_ahriman","name":"Wraith Ahriman","base_monster_id":"ahriman","element":"Magic / Status","art":"/seasonal/halloween-2026/wraith-ahriman.webp","locked_art":"/seasonal/halloween-2026/wraith-ahriman-locked.webp"},
)
SEASONAL_VARIANTS_BY_ID = {row["id"]: row for row in SEASONAL_VARIANTS}

HOLLOW_WARDEN = {
    "id":"hollow_warden",
    "name":"The Hollow Warden",
    "base_monster_id":"iron_giant",
    "description":"An ancient Iron Giant bound to the Hollow Crystal, risen to claim the realm for the night.",
    "threat":"Extreme",
    "bonus_min":6,
    "bonus_max":10,
    "hp_mult":2.25,
    "power_mult":1.22,
    "reward_mult":1.85,
    "art":"/seasonal/halloween-2026/hollow-warden.webp",
    "locked_art":"/seasonal/halloween-2026/hollow-warden-locked.webp",
}

SHOP = (
    {"id":"spooky_supply_cache","name":"Spooky Supply Cache","cost":10,"kind":"cache","art":"/seasonal/halloween-2026/spooky-supply-cache.webp","repeatable":True},
    {"id":"nightwatcher","name":"Nightwatcher","cost":30,"kind":"title","title_id":"nightwatcher","art":"/seasonal/halloween-2026/nightwatcher.webp","repeatable":False},
    {"id":"haunted_candle","name":"Haunted Candle","cost":40,"kind":"keepsake","art":"/seasonal/halloween-2026/haunted-candle.webp","repeatable":False},
    {"id":"hollow_crystal_display","name":"Hollow Crystal Display","cost":60,"kind":"hall_decoration","art":"/seasonal/halloween-2026/hollow-crystal-display.webp","repeatable":False},
)
SHOP_BY_ID = {row["id"]: row for row in SHOP}

TROPHIES = (
    {"id":"season_halloween_first","name":"A Light in the Dark","description":"Defeat your first seasonal monster.","art":"/seasonal/halloween-2026/trophy-light-in-dark.webp","locked_art":"/seasonal/halloween-2026/trophy-light-in-dark-locked.webp"},
    {"id":"season_halloween_four","name":"Things That Go Bump","description":"Defeat all four Night of the Hollow Crystal variants.","art":"/seasonal/halloween-2026/trophy-things-go-bump.webp","locked_art":"/seasonal/halloween-2026/trophy-things-go-bump-locked.webp"},
    {"id":"season_halloween_warden","name":"The Warden's Seal","description":"Participate in a victorious Hollow Warden World Event.","art":"/seasonal/halloween-2026/trophy-warden-seal.webp","locked_art":"/seasonal/halloween-2026/trophy-warden-seal-locked.webp"},
    {"id":"season_halloween_keeper","name":"Keeper of the Hollow","description":"Acquire the Hollow Crystal Display from the Moonlit Emporium.","art":"/seasonal/halloween-2026/trophy-keeper-hollow.webp","locked_art":"/seasonal/halloween-2026/trophy-keeper-hollow-locked.webp"},
)

OBJECTIVE_POOL = {
    "seasonal": (
        {"id":"lantern_patrol","name":"Lantern Patrol","description":"Defeat 3 Halloween monsters.","kind":"seasonal_kills","target":3,"reward":8},
        {"id":"hollow_hunt","name":"Hollow Hunt","description":"Defeat 5 Halloween monsters.","kind":"seasonal_kills","target":5,"reward":10},
    ),
    "adventure": (
        {"id":"restless_roads","name":"Restless Roads","description":"Complete 2 Ventures or Hunts.","kind":"adventures","target":2,"reward":6},
        {"id":"moonlit_patrol","name":"Moonlit Patrol","description":"Complete 3 Ventures or Hunts.","kind":"adventures","target":3,"reward":8},
    ),
    "guild": (
        {"id":"guild_exorcism","name":"Guild Exorcism","description":"Help the Guild defeat 12 seasonal monsters today.","kind":"guild_seasonal_kills","target":12,"reward":10},
        {"id":"hollow_purge","name":"Hollow Purge","description":"Help the Guild defeat 18 seasonal monsters today.","kind":"guild_seasonal_kills","target":18,"reward":14},
    ),
}

def objectives_for_day(day_key: str) -> tuple[dict[str, Any], ...]:
    try:
        ordinal = datetime.strptime(day_key, "%Y-%m-%d").date().toordinal()
    except ValueError:
        ordinal = 0
    return tuple(pool[ordinal % len(pool)] for pool in OBJECTIVE_POOL.values())



def _parse_iso(value: str | None) -> float:
    raw = str(value or "").strip()
    if not raw:
        return 0.0
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def ensure_event_row(conn) -> None:
    payload = json.dumps(DEFAULT_EVENT_CONFIG, separators=(",", ":"))
    conn.execute(
        "INSERT OR IGNORE INTO seasonal_event_instances(event_id,edition_id,enabled,activation_mode,starts_at,ends_at,redemption_ends_at,paused,config_json) VALUES (?,?,?,?,?,?,?,?,?)",
        (EVENT_ID, EDITION_ID, 1, "scheduled", DEFAULT_EVENT_CONFIG["starts_at"], DEFAULT_EVENT_CONFIG["ends_at"], DEFAULT_EVENT_CONFIG["redemption_ends_at"], 0, payload),
    )
    row = conn.execute("SELECT config_json FROM seasonal_event_instances WHERE edition_id=?", (EDITION_ID,)).fetchone()
    stored_revision = 0
    if row:
        try:
            stored_revision = int((json.loads(str(row["config_json"] or "{}")) or {}).get("config_revision", 0) or 0)
        except (TypeError, ValueError, json.JSONDecodeError):
            stored_revision = 0
    if stored_revision < EVENT_CONFIG_REVISION:
        # One-time live-edition migration for existing installs. This promotes
        # the previously disabled/manual Halloween row into the requested live
        # schedule, but the revision marker prevents later manual pause/off
        # controls from being silently undone.
        conn.execute(
            "UPDATE seasonal_event_instances SET enabled=1,activation_mode='scheduled',starts_at=?,ends_at=?,redemption_ends_at=?,paused=0,config_json=?,updated_at=CURRENT_TIMESTAMP WHERE edition_id=?",
            (DEFAULT_EVENT_CONFIG["starts_at"], DEFAULT_EVENT_CONFIG["ends_at"], DEFAULT_EVENT_CONFIG["redemption_ends_at"], payload, EDITION_ID),
        )


def event_state(conn, now: float | None = None) -> dict[str, Any]:
    ensure_event_row(conn)
    row = conn.execute("SELECT * FROM seasonal_event_instances WHERE edition_id=?", (EDITION_ID,)).fetchone()
    now = float(time.time() if now is None else now)
    if not row:
        return {**DEFAULT_EVENT_CONFIG, "state":"disabled", "active":False, "redemption":False}
    enabled = bool(row["enabled"])
    paused = bool(row["paused"])
    mode = str(row["activation_mode"] or "manual")
    start = _parse_iso(row["starts_at"])
    end = _parse_iso(row["ends_at"])
    redeem_end = _parse_iso(row["redemption_ends_at"])
    active = enabled and not paused
    if mode == "scheduled":
        active = active and start <= now <= end
    redemption = enabled and not paused and not active and end < now <= redeem_end
    if paused:
        state = "paused"
    elif active:
        state = "active"
    elif redemption:
        state = "redemption"
    elif mode == "scheduled" and now < start:
        state = "scheduled"
    else:
        state = "archived" if enabled else "disabled"
    return {
        "event_id": EVENT_ID, "edition_id": EDITION_ID, "name": EVENT_NAME,
        "enabled": enabled, "paused": paused, "activation_mode": mode,
        "starts_at": row["starts_at"], "ends_at": row["ends_at"], "redemption_ends_at": row["redemption_ends_at"],
        "state": state, "active": state == "active", "redemption": state in {"active", "redemption"},
    }


def set_event_control(conn, *, enabled: bool | None = None, paused: bool | None = None, activation_mode: str | None = None) -> dict[str, Any]:
    ensure_event_row(conn)
    fields, args = [], []
    if enabled is not None:
        fields.append("enabled=?"); args.append(1 if enabled else 0)
    if paused is not None:
        fields.append("paused=?"); args.append(1 if paused else 0)
    if activation_mode is not None:
        if activation_mode not in {"manual", "scheduled"}:
            raise ValueError("activation_mode must be manual or scheduled")
        fields.append("activation_mode=?"); args.append(activation_mode)
    if fields:
        fields.append("updated_at=CURRENT_TIMESTAMP")
        args.append(EDITION_ID)
        conn.execute(f"UPDATE seasonal_event_instances SET {', '.join(fields)} WHERE edition_id=?", tuple(args))
    return event_state(conn)


def seasonal_monster(base_monster: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    monster = copy.deepcopy(base_monster)
    monster["id"] = f"seasonal_{EDITION_ID}_{variant['id']}"
    monster["name"] = variant["name"]
    monster["seasonal_variant_id"] = variant["id"]
    monster["seasonal_event_id"] = EDITION_ID
    monster["art"] = variant["art"]
    monster["xp"] = max(1, int(round(float(monster.get("xp", 0)) * 1.15)))
    monster["jp"] = max(0, int(round(float(monster.get("jp", 0)) * 1.10)))
    monster["gil"] = max(0, int(round(float(monster.get("gil", 0)) * 1.10)))
    return monster


def player_progress(conn, player_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM player_seasonal_event_progress WHERE player_id=? AND edition_id=?", (str(player_id), EDITION_ID)).fetchone()
    clears = conn.execute("SELECT variant_id,clears FROM player_seasonal_monster_clears WHERE player_id=? AND edition_id=?", (str(player_id), EDITION_ID)).fetchall()
    claims = conn.execute("SELECT reward_id,quantity FROM player_seasonal_reward_claims WHERE player_id=? AND edition_id=?", (str(player_id), EDITION_ID)).fetchall()
    trophies = conn.execute("SELECT trophy_id,unlocked_at FROM player_seasonal_trophies WHERE player_id=? AND edition_id=?", (str(player_id), EDITION_ID)).fetchall()
    return {
        "tokens": int(row["tokens"] or 0) if row else 0,
        "seasonal_kills": int(row["seasonal_kills"] or 0) if row else 0,
        "adventures": int(row["adventures"] or 0) if row else 0,
        "daily_kills": int(row["daily_kills"] or 0) if row else 0,
        "daily_key": str(row["daily_key"] or "") if row else "",
        "warden_clears": int(row["warden_clears"] or 0) if row else 0,
        "clears": {str(x["variant_id"]): int(x["clears"] or 0) for x in clears},
        "claims": {str(x["reward_id"]): int(x["quantity"] or 0) for x in claims},
        "trophies": {str(x["trophy_id"]): x["unlocked_at"] for x in trophies},
    }


def _unlock_trophy(conn, player_id: str, trophy_id: str, source: str) -> bool:
    cur = conn.execute("INSERT OR IGNORE INTO player_seasonal_trophies(player_id,edition_id,trophy_id,unlock_source) VALUES (?,?,?,?)", (str(player_id), EDITION_ID, trophy_id, source))
    return int(cur.rowcount or 0) > 0


def reconcile_trophies(conn, player_id: str) -> list[str]:
    p = player_progress(conn, player_id)
    unlocked = []
    if p["seasonal_kills"] >= 1 and _unlock_trophy(conn, player_id, "season_halloween_first", "seasonal_monster"):
        unlocked.append("A Light in the Dark")
    if all(p["clears"].get(v["id"], 0) > 0 for v in SEASONAL_VARIANTS) and _unlock_trophy(conn, player_id, "season_halloween_four", "seasonal_collection"):
        unlocked.append("Things That Go Bump")
    if p["warden_clears"] > 0 and _unlock_trophy(conn, player_id, "season_halloween_warden", "hollow_warden"):
        unlocked.append("The Warden's Seal")
    if p["claims"].get("hollow_crystal_display", 0) > 0 and _unlock_trophy(conn, player_id, "season_halloween_keeper", "event_shop"):
        unlocked.append("Keeper of the Hollow")
    return unlocked


def _daily_row(conn, player_id: str, day_key: str):
    conn.execute("INSERT OR IGNORE INTO player_seasonal_daily_progress(player_id,edition_id,day_key) VALUES (?,?,?)", (str(player_id),EDITION_ID,day_key))
    return conn.execute("SELECT * FROM player_seasonal_daily_progress WHERE player_id=? AND edition_id=? AND day_key=?", (str(player_id),EDITION_ID,day_key)).fetchone()

def _guild_daily_kills(conn, day_key: str) -> int:
    row = conn.execute("SELECT COALESCE(SUM(seasonal_kills),0) FROM player_seasonal_daily_progress WHERE edition_id=? AND day_key=?", (EDITION_ID,day_key)).fetchone()
    return int(row[0] or 0)

def reconcile_objectives(conn, player_id: str, day_key: str) -> list[dict[str, Any]]:
    row = _daily_row(conn, player_id, day_key)
    guild_kills = _guild_daily_kills(conn, day_key)
    awarded = []
    for obj in objectives_for_day(day_key):
        if obj["kind"] == "seasonal_kills": value = int(row["seasonal_kills"] or 0)
        elif obj["kind"] == "adventures": value = int(row["adventures"] or 0)
        else:
            value = guild_kills
            if int(row["seasonal_kills"] or 0) <= 0:
                continue
        if value < int(obj["target"]):
            continue
        cur = conn.execute("INSERT OR IGNORE INTO player_seasonal_objective_claims(player_id,edition_id,day_key,objective_id,reward_tokens) VALUES (?,?,?,?,?)", (str(player_id),EDITION_ID,day_key,obj["id"],int(obj["reward"])))
        if int(cur.rowcount or 0) > 0:
            conn.execute("UPDATE player_seasonal_event_progress SET tokens=tokens+?,updated_at=CURRENT_TIMESTAMP WHERE player_id=? AND edition_id=?", (int(obj["reward"]),str(player_id),EDITION_ID))
            awarded.append(obj)
    return awarded

def award_seasonal_kill(conn, player_id: str, variant_id: str, *, today_key: str | None = None) -> dict[str, Any]:
    variant_id = str(variant_id)
    if variant_id not in SEASONAL_VARIANTS_BY_ID:
        return {"tokens":0,"trophies":[]}
    today_key = today_key or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn.execute("INSERT OR IGNORE INTO player_seasonal_event_progress(player_id,edition_id) VALUES (?,?)", (str(player_id), EDITION_ID))
    row = conn.execute("SELECT daily_key,daily_kills FROM player_seasonal_event_progress WHERE player_id=? AND edition_id=?", (str(player_id), EDITION_ID)).fetchone()
    daily_kills = int(row["daily_kills"] or 0) if str(row["daily_key"] or "") == today_key else 0
    token_gain = TOKEN_PER_SEASONAL_KILL if daily_kills < TOKEN_DAILY_KILL_CAP else 0
    new_daily = daily_kills + 1
    conn.execute("UPDATE player_seasonal_event_progress SET tokens=tokens+?,seasonal_kills=seasonal_kills+1,daily_kills=?,daily_key=?,updated_at=CURRENT_TIMESTAMP WHERE player_id=? AND edition_id=?", (token_gain,new_daily,today_key,str(player_id),EDITION_ID))
    daily = _daily_row(conn, player_id, today_key)
    conn.execute("UPDATE player_seasonal_daily_progress SET seasonal_kills=seasonal_kills+1,updated_at=CURRENT_TIMESTAMP WHERE player_id=? AND edition_id=? AND day_key=?", (str(player_id),EDITION_ID,today_key))
    conn.execute("INSERT INTO player_seasonal_monster_clears(player_id,edition_id,variant_id,clears,first_cleared_at,last_cleared_at) VALUES (?,?,?,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP) ON CONFLICT(player_id,edition_id,variant_id) DO UPDATE SET clears=clears+1,last_cleared_at=CURRENT_TIMESTAMP", (str(player_id),EDITION_ID,variant_id))
    objective_awards = reconcile_objectives(conn, player_id, today_key)
    if _guild_daily_kills(conn, today_key) >= min(int(o["target"]) for o in OBJECTIVE_POOL["guild"]):
        contributors = conn.execute("SELECT player_id FROM player_seasonal_daily_progress WHERE edition_id=? AND day_key=? AND seasonal_kills>0", (EDITION_ID,today_key)).fetchall()
        for contributor in contributors:
            if str(contributor["player_id"]) != str(player_id):
                reconcile_objectives(conn, str(contributor["player_id"]), today_key)
    trophies = reconcile_trophies(conn, player_id)
    return {"tokens":token_gain + sum(int(o["reward"]) for o in objective_awards),"trophies":trophies,"objectives":[o["name"] for o in objective_awards]}


def award_adventure(conn, player_id: str, *, today_key: str | None = None) -> list[dict[str, Any]]:
    today_key = today_key or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn.execute("INSERT OR IGNORE INTO player_seasonal_event_progress(player_id,edition_id) VALUES (?,?)", (str(player_id), EDITION_ID))
    conn.execute("UPDATE player_seasonal_event_progress SET adventures=adventures+1,updated_at=CURRENT_TIMESTAMP WHERE player_id=? AND edition_id=?", (str(player_id),EDITION_ID))
    _daily_row(conn, player_id, today_key)
    conn.execute("UPDATE player_seasonal_daily_progress SET adventures=adventures+1,updated_at=CURRENT_TIMESTAMP WHERE player_id=? AND edition_id=? AND day_key=?", (str(player_id),EDITION_ID,today_key))
    return reconcile_objectives(conn, player_id, today_key)


def award_warden_clear(conn, player_id: str) -> dict[str, Any]:
    conn.execute("INSERT OR IGNORE INTO player_seasonal_event_progress(player_id,edition_id) VALUES (?,?)", (str(player_id), EDITION_ID))
    row = conn.execute("SELECT warden_clears FROM player_seasonal_event_progress WHERE player_id=? AND edition_id=?", (str(player_id),EDITION_ID)).fetchone()
    first = int(row["warden_clears"] or 0) == 0
    gain = HOLLOW_WARDEN_FIRST_CLEAR_TOKENS if first else 0
    conn.execute("UPDATE player_seasonal_event_progress SET tokens=tokens+?,warden_clears=warden_clears+1,updated_at=CURRENT_TIMESTAMP WHERE player_id=? AND edition_id=?", (gain,str(player_id),EDITION_ID))
    trophies = reconcile_trophies(conn, player_id)
    return {"tokens":gain,"trophies":trophies}


def buy_reward(conn, player_id: str, reward_id: str) -> tuple[bool, str, dict[str, Any]]:
    reward = SHOP_BY_ID.get(str(reward_id))
    if not reward:
        return False, "That Moonlit Emporium reward does not exist.", {}
    state = event_state(conn)
    if not state["redemption"]:
        return False, "The Moonlit Emporium is closed.", {}
    p = player_progress(conn, player_id)
    if not reward.get("repeatable") and p["claims"].get(reward["id"], 0) > 0:
        return False, f"{reward['name']} is already owned.", {}
    if p["tokens"] < int(reward["cost"]):
        return False, f"You need {reward['cost']} {TOKEN_NAME}; you have {p['tokens']}.", {}
    conn.execute("UPDATE player_seasonal_event_progress SET tokens=tokens-?,updated_at=CURRENT_TIMESTAMP WHERE player_id=? AND edition_id=?", (int(reward["cost"]),str(player_id),EDITION_ID))
    conn.execute("INSERT INTO player_seasonal_reward_claims(player_id,edition_id,reward_id,quantity,claimed_at) VALUES (?,?,?,1,CURRENT_TIMESTAMP) ON CONFLICT(player_id,edition_id,reward_id) DO UPDATE SET quantity=quantity+1,claimed_at=CURRENT_TIMESTAMP", (str(player_id),EDITION_ID,reward["id"]))
    if reward["kind"] == "title":
        conn.execute("INSERT OR IGNORE INTO player_titles(player_id,title_id,unlocked_at) VALUES (?,?,CURRENT_TIMESTAMP)", (str(player_id),str(reward["title_id"])))
    trophies = reconcile_trophies(conn, player_id)
    return True, f"Moonlit Emporium — acquired {reward['name']} for {reward['cost']} {TOKEN_NAME}.", {"reward_id":reward["id"],"trophies":trophies}


def public_snapshot(conn, player_id: str) -> dict[str, Any]:
    state = event_state(conn)
    progress = player_progress(conn, player_id)
    guild_kills = int(conn.execute("SELECT COALESCE(SUM(clears),0) FROM player_seasonal_monster_clears WHERE edition_id=?", (EDITION_ID,)).fetchone()[0] or 0)
    day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily = conn.execute("SELECT seasonal_kills,adventures FROM player_seasonal_daily_progress WHERE player_id=? AND edition_id=? AND day_key=?", (str(player_id),EDITION_ID,day_key)).fetchone()
    daily_kills = int(daily["seasonal_kills"] or 0) if daily else 0
    daily_adventures = int(daily["adventures"] or 0) if daily else 0
    guild_daily = _guild_daily_kills(conn, day_key)
    claims = {str(r["objective_id"]) for r in conn.execute("SELECT objective_id FROM player_seasonal_objective_claims WHERE player_id=? AND edition_id=? AND day_key=?", (str(player_id),EDITION_ID,day_key)).fetchall()}
    objectives = []
    for obj in objectives_for_day(day_key):
        if obj["kind"] == "seasonal_kills": value = daily_kills
        elif obj["kind"] == "adventures": value = daily_adventures
        else: value = guild_daily
        objectives.append({**obj,"progress":min(int(obj["target"]),int(value)),"complete":obj["id"] in claims,"ready":int(value)>=int(obj["target"])})
    return {
        **state,
        "token_name": TOKEN_NAME,
        "tokens": progress["tokens"],
        "daily_kills": progress["daily_kills"],
        "daily_kill_cap": TOKEN_DAILY_KILL_CAP,
        "variants":[{**row,"clears":progress["clears"].get(row["id"],0)} for row in SEASONAL_VARIANTS],
        "world_event":HOLLOW_WARDEN,
        "objectives":objectives,
        "shop":[{**row,"owned":progress["claims"].get(row["id"],0)>0} for row in SHOP],
        "trophies":[{**row,"unlocked_at":progress["trophies"].get(row["id"])} for row in TROPHIES],
        "guild_seasonal_kills":guild_kills,
        "art":{"banner":"/seasonal/halloween-2026/event-banner.webp","background":"/seasonal/halloween-2026/hollow-crystal-spire.webp"},
    }

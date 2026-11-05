"""Live Twitch exploration and the limited-time Traveling Moogle Merchant.

The event uses the existing SQLite runtime_state/cooldowns/inventory/transactions
ledger. No schema migration, permanent shop unlocks or Relic sale rights.
"""
from __future__ import annotations

import json
import math
import time
from typing import Any

MOOGLE_STATE_KEY = "stream_traveling_moogle_v211"
EXPLORE_COOLDOWN_SECONDS = 5 * 60
MOOGLE_VISIT_SECONDS = 12 * 60
MOOGLE_CHECK_SECONDS = 8 * 60
MOOGLE_ARRIVAL_CHANCE = 0.32
MOOGLE_STOCK_SLOTS = 5

# Explicit allowlist. Rare found-only items are *not* globally unlocked as shop
# stock; only these finite, time-limited merchant offers can be purchased.
# Equipment, Relics, quest keys, and zero-price progression materials excluded.
ORDINARY_STOCK = (
    "hi_potion", "mega_potion", "phoenix_down", "ether", "hi_ether",
    "x_potion", "remedy",
)
SPECIAL_STOCK = (
    "turbo_ether", "elixir", "megalixir", "crystal_shard", "dragon_scale",
    "adamantite", "dark_matter", "eidolon_shard", "crystal_core",
)
EXPLORATION_ITEMS = ("potion", "ether", "hi_potion", "phoenix_down", "remedy", "mega_potion")
EXPLORATION_MATERIALS = ("crystal_shard", "wyvern_scale", "elemental_crystal", "ahriman_lens", "magitek_capacitor")
EXPLORATION_RARES = ("dragon_scale", "adamantite", "tonberry_lantern", "dragon_heart")

FLAVOR = {
    "quiet": (
        "A suspiciously polite bush offers no treasure. It keeps your secret, kupo.",
        "You discover an ancient map. Someone drew a moogle with impressive confidence and zero directions.",
        "A hidden passage ends at a door labeled 'Definitely Not a Mimic'. You wisely move on.",
        "A distant chocobo answers your call. The conversation is emotional but entirely unproductive.",
    ),
    "gil": (
        "A loose cobblestone conceals an old traveler's purse.",
        "You escort a wandering courier past a suspicious crossroads.",
        "A grateful caravan hands over a modest pouch of Gil.",
        "You win a staring contest with a mischievous moogle and claim its wager.",
    ),
    "supplies": (
        "You discover a forgotten field satchel beneath a fallen signpost.",
        "A friendly wandering alchemist leaves behind a useful provision.",
        "An overturned supply crate yields something intact.",
        "Your pack rustles; a generous moogle insists it was always there.",
    ),
    "materials": (
        "A cluster of unusual minerals glimmers beneath the roots of an ancient tree.",
        "You salvage a rare component from an abandoned Magitek waystation.",
        "An old stone altar responds to your curiosity with a fragment of crystal.",
    ),
    "knowledge": (
        "A weathered ruin reveals carvings from an almost-forgotten age.",
        "You decipher the scratches on an old Guild waystone.",
        "You follow the trail of an ancient adventuring party and learn from their mistakes.",
        "A moonlit vision illuminates a safer path through the wilderness.",
    ),
    "misfortune": (
        "A very persuasive bridge troll charges an unexpected crossing fee.",
        "A coin purse springs open while you scramble out of an old trap.",
        "A tiny moogle demands customs duties on your imaginary treasure.",
    ),
    "wound": (
        "A concealed pressure plate launches harmless-looking, decidedly sharp darts.",
        "You narrowly escape a nest of territorial crystal wasps.",
        "An ancient ward flashes before you can duck behind cover.",
    ),
    "healing": (
        "A sparkling spring soothes your battle-worn spirit.",
        "A wandering healer shares a restorative charm.",
        "A gentle crystal wind mends some of your wounds.",
    ),
    "rare": (
        "An old adventurer's cache opens after you solve a deceptively simple riddle.",
        "A hidden grotto rewards your curiosity with an uncommon find.",
        "A golden light reveals something the wilderness has guarded for years.",
    ),
}


def _result():
    # Late import to avoid a circular import from engine.py.
    from .engine import GameResult
    return GameResult


def _read(conn: Any) -> dict[str, Any]:
    row = conn.execute("SELECT value_json FROM runtime_state WHERE state_key=?", (MOOGLE_STATE_KEY,)).fetchone()
    if not row:
        return {}
    try:
        obj = json.loads(row["value_json"])
    except (TypeError, ValueError):
        return {}
    return obj if isinstance(obj, dict) else {}


def _write(conn: Any, data: dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO runtime_state(state_key,value_json,updated_at) VALUES (?,?,CURRENT_TIMESTAMP) "
        "ON CONFLICT(state_key) DO UPDATE SET value_json=excluded.value_json,updated_at=CURRENT_TIMESTAMP",
        (MOOGLE_STATE_KEY, json.dumps(data, sort_keys=True, separators=(",", ":"))),
    )


def _choice(game: Any, ids: tuple[str, ...]) -> dict[str, Any] | None:
    matches = [game.data.items[i] for i in ids if i in game.data.items and
               game.data.items[i].get("type") in {"consumable", "material"} and
               int(game.data.items[i].get("price") or 0) > 0]
    return game.rng.choice(matches) if matches else None


def explore(game: Any, player_id: str, *, stream_live: bool, now: int | None = None):
    G = _result()
    if not stream_live:
        return G.fail("EXPLORE — The wilderness wakes only while the Twitch stream is LIVE.")
    now = int(time.time() if now is None else now)
    pid = str(player_id)
    with game._state_lock, game.db.tx(immediate=True) as conn:
        p = conn.execute("SELECT * FROM players WHERE twitch_id=?", (pid,)).fetchone()
        if not p:
            return game._need_recruit()
        # A personal explore must not compete with another running activity or
        # grant free rewards to incapacitated characters.
        if (game._dungeon_load(pid) or game._expedition_load(pid) or game._solo_expedition_load(pid)
                or pid in game.active_hunts or pid in game.encounter_roster or pid in game.raid_roster
                or int(p["current_hp"] or 0) <= 0 or int(p["camp_until"] or 0) > now):
            return G.fail("EXPLORE — Finish your current adventure or recover before setting out.")
        row = conn.execute("SELECT available_at FROM cooldowns WHERE player_id=? AND action='stream_explore'", (pid,)).fetchone()
        remaining = max(0, int(row["available_at"]) - now) if row else 0
        if remaining:
            return G.fail(f"EXPLORE — Your next outing is ready in {game._format_seconds(remaining)}.", cooldown_remaining=remaining)

        roll = game.rng.random()
        level = int(p["level"])
        gil = 0
        xp = 0
        jp = 0
        hp_delta = 0
        item_id = None
        qty = 0
        kind = "quiet"
        if roll < 0.14:
            kind = "quiet"
        elif roll < 0.35:
            kind = "gil"
            gil = game.rng.randint(35 + level * 2, 75 + level * 5)
        elif roll < 0.53:
            kind = "supplies"
            selected = _choice(game, EXPLORATION_ITEMS)
            item_id = selected["id"] if selected else None
            qty = game.rng.randint(1, 2)
        elif roll < 0.65:
            kind = "materials"
            selected = _choice(game, EXPLORATION_MATERIALS)
            item_id = selected["id"] if selected else None
            qty = 1
        elif roll < 0.84:
            kind = "knowledge"
            xp = game.rng.randint(20 + level * 3, 50 + level * 6)
            jp = game.rng.randint(7 + level, 15 + level * 2)
        elif roll < 0.91:
            kind = "misfortune"
            gil = -min(int(p["gil"]), game.rng.randint(15, 55 + level * 2))
        elif roll < 0.95:
            kind = "wound"
            hp_delta = -min(max(0, int(p["current_hp"]) - 1), max(1, game._max_hp(p) // 12))
        elif roll < 0.98:
            kind = "healing"
            hp_delta = min(max(0, game._max_hp(p) - int(p["current_hp"])), max(5, game._max_hp(p) // 5))
        else:
            kind = "rare"
            selected = _choice(game, EXPLORATION_RARES)
            item_id = selected["id"] if selected else None
            qty = 1

        description = game.rng.choice(FLAVOR[kind])
        messages = [f"EXPLORE — {description}"]
        if gil:
            conn.execute("UPDATE players SET gil=gil+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (gil, pid))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,'stream_explore')", (pid, gil))
            messages.append(f"{'Found' if gil > 0 else 'Lost'} {abs(gil):,} Gil.")
        if xp or jp:
            conn.execute("UPDATE players SET xp=xp+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (xp, pid))
            conn.execute("UPDATE player_jobs SET jp=jp+? WHERE player_id=? AND job_id=?", (jp, pid, p["current_job"]))
            messages.append(f"Gained {xp:,} XP / {jp:,} JP from the discovery.")
        if hp_delta:
            conn.execute("UPDATE players SET current_hp=current_hp+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (hp_delta, pid))
            messages.append(f"{'Recovered' if hp_delta > 0 else 'Lost'} {abs(hp_delta)} HP.")
        if item_id:
            conn.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) "
                         "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (pid, item_id, qty))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'item',?,?,'stream_explore')", (pid, item_id, qty))
            messages.append(f"Found {game.data.items[item_id]['name']} x{qty}!")
        conn.execute("INSERT INTO cooldowns(player_id,action,available_at) VALUES (?,'stream_explore',?) "
                     "ON CONFLICT(player_id,action) DO UPDATE SET available_at=excluded.available_at",
                     (pid, now + EXPLORE_COOLDOWN_SECONDS))
    if xp or jp:
        messages.extend(game._process_levels(pid, str(p["current_job"])))
    return G.success(*messages, outcome=kind, gil=gil, xp=xp, jp=jp, item_id=item_id,
                     quantity=qty, cooldown_seconds=EXPLORE_COOLDOWN_SECONDS)


def _roll_stock(game: Any) -> list[dict[str, Any]]:
    offerings: list[dict[str, Any]] = []
    seen: set[str] = set()
    groups = (ORDINARY_STOCK, ORDINARY_STOCK, ORDINARY_STOCK, SPECIAL_STOCK, SPECIAL_STOCK)
    for source in groups:
        candidates = [i for i in source if i not in seen and i in game.data.items and
                      game.data.items[i].get("type") in {"consumable", "material"} and
                      int(game.data.items[i].get("price") or 0) > 0]
        if not candidates:
            continue
        item_id = game.rng.choice(candidates)
        seen.add(item_id)
        item = game.data.items[item_id]
        special = source is SPECIAL_STOCK
        price = max(1, int(math.ceil(int(item["price"]) * (1.6 if special else 1.12))))
        # Specials are scarce; no permanent shop eligibility is granted.
        quantity = 1 if special else game.rng.randint(2, 5)
        offerings.append({"slot": len(offerings) + 1, "id": item_id,
                          "price": price, "remaining": quantity})
    return offerings


def _fresh(state: dict[str, Any], now: int) -> dict[str, Any] | None:
    visit = state.get("visit")
    return visit if isinstance(visit, dict) and int(visit.get("expires_at") or 0) > now else None


def maybe_spawn_merchant(game: Any, *, stream_live: bool, now: int | None = None, force: bool = False):
    """Tick the shared merchant independently of battle scheduling. Broadcast on spawn."""
    G = _result()
    now = int(time.time() if now is None else now)
    with game._state_lock, game.db.tx(immediate=True) as conn:
        state = _read(conn)
        visit = _fresh(state, now)
        if not stream_live:
            if state.get("online") or state.get("visit"):
                # Offline interruptions close the merchant; visits never resume
                # after restarting the stream.
                _write(conn, {"online": False, "next_check_at": now + game.rng.randint(1200, 2100), "visit": None})
            return G.success(merchant_spawned=False)
        if not state.get("online") and not force:
            _write(conn, {"online": True, "next_check_at": now + game.rng.randint(900, 1800), "visit": None})
            return G.success(merchant_spawned=False)
        if visit:
            return G.success(merchant_spawned=False, expires_at=int(visit["expires_at"]))
        if state.get("visit"):
            state["visit"] = None
            state["next_check_at"] = now + game.rng.randint(1200, 2100)
            _write(conn, state)
            return G.success("TRAVELING MOOGLE — The merchant packs up and vanishes down the road. Kupo!",
                             merchant_spawned=False, merchant_departed=True)
        if not force and now < int(state.get("next_check_at") or 0):
            return G.success(merchant_spawned=False)
        if not force and game.rng.random() > MOOGLE_ARRIVAL_CHANCE:
            state["next_check_at"] = now + MOOGLE_CHECK_SECONDS
            state["online"] = True
            _write(conn, state)
            return G.success(merchant_spawned=False)
        stock = _roll_stock(game)
        if not stock:
            state["next_check_at"] = now + MOOGLE_CHECK_SECONDS
            _write(conn, state)
            return G.success(merchant_spawned=False)
        visit = {"id": f"moogle:{now}:{game.rng.randrange(1000000)}",
                 "arrived_at": now, "expires_at": now + MOOGLE_VISIT_SECONDS, "stock": stock}
        _write(conn, {"online": True, "next_check_at": now + MOOGLE_VISIT_SECONDS + 1800,
                      "visit": visit})
        previews = [f"#{e['slot']} {game.data.items[e['id']]['name']} {e['price']:,}g (x{e['remaining']})" for e in stock]
        return G.success("TRAVELING MOOGLE — Kupo! A wandering merchant has appeared for 12 minutes!",
                         " | ".join(previews),
                         "View: !moogle · Buy: !moogle buy <slot> [quantity]. Limited stock, shared across the Guild!",
                         merchant_spawned=True, expires_at=visit["expires_at"], stock=stock)


def merchant_status(game: Any, *, stream_live: bool, now: int | None = None):
    G = _result()
    if not stream_live:
        return G.fail("TRAVELING MOOGLE — The merchant appears only while the stream is LIVE.")
    now = int(time.time() if now is None else now)
    with game.db.tx() as conn:
        state = _read(conn)
        visit = _fresh(state, now)
    if not visit:
        return G.success("TRAVELING MOOGLE — No merchant is in town right now. Keep watching the stream for a surprise visit!")
    available = [s for s in visit.get("stock", []) if int(s.get("remaining") or 0) > 0]
    rows = [f"#{row['slot']} {game.data.items[row['id']]['name']} {int(row['price']):,}g (x{row['remaining']})"
            for row in available if row.get("id") in game.data.items]
    return G.success(f"TRAVELING MOOGLE — Open for {game._format_seconds(int(visit['expires_at'])-now)}!",
                     " | ".join(rows) if rows else "Sold out, kupo!",
                     "Buy: !moogle buy <slot> [quantity] · Shared stock until departure.",
                     expires_at=visit["expires_at"], stock=available)


def merchant_buy(game: Any, player_id: str, slot: str, quantity: int = 1,
                 *, stream_live: bool, now: int | None = None):
    G = _result()
    if not stream_live:
        return G.fail("TRAVELING MOOGLE — Purchases are live-stream only.")
    now = int(time.time() if now is None else now)
    pid = str(player_id)
    try:
        slot_num = int(str(slot).removeprefix("#"))
    except (TypeError, ValueError):
        return G.fail("TRAVELING MOOGLE — Choose a numbered offer. Example: !moogle buy 2 1")
    if quantity < 1 or quantity > 5:
        return G.fail("TRAVELING MOOGLE — Choose between 1 and 5 items per purchase.")
    with game._state_lock, game.db.tx(immediate=True) as conn:
        p = conn.execute("SELECT gil FROM players WHERE twitch_id=?", (pid,)).fetchone()
        if not p:
            return game._need_recruit()
        state = _read(conn)
        visit = _fresh(state, now)
        if not visit:
            return G.fail("TRAVELING MOOGLE — The merchant has already moved on. No Gil spent.")
        offer = next((o for o in visit.get("stock", []) if int(o.get("slot") or 0) == slot_num), None)
        if not offer or offer.get("id") not in game.data.items:
            return G.fail("TRAVELING MOOGLE — That slot isn't on the stall. Use !moogle for the current stock.")
        available = int(offer.get("remaining") or 0)
        if available < quantity:
            return G.fail(f"TRAVELING MOOGLE — Only {available} left in slot #{slot_num}. No Gil spent.")
        cost = int(offer["price"]) * quantity
        if int(p["gil"]) < cost:
            return G.fail(f"TRAVELING MOOGLE — Need {cost:,} Gil; you have {int(p['gil']):,}. No Gil spent.")
        debited = conn.execute("UPDATE players SET gil=gil-?,updated_at=CURRENT_TIMESTAMP "
                               "WHERE twitch_id=? AND gil>=?", (cost, pid, cost))
        if debited.rowcount != 1:
            return G.fail("TRAVELING MOOGLE — Not enough Gil. No item was granted.")
        offer["remaining"] = available - quantity
        item_id = str(offer["id"])
        conn.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) "
                     "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (pid, item_id, quantity))
        conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,'traveling_moogle')", (pid, -cost))
        conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'item',?,?,'traveling_moogle')", (pid, item_id, quantity))
        state["visit"] = visit
        _write(conn, state)
    return G.success(f"TRAVELING MOOGLE — Purchased {game.data.items[item_id]['name']} x{quantity} for {cost:,} Gil. Kupo!",
                     item_id=item_id, quantity=quantity, cost=cost, remaining=int(offer["remaining"]))

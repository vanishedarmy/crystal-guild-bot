"""Durable, server-only Records & Moments settlement (Step 3).

Never invoke from an HTTP/client payload. Producers call these helpers while the
original authoritative game transaction is still open, using stable run/row IDs.
Catalog IDs stay separate from the legacy achievements/Title discovery lists
until the spoiler-safe Step 4 Portal integration.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .moments import EVENT_FACTS, matches_settlement

# Only the original persisted columns count as historical evidence.
_PURCHASE_SOURCES = frozenset({"shop", "portal_shop", "trading_post_buy"})
_LOWER_IS_BETTER = frozenset({"closest_victory", "closest_world_event"})


def _validate_settlement_ranges(trigger: str, evidence: Mapping[str, Any]) -> None:
    """Reject impossible *settled* numbers before they become permanent proof.

    Type checks alone admit negative HP, a 150% survivor, or a negative ticket
    streak. These constraints deliberately do not infer a historical result or
    require that a particular Moment's condition already matches.
    """
    nonnegative = {
        "combat_victory": ("final_hp",),
        "combat_finishing_blow": ("damage_dealt", "target_hp_before_hit", "target_max_hp"),
        "combat_player_ko": ("self_item_shop_price_gil", "player_actions_since_item", "player_actions_completed"),
        "world_event_victory": ("participant_count", "living_party_count"),
        "saucer_round_settled": ("record_value",),
        "raid_victory": ("party_size_at_start", "living_party_count"),
        "purchase_settled": ("record_value",),
        "venture_completed": ("consumables_used",),
    }
    if any(evidence[field] < 0 for field in nonnegative.get(trigger, ())):
        raise ValueError("Negative values cannot be settled as Moment evidence")
    for field in ("highest_survivor_hp_pct_raw", "final_hp_pct_pre_recovery_raw"):
        if field in evidence and not 0 <= evidence[field] <= 100:
            raise ValueError("A settled HP percentage must be between 0 and 100")
    if trigger == "combat_victory" and evidence["player_alive"] and evidence["final_hp"] < 1:
        raise ValueError("A living victor must have at least one HP")
    if trigger in ("world_event_victory", "raid_victory"):
        if evidence["living_party_count"] > evidence.get("participant_count", evidence.get("party_size_at_start")):
            raise ValueError("Survivors cannot outnumber participants")
        if evidence["player_alive"] and evidence["living_party_count"] < 1:
            raise ValueError("A living player must count among the survivors")


def award_settlement(
    conn: Any, data: Any, player_id: str, event_key: str,
    evidence: Mapping[str, Any], *, historical: bool = False,
    occurred_at: str | int | None = None,
) -> list[str]:
    """Atomically insert once-only Moment and matching reserved cosmetic Title.

    A live producer must call this INSIDE the source game transaction. A
    duplicate producer/restarted engine cannot award the same Moment twice.
    Reject incomplete/invalid evidence instead of allowing partial matching.
    """
    if (not isinstance(player_id, str) or not player_id.strip()
            or not isinstance(event_key, str) or not event_key.strip()
            or len(event_key) > 220 or not isinstance(evidence, Mapping)):
        raise ValueError("A Moment settlement needs a player and a stable server event key")
    trigger = evidence.get("event")
    schema = EVENT_FACTS.get(trigger)
    if not schema or evidence.get("settled") is not True:
        raise ValueError("Moments require known, finished server settlement evidence")
    for key, expected in schema.items():
        if key not in evidence:
            raise ValueError(f"Missing authoritative {trigger} settlement fact: {key}")
        value = evidence[key]
        if expected is float:
            import math
            if type(value) not in (float, int) or not math.isfinite(value):
                raise ValueError(f"Invalid numeric settlement fact: {key}")
        elif type(value) is not expected:
            raise ValueError(f"Invalid settlement fact type: {key}")
    _validate_settlement_ranges(trigger, evidence)
    matched: list[str] = []
    stored = {key: evidence[key] for key in sorted(schema)}
    stored["event"] = trigger
    stored["settled"] = True
    serialized = json.dumps(stored, sort_keys=True, separators=(",", ":"))
    # One stable event key may award several Moments, but a replay of that key
    # must NEVER introduce a different event type or contradictory facts.
    # Do this before any new rewards are inserted, so the caller can roll back
    # the entire source transaction on a producer/recovery collision.
    previously_settled = conn.execute(
        "SELECT event_type,evidence_json FROM player_moment_unlocks "
        "WHERE player_id=? AND event_key=? LIMIT 1", (player_id, event_key),
    ).fetchone()
    if previously_settled and (previously_settled["event_type"] != trigger
                                or previously_settled["evidence_json"] != serialized):
        raise ValueError("Conflicting evidence for an already settled Moment event key")
    for moment_id, moment in data.moments.items():
        if moment["trigger"] != trigger or not matches_settlement(moment, evidence):
            continue
        if historical and moment.get("backfill") != "verified_saved_history":
            continue
        title_id = moment["reward"]["title_id"]
        inserted = conn.execute(
            "INSERT OR IGNORE INTO player_moment_unlocks"
            "(player_id,moment_id,title_id,event_key,event_type,evidence_json,earned_at,historical) "
            "VALUES (?,?,?,?,?,?,COALESCE(?,CURRENT_TIMESTAMP),?)",
            (player_id, moment_id, title_id, event_key, trigger, serialized,
             str(occurred_at) if occurred_at is not None else None,
             1 if historical else 0),
        ).rowcount
        if inserted:
            conn.execute(
                "INSERT OR IGNORE INTO player_titles(player_id,title_id) VALUES (?,?)",
                (player_id, title_id),
            )
            # An earned exceptional Moment may also leave a permanent object in
            # the Hall. The same transaction owns both rewards, replay-safe.
            trophy_id = moment["reward"].get("trophy_candidate_id")
            if trophy_id:
                from .trophies import TROPHIES_BY_ID
                trophy = TROPHIES_BY_ID.get(trophy_id)
                if not trophy or trophy["unlock"] != {"kind": "moment", "id": moment_id}:
                    raise ValueError("Moment trophy contract does not match its catalog")
                conn.execute(
                    "INSERT OR IGNORE INTO player_trophies(player_id,trophy_id,unlock_source) VALUES (?,?,?)",
                    (player_id, trophy_id, f"moment:{event_key}"),
                )
            matched.append(moment["name"])
    return matched


def best_record(
    conn: Any, player_id: str, record_id: str, value: int,
    event_key: str, *, context: Mapping[str, Any] | None = None,
    lower_is_better: bool | None = None, occurred_at: str | int | None = None,
) -> bool:
    """Persist real observed event bests; zero/negative samples do not count."""
    from .personal_records import RECORD_SPECS
    new_event = {spec[0] for spec in RECORD_SPECS if spec[4] == "new_event"}
    if (record_id not in new_event or type(value) is not int or value < 1
            or not isinstance(event_key, str) or not event_key.strip()
            or len(event_key) > 220):
        raise ValueError("Unsupported or nonpositive personal best")
    canonical_lower = record_id in _LOWER_IS_BETTER
    if lower_is_better is not None and lower_is_better is not canonical_lower:
        raise ValueError("Record direction differs from the canonical personal best")
    previous = conn.execute(
        "SELECT best_value,event_key FROM player_record_events WHERE player_id=? AND record_id=?",
        (player_id, record_id),
    ).fetchone()
    if previous and previous["event_key"] == event_key and previous["best_value"] != value:
        raise ValueError("A settled record event cannot report two different results")
    if previous and (value >= previous["best_value"] if canonical_lower else value <= previous["best_value"]):
        return False
    conn.execute(
        "INSERT INTO player_record_events(player_id,record_id,best_value,event_key,context_json,occurred_at) "
        "VALUES (?,?,?,?,?,COALESCE(?,CURRENT_TIMESTAMP)) "
        "ON CONFLICT(player_id,record_id) DO UPDATE SET "
        "best_value=excluded.best_value,event_key=excluded.event_key,"
        "context_json=excluded.context_json,occurred_at=excluded.occurred_at",
        (player_id, record_id, value, event_key,
         json.dumps(dict(context or {}), sort_keys=True, separators=(",", ":")),
         str(occurred_at) if occurred_at is not None else None),
    )
    return True


def reconcile_owned_moment_rewards(conn: Any, data: Any, player_id: str) -> dict[str, int]:
    """Repair *only* missing cosmetic rewards of real, previously earned Moments.

    Migration from Step 3 can predate trophy art; an interrupted upgrade may
    also leave a title receipt absent. Do not create a Moment on this path, and
    do not infer one from a title, a best record, a combat statistic or a trophy.
    """
    restored = {"titles": 0, "trophies": 0}
    for row in conn.execute(
        "SELECT moment_id,title_id FROM player_moment_unlocks WHERE player_id=?", (player_id,),
    ).fetchall():
        moment = data.moments.get(str(row["moment_id"]))
        if not moment or moment["reward"]["title_id"] != row["title_id"]:
            continue
        restored["titles"] += conn.execute(
            "INSERT OR IGNORE INTO player_titles(player_id,title_id) VALUES (?,?)",
            (player_id, row["title_id"]),
        ).rowcount
        trophy_id = moment["reward"].get("trophy_candidate_id")
        if trophy_id:
            from .trophies import TROPHIES_BY_ID
            trophy = TROPHIES_BY_ID.get(trophy_id)
            if not trophy or trophy["unlock"] != {"kind": "moment", "id": row["moment_id"]}:
                raise ValueError("Owned Moment trophy contract does not match its catalog")
            restored["trophies"] += conn.execute(
                "INSERT OR IGNORE INTO player_trophies(player_id,trophy_id,unlock_source) "
                "VALUES (?,?,?)", (player_id, trophy_id, "moment:reward_reconciliation"),
            ).rowcount
    return restored


def reconcile_all_owned_moment_rewards(db: Any, data: Any) -> dict[str, int]:
    result = {"players_checked": 0, "titles_restored": 0, "trophies_restored": 0}
    ids = [str(row["player_id"]) for row in db.all(
        "SELECT DISTINCT player_id FROM player_moment_unlocks ORDER BY player_id"
    )]
    for player_id in ids:
        with db.tx() as conn:
            repaired = reconcile_owned_moment_rewards(conn, data, player_id)
            result["titles_restored"] += repaired["titles"]
            result["trophies_restored"] += repaired["trophies"]
            result["players_checked"] += 1
    return result


def _verified_first_cactpot_streak(conn: Any, player_id: str) -> dict[str, Any] | None:
    streak = 0
    for row in conn.execute(
        "SELECT id,wager,payout,created_at FROM gold_saucer_history "
        "WHERE player_id=? AND game='mini_cactpot' ORDER BY created_at,id",
        (player_id,),
    ).fetchall():
        try:
            wager, payout = int(row["wager"]), int(row["payout"])
        except (TypeError, ValueError, OverflowError):
            # Invalid historical rows cannot prove a continuous losing streak.
            streak = 0
            continue
        if wager <= 0:
            continue
        # A damaged old payout row is not evidence of an additional genuine
        # paid loss, nor proof of an unbroken five-ticket sequence.
        if payout < 0:
            streak = 0
            continue
        streak = streak + 1 if payout < wager else 0
        if streak == 5:
            return dict(row)
    return None


def reconcile_verified_history(conn: Any, data: Any, player_id: str) -> list[str]:
    """One-shot, per-player conservative historical reconciliation.

    Cactpot: only five *consecutive paid* losses; earliest crossing evidence.
    Purchase: only one persisted Gil debit in a known genuine shop source.
    Other Moments have no historical evidence and are never inferred.
    """
    already = conn.execute(
        "SELECT 1 FROM player_moment_reconciliation WHERE player_id=?", (player_id,)
    ).fetchone()
    if already:
        return []
    unlocked: list[str] = []
    first_streak = _verified_first_cactpot_streak(conn, player_id)
    if first_streak:
        unlocked.extend(award_settlement(conn, data, player_id,
            f"historic:cactpot:{first_streak['id']}", {
                "event": "saucer_round_settled", "settled": True,
                "game": "mini_cactpot", "paid_net_loss": True,
                "record_id": "longest_cactpot_loss_streak", "record_value": 5,
            }, historical=True, occurred_at=first_streak["created_at"]))
    purchase = conn.execute(
        "SELECT id,amount,source,created_at FROM transactions "
        "WHERE player_id=? AND kind='gil' AND amount<=-25000 "
        "AND source IN ('shop','portal_shop','trading_post_buy') "
        "ORDER BY created_at,id LIMIT 1", (player_id,),
    ).fetchone()
    if purchase and purchase["source"] in _PURCHASE_SOURCES:
        unlocked.extend(award_settlement(conn, data, player_id,
            f"historic:purchase:{purchase['id']}", {
                "event": "purchase_settled", "settled": True,
                "qualifying_shop_purchase": True, "single_transaction": True,
                "record_id": "biggest_purchase", "record_value": -int(purchase["amount"]),
            }, historical=True, occurred_at=purchase["created_at"]))
    conn.execute(
        "INSERT INTO player_moment_reconciliation(player_id) VALUES (?)", (player_id,),
    )
    return unlocked


def reconcile_all_verified_history(db: Any, data: Any) -> dict[str, int]:
    players = 0
    unlocked = 0
    # Reconciliation performed in its own transaction per player so an invalid
    # historical row can never partially award a title or mark a player done.
    player_ids = [str(row["twitch_id"]) for row in db.all("SELECT twitch_id FROM players ORDER BY twitch_id")]
    for player_id in player_ids:
        with db.tx() as conn:
            if conn.execute("SELECT 1 FROM player_moment_reconciliation WHERE player_id=?", (player_id,)).fetchone():
                continue
            unlocked += len(reconcile_verified_history(conn, data, player_id))
            players += 1
    return {"players_reconciled": players, "moments_unlocked": unlocked}

"""The staged Moments contract: rules, spoiler-safe previews and pure matching.

Step 2 deliberately has NO DB access, player writes or live event hooks. Step 3
must call the pure matcher ONLY with server-authored, settled event evidence and
award through one durable, per-player once-only ledger. Never feed it an action
request, a browser payload, or an intermediate combat frame.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from .personal_records import RECORD_SPECS


# Each fact is supplied by a trusted settlement producer, never by a player.
# The explicit allowlist prevents a catalog typo becoming an unobtainable title.
EVENT_FACTS: dict[str, dict[str, type]] = {
    "combat_victory": {
        "player_alive": bool, "final_hp": int,
    },
    "combat_finishing_blow": {
        "direct_hit": bool, "target_defeated": bool, "poison_active_at_hit": bool,
        "damage_dealt": int, "target_hp_before_hit": int, "target_max_hp": int,
    },
    "combat_player_ko": {
        "player_knocked_out": bool, "self_item_consumed": bool,
        "self_item_shop_price_gil": int, "item_targeted_self": bool,
        "self_item_restorative": bool, "ko_source": str,
        "same_battle": bool, "next_hostile_action_caused_ko": bool,
        "player_actions_since_item": int, "player_actions_completed": int,
        "first_hostile_action_of_encounter": bool,
    },
    "world_event_victory": {
        "player_alive": bool, "participant_count": int, "living_party_count": int,
        "highest_survivor_hp_pct_raw": float,
    },
    "saucer_round_settled": {
        "game": str, "paid_net_loss": bool, "record_id": str, "record_value": int,
    },
    "solo_boss_victory": {
        "player_alive": bool, "solo_encounter": bool, "merc_assisted": bool,
        "boss_effective_level_gap": int,
    },
    "raid_victory": {
        "player_alive": bool, "party_size_at_start": int, "living_party_count": int,
        "player_contribution_eligible": bool, "player_revived_during_raid": bool,
        "player_dealt_final_blow": bool,
    },
    "purchase_settled": {
        "qualifying_shop_purchase": bool, "single_transaction": bool,
        "record_id": str, "record_value": int,
    },
    "venture_completed": {
        "successful": bool, "player_alive": bool,
        "final_hp_pct_pre_recovery_raw": float, "consumables_used": int,
    },
}
VALID_TIERS = frozenset({"bronze", "silver", "gold", "crystal"})
VALID_RARITIES = frozenset({"common", "uncommon", "rare", "epic", "legendary"})
VALID_OPS = frozenset({"eq", "gte", "lte", "gte_multiple"})
# Only these precise metrics have reproducible saved history from Step 1.
BACKFILL_RECORDS = frozenset({"longest_cactpot_loss_streak", "biggest_purchase"})
RECORD_IDS = frozenset(spec[0] for spec in RECORD_SPECS)


def _type_is(value: Any, expected: type) -> bool:
    # bool is a subclass of int, but True is not a valid Gil amount or HP.
    if expected is float:
        return type(value) in (int, float) and math.isfinite(value)
    return type(value) is expected


def validate_moment_catalog(
    moments: Mapping[str, dict[str, Any]],
    moment_titles: Mapping[str, dict[str, Any]],
    achievements: Mapping[str, dict[str, Any]],
    regular_titles: Mapping[str, dict[str, Any]],
) -> list[str]:
    """Validate active-contract readiness without activating new rewards."""
    errors: list[str] = []
    used_titles: set[str] = set()
    used_badges: set[str] = set()
    used_trophies: set[str] = set()
    regular_achievement_names = {a["name"].casefold() for a in achievements.values()}
    regular_title_names = {t["name"].casefold() for t in regular_titles.values()}
    reserved_title_names: set[str] = set()
    moment_names: set[str] = set()

    for title_id, title in moment_titles.items():
        if title_id in regular_titles or title_id in achievements:
            errors.append(f"moment title {title_id}: collides with a live catalog id")
        if not title_id.startswith("moment_title_"):
            errors.append(f"moment title {title_id}: id must start with moment_title_")
        if not str(title.get("name") or "").strip() or not str(title.get("description") or "").strip():
            errors.append(f"moment title {title_id}: missing copy")
        if title.get("name", "").casefold() in regular_title_names:
            errors.append(f"moment title {title_id}: duplicates a live title name")
        if str(title.get("name") or "").casefold() in reserved_title_names:
            errors.append(f"moment title {title_id}: duplicate reserved title name")
        reserved_title_names.add(str(title.get("name") or "").casefold())
        if title.get("rarity") not in VALID_RARITIES:
            errors.append(f"moment title {title_id}: unsupported rarity")
        if title.get("source") != "Moment":
            errors.append(f"moment title {title_id}: source must be Moment")

    for moment_id, moment in moments.items():
        where = f"moment {moment_id}"
        if not moment_id.startswith("moment_") or moment_id in achievements or moment_id in regular_titles:
            errors.append(f"{where}: invalid/colliding id")
        name = str(moment.get("name") or "").strip()
        if not name or not str(moment.get("description") or "").strip():
            errors.append(f"{where}: missing player-facing copy")
        if name.casefold() in moment_names or name.casefold() in regular_achievement_names:
            errors.append(f"{where}: duplicate moment/achievement name")
        moment_names.add(name.casefold())
        if type(moment.get("secret")) is not bool:
            errors.append(f"{where}: secret must be true or false")
        if moment.get("tier") not in VALID_TIERS:
            errors.append(f"{where}: invalid tier")
        if not str(moment.get("category") or "").strip():
            errors.append(f"{where}: category is required")
        if moment.get("trigger") not in EVENT_FACTS:
            errors.append(f"{where}: unknown trusted settlement event")
            continue

        condition = moment.get("condition") or {}
        if condition.get("type") not in {"event_facts", "record_threshold"}:
            errors.append(f"{where}: unsupported condition type")
        if not isinstance(condition.get("rules"), list) or not condition["rules"]:
            errors.append(f"{where}: at least one rule is required")
        facts = EVENT_FACTS[moment["trigger"]]
        for i, rule in enumerate(condition.get("rules") or []):
            field = rule.get("field")
            op = rule.get("op")
            if field not in facts or op not in VALID_OPS:
                errors.append(f"{where}: rule {i} uses unknown field/operator")
                continue
            if op == "gte_multiple":
                other = rule.get("other_field")
                factor = rule.get("multiplier")
                if (other not in facts or facts[field] is not int or facts[other] is not int
                        or type(factor) is not int or factor < 2):
                    errors.append(f"{where}: rule {i} requires two integer facts and multiplier >=2")
            elif not _type_is(rule.get("value"), facts[field]):
                errors.append(f"{where}: rule {i} value has wrong type")
            elif op in {"gte", "lte"} and facts[field] not in (int, float):
                errors.append(f"{where}: rule {i} numeric operator on non-numeric fact")

        backfill = moment.get("backfill")
        if condition.get("type") == "record_threshold":
            record_id = condition.get("record_id")
            if record_id not in RECORD_IDS or record_id not in BACKFILL_RECORDS:
                errors.append(f"{where}: no proven saved-history metric for record threshold")
            if backfill != "verified_saved_history":
                errors.append(f"{where}: saved record threshold needs explicit backfill policy")
            if not any(r.get("field") == "record_id" and r.get("op") == "eq"
                       and r.get("value") == record_id for r in condition.get("rules") or []):
                errors.append(f"{where}: record_id guard missing")
            if not any(r.get("field") == "record_value" and r.get("op") == "gte"
                       for r in condition.get("rules") or []):
                errors.append(f"{where}: record threshold guard missing")
        elif backfill != "none":
            errors.append(f"{where}: event-only Moments must not claim historical backfill")

        reward = moment.get("reward") or {}
        title_id = reward.get("title_id")
        badge_id = reward.get("badge_id")
        if title_id not in moment_titles or title_id in used_titles:
            errors.append(f"{where}: missing or reused reserved title")
        used_titles.add(title_id)
        if not isinstance(badge_id, str) or not badge_id.startswith("moment_badge_") or badge_id in used_badges:
            errors.append(f"{where}: missing or reused badge key")
        used_badges.add(badge_id)
        trophy_id = reward.get("trophy_candidate_id")
        if trophy_id is not None:
            if not isinstance(trophy_id, str) or not trophy_id.startswith("moment_trophy_") or trophy_id in used_trophies:
                errors.append(f"{where}: invalid or duplicate reserved trophy key")
            used_trophies.add(trophy_id)
        if reward.get("currency") is not None or reward.get("stats") is not None:
            errors.append(f"{where}: Moments must not add economic or permanent stat rewards")
        if moment.get("secret") and moment.get("sealed_hint") and len(moment["sealed_hint"]) > 90:
            errors.append(f"{where}: sealed hint is too long")

    unused_titles = set(moment_titles) - used_titles
    if unused_titles:
        errors.append("orphan moment titles: " + ", ".join(sorted(unused_titles)))
    return errors


def _rule_matches(rule: dict[str, Any], facts: Mapping[str, Any]) -> bool:
    field = rule["field"]
    if field not in facts:
        return False
    observed = facts[field]
    if rule["op"] == "gte_multiple":
        other = facts.get(rule["other_field"])
        return (type(observed) is int and type(other) is int and other > 0
                and observed >= other * rule["multiplier"])
    reference = rule["value"]
    expected = float if type(reference) in (int, float) and type(reference) is float else type(reference)
    if not _type_is(observed, expected):
        return False
    if rule["op"] == "eq":
        return observed == reference
    if rule["op"] == "gte":
        return observed >= reference
    if rule["op"] == "lte":
        return observed <= reference
    return False


def matches_settlement(moment: Mapping[str, Any], settled_event: Mapping[str, Any]) -> bool:
    """Pure candidate check. Caller must provide verified SERVER settlement facts.

    This function never awards, updates progress, trusts a browser or validates
    settlement authenticity. Step 3 will provide that boundary and persistence.
    """
    if moment.get("trigger") != settled_event.get("event") or settled_event.get("settled") is not True:
        return False
    condition = moment["condition"]
    if condition["type"] not in {"event_facts", "record_threshold"}:
        return False
    return all(_rule_matches(rule, settled_event) for rule in condition["rules"])


def public_moments_view(
    moments: Mapping[str, dict[str, Any]],
    moment_titles: Mapping[str, dict[str, Any]],
    unlocked_ids: set[str] | frozenset[str],
) -> list[dict[str, Any]]:
    """Safe future Portal projection; never transmits a locked secret's real id.

    Award timestamps will be added from the Step 3 durable ledger. Until then
    this preview is data-only; NO Portal endpoint calls it in Step 2.
    """
    output: list[dict[str, Any]] = []
    for slot, (moment_id, moment) in enumerate(moments.items(), start=1):
        unlocked = moment_id in unlocked_ids
        sealed = bool(moment["secret"]) and not unlocked
        if sealed:
            output.append({
                "id": f"sealed_slot_{slot:02d}", "name": "Undiscovered Moment",
                "description": "The Guild hasn't heard this story yet.",
                "category": "Mystery", "tier": None, "secret": True,
                "unlocked": False, "hint": moment.get("sealed_hint") or None,
                "reward_title": None, "badge_id": None, "trophy_candidate_id": None,
            })
            continue
        title = moment_titles[moment["reward"]["title_id"]]
        output.append({
            "id": moment_id, "name": moment["name"], "description": moment["description"],
            "category": moment["category"], "tier": moment["tier"],
            "secret": bool(moment["secret"]), "unlocked": unlocked, "hint": None,
            "reward_title": title["name"], "badge_id": moment["reward"]["badge_id"],
            "trophy_candidate_id": moment["reward"].get("trophy_candidate_id"),
        })
    return output

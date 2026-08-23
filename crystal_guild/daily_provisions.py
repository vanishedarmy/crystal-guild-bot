from __future__ import annotations

from typing import Any

# Twitch subscriber perks intentionally start small and predictable.  The
# subscriber-status service is reusable by future systems, but Hotfix 2 applies
# the perk to Daily Guild Provisions only so normal RPG balance does not become
# dependent on a paid subscription.
SUBSCRIBER_PERKS: dict[int, dict[str, Any]] = {
    0: {"label": "Standard", "gil_multiplier": 1.00, "rolls": 1},
    1: {"label": "Subscriber Tier 1", "gil_multiplier": 1.10, "rolls": 2},
    2: {"label": "Subscriber Tier 2", "gil_multiplier": 1.20, "rolls": 3},
    3: {"label": "Subscriber Tier 3", "gil_multiplier": 1.30, "rolls": 4},
}

_RARITY_WEIGHT = {
    "common": 8,
    "uncommon": 4,
    "rare": 2,
    "epic": 1,
}


def normalize_subscriber_tier(value: Any) -> int:
    """Normalize Twitch/Crystal-Guild tier values to 0..3."""
    text = str(value or "").strip().lower()
    aliases = {
        "1000": 1,
        "2000": 2,
        "3000": 3,
        "tier 1": 1,
        "tier1": 1,
        "tier 2": 2,
        "tier2": 2,
        "tier 3": 3,
        "tier3": 3,
    }
    if text in aliases:
        return aliases[text]
    try:
        return max(0, min(3, int(text)))
    except (TypeError, ValueError):
        return 0


def subscriber_perk(tier: Any) -> dict[str, Any]:
    value = normalize_subscriber_tier(tier)
    result = dict(SUBSCRIBER_PERKS[value])
    result["tier"] = value
    result["gil_bonus_percent"] = int(round((float(result["gil_multiplier"]) - 1.0) * 100))
    return result


def daily_gil_with_perk(low: int, high: int, tier: Any) -> tuple[int, int]:
    perk = subscriber_perk(tier)
    mult = float(perk["gil_multiplier"])
    return max(1, int(round(int(low) * mult))), max(1, int(round(int(high) * mult)))


def _eligible_consumables(items: dict[str, dict[str, Any]], level: int) -> list[dict[str, Any]]:
    level = max(1, int(level))
    result: list[dict[str, Any]] = []
    for item in items.values():
        if str(item.get("type") or "").lower() != "consumable":
            continue
        # Daily provisions should feel useful without bypassing rare encounter,
        # raid, relic or artifact rewards.  Only normal shop consumables whose
        # listed shop level has been reached are eligible.
        if not item.get("shop"):
            continue
        if int(item.get("shop_level") or 1) > level:
            continue
        if str(item.get("rarity") or "common").lower() not in _RARITY_WEIGHT:
            continue
        result.append(item)
    return result


def _eligible_materials(items: dict[str, dict[str, Any]], level: int) -> list[dict[str, Any]]:
    level = max(1, int(level))
    # Materials do not currently carry min-level metadata, so use a bounded
    # value ceiling as a gentle proxy.  Common/uncommon crafting materials can
    # appear; boss/relic/artifact materials remain encounter rewards.
    value_ceiling = 45 + (level * 8)
    result: list[dict[str, Any]] = []
    for item in items.values():
        if str(item.get("type") or "").lower() != "material":
            continue
        rarity = str(item.get("rarity") or "common").lower()
        if rarity not in {"common", "uncommon"}:
            continue
        if int(item.get("price") or 0) > value_ceiling:
            continue
        result.append(item)
    return result


def _weighted_choice(rng: Any, entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        raise ValueError("daily provision pool is empty")
    weighted = [(entry, max(1, int(_RARITY_WEIGHT.get(str(entry.get("rarity") or "common").lower(), 1)))) for entry in entries]
    total = sum(weight for _, weight in weighted)
    ticket = int(rng.randint(1, total))
    cursor = 0
    for entry, weight in weighted:
        cursor += weight
        if ticket <= cursor:
            return entry
    return weighted[-1][0]


def _quantity_for(rng: Any, item: dict[str, Any]) -> int:
    rarity = str(item.get("rarity") or "common").lower()
    item_type = str(item.get("type") or "").lower()
    if item_type == "material":
        return int(rng.randint(2, 4)) if rarity == "common" else int(rng.randint(1, 2))
    price = int(item.get("price") or 0)
    if rarity == "common" and price <= 100:
        return int(rng.randint(1, 3))
    if rarity in {"common", "uncommon"} and price <= 400:
        return int(rng.randint(1, 2))
    return 1


def roll_daily_provisions(
    items: dict[str, dict[str, Any]],
    level: int,
    rng: Any,
    tier: Any = 0,
) -> list[dict[str, Any]]:
    """Roll and merge level-appropriate Daily Guild Provision bundles."""
    perk = subscriber_perk(tier)
    rolls = int(perk["rolls"])
    consumables = _eligible_consumables(items, level)
    materials = _eligible_materials(items, level)
    if not consumables:
        potion = items.get("potion")
        if potion:
            consumables = [potion]
    merged: dict[str, dict[str, Any]] = {}

    for _ in range(rolls):
        # Three quarters of provision rolls are practical consumables; the
        # remainder are basic crafting materials.  If one pool is empty, use
        # the other without dropping the reward roll.
        choose_material = bool(materials) and (not consumables or int(rng.randint(1, 100)) <= 25)
        pool = materials if choose_material else consumables
        if not pool:
            pool = materials or consumables
        item = _weighted_choice(rng, pool)
        quantity = _quantity_for(rng, item)
        item_id = str(item["id"])
        if item_id not in merged:
            merged[item_id] = {
                "item_id": item_id,
                "name": str(item.get("name") or item_id),
                "quantity": 0,
                "type": str(item.get("type") or ""),
                "rarity": str(item.get("rarity") or "common"),
            }
        merged[item_id]["quantity"] += quantity

    return list(merged.values())


def provision_preview(level: int, tier: Any) -> dict[str, Any]:
    perk = subscriber_perk(tier)
    rolls = int(perk["rolls"])
    bundle_word = "bundle" if rolls == 1 else "bundles"
    return {
        "provision_rolls": rolls,
        "provision_summary": f"{rolls} random level-appropriate provision {bundle_word}",
        "subscriber_tier": int(perk["tier"]),
        "subscriber_label": str(perk["label"]),
        "subscriber_gil_bonus_percent": int(perk["gil_bonus_percent"]),
        "level": max(1, int(level)),
    }

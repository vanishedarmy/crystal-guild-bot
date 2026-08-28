from __future__ import annotations

from typing import Any

DEPTHS: dict[str, dict[str, Any]] = {
    "scout": {
        "id": "scout", "name": "Scout", "stages": 3, "travel_seconds": 4 * 60,
        "reward_mult": 0.90, "description": "A short survey with low commitment and modest rewards.",
    },
    "journey": {
        "id": "journey", "name": "Journey", "stages": 5, "travel_seconds": 6 * 60,
        "reward_mult": 1.05, "description": "The standard Expedition route with balanced risk and reward.",
    },
    "deep": {
        "id": "deep", "name": "Deep Expedition", "stages": 8, "travel_seconds": 8 * 60,
        "reward_mult": 1.20, "description": "A long push into dangerous territory with the best standard rewards.",
    },
}

ROUTES: dict[str, dict[str, Any]] = {
    "safe": {
        "id": "safe", "name": "Safe Route", "reward_mult": 0.90,
        "risk": "Low", "rare_event_chance": 0.02, "rare_encounter_mult": 0.65,
        "signals": ["Less combat", "Fewer hazards", "Steadier discoveries"],
        "description": "Lower combat and hazard pressure. Slower rewards, safer footing.",
        "weight_mult": {"combat": 0.72, "hazard": 0.62, "treasure": 0.85, "resource": 0.95, "discovery": 1.10},
    },
    "unknown": {
        "id": "unknown", "name": "Unknown Route", "reward_mult": 1.00,
        "risk": "Balanced", "rare_event_chance": 0.05, "rare_encounter_mult": 1.00,
        "signals": ["Balanced encounters", "Balanced rewards", "Unpredictable events"],
        "description": "Balanced risk. You take the road as it comes.",
        "weight_mult": {},
    },
    "deep": {
        "id": "deep", "name": "Push Deeper", "reward_mult": 1.20,
        "risk": "High", "rare_event_chance": 0.09, "rare_encounter_mult": 1.75,
        "signals": ["More combat", "More hazards", "Better rare-event odds"],
        "description": "More danger, but much stronger treasure and material opportunities.",
        "weight_mult": {"combat": 1.22, "hazard": 1.25, "treasure": 1.30, "resource": 1.18, "discovery": 1.10},
    },
}

BONUS_STAGES = 2
BASE_DEFEAT_CACHE_KEEP = 0.70
MAX_DEFEAT_CACHE_KEEP = 0.85


def effective_travel_seconds(base_seconds: int, traits: set[str]) -> int:
    seconds = max(30, int(base_seconds))
    if "fleet_feet" in traits:
        seconds = int(round(seconds * 0.85))
    return max(30, seconds)


def event_weights(region: dict[str, Any], route_id: str, traits: set[str]) -> tuple[list[str], list[float]]:
    raw = dict(region.get("event_weights") or {})
    route = ROUTES.get(route_id, ROUTES["unknown"])
    multipliers = dict(route.get("weight_mult") or {})
    if "steady_strider" in traits:
        multipliers["hazard"] = float(multipliers.get("hazard", 1.0)) * 0.70
    if "keen_eye" in traits:
        multipliers["discovery"] = float(multipliers.get("discovery", 1.0)) * 1.25
    if "forager" in traits:
        multipliers["resource"] = float(multipliers.get("resource", 1.0)) * 1.25
    if "lucky_plume" in traits:
        multipliers["treasure"] = float(multipliers.get("treasure", 1.0)) * 1.15
        multipliers["chocobo"] = float(multipliers.get("chocobo", 1.0)) * 1.10
    kinds: list[str] = []
    weights: list[float] = []
    for kind, value in raw.items():
        weight = max(0.0, float(value or 0)) * float(multipliers.get(kind, 1.0))
        if weight > 0:
            kinds.append(str(kind))
            weights.append(weight)
    return kinds, weights


def defeat_cache_keep(traits: set[str]) -> float:
    value = BASE_DEFEAT_CACHE_KEEP
    if "steady_strider" in traits:
        value += 0.10
    if "lucky_plume" in traits:
        value += 0.05
    return min(MAX_DEFEAT_CACHE_KEEP, value)

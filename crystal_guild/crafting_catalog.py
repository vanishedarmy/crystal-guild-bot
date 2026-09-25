"""Crafting Reforged catalog presentation and source indexing (1.9.4).

Source hints are built from real content tables, never invented from item rarity.
This module has no database dependencies; the game still validates and commits
all ingredient/currency spending under its existing transaction protocol.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .retainer import RETAINER_ASSIGNMENTS

CATEGORIES = ("field", "weapons", "armor", "accessories")


def recipe_category(recipe: dict[str, Any], item: dict[str, Any]) -> str:
    explicit = str(recipe.get("category") or "").strip().lower()
    if explicit in CATEGORIES:
        return explicit
    return {"consumable": "field", "weapon": "weapons", "armor": "armor", "accessory": "accessories"}.get(
        str(item.get("type") or ""), "field"
    )


def recipe_subcategory(item: dict[str, Any]) -> str:
    item_type = str(item.get("type") or "")
    if item_type == "weapon":
        return str(item.get("gear_family") or "Other").replace("_", " ").title()
    if item_type in ("armor", "accessory"):
        return "Equipment"
    if item.get("id") in {"trail_rations", "tent"}:
        return "Camp supplies"
    effects = (item.get("use") or {}).get("effects") or []
    effect_types = {str(effect.get("type") or "") for effect in effects}
    if "damage" in effect_types:
        return "Battle items"
    if "status" in effect_types:
        return "Battle buffs"
    if "cleanse" in effect_types:
        return "Status cures"
    if effect_types & {"heal_hp", "restore_mp", "restore_ap", "revive"}:
        return "Restoratives"
    return "Field supplies"


def build_source_index(game_data: Any) -> dict[str, list[str]]:
    """Small, deterministic acquisition hints for recipe ingredient detail panels."""
    hints: dict[str, list[str]] = defaultdict(list)

    def add(item_id: str, label: str) -> None:
        if item_id and label not in hints[item_id]:
            hints[item_id].append(label)

    for item in game_data.items.values():
        if item.get("shop"):
            add(str(item["id"]), "Moogle Emporium")
    for route in RETAINER_ASSIGNMENTS:
        for item_id, _ in route.get("pool", ()):
            add(str(item_id), f"Retainer: {route['name']} (Rank {route['rank_required']}+)")
    for group, label in ((game_data.monsters, "Monster"), (game_data.bosses, "Boss")):
        for creature in sorted(group.values(), key=lambda row: (int(row.get("level", 1) or 1), str(row.get("name") or ""))):
            for drop in (*creature.get("drops", []), *creature.get("pity_drops", [])):
                add(str(drop.get("item_id") or ""), f"{label}: {creature.get('name', creature['id'])}")
    for hunt in game_data.hunts.values():
        if hunt.get("first_clear_item"):
            add(str(hunt["first_clear_item"]), f"Hunt: {hunt.get('name', hunt['id'])} first clear")
    for recipe in game_data.recipes.values():
        out = recipe.get("output") or {}
        if out.get("item_id"):
            add(str(out["item_id"]), "Crafting")
    return dict(hints)

"""Schema validation for the static Bestiary research overlay.

This module intentionally does not compute player progress or award any rewards.
`monsters.json` remains authoritative for all gameplay values. The overlay
only defines stable classification, field-guide text and milestone visibility.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

SCHEMA_VERSION = 1
CATEGORIES = frozenset({'regional', 'hunt', 'expedition'})
ALLOWED_REVEALS = frozenset({
    'name', 'level', 'portrait', 'habitats', 'family', 'weakness',
    'combat_profile', 'active_skill', 'drops', 'lore', 'mastery',
})
COMBAT_VALUES = frozenset({
    'name', 'level', 'weakness', 'resistances', 'resistance', 'drops',
    'combat_profile', 'active_skill', 'special', 'hp', 'attack',
    'defense', 'spirit', 'xp', 'jp', 'gil',
})
EXPECTED_MILESTONES = {
    'regional': (1, 3, 5, 10, 15, 20),
    'hunt': (1, 2, 3, 5),
    'expedition': (1, 2, 3),
}


def validate_research_overlay(
    overlay: dict[str, Any],
    *,
    monsters: dict[str, dict[str, Any]],
    regions: dict[str, dict[str, Any]],
    expeditions: dict[str, dict[str, Any]],
    hunts: dict[str, dict[str, Any]],
) -> list[str]:
    """Return errors without mutating the supplied source catalogs.

    Region encounter lists and expedition boss IDs determine official habitat
    assignments. Hunt survey territories are editorial field-guide placements,
    *not* assertions about random-world encounter tables.
    """
    errors: list[str] = []
    if not isinstance(overlay, dict):
        return ['bestiary_research: root must be an object']
    if overlay.get('schema_version') != SCHEMA_VERSION:
        errors.append(f'bestiary_research: unsupported schema_version {overlay.get("schema_version")!r}')
    if overlay.get('namespace') != 'base':
        errors.append("bestiary_research: namespace must be 'base'")

    entries = overlay.get('entries')
    families = overlay.get('families')
    rules = overlay.get('tiers')
    if not isinstance(entries, dict):
        return errors + ['bestiary_research: entries must be an object keyed by monster ID']
    if not isinstance(families, dict):
        return errors + ['bestiary_research: families must be an object keyed by family ID']
    if not isinstance(rules, dict):
        return errors + ['bestiary_research: tiers must be an object keyed by category']

    missing = set(monsters) - set(entries)
    extra = set(entries) - set(monsters)
    if missing: errors.append(f'bestiary_research: missing entries {sorted(missing)!r}')
    if extra: errors.append(f'bestiary_research: unknown entries {sorted(extra)!r}')

    hunt_ids = {str(hunt.get('monster_id') or '') for hunt in hunts.values()}
    expedition_boss_to_region = {
        str(region.get('boss', {}).get('monster_id') or ''): region_id
        for region_id, region in expeditions.items()
    }
    if hunt_ids & set(expedition_boss_to_region):
        errors.append('bestiary_research: hunt and expedition bosses must have disjoint IDs')
    official_habitats: dict[str, set[str]] = defaultdict(set)
    for region_id, region in regions.items():
        for encounter in region.get('encounters', []):
            official_habitats[str(encounter.get('monster_id') or '')].add(region_id)

    if set(rules) != CATEGORIES:
        errors.append(f'bestiary_research: tier categories must be exactly {sorted(CATEGORIES)!r}')
    for category, expected in EXPECTED_MILESTONES.items():
        config = rules.get(category)
        milestones = config.get('milestones') if isinstance(config, dict) else None
        if not isinstance(milestones, list):
            errors.append(f'bestiary_research: {category} milestones must be an array')
            continue
        counts = [row.get('defeats') if isinstance(row, dict) else None for row in milestones]
        if tuple(counts) != expected:
            errors.append(f'bestiary_research: {category} thresholds must be {expected!r}, got {counts!r}')
        keys = [row.get('key') for row in milestones if isinstance(row, dict)]
        if len(set(keys)) != len(milestones):
            errors.append(f'bestiary_research: {category} milestone keys must be unique')
        for milestone in milestones:
            if not isinstance(milestone, dict):
                errors.append(f'bestiary_research: {category} milestone must be an object')
                continue
            reveal = milestone.get('reveal')
            if not isinstance(reveal, list) or not reveal or any(field not in ALLOWED_REVEALS for field in reveal):
                errors.append(f'bestiary_research: {category} {milestone.get("key")}: invalid reveal fields')
        if milestones and milestones[-1].get('reveal') != ['mastery']:
            errors.append(f'bestiary_research: {category} final milestone must grant mastery only')

    for family_id, family in families.items():
        if not isinstance(family, dict) or not str(family.get('name') or '').strip():
            errors.append(f'bestiary_research: family {family_id!r} requires a display name')

    for monster_id, entry in entries.items():
        if not isinstance(entry, dict):
            errors.append(f'bestiary_research: monster {monster_id!r} must be an object')
            continue
        duplicate_gameplay = COMBAT_VALUES & set(entry)
        if duplicate_gameplay:
            errors.append(f'bestiary_research: {monster_id}: duplicated gameplay fields {sorted(duplicate_gameplay)!r}')
        if set(entry) != {'category', 'family', 'habitats', 'habitat_provenance', 'lore'}:
            errors.append(f'bestiary_research: {monster_id}: invalid/missing field-guide keys')
        category = entry.get('category')
        expected_category = (
            'hunt' if monster_id in hunt_ids else
            'expedition' if monster_id in expedition_boss_to_region else 'regional'
        )
        if category != expected_category:
            errors.append(f'bestiary_research: {monster_id}: expected {expected_category}, got {category!r}')
        if entry.get('family') not in families:
            errors.append(f'bestiary_research: {monster_id}: unknown family {entry.get("family")!r}')
        if not isinstance(entry.get('lore'), str) or len(entry['lore'].strip()) < 20:
            errors.append(f'bestiary_research: {monster_id}: missing or short lore')
        habitats = entry.get('habitats')
        if not isinstance(habitats, list) or not habitats or any(not isinstance(h, str) for h in habitats):
            errors.append(f'bestiary_research: {monster_id}: habitats must be nonempty string array')
            continue
        if len(set(habitats)) != len(habitats):
            errors.append(f'bestiary_research: {monster_id}: duplicate habitats')
        source = entry.get('habitat_provenance')
        if expected_category == 'regional':
            if source != 'region_encounters':
                errors.append(f'bestiary_research: {monster_id}: regional habitat provenance must be region_encounters')
            if set(habitats) != official_habitats.get(monster_id, set()):
                errors.append(f'bestiary_research: {monster_id}: region habitat drift; expected {sorted(official_habitats.get(monster_id, set()))!r}')
        elif expected_category == 'expedition':
            if source != 'expedition_registry':
                errors.append(f'bestiary_research: {monster_id}: expedition habitat provenance must be expedition_registry')
            if habitats != [expedition_boss_to_region[monster_id]]:
                errors.append(f'bestiary_research: {monster_id}: incorrect expedition habitat')
        else:
            if source != 'guild_survey':
                errors.append(f'bestiary_research: {monster_id}: Hunt habitats must be marked guild_survey')
            if set(habitats) - set(regions):
                errors.append(f'bestiary_research: {monster_id}: Hunt survey contains unknown region')

    rewards = overlay.get('rewards')
    if rewards != {'mastery_seal': True, 'research_points': 1, 'material_drop_bonus_enabled': False}:
        errors.append('bestiary_research: unexpected pending reward policy')
    return errors

"""Advanced Ascension encounter rules (deterministic, save-safe; no timers)."""
from __future__ import annotations
from typing import Any

ELEMENTS = frozenset({'fire', 'ice', 'lightning', 'water', 'earth', 'wind', 'holy', 'dark'})


def phase_for_hp(config: dict[str, Any], hp: int, maximum: int) -> dict[str, Any]:
    """Select the deepest phase reached. Never mutates the catalog."""
    phases = list(config.get('phases') or [])
    ratio = max(0, hp) / max(1, maximum)
    selected: dict[str, Any] = {}
    for phase in sorted(phases, key=lambda row: float(row.get('threshold', 1)), reverse=True):
        if ratio <= float(phase.get('threshold', 1)) + 1e-9:
            selected = phase
    return selected


def affinities(config: dict[str, Any], hp: int, maximum: int) -> dict[str, list[str]]:
    phase = phase_for_hp(config, hp, maximum)
    base = dict(config.get('affinities') or {})
    override = dict(phase.get('affinities') or {})
    return {key: [str(x).lower() for x in (override.get(key, base.get(key, [])) or [])]
            for key in ('weak', 'resist')}


def affinity_multiplier(config: dict[str, Any], hp: int, maximum: int, element: str | None) -> tuple[float, str]:
    element = str(element or '').lower()
    if element not in ELEMENTS:
        return 1.0, ''
    profile = affinities(config, hp, maximum)
    if element in profile['resist']:
        return 0.65, 'RESISTED'
    if element in profile['weak']:
        return 1.40, 'WEAKNESS'
    return 1.0, ''


def telegraph_for_round(config: dict[str, Any], round_no: int) -> dict[str, Any] | None:
    attack = config.get('telegraph') or {}
    every = int(attack.get('every', 0) or 0)
    if every < 2 or round_no < every or round_no % every:
        return None
    return {
        'kind': 'dungeon_telegraph', 'name': str(attack.get('name') or 'Guardian Onslaught'),
        'label': f"WARNING — {attack.get('name') or 'Guardian Onslaught'}! DEFEND to reduce damage.",
        'power': max(0.1, min(2.0, float(attack.get('power', 1.25)))),
        'scaling': str(attack.get('scaling') or 'magic'),
    }


def validate_config(config: dict[str, Any], where: str) -> None:
    if not config:
        return
    for row in [config.get('affinities') or {}, *[p.get('affinities') or {} for p in config.get('phases', [])]]:
        weak, resist = [set(str(x).lower() for x in row.get(k, [])) for k in ('weak','resist')]
        if not (weak | resist) <= ELEMENTS or weak & resist:
            raise ValueError(f'{where}: invalid/overlapping elemental affinities')
    thresholds = [float(p.get('threshold', 0)) for p in config.get('phases', [])]
    if thresholds and (thresholds[0] != 1 or thresholds != sorted(thresholds, reverse=True)
                       or len(thresholds) != len(set(thresholds)) or min(thresholds) <= 0):
        raise ValueError(f'{where}: phases require unique descending thresholds beginning at 1')
    for p in config.get('phases', []):
        if float(p.get('pressure', 1)) < 0.5 or float(p.get('pressure', 1)) > 1.5:
            raise ValueError(f'{where}: phase pressure outside safe bounds')
    attack = config.get('telegraph') or {}
    if attack and (int(attack.get('every', 0)) < 2 or float(attack.get('power', 0)) > 2.0
                   or str(attack.get('scaling') or 'magic') not in ('magic', 'physical')):
        raise ValueError(f'{where}: telegraph outside balance limits')

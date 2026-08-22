"""Player-facing Active Battle presentation helpers.

Presentation remains separate from combat resolution. Nothing in this
module mutates battle state or decides outcomes; it only turns already-resolved
state/events into concise Twitch-friendly text.  Future readability changes
should generally start here instead of editing combat math in ``engine.py``.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from .active_battle import format_statuses


# Twitch accepts longer messages, but keeping individual battle lines well below
# the hard ceiling gives the sender room to pack multiple related lines safely.
ROUND_SUMMARY_TARGET = 330
STATUS_LINE_TARGET = 420


def compact_number(value: int | float) -> str:
    """Return a short human-readable integer without hiding meaningful scale."""
    number = int(value)
    sign = "-" if number < 0 else ""
    number = abs(number)
    if number < 1_000:
        return f"{sign}{number}"
    if number < 1_000_000:
        scaled = number / 1_000
        text = f"{scaled:.1f}".rstrip("0").rstrip(".")
        return f"{sign}{text}K"
    scaled = number / 1_000_000
    text = f"{scaled:.1f}".rstrip("0").rstrip(".")
    return f"{sign}{text}M"


def percent(current: int | float, maximum: int | float) -> int:
    if int(maximum) <= 0:
        return 0
    return max(0, min(100, int(round((float(current) / float(maximum)) * 100))))


def resource_text(label: str, current: int, maximum: int, *, include_percent: bool = True) -> str:
    body = f"{label} {compact_number(current)}/{compact_number(maximum)}"
    if include_percent:
        body += f" ({percent(current, maximum)}%)"
    return body


def status_text(statuses: dict[str, Any] | None, *, limit: int = 3) -> str:
    formatted = format_statuses(statuses or {}, limit=limit)
    return f"[{formatted}]" if formatted and formatted not in {"—", "-"} and formatted.lower() != "none" else "[Clear]"



def combatant_text(
    row: dict[str, Any],
    *,
    action_label: str | None = None,
    status_limit: int = 2,
) -> str:
    name = str(row.get("name") or row.get("username") or "Hero")
    hp = int(row.get("hp", 0))
    max_hp = max(1, int(row.get("max_hp", 1)))
    if hp <= 0:
        return f"{name} KO [--]"
    resources: list[str] = []
    max_ap = max(0, int(row.get("max_ap", 0)))
    if max_ap:
        ap = max(0, int(row.get("ap", 0)))
        resources.append(f"AP {compact_number(ap)}/{compact_number(max_ap)}")
    max_mp = max(0, int(row.get("max_mp", 0)))
    if max_mp:
        mp = max(0, int(row.get("mp", 0)))
        resources.append(f"MP {compact_number(mp)}/{compact_number(max_mp)}")
    resource_text = " ".join(resources) if resources else "RES --"
    action = action_label or ("QUEUED" if row.get("action") else "WAIT")
    return (
        f"{name} HP {compact_number(hp)}/{compact_number(max_hp)} ({percent(hp, max_hp)}%) "
        f"{resource_text} {status_text(row.get('statuses'), limit=status_limit)} [{action}]"
    )


def party_status_lines(
    roster: Iterable[dict[str, Any]],
    *,
    action_labels: dict[str, str] | None = None,
    max_chars: int = STATUS_LINE_TARGET,
) -> list[str]:
    """Pack player vitals into readable lines for the on-demand status command."""
    rows = list(roster)
    if not rows:
        return ["PARTY — no heroes remain standing."]
    pieces: list[str] = []
    for row in rows:
        pid = str(row.get("player_id") or row.get("id") or row.get("twitch_id") or "")
        label = action_labels.get(pid) if action_labels else None
        pieces.append(combatant_text(row, action_label=label))

    lines: list[str] = []
    current = "PARTY — "
    for piece in pieces:
        candidate = piece if current == "PARTY — " else f"{current} | {piece}"
        if current != "PARTY — " and len(candidate) > max_chars:
            lines.append(current)
            current = f"PARTY — {piece}"
        elif current == "PARTY — ":
            current += piece
        else:
            current = candidate
    if current != "PARTY — ":
        lines.append(current)
    return lines


def party_condition_text(roster: Iterable[dict[str, Any]]) -> str:
    rows = list(roster)
    total = len(rows)
    standing = [row for row in rows if int(row.get("hp", 0)) > 0]
    critical = [
        str(row.get("name") or "Hero")
        for row in standing
        if percent(int(row.get("hp", 0)), max(1, int(row.get("max_hp", 1)))) <= 30
    ]
    ko = total - len(standing)
    text = f"Party {len(standing)}/{total} standing"
    if ko:
        text += f" · {ko} KO"
    if critical:
        shown = ", ".join(critical[:2])
        extra = f" +{len(critical) - 2}" if len(critical) > 2 else ""
        text += f" · Critical: {shown}{extra}"
    return text


_EVENT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(.+?) attacks for (\d+)(?: \[(.+?)\])?\.$"), "player_attack"),
    (re.compile(r"^(.+?) attacks but misses while Blinded\.$"), "player_miss"),
    (re.compile(r"^(.+?) Defends and recovers (.+?)\.$"), "defend"),
    (re.compile(r"^(.+?) suffers (\d+) Poison damage\.$"), "poison"),
    (re.compile(r"^(.+?) regenerates (\d+) HP\.$"), "regen"),
    (re.compile(r"^(.+?) attacks (.+?) for (\d+)\.$"), "enemy_attack"),
    (re.compile(r"^(.+?) evades (.+?)'s attack\.$"), "evade"),
    (re.compile(r"^(.+?) is stunned and loses its turn\.$"), "stun"),
)


def compact_event(text: str) -> str:
    """Compress common resolver prose while preserving names, values and effects."""
    raw = " ".join(str(text).split()).strip()
    for pattern, kind in _EVENT_PATTERNS:
        match = pattern.match(raw)
        if not match:
            continue
        groups = match.groups()
        if kind == "player_attack":
            name, damage, flourish = groups
            suffix = f" [{flourish}]" if flourish else ""
            return f"{name} Attack -{damage}{suffix}"
        if kind == "player_miss":
            return f"{groups[0]} Attack MISS (Blind)"
        if kind == "defend":
            detail = str(groups[1]).replace(" and ", "/")
            detail = re.sub(r"(\d+)\s+(AP|MP)", r"\1\2", detail)
            return f"{groups[0]} Defend +{detail}"
        if kind == "poison":
            return f"{groups[0]} Poison -{groups[1]}HP"
        if kind == "regen":
            return f"{groups[0]} Regen +{groups[1]}HP"
        if kind == "enemy_attack":
            return f"{groups[0]} → {groups[1]} -{groups[2]}HP"
        if kind == "evade":
            return f"{groups[0]} evades {groups[1]}"
        if kind == "stun":
            return f"{groups[0]} Stunned"

    ability = re.match(r"^(.+?) uses (.+?) — (.+)\.$", raw)
    if ability:
        actor, name, detail = ability.groups()
        return f"{actor} {name}: {detail}"

    item = re.match(r"^(.+?) uses (.+?) and (.+)\.$", raw)
    if item:
        actor, name, detail = item.groups()
        return f"{actor} {name}: {detail}"

    # Unknown future resolver prose stays readable rather than disappearing.
    return raw.rstrip(".")


def round_summary(
    events: Iterable[str],
    *,
    max_events: int = 6,
    max_chars: int = ROUND_SUMMARY_TARGET,
) -> str:
    """Return one bounded recap and explicitly report omitted events."""
    raw = [compact_event(event) for event in events if str(event).strip()]
    if not raw:
        return "No resolved actions."

    selected: list[str] = []
    used = 0
    for event in raw:
        remaining_after = len(raw) - (used + 1)
        suffix = f" | +{remaining_after} more" if remaining_after > 0 else ""
        candidate = " | ".join([*selected, event]) + suffix
        if selected and (len(candidate) > max_chars or len(selected) >= max_events):
            break
        selected.append(event)
        used += 1
        if len(selected) >= max_events:
            break

    omitted = len(raw) - len(selected)
    body = " | ".join(selected)
    if omitted:
        marker = f" | +{omitted} more"
        if len(body) + len(marker) <= max_chars:
            body += marker
        elif len(body) > max_chars - len(marker):
            body = body[: max(1, max_chars - len(marker) - 1)].rstrip(" |") + marker
    return body[:max_chars]

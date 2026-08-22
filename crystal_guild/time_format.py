from __future__ import annotations


def format_duration(seconds: float | int | None) -> str:
    """Format a countdown using Crystal Guild's canonical w/d/h/m/s ladder.

    Only leading zero units are omitted; once the highest non-zero unit is
    reached, every lower unit through seconds is retained. This keeps timer
    components bounded (minutes/seconds never exceed 59) and makes long
    cooldowns scan consistently.
    """
    try:
        total = max(0, int(float(seconds or 0)))
    except (TypeError, ValueError, OverflowError):
        total = 0

    weeks, rem = divmod(total, 7 * 24 * 60 * 60)
    days, rem = divmod(rem, 24 * 60 * 60)
    hours, rem = divmod(rem, 60 * 60)
    minutes, secs = divmod(rem, 60)

    units = (("w", weeks), ("d", days), ("h", hours), ("m", minutes), ("s", secs))
    first = next((index for index, (_, value) in enumerate(units) if value), len(units) - 1)
    return " ".join(f"{value}{suffix}" for suffix, value in units[first:])

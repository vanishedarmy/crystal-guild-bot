from __future__ import annotations

from typing import Any

WELCOME_POINTS = 500
DAILY_ALLOWANCE_POINTS = 50
CACTPOT_COST = 10
CACTPOT_COOLDOWN_SECONDS = 24 * 60 * 60
SLOTS_COST = 15
SLOTS_COOLDOWN_SECONDS = 5

CACTPOT_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Familiar Mini-Cactpot-style sum table, denominated only in Crystal Guild
# Saucer Points. The currency cannot be purchased for Gil or real money.
CACTPOT_PAYOUTS = {
    6: 10000, 7: 36, 8: 720, 9: 360, 10: 80, 11: 252,
    12: 108, 13: 72, 14: 54, 15: 180, 16: 72, 17: 180,
    18: 119, 19: 36, 20: 306, 21: 1080, 22: 144, 23: 1800, 24: 3600,
}

SLOT_SYMBOLS = (
    ("crystal", "Crystal", 1),
    ("moogle", "Moogle", 2),
    ("chocobo", "Chocobo", 3),
    ("cactuar", "Cactuar", 4),
    ("bomb", "Bomb", 5),
    ("potion", "Potion", 7),
)
SLOT_TRIPLE_PAYOUTS = {
    "crystal": 800,
    "moogle": 400,
    "chocobo": 180,
    "cactuar": 100,
    "bomb": 60,
    "potion": 40,
}
SLOT_PAIR_PAYOUT = 20


# Alpha 1 Prize Counter is intentionally cosmetic-only. Rewards unlock
# existing title functionality and never grant combat power, Gil, items,
# or progression shortcuts.
PRIZES = (
    {
        "id": "saucer_regular",
        "title_id": "saucer_regular",
        "name": "Saucer Regular",
        "cost": 400,
        "description": "A simple Gold Saucer title for adventurers who keep coming back.",
    },
    {
        "id": "cactpot_connoisseur",
        "title_id": "cactpot_connoisseur",
        "name": "Cactpot Connoisseur",
        "cost": 1200,
        "description": "A cosmetic title for the Guild's dedicated scratch-card optimists.",
    },
    {
        "id": "jackpot_chaser",
        "title_id": "jackpot_chaser",
        "name": "Jackpot Chaser",
        "cost": 2500,
        "description": "A prestige title for adventurers who have spent far too long watching reels spin.",
    },
)
PRIZES_BY_ID = {str(row["id"]): row for row in PRIZES}


def slot_labels(reels: list[str]) -> list[str]:
    labels = {row[0]: row[1] for row in SLOT_SYMBOLS}
    return [labels.get(value, str(value).title()) for value in reels]


def slot_payout(reels: list[str]) -> tuple[int, str]:
    if len(reels) != 3:
        return 0, "miss"
    if reels[0] == reels[1] == reels[2]:
        return int(SLOT_TRIPLE_PAYOUTS.get(reels[0], 0)), "triple"
    if reels[0] == reels[1] or reels[0] == reels[2] or reels[1] == reels[2]:
        return SLOT_PAIR_PAYOUT, "pair"
    return 0, "miss"


def masked_grid(grid: list[int], revealed: list[int], *, show_all: bool = False) -> list[int | None]:
    visible = set(int(value) for value in revealed)
    return [int(value) if show_all or index in visible else None for index, value in enumerate(grid)]


def cactpot_line_payload(line_index: int) -> dict[str, Any]:
    cells = CACTPOT_LINES[int(line_index)]
    return {"index": int(line_index), "cells": list(cells)}

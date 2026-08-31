from __future__ import annotations

from typing import Any

WELCOME_MGP = 500
DAILY_ALLOWANCE_MGP = 50
# Compatibility aliases for pre-Alpha-3 callers/tests. New code should use MGP names.
WELCOME_POINTS = WELCOME_MGP
DAILY_ALLOWANCE_POINTS = DAILY_ALLOWANCE_MGP
CACTPOT_COST = 10
CACTPOT_COOLDOWN_SECONDS = 24 * 60 * 60
SLOTS_COST = 15
SLOTS_COOLDOWN_SECONDS = 5
SLOTS_THEORETICAL_RETURN_PCT = 87.5

CACTPOT_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Familiar Mini-Cactpot-style sum table, denominated only in Crystal Guild
# MGP. The currency cannot be purchased for Gil or real money.
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


# Alpha 2 — Monster Toss. A game is five authoritative throws. Players choose
# a target and throw style each turn; higher-scoring targets trade away hit
# chance. Three games are available per UTC day, and an active game persists
# across refresh/reconnect/restart.
MONSTER_TOSS_COST = 20
MONSTER_TOSS_THROWS = 5
MONSTER_TOSS_DAILY_GAMES = 3
MONSTER_TOSS_TARGETS = (
    {"id": "small_pot", "name": "Small Pot", "points": 25, "accuracy": 0.90, "description": "Easy target with a modest score."},
    {"id": "medium_pot", "name": "Medium Pot", "points": 55, "accuracy": 0.72, "description": "Balanced target with a useful score bump."},
    {"id": "large_pot", "name": "Large Pot", "points": 100, "accuracy": 0.52, "description": "Difficult target with a strong score reward."},
    {"id": "golden_cactuar", "name": "Golden Cactuar", "points": 250, "accuracy": 0.28, "description": "Jackpot target: difficult, volatile, and worth a huge score."},
)
MONSTER_TOSS_STYLES = (
    {"id": "safe", "name": "Safe Throw", "accuracy_mod": 0.12, "score_mult": 0.75, "description": "More accurate, but scores less on a hit."},
    {"id": "normal", "name": "Normal Throw", "accuracy_mod": 0.0, "score_mult": 1.0, "description": "Balanced accuracy and score."},
    {"id": "power", "name": "Power Throw", "accuracy_mod": -0.15, "score_mult": 1.5, "description": "Harder to land, but scores much more."},
)
MONSTER_TOSS_PAYOUTS = (
    (900, 70, "jackpot"),
    (600, 40, "gold"),
    (400, 22, "silver"),
    (250, 12, "bronze"),
    (100, 5, "participation"),
    (0, 0, "miss"),
)
MONSTER_TOSS_TARGETS_BY_ID = {row["id"]: row for row in MONSTER_TOSS_TARGETS}
MONSTER_TOSS_STYLES_BY_ID = {row["id"]: row for row in MONSTER_TOSS_STYLES}

def monster_toss_throw_profile(target_id: str, style_id: str) -> tuple[float, int]:
    target = MONSTER_TOSS_TARGETS_BY_ID[str(target_id)]
    style = MONSTER_TOSS_STYLES_BY_ID[str(style_id)]
    accuracy = max(0.05, min(0.95, float(target["accuracy"]) + float(style["accuracy_mod"])))
    score = max(1, int(round(int(target["points"]) * float(style["score_mult"]))))
    return accuracy, score

def monster_toss_payout(score: int) -> tuple[int, str]:
    value = max(0, int(score))
    for minimum, payout, tier in MONSTER_TOSS_PAYOUTS:
        if value >= int(minimum):
            return int(payout), str(tier)
    return 0, "miss"


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
    {
        "id": "toss_tactician",
        "title_id": "toss_tactician",
        "name": "Toss Tactician",
        "cost": 1800,
        "description": "For players who know when to play safe and when to aim at the Golden Cactuar.",
    },
    {
        "id": "pot_shot_pro",
        "title_id": "pot_shot_pro",
        "name": "Pot Shot Pro",
        "cost": 3200,
        "description": "A prestige Monster Toss title for suspiciously accurate carnival heroes.",
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

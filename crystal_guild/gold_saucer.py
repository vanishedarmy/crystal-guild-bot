from __future__ import annotations

from typing import Any

WELCOME_MGP = 500
DAILY_ALLOWANCE_MGP = 125
DAILY_REWARD_MGP = 50
# Compatibility aliases for pre-Alpha-3 callers/tests. New code should use MGP names.
WELCOME_POINTS = WELCOME_MGP
DAILY_ALLOWANCE_POINTS = DAILY_ALLOWANCE_MGP
CACTPOT_COST = 10
CACTPOT_COOLDOWN_SECONDS = 24 * 60 * 60
SLOTS_COST = 15
SLOTS_COOLDOWN_SECONDS = 5
SLOTS_THEORETICAL_RETURN_PCT = 97.1

CACTPOT_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Familiar Mini-Cactpot-style sum table, denominated only in Crystal Guild
# MGP. The currency cannot be purchased for Gil or real money.
# RC2 balance pass: Crystal Guild uses a much smaller MGP prize economy than
# the source inspiration for this table. These payouts preserve the familiar
# high/low sum shape while scaling the daily ticket to Crystal Guild's broader
# Prize Counter economy. Alpha 2 lifts the 6-sum headline jackpot to 1,250 MGP
# while keeping the 10 MGP ticket and the rest of the familiar table shape.
CACTPOT_PAYOUTS = {
    6: 1250, 7: 5, 8: 75, 9: 40, 10: 10, 11: 25,
    12: 10, 13: 5, 14: 5, 15: 20, 16: 5, 17: 20,
    18: 10, 19: 5, 20: 30, 21: 110, 22: 15, 23: 180, 24: 360,
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
SLOT_PAIR_PAYOUT = 23


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
    (900, 90, "jackpot"),
    (600, 60, "gold"),
    (400, 35, "silver"),
    (250, 18, "bronze"),
    (100, 8, "participation"),
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


# Alpha 4 — Chocobo Racing. Races resolve authoritatively in one Portal action
# and use the player's existing registered Chocobo. Level provides a modest
# performance curve, while each course favors one or more existing traits.
# MGP remains separate from Gil and all race rewards stay inside the Saucer.
CHOCOBO_RACING_DAILY_RACES = 3
CHOCOBO_RACING_COURSES = (
    {
        "id": "manderville_sprint",
        "name": "Manderville Sprint",
        "min_level": 1,
        "cost": 25,
        "field_rating": 56.0,
        "field_variance": 7.0,
        "favored_traits": ("steady_strider", "forager"),
        "description": "A welcoming short course with a tight final turn.",
        "payouts": {1: 120, 2: 70, 3: 35},
    },
    {
        "id": "crystal_circuit",
        "name": "Crystal Circuit",
        "min_level": 5,
        "cost": 35,
        "field_rating": 60.5,
        "field_variance": 7.5,
        "favored_traits": ("keen_eye", "fleet_feet"),
        "description": "A faster technical circuit where clean lines matter.",
        "payouts": {1: 190, 2: 105, 3: 50},
    },
    {
        "id": "golden_gauntlet",
        "name": "Golden Gauntlet",
        "min_level": 10,
        "cost": 50,
        "field_rating": 66.0,
        "field_variance": 8.0,
        "favored_traits": ("lucky_plume",),
        "description": "The headline race: a demanding field with the richest podium purse.",
        "payouts": {1: 300, 2: 160, 3: 75},
    },
)
CHOCOBO_RACING_STRATEGIES = (
    {"id": "steady", "name": "Steady Pace", "performance_mod": 1.0, "variance": 5.0, "description": "Lower variance for a dependable run."},
    {"id": "balanced", "name": "Balanced", "performance_mod": 0.0, "variance": 8.0, "description": "A neutral pace with normal risk and upside."},
    {"id": "sprint", "name": "Final Sprint", "performance_mod": -0.5, "variance": 11.0, "description": "Higher variance creates a bigger ceiling and a bigger chance to fade late."},
)
CHOCOBO_RACING_COURSES_BY_ID = {row["id"]: row for row in CHOCOBO_RACING_COURSES}
CHOCOBO_RACING_STRATEGIES_BY_ID = {row["id"]: row for row in CHOCOBO_RACING_STRATEGIES}


def chocobo_race_result(level: int, traits: set[str] | list[str] | tuple[str, ...], course_id: str, strategy_id: str, rng: Any) -> dict[str, Any]:
    course = CHOCOBO_RACING_COURSES_BY_ID[str(course_id)]
    strategy = CHOCOBO_RACING_STRATEGIES_BY_ID[str(strategy_id)]
    level = max(1, min(20, int(level)))
    trait_set = {str(value) for value in traits}
    trait_bonus = 1.5 if trait_set.intersection(course["favored_traits"]) else 0.0
    level_bonus = min(3.0, max(0, level - int(course["min_level"])) * 0.2)
    player_mean = float(course["field_rating"]) + level_bonus + float(strategy["performance_mod"]) + trait_bonus
    player_score = float(rng.gauss(player_mean, float(strategy["variance"])))
    opponents = [
        float(rng.gauss(float(course["field_rating"]), float(course["field_variance"])))
        for _ in range(5)
    ]
    placement = 1 + sum(1 for score in opponents if score > player_score)
    payout = int(course["payouts"].get(placement, 0))
    return {
        "placement": int(placement),
        "field_size": 6,
        "payout": payout,
        "performance": round(player_score, 1),
        "trait_bonus": round(trait_bonus, 1),
        "course_id": str(course["id"]),
        "course_name": str(course["name"]),
        "strategy_id": str(strategy["id"]),
        "strategy_name": str(strategy["name"]),
    }


# Alpha 5 — Triple Triad. The first playable ruleset intentionally uses the
# classic four-side comparison game without Same, Plus, elemental modifiers,
# or regional rules. Matches are persistent and authoritative; a player move
# and the responding NPC move are committed together so refresh/retry cannot
# duplicate MGP or board actions.
TRIPLE_TRIAD_DAILY_MATCHES = 5
TRIPLE_TRIAD_STARTER_DECK = ("chocobo", "moogle", "cactuar", "bomb", "flan")
TRIPLE_TRIAD_CARDS = (
    {"id": "chocobo", "name": "Chocobo", "rarity": 1, "top": 3, "right": 4, "bottom": 2, "left": 1},
    {"id": "moogle", "name": "Moogle", "rarity": 1, "top": 2, "right": 3, "bottom": 4, "left": 3},
    {"id": "cactuar", "name": "Cactuar", "rarity": 1, "top": 5, "right": 2, "bottom": 1, "left": 5},
    {"id": "bomb", "name": "Bomb", "rarity": 1, "top": 4, "right": 2, "bottom": 6, "left": 2},
    {"id": "flan", "name": "Flan", "rarity": 1, "top": 1, "right": 5, "bottom": 4, "left": 3},
    {"id": "tonberry", "name": "Tonberry", "rarity": 2, "top": 6, "right": 2, "bottom": 5, "left": 3},
    {"id": "coeurl", "name": "Coeurl", "rarity": 2, "top": 4, "right": 6, "bottom": 3, "left": 5},
    {"id": "ahriman", "name": "Ahriman", "rarity": 2, "top": 5, "right": 4, "bottom": 6, "left": 3},
    {"id": "malboro", "name": "Malboro", "rarity": 3, "top": 6, "right": 5, "bottom": 5, "left": 4},
    {"id": "ifrit", "name": "Ifrit", "rarity": 3, "top": 7, "right": 5, "bottom": 6, "left": 6},
    {"id": "shiva", "name": "Shiva", "rarity": 3, "top": 6, "right": 7, "bottom": 5, "left": 6},
    {"id": "ramuh", "name": "Ramuh", "rarity": 4, "top": 7, "right": 6, "bottom": 7, "left": 4},
    {"id": "leviathan", "name": "Leviathan", "rarity": 4, "top": 8, "right": 7, "bottom": 5, "left": 6},
    {"id": "bahamut", "name": "Bahamut", "rarity": 5, "top": 8, "right": 8, "bottom": 7, "left": 7},
    {"id": "odin", "name": "Odin", "rarity": 5, "top": 9, "right": 7, "bottom": 8, "left": 6},
)
TRIPLE_TRIAD_CARDS_BY_ID = {row["id"]: row for row in TRIPLE_TRIAD_CARDS}
TRIPLE_TRIAD_OPPONENTS = (
    {
        "id": "saucer_attendant",
        "name": "Saucer Attendant",
        "difficulty": "Novice",
        "unlock_wins": 0,
        "cost": 20,
        "win_payout": 100,
        "draw_payout": 20,
        "deck": ("chocobo", "moogle", "cactuar", "tonberry", "coeurl"),
        "rewards": ("tonberry", "coeurl", "ahriman"),
        "description": "A friendly floor attendant who teaches clean corners and basic captures.",
    },
    {
        "id": "card_shark",
        "name": "Card Shark",
        "difficulty": "Skilled",
        "unlock_wins": 3,
        "cost": 30,
        "win_payout": 150,
        "draw_payout": 30,
        "deck": ("tonberry", "coeurl", "ahriman", "malboro", "ifrit"),
        "rewards": ("malboro", "ifrit", "shiva"),
        "description": "A sharper opponent who looks for immediate captures and stronger edges.",
    },
    {
        "id": "crystal_master",
        "name": "Crystal Master",
        "difficulty": "Master",
        "unlock_wins": 8,
        "cost": 45,
        "win_payout": 240,
        "draw_payout": 45,
        "deck": ("malboro", "ifrit", "shiva", "ramuh", "leviathan"),
        "rewards": ("ramuh", "leviathan", "bahamut", "odin"),
        "description": "The high-table challenge: powerful cards, deliberate placement, and premium rewards.",
    },
)
TRIPLE_TRIAD_OPPONENTS_BY_ID = {row["id"]: row for row in TRIPLE_TRIAD_OPPONENTS}


def triple_triad_card_payload(card_id: str) -> dict[str, Any]:
    row = TRIPLE_TRIAD_CARDS_BY_ID[str(card_id)]
    return {
        "id": str(row["id"]), "name": str(row["name"]), "rarity": int(row["rarity"]),
        "top": int(row["top"]), "right": int(row["right"]),
        "bottom": int(row["bottom"]), "left": int(row["left"]),
    }


def triple_triad_capture(board: list[dict[str, Any] | None], cell: int) -> list[int]:
    """Apply the basic Triple Triad capture rule for the card at ``cell``."""
    placed = board[int(cell)]
    if not isinstance(placed, dict):
        return []
    card = TRIPLE_TRIAD_CARDS_BY_ID[str(placed["card_id"])]
    owner = str(placed["owner"])
    row, col = divmod(int(cell), 3)
    checks = []
    if row > 0:
        checks.append((cell - 3, "top", "bottom"))
    if col < 2:
        checks.append((cell + 1, "right", "left"))
    if row < 2:
        checks.append((cell + 3, "bottom", "top"))
    if col > 0:
        checks.append((cell - 1, "left", "right"))
    captured: list[int] = []
    for neighbor_index, attack_side, defend_side in checks:
        neighbor = board[int(neighbor_index)]
        if not isinstance(neighbor, dict) or str(neighbor.get("owner")) == owner:
            continue
        other = TRIPLE_TRIAD_CARDS_BY_ID.get(str(neighbor.get("card_id")))
        if other and int(card[attack_side]) > int(other[defend_side]):
            neighbor["owner"] = owner
            captured.append(int(neighbor_index))
    return captured


def triple_triad_place(board: list[dict[str, Any] | None], cell: int, card_id: str, owner: str) -> list[int]:
    if int(cell) < 0 or int(cell) > 8 or board[int(cell)] is not None:
        raise ValueError("Triple Triad cell is unavailable.")
    if str(card_id) not in TRIPLE_TRIAD_CARDS_BY_ID:
        raise ValueError("Unknown Triple Triad card.")
    board[int(cell)] = {"card_id": str(card_id), "owner": str(owner)}
    return triple_triad_capture(board, int(cell))


def triple_triad_score(board: list[dict[str, Any] | None]) -> tuple[int, int]:
    player = sum(1 for row in board if isinstance(row, dict) and row.get("owner") == "player")
    npc = sum(1 for row in board if isinstance(row, dict) and row.get("owner") == "npc")
    return int(player), int(npc)


def triple_triad_npc_move(board: list[dict[str, Any] | None], hand: list[str], difficulty: str = "Novice") -> tuple[str, int]:
    """Choose a deterministic NPC move, making higher tiers more capture-aware."""
    empty = [index for index, row in enumerate(board) if row is None]
    if not empty or not hand:
        raise ValueError("Triple Triad NPC has no legal move.")
    level = str(difficulty or "Novice").lower()
    ranked: list[tuple[float, str, int]] = []
    for card_id in hand:
        card = TRIPLE_TRIAD_CARDS_BY_ID[str(card_id)]
        for cell in empty:
            trial = [dict(row) if isinstance(row, dict) else None for row in board]
            captures = len(triple_triad_place(trial, cell, card_id, "npc"))
            side_sum = sum(int(card[key]) for key in ("top", "right", "bottom", "left"))
            center = 1 if cell == 4 else 0
            corner = 1 if cell in {0, 2, 6, 8} else 0
            if level == "novice":
                value = captures * 20 - side_sum * 0.05 + corner * 0.1
            elif level == "skilled":
                value = captures * 30 + side_sum * 0.15 + center * 0.6 + corner * 0.3
            else:
                value = captures * 40 + side_sum * 0.25 + center * 0.8 + corner * 0.5
            ranked.append((float(value), str(card_id), int(cell)))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    _score, card_id, cell = ranked[0]
    return str(card_id), int(cell)


# Alpha 1 Prize Counter is intentionally cosmetic-only. Rewards unlock
# existing title functionality and never grant combat power, Gil, items,
# or progression shortcuts.
PRIZES = (
    {
        "id": "saucer_regular",
        "title_id": "saucer_regular",
        "name": "Saucer Regular",
        "cost": 500,
        "description": "A simple Gold Saucer title for adventurers who keep coming back.",
    },
    {
        "id": "cactpot_connoisseur",
        "title_id": "cactpot_connoisseur",
        "name": "Cactpot Connoisseur",
        "cost": 1750,
        "description": "A cosmetic title for the Guild's dedicated scratch-card optimists.",
    },
    {
        "id": "jackpot_chaser",
        "title_id": "jackpot_chaser",
        "name": "Jackpot Chaser",
        "cost": 3500,
        "description": "A prestige title for adventurers who have spent far too long watching reels spin.",
    },
    {
        "id": "toss_tactician",
        "title_id": "toss_tactician",
        "name": "Toss Tactician",
        "cost": 2500,
        "description": "For players who know when to play safe and when to aim at the Golden Cactuar.",
    },
    {
        "id": "pot_shot_pro",
        "title_id": "pot_shot_pro",
        "name": "Pot Shot Pro",
        "cost": 4500,
        "description": "A prestige Monster Toss title for suspiciously accurate carnival heroes.",
    },
    {
        "id": "feathered_finisher",
        "title_id": "feathered_finisher",
        "name": "Feathered Finisher",
        "cost": 3000,
        "description": "For riders who discovered that every straightaway is an invitation.",
    },
    {
        "id": "circuit_champion",
        "title_id": "circuit_champion",
        "name": "Circuit Champion",
        "cost": 7500,
        "description": "A prestige title for Gold Saucer riders with podium feathers to spare.",
    },
    {
        "id": "triad_tactician",
        "title_id": "triad_tactician",
        "name": "Triad Tactician",
        "cost": 4000,
        "description": "For card players who can see a capture from four sides away.",
    },
    {
        "id": "card_hall_master",
        "title_id": "card_hall_master",
        "name": "Card Hall Master",
        "cost": 9000,
        "description": "A prestige title for adventurers who have conquered the Gold Saucer card hall.",
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

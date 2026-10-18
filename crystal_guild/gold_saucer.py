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
    # Economy Balance Alpha 2: beginner-friendly floor with stronger
    # performance rewards. Daily entry limits keep the faucet bounded.
    (900, 120, "jackpot"),
    (600, 80, "gold"),
    (400, 50, "silver"),
    (250, 30, "bronze"),
    (100, 15, "participation"),
    (75, 10, "near_miss"),
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


# Legacy compatibility reexports; all card-game rules live in triple_triad.py.
from .triple_triad import (
    TRIPLE_TRIAD_DAILY_MATCHES, TRIPLE_TRIAD_STARTER_DECK, TRIPLE_TRIAD_STARTER_COLLECTION,
    TRIPLE_TRIAD_CARDS, TRIPLE_TRIAD_CARDS_BY_ID, TRIPLE_TRIAD_OPPONENTS,
    TRIPLE_TRIAD_OPPONENTS_BY_ID, triple_triad_card_payload, triple_triad_npc_move,
    triple_triad_capture, triple_triad_place, triple_triad_score,
)


def gold_saucer_record_value(conn: Any, player_id: str, metric: str) -> int:
    """Return stable achievement metrics derived from authoritative Saucer state.

    Keeping these metrics here lets the Bot achievement engine and the read-only
    Portal snapshot use the exact same definitions without adding schema columns.
    """
    key = str(metric or "").strip().lower()
    if key in {"lifetime_earned", "lifetime_spent"}:
        row = conn.execute(
            f"SELECT {key} AS value FROM player_gold_saucer WHERE player_id=?",
            (str(player_id),),
        ).fetchone()
        return int(row["value"] or 0) if row else 0
    if key == "games_played":
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM gold_saucer_history "
            "WHERE player_id=? AND game IN ('mini_cactpot','slots','monster_toss','chocobo_racing')",
            (str(player_id),),
        ).fetchone()
        return int(row["n"] or 0) if row else 0
    if key == "unique_games":
        row = conn.execute(
            "SELECT COUNT(DISTINCT game) AS n FROM gold_saucer_history "
            "WHERE player_id=? AND game IN ('mini_cactpot','slots','monster_toss','chocobo_racing')",
            (str(player_id),),
        ).fetchone()
        return int(row["n"] or 0) if row else 0
    if key == "cactpot_jackpots":
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id=? AND game='mini_cactpot' AND payout>=1250",
            (str(player_id),),
        ).fetchone()
        return int(row["n"] or 0) if row else 0
    if key == "slots_jackpots":
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id=? AND game='slots' AND outcome='triple' AND payout>=800",
            (str(player_id),),
        ).fetchone()
        return int(row["n"] or 0) if row else 0
    if key == "monster_toss_gold_games":
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id=? AND game='monster_toss' "
            "AND COALESCE(CAST(json_extract(details_json,'$.score') AS INTEGER),0)>=600",
            (str(player_id),),
        ).fetchone()
        return int(row["n"] or 0) if row else 0
    if key == "chocobo_race_wins":
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM gold_saucer_history WHERE player_id=? AND game='chocobo_racing' "
            "AND COALESCE(CAST(json_extract(details_json,'$.placement') AS INTEGER),99)=1",
            (str(player_id),),
        ).fetchone()
        return int(row["n"] or 0) if row else 0
    return 0


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
        "id": "one_more_spin",
        "title_id": "one_more_spin",
        "name": "One More Spin",
        "cost": 750,
        "description": "A low-cost vanity title for anyone absolutely certain the next spin is the one.",
    },
    {
        "id": "probably_rigged",
        "title_id": "probably_rigged",
        "name": "Probably Rigged",
        "cost": 1000,
        "description": "A sarcastic souvenir for players with healthy skepticism and unhealthy persistence.",
    },
    {
        "id": "bird_is_the_word",
        "title_id": "bird_is_the_word",
        "name": "Bird Is the Word",
        "cost": 1250,
        "description": "A racing-flavored vanity title for dedicated feather enthusiasts.",
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

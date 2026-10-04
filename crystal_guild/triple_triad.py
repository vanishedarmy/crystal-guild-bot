"""Data-driven Triple Triad ladder and bounded, public-board-only tactics."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

CATALOG = json.loads(Path(__file__).with_name("triple_triad_catalog.json").read_text(encoding="utf-8"))
TRIPLE_TRIAD_DAILY_MATCHES = CATALOG["daily_matches"]
TRIPLE_TRIAD_STARTER_DECK = tuple(CATALOG["starter_deck"])
TRIPLE_TRIAD_STARTER_COLLECTION = tuple(CATALOG["starter_collection"])
TRIPLE_TRIAD_CARDS = tuple(CATALOG["cards"])
TRIPLE_TRIAD_CARDS_BY_ID = {c["id"]: c for c in TRIPLE_TRIAD_CARDS}
TRIPLE_TRIAD_OPPONENTS = tuple(CATALOG["opponents"])
TRIPLE_TRIAD_OPPONENTS_BY_ID = {o["id"]: o for o in TRIPLE_TRIAD_OPPONENTS}
TRIPLE_TRIAD_CIRCUITS = tuple(CATALOG["circuits"])
SIDES = ("top", "right", "bottom", "left")


def triple_triad_power(ids: list[str] | tuple[str, ...]) -> int:
    return sum(sum(c[s] + max(0, c[s] - 7) for s in SIDES) for c in (TRIPLE_TRIAD_CARDS_BY_ID[id] for id in ids))


# Fixed decks are bounded here so future catalogue edits cannot accidentally
# put an endgame hand at a beginner table.
POWER_CAPS = {"Novice": 52, "Standard": 75, "Skilled": 95, "Expert": 118, "Master": 150}
def validate_catalog() -> None:
    if len(TRIPLE_TRIAD_CARDS_BY_ID) != len(TRIPLE_TRIAD_CARDS):
        raise ValueError("Duplicate Triple Triad card IDs")
    for c in TRIPLE_TRIAD_CARDS:
        if any(type(c[s]) is not int or not 1 <= c[s] <= 10 for s in SIDES):
            raise ValueError(f"Invalid side values on {c['id']}")
    for o in TRIPLE_TRIAD_OPPONENTS:
        if len(o["deck"]) != 5 or len(set(o["deck"])) != 5:
            raise ValueError(f"Invalid opponent deck: {o['id']}")
        if triple_triad_power(o["deck"]) > POWER_CAPS[o["difficulty"]]:
            raise ValueError(f"Opponent deck exceeds power cap: {o['id']}")
        if any(c not in TRIPLE_TRIAD_CARDS_BY_ID for c in o["rewards"]):
            raise ValueError(f"Unknown reward card: {o['id']}")
validate_catalog()


def triple_triad_card_payload(card_id: str) -> dict[str, Any]:
    card = dict(TRIPLE_TRIAD_CARDS_BY_ID[card_id])
    card["sources"] = [{"id": o["id"], "name": o["name"], "circuit": o["circuit"]} for o in TRIPLE_TRIAD_OPPONENTS if card_id in o["rewards"]]
    card["starter"] = card_id in TRIPLE_TRIAD_STARTER_COLLECTION
    return card


def triple_triad_progress(history: list[dict[str, Any]], wins: int = 0) -> dict[str, Any]:
    """History is already durable and indexed; no destructive profile migration."""
    victories: dict[str, int] = {}
    quantities: dict[str, int] = {}
    paid = set()
    modern_wins = 0
    for h in history:
        details = h["details"]
        if h["game"] == "triad_collection":
            quantities = dict(details.get("quantities", {}))
            continue
        if h["game"] == "triad_circuit":
            paid.add(details.get("circuit"))
            continue
        if h["outcome"] == "win":
            id = details.get("opponent_id")
            victories[id] = victories.get(id, 0) + 1
            modern_wins += int(details.get("catalog_revision", 0) >= 2)
        reward = details.get("card_reward")
        if reward in TRIPLE_TRIAD_CARDS_BY_ID:
            quantities[reward] = quantities.get(reward, 0) + 1
    legacy_wins = max(0, wins - modern_wins)
    circuits = []
    previous_cleared = True
    for index, circuit in enumerate(TRIPLE_TRIAD_CIRCUITS):
        opponents = [o for o in TRIPLE_TRIAD_OPPONENTS if o["circuit"] == circuit["id"]]
        defeated = sum(victories.get(o["id"], 0) > 0 for o in opponents)
        cleared = defeated == len(opponents)
        grandfathered = (legacy_wins >= 3 and index <= 2) or legacy_wins >= 8
        unlocked = index == 0 or previous_cleared or grandfathered
        circuits.append({**circuit, "defeated": defeated, "total": len(opponents), "cleared": cleared, "unlocked": unlocked, "bonus_paid": circuit["id"] in paid})
        # A later circuit cannot be skipped merely by winning against one NPC.
        previous_cleared = cleared and unlocked
    return {"circuits": circuits, "victories": victories, "quantities": quantities}


def triple_triad_recent_misses(history: list[dict[str, Any]], opponent_id: str) -> int:
    misses = 0
    for h in reversed(history):
        d = h["details"]
        if h["game"] != "triple_triad" or d.get("opponent_id") != opponent_id:
            continue
        if d.get("card_reward"):
            break
        if h["outcome"] == "win":
            misses += 1
    return misses


def triple_triad_npc_move(board, hand, difficulty="Novice", match_seed="") -> tuple[str, int]:
    # Only the visible board and the NPC's own hand are available here.
    from .gold_saucer import triple_triad_place
    empty = [i for i, cell in enumerate(board) if cell is None]
    if not empty or not hand:
        raise ValueError("Triple Triad NPC has no legal move.")
    seed = hashlib.sha256(json.dumps([board, hand, difficulty, match_seed], sort_keys=True).encode()).digest()
    rng = random.Random(int.from_bytes(seed[:8], "big"))
    level = difficulty.lower()
    moves = [(id, cell) for id in hand for cell in empty]
    # Novices often overlook captures. Standard sometimes makes a modest mistake.
    if rng.random() < {"novice": .35, "standard": .30, "skilled": .10, "expert": .05}.get(level, 0):
        return rng.choice(moves)
    ranked = []
    for id, cell in moves:
        trial = [dict(c) if c else None for c in board]
        captures = len(triple_triad_place(trial, cell, id, "npc"))
        card = TRIPLE_TRIAD_CARDS_BY_ID[id]
        row, col = divmod(cell, 3)
        exposed = [s for s, neighbor, legal in (("top",cell-3,row>0),("right",cell+1,col<2),("bottom",cell+3,row<2),("left",cell-1,col>0)) if legal and trial[neighbor] is None]
        protection = sum(card[s] for s in exposed) / max(1, len(exposed))
        value = captures * 8
        if level != "novice":
            value += protection * {"standard": .25, "skilled": .7, "expert": 1., "master": 1.2}.get(level, .25)
        # Expert/Master consider the weakest visible edge of all their cards;
        # no search of the player's hidden hand or exhaustive future turns.
        if level in {"expert", "master"}:
            exposed_values = []
            for i, c in enumerate(trial):
                if not c or c["owner"] != "npc":
                    continue
                r, co = divmod(i, 3)
                for side, n, legal in (("top",i-3,r>0),("right",i+1,co<2),("bottom",i+3,r<2),("left",i-1,co>0)):
                    if legal and trial[n] is None:
                        exposed_values.append(TRIPLE_TRIAD_CARDS_BY_ID[c["card_id"]][side])
            value += min(exposed_values, default=0) * .7
        value += rng.uniform(0, {"novice": 6, "standard": 3, "skilled": .4, "expert": .1, "master": .05}.get(level, 1))
        ranked.append((value, id, cell))
    _, id, cell = max(ranked)
    return id, cell

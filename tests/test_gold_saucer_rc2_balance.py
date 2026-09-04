from __future__ import annotations

import itertools
import math
import random
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine
from crystal_guild.gold_saucer import (
    CACTPOT_COST,
    CACTPOT_PAYOUTS,
    CHOCOBO_RACING_COURSES,
    MONSTER_TOSS_COST,
    MONSTER_TOSS_STYLES,
    MONSTER_TOSS_TARGETS,
    SLOTS_COST,
    SLOT_SYMBOLS,
    TRIPLE_TRIAD_OPPONENTS,
    monster_toss_payout,
    monster_toss_throw_profile,
    slot_payout,
)

ROOT = Path(__file__).resolve().parents[1]


class GoldSaucerRC2BalanceTests(unittest.TestCase):
    def test_cactpot_is_scaled_to_crystal_guild_economy_and_has_net_wdl(self):
        self.assertEqual(CACTPOT_COST, 10)
        self.assertEqual(CACTPOT_PAYOUTS[6], 1250)
        self.assertEqual(CACTPOT_PAYOUTS[24], 360)
        self.assertTrue(any(value < CACTPOT_COST for value in CACTPOT_PAYOUTS.values()))
        self.assertTrue(any(value == CACTPOT_COST for value in CACTPOT_PAYOUTS.values()))
        self.assertTrue(any(value > CACTPOT_COST for value in CACTPOT_PAYOUTS.values()))

        # A random three-number line is now about 36.19 MGP instead of the
        # prerelease table's ~360 MGP, keeping the daily jackpot attractive
        # without making every other attraction economically irrelevant.
        totals = Counter(sum(values) for values in itertools.combinations(range(1, 10), 3))
        samples = sum(totals.values())
        expected = sum(totals[total] * CACTPOT_PAYOUTS[total] for total in totals) / samples
        self.assertGreater(expected, 39.0)
        self.assertLess(expected, 39.3)

    def test_slots_return_and_outcome_mix_remain_bounded(self):
        weights = {symbol: int(weight) for symbol, _label, weight in SLOT_SYMBOLS}
        total_weight = sum(weights.values())
        payout_ev = 0.0
        net_wins = 0.0
        net_losses = 0.0
        for a, b, c in itertools.product(weights, repeat=3):
            probability = (weights[a] / total_weight) * (weights[b] / total_weight) * (weights[c] / total_weight)
            payout, _outcome = slot_payout([a, b, c])
            payout_ev += probability * payout
            if payout > SLOTS_COST:
                net_wins += probability
            elif payout < SLOTS_COST:
                net_losses += probability
        self.assertAlmostEqual(payout_ev / SLOTS_COST, 0.9714500376, places=6)
        self.assertGreater(net_wins, 0.53)
        self.assertGreater(net_losses, 0.46)

    def test_monster_toss_best_fixed_profile_is_rewarding_but_bounded(self):
        best = 0.0
        for target in MONSTER_TOSS_TARGETS:
            for style in MONSTER_TOSS_STYLES:
                probability, hit_score = monster_toss_throw_profile(target["id"], style["id"])
                ev = 0.0
                for hits in range(6):
                    chance = math.comb(5, hits) * (probability ** hits) * ((1.0 - probability) ** (5 - hits))
                    payout, _tier = monster_toss_payout(hits * hit_score)
                    ev += chance * payout
                best = max(best, ev)
        self.assertGreater(best / MONSTER_TOSS_COST, 1.28)
        self.assertLess(best / MONSTER_TOSS_COST, 1.31)

    def test_racing_and_triad_preserve_clear_win_draw_loss_stakes(self):
        for course in CHOCOBO_RACING_COURSES:
            cost = int(course["cost"])
            self.assertGreater(int(course["payouts"][1]), cost)
            self.assertGreater(int(course["payouts"][2]), cost)
            self.assertGreater(int(course["payouts"][3]), cost)
        for opponent in TRIPLE_TRIAD_OPPONENTS:
            cost = int(opponent["cost"])
            self.assertGreater(int(opponent["win_payout"]), cost)
            self.assertEqual(int(opponent["draw_payout"]), cost)

    def test_cactpot_history_tracks_net_outcome_and_net_win_count(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            db = Database(Path(tmp.name) / "guild.db")
            game = CrystalGuildEngine(db, GameData(ROOT / "data"), overlay_state_path=str(Path(tmp.name) / "overlay.json"), rng=random.Random(160602))
            self.assertTrue(game.recruit("100", "van", "Van").ok)
            self.assertTrue(game.choose_job("100", "warrior").ok)
            self.assertTrue(game.portal_cactpot_start("100", "rc2-cactpot-start").ok)
            ticket = db.one("SELECT grid_json,revealed_json FROM gold_saucer_cactpot WHERE player_id='100'")
            import json
            grid = json.loads(ticket["grid_json"])
            revealed = set(json.loads(ticket["revealed_json"]))
            for cell in range(9):
                if cell not in revealed:
                    self.assertTrue(game.portal_cactpot_reveal("100", cell, f"rc2-reveal-{cell}").ok)
                    revealed.add(cell)
                    if len(revealed) == 4:
                        break
            # Pick any line; verify the stored semantic matches wager vs payout.
            result = game.portal_cactpot_line("100", 0, "rc2-line")
            self.assertTrue(result.ok)
            payout = int(result.data["cactpot_payout"])
            row = db.one("SELECT wager,payout,details_json FROM gold_saucer_history WHERE player_id='100' AND game='mini_cactpot'")
            details = json.loads(row["details_json"])
            expected = "win" if payout > int(row["wager"]) else "draw" if payout == int(row["wager"]) else "loss"
            self.assertEqual(details["net_outcome"], expected)
            self.assertEqual(int(details["net_mgp"]), payout - int(row["wager"]))
            state = game.portal_gold_saucer_state("100").data["gold_saucer_state"]
            self.assertEqual(state["records"]["cactpot_net_wins"], 1 if expected == "win" else 0)
            self.assertEqual(state["records"]["cactpot_draws"], 1 if expected == "draw" else 0)
            self.assertEqual(state["records"]["cactpot_losses"], 1 if expected == "loss" else 0)
            db.close()
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()

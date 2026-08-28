from __future__ import annotations

import argparse
import json
import random
import statistics
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.engine import CrystalGuildEngine

ROOT = Path(__file__).resolve().parents[1]
PLAYER_ID = "sim-player"

BANDS = [
    ("Starter", 8, "emerald_wilds"),
    ("Early", 16, "ashen_highlands"),
    ("Mid", 24, "mistfen_marshes"),
    ("Late", 34, "frostveil_reach"),
    ("Endgame", 45, "astral_scar"),
]
ROUTES = ("safe", "unknown", "deep")
DEPTHS = ("scout", "journey", "deep")


def _item_score(item: dict[str, Any], slot: str) -> float:
    b = item.get("bonuses") or {}
    if slot == "weapon":
        return 4 * float(b.get("attack", 0)) + 2.5 * float(b.get("str", 0)) + float(b.get("dex", 0)) + 0.3 * float(b.get("hp", 0))
    if slot == "armor":
        return 3 * float(b.get("vit", 0)) + 1.5 * float(b.get("spr", 0)) + 0.16 * float(b.get("hp", 0)) + 0.5 * float(b.get("dex", 0))
    return 2 * float(b.get("vit", 0)) + 2 * float(b.get("str", 0)) + float(b.get("spr", 0)) + float(b.get("dex", 0)) + float(b.get("lck", 0)) + 0.10 * float(b.get("hp", 0)) + 2 * float(b.get("attack", 0))


def best_shop_gear(data: GameData, level: int, job_id: str = "warrior") -> dict[str, str | None]:
    result: dict[str, str | None] = {"weapon": None, "armor": None, "accessory": None}
    for slot in result:
        candidates = []
        for item in data.items.values():
            if item.get("type") != slot:
                continue
            if int(item.get("min_level", 1) or 1) > level:
                continue
            if int(item.get("shop_level", item.get("min_level", 1)) or 1) > level:
                continue
            if not bool(item.get("shop", False)) and slot != "accessory":
                continue
            allowed = item.get("allowed_jobs") or []
            if allowed and job_id not in allowed:
                continue
            candidates.append(item)
        if candidates:
            result[slot] = max(candidates, key=lambda item: (_item_score(item, slot), int(item.get("min_level", 1) or 1), item["id"]))["id"]
    return result


@dataclass
class RunResult:
    outcome: str
    stages: int
    combats: int
    hazards: int
    rare_events: int
    camps: int
    travel_seconds: int
    xp: int
    jp: int
    gil: int
    seals: int
    lost_gil: int
    hp_ratio: float


class ExpeditionSimulator:
    def __init__(self, seed: int):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "balance.db")
        self.data = GameData(ROOT / "data")
        self.game = CrystalGuildEngine(
            self.db,
            self.data,
            overlay_state_path=str(Path(self.tmp.name) / "overlay.json"),
            rng=random.Random(seed),
        )
        self.game.recruit(PLAYER_ID, "simulation", "Simulation")
        self.game.choose_job(PLAYER_ID, "warrior")
        self.db.execute("UPDATE fellowship_state SET expedition_board_complete=1 WHERE singleton_id=1")
        self.db.execute(
            "INSERT INTO player_chocobos(player_id,name,registered_at,xp) VALUES (?,?,CURRENT_TIMESTAMP,0) "
            "ON CONFLICT(player_id) DO UPDATE SET name=excluded.name,registered_at=CURRENT_TIMESTAMP,xp=0",
            (PLAYER_ID, "Compass"),
        )

    def close(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def prepare(self, level: int, region_id: str, contract: str | None = None) -> None:
        self.game._expedition_delete(PLAYER_ID)
        self.db.execute("DELETE FROM portal_adventure_results WHERE player_id=?", (PLAYER_ID,))
        self.db.execute("DELETE FROM player_chocobo_traits WHERE player_id=?", (PLAYER_ID,))
        self.db.execute("UPDATE player_chocobos SET xp=0 WHERE player_id=?", (PLAYER_ID,))
        self.db.execute(
            "UPDATE players SET level=?,xp=0,current_job='warrior',stance='balanced',current_hp=1,current_mp=NULL,current_ap=NULL,camp_until=0 WHERE twitch_id=?",
            (int(level), PLAYER_ID),
        )
        self.db.execute("UPDATE player_jobs SET level=?,jp=0 WHERE player_id=? AND job_id='warrior'", (min(50, max(1, int(level))), PLAYER_ID))
        gear = best_shop_gear(self.data, int(level), "warrior")
        self.db.execute(
            "UPDATE equipment SET weapon_id=?,armor_id=?,accessory_id=? WHERE player_id=?",
            (gear["weapon"], gear["armor"], gear["accessory"], PLAYER_ID),
        )
        p = self.game._player(PLAYER_ID)
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id=?", (self.game._max_hp(p), PLAYER_ID))
        self.game._restore_current_job_resources(PLAYER_ID)
        if contract == "legendary":
            progress, clears = 100, 1
        elif contract == "boss":
            progress, clears = 75, 0
        else:
            progress, clears = 50, 0
        self.db.execute(
            "INSERT INTO player_region_exploration(player_id,region_id,progress,boss_clears) VALUES (?,?,?,?) "
            "ON CONFLICT(player_id,region_id) DO UPDATE SET progress=excluded.progress,boss_clears=excluded.boss_clears,stages_cleared=0,completed_runs=0",
            (PLAYER_ID, region_id, progress, clears),
        )

    def run(self, level: int, region_id: str, depth: str, route: str, contract: str | None = None) -> RunResult:
        self.prepare(level, region_id, contract)
        depth_id = contract or depth
        started = self.game.expedition_start(PLAYER_ID, region_id, depth_id)
        if not started.ok:
            raise RuntimeError("start failed: " + " ".join(started.messages))
        combats = hazards = rare_events = camps = travel_seconds = 0
        guard = 0
        final = None
        while guard < 200:
            guard += 1
            state = self.game._expedition_load(PLAYER_ID)
            if not state:
                break
            status = str(state.get("status") or "")
            if status == "travel":
                travel_seconds += max(0, int(state.get("travel_ready_at", 0)) - int(state.get("travel_started_at", state.get("updated_at", 0)) or 0))
                state["travel_ready_at"] = 0
                self.game._expedition_save(PLAYER_ID, state)
                resolved = self.game.expedition_resolve_stage(PLAYER_ID)
                if not resolved.ok:
                    raise RuntimeError("resolve failed: " + " ".join(resolved.messages))
                after = self.game._expedition_load(PLAYER_ID)
                if not after:
                    final = resolved
                    break
                if str(after.get("status")) == "combat":
                    combats += 1
                else:
                    event = after.get("event") or {}
                    etype = str(event.get("type") or "")
                    hazards += int(etype == "hazard")
                    rare_events += int(etype == "rare")
                continue
            if status == "combat":
                acted = self.game.expedition_combat_action(PLAYER_ID, "attack")
                if not acted.ok:
                    raise RuntimeError("combat failed: " + " ".join(acted.messages))
                if acted.data.get("expedition_finished"):
                    final = acted
                    break
                continue
            if status == "choice":
                stage = int(state.get("stage", 1))
                base = int(state.get("base_stages", 1))
                if stage >= base:
                    final = self.game.expedition_return(PLAYER_ID)
                    break
                p = self.game._player(PLAYER_ID)
                max_hp = max(1, self.game._max_hp(p))
                if int(p["current_hp"] or 0) / max_hp <= 0.42 and not bool(state.get("camp_used_stage")):
                    camped = self.game.expedition_camp(PLAYER_ID)
                    if camped.ok:
                        camps += 1
                continued = self.game.expedition_continue(PLAYER_ID, route)
                if not continued.ok:
                    raise RuntimeError("continue failed: " + " ".join(continued.messages))
                continue
            raise RuntimeError(f"unexpected status {status!r}")
        if final is None:
            raise RuntimeError("simulation guard exhausted")
        summary = final.data.get("expedition_result") or {}
        rewards = summary.get("rewards") or {}
        lost = summary.get("lost") or {}
        player = summary.get("player") or {}
        max_hp = max(1, int(player.get("max_hp", 1) or 1))
        return RunResult(
            outcome=str(summary.get("outcome") or ("defeat" if not final.data.get("won", True) else "unknown")),
            stages=int(summary.get("stages", 0) or 0),
            combats=combats,
            hazards=hazards,
            rare_events=rare_events,
            camps=camps,
            travel_seconds=travel_seconds,
            xp=int(rewards.get("xp", 0) or 0),
            jp=int(rewards.get("jp", 0) or 0),
            gil=int(rewards.get("gil", 0) or 0),
            seals=int(rewards.get("seals", 0) or 0),
            lost_gil=int(lost.get("gil", 0) or 0),
            hp_ratio=max(0.0, min(1.0, int(player.get("hp", 0) or 0) / max_hp)),
        )


def summarize(rows: list[RunResult]) -> dict[str, Any]:
    n = max(1, len(rows))
    outcomes = Counter(r.outcome for r in rows)
    return {
        "runs": len(rows),
        "completion_rate": round(outcomes.get("complete", 0) / n, 4),
        "defeat_rate": round(outcomes.get("defeat", 0) / n, 4),
        "avg_combats": round(statistics.fmean(r.combats for r in rows), 3),
        "avg_hazards": round(statistics.fmean(r.hazards for r in rows), 3),
        "avg_rare_events": round(statistics.fmean(r.rare_events for r in rows), 3),
        "avg_camps": round(statistics.fmean(r.camps for r in rows), 3),
        "avg_travel_minutes": round(statistics.fmean(r.travel_seconds for r in rows) / 60.0, 2),
        "avg_xp": round(statistics.fmean(r.xp for r in rows), 1),
        "avg_jp": round(statistics.fmean(r.jp for r in rows), 1),
        "avg_gil": round(statistics.fmean(r.gil for r in rows), 1),
        "avg_seals": round(statistics.fmean(r.seals for r in rows), 2),
        "avg_lost_gil": round(statistics.fmean(r.lost_gil for r in rows), 1),
        "avg_finish_hp_pct": round(statistics.fmean(r.hp_ratio for r in rows) * 100.0, 1),
    }


def run_matrix(runs: int, seed: int) -> dict[str, Any]:
    sim = ExpeditionSimulator(seed)
    output: dict[str, Any] = {"seed": seed, "runs_per_scenario": runs, "standard": [], "contracts": []}
    try:
        for band, level, region_id in BANDS:
            for depth in DEPTHS:
                for route in ROUTES:
                    rows = [sim.run(level, region_id, depth, route) for _ in range(runs)]
                    output["standard"].append({"band": band, "level": level, "region": region_id, "depth": depth, "route": route, **summarize(rows)})
        for region_id, region in sim.data.expedition_regions.items():
            boss = sim.data.monsters[str((region.get("boss") or {}).get("monster_id"))]
            level = max(int(region.get("min_level", 1)), int(boss.get("level", 1)))
            for contract in ("boss", "legendary"):
                for route in ROUTES:
                    rows = [sim.run(level, region_id, contract, route, contract=contract) for _ in range(runs)]
                    output["contracts"].append({"band": "Contract", "level": level, "region": region_id, "contract": contract, "route": route, **summarize(rows)})
    finally:
        sim.close()
    output["total_runs"] = sum(row["runs"] for section in ("standard", "contracts") for row in output[section])
    return output


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Crystal Guild v1.2 Beta 1 — Expedition Balance Simulation",
        "",
        f"Fixed seed: `{report['seed']}`  ",
        f"Runs per scenario: **{report['runs_per_scenario']}**  ",
        f"Total simulated Expeditions: **{report['total_runs']}**",
        "",
        "Simulation uses a Warrior at the representative level for each region, level-appropriate shop gear, persistent HP/resources between stages, basic Attack combat, and automatic Expedition Camp at 42% HP or lower. Standard runs begin at 50% regional exploration; contract runs use the required unlock state.",
        "",
        "## Standard route/depth matrix",
        "",
        "| Band | Lv | Region | Depth | Route | Complete | Defeat | Combat | Hazard | Rare | Camp | Travel min | XP | Gil | Seals | Finish HP |",
        "|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["standard"]:
        lines.append(
            f"| {row['band']} | {row['level']} | {row['region']} | {row['depth']} | {row['route']} | {row['completion_rate']*100:.1f}% | {row['defeat_rate']*100:.1f}% | {row['avg_combats']:.2f} | {row['avg_hazards']:.2f} | {row['avg_rare_events']:.2f} | {row['avg_camps']:.2f} | {row['avg_travel_minutes']:.1f} | {row['avg_xp']:.0f} | {row['avg_gil']:.0f} | {row['avg_seals']:.1f} | {row['avg_finish_hp_pct']:.0f}% |"
        )
    lines += [
        "",
        "## Regional and Legendary contracts",
        "",
        "| Region | Lv | Contract | Route | Complete | Defeat | Combat | Hazard | Travel min | XP | Gil | Seals | Finish HP |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["contracts"]:
        lines.append(
            f"| {row['region']} | {row['level']} | {row['contract']} | {row['route']} | {row['completion_rate']*100:.1f}% | {row['defeat_rate']*100:.1f}% | {row['avg_combats']:.2f} | {row['avg_hazards']:.2f} | {row['avg_travel_minutes']:.1f} | {row['avg_xp']:.0f} | {row['avg_gil']:.0f} | {row['avg_seals']:.1f} | {row['avg_finish_hp_pct']:.0f}% |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reproducible Crystal Guild Expedition balance simulations.")
    parser.add_argument("--runs", type=int, default=60, help="runs per scenario (default: 60)")
    parser.add_argument("--seed", type=int, default=1201)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    report = run_matrix(max(1, args.runs), args.seed)
    text = markdown(report)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

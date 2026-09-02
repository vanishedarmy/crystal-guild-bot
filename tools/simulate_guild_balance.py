from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crystal_guild.fellowship import (
    AIRSHIP_MISSIONS,
    DEEDS,
    FELLOWSHIP_LEVEL_THRESHOLDS,
    LEGACY_ACCOMPLISHMENTS,
    ORDER_DEFINITIONS,
    PROJECTS,
    WEEKLY_ORDER_SET_REWARD,
)

PROFILES: dict[str, dict[str, Any]] = {
    "casual": {
        "label": "Casual Guild",
        "players": 5,
        "weekly_gil": 55_000,
        "weekly_items": {
            "iron_ore": 28,
            "ancient_coin": 8,
            "mythril_ore": 9,
            "elemental_crystal": 8,
            "wyvern_scale": 7,
            "adamantite": 0.6,
            "magitek_capacitor": 1.0,
            "dark_matter": 0.35,
            "potion": 25,
            "hi_potion": 10,
            "tent": 4,
        },
        "weekly_activity": {
            "venture_complete": 70,
            "encounter_win": 50,
            "hunt_win": 8,
            "craft": 15,
            "forge": 10,
            "treasure": 18,
            "raid_clear": 1.2,
            "raid_participation": 8,
            "raid_win": 8,
            "expedition_complete": 4,
        },
    },
    "core": {
        "label": "Core Guild",
        "players": 10,
        "weekly_gil": 125_000,
        "weekly_items": {
            "iron_ore": 60,
            "ancient_coin": 18,
            "mythril_ore": 20,
            "elemental_crystal": 18,
            "wyvern_scale": 15,
            "adamantite": 1.8,
            "magitek_capacitor": 2.5,
            "dark_matter": 0.8,
            "potion": 50,
            "hi_potion": 20,
            "tent": 8,
        },
        "weekly_activity": {
            "venture_complete": 130,
            "encounter_win": 90,
            "hunt_win": 20,
            "craft": 30,
            "forge": 20,
            "treasure": 35,
            "raid_clear": 3,
            "raid_participation": 30,
            "raid_win": 30,
            "expedition_complete": 10,
        },
    },
    "active": {
        "label": "Active Guild",
        "players": 20,
        "weekly_gil": 250_000,
        "weekly_items": {
            "iron_ore": 120,
            "ancient_coin": 36,
            "mythril_ore": 40,
            "elemental_crystal": 36,
            "wyvern_scale": 30,
            "adamantite": 4,
            "magitek_capacitor": 5,
            "dark_matter": 1.8,
            "potion": 100,
            "hi_potion": 40,
            "tent": 16,
        },
        "weekly_activity": {
            "venture_complete": 260,
            "encounter_win": 180,
            "hunt_win": 40,
            "craft": 60,
            "forge": 40,
            "treasure": 70,
            "raid_clear": 5,
            "raid_participation": 70,
            "raid_win": 70,
            "expedition_complete": 20,
        },
    },
}

SPINE_QUEUE = [
    # Representative progression strategy: establish the main Lv.1/2 services,
    # secure Expedition access, then pursue the v1.3 centerpiece instead of
    # requiring every unrelated facility to hit Lv.3 before the Airship exists.
    "workshop_t1",
    "archives_t1",
    "chocobo_stable_t1",
    "guild_hall_t2",
    "workshop_t2",
    "archives_t2",
    "chocobo_stable_t2",
    "expedition_board",
    "guild_hall_t3",
    "airship_dock_t1",
    "crystal_guild_airship",
    "workshop_t3",
    "archives_t3",
    "chocobo_stable_t3",
    "airship_dock_t2",
    "airship_dock_t3",
]
for _tier in (1, 2, 3):
    for _upgrade in ("hull", "engine", "cargo", "survey", "crystal_core"):
        SPINE_QUEUE.append(f"airship_{_upgrade}_t{_tier}")

COMMUNITY_PROJECTS = [
    "moogle_relief_shipment",
    "clear_the_roads",
    "forge_stockpile",
    "chart_the_frontier",
    "frontier_stores",
    "raid_preparedness",
]


class GuildBalanceSimulator:
    def __init__(self, profile: dict[str, Any], seed: int):
        self.profile = profile
        self.rng = random.Random(seed)
        self.renown = 0
        self.level = 1
        self.pools: defaultdict[str, float] = defaultdict(float)
        self.facilities = {"guild_hall": 1, "workshop": 0, "archives": 0, "chocobo_stable": 0, "airship_dock": 0}
        self.upgrades = {key: 0 for key in ("hull", "engine", "cargo", "survey", "crystal_core")}
        self.airship_built = False
        self.expedition_board = False
        self.completed: set[str] = set()
        self.project_progress: dict[str, defaultdict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.active_project: str | None = None
        self.total_activity: defaultdict[str, int] = defaultdict(int)
        self.week_activity: defaultdict[str, int] = defaultdict(int)
        self.total_gil_donated = 0.0
        self.weekly_sets = 0
        self.deeds_claimed: set[str] = set()
        self.legacy_claimed: set[str] = set()
        self.airship_missions = 0
        self.airship_active: dict[str, Any] | None = None
        self.mission_index = 0
        self.milestones: dict[str, float] = {}

    def _poisson(self, lam: float) -> int:
        if lam <= 0:
            return 0
        if lam < 20:
            limit = math.exp(-lam)
            k = 0
            product = 1.0
            while product > limit:
                k += 1
                product *= self.rng.random()
            return k - 1
        return max(0, int(round(self.rng.gauss(lam, math.sqrt(lam)))))

    @staticmethod
    def _level_for(renown: int) -> int:
        level = 1
        for index, threshold in enumerate(FELLOWSHIP_LEVEL_THRESHOLDS, start=1):
            if renown >= threshold:
                level = index
        return min(level, len(FELLOWSHIP_LEVEL_THRESHOLDS))

    @staticmethod
    def _activity_value(activity: str, source: dict[str, int]) -> int:
        if activity in {"combat_victory", "monster_victory"}:
            return int(source.get("encounter_win", 0)) + int(source.get("hunt_win", 0))
        if activity == "craft_forge":
            return int(source.get("craft", 0)) + int(source.get("forge", 0))
        return int(source.get(activity, 0))

    def _project_available(self, project_id: str) -> bool:
        if project_id in self.completed:
            return False
        project = PROJECTS[project_id]
        if self.level < int(project.get("required_level", 1)):
            return False
        project_type = str(project.get("project_type") or "construction")
        if project_type == "airship_construction":
            return (not self.airship_built) and self.facilities["airship_dock"] >= int(project.get("required_dock_level", 1))
        if project_type == "airship_upgrade":
            upgrade_id = str(project["upgrade_id"])
            return (
                self.airship_built
                and self.upgrades[upgrade_id] + 1 == int(project["tier"])
                and self.facilities["airship_dock"] >= int(project.get("required_dock_level", project["tier"]))
            )
        if project_type in {"supply_drive", "guild_objective"}:
            return True
        if project.get("teaser"):
            return (not self.expedition_board) and self.facilities["guild_hall"] >= int(project.get("required_hall_tier", 1))
        facility_id = str(project["facility_id"])
        tier = int(project["tier"])
        if self.facilities.get(facility_id, 0) + 1 != tier:
            return False
        if facility_id == "airship_dock":
            return self.facilities["guild_hall"] >= int(project.get("required_hall_tier", 1))
        if facility_id != "guild_hall" and tier > self.facilities["guild_hall"]:
            return False
        return True

    def _refine_for_project(self, project: dict[str, Any]) -> None:
        if self.facilities["workshop"] < 2:
            return
        item_requirements = [req for req in project["requirements"] if req["kind"] == "item"]
        for req in item_requirements:
            asset = str(req["asset_id"])
            need = max(0, int(req["target"]) - int(self.project_progress[project["id"]][req["key"]]) - int(self.pools[asset]))
            if need <= 0:
                continue
            if asset == "mythril_ore":
                possible = min(need, int(self.pools["iron_ore"] // 5), int(self.pools["gil"] // 250))
                if possible > 0:
                    self.pools["iron_ore"] -= possible * 5
                    self.pools["gil"] -= possible * 250
                    self.pools["mythril_ore"] += possible
            elif self.facilities["workshop"] >= 3 and asset == "adamantite":
                possible = min(need, int(self.pools["mythril_ore"] // 6), int(self.pools["gil"] // 750))
                if possible > 0:
                    self.pools["mythril_ore"] -= possible * 6
                    self.pools["gil"] -= possible * 750
                    self.pools["adamantite"] += possible
            elif self.facilities["workshop"] >= 3 and asset == "dark_matter":
                possible = min(need, int(self.pools["elemental_crystal"] // 10), int(self.pools["gil"] // 1000))
                if possible > 0:
                    self.pools["elemental_crystal"] -= possible * 10
                    self.pools["gil"] -= possible * 1000
                    self.pools["dark_matter"] += possible

    def _finish_project(self, project_id: str, day: int) -> None:
        project = PROJECTS[project_id]
        project_type = str(project.get("project_type") or "construction")
        self.completed.add(project_id)
        bonus = 250 * max(1, int(project.get("tier", 1)))
        if project_type == "airship_construction":
            self.airship_built = True
            bonus = int(project.get("reward_renown", 1500))
            self.milestones.setdefault("airship_week", (day + 1) / 7.0)
        elif project_type == "airship_upgrade":
            self.upgrades[str(project["upgrade_id"])] = int(project["tier"])
            bonus = int(project.get("reward_renown", 300 * int(project["tier"])))
        elif project_type in {"supply_drive", "guild_objective"}:
            bonus = int(project.get("reward_renown", 300))
        elif project.get("teaser"):
            self.expedition_board = True
        else:
            self.facilities[str(project["facility_id"])] = int(project["tier"])
            if project["facility_id"] == "airship_dock" and int(project["tier"]) == 1:
                self.milestones.setdefault("dock1_week", (day + 1) / 7.0)
        self.renown += bonus

    def _claim_deeds(self) -> None:
        for deed in DEEDS:
            if deed["id"] in self.deeds_claimed:
                continue
            if self._activity_value(str(deed["activity"]), self.total_activity) >= int(deed["target"]):
                self.deeds_claimed.add(str(deed["id"]))
                self.renown += int(deed["renown"])

    def _claim_legacy(self) -> None:
        metrics = {
            "major_facilities_built": sum(self.facilities.get(key, 0) >= 1 for key in ("guild_hall", "workshop", "chocobo_stable", "archives", "airship_dock")),
            "major_facilities_complete": sum(self.facilities.get(key, 0) >= 3 for key in ("guild_hall", "workshop", "chocobo_stable", "archives", "airship_dock")),
            "gil_donated": int(self.total_gil_donated),
            "expeditions_completed": int(self.total_activity["expedition_complete"]),
            "raids_won": int(self.total_activity["raid_clear"]),
            "airship_built": int(self.airship_built),
            "airship_missions_completed": self.airship_missions,
            "airship_upgrade_tiers": sum(self.upgrades.values()),
            "deeds_complete": len(self.deeds_claimed),
            "weekly_sets_completed": self.weekly_sets,
        }
        for accomplishment in LEGACY_ACCOMPLISHMENTS:
            if accomplishment["id"] in self.legacy_claimed:
                continue
            if int(metrics.get(str(accomplishment["metric"]), 0)) >= int(accomplishment["target"]):
                self.legacy_claimed.add(str(accomplishment["id"]))
                self.renown += int(accomplishment["renown"])

    def _weekly_orders(self) -> None:
        selected = self.rng.sample(ORDER_DEFINITIONS, 3)
        completed = 0
        for order in selected:
            if self._activity_value(str(order["activity"]), self.week_activity) >= int(order["target"]):
                self.renown += int(order["renown"])
                completed += 1
        if completed == 3:
            self.renown += int(WEEKLY_ORDER_SET_REWARD["guild_renown"])
            self.weekly_sets += 1
        self.week_activity = defaultdict(int)

    def _progress_airship(self, activity: dict[str, int]) -> None:
        if not self.airship_built:
            return
        if self.airship_active is None:
            available = [mission for mission in AIRSHIP_MISSIONS if self.upgrades["crystal_core"] >= int(mission["required_core"])]
            mission = available[self.mission_index % len(available)]
            self.mission_index += 1
            target = max(1, int(math.ceil(int(mission["target"]) * (1.0 - 0.04 * self.upgrades["hull"]))))
            hours = float(mission["duration_hours"]) * (1.0 - 0.06 * self.upgrades["engine"])
            self.airship_active = {"mission": mission, "target": target, "days": max(1, int(math.ceil(hours / 24))), "elapsed": 0, "progress": 0}
        state = self.airship_active
        mission = state["mission"]
        state["elapsed"] += 1
        for activity_id, weight in dict(mission["activities"]).items():
            state["progress"] += self._activity_value(str(activity_id), activity) * int(weight)
        if state["elapsed"] >= state["days"]:
            if state["progress"] >= state["target"]:
                self.airship_missions += 1
                reward = int(round(int(mission["guild_renown"]) * (1.0 + 0.05 * self.upgrades["survey"])))
                self.renown += reward
            self.airship_active = None

    def run(self, *, max_days: int = 560) -> dict[str, Any]:
        queue = list(SPINE_QUEUE)
        for day in range(max_days):
            activity: dict[str, int] = {}
            for key, weekly in dict(self.profile["weekly_activity"]).items():
                count = self._poisson(float(weekly) / 7.0)
                activity[key] = count
                self.week_activity[key] += count
                self.total_activity[key] += count

            # Only player-bound activities generate Fellowship Renown. Shared raid_clear
            # is a project/deed counter; raid participant/winner events are already in
            # the profile as their player-level rewards.
            self.renown += activity.get("venture_complete", 0) * 8
            self.renown += activity.get("hunt_win", 0) * 18
            self.renown += activity.get("craft", 0) * 2
            self.renown += activity.get("forge", 0) * 8
            self.renown += activity.get("raid_participation", 0) * 12
            self.renown += activity.get("raid_win", 0) * 20

            self.pools["gil"] += max(0.0, self.rng.gauss(float(self.profile["weekly_gil"]) / 7.0, float(self.profile["weekly_gil"]) / 38.5))
            for asset, weekly in dict(self.profile["weekly_items"]).items():
                self.pools[str(asset)] += self._poisson(float(weekly) / 7.0)

            self.level = self._level_for(self.renown)
            if self.level >= 8:
                self.milestones.setdefault("level8_week", (day + 1) / 7.0)

            if self.active_project is None:
                for project_id in queue:
                    if self._project_available(project_id):
                        self.active_project = project_id
                        break

            if self.active_project is not None:
                project = PROJECTS[self.active_project]
                self._refine_for_project(project)
                for requirement in project["requirements"]:
                    key = str(requirement["key"])
                    target = int(requirement["target"])
                    if requirement["kind"] == "gil":
                        current = self.project_progress[self.active_project][key]
                        spend = min(max(0.0, target - current), self.pools["gil"])
                        self.project_progress[self.active_project][key] += spend
                        self.pools["gil"] -= spend
                        self.total_gil_donated += spend
                    elif requirement["kind"] == "item":
                        current = self.project_progress[self.active_project][key]
                        spend = min(max(0, target - int(current)), int(self.pools[str(requirement["asset_id"])]))
                        self.project_progress[self.active_project][key] += spend
                        self.pools[str(requirement["asset_id"])] -= spend
                    elif requirement["kind"] == "activity":
                        current = self.project_progress[self.active_project][key]
                        add = min(max(0, target - int(current)), self._activity_value(str(requirement["asset_id"]), activity))
                        self.project_progress[self.active_project][key] += add

                self.level = self._level_for(self.renown)
                complete = True
                for requirement in project["requirements"]:
                    current = self.level if requirement["kind"] == "level" else self.project_progress[self.active_project][str(requirement["key"])]
                    if current < int(requirement["target"]):
                        complete = False
                        break
                if complete:
                    project_id = self.active_project
                    self.active_project = None
                    self._finish_project(project_id, day)

            self._progress_airship(activity)
            self._claim_deeds()
            if day % 7 == 6:
                self._weekly_orders()
            self._claim_legacy()
            self.level = self._level_for(self.renown)

            if all(self.facilities.get(key, 0) >= 3 for key in ("guild_hall", "workshop", "chocobo_stable", "archives", "airship_dock")):
                self.milestones.setdefault("facilities_week", (day + 1) / 7.0)
            if sum(self.upgrades.values()) >= 15:
                self.milestones.setdefault("upgrades_week", (day + 1) / 7.0)
                break

        return {
            **self.milestones,
            "weeks": (day + 1) / 7.0,
            "renown": self.renown,
            "level": self.level,
            "airship_missions": self.airship_missions,
            "weekly_sets": self.weekly_sets,
            "legacy": len(self.legacy_claimed),
        }


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * p))))
    return round(float(ordered[index]), 2)


def run_matrix(runs_per_profile: int, seed: int) -> dict[str, Any]:
    report: dict[str, Any] = {"seed": seed, "runs_per_profile": runs_per_profile, "profiles": []}
    for offset, (profile_id, profile) in enumerate(PROFILES.items()):
        rows = [GuildBalanceSimulator(profile, seed + offset * 100_000 + index).run() for index in range(runs_per_profile)]
        summary: dict[str, Any] = {
            "id": profile_id,
            "label": profile["label"],
            "players": profile["players"],
            "runs": len(rows),
        }
        for key in ("level8_week", "dock1_week", "airship_week", "facilities_week", "upgrades_week"):
            vals = [float(row[key]) for row in rows if key in row]
            summary[key] = {
                "success_rate": round(len(vals) / max(1, len(rows)), 4),
                "median": _percentile(vals, 0.5),
                "p90": _percentile(vals, 0.9),
            }
        summary["median_airship_missions"] = round(statistics.median(row["airship_missions"] for row in rows), 1)
        summary["median_weekly_sets"] = round(statistics.median(row["weekly_sets"] for row in rows), 1)
        report["profiles"].append(summary)
    report["total_runs"] = runs_per_profile * len(PROFILES)
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Crystal Guild — Guild Economy & Progression Simulation",
        "",
        f"Fixed seed: `{report['seed']}`  ",
        f"Runs per Guild profile: **{report['runs_per_profile']}**  ",
        f"Total simulated Guild seasons: **{report['total_runs']}**",
        "",
        "The model uses the shipping Fellowship level thresholds, project requirements, Weekly Order shared Renown, Airship mission rewards, Legacy rewards, and Workshop refining recipes. Each profile supplies a conservative weekly pool of donatable Gil/materials plus representative normal-play activity. It excludes contribution Renown, so level timing is intentionally conservative.",
        "",
        "## Progression timing",
        "",
        "| Guild profile | Active heroes | Fellowship LVL 8 | Dock Lv.1 | Airship built | All major facilities Lv.3 | All Airship upgrades |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in report["profiles"]:
        def cell(key: str) -> str:
            row = profile[key]
            if row["median"] is None:
                return "—"
            return f"{row['median']:.1f} wk (P90 {row['p90']:.1f})"
        lines.append(
            f"| {profile['label']} | {profile['players']} | {cell('level8_week')} | {cell('dock1_week')} | {cell('airship_week')} | {cell('facilities_week')} | {cell('upgrades_week')} |"
        )
    lines += [
        "",
        "## Current tuning",
        "",
        "- Airship Dock construction remains a major commitment, but its Gil, Ancient Coin, and raid-clear requirements are lower than the earlier tuning curve.",
        "- Crystal Guild Airship construction has a modestly lower launch cost so the feature arrives before the upgrade grind dominates the season.",
        "- Airship upgrades now use material curves based on rarity: Adamantite and Dark Matter no longer require the same quantities as Mythril Ore or Elemental Crystals.",
        "- Airship upgrade Gil and raid-clear requirements are reduced while remaining substantial enough to make Tier III a long-term Guild goal.",
        "- Weekly Order contributor payouts, Supply Drive rewards, Workshop refining rates, Fellowship level thresholds, and Legacy milestones remain unchanged after the audit.",
        "",
        "## Interpretation",
        "",
        "The Core profile is the primary balance target: the Airship should arrive over several weeks rather than immediately, while full Tier III facility/Airship completion remains a longer-term season goal. Casual Guilds are allowed to take substantially longer, and very active Guilds progress faster without collapsing the entire system into a few days.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reproducible Crystal Guild v1.3 Fellowship economy simulations.")
    parser.add_argument("--runs", type=int, default=1000, help="simulations per Guild profile (default: 1000)")
    parser.add_argument("--seed", type=int, default=1301)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    report = run_matrix(max(1, args.runs), int(args.seed))
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

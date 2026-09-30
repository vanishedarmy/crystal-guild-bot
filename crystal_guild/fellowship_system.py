from __future__ import annotations

import math
import re
import time
from typing import Any

from .trophies import reconcile_player_trophies
from .guild_initiatives import progress_event

from .fellowship import (
    AIRSHIP_MISSIONS,
    AIRSHIP_UPGRADES,
    DEEDS,
    FACILITIES,
    GUILD_RANKS,
    LEGACY_ACCOMPLISHMENTS,
    GUILD_EXPANSION_FACILITY_IDS,
    PUBLIC_GUILD_FACILITY_IDS,
    PROJECTS,
    WEEKLY_ORDER_SET_REWARD,
    WORKSHOP_EXCHANGES,
    facility_effects,
    fellowship_level_for_renown,
    fellowship_level_progress,
    guild_rank_for_renown,
    legacy_metric_values,
    legacy_snapshot_from_connection,
    weekly_orders,
    weekly_period_key,
)


ACTIVITY_RENOWN = {
    "venture_complete": 8,
    "treasure": 8,
    "encounter_win": 10,
    "combat_victory": 10,
    "monster_victory": 10,
    "hunt_win": 18,
    "raid_participation": 12,
    "raid_win": 20,
    "craft": 2,
    "forge": 8,
    "job_mastery": 50,
}


# Offline Progression hotfix removes live-stream-only gates from Fellowship construction and
# Airship upgrades. These aliases preserve partial progress from projects that
# were already underway before the requirement keys changed. Old rows are kept
# as harmless audit history; the new offline key receives the same progress.
OFFLINE_PROJECT_REQUIREMENT_MIGRATIONS = {
    **{f"guild_hall_t{tier}": ("activity:raid_clear", "activity:hunt_win") for tier in range(2, 6)},
    **{f"airship_dock_t{tier}": ("activity:raid_clear", "activity:hunt_win") for tier in range(1, 4)},
    "expedition_board": ("activity:raid_clear", "activity:hunt_win"),
    "raid_preparedness": ("activity:raid_clear", "activity:combat_victory"),
    "crystal_guild_airship": ("activity:raid_clear", "activity:hunt_win"),
    **{
        f"airship_{upgrade_id}_t{tier}": ("activity:raid_clear", "activity:hunt_win")
        for upgrade_id in AIRSHIP_UPGRADES
        for tier in range(1, 4)
    },
}


def _project_query_key(value: Any) -> str:
    """Normalize human-facing project labels for streamer selection.

    Public Fellowship cards intentionally show friendly names such as
    ``Moogle Emporium Annex — Lv. 1``. Streamer controls should accept that
    exact label, the facility name without the level suffix, or a unique short
    fragment instead of requiring an internal identifier.
    """
    text = str(value or "").casefold().replace("’", "'")
    text = re.sub(r"[—–-]+", " ", text)
    text = re.sub(r"\b(?:lv|level|tier)\.?\s*\d+\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


class FellowshipSystem:
    """Persistent channel-wide Fellowship progression.

    The Bot database remains authoritative. Every mutation is safe to call from
    inside the engine's existing outer transactions because Database.tx() is
    composable and uses savepoints for nested writes.
    """

    def __init__(self, db: Any, data: Any):
        self.db = db
        self.data = data
        self._seed_static_rows()
        self._migrate_offline_project_requirements()
        self._settle_legacy_accomplishments()

    def _seed_static_rows(self) -> None:
        with self.db.tx() as conn:
            conn.execute("INSERT OR IGNORE INTO fellowship_state(singleton_id,level,renown) VALUES (1,1,0)")
            for facility_id in FACILITIES:
                tier = 1 if facility_id == "guild_hall" else 0
                conn.execute(
                    "INSERT OR IGNORE INTO fellowship_facilities(facility_id,tier) VALUES (?,?)",
                    (facility_id, tier),
                )
            for deed in DEEDS:
                conn.execute(
                    "INSERT OR IGNORE INTO fellowship_deeds(deed_id,progress,target) VALUES (?,?,?)",
                    (deed["id"], 0, int(deed["target"])),
                )
        self._ensure_orders()

    def _migrate_offline_project_requirements(self) -> None:
        """Carry partial progress from former Raid-gated construction into offline goals."""
        with self.db.tx() as conn:
            for project_id, (old_key, new_key) in OFFLINE_PROJECT_REQUIREMENT_MIGRATIONS.items():
                project = PROJECTS.get(project_id)
                if not project:
                    continue
                requirement = next((row for row in project.get("requirements", []) if row.get("key") == new_key), None)
                if not requirement:
                    continue
                old = conn.execute(
                    "SELECT current FROM fellowship_project_progress WHERE project_id=? AND requirement_key=?",
                    (project_id, old_key),
                ).fetchone()
                if not old:
                    continue
                carried = min(max(0, int(old["current"] or 0)), max(1, int(requirement.get("target", 1))))
                if carried <= 0:
                    continue
                conn.execute(
                    "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES (?,?,?) "
                    "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=MAX(fellowship_project_progress.current,excluded.current)",
                    (project_id, new_key, carried),
                )

    def ensure_member(self, player_id: str, *, founding: bool = False) -> None:
        self.db.execute(
            "INSERT OR IGNORE INTO fellowship_members(player_id,founding_member) VALUES (?,?)",
            (str(player_id), 1 if founding else 0),
        )

    def _state(self) -> Any:
        return self.db.one("SELECT * FROM fellowship_state WHERE singleton_id=1")

    def facility_tiers(self) -> dict[str, int]:
        rows = self.db.all("SELECT facility_id,tier FROM fellowship_facilities")
        return {str(row["facility_id"]): int(row["tier"]) for row in rows}

    def effects(self) -> dict[str, float]:
        return facility_effects(self.facility_tiers())

    def effective_camp_seconds(self, base_seconds: int) -> int:
        reduction = self.effects()["camp_reduction"]
        return max(60, int(round(int(base_seconds) * (1.0 - reduction))))

    def effective_shop_refresh_seconds(self, base_seconds: int) -> int:
        reduction = self.effects()["shop_refresh_reduction"]
        return max(60, int(round(int(base_seconds) * (1.0 - reduction))))

    def effective_forge_gil(self, base_gil: int) -> int:
        discount = self.effects()["forge_discount"]
        return max(0, int(round(int(base_gil) * (1.0 - discount))))

    def emporium_annex_level(self) -> int:
        return max(0, min(1, int(self.facility_tiers().get("emporium_annex", 0))))

    def emporium_annex_stock_bonus(self) -> dict[str, int]:
        if self.emporium_annex_level() < 1:
            return {"weapons": 0, "armor": 0, "items": 0}
        return {"weapons": 2, "armor": 4, "items": 6}

    def emporium_stock_slots(self) -> int:
        bonus = self.emporium_annex_stock_bonus()
        return 9 + sum(bonus.values())

    def trading_post_level(self) -> int:
        return max(0, min(1, int(self.facility_tiers().get("trading_post", 0))))

    def trading_post_unlocked(self) -> bool:
        return self.trading_post_level() >= 1

    def major_facility_level(self, facility_id: str) -> int:
        config = FACILITIES.get(str(facility_id), {})
        maximum = int(config.get("max_level", config.get("max_tier", 0)) or 0)
        return max(0, min(maximum, int(self.facility_tiers().get(str(facility_id), 0))))

    def effective_chocobo_xp(self, base_xp: int) -> int:
        bonus = float(self.effects().get("chocobo_xp_bonus", 0.0))
        return max(0, int(round(max(0, int(base_xp)) * (1.0 + bonus))))

    def archive_rare_event_bonus(self) -> float:
        return max(0.0, float(self.effects().get("archive_rare_event_bonus", 0.0)))

    def _airship_state(self) -> Any:
        return self.db.one("SELECT * FROM fellowship_airship_state WHERE singleton_id=1")

    def airship_upgrades(self) -> dict[str, int]:
        rows = self.db.all("SELECT upgrade_id,tier FROM fellowship_airship_upgrades")
        values = {str(row["upgrade_id"]): max(0, min(3, int(row["tier"] or 0))) for row in rows}
        for upgrade_id in AIRSHIP_UPGRADES:
            values.setdefault(upgrade_id, 0)
        return values

    @staticmethod
    def _airship_mission_definition(mission_id: str) -> dict[str, Any] | None:
        return next((mission for mission in AIRSHIP_MISSIONS if mission["id"] == str(mission_id)), None)

    def _airship_mission_target(self, mission: dict[str, Any], upgrades: dict[str, int]) -> int:
        # Hull reinforcement gives dangerous deployments a small progress buffer
        # without making normal play irrelevant. At Tier III the requirement is
        # only 12% lower than the base mission target.
        hull = max(0, min(3, int(upgrades.get("hull", 0))))
        return max(1, int(math.ceil(int(mission["target"]) * (1.0 - (0.04 * hull)))))

    def _airship_mission_duration(self, mission: dict[str, Any], upgrades: dict[str, int]) -> int:
        engine = max(0, min(3, int(upgrades.get("engine", 0))))
        hours = float(mission["duration_hours"]) * (1.0 - (0.06 * engine))
        return max(6 * 3600, int(round(hours * 3600)))

    @staticmethod
    def _activity_semantics(activity: str) -> set[str]:
        """Return every requirement family satisfied by one completed activity.

        Source-specific events remain distinct for Hunts, Raids, Ventures, and
        other systems, while broad labels such as ``combat_victory`` and
        ``monster_victory`` are treated the way players naturally read them.
        This keeps Fellowship construction, Weekly Orders, Deeds, and Airship
        missions aligned even as new combat sources are added.
        """
        activity = str(activity)
        semantics = {activity}
        if activity in {"encounter_win", "hunt_win", "monster_victory"}:
            semantics.update({"combat_victory", "monster_victory"})
        elif activity == "raid_win":
            semantics.add("combat_victory")
        return semantics

    def _progress_airship_mission(self, conn: Any, player_id: str | None, activity: str, amount: int) -> None:
        state = conn.execute("SELECT * FROM fellowship_airship_state WHERE singleton_id=1").fetchone()
        if not state or not int(state["built"] or 0) or not state["active_mission_id"]:
            return
        now = int(time.time())
        if state["ends_at"] is not None and now >= int(state["ends_at"]):
            return
        mission = self._airship_mission_definition(str(state["active_mission_id"]))
        if not mission:
            return
        activity_weights = mission.get("activities") or {}
        # A source event may satisfy a broader activity family (for example a
        # Hunt win is also a combat victory). Use the strongest matching weight
        # rather than summing aliases, so one victory can never double-count.
        weight = max(
            (int(activity_weights.get(candidate, 0)) for candidate in self._activity_semantics(activity)),
            default=0,
        )
        if weight <= 0:
            return
        before = max(0, int(state["progress"] or 0))
        target = max(1, int(state["target"] or mission["target"]))
        add = max(0, min(target - before, max(1, int(amount)) * weight))
        if not add:
            return
        conn.execute(
            "UPDATE fellowship_airship_state SET progress=progress+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1",
            (add,),
        )
        if player_id and state["active_run_id"]:
            conn.execute(
                "INSERT INTO fellowship_airship_mission_members(run_id,player_id,contribution) VALUES (?,?,?) "
                "ON CONFLICT(run_id,player_id) DO UPDATE SET contribution=fellowship_airship_mission_members.contribution+excluded.contribution",
                (str(state["active_run_id"]), str(player_id), add),
            )

    def _settle_airship_mission_if_due(self, now: int | None = None) -> list[str]:
        """Settle a due Airship run as one serialized, replay-safe mutation.

        The active run is re-read after taking the database write lock. This
        prevents a stale heartbeat/reconnect worker from clearing or paying a
        newer mission that launched after another worker already settled the
        old run.
        """
        now = int(time.time()) if now is None else int(now)
        with self.db.tx() as conn:
            state = conn.execute(
                "SELECT * FROM fellowship_airship_state WHERE singleton_id=1"
            ).fetchone()
            if not state or not state["active_mission_id"] or not state["active_run_id"]:
                return []
            if state["ends_at"] is None or now < int(state["ends_at"]):
                return []

            run_id = str(state["active_run_id"])
            mission = self._airship_mission_definition(str(state["active_mission_id"]))
            if not mission:
                conn.execute(
                    "UPDATE fellowship_airship_state SET active_mission_id=NULL,active_run_id=NULL,started_at=NULL,ends_at=NULL,progress=0,target=0,missions_failed=missions_failed+1,updated_at=CURRENT_TIMESTAMP "
                    "WHERE singleton_id=1 AND active_run_id=?",
                    (run_id,),
                )
                return ["AIRSHIP — The returning mission record was invalid and has been cleared."]

            progress = max(0, int(state["progress"] or 0))
            target = max(1, int(state["target"] or mission["target"]))
            success = progress >= target
            guild_state = conn.execute(
                "SELECT level FROM fellowship_state WHERE singleton_id=1"
            ).fetchone()
            old_level = int(guild_state["level"] if guild_state else 1)
            upgrades = {
                str(row["upgrade_id"]): max(0, min(3, int(row["tier"] or 0)))
                for row in conn.execute("SELECT upgrade_id,tier FROM fellowship_airship_upgrades").fetchall()
            }
            survey = max(0, min(3, int(upgrades.get("survey", 0))))
            cargo = max(0, min(3, int(upgrades.get("cargo", 0))))
            guild_reward = int(round(int(mission["guild_renown"]) * (1.0 + 0.05 * survey))) if success else 0
            personal_gil = int(round(int(mission["personal_gil"]) * (1.0 + 0.10 * cargo))) if success else 0
            personal_renown = int(mission["personal_renown"]) if success else 0
            participants = conn.execute(
                "SELECT player_id,contribution FROM fellowship_airship_mission_members WHERE run_id=? ORDER BY contribution DESC,player_id",
                (run_id,),
            ).fetchall()

            event_key = f"airship_mission_settle:{run_id}"
            inserted = conn.execute(
                "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,NULL,'airship_mission_settle',?,1)",
                (event_key, guild_reward),
            ).rowcount
            if not inserted:
                # A prior worker already settled this exact run. Only clear the
                # state if the same stale run is still present; never clear a
                # newer mission that may have launched meanwhile.
                conn.execute(
                    "UPDATE fellowship_airship_state SET active_mission_id=NULL,active_run_id=NULL,started_at=NULL,ends_at=NULL,progress=0,target=0,updated_at=CURRENT_TIMESTAMP "
                    "WHERE singleton_id=1 AND active_run_id=?",
                    (run_id,),
                )
                return []

            if success and guild_reward:
                conn.execute(
                    "UPDATE fellowship_state SET renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1",
                    (guild_reward,),
                )

            rewarded = 0
            if success:
                for row in participants:
                    participant_id = str(row["player_id"])
                    conn.execute(
                        "INSERT OR IGNORE INTO fellowship_members(player_id) VALUES (?)",
                        (participant_id,),
                    )
                    reward_key = f"airship_mission_reward:{run_id}:{participant_id}"
                    reward_inserted = conn.execute(
                        "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,?,'airship_mission_reward',0,1)",
                        (reward_key, participant_id),
                    ).rowcount
                    if not reward_inserted:
                        continue
                    if personal_gil:
                        conn.execute(
                            "UPDATE players SET gil=gil+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
                            (personal_gil, participant_id),
                        )
                        conn.execute(
                            "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,'guild_airship')",
                            (participant_id, personal_gil),
                        )
                    if personal_renown:
                        conn.execute(
                            "UPDATE fellowship_members SET renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
                            (personal_renown, participant_id),
                        )
                    rewarded += 1

            outcome = "success" if success else "failed"
            conn.execute(
                "INSERT OR REPLACE INTO fellowship_airship_mission_history(run_id,mission_id,started_at,ended_at,outcome,progress,target,guild_renown,participant_count) VALUES (?,?,?,?,?,?,?,?,?)",
                (run_id, mission["id"], int(state["started_at"] or now), now, outcome, progress, target, guild_reward, len(participants)),
            )
            if success:
                conn.execute(
                    "UPDATE fellowship_airship_state SET active_mission_id=NULL,active_run_id=NULL,started_at=NULL,ends_at=NULL,progress=0,target=0,missions_completed=missions_completed+1,updated_at=CURRENT_TIMESTAMP "
                    "WHERE singleton_id=1 AND active_run_id=?",
                    (run_id,),
                )
                conn.execute(
                    "INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'airship_mission_complete',?,?)",
                    (mission["name"], guild_reward),
                )
            else:
                conn.execute(
                    "UPDATE fellowship_airship_state SET active_mission_id=NULL,active_run_id=NULL,started_at=NULL,ends_at=NULL,progress=0,target=0,missions_failed=missions_failed+1,updated_at=CURRENT_TIMESTAMP "
                    "WHERE singleton_id=1 AND active_run_id=?",
                    (run_id,),
                )
                conn.execute(
                    "INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'airship_mission_failed',?,0)",
                    (mission["name"],),
                )

            # Keep Guild level/Legacy/project settlement in the same outer
            # transaction as the mission payout so no concurrent Guild action
            # can observe a half-settled return.
            notes = self._finalize_progress(None, old_level, None)

            if success:
                return [
                    f"AIRSHIP MISSION COMPLETE — {mission['name']} (+{guild_reward} Fellowship Renown).",
                    f"Airship crew support — {rewarded} contributor{'s' if rewarded != 1 else ''} received {personal_gil:,}g +{personal_renown} personal Renown.",
                    *notes[:2],
                ]
            return [f"AIRSHIP MISSION FAILED — {mission['name']} returned at {progress}/{target} mission progress."]

    def start_airship_mission(self, query: str) -> tuple[bool, str, dict[str, Any] | None]:
        self._settle_airship_mission_if_due()
        norm = str(query or "").strip().lower().replace("-", "_").replace(" ", "_")
        with self.db.tx() as conn:
            # Re-read after taking the write lock. Two owner actions arriving
            # together may never overwrite one another's active run.
            state = conn.execute(
                "SELECT * FROM fellowship_airship_state WHERE singleton_id=1"
            ).fetchone()
            if not state or not int(state["built"] or 0):
                return False, "The Crystal Guild Airship has not been completed yet.", None
            if state["active_mission_id"]:
                mission = self._airship_mission_definition(str(state["active_mission_id"]))
                return False, f"The Airship is already away on {mission['name'] if mission else 'a mission'}.", None

            upgrades = {
                str(row["upgrade_id"]): max(0, min(3, int(row["tier"] or 0)))
                for row in conn.execute("SELECT upgrade_id,tier FROM fellowship_airship_upgrades").fetchall()
            }
            core = int(upgrades.get("crystal_core", 0))
            unlocked = [mission for mission in AIRSHIP_MISSIONS if int(mission.get("required_core", 0)) <= core]
            mission = next((item for item in unlocked if item["id"] == norm), None)
            if mission is None:
                mission = next((item for item in unlocked if str(item["name"]).lower() == str(query or "").strip().lower()), None)
            if mission is None:
                names = ", ".join(item["name"] for item in unlocked) or "none"
                return False, f"Airship mission unavailable. Unlocked missions: {names}.", None

            now = int(time.time())
            duration = self._airship_mission_duration(mission, upgrades)
            target = self._airship_mission_target(mission, upgrades)
            run_id = f"{mission['id']}:{time.time_ns()}"
            updated = conn.execute(
                "UPDATE fellowship_airship_state SET active_mission_id=?,active_run_id=?,started_at=?,ends_at=?,progress=0,target=?,updated_at=CURRENT_TIMESTAMP "
                "WHERE singleton_id=1 AND active_mission_id IS NULL AND active_run_id IS NULL",
                (mission["id"], run_id, now, now + duration, target),
            ).rowcount
            if not updated:
                return False, "The Airship received another mission order first. Check its current deployment.", None
            conn.execute(
                "INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'airship_mission_started',?,?)",
                (mission["name"], target),
            )

        snapshot = self.airship_snapshot()
        active = snapshot.get("active_mission")
        return True, f"AIRSHIP MISSION — {mission['name']} launched. Return in {active['duration_label'] if active else 'scheduled time'}; goal {target} progress.", active

    def airship_snapshot(self, now: int | None = None) -> dict[str, Any]:
        now = int(time.time()) if now is None else int(now)
        settlement_notes = self._settle_airship_mission_if_due(now)
        state = self._airship_state()
        upgrades = self.airship_upgrades()
        built = bool(state and int(state["built"] or 0))
        core = int(upgrades.get("crystal_core", 0))
        mission_list = []
        for mission in AIRSHIP_MISSIONS:
            unlocked = built and int(mission.get("required_core", 0)) <= core
            mission_list.append({
                **mission,
                "unlocked": unlocked,
                "target_effective": self._airship_mission_target(mission, upgrades),
                "duration_seconds": self._airship_mission_duration(mission, upgrades),
            })
        active = None
        if state and state["active_mission_id"]:
            mission = self._airship_mission_definition(str(state["active_mission_id"]))
            if mission:
                remaining = max(0, int(state["ends_at"] or now) - now)
                hours, rem = divmod(remaining, 3600)
                minutes = rem // 60
                participants = self.db.one(
                    "SELECT COUNT(*) AS n FROM fellowship_airship_mission_members WHERE run_id=?",
                    (str(state["active_run_id"]),),
                )
                active = {
                    **mission,
                    "run_id": str(state["active_run_id"]),
                    "started_at": int(state["started_at"] or now),
                    "ends_at": int(state["ends_at"] or now),
                    "progress": int(state["progress"] or 0),
                    "target": int(state["target"] or mission["target"]),
                    "ready": int(state["progress"] or 0) >= int(state["target"] or mission["target"]),
                    "remaining_seconds": remaining,
                    "duration_label": f"{hours}h {minutes:02d}m" if hours else f"{minutes}m",
                    "participant_count": int(participants["n"] if participants else 0),
                }
        history_rows = self.db.all(
            "SELECT * FROM fellowship_airship_mission_history ORDER BY ended_at DESC LIMIT 5"
        )
        history = []
        for row in history_rows:
            mission = self._airship_mission_definition(str(row["mission_id"])) or {"name": str(row["mission_id"])}
            history.append({
                "run_id": row["run_id"], "mission_id": row["mission_id"], "name": mission["name"],
                "outcome": row["outcome"], "progress": int(row["progress"]), "target": int(row["target"]),
                "guild_renown": int(row["guild_renown"]), "participant_count": int(row["participant_count"]),
                "ended_at": int(row["ended_at"]),
            })
        return {
            "built": built,
            "dock_level": self.major_facility_level("airship_dock"),
            "missions_completed": int(state["missions_completed"] or 0) if state else 0,
            "missions_failed": int(state["missions_failed"] or 0) if state else 0,
            "active_mission": active,
            "missions": mission_list,
            "upgrades": [
                {"id": upgrade_id, "name": AIRSHIP_UPGRADES[upgrade_id]["name"], "description": AIRSHIP_UPGRADES[upgrade_id]["description"], "tier": int(upgrades.get(upgrade_id, 0)), "max_tier": 3}
                for upgrade_id in AIRSHIP_UPGRADES
            ],
            "history": history,
            "settlement_notes": settlement_notes[:3],
        }

    def workshop_services_snapshot(self, player_id: str | None = None) -> dict[str, Any]:
        workshop_level = self.major_facility_level("workshop")
        stable_level = self.major_facility_level("chocobo_stable")
        archive_level = self.major_facility_level("archives")
        annex_level = self.emporium_annex_level()
        trading_post_level = self.trading_post_level()
        player = self.db.one("SELECT gil FROM players WHERE twitch_id=?", (str(player_id),)) if player_id else None
        gil = max(0, int(player["gil"] or 0)) if player else 0
        exchanges: list[dict[str, Any]] = []
        for config in WORKSHOP_EXCHANGES:
            input_id = str(config["input_id"])
            output_id = str(config["output_id"])
            input_item = self.data.items.get(input_id, {})
            output_item = self.data.items.get(output_id, {})
            owned = 0
            if player_id:
                row = self.db.one("SELECT quantity FROM inventory WHERE player_id=? AND item_id=?", (str(player_id), input_id))
                owned = max(0, int(row["quantity"] or 0)) if row else 0
            unlocked = workshop_level >= int(config["min_level"])
            max_batches = 0
            if player_id and unlocked:
                max_batches = owned // max(1, int(config["input_qty"]))
                fee = max(0, int(config.get("gil", 0)))
                if fee:
                    max_batches = min(max_batches, gil // fee)
                max_batches = max(0, min(20, max_batches))
            exchanges.append({
                **config,
                "input_name": str(input_item.get("name") or input_id.replace("_", " ").title()),
                "output_name": str(output_item.get("name") or output_id.replace("_", " ").title()),
                "unlocked": unlocked,
                "owned": owned,
                "max_batches": max_batches,
            })
        return {
            "guild_hall": {"level": self.major_facility_level("guild_hall"), "message": "Guild Hall coordinates construction, Supply Drives, Objectives, and shared services."},
            "workshop": {"level": workshop_level, "forge_discount": float(self.effects().get("forge_discount", 0.0)), "exchanges": exchanges},
            "chocobo_stable": {"level": stable_level, "xp_bonus": float(self.effects().get("chocobo_xp_bonus", 0.0))},
            "archive": {"level": archive_level, "rare_event_bonus": self.archive_rare_event_bonus()},
            "emporium_annex": {
                "level": annex_level,
                "unlocked": annex_level >= 1,
                "base_stock_slots": 9,
                "bonus_stock_slots": 12 if annex_level >= 1 else 0,
                "bonus_by_category": self.emporium_annex_stock_bonus(),
                "stock_slots": self.emporium_stock_slots(),
            },
            "trading_post": {
                "level": trading_post_level,
                "unlocked": trading_post_level >= 1,
                "listing_fee_rate": 0.02,
                "sale_tax_rate": 0.05,
                "listing_hours": 48,
            },
        }

    def workshop_exchange(self, player_id: str, exchange_id: str, batches: int = 1) -> tuple[bool, str]:
        exchange = next((item for item in WORKSHOP_EXCHANGES if item["id"] == str(exchange_id)), None)
        if not exchange:
            return False, "That Workshop refining service is not recognized."
        batches = int(batches)
        if batches < 1 or batches > 20:
            return False, "Workshop refining quantity must be between 1 and 20 batches."
        workshop_level = self.major_facility_level("workshop")
        if workshop_level < int(exchange["min_level"]):
            return False, f"{exchange['name']} requires Workshop Lv.{int(exchange['min_level'])}."
        input_id = str(exchange["input_id"]); output_id = str(exchange["output_id"])
        input_qty = int(exchange["input_qty"]) * batches
        output_qty = int(exchange["output_qty"]) * batches
        gil_fee = max(0, int(exchange.get("gil", 0))) * batches
        input_name = str(self.data.items.get(input_id, {}).get("name") or input_id.replace("_", " ").title())
        output_name = str(self.data.items.get(output_id, {}).get("name") or output_id.replace("_", " ").title())
        with self.db.tx() as conn:
            player = conn.execute("SELECT gil FROM players WHERE twitch_id=?", (str(player_id),)).fetchone()
            if not player:
                return False, "Recruit a Crystal Guild adventurer first."
            row = conn.execute("SELECT quantity FROM inventory WHERE player_id=? AND item_id=?", (str(player_id), input_id)).fetchone()
            owned = max(0, int(row["quantity"] or 0)) if row else 0
            if owned < input_qty:
                return False, f"{exchange['name']} needs {input_name} x{input_qty}; you have {owned}."
            if int(player["gil"] or 0) < gil_fee:
                return False, f"{exchange['name']} needs {gil_fee:,} Gil in service fees."
            conn.execute("UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?", (input_qty, str(player_id), input_id))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'item',?,?,'guild_workshop')", (str(player_id), input_id, -input_qty))
            if gil_fee:
                conn.execute("UPDATE players SET gil=gil-?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (gil_fee, str(player_id)))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,'guild_workshop')", (str(player_id), -gil_fee))
            conn.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (str(player_id), output_id, output_qty))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'item',?,?,'guild_workshop')", (str(player_id), output_id, output_qty))
            conn.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (?,'workshop_service',?,?)", (str(player_id), f"{exchange['name']}: {input_name} -> {output_name}", batches))
        return True, f"WORKSHOP — {input_name} x{input_qty} refined into {output_name} x{output_qty} for {gil_fee:,} Gil."

    def apply_jp_bonus(self, jp: int) -> int:
        bonus = self.effects()["jp_bonus"]
        return max(0, int(round(int(jp) * (1.0 + bonus))))

    def _member(self, player_id: str) -> Any:
        self.ensure_member(player_id)
        return self.db.one("SELECT * FROM fellowship_members WHERE player_id=?", (str(player_id),))

    def _settle_legacy_accomplishments(self) -> list[str]:
        notes: list[str] = []
        old_state = self._state()
        old_level = int(old_state["level"] if old_state else 1)
        bonus = 0
        with self.db.tx() as conn:
            metrics = legacy_metric_values(conn)
            for item in LEGACY_ACCOMPLISHMENTS:
                progress = int(metrics.get(str(item["metric"]), 0))
                if progress < int(item["target"]):
                    continue
                event_key = f"legacy_accomplishment:{item['id']}"
                inserted = conn.execute(
                    "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,NULL,'legacy_accomplishment',?,1)",
                    (event_key, int(item["renown"])),
                ).rowcount
                if not inserted:
                    continue
                reward = max(0, int(item["renown"]))
                bonus += reward
                notes.append(f"GUILD LEGACY — {item['name']} (+{reward} Fellowship Renown) · {item['trophy']} unlocked.")
                conn.execute(
                    "INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'legacy_accomplishment',?,?)",
                    (f"{item['name']} — {item['trophy']}", reward),
                )
            if bonus:
                conn.execute(
                    "UPDATE fellowship_state SET renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1",
                    (bonus,),
                )
        if bonus:
            state = self._state()
            new_level = fellowship_level_for_renown(int(state["renown"] if state else 0))
            if state and new_level != int(state["level"]):
                self.db.execute("UPDATE fellowship_state SET level=?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (new_level,))
            if new_level > old_level:
                notes.append(f"FELLOWSHIP LEVEL UP — LVL {new_level} reached!")
        return notes

    def legacy_snapshot(self) -> dict[str, Any]:
        with self.db.tx() as conn:
            return legacy_snapshot_from_connection(conn)

    def _personal_service_record(self, player_id: str) -> dict[str, Any]:
        rows = self.db.all(
            "SELECT activity,COALESCE(SUM(amount),0) AS amount FROM fellowship_events WHERE player_id=? GROUP BY activity",
            (str(player_id),),
        )
        totals = {str(row["activity"]): int(row["amount"] or 0) for row in rows}
        crew = self.db.one(
            "SELECT COUNT(DISTINCT run_id) AS n FROM fellowship_airship_mission_members WHERE player_id=?",
            (str(player_id),),
        )
        workshop = self.db.one(
            "SELECT COALESCE(SUM(amount),0) AS n FROM fellowship_activity WHERE player_id=? AND kind='workshop_service'",
            (str(player_id),),
        )
        return {
            "ventures_completed": int(totals.get("venture_complete", 0)),
            "hunts_won": int(totals.get("hunt_win", 0)),
            "raid_participations": int(totals.get("raid_participation", 0)),
            "expeditions_completed": int(totals.get("expedition_complete", 0)),
            "crafts_completed": int(totals.get("craft", 0)),
            "forge_upgrades": int(totals.get("forge", 0)),
            "airship_missions_supported": int(crew["n"] if crew else 0),
            "workshop_batches": int(workshop["n"] if workshop else 0),
        }

    def member_snapshot(self, player_id: str) -> dict[str, Any]:
        member = self._member(player_id)
        rank = guild_rank_for_renown(int(member["renown"]))
        service = self._personal_service_record(str(player_id))
        distinctions: list[str] = []
        if bool(member["founding_member"]): distinctions.append("Founding Member")
        if int(member["projects_contributed"]) >= 5: distinctions.append("Guild Builder")
        if int(member["gil_donated"]) >= 100_000: distinctions.append("Guild Benefactor")
        if int(member["orders_participated"]) >= 10: distinctions.append("Order Veteran")
        if int(member["deeds_assisted"]) >= 5: distinctions.append("Deedkeeper")
        if int(service["airship_missions_supported"]) >= 5: distinctions.append("Airship Crew")
        if int(service["expeditions_completed"]) >= 25: distinctions.append("Frontier Pathfinder")
        return {
            "renown": int(member["renown"]),
            "rank": rank,
            "founding_member": bool(member["founding_member"]),
            "projects_contributed": int(member["projects_contributed"]),
            "gil_donated": int(member["gil_donated"]),
            "materials_donated": int(member["materials_donated"]),
            "orders_participated": int(member["orders_participated"]),
            "deeds_assisted": int(member["deeds_assisted"]),
            "service_record": service,
            "distinctions": distinctions,
        }

    def _ensure_orders(self) -> tuple[str, list[dict[str, Any]]]:
        period = weekly_period_key()
        selected = weekly_orders(period)
        with self.db.tx() as conn:
            for order in selected:
                conn.execute(
                    "INSERT OR IGNORE INTO fellowship_orders(period_key,order_id,progress,target) VALUES (?,?,0,?)",
                    (period, order["id"], int(order["target"])),
                )
        return period, selected

    def orders_snapshot(self) -> dict[str, Any]:
        period, selected = self._ensure_orders()
        rows = {
            str(row["order_id"]): row
            for row in self.db.all(
                "SELECT * FROM fellowship_orders WHERE period_key=?",
                (period,),
            )
        }
        result = []
        for order in selected:
            row = rows[order["id"]]
            result.append({
                **order,
                "progress": int(row["progress"]),
                "target": int(row["target"]),
                "complete": bool(row["completed_at"]),
                "completed_at": row["completed_at"],
            })
        return {
            "period": period,
            "orders": result,
            "completed": sum(1 for item in result if item["complete"]),
            "total": len(result),
            "weekly_bonus": dict(WEEKLY_ORDER_SET_REWARD),
        }

    def deeds_snapshot(self) -> list[dict[str, Any]]:
        rows = {str(row["deed_id"]): row for row in self.db.all("SELECT * FROM fellowship_deeds")}
        result = []
        for deed in DEEDS:
            row = rows.get(deed["id"])
            progress = int(row["progress"]) if row else 0
            result.append({
                **deed,
                "progress": progress,
                "complete": bool(row and row["completed_at"]),
                "completed_at": row["completed_at"] if row else None,
            })
        return result

    def _project_current(self, project_id: str, key: str) -> int:
        row = self.db.one(
            "SELECT current FROM fellowship_project_progress WHERE project_id=? AND requirement_key=?",
            (project_id, key),
        )
        return int(row["current"]) if row else 0

    def project_snapshot(self, project_id: str | None = None) -> dict[str, Any] | None:
        state = self._state()
        project_id = project_id or (str(state["active_project_id"]) if state and state["active_project_id"] else None)
        if not project_id or project_id not in PROJECTS:
            return None
        project = PROJECTS[project_id]
        fellowship_level = int(state["level"] if state else 1)
        requirements = []
        complete = True
        for req in project["requirements"]:
            if req["kind"] == "level":
                current = fellowship_level
            else:
                current = self._project_current(project_id, req["key"])
            target = int(req["target"])
            is_complete = current >= target
            complete = complete and is_complete
            requirements.append({**req, "current": min(current, target), "complete": is_complete})
        return {**project, "requirements": requirements, "complete": complete}

    def available_projects(self) -> list[dict[str, Any]]:
        state = self._state()
        level = int(state["level"] if state else 1)
        tiers = self.facility_tiers()
        hall = int(tiers.get("guild_hall", 1))
        expedition_done = bool(state and state["expedition_board_complete"])
        result = []
        airship_state = self._airship_state()
        airship_built = bool(airship_state and int(airship_state["built"] or 0))
        airship_upgrades = self.airship_upgrades()
        for project in PROJECTS.values():
            # Legacy facilities remain readable/completable if already active,
            # while the public construction board exposes current major facilities
            # plus the smaller one-time Emporium Annex service building.
            if project.get("legacy"):
                continue
            if project.get("project_type") == "airship_construction":
                if airship_built or level < int(project.get("required_level", 1)):
                    continue
                if int(tiers.get("airship_dock", 0)) < int(project.get("required_dock_level", 1)):
                    continue
                result.append(self.project_snapshot(project["id"]) or dict(project))
                continue
            if project.get("project_type") == "airship_upgrade":
                if not airship_built or level < int(project.get("required_level", 1)):
                    continue
                upgrade_id = str(project.get("upgrade_id"))
                current_upgrade = int(airship_upgrades.get(upgrade_id, 0))
                if int(project.get("tier", 0)) != current_upgrade + 1:
                    continue
                if int(tiers.get("airship_dock", 0)) < int(project.get("required_dock_level", project.get("tier", 1))):
                    continue
                result.append(self.project_snapshot(project["id"]) or dict(project))
                continue
            if project.get("project_type") in {"supply_drive", "guild_objective"}:
                if level < int(project.get("required_level", 1)):
                    continue
                completed = self.db.one(
                    "SELECT 1 AS done FROM fellowship_events WHERE event_key=?",
                    (f"community_project_complete:{project['id']}",),
                )
                if completed:
                    continue
                result.append(self.project_snapshot(project["id"]) or dict(project))
                continue
            if project.get("teaser"):
                if expedition_done or hall < int(project.get("required_hall_tier", 5)) or level < int(project["required_level"]):
                    continue
            else:
                current = int(tiers.get(project["facility_id"], 0))
                if int(project["tier"]) != current + 1:
                    continue
                if project["facility_id"] == "airship_dock" and hall < int(project.get("required_hall_tier", 1)):
                    continue
                if project["facility_id"] != "guild_hall" and project["facility_id"] != "airship_dock" and int(project["tier"]) > hall:
                    continue
                if level < int(project["required_level"]):
                    continue
            result.append(self.project_snapshot(project["id"]) or dict(project))
        return sorted(result, key=lambda item: (int(item.get("tier", 0)), str(item.get("name", ""))))

    def set_active_project(self, query: str) -> tuple[bool, str, dict[str, Any] | None]:
        norm = str(query or "").strip().lower().replace(" ", "_").replace("-", "_")
        with self.db.tx() as conn:
            # Resolve availability while holding the Guild write lock. This
            # prevents a project selection based on facility/level state that
            # changed between validation and the actual switch.
            available = self.available_projects()
            match = next((p for p in available if p["id"] == norm), None)
            if not match:
                match = next((p for p in available if p.get("facility_id") == norm), None)
            if not match:
                match = next((p for p in available if str(p["name"]).lower() == str(query).strip().lower()), None)
            if not match:
                query_key = _project_query_key(query)
                for candidate in available:
                    facility = FACILITIES.get(str(candidate.get("facility_id") or ""), {})
                    aliases = (
                        candidate.get("id"),
                        candidate.get("facility_id"),
                        candidate.get("name"),
                        facility.get("name"),
                    )
                    if query_key and any(_project_query_key(alias) == query_key for alias in aliases if alias):
                        match = candidate
                        break
            if not match:
                # A short human label such as "Annex" or "Archive" is safe
                # when it identifies exactly one currently available project.
                query_key = _project_query_key(query)
                if len(query_key) >= 4:
                    partials = []
                    for candidate in available:
                        facility = FACILITIES.get(str(candidate.get("facility_id") or ""), {})
                        searchable = {
                            _project_query_key(candidate.get("name")),
                            _project_query_key(facility.get("name")),
                        }
                        if any(query_key in label for label in searchable if label):
                            partials.append(candidate)
                    if len(partials) == 1:
                        match = partials[0]
            if not match:
                # Compatibility lane for v1.2 support-facility steps.
                state = conn.execute("SELECT level FROM fellowship_state WHERE singleton_id=1").fetchone()
                level = int(state["level"] if state else 1)
                tiers = {
                    str(row["facility_id"]): int(row["tier"])
                    for row in conn.execute("SELECT facility_id,tier FROM fellowship_facilities").fetchall()
                }
                legacy = [
                    project for project in PROJECTS.values()
                    if project.get("legacy")
                    and project.get("facility_id") == norm
                    and int(project.get("tier", 0)) == int(tiers.get(norm, 0)) + 1
                    and level >= int(project.get("required_level", 1))
                ]
                if legacy:
                    match = self.project_snapshot(legacy[0]["id"]) or legacy[0]
            if not match:
                names = ", ".join(p["name"] for p in available[:6]) or "none currently unlocked"
                return False, f"Project unavailable. Unlocked projects: {names}.", None

            project_id = match["id"]
            current = conn.execute(
                "SELECT active_project_id FROM fellowship_state WHERE singleton_id=1"
            ).fetchone()
            if current and str(current["active_project_id"] or "") == project_id:
                return True, f"ACTIVE PROJECT — {PROJECTS[project_id]['name']} is already selected.", self.project_snapshot(project_id)

            conn.execute(
                "UPDATE fellowship_state SET active_project_id=?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1",
                (project_id,),
            )
            for req in PROJECTS[project_id]["requirements"]:
                if req["kind"] != "level":
                    conn.execute(
                        "INSERT OR IGNORE INTO fellowship_project_progress(project_id,requirement_key,current) VALUES (?,?,0)",
                        (project_id, req["key"]),
                    )
            conn.execute(
                "INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'project_selected',?,0)",
                (PROJECTS[project_id]["name"],),
            )
            snapshot = self.project_snapshot(project_id)
        return True, f"ACTIVE PROJECT — {PROJECTS[project_id]['name']} selected.", snapshot

    def contribute(
        self,
        player_id: str,
        raw: str,
        *,
        expected_project_id: str | None = None,
    ) -> tuple[bool, str, list[str]]:
        text = str(raw or "").strip()
        parts = text.split()
        if len(parts) < 2:
            return False, "Use !contribute gil <amount> or !contribute <amount> <item>.", []

        kind = "item"
        asset_id = ""
        if parts[0].lower() == "gil":
            kind = "gil"
            try:
                amount = int(parts[1].replace(",", ""))
            except ValueError:
                return False, "Gil contribution must be a whole number.", []
            asset_id = "gil"
        else:
            try:
                amount = int(parts[0].replace(",", ""))
            except ValueError:
                return False, "Use !contribute gil <amount> or !contribute <amount> <item>.", []
            item_query = " ".join(parts[1:]).strip().lower()
            item = next((item for item in self.data.items.values() if item["id"] == item_query.replace(" ", "_")), None)
            if not item:
                item = next((item for item in self.data.items.values() if str(item["name"]).lower() == item_query), None)
            if not item:
                return False, "That item is not recognized by the Fellowship quartermaster.", []
            asset_id = item["id"]
        if amount <= 0:
            return False, "Contribution amount must be at least 1.", []

        with self.db.tx() as conn:
            player = conn.execute(
                "SELECT display_name,gil FROM players WHERE twitch_id=?",
                (str(player_id),),
            ).fetchone()
            if not player:
                return False, "Recruit a hero before contributing to the Fellowship.", []

            project = self.project_snapshot()
            if not project:
                return False, "The Fellowship has no active project. The streamer can choose one with !fellowshipproject.", []
            if expected_project_id and str(project["id"]) != str(expected_project_id):
                return False, "The active Guild project changed before your contribution was processed. Refresh Fellowship and try again.", []

            key = "gil" if kind == "gil" else f"item:{asset_id}"
            requirement = next((req for req in project["requirements"] if req["key"] == key), None)
            if not requirement:
                return False, f"{project['name']} does not currently need that resource.", []

            # Recompute the remaining requirement only after taking the Guild
            # write lock. Simultaneous contributors can never overfill a goal
            # or have resources deducted beyond what the project still needs.
            current_row = conn.execute(
                "SELECT current FROM fellowship_project_progress WHERE project_id=? AND requirement_key=?",
                (project["id"], key),
            ).fetchone()
            current = int(current_row["current"]) if current_row else 0
            remaining = max(0, int(requirement["target"]) - current)
            if remaining <= 0:
                return False, f"That requirement for {project['name']} is already complete.", []
            accepted = min(amount, remaining)

            conn.execute(
                "INSERT OR IGNORE INTO fellowship_members(player_id) VALUES (?)",
                (str(player_id),),
            )
            if kind == "gil":
                live = conn.execute("SELECT gil FROM players WHERE twitch_id=?", (str(player_id),)).fetchone()
                if not live or int(live["gil"]) < accepted:
                    return False, f"You need {accepted:,} Gil to make that contribution.", []
                conn.execute(
                    "UPDATE players SET gil=gil-?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
                    (accepted, str(player_id)),
                )
                conn.execute(
                    "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,?)",
                    (str(player_id), -accepted, f"fellowship:{project['id']}"),
                )
                conn.execute(
                    "UPDATE fellowship_members SET gil_donated=gil_donated+?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
                    (accepted, str(player_id)),
                )
                renown = max(1, min(40, accepted // 250))
                label = f"{accepted:,} Gil"
            else:
                row = conn.execute(
                    "SELECT quantity FROM inventory WHERE player_id=? AND item_id=?",
                    (str(player_id), asset_id),
                ).fetchone()
                if not row or int(row["quantity"]) < accepted:
                    return False, f"You need {accepted} {self.data.items[asset_id]['name']} to make that contribution.", []
                conn.execute(
                    "UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?",
                    (accepted, str(player_id), asset_id),
                )
                conn.execute(
                    "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'item',?,?,?)",
                    (str(player_id), asset_id, -accepted, f"fellowship:{project['id']}"),
                )
                conn.execute(
                    "UPDATE fellowship_members SET materials_donated=materials_donated+?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
                    (accepted, str(player_id)),
                )
                renown = min(40, accepted * 2)
                label = f"{self.data.items[asset_id]['name']} x{accepted}"

            conn.execute(
                "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES (?,?,?) "
                "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=fellowship_project_progress.current+excluded.current",
                (project["id"], key, accepted),
            )
            conn.execute(
                "INSERT INTO fellowship_contributions(player_id,project_id,kind,asset_id,amount) VALUES (?,?,?,?,?)",
                (str(player_id), project["id"], kind, asset_id, accepted),
            )
            conn.execute(
                "INSERT OR IGNORE INTO fellowship_project_members(project_id,player_id) VALUES (?,?)",
                (project["id"], str(player_id)),
            )
            conn.execute(
                "INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (?,'contribution',?,?)",
                (str(player_id), f"{player['display_name']} contributed {label} to {project['name']}", accepted),
            )

            # Award contribution Renown and settle any newly completed project
            # before releasing the outer transaction. Project selection cannot
            # race between the final contribution and the completion upgrade.
            notes = self._award_renown(
                str(player_id),
                renown,
                f"contribution:{time.time_ns()}:{player_id}",
                "contribution",
                1,
                progress_activity=False,
            )

            message = f"FELLOWSHIP CONTRIBUTION — {player['display_name']} contributed {label} to {project['name']}."
            if accepted < amount:
                message += f" Only {accepted:,} was needed; the excess stayed with you."
            return True, message, notes

    def record_activity(
        self,
        player_id: str,
        activity: str,
        *,
        amount: int = 1,
        event_key: str | None = None,
        renown: int | None = None,
    ) -> list[str]:
        amount = max(1, int(amount))
        event_key = event_key or f"{activity}:{player_id}:{time.time_ns()}"
        base = ACTIVITY_RENOWN.get(activity, 0) if renown is None else int(renown)
        personal_renown = max(0, base * amount if activity in {"craft"} else base)
        return self._award_renown(str(player_id), personal_renown, event_key, activity, amount, progress_activity=True)

    def record_shared_activity(
        self,
        activity: str,
        *,
        amount: int = 1,
        event_key: str | None = None,
        renown: int = 0,
    ) -> list[str]:
        """Record one Guild-wide activity event rather than one event per participant.

        Event insertion, shared progress, project completion, level changes and
        rewards remain inside one serialized transaction so another Guild
        action cannot switch projects during finalization.
        """
        amount = max(1, int(amount))
        event_key = event_key or f"shared:{activity}:{time.time_ns()}"
        with self.db.tx() as conn:
            state = conn.execute("SELECT level FROM fellowship_state WHERE singleton_id=1").fetchone()
            old_level = int(state["level"] if state else 1)
            inserted = conn.execute(
                "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,NULL,?,?,?)",
                (str(event_key), str(activity), int(renown), int(amount)),
            ).rowcount
            if not inserted:
                return []
            if renown:
                conn.execute(
                    "UPDATE fellowship_state SET renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1",
                    (int(renown),),
                )
            self._progress_project_activity(conn, None, activity, amount)
            self._progress_orders(conn, None, activity, amount)
            self._progress_deeds(conn, None, activity, amount)
            self._progress_airship_mission(conn, None, activity, amount)
            return self._finalize_progress(None, old_level, None)

    def _award_renown(
        self,
        player_id: str | None,
        renown: int,
        event_key: str,
        activity: str,
        amount: int,
        *,
        progress_activity: bool,
    ) -> list[str]:
        # The event, Guild/member Renown, activity progress, project completion,
        # Weekly Orders/Deeds, level/rank changes and Legacy settlement all live
        # beneath one outer transaction. This prevents a concurrent project
        # switch from splitting "goal reached" and "project completed" into two
        # independently visible states.
        with self.db.tx() as conn:
            state = conn.execute("SELECT level FROM fellowship_state WHERE singleton_id=1").fetchone()
            old_level = int(state["level"] if state else 1)
            old_rank = None
            if player_id:
                conn.execute("INSERT OR IGNORE INTO fellowship_members(player_id) VALUES (?)", (player_id,))
                member = conn.execute("SELECT renown FROM fellowship_members WHERE player_id=?", (player_id,)).fetchone()
                old_rank = guild_rank_for_renown(int(member["renown"] if member else 0))

            inserted = conn.execute(
                "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,?,?,?,?)",
                (str(event_key), player_id, str(activity), int(renown), int(amount)),
            ).rowcount
            if not inserted:
                return []
            if player_id and renown:
                conn.execute(
                    "UPDATE fellowship_members SET renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
                    (int(renown), player_id),
                )
            if renown:
                conn.execute(
                    "UPDATE fellowship_state SET renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1",
                    (int(renown),),
                )
            if progress_activity:
                self._progress_project_activity(conn, player_id, activity, amount)
                self._progress_orders(conn, player_id, activity, amount)
                self._progress_deeds(conn, player_id, activity, amount)
                self._progress_airship_mission(conn, player_id, activity, amount)
                # Must remain after the freshly inserted fellowship_events receipt
                # and inside the same transaction as Guild progress and rewards.
                if player_id:
                    initiative_notes = progress_event(conn, self.data, player_id, self._activity_semantics(activity), amount, timestamp=time.time())
                else:
                    initiative_notes = []
            else:
                initiative_notes = []
            return [*self._finalize_progress(player_id, old_level, old_rank), *initiative_notes]

    def _progress_project_activity(self, conn: Any, player_id: str | None, activity: str, amount: int) -> None:
        state = conn.execute("SELECT active_project_id FROM fellowship_state WHERE singleton_id=1").fetchone()
        project_id = str(state["active_project_id"]) if state and state["active_project_id"] else ""
        project = PROJECTS.get(project_id)
        if not project:
            return
        accepted_activities = self._activity_semantics(activity)
        for candidate in accepted_activities:
            key = f"activity:{candidate}"
            req = next((req for req in project["requirements"] if req["key"] == key), None)
            if not req:
                continue
            current = conn.execute(
                "SELECT current FROM fellowship_project_progress WHERE project_id=? AND requirement_key=?",
                (project_id, key),
            ).fetchone()
            before = int(current["current"]) if current else 0
            add = max(0, min(int(amount), int(req["target"]) - before))
            if add:
                conn.execute(
                    "INSERT INTO fellowship_project_progress(project_id,requirement_key,current) VALUES (?,?,?) "
                    "ON CONFLICT(project_id,requirement_key) DO UPDATE SET current=fellowship_project_progress.current+excluded.current",
                    (project_id, key, add),
                )
                if player_id:
                    conn.execute("INSERT OR IGNORE INTO fellowship_project_members(project_id,player_id) VALUES (?,?)", (project_id, player_id))

    @classmethod
    def _activity_matches(cls, order_activity: str, activity: str) -> bool:
        if order_activity in cls._activity_semantics(activity):
            return True
        if order_activity == "craft_forge" and activity in {"craft", "forge"}:
            return True
        return False

    def _progress_orders(self, conn: Any, player_id: str | None, activity: str, amount: int) -> None:
        period, selected = self._ensure_orders()
        for order in selected:
            if not self._activity_matches(order["activity"], activity):
                continue
            row = conn.execute(
                "SELECT progress,target,completed_at FROM fellowship_orders WHERE period_key=? AND order_id=?",
                (period, order["id"]),
            ).fetchone()
            if not row or row["completed_at"]:
                continue
            add = max(0, min(int(amount), int(row["target"]) - int(row["progress"])))
            if add:
                conn.execute(
                    "UPDATE fellowship_orders SET progress=progress+? WHERE period_key=? AND order_id=?",
                    (add, period, order["id"]),
                )
                if player_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO fellowship_order_members(period_key,order_id,player_id) VALUES (?,?,?)",
                        (period, order["id"], player_id),
                    )

    def _progress_deeds(self, conn: Any, player_id: str | None, activity: str, amount: int) -> None:
        for deed in DEEDS:
            if not self._activity_matches(str(deed["activity"]), activity):
                continue
            row = conn.execute("SELECT progress,target,completed_at FROM fellowship_deeds WHERE deed_id=?", (deed["id"],)).fetchone()
            if not row or row["completed_at"]:
                continue
            add = max(0, min(int(amount), int(row["target"]) - int(row["progress"])))
            if add:
                conn.execute("UPDATE fellowship_deeds SET progress=progress+? WHERE deed_id=?", (add, deed["id"]))
                if player_id:
                    conn.execute("INSERT OR IGNORE INTO fellowship_deed_members(deed_id,player_id) VALUES (?,?)", (deed["id"], player_id))

    def _award_order_participant(
        self, conn: Any, *, period: str, order: dict[str, Any], participant_id: str
    ) -> bool:
        event_key = f"order_participant_reward:{period}:{order['id']}:{participant_id}"
        inserted = conn.execute(
            "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,?,'order_participant_reward',0,1)",
            (event_key, str(participant_id)),
        ).rowcount
        if not inserted:
            return False
        gil = max(0, int(order.get("personal_gil", 0)))
        renown = max(0, int(order.get("personal_renown", 0)))
        if gil:
            conn.execute("UPDATE players SET gil=gil+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (gil, str(participant_id)))
            conn.execute(
                "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,'fellowship_order_reward')",
                (str(participant_id), gil),
            )
        if renown:
            conn.execute(
                "UPDATE fellowship_members SET renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
                (renown, str(participant_id)),
            )
        return True

    def _award_weekly_order_participant(self, conn: Any, *, period: str, participant_id: str) -> bool:
        event_key = f"weekly_order_participant_reward:{period}:{participant_id}"
        inserted = conn.execute(
            "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,?,'weekly_order_participant_reward',0,1)",
            (event_key, str(participant_id)),
        ).rowcount
        if not inserted:
            return False
        gil = max(0, int(WEEKLY_ORDER_SET_REWARD.get("personal_gil", 0)))
        renown = max(0, int(WEEKLY_ORDER_SET_REWARD.get("personal_renown", 0)))
        if gil:
            conn.execute("UPDATE players SET gil=gil+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (gil, str(participant_id)))
            conn.execute(
                "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,'fellowship_orders_week_reward')",
                (str(participant_id), gil),
            )
        if renown:
            conn.execute(
                "UPDATE fellowship_members SET renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
                (renown, str(participant_id)),
            )
        return True

    def _finalize_progress(self, player_id: str | None, old_level: int, old_rank: dict[str, Any] | None) -> list[str]:
        notes: list[str] = []
        # Order/deed completion bonuses are shared Guild Renown; they do not
        # multiply the personal rank of the player who happened to land the final point.
        bonus = 0
        with self.db.tx() as conn:
            period, selected = self._ensure_orders()
            for order in selected:
                row = conn.execute("SELECT progress,target,completed_at FROM fellowship_orders WHERE period_key=? AND order_id=?", (period, order["id"])).fetchone()
                if row and not row["completed_at"] and int(row["progress"]) >= int(row["target"]):
                    conn.execute("UPDATE fellowship_orders SET completed_at=CURRENT_TIMESTAMP WHERE period_key=? AND order_id=?", (period, order["id"]))
                    bonus += int(order["renown"])
                    notes.append(f"ORDER COMPLETE — {order['name']} (+{order['renown']} Fellowship Renown)")
                    conn.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'order_complete',?,?)", (order["name"], int(order["renown"])))
                    participants = conn.execute("SELECT player_id FROM fellowship_order_members WHERE period_key=? AND order_id=?", (period, order["id"])).fetchall()
                    rewarded = 0
                    for rowp in participants:
                        participant_id = str(rowp["player_id"])
                        conn.execute("UPDATE fellowship_members SET orders_participated=orders_participated+1 WHERE player_id=?", (participant_id,))
                        if self._award_order_participant(conn, period=period, order=order, participant_id=participant_id):
                            rewarded += 1
                    if rewarded:
                        notes.append(
                            f"ORDER PARTICIPATION — {rewarded} contributor{'s' if rewarded != 1 else ''} received "
                            f"{int(order.get('personal_gil', 0)):,}g +{int(order.get('personal_renown', 0))} personal Renown."
                        )
            completed_orders = conn.execute("SELECT COUNT(*) AS n FROM fellowship_orders WHERE period_key=? AND completed_at IS NOT NULL", (period,)).fetchone()
            if int(completed_orders["n"] if completed_orders else 0) >= len(selected):
                event_key = f"weekly_orders_complete:{period}"
                guild_bonus = int(WEEKLY_ORDER_SET_REWARD.get("guild_renown", 500))
                inserted = conn.execute(
                    "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,NULL,'weekly_orders_complete',?,1)",
                    (event_key, guild_bonus),
                ).rowcount
                if inserted:
                    bonus += guild_bonus
                    notes.append(f"WEEKLY ORDERS COMPLETE — all Fellowship Orders finished (+{guild_bonus} Renown)")
                    conn.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'orders_week_complete','Weekly Orders complete',?)", (guild_bonus,))
                    weekly_participants = conn.execute(
                        "SELECT DISTINCT player_id FROM fellowship_order_members WHERE period_key=?",
                        (period,),
                    ).fetchall()
                    rewarded = sum(
                        1 for rowp in weekly_participants
                        if self._award_weekly_order_participant(conn, period=period, participant_id=str(rowp["player_id"]))
                    )
                    if rewarded:
                        notes.append(
                            f"WEEKLY PARTICIPATION BONUS — {rewarded} contributor{'s' if rewarded != 1 else ''} received "
                            f"{int(WEEKLY_ORDER_SET_REWARD.get('personal_gil', 0)):,}g +{int(WEEKLY_ORDER_SET_REWARD.get('personal_renown', 0))} personal Renown."
                        )
            for deed in DEEDS:
                row = conn.execute("SELECT progress,target,completed_at FROM fellowship_deeds WHERE deed_id=?", (deed["id"],)).fetchone()
                if row and not row["completed_at"] and int(row["progress"]) >= int(row["target"]):
                    conn.execute("UPDATE fellowship_deeds SET completed_at=CURRENT_TIMESTAMP WHERE deed_id=?", (deed["id"],))
                    bonus += int(deed["renown"])
                    notes.append(f"FELLOWSHIP DEED — {deed['name']} (+{deed['renown']} Renown)")
                    conn.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'deed_complete',?,?)", (deed["name"], int(deed["renown"])))
                    participants = conn.execute("SELECT player_id FROM fellowship_deed_members WHERE deed_id=?", (deed["id"],)).fetchall()
                    for rowp in participants:
                        conn.execute("UPDATE fellowship_members SET deeds_assisted=deeds_assisted+1 WHERE player_id=?", (rowp["player_id"],))
            if bonus:
                conn.execute("UPDATE fellowship_state SET renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (bonus,))
        # Renown can unlock a level-gated project requirement, so synchronize
        # the shared level before checking project completion. A completed
        # project can then award another Renown bonus; synchronize once more.
        state = self._state()
        interim_level = fellowship_level_for_renown(int(state["renown"]))
        if interim_level != int(state["level"]):
            self.db.execute("UPDATE fellowship_state SET level=?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (interim_level,))
        notes.extend(self._check_project_completion(player_id))
        state = self._state()
        new_level = fellowship_level_for_renown(int(state["renown"]))
        if new_level != int(state["level"]):
            self.db.execute("UPDATE fellowship_state SET level=?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (new_level,))
        if new_level > old_level:
            notes.append(f"FELLOWSHIP LEVEL UP — LVL {new_level} reached!")
            self.db.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'level_up',?,?)", (f"Fellowship LVL {new_level}", new_level))
        if player_id and old_rank is not None:
            new_rank = guild_rank_for_renown(int(self._member(player_id)["renown"]))
            if int(new_rank["index"]) > int(old_rank["index"]):
                notes.append(f"GUILD RANK UP — {new_rank['name']}")
                display = self.db.one("SELECT display_name FROM players WHERE twitch_id=?", (player_id,))
                self.db.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (?,'rank_up',?,?)", (player_id, f"{display['display_name'] if display else player_id} reached {new_rank['name']}", int(new_rank["index"])))
        notes.extend(self._settle_legacy_accomplishments())
        return notes

    def _check_project_completion(self, triggering_player_id: str | None) -> list[str]:
        project = self.project_snapshot()
        if not project or not project["complete"]:
            return []
        project_id = project["id"]
        notes = [f"PROJECT COMPLETE — {project['name']}"]
        bonus = 250 * max(1, int(project.get("tier", 1)))
        with self.db.tx() as conn:
            if project.get("project_type") == "airship_construction":
                bonus = int(project.get("reward_renown", 1500))
                inserted = conn.execute(
                    "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,NULL,'airship_built',0,1)",
                    ("airship_built:crystal_guild_airship",),
                ).rowcount
                if not inserted:
                    conn.execute("UPDATE fellowship_state SET active_project_id=NULL,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1")
                    return []
                conn.execute("UPDATE fellowship_airship_state SET built=1,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1")
                conn.execute("UPDATE fellowship_state SET active_project_id=NULL,renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (bonus,))
                notes[0] = f"AIRSHIP COMPLETE — Crystal Guild Airship (+{bonus} Fellowship Renown)"
                notes.append("Guild-scale Airship Missions are now available.")
            elif project.get("project_type") == "airship_upgrade":
                upgrade_id = str(project.get("upgrade_id"))
                tier = int(project.get("tier", 1))
                bonus = int(project.get("reward_renown", 300 * tier))
                inserted = conn.execute(
                    "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,NULL,'airship_upgrade',0,1)",
                    (f"airship_upgrade:{upgrade_id}:{tier}",),
                ).rowcount
                if not inserted:
                    conn.execute("UPDATE fellowship_state SET active_project_id=NULL,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1")
                    return []
                conn.execute(
                    "UPDATE fellowship_airship_upgrades SET tier=?,updated_at=CURRENT_TIMESTAMP WHERE upgrade_id=?",
                    (tier, upgrade_id),
                )
                conn.execute("UPDATE fellowship_state SET active_project_id=NULL,renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (bonus,))
                notes[0] = f"AIRSHIP UPGRADE COMPLETE — {AIRSHIP_UPGRADES[upgrade_id]['name']} Tier {tier} (+{bonus} Fellowship Renown)"
            elif project.get("project_type") in {"supply_drive", "guild_objective"}:
                bonus = int(project.get("reward_renown", 300))
                inserted = conn.execute(
                    "INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,NULL,'community_project_complete',0,1)",
                    (f"community_project_complete:{project_id}",),
                ).rowcount
                if not inserted:
                    conn.execute("UPDATE fellowship_state SET active_project_id=NULL,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1")
                    return []
                conn.execute(
                    "UPDATE fellowship_state SET active_project_id=NULL,renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1",
                    (bonus,),
                )
                label = "SUPPLY DRIVE COMPLETE" if project.get("project_type") == "supply_drive" else "GUILD OBJECTIVE COMPLETE"
                notes[0] = f"{label} — {project['name']} (+{bonus} Fellowship Renown)"
            elif project.get("teaser"):
                conn.execute("UPDATE fellowship_state SET active_project_id=NULL,expedition_board_complete=1,renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (bonus,))
                notes.append("The Expedition Board is ready. Distant contracts are now open Guild-wide.")
            else:
                conn.execute("UPDATE fellowship_facilities SET tier=?,updated_at=CURRENT_TIMESTAMP WHERE facility_id=?", (int(project["tier"]), project["facility_id"]))
                conn.execute("UPDATE fellowship_state SET active_project_id=NULL,renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (bonus,))
                benefit = FACILITIES[project["facility_id"]]["benefits"][int(project["tier"]) - 1]
                if project["facility_id"] == "emporium_annex":
                    notes.append(f"Moogle Emporium Annex constructed — {benefit}.")
                elif project["facility_id"] == "trading_post":
                    notes.append(f"Moogle Trading Post constructed — {benefit}.")
                else:
                    notes.append(f"{FACILITIES[project['facility_id']]['name']} Tier {project['tier']} unlocked — {benefit}.")
            conn.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'project_complete',?,?)", (project["name"], bonus))
            participants = conn.execute("SELECT player_id FROM fellowship_project_members WHERE project_id=?", (project_id,)).fetchall()
            for row in participants:
                player_id = str(row["player_id"])
                conn.execute("UPDATE fellowship_members SET projects_contributed=projects_contributed+1 WHERE player_id=?", (player_id,))
                reconcile_player_trophies(conn, player_id, source=f"fellowship:{project_id}")
            # Progress project-completion Orders/Deeds even though the project has
            # already been cleared from active state.
            self._progress_orders(conn, triggering_player_id, "project_complete", 1)
            self._progress_deeds(conn, triggering_player_id, "project_complete", 1)
        return notes

    def public_snapshot(self) -> dict[str, Any]:
        state = self._state()
        renown = int(state["renown"] if state else 0)
        level_progress = fellowship_level_progress(renown)
        tiers = self.facility_tiers()
        facilities = []
        for facility_id in PUBLIC_GUILD_FACILITY_IDS:
            config = FACILITIES[facility_id]
            raw_tier = int(tiers.get(facility_id, 0))
            max_level = int(config.get("max_level", 3))
            level = min(max(0, raw_tier), max_level)
            level_benefits = list(config.get("level_benefits") or config.get("benefits") or [])
            future_locked = bool(config.get("future_locked"))
            current_benefit = (
                level_benefits[level - 1]
                if level > 0 and level <= len(level_benefits)
                else ("Construction plans are posted, but building has not started." if not future_locked else "Airship construction is not open yet.")
            )
            next_benefit = None
            if future_locked:
                next_benefit = "The Airship Dock will become a major Fellowship construction project in a later Guild Expansion phase."
            elif level < max_level and level < len(level_benefits):
                next_benefit = level_benefits[level]
            facilities.append({
                "id": facility_id,
                "name": config["name"],
                "level": level,
                "max_level": max_level,
                # Keep tier fields for older Web clients during rolling deploys.
                "tier": level,
                "max_tier": max_level,
                "description": config["description"],
                "current_benefit": current_benefit,
                "next_benefit": next_benefit,
                "locked": future_locked,
                "status": "Future Construction" if future_locked else ("Complete" if level >= max_level else "Buildable"),
            })
        members = []
        rows = self.db.all(
            "SELECT fm.*,p.username,p.display_name,p.level FROM fellowship_members fm JOIN players p ON p.twitch_id=fm.player_id ORDER BY fm.renown DESC,p.level DESC,lower(p.display_name) ASC LIMIT 12"
        )
        for row in rows:
            rank = guild_rank_for_renown(int(row["renown"]))
            members.append({
                "username": row["username"],
                "display_name": row["display_name"],
                "level": int(row["level"]),
                "renown": int(row["renown"]),
                "rank": rank["name"],
                "founding_member": bool(row["founding_member"]),
            })
        activity_rows = self.db.all(
            "SELECT fa.*,p.username,p.display_name FROM fellowship_activity fa LEFT JOIN players p ON p.twitch_id=fa.player_id ORDER BY fa.id DESC LIMIT 16"
        )
        activity = [
            {
                "kind": row["kind"],
                "label": row["label"],
                "amount": int(row["amount"]),
                "username": row["username"],
                "display_name": row["display_name"],
                "created_at": row["created_at"],
            }
            for row in activity_rows
        ]
        member_count = self.db.one("SELECT COUNT(*) AS n FROM fellowship_members")
        contribution = self.db.one("SELECT COALESCE(SUM(gil_donated),0) AS gil,COALESCE(SUM(materials_donated),0) AS materials FROM fellowship_members")
        deeds = self.deeds_snapshot()
        return {
            "level": int(state["level"] if state else 1),
            "level_label": f"LVL {int(state['level'] if state else 1)}",
            "renown": renown,
            "level_progress": level_progress,
            "member_count": int(member_count["n"] if member_count else 0),
            "active_project": self.project_snapshot(),
            "available_projects": self.available_projects(),
            "guild_board": {
                "facility_count": len(facilities),
                "built_count": sum(1 for facility in facilities if int(facility["level"]) > 0),
                "complete_count": sum(1 for facility in facilities if not facility["locked"] and int(facility["level"]) >= int(facility["max_level"])),
                "airship_dock_locked": False,
            },
            "facilities": facilities,
            "orders": self.orders_snapshot(),
            "deeds": deeds,
            "deeds_complete": sum(1 for deed in deeds if deed["complete"]),
            "leaders": members,
            "recent_activity": activity,
            "totals": {
                "gil_donated": int(contribution["gil"] if contribution else 0),
                "materials_donated": int(contribution["materials"] if contribution else 0),
            },
            "expedition_board_complete": bool(state and state["expedition_board_complete"]),
            "rank_ladder": GUILD_RANKS,
            "effects": self.effects(),
            "services": self.workshop_services_snapshot(),
            "airship": self.airship_snapshot(),
            "legacy": self.legacy_snapshot(),
        }

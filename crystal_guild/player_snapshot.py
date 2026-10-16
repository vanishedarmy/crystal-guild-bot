from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import unquote

from .active_battle import FULL_RESOURCE_SENTINEL, battle_resource_pools, job_resource_mode
from .balance import jp_to_next, sell_value, xp_to_next
from .chocobo import DEFAULT_PORTRAIT_ID as CHOCOBO_DEFAULT_PORTRAIT_ID, PORTRAITS as CHOCOBO_PORTRAITS, TRAITS as CHOCOBO_TRAITS, level_from_total_xp as chocobo_level_from_total_xp, expedition_specialization as chocobo_expedition_specialization
from .emporium import guild_commerce
from .data import GameData
from .bestiary_progress import progress_for
from .gold_saucer import gold_saucer_record_value
from .personal_records import project_personal_records
from .guild_initiatives import contract_view, board_view
from .moments import public_moments_view
from .trophies import TROPHY_CATALOG, TROPHIES_BY_ID
from .fellowship import (AIRSHIP_MISSIONS, AIRSHIP_UPGRADES, DEEDS, FACILITIES, GUILD_EXPANSION_FACILITY_IDS, PUBLIC_GUILD_FACILITY_IDS, GUILD_RANKS, PROJECTS, WEEKLY_ORDER_SET_REWARD, facility_effects, fellowship_level_progress, guild_rank_for_renown, legacy_snapshot_from_connection, weekly_orders, weekly_period_key)


SNAPSHOT_VERSION = "1.9.7-queens-blood"


class PortalRepository:
    """Read-only view of Crystal Guild player data for the web portal."""

    def __init__(self, database_path: str | Path, data_dir: str | Path):
        self.database_path = Path(database_path).resolve()
        self.data = GameData(data_dir)
        self.data.validate_or_raise()
        self._forge_bonus = float(self.data.forge[0].get("bonus_per_level", 0.08)) if self.data.forge else 0.08
        self._conn_lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None

    def _open_connection(self) -> sqlite3.Connection:
        if not self.database_path.exists():
            raise FileNotFoundError(self.database_path)
        uri = f"file:{self.database_path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=5.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA cache_size = -8192")
        return conn

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        with self._conn_lock:
            if self._conn is None:
                self._conn = self._open_connection()
            try:
                yield self._conn
            except sqlite3.Error:
                try:
                    self._conn.close()
                finally:
                    self._conn = None
                raise

    @contextmanager
    def consistent_read(self) -> Iterator[None]:
        """Hold one SQLite read snapshot across a multi-module portal export."""
        with self.connect() as conn:
            started = not conn.in_transaction
            if started:
                conn.execute("BEGIN")
            try:
                yield
            finally:
                if started and conn.in_transaction:
                    conn.rollback()

    def close(self) -> None:
        with self._conn_lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def health(self) -> dict[str, Any]:
        try:
            with self.connect() as conn:
                row = conn.execute("SELECT COUNT(*) AS n FROM players").fetchone()
            return {
                "ok": True,
                "version": SNAPSHOT_VERSION,
                "players": int(row["n"]),
                "database": self.database_path.name,
            }
        except Exception as exc:
            return {
                "ok": False,
                "version": SNAPSHOT_VERSION,
                "players": 0,
                "database": self.database_path.name,
                "error": str(exc),
            }

    def twitch_id_for(self, username: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT twitch_id FROM players WHERE lower(username)=lower(?) LIMIT 1",
                (str(username).strip(),),
            ).fetchone()
        return str(row["twitch_id"]) if row else None

    def list_players(self, search: str = "") -> list[dict[str, Any]]:
        with self.connect() as conn:
            params: tuple[Any, ...] = ()
            where = ""
            if search.strip():
                term = f"%{search.strip().lower()}%"
                where = "WHERE lower(username) LIKE ? OR lower(display_name) LIKE ?"
                params = (term, term)
            rows = conn.execute(
                f"""
                SELECT twitch_id, username, display_name, level, current_job,
                       title, current_hp, camp_until, updated_at, created_at
                FROM players
                {where}
                ORDER BY level DESC, lower(display_name) ASC
                """,
                params,
            ).fetchall()
            result = []
            for row in rows:
                current_job = self.data.jobs.get(row["current_job"])
                job_name = current_job["name"] if current_job else "Adventurer"
                status = self._status(row)
                result.append(
                    {
                        "username": row["username"],
                        "display_name": row["display_name"],
                        "level": int(row["level"]),
                        "job_id": row["current_job"],
                        "job_name": job_name,
                        "title": row["title"],
                        "status": status["state"],
                        "status_label": status["label"],
                        "updated_at": row["updated_at"],
                        "created_at": row["created_at"],
                    }
                )
            return result

    def _resource_state(
        self,
        conn: sqlite3.Connection,
        player_id: str,
        stats: dict[str, int],
        job: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Return current/max MP/AP, using live runtime combat state when present."""
        pools = battle_resource_pools(stats, job)
        try:
            persisted = conn.execute(
                "SELECT current_mp, current_ap FROM players WHERE twitch_id=?",
                (str(player_id),),
            ).fetchone()
        except sqlite3.Error:
            # Upgrade-order compatibility: Portal sync can safely read a legacy
            # schema-1 Guild before the Bot/maintenance command performs the
            # additive local schema-2 migration. Legacy resources display full.
            persisted = None
        max_mp = int(pools["max_mp"])
        max_ap = int(pools["max_ap"])
        raw_mp = persisted["current_mp"] if persisted else None
        raw_ap = persisted["current_ap"] if persisted else None
        current_mp = 0 if max_mp <= 0 else (max_mp if raw_mp is None or int(raw_mp) == FULL_RESOURCE_SENTINEL else max(0, min(max_mp, int(raw_mp))))
        current_ap = 0 if max_ap <= 0 else (max_ap if raw_ap is None or int(raw_ap) == FULL_RESOURCE_SENTINEL else max(0, min(max_ap, int(raw_ap))))
        live = False
        try:
            row = conn.execute(
                "SELECT value_json FROM runtime_state WHERE state_key='combat'"
            ).fetchone()
            if row:
                state = json.loads(row["value_json"])
                encounter = state.get("active_encounter") if isinstance(state, dict) else None
                roster = state.get("encounter_roster") if isinstance(state, dict) else None
                if encounter and encounter.get("state") == "combat" and isinstance(roster, dict):
                    meta = roster.get(str(player_id))
                    if isinstance(meta, dict):
                        live = True
                        if int(pools["max_mp"]) > 0:
                            current_mp = max(0, min(int(pools["max_mp"]), int(meta.get("mp", current_mp))))
                        if int(pools["max_ap"]) > 0:
                            current_ap = max(0, min(int(pools["max_ap"]), int(meta.get("ap", current_ap))))
        except (sqlite3.Error, ValueError, TypeError, json.JSONDecodeError):
            # Resource bars are informational. A malformed/locked runtime row
            # must never make the player profile unavailable.
            live = False
        return {
            "mode": job_resource_mode(job),
            "live_battle": live,
            "mp": {"current": current_mp, "max": max_mp},
            "ap": {"current": current_ap, "max": max_ap},
        }

    def _chocobo_public(self, conn: sqlite3.Connection, player_id: str) -> dict[str, Any] | None:
        try:
            row = conn.execute(
                "SELECT name,level,xp,registered_at,portrait_id FROM player_chocobos WHERE player_id=?",
                (str(player_id),),
            ).fetchone()
        except sqlite3.Error:
            return None
        if not row or not row["registered_at"] or not row["name"]:
            return None
        level, xp_current, xp_next = chocobo_level_from_total_xp(int(row["xp"] or 0))
        traits = []
        try:
            trait_rows = conn.execute(
                "SELECT trait_id FROM player_chocobo_traits WHERE player_id=? ORDER BY unlocked_at,trait_id",
                (str(player_id),),
            ).fetchall()
        except sqlite3.Error:
            trait_rows = []
        for trait_row in trait_rows:
            trait_id = str(trait_row["trait_id"])
            trait = CHOCOBO_TRAITS.get(trait_id)
            if trait:
                traits.append({"id": trait_id, **trait})
        portrait_id = str(row["portrait_id"] or CHOCOBO_DEFAULT_PORTRAIT_ID)
        if portrait_id not in CHOCOBO_PORTRAITS:
            portrait_id = CHOCOBO_DEFAULT_PORTRAIT_ID
        return {
            "name": str(row["name"]),
            "level": int(level),
            "xp_current": int(xp_current),
            "xp_next": int(xp_next),
            "traits": traits,
            "specialization": chocobo_expedition_specialization({row["id"] for row in traits}, int(level)),
            "portrait_id": portrait_id,
            "portrait_name": CHOCOBO_PORTRAITS[portrait_id]["name"],
            "registered_at": str(row["registered_at"]),
        }

    def _fellowship_member(self, conn: sqlite3.Connection, player_id: str) -> dict[str, Any]:
        try:
            row = conn.execute("SELECT * FROM fellowship_members WHERE player_id=?", (str(player_id),)).fetchone()
        except sqlite3.Error:
            row = None
        renown = int(row["renown"]) if row else 0
        event_rows = conn.execute("SELECT activity,COALESCE(SUM(amount),0) AS amount FROM fellowship_events WHERE player_id=? GROUP BY activity", (str(player_id),)).fetchall()
        totals = {str(item["activity"]): int(item["amount"] or 0) for item in event_rows}
        crew = conn.execute("SELECT COUNT(DISTINCT run_id) AS n FROM fellowship_airship_mission_members WHERE player_id=?", (str(player_id),)).fetchone()
        workshop = conn.execute("SELECT COALESCE(SUM(amount),0) AS n FROM fellowship_activity WHERE player_id=? AND kind='workshop_service'", (str(player_id),)).fetchone()
        service = {
            "ventures_completed": int(totals.get("venture_complete", 0)),
            "hunts_won": int(totals.get("hunt_win", 0)),
            "raid_participations": int(totals.get("raid_participation", 0)),
            "expeditions_completed": int(totals.get("expedition_complete", 0)),
            "crafts_completed": int(totals.get("craft", 0)),
            "forge_upgrades": int(totals.get("forge", 0)),
            "airship_missions_supported": int(crew["n"] if crew else 0),
            "workshop_batches": int(workshop["n"] if workshop else 0),
        }
        distinctions = []
        if row and bool(row["founding_member"]): distinctions.append("Founding Member")
        if row and int(row["projects_contributed"]) >= 5: distinctions.append("Guild Builder")
        if row and int(row["gil_donated"]) >= 100_000: distinctions.append("Guild Benefactor")
        if row and int(row["orders_participated"]) >= 10: distinctions.append("Order Veteran")
        if row and int(row["deeds_assisted"]) >= 5: distinctions.append("Deedkeeper")
        if int(service["airship_missions_supported"]) >= 5: distinctions.append("Airship Crew")
        if int(service["expeditions_completed"]) >= 25: distinctions.append("Frontier Pathfinder")
        return {
            "renown": renown,
            "rank": guild_rank_for_renown(renown),
            "founding_member": bool(row["founding_member"]) if row else False,
            "projects_contributed": int(row["projects_contributed"]) if row else 0,
            "gil_donated": int(row["gil_donated"]) if row else 0,
            "materials_donated": int(row["materials_donated"]) if row else 0,
            "orders_participated": int(row["orders_participated"]) if row else 0,
            "deeds_assisted": int(row["deeds_assisted"]) if row else 0,
            "service_record": service,
            "distinctions": distinctions,
        }

    def fellowship(self) -> dict[str, Any]:
        """Return the sanitized channel-wide Fellowship snapshot for hosted sync."""
        with self.connect() as conn:
            try:
                state = conn.execute("SELECT * FROM fellowship_state WHERE singleton_id=1").fetchone()
            except sqlite3.Error:
                state = None
            if not state:
                return {
                    "level": 1, "level_label": "LVL 1", "renown": 0,
                    "level_progress": fellowship_level_progress(0), "member_count": 0,
                    "active_project": None, "available_projects": [], "facilities": [],
                    "guild_board": {"facility_count": 7, "built_count": 0, "complete_count": 0, "airship_dock_locked": False},
                    "orders": {"period": weekly_period_key(), "orders": [], "completed": 0, "total": 0, "weekly_bonus": dict(WEEKLY_ORDER_SET_REWARD)},
                    "contracts": {"period": weekly_period_key(), "objectives": [], "completed": 0, "total": 3},
                    "deeds": [], "deeds_complete": 0, "leaders": [], "recent_activity": [],
                    "totals": {"gil_donated": 0, "materials_donated": 0},
                    "expedition_board_complete": False, "rank_ladder": GUILD_RANKS,
                    "effects": facility_effects({}),
                    "services": {"workshop": {"level": 0, "forge_discount": 0.0}, "emporium_annex": {"level": 0, "unlocked": False, "stock_slots": 18, "purchase_discount": 0.0}, "trading_post": {"level": 0, "unlocked": True, **guild_commerce({}), "listing_hours": 48}, "chocobo_stable": {"level": 0, "xp_bonus": 0.0}, "archive": {"level": 0, "rare_event_bonus": 0.0}},
                    "airship": {"built": False, "dock_level": 0, "active_mission": None, "missions": [], "upgrades": [], "history": [], "missions_completed": 0, "missions_failed": 0},
                    "legacy": {"stage": 1, "stage_name": "Founding Hall", "completed": 0, "total": 10, "accomplishments": [], "decorations": [], "next_accomplishment": None},
                }
            level = int(state["level"] or 1)
            renown = int(state["renown"] or 0)
            tier_rows = conn.execute("SELECT facility_id,tier FROM fellowship_facilities").fetchall()
            tiers = {str(row["facility_id"]): int(row["tier"]) for row in tier_rows}
            facilities = []
            for facility_id in PUBLIC_GUILD_FACILITY_IDS:
                config = FACILITIES[facility_id]
                raw_tier = int(tiers.get(facility_id, 0))
                max_level = int(config.get("max_level", 3))
                facility_level = min(max(0, raw_tier), max_level)
                benefits = list(config.get("level_benefits") or config.get("benefits") or [])
                current_benefit = benefits[facility_level - 1] if facility_level > 0 and facility_level <= len(benefits) else "Construction plans are posted, but building has not started."
                next_benefit = benefits[facility_level] if facility_level < max_level and facility_level < len(benefits) else None
                facilities.append({
                    "id": facility_id, "name": config["name"], "level": facility_level, "max_level": max_level,
                    "tier": facility_level, "max_tier": max_level, "description": config["description"],
                    "current_benefit": current_benefit, "next_benefit": next_benefit, "locked": False,
                    "status": "Complete" if facility_level >= max_level else "Buildable",
                })

            def project_snapshot(project_id: str | None) -> dict[str, Any] | None:
                if not project_id or project_id not in PROJECTS:
                    return None
                project = PROJECTS[project_id]
                reqs = []
                complete = True
                for req in project["requirements"]:
                    if req["kind"] == "level":
                        current = level
                    else:
                        row = conn.execute("SELECT current FROM fellowship_project_progress WHERE project_id=? AND requirement_key=?", (project_id, req["key"])).fetchone()
                        current = int(row["current"]) if row else 0
                    target = int(req["target"])
                    done = current >= target
                    complete = complete and done
                    reqs.append({**req, "current": min(current, target), "complete": done})
                return {**project, "requirements": reqs, "complete": complete}

            active_id = str(state["active_project_id"]) if state["active_project_id"] else None
            active_project = project_snapshot(active_id)
            hall = int(tiers.get("guild_hall", 1))
            expedition_done = bool(state["expedition_board_complete"])
            airship_state = conn.execute("SELECT * FROM fellowship_airship_state WHERE singleton_id=1").fetchone()
            airship_built = bool(airship_state and int(airship_state["built"] or 0))
            upgrade_rows = conn.execute("SELECT upgrade_id,tier FROM fellowship_airship_upgrades").fetchall()
            airship_upgrades = {str(row["upgrade_id"]): int(row["tier"] or 0) for row in upgrade_rows}
            available = []
            for project in PROJECTS.values():
                if project.get("legacy"):
                    continue
                ptype = str(project.get("project_type") or "construction")
                if ptype == "airship_construction":
                    if airship_built or level < int(project.get("required_level", 1)) or int(tiers.get("airship_dock", 0)) < int(project.get("required_dock_level", 1)):
                        continue
                elif ptype == "airship_upgrade":
                    upgrade_id = str(project.get("upgrade_id") or "")
                    if not airship_built or level < int(project.get("required_level", 1)):
                        continue
                    if int(project.get("tier", 0)) != int(airship_upgrades.get(upgrade_id, 0)) + 1:
                        continue
                    if int(tiers.get("airship_dock", 0)) < int(project.get("required_dock_level", project.get("tier", 1))):
                        continue
                elif ptype in {"supply_drive", "guild_objective"}:
                    if level < int(project.get("required_level", 1)):
                        continue
                    done = conn.execute("SELECT 1 FROM fellowship_events WHERE event_key=?", (f"community_project_complete:{project['id']}",)).fetchone()
                    if done:
                        continue
                elif project.get("teaser"):
                    if expedition_done or hall < int(project.get("required_hall_tier", 5)) or level < int(project["required_level"]):
                        continue
                else:
                    current = int(tiers.get(project["facility_id"], 0))
                    if int(project["tier"]) != current + 1:
                        continue
                    if project["facility_id"] == "airship_dock" and hall < int(project.get("required_hall_tier", 1)):
                        continue
                    if project["facility_id"] not in {"guild_hall", "airship_dock"} and int(project["tier"]) > hall:
                        continue
                    if level < int(project["required_level"]):
                        continue
                available.append(project_snapshot(project["id"]) or dict(project))
            available.sort(key=lambda item: (str(item.get("project_type", "construction")), int(item.get("tier", 0)), str(item.get("name", ""))))


            period = weekly_period_key()
            selected = weekly_orders(period)
            order_rows = {str(row["order_id"]): row for row in conn.execute("SELECT * FROM fellowship_orders WHERE period_key=?", (period,)).fetchall()}
            order_items = []
            for order in selected:
                row = order_rows.get(order["id"])
                progress = int(row["progress"]) if row else 0
                completed_at = row["completed_at"] if row else None
                order_items.append({**order, "progress": progress, "complete": bool(completed_at), "completed_at": completed_at})

            deed_rows = {str(row["deed_id"]): row for row in conn.execute("SELECT * FROM fellowship_deeds").fetchall()}
            deed_items = []
            for deed in DEEDS:
                row = deed_rows.get(deed["id"])
                deed_items.append({**deed, "progress": int(row["progress"]) if row else 0, "complete": bool(row and row["completed_at"]), "completed_at": row["completed_at"] if row else None})

            leaders = []
            for row in conn.execute("SELECT fm.*,p.username,p.display_name,p.level FROM fellowship_members fm JOIN players p ON p.twitch_id=fm.player_id ORDER BY fm.renown DESC,p.level DESC,lower(p.display_name) ASC LIMIT 12").fetchall():
                leaders.append({
                    "username": row["username"], "display_name": row["display_name"], "level": int(row["level"]),
                    "renown": int(row["renown"]), "rank": guild_rank_for_renown(int(row["renown"]))["name"],
                    "founding_member": bool(row["founding_member"]),
                })
            activity = []
            for row in conn.execute("SELECT fa.*,p.username,p.display_name FROM fellowship_activity fa LEFT JOIN players p ON p.twitch_id=fa.player_id ORDER BY fa.id DESC LIMIT 16").fetchall():
                activity.append({
                    "kind": row["kind"], "label": row["label"], "amount": int(row["amount"]),
                    "username": row["username"], "display_name": row["display_name"], "created_at": row["created_at"],
                })
            member_count = conn.execute("SELECT COUNT(*) AS n FROM fellowship_members").fetchone()
            totals = conn.execute("SELECT COALESCE(SUM(gil_donated),0) AS gil,COALESCE(SUM(materials_donated),0) AS materials FROM fellowship_members").fetchone()
            effects = facility_effects(tiers)
            annex_level = max(0, min(1, int(tiers.get("emporium_annex", 0))))
            trading_post_level = max(0, min(1, int(tiers.get("trading_post", 0))))
            services = {
                "guild_hall": {"level": min(3, int(tiers.get("guild_hall", 0)))},
                "workshop": {"level": min(3, int(tiers.get("workshop", 0))), "forge_discount": float(effects.get("forge_discount", 0.0))},
                "emporium_annex": {"level": annex_level, "unlocked": annex_level >= 1, "stock_slots": 18, "purchase_discount": guild_commerce(tiers)["purchase_discount"]},
                "trading_post": {"level": trading_post_level, "unlocked": True, **guild_commerce(tiers), "listing_hours": 48},
                "chocobo_stable": {"level": min(3, int(tiers.get("chocobo_stable", 0))), "xp_bonus": float(effects.get("chocobo_xp_bonus", 0.0))},
                "archive": {"level": min(3, int(tiers.get("archives", 0))), "rare_event_bonus": float(effects.get("archive_rare_event_bonus", 0.0))},
            }
            upgrades = {key: max(0, min(3, int(airship_upgrades.get(key, 0)))) for key in AIRSHIP_UPGRADES}
            now = int(time.time())
            active_mission = None
            if airship_state and airship_state["active_mission_id"]:
                mission = next((m for m in AIRSHIP_MISSIONS if m["id"] == str(airship_state["active_mission_id"])), None)
                if mission:
                    remaining = max(0, int(airship_state["ends_at"] or now) - now)
                    hours, rem = divmod(remaining, 3600)
                    minutes = rem // 60
                    participant = conn.execute("SELECT COUNT(*) AS n FROM fellowship_airship_mission_members WHERE run_id=?", (str(airship_state["active_run_id"]),)).fetchone()
                    active_mission = {**mission, "run_id": str(airship_state["active_run_id"]), "started_at": int(airship_state["started_at"] or now), "ends_at": int(airship_state["ends_at"] or now), "progress": int(airship_state["progress"] or 0), "target": int(airship_state["target"] or mission["target"]), "ready": int(airship_state["progress"] or 0) >= int(airship_state["target"] or mission["target"]), "remaining_seconds": remaining, "duration_label": f"{hours}h {minutes:02d}m" if hours else f"{minutes}m", "participant_count": int(participant["n"] if participant else 0)}
            mission_list = []
            hull = upgrades.get("hull", 0); engine = upgrades.get("engine", 0); core = upgrades.get("crystal_core", 0)
            for mission in AIRSHIP_MISSIONS:
                mission_list.append({**mission, "unlocked": airship_built and int(mission.get("required_core", 0)) <= core, "target_effective": max(1, int(math.ceil(int(mission["target"]) * (1.0 - 0.04 * hull)))), "duration_seconds": max(21600, int(round(float(mission["duration_hours"]) * (1.0 - 0.06 * engine) * 3600)))})
            history = []
            for row in conn.execute("SELECT * FROM fellowship_airship_mission_history ORDER BY ended_at DESC LIMIT 5").fetchall():
                mission = next((m for m in AIRSHIP_MISSIONS if m["id"] == str(row["mission_id"])), {"name": str(row["mission_id"])})
                history.append({"run_id": row["run_id"], "mission_id": row["mission_id"], "name": mission["name"], "outcome": row["outcome"], "progress": int(row["progress"]), "target": int(row["target"]), "guild_renown": int(row["guild_renown"]), "participant_count": int(row["participant_count"]), "ended_at": int(row["ended_at"])})
            airship = {"built": airship_built, "dock_level": min(3, int(tiers.get("airship_dock", 0))), "missions_completed": int(airship_state["missions_completed"] or 0) if airship_state else 0, "missions_failed": int(airship_state["missions_failed"] or 0) if airship_state else 0, "active_mission": active_mission, "missions": mission_list, "upgrades": [{"id": key, "name": AIRSHIP_UPGRADES[key]["name"], "description": AIRSHIP_UPGRADES[key]["description"], "tier": upgrades[key], "max_tier": 3} for key in AIRSHIP_UPGRADES], "history": history}
            return {
                "level": level, "level_label": f"LVL {level}", "renown": renown,
                "level_progress": fellowship_level_progress(renown),
                "member_count": int(member_count["n"] if member_count else 0),
                "active_project": active_project, "available_projects": available, "facilities": facilities,
                "guild_board": {"facility_count": len(facilities), "built_count": sum(1 for item in facilities if int(item["level"]) > 0), "complete_count": sum(1 for item in facilities if int(item["level"]) >= int(item["max_level"])), "airship_dock_locked": False},
                "orders": {"period": period, "orders": order_items, "completed": sum(1 for item in order_items if item["complete"]), "total": len(order_items), "weekly_bonus": dict(WEEKLY_ORDER_SET_REWARD)},
                "contracts": contract_view(conn),
                "deeds": deed_items, "deeds_complete": sum(1 for item in deed_items if item["complete"]),
                "leaders": leaders, "recent_activity": activity,
                "totals": {"gil_donated": int(totals["gil"] if totals else 0), "materials_donated": int(totals["materials"] if totals else 0)},
                "expedition_board_complete": expedition_done, "rank_ladder": GUILD_RANKS,
                "effects": effects, "services": services, "airship": airship,
                "legacy": legacy_snapshot_from_connection(conn),
            }

    def guild_board(self, key: str) -> dict[str, Any] | None:
        """Public personal objectives. Never expose Twitch IDs in hosted snapshots."""
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            return {"player": self._public_identity(player), "board": board_view(conn, str(player["twitch_id"]))}

    def overview(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            player_id = player["twitch_id"]
            job = self.data.jobs.get(player["current_job"])
            jrow = None
            if job:
                jrow = conn.execute(
                    "SELECT level, jp FROM player_jobs WHERE player_id=? AND job_id=?",
                    (player_id, player["current_job"]),
                ).fetchone()
            equipment = self._equipment(conn, player_id, job)
            stats = self._stats(conn, player, job, equipment)
            status = self._status(player, stats["hp"])
            hp_current = stats["hp"] if status["state"] == "ready_after_rest" else int(player["current_hp"])
            counts = self._counts(conn, player_id)
            mastery_slots = self._mastery_slots(conn, player_id)
            region = self.data.regions.get(player["current_region"])
            recent = self._recent_activity(conn, player_id, 8)
            return {
                "identity": {
                    "username": player["username"],
                    "display_name": player["display_name"],
                    "title": player["title"],
                    "level": int(player["level"]),
                    "xp": int(player["xp"]),
                    "xp_next": xp_to_next(int(player["level"])),
                    "gil": int(player["gil"]),
                    "hunt_seals": int(player["hunt_seals"]),
                    "stance": player["stance"],
                    "created_at": player["created_at"],
                    "updated_at": player["updated_at"],
                },
                "job": {
                    "id": player["current_job"],
                    "name": job["name"] if job else "Adventurer",
                    "level": int(jrow["level"]) if jrow else 0,
                    "jp": int(jrow["jp"]) if jrow else 0,
                    "jp_next": jp_to_next(int(jrow["level"])) if jrow else 0,
                    "tier": job.get("tier", "starter") if job else "unassigned",
                    "signature": job.get("signature", "—") if job else "—",
                    "resource_mode": job_resource_mode(job),
                },
                "status": status,
                "hp": {"current": max(0, hp_current), "max": stats["hp"]},
                "resources": self._resource_state(conn, player_id, stats, job),
                "stats": stats,
                "region": {
                    "id": player["current_region"],
                    "name": region["name"] if region else player["current_region"],
                },
                "equipment": equipment,
                "mastery_slots": mastery_slots,
                "counts": counts,
                "fellowship": self._fellowship_member(conn, player_id),
                "chocobo": self._chocobo_public(conn, player_id),
                "recent_activity": recent,
            }

    def jobs(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            rows = conn.execute(
                "SELECT job_id, level, jp FROM player_jobs WHERE player_id=?",
                (player["twitch_id"],),
            ).fetchall()
            owned = {row["job_id"]: row for row in rows}
            entries = []
            for job in self.data.jobs.values():
                row = owned.get(job["id"])
                level = int(row["level"]) if row else 0
                jp = int(row["jp"]) if row else 0
                learned = [a for a in job.get("abilities", []) if level >= int(a["level"])]
                entries.append(
                    {
                        "id": job["id"],
                        "name": job["name"],
                        "tier": job.get("tier", "starter"),
                        "owned": row is not None,
                        "current": player["current_job"] == job["id"],
                        "level": level,
                        "jp": jp,
                        "jp_next": jp_to_next(level) if level else 0,
                        "mastered": level >= 50,
                        "signature": job.get("signature", "—"),
                        "abilities": learned,
                        "mastery": job.get("mastery", {}),
                    }
                )
            return {
                "player": self._public_identity(player),
                "mastery_slots": self._mastery_slots(conn, player["twitch_id"]),
                "jobs": entries,
            }

    def inventory(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            player_id = player["twitch_id"]
            equipped_row = conn.execute("SELECT * FROM equipment WHERE player_id=?", (player_id,)).fetchone()
            equipped = {
                equipped_row["weapon_id"] if equipped_row else None,
                equipped_row["armor_id"] if equipped_row else None,
                equipped_row["accessory_id"] if equipped_row else None,
            }
            upgrades = {
                row["item_id"]: int(row["upgrade_level"])
                for row in conn.execute(
                    "SELECT item_id, upgrade_level FROM item_upgrades WHERE player_id=?",
                    (player_id,),
                ).fetchall()
            }
            rows = conn.execute(
                "SELECT item_id, quantity FROM inventory WHERE player_id=? AND quantity>0",
                (player_id,),
            ).fetchall()
            items = []
            for row in rows:
                item = self.data.items.get(row["item_id"])
                if not item:
                    continue
                upgrade_level = upgrades.get(item["id"], 0)
                raw_bonuses = item.get("bonuses", {})
                scale = 1 + self._forge_bonus * upgrade_level
                effective_bonuses = {
                    key: int(round(float(value) * scale))
                    for key, value in raw_bonuses.items()
                }
                allowed_job_ids = [j for j in item.get("allowed_jobs", []) if j in self.data.jobs]
                items.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "type": item.get("type", "item"),
                        "description": str(item.get("description") or ""),
                        "use": item.get("use"),
                        "rarity": item.get("rarity", "common"),
                        "quantity": int(row["quantity"]),
                        "equipped": item["id"] in equipped,
                        "upgrade_level": upgrade_level,
                        "bonuses": raw_bonuses,
                        "effective_bonuses": effective_bonuses,
                        "min_level": int(item.get("min_level", 1) or 1),
                        "allowed_job_ids": allowed_job_ids,
                        "allowed_jobs": [self.data.jobs[j]["name"] for j in allowed_job_ids],
                        "relic_stage": item.get("relic_stage"),
                        "price": int(item.get("price", 0) or 0),
                        "sellable": not bool(item.get("unsellable") or item.get("relic_id")),
                        "sell_value": int(sell_value(item.get("price", 0), item.get("type", "item"))) if not (item.get("unsellable") or item.get("relic_id")) else 0,
                    }
                )
            type_order = {"weapon": 0, "armor": 1, "accessory": 2, "item": 3, "consumable": 3, "material": 4}

            def inventory_sort_key(entry: dict[str, Any]) -> tuple[Any, ...]:
                item_type = str(entry.get("type") or "item").lower()
                group = type_order.get(item_type, 3)
                if item_type in {"weapon", "armor", "accessory"}:
                    return (group, -int(entry.get("min_level", 1) or 1), str(entry.get("name") or "").lower())
                return (group, 0, str(entry.get("name") or "").lower())

            items.sort(key=inventory_sort_key)
            favorite_item_ids = [
                str(row["item_id"])
                for row in conn.execute(
                    "SELECT item_id FROM player_gear_favorites WHERE player_id=? ORDER BY created_at ASC, item_id ASC",
                    (player_id,),
                ).fetchall()
            ]
            return {
                "player": self._public_identity(player),
                "items": items,
                "favorite_item_ids": favorite_item_ids,
            }

    def hunts(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            rows = conn.execute(
                "SELECT hunt_id, clears, first_cleared_at, last_cleared_at FROM player_hunts WHERE player_id=?",
                (player["twitch_id"],),
            ).fetchall()
            progress = {row["hunt_id"]: row for row in rows}
            hunts = []
            for hunt in self.data.hunts.values():
                row = progress.get(hunt["id"])
                monster = self.data.monsters.get(hunt["monster_id"])
                hunts.append(
                    {
                        "id": hunt["id"],
                        "name": hunt["name"],
                        "rank": hunt["rank"],
                        "min_level": int(hunt["min_level"]),
                        "monster": monster["name"] if monster else hunt["monster_id"],
                        "clears": int(row["clears"]) if row else 0,
                        "first_cleared_at": row["first_cleared_at"] if row else None,
                        "last_cleared_at": row["last_cleared_at"] if row else None,
                    }
                )
            rank_summary = {}
            for rank in ("C", "B", "A", "S", "S+"):
                group = [h for h in hunts if h["rank"] == rank]
                if group:
                    rank_summary[rank] = {
                        "cleared": sum(1 for h in group if h["clears"] > 0),
                        "total": len(group),
                    }
            return {"player": self._public_identity(player), "summary": rank_summary, "hunts": hunts}

    def bestiary(self, key: str) -> dict[str, Any] | None:
        """Return the unified Bestiary without taking ownership of other systems.

        Base research (regional monsters, Hunts, Expedition bosses) remains
        driven by ``bestiary.defeats`` and the schema-22 mastery ledger.
        Raid/boss, World Event, and seasonal records are read from their own
        canonical progress tables and projected into scoped Bestiary entries.
        """
        from .world_events import WORLD_EVENTS
        from .seasonal_events import EDITION_ID, EVENT_NAME, HOLLOW_WARDEN, SEASONAL_VARIANTS

        def item_drops(rows):
            out = []
            for drop in rows or []:
                item_id = str(drop.get("item_id") or "")
                item = self.data.items.get(item_id) or {}
                out.append({
                    "item_id": item_id,
                    "name": item.get("name") or item_id,
                    "chance": float(drop.get("chance", 0) or 0),
                    "min": int(drop.get("min", 1) or 1),
                    "max": int(drop.get("max", 1) or 1),
                })
            return out

        def external_research(clears: int, *, source: str, unit: str = "clear"):
            clears = max(0, int(clears or 0))
            complete = clears > 0
            return {
                "category": source,
                "family_id": None,
                "family": None,
                "stage": "recorded" if complete else "undiscovered",
                "stage_index": 1 if complete else 0,
                "stage_count": 1,
                "visible_fields": ["name", "level", "portrait", "habitats", "family", "weakness", "combat_profile", "active_skill", "drops", "lore"] if complete else [],
                "next_milestone": None if complete else {"key": "recorded", "defeats": 1, "remaining": 1},
                "mastered": complete,
                "mastery_threshold": 1,
                "completion_kind": "external_record",
                "progress_unit": unit,
            }

        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            player_id = str(player["twitch_id"])
            rows = conn.execute(
                "SELECT monster_id, defeats FROM bestiary WHERE player_id=?",
                (player_id,),
            ).fetchall()
            defeated = {row["monster_id"]: int(row["defeats"]) for row in rows}
            try:
                mastery_rows = conn.execute(
                    """
                    SELECT monster_id, research_points, source_defeats, mastered_at
                    FROM player_bestiary_mastery WHERE player_id=?
                    """,
                    (player_id,),
                ).fetchall()
            except sqlite3.OperationalError:
                mastery_rows = []
            mastery = {row["monster_id"]: row for row in mastery_rows}
            entries = []
            overlay_entries = self.data.bestiary_research.get("entries") or {}
            # Keep raw habitat IDs for stable API consumers. Names are a separate,
            # reveal-gated presentation field so players never see sable_coast.
            location_names = {
                row_id: row.get("name") or row_id
                for collection in (self.data.regions, self.data.expedition_regions)
                for row_id, row in collection.items()
            }

            # Canonical 112-entry base catalog: regional + Hunt + Expedition.
            for monster in self.data.monsters.values():
                monster_id = str(monster["id"])
                defeats = defeated.get(monster_id, 0)
                research = progress_for(self.data, monster_id, defeats)
                visible = set(research["visible_fields"])
                field_guide = overlay_entries.get(monster_id) or {}
                behavior = self.data.enemy_actions.get(monster_id, {})
                profile = self.data.enemy_profiles.get(behavior.get("profile"), {})
                active_skill = behavior.get("ability") or {}
                receipt = mastery.get(monster_id)
                drops = item_drops(monster.get("drops", [])) if "drops" in visible else []
                entries.append({
                    "id": monster_id,
                    "scope": "base",
                    "source_id": monster_id,
                    "name": monster["name"] if "name" in visible else "???",
                    "level": int(monster["level"]) if "level" in visible else None,
                    "defeats": defeats,
                    "progress_count": defeats,
                    "progress_unit": "defeat",
                    "discovered": defeats > 0,
                    "portrait_unlocked": "portrait" in visible,
                    "category": research["category"] if defeats > 0 else None,
                    "family_id": research["family_id"] if "family" in visible else None,
                    "family": research["family"] if "family" in visible else None,
                    "family_description": ((self.data.bestiary_research.get("families") or {}).get(research["family_id"]) or {}).get("description") if "family" in visible else None,
                    "habitats": list(field_guide.get("habitats") or []) if "habitats" in visible else [],
                    "habitat_names": [location_names.get(region_id, region_id) for region_id in field_guide.get("habitats") or []] if "habitats" in visible else [],
                    "weakness": monster.get("weakness", "—") if "weakness" in visible else None,
                    "special": monster.get("special", "—") if "combat_profile" in visible else None,
                    "combat_profile": profile.get("name", "Balanced") if "combat_profile" in visible else None,
                    "active_skill": (active_skill.get("name") or "Basic attacks") if "active_skill" in visible else None,
                    "drops": drops,
                    "lore": field_guide.get("lore") if "lore" in visible else None,
                    "research": research,
                    "mastery_reward": {
                        "seal": bool(receipt),
                        "research_points": int(receipt["research_points"]) if receipt else 0,
                        "awarded_at": receipt["mastered_at"] if receipt else None,
                        "source_defeats": int(receipt["source_defeats"]) if receipt else None,
                        "external": False,
                    },
                })

            # Raid and boss records remain canonical in player_boss_clears.
            boss_rows = conn.execute(
                "SELECT boss_id, clears, last_cleared_at FROM player_boss_clears WHERE player_id=?",
                (player_id,),
            ).fetchall()
            boss_progress = {str(row["boss_id"]): row for row in boss_rows}
            for boss_id, boss in self.data.bosses.items():
                row = boss_progress.get(str(boss_id))
                clears = int(row["clears"] or 0) if row else 0
                discovered = clears > 0
                is_raid = str(boss.get("encounter_type") or "").lower() == "trial"
                category = "raid" if is_raid else "boss"
                encounter = boss.get("encounter_name") or "Guild Boss Board"
                research = external_research(clears, source=category, unit="clear")
                entries.append({
                    "id": f"boss:{boss_id}",
                    "scope": "boss",
                    "source_id": str(boss_id),
                    "name": boss.get("name", str(boss_id)) if discovered else "???",
                    "level": int(boss.get("recommended_level", 0) or 0) if discovered else None,
                    "defeats": clears,
                    "progress_count": clears,
                    "progress_unit": "clear",
                    "discovered": discovered,
                    "portrait_unlocked": discovered,
                    "art": f"/retro-phase-ii/boss-art-v1/{boss_id}.webp",
                    "category": category if discovered else None,
                    "family_id": None,
                    "family": (boss.get("tier") or "Boss Encounter") if discovered else None,
                    "habitats": [str(encounter)] if discovered else [],
                    "habitat_names": [str(encounter)] if discovered else [],
                    "weakness": None,
                    "special": boss.get("signature") if discovered else None,
                    "combat_profile": (boss.get("tier") or "Boss Encounter") if discovered else None,
                    "active_skill": boss.get("signature") if discovered else None,
                    "drops": item_drops(boss.get("drops", [])) if discovered else [],
                    "lore": boss.get("description") if discovered else None,
                    "research": research,
                    "mastery_reward": {
                        "seal": False,
                        "research_points": 0,
                        "external": True,
                        "label": "Encounter record complete",
                        "source": "Raid / Boss clear history",
                        "awarded_at": row["last_cleared_at"] if row else None,
                    },
                })

            # World Event variants remain canonical in player_world_event_clears.
            try:
                world_rows = conn.execute(
                    "SELECT world_event_id, clears, last_cleared_at FROM player_world_event_clears WHERE player_id=?",
                    (player_id,),
                ).fetchall()
            except sqlite3.OperationalError:
                world_rows = []
            world_progress = {str(row["world_event_id"]): row for row in world_rows}
            for event in WORLD_EVENTS:
                event_id = str(event["id"])
                row = world_progress.get(event_id)
                clears = int(row["clears"] or 0) if row else 0
                discovered = clears > 0
                base = self.data.monsters.get(str(event.get("base_monster_id") or "")) or {}
                base_guide = overlay_entries.get(str(event.get("base_monster_id") or "")) or {}
                research = external_research(clears, source="world_event", unit="victory")
                entries.append({
                    "id": f"world_event:{event_id}",
                    "scope": "world_event",
                    "source_id": event_id,
                    "name": event["name"] if discovered else "???",
                    "level": int(base.get("level", 0) or 0) if discovered else None,
                    "defeats": clears,
                    "progress_count": clears,
                    "progress_unit": "victory",
                    "discovered": discovered,
                    "portrait_unlocked": discovered,
                    "art": event.get("art"),
                    "category": "world_event" if discovered else None,
                    "family_id": base_guide.get("family") if discovered else None,
                    "family": "World Event Variant" if discovered else None,
                    "habitats": ["World Event"] if discovered else [],
                    "habitat_names": ["World Event"] if discovered else [],
                    "weakness": base.get("weakness") if discovered else None,
                    "special": f"Threat: {event.get('threat', 'Unknown')}" if discovered else None,
                    "combat_profile": f"{event.get('threat', 'Unknown')} threat" if discovered else None,
                    "active_skill": None,
                    "drops": item_drops(base.get("drops", [])) if discovered else [],
                    "lore": event.get("description") if discovered else None,
                    "research": research,
                    "mastery_reward": {
                        "seal": False,
                        "research_points": 0,
                        "external": True,
                        "label": "World Event record complete",
                        "source": "World Event clear history / Hall of Trophies",
                        "awarded_at": row["last_cleared_at"] if row else None,
                    },
                })

            # Seasonal discoveries stay edition-scoped and survive event archival.
            try:
                seasonal_rows = conn.execute(
                    "SELECT variant_id, clears, last_cleared_at FROM player_seasonal_monster_clears WHERE player_id=? AND edition_id=?",
                    (player_id, EDITION_ID),
                ).fetchall()
                season_state = conn.execute(
                    "SELECT warden_clears, updated_at FROM player_seasonal_event_progress WHERE player_id=? AND edition_id=?",
                    (player_id, EDITION_ID),
                ).fetchone()
            except sqlite3.OperationalError:
                seasonal_rows, season_state = [], None
            seasonal_progress = {str(row["variant_id"]): row for row in seasonal_rows}
            seasonal_catalog = list(SEASONAL_VARIANTS) + [HOLLOW_WARDEN]
            for variant in seasonal_catalog:
                variant_id = str(variant["id"])
                if variant_id == str(HOLLOW_WARDEN["id"]):
                    clears = int(season_state["warden_clears"] or 0) if season_state else 0
                    last_clear = season_state["updated_at"] if season_state and clears > 0 else None
                else:
                    row = seasonal_progress.get(variant_id)
                    clears = int(row["clears"] or 0) if row else 0
                    last_clear = row["last_cleared_at"] if row else None
                discovered = clears > 0
                base_id = str(variant.get("base_monster_id") or "")
                base = self.data.monsters.get(base_id) or {}
                research = external_research(clears, source="seasonal", unit="clear")
                entries.append({
                    "id": f"seasonal:{EDITION_ID}:{variant_id}",
                    "scope": "seasonal",
                    "source_id": variant_id,
                    "edition_id": EDITION_ID,
                    "name": variant["name"] if discovered else "???",
                    "level": int(base.get("level", 0) or 0) if discovered else None,
                    "defeats": clears,
                    "progress_count": clears,
                    "progress_unit": "clear",
                    "discovered": discovered,
                    "portrait_unlocked": discovered,
                    "art": variant.get("art"),
                    "locked_art": variant.get("locked_art"),
                    "category": "seasonal" if discovered else None,
                    "family_id": None,
                    "family": EVENT_NAME if discovered else None,
                    "habitats": [EVENT_NAME] if discovered else [],
                    "habitat_names": [EVENT_NAME] if discovered else [],
                    "weakness": base.get("weakness") if discovered else None,
                    "special": variant.get("element") or variant.get("threat") if discovered else None,
                    "combat_profile": "Seasonal Variant" if discovered else None,
                    "active_skill": None,
                    "drops": item_drops(base.get("drops", [])) if discovered else [],
                    "lore": (variant.get("description") or f"A limited seasonal form recorded during {EVENT_NAME}.") if discovered else None,
                    "research": research,
                    "mastery_reward": {
                        "seal": False,
                        "research_points": 0,
                        "external": True,
                        "label": "Seasonal record complete",
                        "source": f"{EVENT_NAME} ({EDITION_ID})",
                        "awarded_at": last_clear,
                    },
                })

            # Locked names never become a sorting/search oracle.
            entries.sort(key=lambda m: (m["level"] is None, m["level"] or 10**9, (m["name"] if m["name"] != "???" else "").lower(), m["id"]))
            discovered_count = sum(1 for m in entries if m["discovered"])
            completed_count = sum(1 for m in entries if m["research"].get("mastered"))
            total_progress = sum(int(m.get("progress_count", 0) or 0) for m in entries)
            research_points = sum(int(row["research_points"] or 0) for row in mastery_rows)
            base_entries = [m for m in entries if m.get("scope") == "base"]
            visible_base = [m for m in base_entries if m["defeats"] > 0]
            nemesis = max(visible_base, key=lambda m: m["defeats"], default=None)
            return {
                "player": self._public_identity(player),
                "summary": {
                    "discovered": discovered_count,
                    "mastered": completed_count,
                    "completed": completed_count,
                    "total": len(entries),
                    "base_total": len(base_entries),
                    "special_total": len(entries) - len(base_entries),
                    "defeats": sum(m["defeats"] for m in base_entries),
                    "recorded_progress": total_progress,
                    "research_points": research_points,
                    "mastery_seals": len(mastery_rows),
                    "most_defeated": nemesis,
                },
                "monsters": entries,
            }

    def relics(self, key: str) -> dict[str, Any] | None:
        """Relic catalog and live progress; fixed number of indexed player reads.

        Preserve the legacy ``stages`` string list for existing consumers.  The
        richer ``path`` includes published stage requirements and reward stats,
        while readiness is calculated only for the player's *next* stage.
        """
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            player_id = player["twitch_id"]
            progress = {
                row["relic_id"]: row for row in conn.execute(
                    "SELECT relic_id,stage,completed_at FROM player_relics WHERE player_id=?",
                    (player_id,),
                )
            }
            # Read each source just once.  18 Relics x 3 stages should not
            # become hundreds of per-material/per-Hunt SQLite queries.
            job_levels = {
                row["job_id"]: int(row["level"] or 0) for row in conn.execute(
                    "SELECT job_id,level FROM player_jobs WHERE player_id=?", (player_id,),
                )
            }
            inventory = {
                row["item_id"]: int(row["quantity"] or 0) for row in conn.execute(
                    "SELECT item_id,quantity FROM inventory WHERE player_id=?", (player_id,),
                )
            }
            kills = {
                row["monster_id"]: int(row["defeats"] or 0) for row in conn.execute(
                    "SELECT monster_id,defeats FROM bestiary WHERE player_id=?", (player_id,),
                )
            }
            hunt_clears = {
                row["hunt_id"]: int(row["clears"] or 0) for row in conn.execute(
                    "SELECT hunt_id,clears FROM player_hunts WHERE player_id=?", (player_id,),
                )
            }
            unique_ranks: dict[str, int] = {}
            for hunt_id, clears in hunt_clears.items():
                hunt = self.data.hunts.get(hunt_id)
                if hunt and clears > 0:
                    rank = str(hunt["rank"])
                    unique_ranks[rank] = unique_ranks.get(rank, 0) + 1

            def requirement_info(req: dict[str, Any]) -> dict[str, Any]:
                kind = req["type"]
                amount = int(req.get("amount", 1))
                if kind == "character_level":
                    label = "Character level"
                    current = int(player["level"])
                elif kind == "job_level":
                    job_id = str(req.get("job_id") or "")
                    job = self.data.jobs.get(job_id, {})
                    label = f"{job.get('name', 'Job')} Job level"
                    current = int(job_levels.get(job_id, 0))
                elif kind == "monster_kills":
                    monster_id = str(req.get("monster_id") or "")
                    monster = self.data.monsters.get(monster_id, {})
                    label = f"Defeat {monster.get('name', 'monster')}"
                    current = int(kills.get(monster_id, 0))
                elif kind == "hunt_clear":
                    hunt_id = str(req.get("hunt_id") or "")
                    hunt = self.data.hunts.get(hunt_id, {})
                    label = f"Clear {hunt.get('name', 'Hunt')}"
                    current = int(hunt_clears.get(hunt_id, 0))
                elif kind == "hunt_rank_clears":
                    rank = str(req.get("rank") or "")
                    label = f"Unique {rank}-Rank Hunts cleared"
                    current = int(unique_ranks.get(rank, 0))
                else:
                    # New requirement types should not be falsely marked as met.
                    label = kind.replace("_", " ").capitalize()
                    current = 0
                return {
                    "type": kind,
                    "label": label,
                    "current": current,
                    "required": amount,
                    "met": current >= amount,
                }

            def reward_info(item_id: str) -> dict[str, Any]:
                item = self.data.items.get(item_id) or {}
                return {
                    "id": item_id,
                    "name": item.get("name", item_id.replace("_", " ").title()),
                    "rarity": item.get("rarity", "relic"),
                    "min_level": int(item.get("min_level", 1)),
                    "bonuses": dict(item.get("bonuses") or {}),
                    "allowed_jobs": list(item.get("allowed_jobs") or []),
                    "allowed_job_names": [self.data.jobs.get(job_id, {}).get("name", job_id) for job_id in (item.get("allowed_jobs") or [])],
                    "description": item.get("description") or "",
                    "element": item.get("element"),
                    "on_hit_status": item.get("on_hit_status"),
                    "lifesteal": item.get("lifesteal"),
                    "owned": int(inventory.get(item_id, 0)),
                }

            relics = []
            for relic in self.data.relics.values():
                row = progress.get(relic["id"])
                total = len(relic.get("stages", []))
                stage = min(max(int(row["stage"] or 0), 0), total) if row else 0
                job = self.data.jobs.get(relic["job_id"]) or {}
                job_level = int(job_levels.get(relic["job_id"], 0))
                path = []
                for index, step in enumerate(relic.get("stages", [])):
                    requirements = [requirement_info(req) for req in step.get("requirements", [])]
                    cost = step.get("cost") or {}
                    gil = int(cost.get("gil", 0))
                    seals = int(cost.get("hunt_seals", 0))
                    materials = []
                    for entry in cost.get("items", []):
                        material_id = str(entry["item_id"])
                        required = int(entry["quantity"])
                        owned = int(inventory.get(material_id, 0))
                        material = self.data.items.get(material_id) or {}
                        materials.append({
                            "id": material_id,
                            "name": material.get("name", material_id.replace("_", " ").title()),
                            "required": required,
                            "owned": owned,
                            "met": owned >= required,
                        })
                    costs_met = (int(player["gil"]) >= gil
                                 and int(player["hunt_seals"]) >= seals
                                 and all(entry["met"] for entry in materials))
                    earned = index < stage
                    current = index == stage and stage < total
                    path.append({
                        "number": index + 1,
                        "name": step["name"],
                        "state": "completed" if earned else "current" if current else "upcoming",
                        "requirements": requirements,
                        "requirements_met": all(req["met"] for req in requirements),
                        "cost": {
                            "gil": {"required": gil, "owned": int(player["gil"]), "met": int(player["gil"]) >= gil},
                            "hunt_seals": {"required": seals, "owned": int(player["hunt_seals"]), "met": int(player["hunt_seals"]) >= seals},
                            "materials": materials,
                        },
                        "costs_met": costs_met,
                        "ready": bool(current and costs_met and all(req["met"] for req in requirements)),
                        "reward": reward_info(step["reward_item"]),
                    })
                ready = bool(stage < total and path[stage]["ready"])
                status = ("complete" if stage >= total else "ready" if ready
                          else "not_started" if stage == 0 else "in_progress")
                current_reward = path[stage - 1]["reward"]["name"] if stage else None
                relics.append({
                    "id": relic["id"],
                    "name": relic["name"],
                    "description": relic.get("description") or "",
                    "job": job.get("name", relic["job_id"]),
                    "job_id": relic["job_id"],
                    "job_level": job_level,
                    "stage": stage,
                    "total_stages": total,
                    "completed": stage >= total,
                    "completed_at": row["completed_at"] if row else None,
                    "status": status,
                    "ready": ready,
                    "current_reward": current_reward,
                    "next_stage": path[stage]["name"] if stage < total else None,
                    "final_reward": path[-1]["reward"] if path else None,
                    "stages": [s["name"] for s in relic.get("stages", [])],
                    "path": path,
                })
            return {
                "player": self._public_identity(player),
                "summary": {
                    "total": len(relics),
                    "complete": sum(int(r["completed"]) for r in relics),
                    "ready": sum(int(r["ready"]) for r in relics),
                    "in_progress": sum(int(r["status"] == "in_progress") for r in relics),
                    "earned_stages": sum(r["stage"] for r in relics),
                    "total_stages": sum(r["total_stages"] for r in relics),
                },
                "relics": relics,
            }

    def _achievement_value(self, conn: sqlite3.Connection, player: sqlite3.Row, condition: dict[str, Any]) -> int:
        player_id = player["twitch_id"]
        kind = condition.get("type")
        if kind == "character_level":
            return int(player["level"])
        if kind == "stat":
            return int(player[condition["field"]])
        if kind == "gil":
            return int(player["gil"])
        if kind == "job_level":
            if condition.get("job_id"):
                row = conn.execute(
                    "SELECT level FROM player_jobs WHERE player_id=? AND job_id=?",
                    (player_id, condition["job_id"]),
                ).fetchone()
                return int(row["level"]) if row else 0
            row = conn.execute(
                "SELECT COALESCE(MAX(level),0) AS n FROM player_jobs WHERE player_id=?",
                (player_id,),
            ).fetchone()
            return int(row["n"] or 0)
        if kind == "bestiary_unique":
            row = conn.execute("SELECT COUNT(*) AS n FROM bestiary WHERE player_id=?", (player_id,)).fetchone()
            return int(row["n"] or 0)
        if kind == "monster_kills":
            row = conn.execute(
                "SELECT defeats FROM bestiary WHERE player_id=? AND monster_id=?",
                (player_id, condition["monster_id"]),
            ).fetchone()
            return int(row["defeats"]) if row else 0
        if kind == "hunt_total":
            row = conn.execute(
                "SELECT COALESCE(SUM(clears),0) AS n FROM player_hunts WHERE player_id=?",
                (player_id,),
            ).fetchone()
            return int(row["n"] or 0)
        if kind in {"hunt_rank_clears", "hunt_rank_total"}:
            rows = conn.execute(
                "SELECT hunt_id, clears FROM player_hunts WHERE player_id=? AND clears>0",
                (player_id,),
            ).fetchall()
            matches = [row for row in rows if row["hunt_id"] in self.data.hunts and self.data.hunts[row["hunt_id"]]["rank"] == condition["rank"]]
            if kind == "hunt_rank_clears":
                return len(matches)
            return sum(int(row["clears"]) for row in matches)
        if kind == "mastery_count":
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM player_jobs WHERE player_id=? AND level>=50",
                (player_id,),
            ).fetchone()
            return int(row["n"] or 0)
        if kind == "quest_count":
            row = conn.execute("SELECT COUNT(*) AS n FROM player_quests WHERE player_id=?", (player_id,)).fetchone()
            return int(row["n"] or 0)
        if kind == "record_stat":
            metric = str(condition["metric"])
            transaction_metrics = {
                "gil_earned": ("gil", ">"),
                "gil_spent": ("gil", "<"),
                "items_acquired": ("item", ">"),
                "items_spent": ("item", "<"),
                "hunt_seals_earned": ("hunt_seals", ">"),
                "hunt_seals_spent": ("hunt_seals", "<"),
            }
            if metric in transaction_metrics:
                asset_kind, direction = transaction_metrics[metric]
                amount_sql = "SUM(amount)" if direction == ">" else "-SUM(amount)"
                row = conn.execute(
                    f"SELECT COALESCE({amount_sql},0) AS value FROM transactions WHERE player_id=? AND kind=? AND amount {direction} 0",
                    (player_id, asset_kind),
                ).fetchone()
                return int(row["value"] or 0) if row else 0
            row = conn.execute(
                "SELECT value FROM player_record_stats WHERE player_id=? AND metric=?",
                (player_id, metric),
            ).fetchone()
            return int(row["value"]) if row else 0
        if kind == "monster_record_defeats":
            row = conn.execute(
                "SELECT defeats FROM player_monster_records WHERE player_id=? AND monster_id=?",
                (player_id, condition["monster_id"]),
            ).fetchone()
            return int(row["defeats"]) if row else 0
        if kind == "boss_clear":
            row = conn.execute(
                "SELECT clears FROM player_boss_clears WHERE player_id=? AND boss_id=?",
                (player_id, condition["boss_id"]),
            ).fetchone()
            return int(row["clears"]) if row else 0
        if kind == "boss_unique":
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM player_boss_clears WHERE player_id=? AND clears>0",
                (player_id,),
            ).fetchone()
            return int(row["n"] or 0)
        if kind == "job_battles":
            if condition.get("job_id"):
                row = conn.execute(
                    "SELECT battles FROM player_job_records WHERE player_id=? AND job_id=?",
                    (player_id, condition["job_id"]),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COALESCE(MAX(battles),0) AS battles FROM player_job_records WHERE player_id=?",
                    (player_id,),
                ).fetchone()
            return int(row["battles"] or 0) if row else 0
        if kind == "gold_saucer_record":
            return int(gold_saucer_record_value(conn, player_id, str(condition.get("metric") or "")))
        if kind == "achievement_category_count":
            category = str(condition.get("category") or "")
            ids = [str(a["id"]) for a in self.data.achievements.values() if str(a.get("category") or "") == category]
            if not ids:
                return 0
            placeholders = ",".join("?" for _ in ids)
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM achievements WHERE player_id=? AND achievement_id IN ({placeholders})",
                (player_id, *ids),
            ).fetchone()
            return int(row["n"] or 0) if row else 0
        if kind == "hunt_repeat_max":
            row = conn.execute("SELECT COALESCE(MAX(clears),0) AS n FROM player_hunts WHERE player_id=?", (player_id,)).fetchone()
            return int(row["n"] or 0) if row else 0
        if kind == "inventory_total":
            row = conn.execute("SELECT COALESCE(SUM(quantity),0) AS n FROM inventory WHERE player_id=?", (player_id,)).fetchone()
            return int(row["n"] or 0) if row else 0
        if kind == "chocobo_level":
            row = conn.execute("SELECT xp FROM player_chocobos WHERE player_id=? AND registered_at IS NOT NULL", (player_id,)).fetchone()
            if not row:
                return 0
            level, _current, _next = chocobo_level_from_total_xp(int(row["xp"] or 0))
            return int(level)
        if kind == "ventures":
            return int(player["ventures"] or 0)
        if kind == "hunt_clear":
            row = conn.execute(
                "SELECT clears FROM player_hunts WHERE player_id=? AND hunt_id=?",
                (player_id, condition["hunt_id"]),
            ).fetchone()
            return int(row["clears"] or 0) if row else 0
        if kind == "quest_complete":
            row = conn.execute(
                "SELECT 1 FROM player_quests WHERE player_id=? AND quest_id=?",
                (player_id, condition["quest_id"]),
            ).fetchone()
            return 1 if row else 0
        if kind == "expedition_region_progress":
            row = conn.execute(
                "SELECT progress FROM player_region_exploration WHERE player_id=? AND region_id=?",
                (player_id, str(condition.get("region_id") or "")),
            ).fetchone()
            return int(row["progress"] or 0) if row else 0
        if kind == "expedition_regions_mastered":
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM player_region_exploration WHERE player_id=? AND progress>=100",
                (player_id,),
            ).fetchone()
            return int(row["n"] or 0) if row else 0
        if kind == "item_quantity":
            row = conn.execute(
                "SELECT quantity FROM inventory WHERE player_id=? AND item_id=?",
                (player_id, condition["item_id"]),
            ).fetchone()
            return int(row["quantity"] or 0) if row else 0
        if kind == "hunt_seals":
            return int(player["hunt_seals"] or 0)
        if kind == "item_upgrade":
            row = conn.execute(
                "SELECT upgrade_level FROM item_upgrades WHERE player_id=? AND item_id=?",
                (player_id, condition["item_id"]),
            ).fetchone()
            return int(row["upgrade_level"] or 0) if row else 0
        if kind == "relic_complete":
            row = conn.execute(
                "SELECT stage FROM player_relics WHERE player_id=? AND relic_id=?",
                (player_id, condition["relic_id"]),
            ).fetchone()
            relic = self.data.relics.get(condition["relic_id"])
            return 1 if row and relic and int(row["stage"] or 0) >= len(relic.get("stages", [])) else 0
        return 0

    def achievements(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            player_id = player["twitch_id"]
            unlocked_rows = conn.execute(
                "SELECT achievement_id, unlocked_at FROM achievements WHERE player_id=?",
                (player_id,),
            ).fetchall()
            unlocked = {row["achievement_id"]: row["unlocked_at"] for row in unlocked_rows}
            title_rows = conn.execute(
                "SELECT title_id, unlocked_at FROM player_titles WHERE player_id=? ORDER BY unlocked_at DESC",
                (player_id,),
            ).fetchall()
            earned_titles = {row["title_id"]: row["unlocked_at"] for row in title_rows}
            entries = []
            category_summary: dict[str, dict[str, int]] = {}
            earned_points = 0
            total_points = 0
            for achievement in self.data.achievements.values():
                is_unlocked = achievement["id"] in unlocked
                secret = bool(achievement.get("secret"))
                value = self._achievement_value(conn, player, achievement.get("condition", {}))
                target = int(achievement.get("condition", {}).get("amount", 1))
                points = int(achievement.get("points", 0))
                total_points += points
                if is_unlocked:
                    earned_points += points
                category = achievement.get("category", "General")
                bucket = category_summary.setdefault(category, {"unlocked": 0, "total": 0, "points": 0})
                bucket["total"] += 1
                if is_unlocked:
                    bucket["unlocked"] += 1
                    bucket["points"] += points
                title = self.data.titles.get(achievement.get("reward_title"))
                display_name = achievement.get("reveal_name", achievement["name"]) if is_unlocked else achievement["name"]
                description = achievement["description"]
                if secret and not is_unlocked:
                    display_name = "Secret Achievement"
                    description = "Hidden until unlocked. The Guild refuses to spoil this particular mistake."
                hidden_secret = secret and not is_unlocked
                # Achievements are permanent once earned.  For reversible
                # requirements (current Gil, inventory held, etc.), never show
                # an unlocked card as partially complete after the value falls.
                display_value = target if is_unlocked else min(value, target)
                progress = {
                    "value": 0 if hidden_secret else display_value,
                    "raw_value": 0 if hidden_secret else value,
                    "target": 0 if hidden_secret else target,
                    "percent": 0 if hidden_secret else (100 if is_unlocked or target <= 0 else min(100, round(value / target * 100, 1))),
                    "hidden": hidden_secret,
                }
                entries.append(
                    {
                        "id": achievement["id"],
                        "name": display_name,
                        "description": description,
                        "unlocked": is_unlocked,
                        "unlocked_at": unlocked.get(achievement["id"]),
                        "category": category,
                        "tier": achievement.get("tier", "bronze"),
                        "points": points,
                        "secret": secret,
                        "progress": progress,
                        "reward_title": None if hidden_secret else (title["name"] if title else None),
                        "reward_title_meta": None if hidden_secret else ({
                            "rarity": title.get("rarity", "common"),
                            "category": title.get("category", "General"),
                        } if title else None),
                    }
                )
            tier_order = {"crystal": 0, "gold": 1, "silver": 2, "bronze": 3}
            entries.sort(
                key=lambda a: (not a["unlocked"], tier_order.get(a["tier"], 9), a["category"], a["name"].lower())
            )
            titles = []
            equipped_name = player["title"]
            for title in self.data.titles.values():
                is_unlocked = title["id"] in earned_titles
                titles.append(
                    {
                        "id": title["id"],
                        "name": title["name"],
                        "description": title["description"],
                        "category": title.get("category", "General"),
                        "rarity": title.get("rarity", "common"),
                        "source": title.get("source", "Progression"),
                        "unlocked": is_unlocked,
                        "unlocked_at": earned_titles.get(title["id"]),
                        "equipped": title["name"] == equipped_name,
                    }
                )
            # Reserved Moment Titles are not part of the public legacy catalog.
            # Reveal only a title whose Moment was genuinely settled for THIS player
            # and whose ownership was committed to player_titles.
            owned_moment_titles = {
                str(row["title_id"]) for row in conn.execute(
                    "SELECT title_id FROM player_moment_unlocks WHERE player_id=?", (player_id,)
                ).fetchall()
            }
            for title_id in owned_moment_titles & earned_titles.keys() & self.data.moment_titles.keys():
                title = self.data.moment_titles[title_id]
                titles.append({
                    "id": title_id, "name": title["name"], "description": title["description"],
                    "category": title.get("category", "Moments"),
                    "rarity": title.get("rarity", "common"), "source": "Moment",
                    "unlocked": True, "unlocked_at": earned_titles[title_id],
                    "equipped": title["name"] == equipped_name,
                })
            rarity_order = {"legendary": 0, "epic": 1, "rare": 2, "uncommon": 3, "common": 4}
            titles.sort(key=lambda t: (not t["unlocked"], rarity_order.get(t["rarity"], 9), t["name"].lower()))
            return {
                "player": self._public_identity(player),
                "summary": {
                    "unlocked": len(unlocked),
                    "total": len(entries),
                    "points": earned_points,
                    "points_total": total_points,
                    "categories": category_summary,
                    "titles_unlocked": sum(1 for title in titles if title["unlocked"]),
                    "titles_total": len(titles),
                    "equipped_title": equipped_name,
                },
                "achievements": entries,
                "titles": titles,
            }

    def trophies(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            player_id = str(player["twitch_id"])
            try:
                rows = conn.execute(
                    "SELECT trophy_id,unlock_source,unlocked_at,seen_at FROM player_trophies WHERE player_id=? ORDER BY unlocked_at,trophy_id",
                    (player_id,),
                ).fetchall()
            except sqlite3.Error:
                # Upgrade-order compatibility while a schema-19 database is
                # waiting for the Bot's additive schema-20 migration.
                rows = []
            owned_ids = {str(row["trophy_id"]) for row in rows}
            # These two secret Hall slots are filled from authoritative Moment
            # trophy receipts. Names, triggers, IDs and art stay server-side
            # until the actual trophy is owned by THIS player.
            moment_slots = []
            for position, trophy in enumerate(
                (row for row in TROPHY_CATALOG if row["unlock"]["kind"] == "moment"), start=1
            ):
                if trophy["id"] in owned_ids:
                    moment_slots.append({
                        "id": trophy["id"], "name": trophy["name"],
                        "description": trophy["description"],
                        "category": trophy["category"],
                        "requirement": trophy["requirement"],
                        "art": trophy["art"], "locked_art": trophy["locked_art"],
                        "secret": True, "earned": True,
                    })
                else:
                    moment_slots.append({
                        "id": f"sealed_trophy_slot_{position:02d}",
                        "name": "Undiscovered Trophy",
                        "description": "Its story has yet to be written.",
                        "category": "mystery", "requirement": None,
                        "art": None, "locked_art": None,
                        "secret": True, "earned": False,
                    })
            try:
                from .seasonal_events import public_snapshot
                seasonal = public_snapshot(conn, player_id)
            except sqlite3.Error:
                seasonal = {}
            seasonal_trophies = [{**row, "category": "seasonal", "requirement": row["description"], "secret": False}
                                 for row in seasonal.get("trophies", [])]
            seasonal_unlocked = [{"id": row["id"], "unlocked_at": row["unlocked_at"],
                                  "unlock_source": "seasonal", "seen_at": None}
                                 for row in seasonal_trophies if row.get("unlocked_at")]
            return {
                "seasonal_trophies": seasonal_trophies,
                "keepsakes": seasonal.get("keepsakes", []),
                "player": self._public_identity(player),
                "moment_slots": moment_slots,
                "unlocked": [
                    {
                        "id": str(row["trophy_id"]),
                        "unlock_source": str(row["unlock_source"] or "reconciliation"),
                        "unlocked_at": row["unlocked_at"],
                        "seen_at": row["seen_at"],
                    }
                    for row in rows
                ] + seasonal_unlocked,
            }


    def seasonal(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            try:
                from .seasonal_events import public_snapshot
                return {"player": self._public_identity(player), "seasonal": public_snapshot(conn, str(player["twitch_id"]))}
            except sqlite3.Error:
                return {"player": self._public_identity(player), "seasonal": {"state":"disabled","active":False,"redemption":False}}

    def records(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            player_id = player["twitch_id"]
            stat_rows = conn.execute(
                "SELECT metric, value FROM player_record_stats WHERE player_id=?",
                (player_id,),
            ).fetchall()
            stats = {row["metric"]: int(row["value"]) for row in stat_rows}

            boss_rows = conn.execute(
                """
                SELECT boss_id, clears, best_damage, last_cleared_at
                FROM player_boss_clears WHERE player_id=?
                """,
                (player_id,),
            ).fetchall()
            bosses = []
            for row in boss_rows:
                boss = self.data.bosses.get(row["boss_id"])
                bosses.append(
                    {
                        "id": row["boss_id"],
                        "name": boss["name"] if boss else row["boss_id"],
                        "tier": boss.get("tier", "boss") if boss else "boss",
                        "clears": int(row["clears"]),
                        "best_damage": int(row["best_damage"]),
                        "last_cleared_at": row["last_cleared_at"],
                    }
                )
            bosses.sort(key=lambda b: (-b["clears"], -b["best_damage"], b["name"].lower()))
            boss_history = {row["id"]: row for row in bosses}
            trials = []
            for boss_id, boss in self.data.bosses.items():
                if str(boss.get("encounter_type") or "").lower() != "trial":
                    continue
                prefix = f"trial_{boss_id}_"
                legacy = boss_history.get(boss_id) or {}
                clears = int(legacy.get("clears", 0) or 0)
                wipes = int(stats.get(prefix + "wipes", 0) or 0)
                fastest = int(stats.get(prefix + "fastest_rounds", 0) or 0)
                best_damage = max(int(legacy.get("best_damage", 0) or 0), int(stats.get(prefix + "best_damage", 0) or 0))
                if clears >= 10:
                    repeat_mastery = "Mastered"
                    next_clear_goal = None
                elif clears >= 5:
                    repeat_mastery = "Veteran"
                    next_clear_goal = 10
                elif clears >= 3:
                    repeat_mastery = "Seasoned"
                    next_clear_goal = 5
                elif clears >= 1:
                    repeat_mastery = "Proven"
                    next_clear_goal = 3
                else:
                    repeat_mastery = "Uncleared"
                    next_clear_goal = 1
                trials.append({
                    "id": boss_id,
                    "name": boss.get("name", boss_id),
                    "encounter_name": boss.get("encounter_name") or boss.get("name", boss_id),
                    "recommended_level": int(boss.get("recommended_level", 1) or 1),
                    "capstone": str(boss.get("raid_script") or "") == "bahamut_final_coil",
                    "clears": clears,
                    "wipes": wipes,
                    "attempts": clears + wipes,
                    "fastest_clear_rounds": fastest or None,
                    "best_score": int(stats.get(prefix + "best_score", 0) or 0),
                    "best_damage": best_damage,
                    "best_healing": int(stats.get(prefix + "best_healing", 0) or 0),
                    "best_mitigation": int(stats.get(prefix + "best_mitigation", 0) or 0),
                    "last_cleared_at": legacy.get("last_cleared_at"),
                    "repeat_mastery": repeat_mastery,
                    "next_clear_goal": next_clear_goal,
                })
            trials.sort(key=lambda row: (row["recommended_level"], row["name"].lower()))
            unique_trial_clears = sum(1 for row in trials if row["clears"] > 0)
            if unique_trial_clears >= len(trials) and trials:
                trial_rank = "Coilbreaker"
                next_trial_goal = None
            elif unique_trial_clears >= 6:
                trial_rank = "Primal Conqueror"
                next_trial_goal = len(trials)
            elif unique_trial_clears >= 3:
                trial_rank = "Trial Vanguard"
                next_trial_goal = 6
            elif unique_trial_clears >= 1:
                trial_rank = "Trial Initiate"
                next_trial_goal = 3
            else:
                trial_rank = "Unproven"
                next_trial_goal = 1
            trial_summary = {
                "rank": trial_rank,
                "unique_clears": unique_trial_clears,
                "total_trials": len(trials),
                "total_clears": sum(row["clears"] for row in trials),
                "tracked_wipes": sum(row["wipes"] for row in trials),
                "best_score": max((row["best_score"] for row in trials), default=0),
                "mastered_trials": sum(1 for row in trials if row.get("repeat_mastery") == "Mastered"),
                "next_unique_clear_goal": next_trial_goal,
            }

            economy = conn.execute(
                """
                SELECT
                  COALESCE(SUM(CASE WHEN kind='gil' AND amount>0 THEN amount ELSE 0 END),0) AS gil_earned,
                  COALESCE(-SUM(CASE WHEN kind='gil' AND amount<0 THEN amount ELSE 0 END),0) AS gil_spent,
                  COALESCE(SUM(CASE WHEN kind='item' AND amount>0 THEN amount ELSE 0 END),0) AS items_acquired,
                  COALESCE(-SUM(CASE WHEN kind='item' AND amount<0 THEN amount ELSE 0 END),0) AS items_spent,
                  COALESCE(SUM(CASE WHEN kind='hunt_seals' AND amount>0 THEN amount ELSE 0 END),0) AS seals_earned,
                  COALESCE(-SUM(CASE WHEN kind='hunt_seals' AND amount<0 THEN amount ELSE 0 END),0) AS seals_spent
                FROM transactions WHERE player_id=?
                """,
                (player_id,),
            ).fetchone()
            hunt_row = conn.execute(
                "SELECT COALESCE(SUM(clears),0) AS n FROM player_hunts WHERE player_id=?",
                (player_id,),
            ).fetchone()
            achievement_row = conn.execute(
                "SELECT COUNT(*) AS n FROM achievements WHERE player_id=?",
                (player_id,),
            ).fetchone()
            bestiary_row = conn.execute(
                "SELECT COUNT(*) AS n FROM bestiary WHERE player_id=?",
                (player_id,),
            ).fetchone()
            mastered_row = conn.execute(
                "SELECT COUNT(*) AS n FROM player_jobs WHERE player_id=? AND level>=50",
                (player_id,),
            ).fetchone()
            inventory_row = conn.execute(
                "SELECT COUNT(*) AS n FROM inventory WHERE player_id=? AND quantity>0",
                (player_id,),
            ).fetchone()

            favorite_job_row = conn.execute(
                """
                SELECT job_id, battles, victories, damage_dealt, healing_done, boss_damage
                FROM player_job_records WHERE player_id=?
                ORDER BY battles DESC, victories DESC, job_id LIMIT 1
                """,
                (player_id,),
            ).fetchone()
            favorite_job = None
            if favorite_job_row:
                job = self.data.jobs.get(favorite_job_row["job_id"])
                favorite_job = {
                    "id": favorite_job_row["job_id"],
                    "name": job["name"] if job else favorite_job_row["job_id"],
                    "battles": int(favorite_job_row["battles"]),
                    "victories": int(favorite_job_row["victories"]),
                    "damage_dealt": int(favorite_job_row["damage_dealt"]),
                    "healing_done": int(favorite_job_row["healing_done"]),
                    "boss_damage": int(favorite_job_row["boss_damage"]),
                }
            elif player["current_job"] in self.data.jobs:
                job = self.data.jobs[player["current_job"]]
                current_job_row = conn.execute(
                    "SELECT level FROM player_jobs WHERE player_id=? AND job_id=?",
                    (player_id, player["current_job"]),
                ).fetchone()
                favorite_job = {
                    "id": player["current_job"],
                    "name": job["name"],
                    "battles": 0,
                    "victories": 0,
                    "damage_dealt": 0,
                    "healing_done": 0,
                    "boss_damage": 0,
                    "job_level": int(current_job_row["level"]) if current_job_row else 0,
                }

            victim_row = conn.execute(
                """
                SELECT monster_id, defeats FROM bestiary WHERE player_id=?
                ORDER BY defeats DESC, monster_id LIMIT 1
                """,
                (player_id,),
            ).fetchone()
            most_defeated = None
            if victim_row:
                monster = self.data.monsters.get(victim_row["monster_id"])
                most_defeated = {
                    "id": victim_row["monster_id"],
                    "name": monster["name"] if monster else victim_row["monster_id"],
                    "defeats": int(victim_row["defeats"]),
                }

            nemesis_row = conn.execute(
                """
                SELECT monster_id, victories, defeats, damage_dealt, damage_taken, best_hit
                FROM player_monster_records
                WHERE player_id=? AND defeats>0
                ORDER BY defeats DESC, victories ASC, monster_id LIMIT 1
                """,
                (player_id,),
            ).fetchone()
            nemesis = None
            if nemesis_row:
                monster = self.data.monsters.get(nemesis_row["monster_id"])
                nemesis = {
                    "id": nemesis_row["monster_id"],
                    "name": monster["name"] if monster else nemesis_row["monster_id"],
                    "victories": int(nemesis_row["victories"]),
                    "knockouts": int(nemesis_row["defeats"]),
                    "damage_dealt": int(nemesis_row["damage_dealt"]),
                    "damage_taken": int(nemesis_row["damage_taken"]),
                    "best_hit": int(nemesis_row["best_hit"]),
                }

            total_boss_clears = sum(b["clears"] for b in bosses)
            best_boss_damage = max((b["best_damage"] for b in bosses), default=0)
            return {
                "player": self._public_identity(player),
                "career": {
                    "ventures": int(player["ventures"]),
                    "monsters_defeated": int(player["monsters_defeated"]),
                    "hunt_clears": int(hunt_row["n"] or 0),
                    "boss_clears": total_boss_clears,
                    "deaths": int(player["deaths"]),
                    "rests": int(player["rests"]),
                    "party_encounters": int(player["party_encounters"]),
                    "raid_revives": int(player["raid_revives"]),
                    "limit_breaks": int(player["limit_breaks"]),
                    "summons_called": stats.get("summons_called", 0),
                    "crafts": int(player["crafts"]),
                    "forge_upgrades": int(player["forge_upgrades"]),
                    "relics_completed": int(player["relics_completed"]),
                },
                "combat": {
                    "battles": stats.get("battles", 0),
                    "damage_dealt": stats.get("damage_dealt", 0),
                    "damage_taken": stats.get("damage_taken", 0),
                    "healing_done": stats.get("healing_done", 0),
                    "damage_mitigated": stats.get("damage_mitigated", 0),
                    "best_hit": stats.get("best_hit", 0),
                    "raid_damage": stats.get("raid_damage", 0),
                    "raid_wins": stats.get("raid_wins", 0),
                    "raid_wipes": stats.get("raid_wipes", 0),
                    "best_boss_damage": best_boss_damage,
                },
                "economy": {
                    "gil_earned": int(economy["gil_earned"] or 0),
                    "gil_spent": int(economy["gil_spent"] or 0),
                    "items_acquired": int(economy["items_acquired"] or 0),
                    "items_spent": int(economy["items_spent"] or 0),
                    "hunt_seals_earned": int(economy["seals_earned"] or 0),
                    "hunt_seals_spent": int(economy["seals_spent"] or 0),
                },
                "progression": {
                    "jobs_mastered": int(mastered_row["n"] or 0),
                    "bestiary_discovered": int(bestiary_row["n"] or 0),
                    "bestiary_total": len(self.data.monsters),
                    "achievements_unlocked": int(achievement_row["n"] or 0),
                    "achievements_total": len(self.data.achievements),
                    "inventory_stacks": int(inventory_row["n"] or 0),
                },
                "rivalries": {
                    "favorite_job": favorite_job,
                    "most_defeated": most_defeated,
                    "nemesis": nemesis,
                },
                "bosses": bosses,
                "trial_summary": trial_summary,
                "trials": trials,
                "personal_records": project_personal_records(conn, str(player_id), self.data, stats),
                "moments": self._moments_for_player(conn, str(player_id)),
            }

    def _moments_for_player(self, conn: sqlite3.Connection, player_id: str) -> dict[str, Any]:
        """Read-only, spoiler-safe projection. Never invoke award or reconciliation here."""
        owned = {
            str(row["moment_id"]): row for row in conn.execute(
                "SELECT moment_id,title_id,earned_at,historical FROM player_moment_unlocks "
                "WHERE player_id=?", (player_id,),
            ).fetchall()
            if row["moment_id"] in self.data.moments
        }
        entries = public_moments_view(self.data.moments, self.data.moment_titles, set(owned))
        actual_trophies = {
            str(row["trophy_id"]) for row in conn.execute(
                "SELECT trophy_id FROM player_trophies WHERE player_id=? AND trophy_id LIKE 'moment_trophy_%'",
                (player_id,),
            ).fetchall()
        }
        for entry in entries:
            unlock = owned.get(entry["id"])
            entry["unlocked_at"] = unlock["earned_at"] if unlock else None
            entry["historical"] = bool(unlock["historical"]) if unlock else False
            candidate_id = entry.pop("trophy_candidate_id", None)
            # A trophy label appears only after a verified Moment *and* its own
            # durable Hall receipt. Unowned secret slots never expose an ID.
            if unlock and candidate_id in actual_trophies:
                trophy = TROPHIES_BY_ID[candidate_id]
                entry["trophy_reward"] = {"id": candidate_id, "name": trophy["name"]}
            else:
                entry["trophy_reward"] = None
        return {
            "summary": {"unlocked": len(owned), "total": len(self.data.moments)},
            "entries": entries,
            "scope_note": "Moments are awarded once, after an adventure has actually finished.",
        }

    def _find_player(self, conn: sqlite3.Connection, key: str) -> sqlite3.Row | None:
        clean = unquote(key).strip()
        return conn.execute(
            """
            SELECT * FROM players
            WHERE lower(username)=lower(?) OR lower(display_name)=lower(?) OR twitch_id=?
            LIMIT 1
            """,
            (clean, clean, clean),
        ).fetchone()

    def _public_identity(self, player: sqlite3.Row) -> dict[str, Any]:
        return {
            "username": player["username"],
            "display_name": player["display_name"],
            "level": int(player["level"]),
            "title": player["title"],
        }

    def _status(self, player: sqlite3.Row, max_hp: int | None = None) -> dict[str, Any]:
        now = int(time.time())
        camp_until = int(player["camp_until"] or 0)
        if camp_until > now:
            return {
                "state": "resting",
                "label": "Resting at Camp",
                "remaining_seconds": camp_until - now,
                "until": camp_until,
            }
        if camp_until and camp_until <= now:
            return {"state": "ready_after_rest", "label": "Rest Complete", "remaining_seconds": 0}
        if int(player["current_hp"] or 0) <= 0 and player["current_job"] != "adventurer":
            return {"state": "ko", "label": "KO'd", "remaining_seconds": 0}
        return {"state": "ready", "label": "Ready", "remaining_seconds": 0}

    def _effects(self, conn: sqlite3.Connection, player_id: str, job: dict[str, Any]) -> dict[str, float]:
        effects: dict[str, float] = {}
        row = conn.execute(
            "SELECT level FROM player_jobs WHERE player_id=? AND job_id=?",
            (player_id, job["id"]),
        ).fetchone()
        jlevel = int(row["level"]) if row else 0
        for ability in job.get("abilities", []):
            if jlevel >= int(ability["level"]):
                for key, value in ability.get("effects", {}).items():
                    effects[key] = effects.get(key, 0.0) + float(value)
        mastery_rows = conn.execute(
            "SELECT slot, job_id FROM mastery_slots WHERE player_id=? ORDER BY slot",
            (player_id,),
        ).fetchall()
        for mastery_row in mastery_rows:
            source = self.data.jobs.get(mastery_row["job_id"])
            if not source:
                continue
            level_row = conn.execute(
                "SELECT level FROM player_jobs WHERE player_id=? AND job_id=?",
                (player_id, mastery_row["job_id"]),
            ).fetchone()
            if not level_row or int(level_row["level"]) < 50:
                continue
            for key, value in source.get("mastery", {}).get("effects", {}).items():
                effects[key] = effects.get(key, 0.0) + float(value)
        return effects

    def _stats(
        self,
        conn: sqlite3.Connection,
        player: sqlite3.Row,
        job: dict[str, Any] | None,
        equipment: list[dict[str, Any]],
    ) -> dict[str, int]:
        if not job:
            return {"str": 10, "vit": 10, "mag": 10, "spr": 10, "dex": 10, "lck": 8, "hp": 100, "attack": 0, "magic_power": 0}
        level = int(player["level"])
        growth = job["growth"]
        stats = {
            "str": 10 + int(level * growth["str"]),
            "vit": 10 + int(level * growth["vit"]),
            "mag": 10 + int(level * growth["mag"]),
            "spr": 10 + int(level * growth["spr"]),
            "dex": 10 + int(level * growth["dex"]),
            "lck": 8 + int(level * growth["lck"]),
            "hp": 90 + int(level * (8 + growth["vit"] * 4)),
            "attack": 0,
            "magic_power": 0,
        }
        effects = self._effects(conn, player["twitch_id"], job)
        for entry in equipment:
            if not entry.get("id"):
                continue
            item = self.data.items.get(entry["id"])
            if not item:
                continue
            if item.get("allowed_jobs") and job["id"] not in item["allowed_jobs"]:
                continue
            scale = 1 + self._forge_bonus * int(entry.get("upgrade_level", 0))
            for key, value in item.get("bonuses", {}).items():
                if key in stats:
                    stats[key] += int(round(float(value) * scale))
        stats["hp"] = int(stats["hp"] * (1 + effects.get("hp_mult", 0)))
        stats["mag"] = int(stats["mag"] * (1 + effects.get("mag_mult", 0)))
        return stats

    def _equipment(
        self,
        conn: sqlite3.Connection,
        player_id: str,
        job: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        row = conn.execute("SELECT * FROM equipment WHERE player_id=?", (player_id,)).fetchone()
        slots = [
            ("weapon", row["weapon_id"] if row else None),
            ("armor", row["armor_id"] if row else None),
            ("accessory", row["accessory_id"] if row else None),
        ]
        result = []
        for slot, item_id in slots:
            item = self.data.items.get(item_id) if item_id else None
            upgrade_row = None
            if item_id:
                upgrade_row = conn.execute(
                    "SELECT upgrade_level FROM item_upgrades WHERE player_id=? AND item_id=?",
                    (player_id, item_id),
                ).fetchone()
            upgrade = int(upgrade_row["upgrade_level"]) if upgrade_row else 0
            raw_bonuses = item.get("bonuses", {}) if item else {}
            scale = 1 + self._forge_bonus * upgrade
            effective_bonuses = {
                key: int(round(float(value) * scale))
                for key, value in raw_bonuses.items()
            }
            result.append(
                {
                    "slot": slot,
                    "id": item_id,
                    "name": item["name"] if item else "—",
                    "rarity": item.get("rarity", "common") if item else "common",
                    "type": item.get("type", slot) if item else slot,
                    "bonuses": raw_bonuses,
                    "effective_bonuses": effective_bonuses,
                    "upgrade_level": upgrade,
                    "min_level": int(item.get("min_level", 1) or 1) if item else 1,
                    "allowed_job_ids": [j for j in item.get("allowed_jobs", []) if j in self.data.jobs] if item else [],
                    "allowed_jobs": [self.data.jobs[j]["name"] for j in item.get("allowed_jobs", []) if j in self.data.jobs] if item else [],
                    "compatible": not item
                    or not item.get("allowed_jobs")
                    or (job is not None and job["id"] in item.get("allowed_jobs", [])),
                }
            )
        return result

    def _mastery_slots(self, conn: sqlite3.Connection, player_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT slot, job_id FROM mastery_slots WHERE player_id=? ORDER BY slot",
            (player_id,),
        ).fetchall()
        result = []
        for row in rows:
            job = self.data.jobs.get(row["job_id"])
            result.append(
                {
                    "slot": int(row["slot"]),
                    "job_id": row["job_id"],
                    "job_name": job["name"] if job else row["job_id"],
                    "name": job.get("mastery", {}).get("name", "Mastery") if job else "Mastery",
                    "description": job.get("mastery", {}).get("description", "") if job else "",
                }
            )
        return result

    def _counts(self, conn: sqlite3.Connection, player_id: str) -> dict[str, int]:
        bestiary = conn.execute("SELECT COUNT(*) AS n FROM bestiary WHERE player_id=?", (player_id,)).fetchone()["n"]
        achievements = conn.execute("SELECT COUNT(*) AS n FROM achievements WHERE player_id=?", (player_id,)).fetchone()["n"]
        hunts = conn.execute("SELECT COALESCE(SUM(clears),0) AS n FROM player_hunts WHERE player_id=?", (player_id,)).fetchone()["n"]
        jobs = conn.execute("SELECT COUNT(*) AS n FROM player_jobs WHERE player_id=?", (player_id,)).fetchone()["n"]
        mastered = conn.execute("SELECT COUNT(*) AS n FROM player_jobs WHERE player_id=? AND level>=50", (player_id,)).fetchone()["n"]
        relics = conn.execute("SELECT COUNT(*) AS n FROM player_relics WHERE player_id=? AND stage>0", (player_id,)).fetchone()["n"]
        bosses = conn.execute("SELECT COALESCE(SUM(clears),0) AS n FROM player_boss_clears WHERE player_id=?", (player_id,)).fetchone()["n"]
        return {
            "bestiary": int(bestiary),
            "bestiary_total": len(self.data.monsters),
            "achievements": int(achievements),
            "achievements_total": len(self.data.achievements),
            "hunts": int(hunts),
            "jobs": int(jobs),
            "jobs_total": len(self.data.jobs),
            "mastered_jobs": int(mastered),
            "relics": int(relics),
            "relics_total": len(self.data.relics),
            "boss_clears": int(bosses),
        }

    def _recent_activity(self, conn: sqlite3.Connection, player_id: str, limit: int) -> list[dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT kind, asset_id, amount, source, created_at
            FROM transactions
            WHERE player_id=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (player_id, limit),
        ).fetchall()
        result = []
        for row in rows:
            asset_name = row["asset_id"]
            if row["kind"] == "item" and row["asset_id"] in self.data.items:
                asset_name = self.data.items[row["asset_id"]]["name"]
            result.append(
                {
                    "kind": row["kind"],
                    "asset": asset_name,
                    "amount": int(row["amount"]),
                    "source": row["source"],
                    "created_at": row["created_at"],
                }
            )
        return result

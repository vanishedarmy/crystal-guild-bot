from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import unquote

from .active_battle import battle_resource_pools, job_resource_mode
from .balance import jp_to_next, sell_value, xp_to_next
from .chocobo import TRAITS as CHOCOBO_TRAITS, level_from_total_xp as chocobo_level_from_total_xp
from .data import GameData
from .fellowship import (DEEDS, FACILITIES, GUILD_RANKS, PROJECTS, facility_effects, fellowship_level_progress, guild_rank_for_renown, weekly_orders, weekly_period_key)


SNAPSHOT_VERSION = "1.1.15-wayfarer"


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
        current_mp = 0 if max_mp <= 0 else (max_mp if raw_mp is None else max(0, min(max_mp, int(raw_mp))))
        current_ap = 0 if max_ap <= 0 else (max_ap if raw_ap is None else max(0, min(max_ap, int(raw_ap))))
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
                "SELECT name,level,xp,registered_at FROM player_chocobos WHERE player_id=?",
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
        return {
            "name": str(row["name"]),
            "level": int(level),
            "xp_current": int(xp_current),
            "xp_next": int(xp_next),
            "traits": traits,
            "registered_at": str(row["registered_at"]),
        }

    def _fellowship_member(self, conn: sqlite3.Connection, player_id: str) -> dict[str, Any]:
        try:
            row = conn.execute("SELECT * FROM fellowship_members WHERE player_id=?", (str(player_id),)).fetchone()
        except sqlite3.Error:
            row = None
        renown = int(row["renown"]) if row else 0
        return {
            "renown": renown,
            "rank": guild_rank_for_renown(renown),
            "founding_member": bool(row["founding_member"]) if row else False,
            "projects_contributed": int(row["projects_contributed"]) if row else 0,
            "gil_donated": int(row["gil_donated"]) if row else 0,
            "materials_donated": int(row["materials_donated"]) if row else 0,
            "orders_participated": int(row["orders_participated"]) if row else 0,
            "deeds_assisted": int(row["deeds_assisted"]) if row else 0,
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
                    "orders": {"period": weekly_period_key(), "orders": [], "completed": 0, "total": 0},
                    "deeds": [], "deeds_complete": 0, "leaders": [], "recent_activity": [],
                    "totals": {"gil_donated": 0, "materials_donated": 0},
                    "expedition_board_complete": False, "rank_ladder": GUILD_RANKS,
                    "effects": facility_effects({}),
                }
            level = int(state["level"] or 1)
            renown = int(state["renown"] or 0)
            tier_rows = conn.execute("SELECT facility_id,tier FROM fellowship_facilities").fetchall()
            tiers = {str(row["facility_id"]): int(row["tier"]) for row in tier_rows}
            facilities = []
            for facility_id, config in FACILITIES.items():
                tier = int(tiers.get(facility_id, 0))
                facilities.append({
                    "id": facility_id, "name": config["name"], "tier": tier,
                    "max_tier": int(config["max_tier"]), "description": config["description"],
                    "current_benefit": config["benefits"][tier - 1] if tier > 0 else "Not yet constructed",
                    "next_benefit": config["benefits"][tier] if tier < int(config["max_tier"]) else None,
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
            available = []
            for project in PROJECTS.values():
                if project.get("teaser"):
                    if expedition_done or hall < 5 or level < int(project["required_level"]):
                        continue
                else:
                    current = int(tiers.get(project["facility_id"], 0))
                    if int(project["tier"]) != current + 1:
                        continue
                    if project["facility_id"] != "guild_hall" and int(project["tier"]) > hall:
                        continue
                    if level < int(project["required_level"]):
                        continue
                available.append(project_snapshot(project["id"]) or dict(project))
            available.sort(key=lambda item: (int(item.get("tier", 0)), str(item.get("name", ""))))

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
            return {
                "level": level, "level_label": f"LVL {level}", "renown": renown,
                "level_progress": fellowship_level_progress(renown),
                "member_count": int(member_count["n"] if member_count else 0),
                "active_project": active_project, "available_projects": available, "facilities": facilities,
                "orders": {"period": period, "orders": order_items, "completed": sum(1 for item in order_items if item["complete"]), "total": len(order_items)},
                "deeds": deed_items, "deeds_complete": sum(1 for item in deed_items if item["complete"]),
                "leaders": leaders, "recent_activity": activity,
                "totals": {"gil_donated": int(totals["gil"] if totals else 0), "materials_donated": int(totals["materials"] if totals else 0)},
                "expedition_board_complete": expedition_done, "rank_ladder": GUILD_RANKS,
                "effects": facility_effects(tiers),
            }

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
            items.sort(key=lambda i: (i["type"], i["rarity"], i["name"].lower()))
            return {"player": self._public_identity(player), "items": items}

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
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            rows = conn.execute(
                "SELECT monster_id, defeats FROM bestiary WHERE player_id=?",
                (player["twitch_id"],),
            ).fetchall()
            defeated = {row["monster_id"]: int(row["defeats"]) for row in rows}
            entries = []
            for monster in self.data.monsters.values():
                defeats = defeated.get(monster["id"], 0)
                behavior = self.data.enemy_actions.get(monster["id"], {})
                profile = self.data.enemy_profiles.get(behavior.get("profile"), {})
                active_skill = behavior.get("ability") or {}
                entries.append(
                    {
                        "id": monster["id"],
                        "name": monster["name"],
                        "level": int(monster["level"]),
                        "weakness": monster.get("weakness", "—"),
                        "special": monster.get("special", "—"),
                        "combat_profile": profile.get("name", "Balanced"),
                        "active_skill": active_skill.get("name") or "Basic attacks",
                        "defeats": defeats,
                        "discovered": defeats > 0,
                    }
                )
            entries.sort(key=lambda m: (m["level"], m["name"].lower(), m["id"]))
            discovered = sum(1 for m in entries if m["discovered"])
            total_defeats = sum(m["defeats"] for m in entries)
            nemesis = max(entries, key=lambda m: m["defeats"], default=None)
            return {
                "player": self._public_identity(player),
                "summary": {
                    "discovered": discovered,
                    "total": len(entries),
                    "defeats": total_defeats,
                    "most_defeated": nemesis if nemesis and nemesis["defeats"] else None,
                },
                "monsters": entries,
            }

    def relics(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            player = self._find_player(conn, key)
            if not player:
                return None
            rows = conn.execute(
                "SELECT relic_id, stage, completed_at FROM player_relics WHERE player_id=?",
                (player["twitch_id"],),
            ).fetchall()
            progress = {row["relic_id"]: row for row in rows}
            relics = []
            for relic in self.data.relics.values():
                row = progress.get(relic["id"])
                stage = int(row["stage"]) if row else 0
                total = len(relic.get("stages", []))
                job = self.data.jobs.get(relic["job_id"])
                reward = None
                if stage > 0 and stage <= total:
                    reward_id = relic["stages"][stage - 1].get("reward_item")
                    reward = self.data.items.get(reward_id)
                relics.append(
                    {
                        "id": relic["id"],
                        "name": relic["name"],
                        "job": job["name"] if job else relic["job_id"],
                        "stage": stage,
                        "total_stages": total,
                        "completed": stage >= total,
                        "completed_at": row["completed_at"] if row else None,
                        "current_reward": reward["name"] if reward else None,
                        "stages": [s["name"] for s in relic.get("stages", [])],
                    }
                )
            return {"player": self._public_identity(player), "relics": relics}

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
                progress = {
                    "value": 0 if hidden_secret else min(value, target),
                    "raw_value": 0 if hidden_secret else value,
                    "target": 0 if hidden_secret else target,
                    "percent": 0 if hidden_secret else (100 if target <= 0 else min(100, round(value / target * 100, 1))),
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
                    "titles_unlocked": len(earned_titles),
                    "titles_total": len(titles),
                    "equipped_title": equipped_name,
                },
                "achievements": entries,
                "titles": titles,
            }

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

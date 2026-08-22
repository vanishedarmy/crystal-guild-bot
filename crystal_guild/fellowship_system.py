from __future__ import annotations

import time
from typing import Any

from .fellowship import (
    DEEDS,
    FACILITIES,
    GUILD_RANKS,
    PROJECTS,
    facility_effects,
    fellowship_level_for_renown,
    fellowship_level_progress,
    guild_rank_for_renown,
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

    def apply_jp_bonus(self, jp: int) -> int:
        bonus = self.effects()["jp_bonus"]
        return max(0, int(round(int(jp) * (1.0 + bonus))))

    def _member(self, player_id: str) -> Any:
        self.ensure_member(player_id)
        return self.db.one("SELECT * FROM fellowship_members WHERE player_id=?", (str(player_id),))

    def member_snapshot(self, player_id: str) -> dict[str, Any]:
        member = self._member(player_id)
        rank = guild_rank_for_renown(int(member["renown"]))
        return {
            "renown": int(member["renown"]),
            "rank": rank,
            "founding_member": bool(member["founding_member"]),
            "projects_contributed": int(member["projects_contributed"]),
            "gil_donated": int(member["gil_donated"]),
            "materials_donated": int(member["materials_donated"]),
            "orders_participated": int(member["orders_participated"]),
            "deeds_assisted": int(member["deeds_assisted"]),
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
        return {"period": period, "orders": result, "completed": sum(1 for item in result if item["complete"]), "total": len(result)}

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
            result.append(self.project_snapshot(project["id"]) or dict(project))
        return sorted(result, key=lambda item: (int(item.get("tier", 0)), str(item.get("name", ""))))

    def set_active_project(self, query: str) -> tuple[bool, str, dict[str, Any] | None]:
        norm = str(query or "").strip().lower().replace(" ", "_").replace("-", "_")
        available = self.available_projects()
        match = next((p for p in available if p["id"] == norm), None)
        if not match:
            match = next((p for p in available if p["facility_id"] == norm), None)
        if not match:
            match = next((p for p in available if str(p["name"]).lower() == str(query).strip().lower()), None)
        if not match:
            names = ", ".join(p["name"] for p in available[:6]) or "none currently unlocked"
            return False, f"Project unavailable. Unlocked projects: {names}.", None
        project_id = match["id"]
        with self.db.tx() as conn:
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
        return True, f"ACTIVE PROJECT — {PROJECTS[project_id]['name']} selected.", self.project_snapshot(project_id)

    def contribute(self, player_id: str, raw: str) -> tuple[bool, str, list[str]]:
        player = self.db.one("SELECT display_name,gil FROM players WHERE twitch_id=?", (str(player_id),))
        if not player:
            return False, "Recruit a hero before contributing to the Fellowship.", []
        project = self.project_snapshot()
        if not project:
            return False, "The Fellowship has no active project. The streamer can choose one with !fellowshipproject.", []
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
        key = "gil" if kind == "gil" else f"item:{asset_id}"
        requirement = next((req for req in project["requirements"] if req["key"] == key), None)
        if not requirement:
            return False, f"{project['name']} does not currently need that resource.", []
        remaining = max(0, int(requirement["target"]) - int(requirement["current"]))
        if remaining <= 0:
            return False, f"That requirement for {project['name']} is already complete.", []
        accepted = min(amount, remaining)
        self.ensure_member(player_id)
        with self.db.tx() as conn:
            if kind == "gil":
                live = conn.execute("SELECT gil FROM players WHERE twitch_id=?", (str(player_id),)).fetchone()
                if not live or int(live["gil"]) < accepted:
                    return False, f"You need {accepted:,} Gil to make that contribution.", []
                conn.execute("UPDATE players SET gil=gil-?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (accepted, str(player_id)))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,?)", (str(player_id), -accepted, f"fellowship:{project['id']}"))
                conn.execute("UPDATE fellowship_members SET gil_donated=gil_donated+?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?", (accepted, str(player_id)))
                renown = max(1, min(40, accepted // 250))
                label = f"{accepted:,} Gil"
            else:
                row = conn.execute("SELECT quantity FROM inventory WHERE player_id=? AND item_id=?", (str(player_id), asset_id)).fetchone()
                if not row or int(row["quantity"]) < accepted:
                    return False, f"You need {accepted} {self.data.items[asset_id]['name']} to make that contribution.", []
                conn.execute("UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?", (accepted, str(player_id), asset_id))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'item',?,?,?)", (str(player_id), asset_id, -accepted, f"fellowship:{project['id']}"))
                conn.execute("UPDATE fellowship_members SET materials_donated=materials_donated+?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?", (accepted, str(player_id)))
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
            conn.execute("INSERT OR IGNORE INTO fellowship_project_members(project_id,player_id) VALUES (?,?)", (project["id"], str(player_id)))
            conn.execute(
                "INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (?,'contribution',?,?)",
                (str(player_id), f"{player['display_name']} contributed {label} to {project['name']}", accepted),
            )
        notes = self._award_renown(str(player_id), renown, f"contribution:{time.time_ns()}:{player_id}", "contribution", 1, progress_activity=False)
        notes.extend(self._check_project_completion(str(player_id)))
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
        notes: list[str] = []
        old_state = self._state()
        old_level = int(old_state["level"] if old_state else 1)
        old_rank = None
        if player_id:
            self.ensure_member(player_id)
            member = self._member(player_id)
            old_rank = guild_rank_for_renown(int(member["renown"]))
        with self.db.tx() as conn:
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
        notes.extend(self._finalize_progress(player_id, old_level, old_rank))
        return notes

    def _progress_project_activity(self, conn: Any, player_id: str | None, activity: str, amount: int) -> None:
        state = conn.execute("SELECT active_project_id FROM fellowship_state WHERE singleton_id=1").fetchone()
        project_id = str(state["active_project_id"]) if state and state["active_project_id"] else ""
        project = PROJECTS.get(project_id)
        if not project:
            return
        accepted_activities = {activity}
        if activity in {"encounter_win", "hunt_win"}:
            accepted_activities.update({"combat_victory", "monster_victory"})
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

    @staticmethod
    def _activity_matches(order_activity: str, activity: str) -> bool:
        if order_activity == activity:
            return True
        if order_activity == "craft_forge" and activity in {"craft", "forge"}:
            return True
        if order_activity == "combat_victory" and activity in {"encounter_win", "hunt_win"}:
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
            if deed["activity"] != activity:
                continue
            row = conn.execute("SELECT progress,target,completed_at FROM fellowship_deeds WHERE deed_id=?", (deed["id"],)).fetchone()
            if not row or row["completed_at"]:
                continue
            add = max(0, min(int(amount), int(row["target"]) - int(row["progress"])))
            if add:
                conn.execute("UPDATE fellowship_deeds SET progress=progress+? WHERE deed_id=?", (add, deed["id"]))
                if player_id:
                    conn.execute("INSERT OR IGNORE INTO fellowship_deed_members(deed_id,player_id) VALUES (?,?)", (deed["id"], player_id))

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
                    for rowp in participants:
                        conn.execute("UPDATE fellowship_members SET orders_participated=orders_participated+1 WHERE player_id=?", (rowp["player_id"],))
            completed_orders = conn.execute("SELECT COUNT(*) AS n FROM fellowship_orders WHERE period_key=? AND completed_at IS NOT NULL", (period,)).fetchone()
            if int(completed_orders["n"] if completed_orders else 0) >= len(selected):
                event_key = f"weekly_orders_complete:{period}"
                inserted = conn.execute("INSERT OR IGNORE INTO fellowship_events(event_key,player_id,activity,renown,amount) VALUES (?,NULL,'weekly_orders_complete',500,1)", (event_key,)).rowcount
                if inserted:
                    bonus += 500
                    notes.append("WEEKLY ORDERS COMPLETE — all Fellowship Orders finished (+500 Renown)")
                    conn.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'orders_week_complete','Weekly Orders complete',500)")
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
        return notes

    def _check_project_completion(self, triggering_player_id: str | None) -> list[str]:
        project = self.project_snapshot()
        if not project or not project["complete"]:
            return []
        project_id = project["id"]
        notes = [f"PROJECT COMPLETE — {project['name']}"]
        bonus = 250 * max(1, int(project.get("tier", 1)))
        with self.db.tx() as conn:
            if project.get("teaser"):
                conn.execute("UPDATE fellowship_state SET active_project_id=NULL,expedition_board_complete=1,renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (bonus,))
                notes.append("The Expedition Board is ready. Distant contracts arrive with v1.2 — Expedition.")
            else:
                conn.execute("UPDATE fellowship_facilities SET tier=?,updated_at=CURRENT_TIMESTAMP WHERE facility_id=?", (int(project["tier"]), project["facility_id"]))
                conn.execute("UPDATE fellowship_state SET active_project_id=NULL,renown=renown+?,updated_at=CURRENT_TIMESTAMP WHERE singleton_id=1", (bonus,))
                benefit = FACILITIES[project["facility_id"]]["benefits"][int(project["tier"]) - 1]
                notes.append(f"{FACILITIES[project['facility_id']]['name']} Tier {project['tier']} unlocked — {benefit}.")
            conn.execute("INSERT INTO fellowship_activity(player_id,kind,label,amount) VALUES (NULL,'project_complete',?,?)", (project["name"], bonus))
            participants = conn.execute("SELECT player_id FROM fellowship_project_members WHERE project_id=?", (project_id,)).fetchall()
            for row in participants:
                conn.execute("UPDATE fellowship_members SET projects_contributed=projects_contributed+1 WHERE player_id=?", (row["player_id"],))
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
        for facility_id, config in FACILITIES.items():
            tier = int(tiers.get(facility_id, 0))
            next_benefit = config["benefits"][tier] if tier < int(config["max_tier"]) else None
            current_benefit = config["benefits"][tier - 1] if tier > 0 else "Not yet constructed"
            facilities.append({
                "id": facility_id,
                "name": config["name"],
                "tier": tier,
                "max_tier": int(config["max_tier"]),
                "description": config["description"],
                "current_benefit": current_benefit,
                "next_benefit": next_benefit,
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
        }

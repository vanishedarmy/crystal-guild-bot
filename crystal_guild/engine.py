from __future__ import annotations

import copy
import json
import logging
import random
import re
import threading
import time
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any

from .active_battle import (
    action_priority,
    STATUS_LABELS,
    ability_cost,
    ability_resource,
    apply_status,
    battle_resource_pools,
    cleanse,
    has_status,
    match_ability,
    normalize_action_text,
    status_magnitude,
    tick_statuses,
    unlocked_abilities,
    player_outgoing_status_multiplier,
    incoming_vulnerability_multiplier,
    job_resource_mode,
)
from .battle_presentation import (
    party_condition_text,
    party_status_lines,
    resource_text,
    round_summary,
    status_text,
)
from .balance import (
    active_hunt_hp,
    active_hunt_pressure,
    active_hunt_round_limit,
    active_hunt_status_chance,
    critical_chance,
    daily_gil_range,
    defend_ap_restore,
    defend_mp_restore,
    encounter_reward_factor,
    hunt_repeat_rewards,
    jp_reward_factor,
    jp_to_next,
    party_enemy_attacks,
    party_monster_hp,
    raid_contribution_score,
    raid_reward_allocations,
    rally_venture_reward_multiplier,
    sell_value,
    xp_to_next,
    STUN_RESIST_ROUNDS_AFTER_SUCCESS,
    VENTURE_MAX_LEVEL_ABOVE_PLAYER,
    SOLO_VENTURE_MAX_LEVEL_ABOVE_PLAYER,
    SOLO_VENTURE_COOLDOWN_SECONDS,
    SOLO_VENTURE_TREASURE_CHANCE,
    SOLO_VENTURE_FELLOWSHIP_RENOWN,
    SOLO_EXPEDITION_MAX_STAGES,
    SOLO_EXPEDITION_STAGE_BONUS,
    SOLO_EXPEDITION_DEFEAT_GIL_KEEP,
    VENTURE_TREASURE_CHANCE,
    VENTURE_TREASURE_LEVEL_BELOW_PLAYER,
    VENTURE_TREASURE_LEVEL_ABOVE_PLAYER,
    VENTURE_TREASURE_CATEGORY_WEIGHTS,
    VENTURE_TREASURE_RARITY_WEIGHTS,
)
from .daily_provisions import (
    daily_gil_with_perk,
    provision_preview,
    roll_daily_provisions,
    subscriber_perk,
)
from .data import GameData
from .expeditions import (
    BONUS_STAGES as EXPEDITION_BONUS_STAGES,
    DEPTHS as EXPEDITION_DEPTHS,
    ROUTES as EXPEDITION_ROUTES,
    defeat_cache_keep as expedition_defeat_cache_keep,
    effective_travel_seconds as expedition_travel_seconds,
    event_weights as expedition_event_weights,
    rare_event_bonus as expedition_rare_event_bonus,
    resource_yield_bonus as expedition_resource_yield_bonus,
    hazard_damage_multiplier as expedition_hazard_damage_multiplier,
    chocobo_event_bond_xp as expedition_chocobo_event_bond_xp,
)
from .enemy_combat import (
    choose_enemy_action,
    effective_status_chance,
    enemy_damage_multiplier,
)
from .database import Database
from .fellowship_system import FellowshipSystem
from .time_format import format_duration
from .chocobo import (
    CHOC_MAX_LEVEL,
    DEFAULT_PORTRAIT_ID as CHOCOBO_DEFAULT_PORTRAIT_ID,
    PORTRAITS as CHOCOBO_PORTRAITS,
    QUEST_DESCRIPTION as CHOCOBO_QUEST_DESCRIPTION,
    QUEST_ID as CHOCOBO_QUEST_ID,
    QUEST_NAME as CHOCOBO_QUEST_NAME,
    QUEST_REQUIREMENTS as CHOCOBO_QUEST_REQUIREMENTS,
    QUEST_REWARD_GIL as CHOCOBO_QUEST_REWARD_GIL,
    STABLE_FACILITY_ID as CHOCOBO_STABLE_FACILITY_ID,
    TRAITS as CHOCOBO_TRAITS,
    WRIT_ACTIVATION_SECONDS as CHOCOBO_WRIT_ACTIVATION_SECONDS,
    WRIT_COST_GIL as CHOCOBO_WRIT_COST_GIL,
    level_from_total_xp as chocobo_level_from_total_xp,
    trait_for_player as chocobo_trait_for_player,
    total_xp_floor_for_level as chocobo_total_xp_floor_for_level,
    expedition_specialization as chocobo_expedition_specialization,
)


STARTER_JOBS = {"warrior", "monk", "thief", "blackmage", "whitemage", "redmage"}
STANCES = {"balanced", "aggressive", "defensive", "magical", "cautious"}
HUNT_RANKS = {"C": 1, "B": 2, "A": 3, "S": 4, "S+": 5}
HUNT_DURATION_SECONDS = {"C": 15 * 60, "B": 30 * 60, "A": 2 * 60 * 60, "S": 5 * 60 * 60, "S+": 5 * 60 * 60}
HUNT_AUTO_ITEM_CAP = {"C": 1, "B": 1, "A": 2, "S": 2, "S+": 3}
TANK_JOBS = {"warrior", "paladin", "darkknight"}
HEALER_JOBS = {"whitemage", "sage"}
SUPPORT_JOBS = {"bard", "timemage"}
RAID_SUMMONS = {
    "ifrit": ("Ifrit", 1.00), "shiva": ("Shiva", 1.00), "ramuh": ("Ramuh", 1.00),
    "titan": ("Titan", 1.00), "garuda": ("Garuda", 1.00), "leviathan": ("Leviathan", 1.00),
    "bahamut": ("Bahamut", 1.35),
}

LOGGER = logging.getLogger(__name__)
RUNTIME_STATE_KEY = "combat"
RUNTIME_STATE_SCHEMA = 1
LONG_REST_SECONDS = 8 * 60 * 60
PLAYER_ACTIVITY_STATE_PREFIX = "player_activity:"
STREAM_REFRESH_STATE_KEY = "stream_live_refresh"
CAMP_REST_ONLINE_SECONDS = 15 * 60
CAMP_REST_OFFLINE_SECONDS = 60 * 60


def _state_guard(method):
    """Serialize and atomically persist authoritative live-combat state.

    The state lock is coupled to one composable database transaction. Any
    nested reward/inventory/record writes therefore commit together with the
    encounter/raid checkpoint. If a command or daemon tick raises, both SQLite
    and the in-memory combat state return to the pre-call snapshot.
    """
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._state_lock:
            before = self._capture_runtime_state()
            try:
                with self.db.tx():
                    result = method(self, *args, **kwargs)
                    after = self._capture_runtime_state()
                    if after != before:
                        self._persist_runtime_state(after)
                    return result
            except Exception:
                self._apply_runtime_state(before)
                raise
    return wrapped


@dataclass
class GameResult:
    ok: bool
    messages: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, *messages: str, **data: Any) -> "GameResult":
        return cls(True, list(messages), data)

    @classmethod
    def fail(cls, message: str, **data: Any) -> "GameResult":
        return cls(False, [message], data)


class CrystalGuildEngine:
    def __init__(self, db: Database, data: GameData, venture_cooldown_seconds: int = 600, encounter_join_seconds: int = 60, camp_rest_seconds: int = 3600, raid_join_seconds: int = 90, raid_round_seconds: int = 60, overlay_state_path: str = "overlay/state.json", rng: random.Random | None = None, shop_refresh_seconds: int = 1800, encounter_round_seconds: int = 30, venture_treasure_chance: float = VENTURE_TREASURE_CHANCE):
        self.db = db
        self.data = data
        self.fellowship_system = FellowshipSystem(db, data)
        self.venture_cooldown_seconds = venture_cooldown_seconds
        self.encounter_join_seconds = max(5, encounter_join_seconds)
        self.encounter_round_seconds = max(5, encounter_round_seconds)
        self.camp_rest_seconds = max(60, camp_rest_seconds)
        self.shop_refresh_seconds = max(60, shop_refresh_seconds)
        self.raid_join_seconds = max(10, raid_join_seconds)
        self.raid_round_seconds = max(5, raid_round_seconds)
        self.overlay_state_path = Path(overlay_state_path)
        self.rng = rng or random.Random()
        self.venture_treasure_chance = max(0.0, min(1.0, float(venture_treasure_chance)))
        self._state_lock = threading.RLock()
        self.active_encounter: dict[str, Any] | None = None
        self.encounter_roster: dict[str, dict[str, Any]] = {}
        # Timed Hunts are per-player autonomous assignments. They are persisted
        # with runtime combat state so several players may hunt concurrently
        # without occupying the Guild-wide Rally Venture / raid battle slot.
        self.active_hunts: dict[str, dict[str, Any]] = {}
        self._encounter_seq = 0
        # Keep a small in-memory recap cache for !battlelog. It is
        # intentionally ephemeral: battle presentation must not become another
        # persistence or hosted-sync responsibility.
        self._last_battle_history: dict[str, Any] | None = None
        # Short-lived Portal presentation cache for immediately resolved field
        # activities. This is intentionally ephemeral and does not alter the
        # authoritative database/schema.
        self._last_adventure_result: dict[str, Any] | None = None
        self.active_boss: dict[str, Any] | None = None
        self.raid_roster: dict[str, dict[str, Any]] = {}
        self._runtime_recovered = False
        self._runtime_recovery_error: str | None = None
        self._runtime_recovered_at: str | None = None
        self._restore_runtime_state()
        if self.active_boss:
            self._update_raid_overlay()
        else:
            self._write_overlay({"active": False, "status": "IDLE"})

    def _capture_runtime_state(self) -> dict[str, Any]:
        return {
            "schema": RUNTIME_STATE_SCHEMA,
            "encounter_seq": int(self._encounter_seq),
            "active_encounter": copy.deepcopy(self.active_encounter),
            "encounter_roster": copy.deepcopy(self.encounter_roster),
            "active_hunts": copy.deepcopy(self.active_hunts),
            "active_boss": copy.deepcopy(self.active_boss),
            "raid_roster": copy.deepcopy(self.raid_roster),
        }

    def _apply_runtime_state(self, state: dict[str, Any]) -> None:
        self._encounter_seq = max(0, int(state.get("encounter_seq", 0)))
        self.active_encounter = copy.deepcopy(state.get("active_encounter"))
        encounter_roster = state.get("encounter_roster") or {}
        self.encounter_roster = copy.deepcopy(encounter_roster) if isinstance(encounter_roster, dict) else {}
        active_hunts = state.get("active_hunts") or {}
        self.active_hunts = copy.deepcopy(active_hunts) if isinstance(active_hunts, dict) else {}
        self.active_boss = copy.deepcopy(state.get("active_boss"))
        raid_roster = state.get("raid_roster") or {}
        self.raid_roster = copy.deepcopy(raid_roster) if isinstance(raid_roster, dict) else {}

    def _normalize_encounter_resources(self) -> None:
        """Upgrade restored v1.0 combat checkpoints to the MP/AP resource model.

        Runtime checkpoints are intentionally schema-stable across this update.
        Older checkpoints may contain only MP because every ability previously
        used that pool. Physical Jobs convert to a fresh AP pool, magic Jobs
        preserve any remaining MP, and dual-resource Jobs preserve MP while
        receiving their AP pool.
        """
        if not self.active_encounter or self.active_encounter.get("state") != "combat":
            return
        for meta in self.encounter_roster.values():
            job = self.data.jobs.get(meta.get("job_id"))
            stats = meta.get("stats") or {}
            if not job or not stats:
                continue
            pools = battle_resource_pools(stats, job)
            max_mp = int(pools["max_mp"])
            max_ap = int(pools["max_ap"])
            old_mp = int(meta.get("mp", max_mp))
            old_ap = meta.get("ap")
            old_max_mp = max(0, int(meta.get("max_mp", max_mp)))
            old_max_ap = max(0, int(meta.get("max_ap", max_ap)))
            meta["max_mp"] = max_mp
            if max_mp > 0:
                # If a checkpoint was saved under the pre-rebalance larger pool,
                # preserve the percentage remaining instead of turning a mid-fight
                # upgrade into either a refill or an excessive drain.
                if old_max_mp > 0 and old_max_mp != max_mp:
                    meta["mp"] = max(0, min(max_mp, int(round(max_mp * old_mp / old_max_mp))))
                else:
                    meta["mp"] = max(0, min(max_mp, old_mp))
            else:
                meta["mp"] = 0
            meta["max_ap"] = max_ap
            if max_ap > 0:
                if old_ap is None:
                    meta["ap"] = max_ap
                elif old_max_ap > 0 and old_max_ap != max_ap:
                    meta["ap"] = max(0, min(max_ap, int(round(max_ap * int(old_ap) / old_max_ap))))
                else:
                    meta["ap"] = max(0, min(max_ap, int(old_ap)))
            else:
                meta["ap"] = 0

    def _validate_runtime_state(self, state: dict[str, Any]) -> None:
        if int(state.get("schema", 0)) != RUNTIME_STATE_SCHEMA:
            raise ValueError("unsupported runtime-state schema")
        encounter = state.get("active_encounter")
        boss = state.get("active_boss")
        if encounter and boss:
            raise ValueError("encounter and raid cannot both be active")
        if encounter:
            if not isinstance(encounter, dict) or "id" not in encounter:
                raise ValueError("active encounter is malformed")
            if str(encounter.get("monster_id") or "") not in self.data.monsters:
                raise ValueError("active encounter references an unknown monster")
            roster = state.get("encounter_roster")
            if not isinstance(roster, dict) or not roster:
                raise ValueError("active encounter has no roster")
        hunts = state.get("active_hunts") or {}
        if not isinstance(hunts, dict):
            raise ValueError("active Hunts are malformed")
        for player_id, assignment in hunts.items():
            if not isinstance(assignment, dict):
                raise ValueError("active Hunt assignment is malformed")
            if str(assignment.get("hunt_id") or "") not in self.data.hunts:
                raise ValueError("active Hunt references an unknown mark")
            if str(assignment.get("monster_id") or "") not in self.data.monsters:
                raise ValueError("active Hunt references an unknown monster")
            if str(assignment.get("player_id") or player_id) != str(player_id):
                raise ValueError("active Hunt player identity is malformed")
            if float(assignment.get("resolves_at") or 0) <= 0:
                raise ValueError("active Hunt is missing its resolution deadline")
        if boss:
            if not isinstance(boss, dict) or str(boss.get("id") or "") not in self.data.bosses:
                raise ValueError("active raid references an unknown boss")
            roster = state.get("raid_roster")
            if not isinstance(roster, dict):
                raise ValueError("active raid roster is malformed")

    def _persist_runtime_state(self, state: dict[str, Any] | None = None) -> None:
        payload = state if state is not None else self._capture_runtime_state()
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        self.db.set_runtime_state(RUNTIME_STATE_KEY, encoded)

    def _restore_runtime_state(self) -> None:
        row = self.db.runtime_state(RUNTIME_STATE_KEY)
        if not row:
            return
        try:
            state = json.loads(row["value_json"])
            if not isinstance(state, dict):
                raise ValueError("runtime checkpoint is not an object")
            self._validate_runtime_state(state)
            self._apply_runtime_state(state)
            self._normalize_encounter_resources()
            if self.active_encounter:
                self._encounter_seq = max(self._encounter_seq, int(self.active_encounter.get("id", 0)))
            self._runtime_recovered = bool(self.active_encounter or self.active_boss or self.active_hunts)
            self._runtime_recovered_at = str(row["updated_at"] or "")
            if self._runtime_recovered:
                kind = "encounter" if self.active_encounter else "raid" if self.active_boss else f"Hunts({len(self.active_hunts)})"
                LOGGER.warning("Recovered active %s from Crystal runtime checkpoint", kind)
        except Exception as exc:
            self._runtime_recovery_error = f"{type(exc).__name__}: {exc}"
            LOGGER.error("Ignoring corrupt Crystal runtime checkpoint: %s", self._runtime_recovery_error)
            self.active_encounter = None
            self.encounter_roster = {}
            self.active_hunts = {}
            self.active_boss = None
            self.raid_roster = {}
            # A corrupt checkpoint must not brick every future launch. Keep the
            # error in diagnostics, then replace it on the next valid state write.
            self.db.delete_runtime_state(RUNTIME_STATE_KEY)

    def runtime_status(self) -> dict[str, Any]:
        active = "idle"
        if self.active_encounter:
            active = f"encounter#{self.active_encounter.get('id')}:{self.active_encounter.get('state', 'rally')}"
        elif self.active_boss:
            active = f"raid:{self.active_boss.get('id')}:{self.active_boss.get('state', 'rally')}"
        elif self.active_hunts:
            active = f"hunts:{len(self.active_hunts)}:timed"
        return {
            "active": active,
            "recovered": self._runtime_recovered,
            "recovered_at": self._runtime_recovered_at or "none",
            "recovery_error": self._runtime_recovery_error or "none",
            "encounter_seq": self._encounter_seq,
            "active_hunts": len(self.active_hunts),
        }

    # ---------- passive recovery ----------
    @staticmethod
    def _player_activity_key(player_id: str) -> str:
        return f"{PLAYER_ACTIVITY_STATE_PREFIX}{str(player_id)}"

    def _load_player_activity_state(self, player_id: str) -> dict[str, int | str]:
        row = self.db.runtime_state(self._player_activity_key(player_id))
        if not row:
            return {"last_action_at": 0, "last_refresh_at": 0, "refresh_reason": ""}
        try:
            payload = json.loads(str(row["value_json"] or "{}"))
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = {}
        return {
            "last_action_at": max(0, int(payload.get("last_action_at") or 0)),
            "last_refresh_at": max(0, int(payload.get("last_refresh_at") or 0)),
            "refresh_reason": str(payload.get("refresh_reason") or ""),
        }

    def _save_player_activity_state(
        self, player_id: str, *, last_action_at: int, last_refresh_at: int = 0, refresh_reason: str = ""
    ) -> None:
        self.db.set_runtime_state(
            self._player_activity_key(player_id),
            json.dumps(
                {
                    "last_action_at": max(0, int(last_action_at)),
                    "last_refresh_at": max(0, int(last_refresh_at)),
                    "refresh_reason": str(refresh_reason or ""),
                },
                separators=(",", ":"),
            ),
        )

    def _full_refresh_player_row(self, player: Any, *, clear_camp: bool = True) -> dict[str, int]:
        player_id = str(player["twitch_id"])
        current_job = str(player["current_job"] or "adventurer")
        max_hp = 100
        max_mp = 0
        max_ap = 0
        job = self.data.jobs.get(current_job)
        if job is not None:
            stats = self._stats(player, job)
            pools = battle_resource_pools(stats, job)
            max_hp = int(stats["hp"])
            max_mp = max(0, int(pools.get("max_mp") or 0))
            max_ap = max(0, int(pools.get("max_ap") or 0))
        camp_until = 0 if clear_camp else int(player["camp_until"] or 0)
        self.db.execute(
            "UPDATE players SET current_hp=?, current_mp=?, current_ap=?, camp_until=?, updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
            (max_hp, max_mp, max_ap, camp_until, player_id),
        )
        return {"hp": max_hp, "mp": max_mp, "ap": max_ap}

    def _persistent_run_blocks_passive_refresh(self, player_id: str) -> bool:
        """Return True while a player-paced run owns HP/MP/AP continuity.

        Long Rest and stream-live roster refreshes are intentionally passive.
        They must never heal through an active Wayfarer or v1.2 Expedition,
        including after Bot restarts, because those runs persist their own
        resource-pressure state in SQLite.
        """
        uid = str(player_id)
        if self.db.one("SELECT 1 FROM player_expeditions WHERE player_id=?", (uid,)):
            return True
        if self.db.one("SELECT 1 FROM solo_expeditions WHERE player_id=?", (uid,)):
            return True
        return False

    def record_player_action(self, player_id: str, *, now: int | None = None) -> dict[str, Any]:
        """Record an intentional player interaction and apply an eight-hour Long Rest once due.

        Runtime-state storage keeps this upgrade schema-neutral and persistent across
        Bot restarts. Read-only hosted Portal polling does not call this method; only
        intentional Twitch commands and Portal mutations advance the inactivity timer.
        """
        uid = str(player_id)
        player = self.db.one("SELECT * FROM players WHERE twitch_id=?", (uid,))
        if not player:
            return {"player_id": uid, "refreshed": False, "tracked": False}
        current = int(time.time()) if now is None else int(now)
        state = self._load_player_activity_state(uid)
        last_action = int(state.get("last_action_at") or 0)
        refreshed = False
        resources: dict[str, int] | None = None
        # Existing players begin a fresh eight-hour inactivity window on their
        # first post-upgrade interaction rather than receiving a surprise heal
        # based on unrelated historical database writes.
        last_refresh = int(state.get("last_refresh_at") or 0)
        refresh_blocked = self._persistent_run_blocks_passive_refresh(uid)
        if last_action and current - last_action >= LONG_REST_SECONDS and last_refresh < last_action and not refresh_blocked:
            resources = self._full_refresh_player_row(player, clear_camp=True)
            refreshed = True
            LOGGER.info(
                "Long Rest refreshed player %s after %ss without player activity",
                uid, current - last_action,
            )
        self._save_player_activity_state(
            uid,
            last_action_at=current,
            last_refresh_at=current if refreshed else last_refresh,
            refresh_reason="long_rest" if refreshed else str(state.get("refresh_reason") or ""),
        )
        return {
            "player_id": uid,
            "refreshed": refreshed,
            "tracked": True,
            "inactive_seconds": max(0, current - last_action) if last_action else 0,
            "resources": resources or {},
            "refresh_blocked_by_active_run": bool(refresh_blocked),
        }

    def refresh_due_long_rests(self, *, now: int | None = None) -> dict[str, Any]:
        """Refresh heroes whose persisted inactivity counter has reached eight hours.

        The combat daemon calls this on a light periodic cadence, so Long Rest
        resolves even if the player never opens chat or the Portal at the exact
        deadline. A later player action sees the persisted refresh marker and
        will not receive a duplicate heal.
        """
        current = int(time.time()) if now is None else int(now)
        refreshed_ids: list[str] = []
        skipped_active_ids: list[str] = []
        with self._state_lock, self.db.tx():
            for player in self.db.all("SELECT * FROM players ORDER BY twitch_id"):
                uid = str(player["twitch_id"])
                state = self._load_player_activity_state(uid)
                last_action = int(state.get("last_action_at") or 0)
                last_refresh = int(state.get("last_refresh_at") or 0)
                if not last_action or current - last_action < LONG_REST_SECONDS or last_refresh >= last_action:
                    continue
                if self._persistent_run_blocks_passive_refresh(uid):
                    skipped_active_ids.append(uid)
                    continue
                self._full_refresh_player_row(player, clear_camp=True)
                self._save_player_activity_state(
                    uid,
                    last_action_at=last_action,
                    last_refresh_at=current,
                    refresh_reason="long_rest",
                )
                refreshed_ids.append(uid)
        if refreshed_ids:
            LOGGER.info("Long Rest scheduler refreshed %s player(s): %s", len(refreshed_ids), ",".join(refreshed_ids))
        return {
            "count": len(refreshed_ids),
            "player_ids": refreshed_ids,
            "skipped_active_run_ids": skipped_active_ids,
            "checked_at": current,
        }

    def refresh_all_players_for_stream(self, started_at: str) -> dict[str, Any]:
        """Refresh every hero once per Twitch stream session.

        Twitch's stream ``started_at`` timestamp is persisted as the idempotency
        key, so repeated status probes and Bot reconnects during the same stream
        do not repeatedly heal the roster.
        """
        session = str(started_at or "").strip()
        if not session:
            return {"refreshed": False, "count": 0, "session": ""}
        with self._state_lock, self.db.tx():
            row = self.db.runtime_state(STREAM_REFRESH_STATE_KEY)
            if row:
                try:
                    previous = json.loads(str(row["value_json"] or "{}"))
                except (TypeError, ValueError, json.JSONDecodeError):
                    previous = {}
                if str(previous.get("started_at") or "") == session:
                    return {"refreshed": False, "count": 0, "session": session}
            players = self.db.all("SELECT * FROM players ORDER BY twitch_id")
            refreshed_at = int(time.time())
            refreshed_ids: list[str] = []
            skipped_active_ids: list[str] = []
            for player in players:
                uid = str(player["twitch_id"])
                if self._persistent_run_blocks_passive_refresh(uid):
                    skipped_active_ids.append(uid)
                    continue
                self._full_refresh_player_row(player, clear_camp=True)
                refreshed_ids.append(uid)
                activity = self._load_player_activity_state(uid)
                self._save_player_activity_state(
                    uid,
                    last_action_at=int(activity.get("last_action_at") or 0),
                    last_refresh_at=refreshed_at,
                    refresh_reason="stream_live",
                )
            self.db.set_runtime_state(
                STREAM_REFRESH_STATE_KEY,
                json.dumps(
                    {
                        "started_at": session,
                        "refreshed_at": refreshed_at,
                        "count": len(refreshed_ids),
                        "skipped_active_run_ids": skipped_active_ids,
                    },
                    separators=(",", ":"),
                ),
            )
        LOGGER.info(
            "Stream-live refresh restored %s Crystal Guild players for session %s; skipped %s active persistent run(s)",
            len(refreshed_ids), session, len(skipped_active_ids),
        )
        return {
            "refreshed": True,
            "count": len(refreshed_ids),
            "player_ids": refreshed_ids,
            "skipped_active_run_ids": skipped_active_ids,
            "session": session,
        }

    # ---------- players ----------
    def recruit(self, twitch_id: str, username: str, display_name: str | None = None) -> GameResult:
        if self._player(twitch_id):
            return GameResult.fail(f"{display_name or username}, you're already registered with the Crystal Guild.")
        display = display_name or username
        with self.db.tx() as conn:
            conn.execute(
                "INSERT INTO players(twitch_id, username, display_name) VALUES (?, ?, ?)",
                (str(twitch_id), username.lower(), display),
            )
            conn.execute("INSERT INTO equipment(player_id) VALUES (?)", (str(twitch_id),))
            conn.execute("INSERT INTO inventory(player_id, item_id, quantity) VALUES (?, 'potion', 3)", (str(twitch_id),))
            conn.execute("INSERT INTO player_titles(player_id, title_id) VALUES (?, 'fresh_meat')", (str(twitch_id),))
            conn.execute(
                "INSERT INTO transactions(player_id, kind, asset_id, amount, source) VALUES (?, 'item', 'potion', 3, 'recruitment')",
                (str(twitch_id),),
            )
        self.fellowship_system.ensure_member(str(twitch_id), founding=False)
        self.record_player_action(str(twitch_id))
        return GameResult.success(
            f"{display} joined the Crystal Guild! Lv.1 Adventurer | 250 gil | 3 Potions | NEXT: !job warrior | monk | thief | blackmage | whitemage | redmage",
            "After choosing a Job: !venture to adventure | !next for your next objective | !guild for the command map.",
        )

    def portal_recruit(self, twitch_id: str, username: str, display_name: str, action_id: str) -> GameResult:
        """Replay-safe website recruitment using the same starting state as ``!recruit``.

        Recruitment is the one Portal mutation permitted before a synced player
        exists. The action receipt is committed in the same transaction as the
        player, starter inventory, title, and Fellowship membership so a lost
        hosted acknowledgement cannot create or award the character twice.
        """
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        uid = str(twitch_id or "").strip()
        login = str(username or "").strip().lower()
        display = " ".join(str(display_name or login).strip().split())[:50] or login
        if not uid.isdigit() or not re.fullmatch(r"[a-z0-9_]{1,25}", login):
            return self._portal_store_nonmutating_result(
                action_id, GameResult.fail("Portal recruitment could not verify that Twitch identity.")
            )
        if self._player(uid):
            return self._portal_store_nonmutating_result(
                action_id, GameResult.fail(f"{display}, you're already registered with the Crystal Guild.")
            )
        result = GameResult.success(
            f"{display} joined the Crystal Guild! Lv.1 Adventurer | 250 gil | 3 Potions | NEXT: !job warrior | monk | thief | blackmage | whitemage | redmage",
            "After choosing a Job: !venture to adventure | !next for your next objective | !guild for the command map.",
            recruited=True,
            username=login,
            display_name=display,
        )
        with self.db.tx() as conn:
            conn.execute(
                "INSERT INTO players(twitch_id, username, display_name) VALUES (?, ?, ?)",
                (uid, login, display),
            )
            conn.execute("INSERT INTO equipment(player_id) VALUES (?)", (uid,))
            conn.execute("INSERT INTO inventory(player_id, item_id, quantity) VALUES (?, 'potion', 3)", (uid,))
            conn.execute("INSERT INTO player_titles(player_id, title_id) VALUES (?, 'fresh_meat')", (uid,))
            conn.execute(
                "INSERT INTO transactions(player_id, kind, asset_id, amount, source) VALUES (?, 'item', 'potion', 3, 'recruitment')",
                (uid,),
            )
            conn.execute(
                "INSERT OR IGNORE INTO fellowship_members(player_id,founding_member) VALUES (?,0)",
                (uid,),
            )
            self._portal_action_store_sql(conn, action_id, result)
        self.record_player_action(uid)
        return result

    def hero(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        healed = self._finish_rest_if_ready(twitch_id)
        p = self._player(twitch_id)
        self._ensure_base_title(twitch_id)
        job = self.data.jobs.get(p["current_job"], {"name": "Adventurer"})
        jrow = self.db.one("SELECT level, jp FROM player_jobs WHERE player_id=? AND job_id=?", (twitch_id, p["current_job"]))
        job_text = "Unassigned" if not jrow else f"{job['name']} JLv.{jrow['level']} ({jrow['jp']}/{jp_to_next(jrow['level'])} JP)"
        eq = self.db.one("SELECT * FROM equipment WHERE player_id=?", (twitch_id,))
        weapon = self._item_name(eq["weapon_id"] if eq else None)
        armor = self._item_name(eq["armor_id"] if eq else None)
        accessory = self._item_name(eq["accessory_id"] if eq else None)
        unique = self.db.one("SELECT COUNT(*) AS n FROM bestiary WHERE player_id=?", (twitch_id,))["n"]
        ach = self.db.one("SELECT COUNT(*) AS n FROM achievements WHERE player_id=?", (twitch_id,))["n"]
        hunts = self.db.one("SELECT COALESCE(SUM(clears),0) AS n FROM player_hunts WHERE player_id=?", (twitch_id,))["n"]
        max_hp = self._max_hp(p)
        resources = self._resource_state_for(p)
        resource_suffix = ""
        resource_parts = self._resource_text_parts(resources)
        if resource_parts:
            resource_suffix = " | " + " | ".join(resource_parts)
        rest_remaining = self._camp_remaining(twitch_id)
        status = f"RESTING {self._format_seconds(rest_remaining)}" if rest_remaining else ("KO — !rest" if p["current_hp"] <= 0 and p["current_job"] != "adventurer" else "READY")
        notice = " Camp rest complete: HP fully restored." if healed else ""
        next_hint = "Choose a starter Job with !job <name>." if p["current_job"] == "adventurer" else "Use !next for a contextual objective."
        return GameResult.success(
            f"{p['display_name']} — {p['title']} | Lv.{p['level']} {job_text} | HP {p['current_hp']}/{max_hp}{resource_suffix} [{status}] | XP {p['xp']}/{xp_to_next(p['level'])} | {p['gil']:,} gil | {p['hunt_seals']:,} seals{notice}",
            f"Gear: {weapon} / {armor} / {accessory} | Region: {self.data.regions[p['current_region']]['name']} | Bestiary {unique}/{len(self.data.monsters)} | Hunts {hunts} | Achievements {ach}/{len(self.data.achievements)}",
            f"NEXT — {next_hint}",
        )

    def next_step(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return GameResult.success("NEXT — Recruit your persistent hero with !recruit. Then use !guild start for the two-minute version of the paperwork.")
        self._finish_rest_if_ready(twitch_id)
        p = self._player(twitch_id)
        remaining = self._camp_remaining(twitch_id)
        if remaining > 0:
            return GameResult.success(f"NEXT — You are resting. Full recovery in {self._format_seconds(remaining)}. Use !rest to check again or !use tent to recover immediately.")
        if p["current_job"] == "adventurer":
            return GameResult.success("NEXT — Choose your first Job: !job warrior | monk | thief | blackmage | whitemage | redmage", "After choosing, use !venture to begin adventuring.")
        if int(p["current_hp"] or 0) <= 0:
            return GameResult.success("NEXT — You are KO'd. Use !rest for a free camp recovery or !use tent if you own one and dignity is no longer a concern.")
        if self.active_encounter:
            monster = self.data.monsters.get(self.active_encounter.get("monster_id"), {})
            state = self.active_encounter.get("state", "rally")
            if state == "combat":
                if twitch_id in self.encounter_roster:
                    actor = self.encounter_roster[twitch_id]
                    queued = actor.get("action")
                    if int(actor.get("hp", 0)) <= 0:
                        return GameResult.success(f"NEXT — You are KO'd in the battle against {monster.get('name','the monster')}. An ally can Raise you or use a Phoenix Down.")
                    if queued:
                        return GameResult.success(f"NEXT — Your Round {self.active_encounter.get('round',1)} action is queued. Use !encounter to watch HP/MP or submit a different action before the timer closes.")
                    return GameResult.success("NEXT — Choose your Active Battle action: !attack | !ability <name> [target] | !defend | !use <item> [target].")
                return GameResult.success(f"NEXT — {monster.get('name','A monster')} is already in combat; the rally is closed. Wait for the next Venture.")
            remaining_window = max(0, int(self.active_encounter.get("closes_at", 0) - time.time()))
            if twitch_id in self.encounter_roster:
                return GameResult.success(f"NEXT — You are rallied against {monster.get('name','the active monster')}. Active Battle starts in {self._format_seconds(remaining_window)}.")
            if remaining_window > 0:
                return GameResult.success(f"NEXT — A rally is open against {monster.get('name','a monster')} for {self._format_seconds(remaining_window)}. Type !join to answer it.")
        if self.active_boss and self.active_boss.get("state") == "rally":
            remaining_window = max(0, int(self.active_boss.get("closes_at", 0) - time.time()))
            if twitch_id in self.raid_roster:
                return GameResult.success(f"NEXT — You are already registered against {self.active_boss['name']}. Use !boss to check the rally status.")
            return GameResult.success(f"NEXT — {self.active_boss['name']} raid rally is open for {self._format_seconds(remaining_window)}. Type !raid to join.")
        chocobo_state = self._chocobo_state_data(twitch_id)
        if chocobo_state and not chocobo_state["companion"]["registered"]:
            quest = chocobo_state["quest"]
            stable = chocobo_state["stable"]
            writ = chocobo_state["writ"]
            if quest["ready"]:
                return GameResult.success("NEXT — Your Chocobo companion quest is ready. Complete A Chocobo of Your Own with !chocoboquest.")
            if quest["complete"] and not stable["unlocked"]:
                return GameResult.success("NEXT — Your Chocobo quest is complete. The Fellowship must construct the Chocobo Stable before registration can continue. Check !facilities and !project.")
            if quest["complete"] and stable["unlocked"] and not writ["quantity"]:
                return GameResult.success(f"NEXT — Purchase your {CHOCOBO_WRIT_COST_GIL:,} Gil Chocobo Registration Writ with !chocobowrit. It activates one hour after issue.")
            if writ["quantity"] and not writ["active"]:
                return GameResult.success(f"NEXT — Your Chocobo Registration Writ is validating. Ready in {self._format_seconds(writ['remaining_seconds'])}.")
            if writ["active"]:
                return GameResult.success("NEXT — Your Chocobo Registration Writ is active. Register your companion with !registerchocobo <name>.")
        job = self.data.jobs[p["current_job"]]
        jrow = self.db.one("SELECT level, jp FROM player_jobs WHERE player_id=? AND job_id=?", (twitch_id, p["current_job"]))
        jlevel = int(jrow["level"]) if jrow else 1
        next_ability = next((a for a in job.get("abilities", []) if int(a["level"]) > jlevel), None)
        available = []
        for hunt in sorted(self.data.hunts.values(), key=lambda h: (HUNT_RANKS[h["rank"]], h["min_level"])):
            met, _ = self._hunt_available(twitch_id, hunt)
            row = self.db.one("SELECT clears FROM player_hunts WHERE player_id=? AND hunt_id=?", (twitch_id, hunt["id"]))
            if met and not row:
                available.append(hunt)
        if available:
            hunt = available[0]
            extra = f" Next Job milestone: JLv.{next_ability['level']} {next_ability['name']}." if next_ability else ""
            return GameResult.success(f"NEXT — Try the {hunt['rank']}-Rank Hunt '{hunt['name']}' with !hunt {hunt['name']}.{extra}")
        milestone = f"JLv.{next_ability['level']} {next_ability['name']}" if next_ability else f"JLv.50 Mastery: {job['mastery']['name']}"
        cooldown = self._cooldown_remaining(twitch_id, "venture")
        if cooldown > 0:
            return GameResult.success(
                f"NEXT — Venture is ready in {self._format_seconds(cooldown)}. Current {job['name']} progression target: {milestone}.",
                "While waiting, check !hunts, !quests, !inventory, !relics, or !guild for another system.",
            )
        return GameResult.success(f"NEXT — Continue adventuring with !venture. Current {job['name']} progression target: {milestone}.", "You can also check !hunts, !quests, !relics, or !guild for another system.")

    @_state_guard
    def choose_job(self, twitch_id: str, job_id: str | None = None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if not job_id:
            owned = self.db.all("SELECT job_id, level FROM player_jobs WHERE player_id=? ORDER BY level DESC, job_id", (twitch_id,))
            owned_text = ", ".join(f"{self.data.jobs[r['job_id']]['name']} {r['level']}" for r in owned) or "none yet"
            advanced = [j["name"] for j in self.data.jobs.values() if j.get("tier") != "starter" and self._requirements_met(twitch_id, j.get("unlock", []))[0]]
            unlocked_text = ", ".join(advanced[:8]) if advanced else "none yet"
            return GameResult.success(
                f"Starter Jobs: Warrior, Monk, Thief, Black Mage, White Mage, Red Mage. Your Jobs: {owned_text}",
                f"Advanced Jobs currently eligible: {unlocked_text}. Use !jobinfo <job> for requirements.",
            )
        self._finish_rest_if_ready(twitch_id)
        p = self._player(twitch_id)
        if self._camp_remaining(twitch_id) > 0:
            return GameResult.fail("You cannot change Jobs while resting at camp.")
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("You cannot change Jobs after committing to an active encounter or raid.")
        if self._expedition_load(twitch_id):
            return GameResult.fail("Return from your Expedition before changing Jobs.")
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before changing Jobs.")
        if str(twitch_id) in self.active_hunts:
            return GameResult.fail("Your Job is locked while your hero is away on a Hunt.")
        if p["current_job"] != "adventurer" and p["current_hp"] <= 0:
            return GameResult.fail("You are KO'd. Recover before attempting a dramatic career change.")
        job = self._find_by_name_or_id(self.data.jobs, job_id)
        if not job:
            return GameResult.fail("Unknown Job. Use !job to see your available Jobs.")
        if job.get("tier") != "starter":
            met, missing = self._requirements_met(twitch_id, job.get("unlock", []))
            if not met:
                return GameResult.fail(f"{job['name']} is still locked — " + "; ".join(missing[:5]))
        with self.db.tx() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO player_jobs(player_id, job_id, level, jp) VALUES (?, ?, 1, 0)",
                (twitch_id, job["id"]),
            )
            conn.execute("UPDATE players SET current_job=?, updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (job["id"], twitch_id))
        refreshed = self._player(twitch_id)
        stats = self._stats(refreshed, job)
        max_hp = int(stats["hp"])
        current = int(refreshed["current_hp"] or 0)
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id=?", (max_hp if current <= 0 else min(current, max_hp), twitch_id))
        refreshed = self._player(twitch_id)
        resources = self._resource_state_for(refreshed, job, stats)
        summary = [f"HP {self._player(twitch_id)['current_hp']}/{max_hp}", *self._resource_text_parts(resources)]
        return GameResult.success(
            f"{p['display_name']} is now a {job['name']}. " + " | ".join(summary) + ". The Guild waives responsibility for poor career choices."
        )

    def job_info(self, twitch_id: str, job_query: str | None = None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        job = self.data.jobs.get(p["current_job"]) if not job_query else self._find_by_name_or_id(self.data.jobs, job_query)
        if not job:
            return GameResult.fail("Job not found.")
        row = self.db.one("SELECT level, jp FROM player_jobs WHERE player_id=? AND job_id=?", (twitch_id, job["id"]))
        owned = bool(row)
        jlevel = row["level"] if row else 0
        learned = [a["name"] for a in job.get("abilities", []) if jlevel >= a["level"]]
        next_ability = next((a for a in job.get("abilities", []) if jlevel < a["level"]), None)
        if job.get("tier") == "starter":
            unlock = "Starter Job — always available"
        else:
            met, missing = self._requirements_met(twitch_id, job.get("unlock", []))
            unlock = "UNLOCKED" if met else "Locked: " + "; ".join(missing[:4])
        ability_text = ", ".join(learned[-4:]) if learned else "none yet"
        next_text = f"Next: JLv.{next_ability['level']} {next_ability['name']}" if next_ability else f"Mastery: {job['mastery']['name']}"
        return GameResult.success(
            f"{job['name']} [{job.get('tier','starter').title()}] | {'Owned JLv.' + str(jlevel) if owned else 'Not yet learned'} | {unlock}",
            f"Abilities: {ability_text} | {next_text} | Mastery: {job['mastery']['name']} — {job['mastery']['description']}",
        )

    def abilities(self, twitch_id: str, job_query: str | None = None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        job = self.data.jobs.get(p["current_job"]) if not job_query else self._find_by_name_or_id(self.data.jobs, job_query)
        if not job:
            return GameResult.fail("Job not found.")
        row = self.db.one("SELECT level FROM player_jobs WHERE player_id=? AND job_id=?", (twitch_id, job["id"]))
        jlevel = int(row["level"]) if row else 0
        passive = []
        for ability in job.get("abilities", []):
            icon = "✓" if jlevel >= ability["level"] else "🔒"
            passive.append(f"{icon} {ability['level']}:{ability['name']}")
        active = []
        for ability in self.data.active_abilities.get(job["id"], []):
            icon = "✓" if jlevel >= int(ability["level"]) else "🔒"
            resource = ability_resource(ability, job).upper()
            active.append(f"{icon} J{ability['level']} {ability['name']} {ability_cost(ability)}{resource}")
        return GameResult.success(
            f"{job['name']} passive traits — " + " | ".join(passive),
            "Active Battle — " + " | ".join(active) + ". Use !ability <name> [target] during combat.",
            f"JLv.50 Mastery: {job['mastery']['name']} — {job['mastery']['description']}",
        )

    def mastery(self, twitch_id: str, job_query: str | None = None, slot: int | None = None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        mastered = self.db.all("SELECT job_id FROM player_jobs WHERE player_id=? AND level>=50 ORDER BY job_id", (twitch_id,))
        equipped = self.db.all("SELECT slot, job_id FROM mastery_slots WHERE player_id=? ORDER BY slot", (twitch_id,))
        if not job_query:
            mastered_text = ", ".join(f"{self.data.jobs[r['job_id']]['name']} ({self.data.jobs[r['job_id']]['mastery']['name']})" for r in mastered) or "none"
            equipped_text = ", ".join(f"Slot {r['slot']}: {self.data.jobs[r['job_id']]['mastery']['name']}" for r in equipped) or "none"
            return GameResult.success(f"Mastered Jobs: {mastered_text}", f"Equipped Masteries: {equipped_text}. Equip with !mastery <job> <1|2>")
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("You cannot change Masteries after committing to an active encounter or raid.")
        if self._expedition_load(twitch_id):
            return GameResult.fail("Return from your Expedition before changing Masteries.")
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before changing Masteries.")
        if str(twitch_id) in self.active_hunts:
            return GameResult.fail("Masteries are locked while your hero is away on a Hunt.")
        job = self._find_by_name_or_id(self.data.jobs, job_query)
        if not job:
            return GameResult.fail("Job not found.")
        row = self.db.one("SELECT level FROM player_jobs WHERE player_id=? AND job_id=?", (twitch_id, job["id"]))
        if not row or row["level"] < 50:
            return GameResult.fail(f"Master {job['name']} at JLv.50 before equipping {job['mastery']['name']}.")
        if slot not in {1, 2}:
            return GameResult.fail("Choose mastery slot 1 or 2. Example: !mastery warrior 1")
        self.db.execute(
            "INSERT INTO mastery_slots(player_id,slot,job_id) VALUES (?,?,?) ON CONFLICT(player_id,slot) DO UPDATE SET job_id=excluded.job_id",
            (twitch_id, slot, job["id"]),
        )
        return GameResult.success(f"Mastery Slot {slot}: {job['mastery']['name']} equipped — {job['mastery']['description']}")

    def clear_mastery(self, twitch_id: str, slot: int) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("You cannot change Masteries after committing to an active encounter or raid.")
        if self._expedition_load(twitch_id):
            return GameResult.fail("Return from your Expedition before changing Masteries.")
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before changing Masteries.")
        if str(twitch_id) in self.active_hunts:
            return GameResult.fail("Masteries are locked while your hero is away on a Hunt.")
        if slot not in {1, 2}:
            return GameResult.fail("Choose mastery slot 1 or 2.")
        current = self.db.one("SELECT job_id FROM mastery_slots WHERE player_id=? AND slot=?", (twitch_id, slot))
        if not current:
            return GameResult.success(f"Mastery Slot {slot} is already empty.", slot=slot, changed=False)
        self.db.execute("DELETE FROM mastery_slots WHERE player_id=? AND slot=?", (twitch_id, slot))
        return GameResult.success(f"Mastery Slot {slot} cleared.", slot=slot, changed=True)

    def set_stance(self, twitch_id: str, stance: str | None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if not stance:
            return GameResult.success(f"Current stance: {p['stance']}. Options: balanced, aggressive, defensive, magical, cautious.")
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("You cannot change stance after committing to an active encounter or raid.")
        if self._expedition_load(twitch_id):
            return GameResult.fail("Return from your Expedition before changing stance.")
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before changing stance.")
        if str(twitch_id) in self.active_hunts:
            return GameResult.fail("Your stance is locked while your hero is away on a Hunt.")
        stance = self._norm(stance)
        if stance not in STANCES:
            return GameResult.fail("Unknown stance. Use balanced, aggressive, defensive, magical, or cautious.")
        self.db.execute("UPDATE players SET stance=? WHERE twitch_id=?", (stance, twitch_id))
        return GameResult.success(f"Combat stance set to {stance}.")

    def _effective_camp_seconds_for_stream(self, stream_live: bool | None) -> int:
        """Return the authoritative Camp timer for the current stream state.

        LIVE uses a 15-minute base rest; OFFLINE and UNKNOWN fail closed to a
        60-minute base rest. Existing Fellowship/Infirmary Camp reductions still
        apply to the selected base duration.
        """
        base_seconds = CAMP_REST_ONLINE_SECONDS if stream_live is True else CAMP_REST_OFFLINE_SECONDS
        return self.fellowship_system.effective_camp_seconds(base_seconds)

    # ---------- recovery / camp ----------
    @_state_guard
    def rest(self, twitch_id: str, *, stream_live: bool | None = None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._expedition_load(twitch_id):
            return GameResult.fail("Use Expedition Camp or return from your Expedition before normal Camp recovery.")
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before setting up camp.")
        if str(twitch_id) in self.active_hunts:
            return GameResult.fail("Your hero cannot set up camp while away on a Hunt.")
        if twitch_id in self.encounter_roster:
            return GameResult.fail("You are already committed to the active encounter. Survive that before setting up camp.")
        if twitch_id in self.raid_roster:
            return GameResult.fail("You are registered for the active raid. The tent can wait until after the apocalypse.")
        if self._finish_rest_if_ready(twitch_id):
            p = self._player(twitch_id)
            resources = self._resource_state_for(p)
            summary = [f"HP {p['current_hp']}/{self._max_hp(p)}", *self._resource_text_parts(resources)]
            return GameResult.success(f"{p['display_name']} breaks camp fully restored: " + " | ".join(summary) + ".")
        remaining = self._camp_remaining(twitch_id)
        if remaining > 0:
            return GameResult.success(f"{p['display_name']} is resting at camp. Full recovery in {self._format_seconds(remaining)}.")

        max_hp = self._max_hp(p)
        resources = self._resource_state_for(p)
        needs_hp = int(p["current_hp"]) < max_hp
        needs_mp = int(resources["max_mp"]) > 0 and int(resources["mp"]) < int(resources["max_mp"])
        needs_ap = int(resources["max_ap"]) > 0 and int(resources["ap"]) < int(resources["max_ap"])
        if not (needs_hp or needs_mp or needs_ap):
            summary = [f"HP {max_hp}/{max_hp}", *self._resource_text_parts(resources)]
            return GameResult.success(
                f"{p['display_name']} is already fully recovered (" + " | ".join(summary) + "). No need to make the Moogle unfold a tent."
            )

        rest_seconds = self._effective_camp_seconds_for_stream(stream_live)
        until = int(time.time()) + rest_seconds
        self.db.execute("UPDATE players SET camp_until=?, rests=rests+1 WHERE twitch_id=?", (until, twitch_id))
        missing: list[str] = []
        if needs_hp:
            missing.append(f"{max_hp - max(0, int(p['current_hp']))} HP")
        if needs_mp:
            missing.append(f"{int(resources['max_mp']) - int(resources['mp'])} MP")
        if needs_ap:
            missing.append(f"{int(resources['max_ap']) - int(resources['ap'])} AP")
        return GameResult.success(
            f"CAMP — {p['display_name']} settles in to recover " + ", ".join(missing) + f". Rest completes in {self._format_seconds(rest_seconds)}.",
            "While resting you cannot Venture, Hunt, join encounters, or join raids. Use !rest to check the camp timer; a Tent can restore HP/MP/AP immediately with !use tent.",
        )

    @_state_guard
    def use_item(
        self,
        twitch_id: str,
        item_query: str,
        *,
        target_query: str | None = None,
        stream_live: bool | None = None,
    ) -> GameResult:
        actor = self._player(twitch_id)
        if not actor:
            return self._need_recruit()
        self._finish_rest_if_ready(twitch_id)
        actor = self._player(twitch_id)

        # During Active Battle, !use remains a queued combat action. Field
        # targeting stays separate so support outside combat never bypasses the
        # authoritative round/action system.
        if twitch_id in self.encounter_roster and self.active_encounter and self.active_encounter.get("state") == "combat":
            return self.battle_item(twitch_id, item_query)
        if twitch_id in self.raid_roster and self.active_boss and self.active_boss.get("state") == "combat":
            return self.battle_item(twitch_id, item_query)
        if self._expedition_load(twitch_id):
            return GameResult.fail("While on an Expedition, use items through Expedition combat or return to the Guild first.")
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("While on a Solo Venture, use battle items through the Adventure Board. Return or retreat before using field items.")
        if str(twitch_id) in self.active_hunts:
            return GameResult.fail("Your Hunt is resolving automatically; field items cannot be used until your hero returns.")

        item = self._find_by_name_or_id(self.data.items, item_query)
        use = item.get("use") if item else None
        if not item or not isinstance(use, dict) or not use.get("field"):
            return GameResult.fail("That item has no field use. It may still be usable during an Active Battle.")
        if self._inventory_qty(twitch_id, item["id"]) <= 0:
            return GameResult.fail(f"You do not own {item['name']}.")
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("Wait until you are outside the active encounter or raid before using field items.")

        target_id = str(twitch_id)
        target = actor
        requested_target = str(target_query or "").strip()
        if requested_target:
            matched = self._streamer_player_match(requested_target)
            if not matched:
                return GameResult.fail(
                    f"Adventurer '{requested_target}' was not found or is ambiguous. Use their exact Twitch username."
                )
            target_id = str(matched["twitch_id"])
            if target_id != str(twitch_id) and stream_live is not True:
                return GameResult.fail("Using a field item on another adventurer is available only while the stream is LIVE.")
            self._finish_rest_if_ready(target_id)
            target = self._player(target_id)
            if not target:
                return GameResult.fail("That adventurer is no longer available.")

        if target_id in self.encounter_roster or target_id in self.raid_roster:
            return GameResult.fail(f"{target['display_name']} is currently in battle; use battle targeting instead.")
        if self._expedition_load(target_id):
            return GameResult.fail(f"{target['display_name']} is away on an Expedition and cannot receive field items right now.")
        if self._solo_expedition_load(target_id):
            return GameResult.fail(f"{target['display_name']} is away on a Solo Venture and cannot receive field items right now.")
        if str(target_id) in self.active_hunts:
            return GameResult.fail(f"{target['display_name']} is away on a Hunt and cannot receive field items right now.")

        max_hp = self._max_hp(target)
        current = int(target["current_hp"])
        new_hp = current
        resources = self._resource_state_for(target)
        new_mp = int(resources["mp"])
        new_ap = int(resources["ap"])
        max_mp = int(resources["max_mp"])
        max_ap = int(resources["max_ap"])
        effects_done: list[str] = []

        for effect in use.get("effects", []):
            effect_type = effect.get("type")
            if effect_type == "heal_hp":
                if new_hp <= 0:
                    continue
                amount = int(effect.get("amount", 0))
                if effect.get("fraction") is not None:
                    amount = max(amount, int(max_hp * float(effect.get("fraction", 0))))
                before = new_hp
                new_hp = min(max_hp, new_hp + max(0, amount))
                if new_hp > before:
                    effects_done.append(f"restores {new_hp - before} HP")
            elif effect_type == "restore_mp" and max_mp > 0 and new_hp > 0:
                amount = max(0, int(effect.get("amount", 0)))
                if effect.get("fraction") is not None:
                    amount = max(amount, int(max_mp * float(effect.get("fraction", 0))))
                before = new_mp
                new_mp = min(max_mp, new_mp + amount)
                if new_mp > before:
                    effects_done.append(f"restores {new_mp - before} MP")
            elif effect_type == "restore_ap" and max_ap > 0 and new_hp > 0:
                amount = max(0, int(effect.get("amount", 0)))
                if effect.get("fraction") is not None:
                    amount = max(amount, int(max_ap * float(effect.get("fraction", 0))))
                before = new_ap
                new_ap = min(max_ap, new_ap + amount)
                if new_ap > before:
                    effects_done.append(f"restores {new_ap - before} AP")
            elif effect_type == "revive" and new_hp <= 0:
                fraction = float(effect.get("fraction", 0.30))
                new_hp = max(1, int(max_hp * fraction))
                effects_done.append(f"revives at {new_hp} HP")

        # Tent is the immediate full-rest field item for the selected target.
        if item["id"] == "tent":
            needs_any = (
                new_hp < max_hp
                or (max_mp > 0 and new_mp < max_mp)
                or (max_ap > 0 and new_ap < max_ap)
                or int(target["camp_until"] or 0) > 0
            )
            if needs_any:
                new_hp = max_hp
                new_mp = max_mp if max_mp > 0 else new_mp
                new_ap = max_ap if max_ap > 0 else new_ap
                effects_done = ["fully restores HP/MP/AP and breaks camp"]

        if not effects_done:
            if current <= 0:
                return GameResult.fail(f"{target['display_name']} is KO'd. Use a Phoenix Down or Tent to revive them.")
            full_parts = [current >= max_hp]
            if max_mp > 0:
                full_parts.append(new_mp >= max_mp)
            if max_ap > 0:
                full_parts.append(new_ap >= max_ap)
            if all(full_parts):
                return GameResult.fail(f"{target['display_name']}'s applicable HP/MP/AP resources are already full.")
            return GameResult.fail(f"{item['name']} has no useful field effect on {target['display_name']} right now.")

        self._change_item(twitch_id, item["id"], -1, "field_use")
        self.db.execute("UPDATE players SET current_hp=?, camp_until=0 WHERE twitch_id=?", (new_hp, target_id))
        resource_meta = {"mp": new_mp, "max_mp": max_mp, "ap": new_ap, "max_ap": max_ap}
        self._save_resources_from_meta(target_id, resource_meta)
        summary = [f"HP {new_hp}/{max_hp}", *self._resource_text_parts(resource_meta)]
        actor_name = str(actor["display_name"] or actor["username"])
        target_name = str(target["display_name"] or target["username"])
        lead = f"{actor_name} uses {item['name']}" if target_id == str(twitch_id) else f"{actor_name} uses {item['name']} on {target_name}"
        return GameResult.success(
            f"{lead} and {'; '.join(effects_done)}. " + " | ".join(summary) + "."
        )

    # ---------- regions ----------
    def regions(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        parts = []
        for region in sorted(self.data.regions.values(), key=lambda r: r["min_level"]):
            state = "✓" if p["level"] >= region["min_level"] else f"Lv.{region['min_level']}"
            parts.append(f"{region['name']} [{state}]")
        return GameResult.success("Regions: " + " | ".join(parts))

    @_state_guard
    def travel(self, twitch_id: str, region_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        blocked = self._activity_block(twitch_id)
        if blocked:
            return GameResult.fail(blocked)
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("Finish your active encounter or raid before traveling.")
        p = self._player(twitch_id)
        region = self._find_by_name_or_id(self.data.regions, region_query)
        if not region:
            return GameResult.fail("Region not found. Use !regions to see available destinations.")
        if p["level"] < region["min_level"]:
            return GameResult.fail(f"{region['name']} requires Lv.{region['min_level']}. You are Lv.{p['level']}.")
        self.db.execute("UPDATE players SET current_region=? WHERE twitch_id=?", (region["id"], twitch_id))
        return GameResult.success(f"Travel complete: {p['display_name']} arrives at {region['name']}. {region['description']}")

    # ---------- venture / active battle ----------
    # NOTE FOR FUTURE EDITS:
    # Random encounters have two explicit phases: ``rally`` and ``combat``.
    # The daemon is the *only* live owner of timed deadline transitions. Player
    # commands may join/queue/read state, but never start or resolve an overdue
    # phase. This invariant is enforced at the engine boundary, not just Twitch.
    # Keep rewards/persistence in _finish_active_encounter() and battle math in
    # the helpers below; doing so prevents chat handlers from becoming combat
    # logic and keeps timed/background resolution deterministic and testable.
    @staticmethod
    def _venture_item_level(item: dict[str, Any]) -> int | None:
        """Return the progression level used for Venture treasure filtering.

        Equipment already exposes ``min_level``. Consumables do not have an
        equip requirement, so their shop/unlock tier is the closest equivalent
        progression marker. Items without a meaningful level are not chest
        candidates because they cannot be proven appropriate for the player.
        """
        raw = item.get("min_level")
        if raw is None:
            raw = item.get("shop_level")
        if raw is None:
            return None
        try:
            level = int(raw)
        except (TypeError, ValueError):
            return None
        return max(1, level)

    def _venture_treasure_candidates(self, player_level: int) -> tuple[int, int, dict[str, list[dict[str, Any]]]]:
        """Return level-banded, progression-safe chest candidates by category."""
        level = max(1, int(player_level))
        min_level = max(1, level - VENTURE_TREASURE_LEVEL_BELOW_PLAYER)
        max_level = level + VENTURE_TREASURE_LEVEL_ABOVE_PLAYER
        candidates: dict[str, list[dict[str, Any]]] = {
            category: [] for category in VENTURE_TREASURE_CATEGORY_WEIGHTS
        }

        for item in self.data.items.values():
            category = str(item.get("type", ""))
            if category not in candidates:
                continue
            # Never bypass the dedicated Relic progression path or hand out
            # other explicitly non-transferable progression pieces.
            if item.get("relic_id") or item.get("unsellable"):
                continue
            item_level = self._venture_item_level(item)
            if item_level is None or not min_level <= item_level <= max_level:
                continue
            candidates[category].append(item)

        return min_level, max_level, candidates

    def _roll_venture_treasure(self, player_level: int) -> tuple[dict[str, Any], int, int, int] | None:
        """Choose a category then a rarity-weighted item for a treasure Venture."""
        min_level, max_level, candidates = self._venture_treasure_candidates(player_level)
        available_categories = [
            category for category, items in candidates.items() if items
        ]
        if not available_categories:
            return None

        category = self.rng.choices(
            available_categories,
            weights=[VENTURE_TREASURE_CATEGORY_WEIGHTS[category] for category in available_categories],
            k=1,
        )[0]
        items = candidates[category]
        item = self.rng.choices(
            items,
            weights=[
                VENTURE_TREASURE_RARITY_WEIGHTS.get(str(row.get("rarity", "common")).lower(), 1)
                for row in items
            ],
            k=1,
        )[0]
        item_level = self._venture_item_level(item)
        if item_level is None:  # Defensive; candidates already guarantee this.
            return None
        return item, item_level, min_level, max_level

    def _resolve_venture_treasure(self, twitch_id: str, p: Any, region: dict[str, Any]) -> GameResult | None:
        rolled = self._roll_venture_treasure(int(p["level"]))
        if not rolled:
            # A custom data pack can theoretically contain no chest-safe item
            # in the current band. Fall through to combat rather than consuming
            # a Venture on an empty chest.
            return None

        item, item_level, min_level, max_level = rolled
        self._set_cooldown(twitch_id, "venture", self.venture_cooldown_seconds)
        self.db.execute(
            "UPDATE players SET ventures=ventures+1, updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
            (twitch_id,),
        )
        self._change_item(twitch_id, item["id"], 1, "venture_treasure")
        venture_no = int(p["ventures"]) + 1
        fellowship_notes = self.fellowship_system.record_activity(
            twitch_id, "venture_complete", event_key=f"venture_treasure:{twitch_id}:{venture_no}"
        )
        fellowship_notes.extend(self.fellowship_system.record_activity(
            twitch_id, "treasure", renown=0, event_key=f"treasure:{twitch_id}:{venture_no}"
        ))
        chocobo_notes = self._award_chocobo_xp(twitch_id, 8)

        rarity = str(item.get("rarity", "common")).title()
        category = str(item.get("type", "item")).replace("_", " ").title()
        return GameResult.success(
            f"TREASURE CHEST — {p['display_name']} discovers a chest in {region['name']}!",
            f"FOUND — {item['name']} ({category} • Lv.{item_level} • {rarity}) has been added to your inventory.",
            *fellowship_notes[:2],
            *chocobo_notes[:2],
            venture_event="treasure",
            treasure_item_id=item["id"],
            treasure_item_level=item_level,
            treasure_level_min=min_level,
            treasure_level_max=max_level,
        )

    def _solo_result_vitals(self, twitch_id: str) -> dict[str, int]:
        """Return compact post-action vitals for Portal Solo Venture results."""
        p = self._player(twitch_id)
        if not p or p["current_job"] not in self.data.jobs:
            return {"hp": 0, "max_hp": 0, "mp": 0, "max_mp": 0, "ap": 0, "max_ap": 0}
        job = self.data.jobs[p["current_job"]]
        effects = self._effects(twitch_id, p["current_job"])
        stats = self._stats(p, job, effects)
        resources = self._resource_state_for(p, job, stats)
        return {
            "hp": max(0, int(p["current_hp"] or 0)),
            "max_hp": max(0, int(stats.get("hp", 0))),
            "mp": max(0, int(resources.get("mp", 0))),
            "max_mp": max(0, int(resources.get("max_mp", 0))),
            "ap": max(0, int(resources.get("ap", 0))),
            "max_ap": max(0, int(resources.get("max_ap", 0))),
        }

    def _persist_portal_adventure_result(
        self, twitch_id: str, kind: str, result: dict[str, Any], *, source_action_id: str = ""
    ) -> int:
        """Store an Adventure Board result until the player explicitly confirms it.

        These rows intentionally have no time-based expiry while unacknowledged.
        This lets a player leave the Portal during a timed Hunt or Solo Venture
        and still see the authoritative result when they return later.
        """
        player_id = str(twitch_id)
        created_at = int(time.time())
        payload = copy.deepcopy(result)
        payload["kind"] = str(kind or payload.get("kind") or "adventure")
        payload["finished_at"] = int(payload.get("finished_at") or created_at)
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        with self.db.tx() as conn:
            cursor = conn.execute(
                "INSERT INTO portal_adventure_results(player_id,kind,result_json,created_at,acknowledged_at,source_action_id) "
                "VALUES (?,?,?,?,NULL,?)",
                (player_id, payload["kind"], encoded, created_at, str(source_action_id or "") or None),
            )
            # Acknowledged history is only diagnostic; prune old confirmed rows.
            # Pending rows are never pruned automatically.
            conn.execute(
                "DELETE FROM portal_adventure_results WHERE player_id=? AND acknowledged_at IS NOT NULL "
                "AND acknowledged_at < ?",
                (player_id, created_at - 30 * 24 * 60 * 60),
            )
            return int(cursor.lastrowid)

    def _pending_portal_adventure_results(self, twitch_id: str, limit: int = 8) -> list[dict[str, Any]]:
        rows = self.db.all(
            "SELECT id,kind,result_json,created_at FROM portal_adventure_results "
            "WHERE player_id=? AND acknowledged_at IS NULL ORDER BY created_at DESC,id DESC LIMIT ?",
            (str(twitch_id), max(1, min(20, int(limit)))),
        )
        pending: list[dict[str, Any]] = []
        for row in rows:
            try:
                payload = json.loads(str(row["result_json"]))
            except (TypeError, ValueError, json.JSONDecodeError):
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
            payload["result_id"] = int(row["id"])
            payload["kind"] = str(payload.get("kind") or row["kind"] or "adventure")
            payload["finished_at"] = int(payload.get("finished_at") or row["created_at"] or 0)
            payload["requires_confirmation"] = True
            pending.append(payload)
        return pending

    def _ack_portal_adventure_result(self, twitch_id: str, result_id: int) -> bool:
        row = self.db.one(
            "SELECT id,acknowledged_at FROM portal_adventure_results WHERE id=? AND player_id=?",
            (int(result_id), str(twitch_id)),
        )
        if not row:
            return False
        if row["acknowledged_at"] is None:
            self.db.execute(
                "UPDATE portal_adventure_results SET acknowledged_at=? WHERE id=? AND player_id=? AND acknowledged_at IS NULL",
                (int(time.time()), int(result_id), str(twitch_id)),
            )
        return True

    def _remember_adventure_result(self, twitch_id: str, summary: dict[str, Any]) -> None:
        finished_at = int(time.time())
        self._last_adventure_result = {
            "participants": [str(twitch_id)],
            "finished_at": finished_at,
            "summary": copy.deepcopy(summary),
        }
        result = {
            "title": str(summary.get("title") or "Solo Venture Result"),
            "won": str(summary.get("outcome") or "") != "defeat",
            "finished_at": finished_at,
            "kind": "solo_venture",
            "monster_name": str((summary.get("enemy") or {}).get("name") or ""),
            "hunt_name": None,
            "messages": [],
            "summary": copy.deepcopy(summary),
        }
        self._persist_portal_adventure_result(twitch_id, "solo_venture", result)

    def _remember_portal_hunt_result(
        self, twitch_id: str, summary: dict[str, Any], messages: list[str], *, source_action_id: str = ""
    ) -> None:
        finished_at = int(time.time())
        monster = summary.get("monster") or {}
        result = {
            "title": str(summary.get("title") or "Hunt Result"),
            "won": str(summary.get("outcome") or "") == "victory",
            "finished_at": finished_at,
            "kind": "hunt",
            "monster_name": str(monster.get("name") or "Unknown Mark"),
            "hunt_name": str(summary.get("hunt_name") or "Hunt"),
            "messages": [str(value) for value in list(messages or [])[:4]],
            "summary": copy.deepcopy(summary),
        }
        self._persist_portal_adventure_result(
            twitch_id, "hunt", result, source_action_id=source_action_id
        )

    # ---------- Wayfarer Solo Ventures ----------
    def _solo_expedition_load(self, twitch_id: str) -> dict[str, Any] | None:
        row = self.db.one("SELECT state_json FROM solo_expeditions WHERE player_id=?", (str(twitch_id),))
        if not row:
            return None
        try:
            state = json.loads(str(row["state_json"]))
            return state if isinstance(state, dict) else None
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    def _solo_expedition_save(self, twitch_id: str, state: dict[str, Any]) -> None:
        now = int(time.time())
        started = int(state.get("started_at") or now)
        state["updated_at"] = now
        self.db.execute(
            "INSERT INTO solo_expeditions(player_id,state_json,started_at,updated_at) VALUES (?,?,?,?) "
            "ON CONFLICT(player_id) DO UPDATE SET state_json=excluded.state_json,updated_at=excluded.updated_at",
            (str(twitch_id), json.dumps(state, separators=(",", ":"), sort_keys=True), started, now),
        )

    def _solo_expedition_delete(self, twitch_id: str) -> None:
        self.db.execute("DELETE FROM solo_expeditions WHERE player_id=?", (str(twitch_id),))

    @staticmethod
    def _solo_stage_multiplier(stage: int) -> float:
        return 1.0 + max(0, int(stage) - 1) * SOLO_EXPEDITION_STAGE_BONUS

    def _roll_solo_expedition_treasure(self, player_level: int, stage: int) -> tuple[dict[str, Any], int, int, int] | None:
        """Roll Solo Venture treasure with deeper-stage quality bias.

        The event odds are the player-facing 80% Encounter / 20% Treasure at
        every stage. Pressing on improves the *quality* of a chest rather than
        quietly changing those published odds.
        """
        min_level, max_level, candidates = self._venture_treasure_candidates(player_level)
        available_categories = [category for category, items in candidates.items() if items]
        if not available_categories:
            return None
        category = self.rng.choices(
            available_categories,
            weights=[VENTURE_TREASURE_CATEGORY_WEIGHTS[category] for category in available_categories],
            k=1,
        )[0]
        items = candidates[category]
        stage = max(1, min(SOLO_EXPEDITION_MAX_STAGES, int(stage)))
        rarity_bias = {
            1: {},
            2: {"common": 0.88, "uncommon": 1.08, "rare": 1.30, "epic": 1.45, "relic": 1.55, "artifact": 1.70, "legendary": 1.80},
            3: {"common": 0.68, "uncommon": 1.05, "rare": 1.65, "epic": 2.00, "relic": 2.20, "artifact": 2.45, "legendary": 2.70},
        }[stage]
        item = self.rng.choices(
            items,
            weights=[
                VENTURE_TREASURE_RARITY_WEIGHTS.get(str(row.get("rarity", "common")).lower(), 1)
                * float(rarity_bias.get(str(row.get("rarity", "common")).lower(), 1.0))
                for row in items
            ],
            k=1,
        )[0]
        item_level = self._venture_item_level(item)
        if item_level is None:
            return None
        return item, item_level, min_level, max_level

    def _solo_owned_battle_items(self, twitch_id: str, meta: dict[str, Any]) -> list[dict[str, Any]]:
        rows = self.db.all(
            "SELECT item_id,quantity FROM inventory WHERE player_id=? AND quantity>0 ORDER BY item_id",
            (str(twitch_id),),
        )
        result: list[dict[str, Any]] = []
        for row in rows:
            item = self.data.items.get(str(row["item_id"]))
            use = item.get("use") if item and isinstance(item.get("use"), dict) else None
            if not item or not use or item.get("id") == "tent" or not use.get("battle", True):
                continue
            effects = list(use.get("effects") or [])
            requires_revive = any(effect.get("type") == "revive" for effect in effects)
            target = str(use.get("target", "ally"))
            usable = not requires_revive and int(meta.get("hp", 0)) > 0
            reason = "Revive items cannot target the acting hero while they are conscious." if requires_revive else ""
            if usable and any(effect.get("type") == "restore_mp" for effect in effects) and int(meta.get("max_mp", 0)) <= 0:
                usable = False
                reason = "Your current Job does not use MP."
            if usable and any(effect.get("type") == "restore_ap" for effect in effects) and int(meta.get("max_ap", 0)) <= 0:
                usable = False
                reason = "Your current Job does not use AP."
            result.append({
                "id": str(item["id"]),
                "name": str(item.get("name") or item["id"]),
                "quantity": int(row["quantity"] or 0),
                "description": str(item.get("description") or ""),
                "target": target,
                "usable": bool(usable),
                "reason": reason,
            })
        return result

    def _solo_ability_rows(self, meta: dict[str, Any]) -> list[dict[str, Any]]:
        job = self.data.jobs.get(str(meta.get("job_id"))) or {}
        job_level = int(meta.get("job_level", 0))
        rows: list[dict[str, Any]] = []
        for ability in self.data.active_abilities.get(str(meta.get("job_id")), []):
            unlocked = int(ability.get("level", 1)) <= job_level
            resource = ability_resource(ability, job)
            cost = ability_cost(ability)
            enough = int(meta.get(resource, 0)) >= cost
            silenced = resource == "mp" and has_status(meta.get("statuses", {}), "silence")
            revive = any(effect.get("type") == "revive" for effect in ability.get("effects", []))
            usable = unlocked and enough and not silenced and not revive
            reason = ""
            if not unlocked:
                reason = f"Unlocks at JLv.{int(ability.get('level', 1))}."
            elif revive:
                reason = "Revive abilities need another KO'd ally."
            elif silenced:
                reason = "Silence prevents MP abilities."
            elif not enough:
                reason = f"Needs {cost} {resource.upper()}."
            traits: list[str] = []
            element = str(ability.get("element") or "").strip()
            if element:
                traits.append(element)
            for effect in ability.get("effects", []):
                effect_type = str(effect.get("type") or "")
                if effect_type == "status":
                    label = str(effect.get("status") or "").replace("_", " ").title()
                    if label and label not in traits:
                        traits.append(label)
                elif effect_type == "heal" and "Healing" not in traits:
                    traits.append("Healing")
                elif effect_type == "cleanse" and "Cleanse" not in traits:
                    traits.append("Cleanse")
                elif effect_type == "drain" and "HP Drain" not in traits:
                    traits.append("HP Drain")
                elif effect_type == "restore_mp" and "MP Restore" not in traits:
                    traits.append("MP Restore")
                elif effect_type == "restore_ap" and "AP Restore" not in traits:
                    traits.append("AP Restore")
                elif effect_type == "revive" and "Revive" not in traits:
                    traits.append("Revive")
                elif effect_type == "damage":
                    if float(effect.get("pierce", 0) or 0) > 0 and "Piercing" not in traits:
                        traits.append("Piercing")
                    if float(effect.get("crit_bonus", 0) or 0) > 0 and "High Crit" not in traits:
                        traits.append("High Crit")
            rows.append({
                "id": str(ability["id"]),
                "name": str(ability.get("name") or ability["id"]),
                "level": int(ability.get("level", 1)),
                "resource": resource,
                "cost": cost,
                "target": str(ability.get("target") or "enemy"),
                "description": str(ability.get("description") or ""),
                "element": element,
                "traits": traits,
                "usable": bool(usable),
                "reason": reason,
            })
        return rows

    def _solo_enemy_intent(self, monster: dict[str, Any], encounter: dict[str, Any]) -> dict[str, Any]:
        statuses = encounter.setdefault("monster_statuses", {})
        if has_status(statuses, "stun"):
            return {"kind": "stunned", "label": f"{monster['name']} is stunned."}
        behavior = self.data.enemy_actions.get(monster["id"], {"profile": "balanced"})
        profile = self.data.enemy_profiles.get(
            behavior.get("profile"), self.data.enemy_profiles.get("balanced", {})
        )
        round_no = int(encounter.get("round", 1))
        action = choose_enemy_action(
            behavior,
            profile,
            hp_ratio=int(encounter.get("monster_hp", 0)) / max(1, int(encounter.get("monster_max_hp", 1))),
            round_no=round_no,
            special_ready_round=int(encounter.get("enemy_special_ready_round", 1)),
            monster_statuses=statuses,
            rng=self.rng,
        )
        kind = str(action.get("kind") or "attack")
        if kind == "special":
            ability = dict(action.get("ability") or {})
            return {"kind": "special", "ability": ability, "label": f"Preparing: {ability.get('name', 'special attack')}"}
        if kind == "utility":
            utility = dict(action.get("utility") or {})
            return {"kind": "utility", "utility": utility, "label": f"Preparing: {utility.get('name', 'defensive technique')}"}
        return {"kind": "attack", "label": "Preparing: Attack"}

    def _solo_resolve_enemy_intent(self, monster: dict[str, Any], encounter: dict[str, Any], log: list[str]) -> None:
        statuses = encounter.setdefault("monster_statuses", {})
        if has_status(statuses, "stun"):
            log.append(f"{monster['name']} is stunned and loses its turn.")
            return
        intent = dict(encounter.get("enemy_intent") or {"kind": "attack"})
        kind = str(intent.get("kind") or "attack")
        behavior = self.data.enemy_actions.get(monster["id"], {"profile": "balanced"})
        profile = self.data.enemy_profiles.get(
            behavior.get("profile"), self.data.enemy_profiles.get("balanced", {})
        )
        target_id = self._enemy_target_id()
        if not target_id:
            return
        if kind == "special" and intent.get("ability"):
            ability = dict(intent["ability"])
            self._resolve_enemy_special(monster, profile, ability, log)
            encounter["enemy_special_ready_round"] = int(encounter.get("round", 1)) + int(ability.get("cooldown", 1)) + 1
            return
        if kind == "utility" and intent.get("utility"):
            utility = dict(intent["utility"])
            status_id = str(utility.get("status", ""))
            apply_status(statuses, status_id, int(utility.get("turns", 1)), float(utility.get("magnitude", 0.0)))
            log.append(f"{monster['name']} uses {utility.get('name', 'Brace')} — {status_id.replace('_', ' ').title()}.")
            return
        target = self.encounter_roster[target_id]
        damage = self._apply_enemy_hit(monster, target, profile, scaling="physical", power=1.0)
        log.append(f"{target['name']} evades {monster['name']}'s attack." if damage == 0 else f"{monster['name']} attacks {target['name']} for {damage}.")

    def _solo_select_monster(self, p: Any, region: dict[str, Any], stage: int) -> dict[str, Any] | None:
        level = int(p["level"])
        minimum = max(1, level - 2)
        maximum = level + SOLO_VENTURE_MAX_LEVEL_ABOVE_PLAYER
        candidates = []
        weights = []
        for encounter in region.get("encounters", []):
            monster = self.data.monsters.get(encounter.get("monster_id"))
            if not monster:
                continue
            monster_level = int(monster.get("level", 1))
            if minimum <= monster_level <= maximum:
                delta = monster_level - level
                stage_bias = {
                    1: {-2: 0.85, -1: 1.20, 0: 1.45, 1: 1.15, 2: 0.75, 3: 0.40, 4: 0.22, 5: 0.12},
                    2: {-2: 0.45, -1: 0.85, 0: 1.25, 1: 1.45, 2: 1.10, 3: 0.70, 4: 0.45, 5: 0.25},
                    3: {-2: 0.20, -1: 0.55, 0: 0.95, 1: 1.35, 2: 1.55, 3: 1.25, 4: 0.90, 5: 0.60},
                }.get(int(stage), {})
                candidates.append(monster)
                weights.append(max(0.01, float(encounter.get("weight", 1.0)) * float(stage_bias.get(delta, 1.0))))
        if not candidates:
            for encounter in region.get("encounters", []):
                monster = self.data.monsters.get(encounter.get("monster_id"))
                if monster and int(monster.get("level", 1)) <= maximum:
                    candidates.append(monster)
                    weights.append(max(0.01, float(encounter.get("weight", 1.0))))
        return self.rng.choices(candidates, weights=weights, k=1)[0] if candidates else None

    def _solo_begin_stage(self, twitch_id: str, expedition: dict[str, Any]) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        region = self.data.regions.get(str(expedition.get("region_id"))) or self.data.regions[p["current_region"]]
        stage = int(expedition.get("stage", 1))
        expedition["status"] = "event"
        expedition["event"] = None
        expedition["combat"] = None
        treasure_roll = SOLO_VENTURE_TREASURE_CHANCE >= 1.0 or (
            SOLO_VENTURE_TREASURE_CHANCE > 0.0 and self.rng.random() < SOLO_VENTURE_TREASURE_CHANCE
        )
        if treasure_roll:
            rolled = self._roll_solo_expedition_treasure(int(p["level"]), stage)
            if rolled:
                item, item_level, _, _ = rolled
                spoil = {"id": str(item["id"]), "name": str(item["name"]), "quantity": 1, "kind": "treasure"}
                expedition.setdefault("spoils", {}).setdefault("items", []).append(spoil)
                expedition.setdefault("history", []).append({"stage": stage, "type": "treasure", "label": f"Found {item['name']}"})
                expedition["event"] = {
                    "type": "treasure",
                    "item": {"id": str(item["id"]), "name": str(item["name"]), "level": int(item_level), "rarity": str(item.get("rarity", "common")).title(), "category": str(item.get("type", "item")).replace("_", " ").title()},
                }
                expedition["status"] = "choice"
                self.db.update_record_stats(twitch_id, {"solo_venture_treasures": 1})
                self._solo_expedition_save(twitch_id, expedition)
                if stage >= SOLO_EXPEDITION_MAX_STAGES:
                    return self._solo_bank_spoils(twitch_id, expedition, outcome="complete")
                return GameResult.success(f"SOLO VENTURE · STAGE {stage} — Treasure found: {item['name']}.", solo_expedition_stage_complete=True)

        monster = self._solo_select_monster(p, region, stage)
        if not monster:
            # A malformed/custom region should not strand a newly started run.
            # Only the first stage can be rolled before the player has received
            # anything, so unwind its cooldown/counter cleanly.
            if stage == 1 and not expedition.get("history"):
                self._solo_expedition_delete(twitch_id)
                self.db.execute("DELETE FROM cooldowns WHERE player_id=? AND action='solo_venture'", (twitch_id,))
                self.db.execute("UPDATE players SET ventures=MAX(0,ventures-1) WHERE twitch_id=?", (twitch_id,))
                self.db.update_record_stats(twitch_id, {"solo_ventures": -1})
            return GameResult.fail(f"No level-appropriate Solo Venture monsters are available in {region['name']} right now.")
        encounter = {
            "id": int(expedition.get("started_at", time.time())) * 10 + stage,
            "kind": "solo_expedition",
            "state": "combat",
            "monster_id": str(monster["id"]),
            "region_id": str(region["id"]),
            "created_at": int(time.time()),
            "starter_id": str(twitch_id),
        }
        roster = {str(twitch_id): {"name": p["display_name"], "username": p["username"], "job_id": p["current_job"]}}
        old_encounter, old_roster = self.active_encounter, self.encounter_roster
        try:
            self.active_encounter, self.encounter_roster = encounter, roster
            combatants, _, _ = self._initialize_active_combat(encounter)
            if combatants == 0:
                return GameResult.fail("Solo Venture cannot continue while your hero is unable to fight.")
            encounter["enemy_intent"] = self._solo_enemy_intent(monster, encounter)
            expedition["combat"] = {"encounter": copy.deepcopy(encounter), "roster": copy.deepcopy(roster)}
        finally:
            self.active_encounter, self.encounter_roster = old_encounter, old_roster
        expedition["event"] = {"type": "encounter", "monster_id": str(monster["id"])}
        expedition["status"] = "combat"
        expedition.setdefault("history", []).append({"stage": stage, "type": "encounter", "label": f"Encountered {monster['name']}"})
        self.db.update_record_stats(twitch_id, {"solo_venture_encounters": 1})
        self._solo_expedition_save(twitch_id, expedition)
        return GameResult.success(f"SOLO VENTURE · STAGE {stage} — {monster['name']} (Lv.{monster['level']}) blocks the road.", solo_expedition_battle=True)

    def _solo_roll_stage_rewards(self, twitch_id: str, monster: dict[str, Any], stage: int) -> dict[str, Any]:
        p = self._player(twitch_id)
        multiplier = self._solo_stage_multiplier(stage)
        level_factor = encounter_reward_factor(p["level"], monster["level"])
        job_level = self._job_level(twitch_id, p["current_job"])
        jp_factor = jp_reward_factor(p["level"], job_level, monster["level"])
        xp = max(5, int(monster["xp"] * level_factor * multiplier * self.rng.uniform(0.92, 1.08)))
        jp = self.fellowship_system.apply_jp_bonus(max(2, int(monster["jp"] * jp_factor * multiplier * self.rng.uniform(0.95, 1.10))))
        gil = max(1, int(monster["gil"] * level_factor * multiplier * self.rng.uniform(0.85, 1.18)))
        job = self.data.jobs[p["current_job"]]
        effects = self._effects(twitch_id, p["current_job"])
        gil = int(gil * (1 + job.get("gil_bonus", 0) + effects.get("gil_bonus", 0)))
        loot_bonus = job.get("loot_bonus", 0) + effects.get("loot_bonus", 0)
        pending_items: list[dict[str, Any]] = []
        for drop in monster.get("drops", []):
            chance = min(0.95, float(drop["chance"]) * (1 + loot_bonus))
            if self.rng.random() <= chance:
                qty = self.rng.randint(int(drop.get("min", 1)), int(drop.get("max", 1)))
                item_id = str(drop["item_id"])
                pending_items.append({"id": item_id, "name": str(self.data.items[item_id]["name"]), "quantity": qty, "kind": "drop"})
        with self.db.tx() as conn:
            conn.execute("UPDATE players SET xp=xp+?, monsters_defeated=monsters_defeated+1 WHERE twitch_id=?", (xp, twitch_id))
            conn.execute("UPDATE player_jobs SET jp=jp+? WHERE player_id=? AND job_id=?", (jp, twitch_id, p["current_job"]))
            conn.execute("INSERT INTO bestiary(player_id,monster_id,defeats) VALUES (?,?,1) ON CONFLICT(player_id,monster_id) DO UPDATE SET defeats=defeats+1", (twitch_id, monster["id"]))
        # Rare pity drops and recipe discoveries are progression systems rather
        # than ordinary loose expedition cargo. Preserve their existing combat
        # semantics by securing them immediately; normal drops remain at risk.
        secured_loot = self._roll_pity_drops(twitch_id, monster, source=f"solo_expedition:{monster['id']}", loot_bonus=loot_bonus)
        secured_loot.extend(self._roll_recipe_drops(twitch_id, monster, source=f"solo_expedition:{monster['id']}", loot_bonus=loot_bonus))
        levelups = self._process_levels(twitch_id, p["current_job"])
        return {"xp": xp, "jp": jp, "gil": gil, "items": pending_items, "secured_loot": secured_loot, "levelups": levelups, "multiplier_percent": int(round((multiplier - 1.0) * 100))}

    def _solo_bank_spoils(self, twitch_id: str, expedition: dict[str, Any], *, outcome: str = "returned") -> GameResult:
        spoils = expedition.setdefault("spoils", {"gil": 0, "items": []})
        gil = max(0, int(spoils.get("gil", 0)))
        items = list(spoils.get("items") or [])
        if gil:
            with self.db.tx() as conn:
                conn.execute("UPDATE players SET gil=gil+? WHERE twitch_id=?", (gil, twitch_id))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,'solo_expedition')", (twitch_id, gil))
        for item in items:
            self._change_item(twitch_id, str(item["id"]), max(1, int(item.get("quantity", 1))), "solo_expedition")
        stage = int(expedition.get("stage", 1))
        renown = min(6, SOLO_VENTURE_FELLOWSHIP_RENOWN + max(0, stage - 1))
        fellowship_notes = self.fellowship_system.record_activity(
            twitch_id, "venture_complete", renown=renown,
            event_key=f"solo_expedition:{twitch_id}:{int(expedition.get('started_at', 0))}",
        )
        chocobo_notes = self._award_chocobo_xp(twitch_id, 8 + stage * 4)
        achievements = self._check_achievements(twitch_id)
        secured = expedition.get("secured") or {}
        item_labels = [f"{row.get('name', row.get('id'))} x{int(row.get('quantity', 1))}" for row in items]
        secured_loot = [str(value) for value in expedition.get("secured_loot", [])]
        summary = {
            "type": "expedition",
            "outcome": outcome,
            "title": "Solo Venture Complete" if stage >= SOLO_EXPEDITION_MAX_STAGES else "Returned to Guild",
            "region_name": str((self.data.regions.get(str(expedition.get("region_id"))) or {}).get("name") or "Unknown Region"),
            "stages": stage,
            "rewards": {
                "xp": int(secured.get("xp", 0)), "jp": int(secured.get("jp", 0)), "gil": gil,
                "loot": [*secured_loot, *item_labels], "secured_loot": secured_loot, "fellowship_renown": renown, "achievements": [str(x) for x in achievements[:4]],
            },
            "history": list(expedition.get("history") or [])[-8:],
            "notes": [str(x) for x in [*fellowship_notes[:2], *chocobo_notes[:2]]],
            "player": self._solo_result_vitals(twitch_id),
            "cooldown_seconds": SOLO_VENTURE_COOLDOWN_SECONDS,
            "interactive": True,
        }
        self._remember_adventure_result(twitch_id, summary)
        self._solo_expedition_delete(twitch_id)
        return GameResult.success(
            f"SOLO VENTURE — {stage} stage{'s' if stage != 1 else ''} complete. Banked {gil} Gil"
            + (f" and {len(items)} spoil stack{'s' if len(items) != 1 else ''}." if items else "."),
            solo_result=summary, solo_expedition_finished=True,
        )

    def _solo_finish_defeat(self, twitch_id: str, expedition: dict[str, Any], monster: dict[str, Any], meta: dict[str, Any], round_no: int, log: list[str]) -> GameResult:
        self._save_hp(twitch_id, int(meta.get("hp", 0)))
        self._save_resources_from_meta(twitch_id, meta)
        knocked_out = int(meta.get("hp", 0)) <= 0
        if knocked_out:
            self.db.execute("UPDATE players SET deaths=deaths+1 WHERE twitch_id=?", (twitch_id,))
        self._record_combat_metrics(
            twitch_id, meta.get("job_id"), monster["id"], battle_type="venture", won=False, knocked_out=knocked_out,
            damage_dealt=int(meta.get("damage", 0)), damage_taken=int(meta.get("damage_taken", 0)), healing_done=int(meta.get("healing", 0)), best_hit=int(meta.get("best_hit", 0)),
        )
        self.db.update_record_stats(twitch_id, {"active_actions": int(meta.get("actions", 0)), "active_abilities": int(meta.get("abilities_used", 0)), "active_items": int(meta.get("items_used", 0)), "active_defends": int(meta.get("defends", 0))})
        spoils = expedition.setdefault("spoils", {"gil": 0, "items": []})
        kept_gil = int(max(0, int(spoils.get("gil", 0))) * SOLO_EXPEDITION_DEFEAT_GIL_KEEP)
        if kept_gil:
            with self.db.tx() as conn:
                conn.execute("UPDATE players SET gil=gil+? WHERE twitch_id=?", (kept_gil, twitch_id))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,'solo_expedition_recovery')", (twitch_id, kept_gil))
        achievements = self._check_achievements(twitch_id)
        secured = expedition.get("secured") or {}
        summary = {
            "type": "expedition", "outcome": "defeat", "title": "Solo Venture Defeat",
            "region_name": str((self.data.regions.get(str(expedition.get("region_id"))) or {}).get("name") or "Unknown Region"),
            "stages": int(expedition.get("stage", 1)), "rounds": int(round_no),
            "enemy": {"id": str(monster["id"]), "name": str(monster["name"]), "level": int(monster["level"])},
            "rewards": {"xp": int(secured.get("xp", 0)), "jp": int(secured.get("jp", 0)), "gil": kept_gil, "loot": [str(x) for x in expedition.get("secured_loot", [])], "secured_loot": [str(x) for x in expedition.get("secured_loot", [])], "fellowship_renown": 0, "achievements": [str(x) for x in achievements[:4]]},
            "lost_spoils": {"gil": max(0, int(spoils.get("gil", 0)) - kept_gil), "items": [str(x.get("name") or x.get("id")) for x in list(spoils.get("items") or [])]},
            "history": list(expedition.get("history") or [])[-8:], "last_round": list(log), "player": self._solo_result_vitals(twitch_id), "interactive": True,
        }
        self._remember_adventure_result(twitch_id, summary)
        self._solo_expedition_delete(twitch_id)
        return GameResult.success(f"SOLO VENTURE DEFEAT — {monster['name']} ends the run. {kept_gil} Gil was recovered; loose item spoils were lost.", solo_result=summary, solo_expedition_finished=True, won=False)

    def _advance_solo_expedition_round(self, twitch_id: str, expedition: dict[str, Any]) -> GameResult:
        combat = expedition.get("combat") or {}
        encounter = self.active_encounter or {}
        meta = self.encounter_roster.get(str(twitch_id))
        if not meta or not encounter:
            return GameResult.fail("That Solo Venture battle state is unavailable. Return to the Adventure Board and refresh.")
        monster = self.data.monsters[encounter["monster_id"]]
        round_no = int(encounter.get("round", 1))
        action = meta.get("action")
        if not action:
            return GameResult.fail("Choose Attack, Ability, Use Item, or Defend for this round.")
        log: list[str] = []
        meta["actions"] = int(meta.get("actions", 0)) + 1
        if has_status(meta.get("statuses", {}), "stun"):
            log.append(f"{meta['name']} is stunned and loses their action.")
        elif action["kind"] == "defend":
            meta["defending"] = True
            meta["defends"] = int(meta.get("defends", 0)) + 1
            recovered = []
            if int(meta.get("max_ap", 0)) > 0:
                before = int(meta.get("ap", 0)); meta["ap"] = min(int(meta["max_ap"]), before + defend_ap_restore(int(meta["max_ap"])))
                if int(meta["ap"]) > before: recovered.append(f"{int(meta['ap'])-before} AP")
            if int(meta.get("max_mp", 0)) > 0:
                before = int(meta.get("mp", 0)); meta["mp"] = min(int(meta["max_mp"]), before + defend_mp_restore(int(meta["max_mp"])))
                if int(meta["mp"]) > before: recovered.append(f"{int(meta['mp'])-before} MP")
            log.append(f"{meta['name']} Defends" + (f" and recovers {' and '.join(recovered)}." if recovered else "."))
        elif action["kind"] == "item":
            self._resolve_active_item(str(twitch_id), meta, action, log)
        elif action["kind"] == "ability":
            self._resolve_active_ability(meta, action, monster, log)
        else:
            self._resolve_active_attack(meta, monster, log)

        if int(encounter.get("monster_hp", 0)) <= 0:
            return self._finish_solo_stage_victory(twitch_id, expedition, monster, meta, round_no, log)

        self._solo_resolve_enemy_intent(monster, encounter, log)
        if int(encounter.get("monster_hp", 0)) <= 0:
            return self._finish_solo_stage_victory(twitch_id, expedition, monster, meta, round_no, log)

        if has_status(meta.get("statuses", {}), "poison") and int(meta.get("hp", 0)) > 0:
            poison = max(1, int(int(meta.get("max_hp", 1)) * max(0.03, status_magnitude(meta.get("statuses", {}), "poison"))))
            meta["hp"] = max(0, int(meta["hp"]) - poison); meta["damage_taken"] = int(meta.get("damage_taken", 0)) + poison
            log.append(f"{meta['name']} suffers {poison} Poison damage.")
        if has_status(meta.get("statuses", {}), "regen") and int(meta.get("hp", 0)) > 0:
            healed = self._apply_battle_heal(meta, meta, status_magnitude(meta.get("statuses", {}), "regen"))
            if healed: log.append(f"{meta['name']} regenerates {healed} HP.")
        tick_statuses(meta.setdefault("statuses", {}))
        meta["action"] = None; meta["defending"] = False
        self._save_hp(twitch_id, int(meta.get("hp", 0))); self._save_resources_from_meta(twitch_id, meta)

        monster_statuses = encounter.setdefault("monster_statuses", {})
        if has_status(monster_statuses, "regen") and int(encounter.get("monster_hp", 0)) > 0:
            before = int(encounter["monster_hp"]); heal = max(1, int(int(encounter["monster_max_hp"]) * status_magnitude(monster_statuses, "regen")))
            encounter["monster_hp"] = min(int(encounter["monster_max_hp"]), before + heal)
            if int(encounter["monster_hp"]) > before: log.append(f"{monster['name']} regenerates {int(encounter['monster_hp'])-before} HP.")
        tick_statuses(monster_statuses)

        expedition["last_round"] = {"round": round_no, "events": list(log), "summary": round_summary(log)}
        expedition.setdefault("round_history", []).append(copy.deepcopy(expedition["last_round"])); expedition["round_history"] = expedition["round_history"][-4:]
        if int(meta.get("hp", 0)) <= 0:
            return self._solo_finish_defeat(twitch_id, expedition, monster, meta, round_no, log)
        if round_no >= int(encounter.get("max_rounds", 12)):
            return self._solo_finish_defeat(twitch_id, expedition, monster, meta, round_no, log + ["The battle reaches the round safety limit."])
        encounter["round"] = round_no + 1
        encounter["enemy_intent"] = self._solo_enemy_intent(monster, encounter)
        combat["encounter"] = copy.deepcopy(encounter); combat["roster"] = copy.deepcopy(self.encounter_roster)
        expedition["combat"] = combat
        return GameResult.success(f"ROUND {round_no} — {round_summary(log)}", solo_expedition_round=True, round_log=list(log))

    def _finish_solo_stage_victory(self, twitch_id: str, expedition: dict[str, Any], monster: dict[str, Any], meta: dict[str, Any], round_no: int, log: list[str]) -> GameResult:
        self._save_hp(twitch_id, int(meta.get("hp", 0))); self._save_resources_from_meta(twitch_id, meta)
        rewards = self._solo_roll_stage_rewards(twitch_id, monster, int(expedition.get("stage", 1)))
        secured = expedition.setdefault("secured", {"xp": 0, "jp": 0})
        secured["xp"] = int(secured.get("xp", 0)) + int(rewards["xp"]); secured["jp"] = int(secured.get("jp", 0)) + int(rewards["jp"])
        spoils = expedition.setdefault("spoils", {"gil": 0, "items": []})
        spoils["gil"] = int(spoils.get("gil", 0)) + int(rewards["gil"]); spoils.setdefault("items", []).extend(rewards["items"])
        expedition.setdefault("secured_loot", []).extend(str(value) for value in rewards.get("secured_loot", []))
        self._record_combat_metrics(
            twitch_id, meta.get("job_id"), monster["id"], battle_type="venture", won=True, knocked_out=False,
            damage_dealt=int(meta.get("damage", 0)), damage_taken=int(meta.get("damage_taken", 0)), healing_done=int(meta.get("healing", 0)), best_hit=int(meta.get("best_hit", 0)),
        )
        self.db.update_record_stats(twitch_id, {"active_actions": int(meta.get("actions", 0)), "active_abilities": int(meta.get("abilities_used", 0)), "active_items": int(meta.get("items_used", 0)), "active_defends": int(meta.get("defends", 0))})
        achievements = self._check_achievements(twitch_id)
        expedition["last_stage"] = {"type": "victory", "monster": {"id": str(monster["id"]), "name": str(monster["name"]), "level": int(monster["level"])}, "rounds": round_no, "rewards": rewards, "achievements": achievements[:4]}
        expedition["last_round"] = {"round": round_no, "events": list(log), "summary": round_summary(log)}
        expedition.setdefault("history", []).append({"stage": int(expedition.get("stage", 1)), "type": "victory", "label": f"Defeated {monster['name']}"})
        expedition["combat"] = None; expedition["event"] = {"type": "victory", "monster_id": str(monster["id"])}; expedition["status"] = "choice"
        if int(expedition.get("stage", 1)) >= SOLO_EXPEDITION_MAX_STAGES:
            return self._solo_bank_spoils(twitch_id, expedition, outcome="complete")
        return GameResult.success(
            f"STAGE {int(expedition.get('stage', 1))} VICTORY — {monster['name']} defeated. +{rewards['xp']} XP / +{rewards['jp']} JP secured; {rewards['gil']} Gil added to expedition spoils.",
            solo_expedition_stage_complete=True,
        )

    def _solo_expedition_public(self, twitch_id: str) -> dict[str, Any] | None:
        expedition = self._solo_expedition_load(twitch_id)
        if not expedition:
            return None
        stage = int(expedition.get("stage", 1))
        payload: dict[str, Any] = {
            "active": True, "status": str(expedition.get("status") or "event"), "stage": stage,
            "max_stages": SOLO_EXPEDITION_MAX_STAGES, "stage_bonus_percent": int(round((self._solo_stage_multiplier(stage)-1.0)*100)),
            "region": {"id": str(expedition.get("region_id") or ""), "name": str((self.data.regions.get(str(expedition.get("region_id"))) or {}).get("name") or "Unknown Region")},
            "secured": copy.deepcopy(expedition.get("secured") or {"xp": 0, "jp": 0}),
            "secured_loot": [str(value) for value in expedition.get("secured_loot", [])],
            "spoils": {"gil": int((expedition.get("spoils") or {}).get("gil", 0)), "items": copy.deepcopy((expedition.get("spoils") or {}).get("items", []))},
            "history": copy.deepcopy(list(expedition.get("history") or [])[-6:]),
            "last_round": copy.deepcopy(expedition.get("last_round")), "last_stage": copy.deepcopy(expedition.get("last_stage")),
            "can_press_on": str(expedition.get("status")) == "choice" and stage < SOLO_EXPEDITION_MAX_STAGES,
            "can_return": str(expedition.get("status")) == "choice", "can_retreat": str(expedition.get("status")) == "combat",
        }
        if str(expedition.get("status")) == "choice" and (expedition.get("event") or {}).get("type") == "treasure":
            payload["treasure"] = copy.deepcopy((expedition.get("event") or {}).get("item"))
        combat = expedition.get("combat") or {}
        encounter = combat.get("encounter") or {}
        roster = combat.get("roster") or {}
        meta = roster.get(str(twitch_id)) if isinstance(roster, dict) else None
        if encounter and meta:
            monster = self.data.monsters.get(str(encounter.get("monster_id"))) or {}
            payload["combat"] = {
                "round": int(encounter.get("round", 1)),
                "enemy": {"id": str(monster.get("id") or ""), "name": str(monster.get("name") or "Unknown Enemy"), "level": int(monster.get("level", 1)), "hp": int(encounter.get("monster_hp", 0)), "max_hp": int(encounter.get("monster_max_hp", 0)), "statuses": status_text(encounter.get("monster_statuses", {}), limit=3), "intent": str((encounter.get("enemy_intent") or {}).get("label") or "Preparing an action")},
                "player": {"name": str(meta.get("name") or "Hero"), "job_id": str(meta.get("job_id") or ""), "job_name": str((self.data.jobs.get(str(meta.get("job_id"))) or {}).get("name") or "Adventurer"), "hp": int(meta.get("hp", 0)), "max_hp": int(meta.get("max_hp", 0)), "mp": int(meta.get("mp", 0)), "max_mp": int(meta.get("max_mp", 0)), "ap": int(meta.get("ap", 0)), "max_ap": int(meta.get("max_ap", 0)), "statuses": status_text(meta.get("statuses", {}), limit=4)},
                "abilities": self._solo_ability_rows(meta), "items": self._solo_owned_battle_items(twitch_id, meta),
            }
        return payload

    @_state_guard
    def solo_venture(self, twitch_id: str, bypass_cooldown: bool = False) -> GameResult:
        """Begin a persistent, player-paced Wayfarer Solo Venture."""
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        existing = self._solo_expedition_load(twitch_id)
        if existing:
            return GameResult.success("Your Solo Venture is already in progress. Continue it from the Adventure Board.", solo_expedition_active=True)
        if p["current_job"] == "adventurer":
            return GameResult.fail("Choose a Job before starting a Solo Venture.")
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("Finish your active encounter or raid before starting a Solo Venture.")
        blocked = self._activity_block(twitch_id)
        if blocked:
            return GameResult.fail(blocked)
        remaining = self._cooldown_remaining(twitch_id, "solo_venture")
        if remaining > 0 and not bypass_cooldown:
            return GameResult.fail(f"Solo Venture ready in {self._format_seconds(remaining)}.")
        p = self._player(twitch_id)
        now = int(time.time())
        expedition = {
            "version": 1, "started_at": now, "updated_at": now, "stage": 1, "max_stages": SOLO_EXPEDITION_MAX_STAGES,
            "region_id": str(p["current_region"]), "status": "event", "secured": {"xp": 0, "jp": 0}, "secured_loot": [],
            "spoils": {"gil": 0, "items": []}, "history": [], "round_history": [], "event": None, "combat": None,
        }
        self._set_cooldown(twitch_id, "solo_venture", SOLO_VENTURE_COOLDOWN_SECONDS)
        self.db.execute("UPDATE players SET ventures=ventures+1,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (twitch_id,))
        self.db.update_record_stats(twitch_id, {"solo_ventures": 1})
        self._solo_expedition_save(twitch_id, expedition)
        return self._solo_begin_stage(twitch_id, expedition)

    @_state_guard
    def solo_expedition_action(self, twitch_id: str, action_kind: str, action_id: str | None = None) -> GameResult:
        expedition = self._solo_expedition_load(twitch_id)
        if not expedition or str(expedition.get("status")) != "combat":
            return GameResult.fail("No Solo Venture battle is waiting for an action.")
        combat = expedition.get("combat") or {}; encounter = copy.deepcopy(combat.get("encounter") or {}); roster = copy.deepcopy(combat.get("roster") or {})
        meta = roster.get(str(twitch_id))
        if not encounter or not meta or int(meta.get("hp", 0)) <= 0:
            return GameResult.fail("Your Solo Venture combat state cannot accept an action.")
        action_kind = str(action_kind or "").lower().strip()
        if action_kind == "attack":
            meta["action"] = {"kind": "attack"}
        elif action_kind == "defend":
            meta["action"] = {"kind": "defend"}
        elif action_kind.startswith("ability:"):
            ability_id = action_kind.split(":", 1)[1]
            ability = next((row for row in self.data.active_abilities.get(str(meta.get("job_id")), []) if str(row.get("id")) == ability_id), None)
            job = self.data.jobs.get(str(meta.get("job_id"))) or {}
            if not ability or int(ability.get("level", 1)) > int(meta.get("job_level", 0)):
                return GameResult.fail("That ability is not available to your current Job level.")
            resource = ability_resource(ability, job); cost = ability_cost(ability)
            if int(meta.get(resource, 0)) < cost:
                return GameResult.fail(f"{ability['name']} needs {cost} {resource.upper()}.")
            if resource == "mp" and has_status(meta.get("statuses", {}), "silence"):
                return GameResult.fail("Silence prevents that MP ability.")
            if any(effect.get("type") == "revive" for effect in ability.get("effects", [])):
                return GameResult.fail("Revive abilities need another KO'd ally and cannot be used in a Solo Venture.")
            target_mode = str(ability.get("target") or "enemy")
            target_id = "monster" if target_mode == "enemy" else "party" if target_mode == "party" else str(twitch_id)
            meta["action"] = {"kind": "ability", "ability_id": str(ability["id"]), "target_id": target_id, "resource": resource, "cost": cost}
        elif action_kind.startswith("item:"):
            item_id = action_kind.split(":", 1)[1]
            item = self.data.items.get(item_id); use = item.get("use") if item and isinstance(item.get("use"), dict) else None
            if not item or not use or self._inventory_qty(twitch_id, item_id) <= 0:
                return GameResult.fail("That battle item is not available.")
            if any(effect.get("type") == "revive" for effect in use.get("effects", [])):
                return GameResult.fail("Revive items cannot be used on your conscious hero in a Solo Venture.")
            target_mode = str(use.get("target", "ally")); target_id = "monster" if target_mode == "enemy" else "party" if target_mode == "party" else str(twitch_id)
            meta["action"] = {"kind": "item", "item_id": item_id, "target_id": target_id}
        else:
            return GameResult.fail("Choose Attack, Ability, Use Item, or Defend.")
        old_encounter, old_roster = self.active_encounter, self.encounter_roster
        try:
            self.active_encounter, self.encounter_roster = encounter, roster
            result = self._advance_solo_expedition_round(twitch_id, expedition)
            if self._solo_expedition_load(twitch_id) is not None:
                expedition["combat"] = {"encounter": copy.deepcopy(self.active_encounter), "roster": copy.deepcopy(self.encounter_roster)} if expedition.get("status") == "combat" else None
                self._solo_expedition_save(twitch_id, expedition)
            return result
        finally:
            self.active_encounter, self.encounter_roster = old_encounter, old_roster

    @_state_guard
    def solo_expedition_continue(self, twitch_id: str) -> GameResult:
        expedition = self._solo_expedition_load(twitch_id)
        if not expedition or str(expedition.get("status")) != "choice":
            return GameResult.fail("There is no cleared Solo Venture stage to continue from.")
        if int(expedition.get("stage", 1)) >= SOLO_EXPEDITION_MAX_STAGES:
            return self._solo_bank_spoils(twitch_id, expedition, outcome="complete")
        expedition["stage"] = int(expedition.get("stage", 1)) + 1
        expedition["last_round"] = None; expedition["last_stage"] = None
        self._solo_expedition_save(twitch_id, expedition)
        return self._solo_begin_stage(twitch_id, expedition)

    @_state_guard
    def solo_expedition_return(self, twitch_id: str) -> GameResult:
        expedition = self._solo_expedition_load(twitch_id)
        if not expedition or str(expedition.get("status")) != "choice":
            return GameResult.fail("You can return safely after clearing the current Solo Venture stage.")
        return self._solo_bank_spoils(twitch_id, expedition, outcome="returned")

    @_state_guard
    def solo_expedition_retreat(self, twitch_id: str) -> GameResult:
        expedition = self._solo_expedition_load(twitch_id)
        if not expedition or str(expedition.get("status")) != "combat":
            return GameResult.fail("There is no active Solo Venture battle to retreat from.")
        combat = expedition.get("combat") or {}; roster = combat.get("roster") or {}; meta = roster.get(str(twitch_id)) or {}
        if meta:
            self._save_hp(twitch_id, int(meta.get("hp", 0))); self._save_resources_from_meta(twitch_id, meta)
        secured = expedition.get("secured") or {}; lost = expedition.get("spoils") or {}
        summary = {"type": "expedition", "outcome": "retreat", "title": "Solo Venture Retreat", "region_name": str((self.data.regions.get(str(expedition.get("region_id"))) or {}).get("name") or "Unknown Region"), "stages": int(expedition.get("stage", 1)), "rewards": {"xp": int(secured.get("xp", 0)), "jp": int(secured.get("jp", 0)), "gil": 0, "loot": [str(x) for x in expedition.get("secured_loot", [])], "secured_loot": [str(x) for x in expedition.get("secured_loot", [])], "fellowship_renown": 0, "achievements": []}, "lost_spoils": {"gil": int(lost.get("gil", 0)), "items": [str(x.get("name") or x.get("id")) for x in list(lost.get("items") or [])]}, "history": list(expedition.get("history") or [])[-8:], "player": self._solo_result_vitals(twitch_id), "interactive": True}
        self._remember_adventure_result(twitch_id, summary); self._solo_expedition_delete(twitch_id)
        return GameResult.success("SOLO VENTURE — You retreat safely. Secured XP/JP remain; expedition Gil and loose spoils are abandoned.", solo_result=summary, solo_expedition_finished=True)

    @_state_guard
    def venture(self, twitch_id: str, bypass_cooldown: bool = False) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self.active_boss:
            return GameResult.fail(
                f"A raid against {self.active_boss['name']} is active. "
                "Deal with that catastrophe before starting a Venture."
            )
        if self.active_encounter:
            state = self.active_encounter.get("state", "rally")
            kind = self.active_encounter.get("kind", "venture")
            if kind == "hunt":
                if twitch_id in self.encounter_roster:
                    return self.encounter_status()
                return GameResult.fail(
                    "An Active Hunt is already underway. Hunt marks are solo battles; "
                    "wait for the mark to resolve before starting a Venture."
                )
            if state == "rally" and time.time() < float(self.active_encounter["closes_at"]):
                return self.join_encounter(twitch_id, bypass_cooldown=bypass_cooldown)
            if state == "rally":
                # Player commands never advance an expired timer.
                # The combat daemon owns the rally -> combat transition.
                if twitch_id in self.encounter_roster:
                    return self.encounter_status()
                return GameResult.fail(
                    "That rally has closed. Active Battle is starting automatically; "
                    "wait for the round announcement before choosing an action."
                )
            if twitch_id in self.encounter_roster:
                return self.encounter_status()
            return GameResult.fail("That battle is already underway. The rally gate is closed until the next Venture.")
        if p["current_job"] == "adventurer":
            return GameResult.fail("Pick a Job before venturing: !job warrior | monk | thief | blackmage | whitemage | redmage")
        blocked = self._activity_block(twitch_id)
        if blocked:
            return GameResult.fail(blocked)
        remaining = self._cooldown_remaining(twitch_id, "venture")
        if remaining > 0 and not bypass_cooldown:
            return GameResult.fail(f"Your hero is still recovering. Venture again in {self._format_seconds(remaining)}.")

        p = self._player(twitch_id)
        region = self.data.regions[p["current_region"]]

        # Resolve the Venture event before rolling a monster. A 0% test/debug
        # override deliberately avoids consuming RNG state, preserving existing
        # deterministic combat regressions.
        treasure_roll = self.venture_treasure_chance >= 1.0 or (
            self.venture_treasure_chance > 0.0
            and self.rng.random() < self.venture_treasure_chance
        )
        if treasure_roll:
            treasure = self._resolve_venture_treasure(twitch_id, p, region)
            if treasure is not None:
                return treasure

        max_monster_level = int(p["level"]) + VENTURE_MAX_LEVEL_ABOVE_PLAYER
        eligible_encounters = [
            encounter
            for encounter in region["encounters"]
            if int(self.data.monsters[encounter["monster_id"]]["level"]) <= max_monster_level
        ]
        if not eligible_encounters:
            return GameResult.fail(
                f"No level-appropriate monsters are available in {region['name']} right now. "
                "Try another region or gain a level first."
            )
        encounter = self.rng.choices(
            eligible_encounters,
            weights=[e["weight"] for e in eligible_encounters],
            k=1,
        )[0]
        monster = self.data.monsters[encounter["monster_id"]]
        now = time.time()
        self._encounter_seq += 1
        encounter_id = self._encounter_seq
        self.active_encounter = {
            "id": encounter_id,
            "kind": "venture",
            "state": "rally",
            "monster_id": monster["id"],
            "region_id": region["id"],
            "created_at": int(now),
            "closes_at": now + self.encounter_join_seconds,
            "starter_id": twitch_id,
        }
        self.encounter_roster = {
            twitch_id: {"name": p["display_name"], "username": p["username"], "job_id": p["current_job"]}
        }
        self._set_cooldown(twitch_id, "venture", self.venture_cooldown_seconds)
        self.db.execute(
            "UPDATE players SET ventures=ventures+1, party_encounters=party_encounters+1, "
            "updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
            (twitch_id,),
        )
        return GameResult.success(
            f"ENCOUNTER — {p['display_name']} finds {monster['name']} (Lv.{monster['level']}) in {region['name']}!",
            f"RALLY OPEN {self._format_seconds(self.encounter_join_seconds)} — !join to enter. "
            "When the rally closes, Active Battle begins and each hero chooses "
            "!attack, !ability, !defend, or !use.",
            venture_event="encounter",
            encounter_started=True,
            encounter_id=encounter_id,
            closes_at=self.active_encounter["closes_at"],
        )

    @_state_guard
    def join_encounter(self, twitch_id: str, bypass_cooldown: bool = False) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if not self.active_encounter:
            return GameResult.fail("There is no open encounter. Start a Venture with !venture.")
        if self.active_encounter.get("kind", "venture") == "hunt":
            if twitch_id in self.encounter_roster:
                return self.encounter_status()
            return GameResult.fail(
                "That is an Active Hunt, not a public rally. Hunt marks are solo battles."
            )
        if self.active_encounter.get("state", "rally") != "rally":
            if twitch_id in self.encounter_roster:
                return self.encounter_status()
            return GameResult.fail("The active battle has already started. Join the next rally.")
        remaining_window = float(self.active_encounter["closes_at"]) - time.time()
        if remaining_window <= 0:
            # Do not let a late !join become the timer callback. The daemon will
            # observe the same deadline and start combat independently.
            return GameResult.fail(
                "The rally timer has closed. Active Battle is starting automatically; "
                "you'll need to join the next rally."
            )
        if twitch_id in self.encounter_roster:
            return GameResult.success(
                f"{p['display_name']} is already in the party. "
                f"Heroes: {len(self.encounter_roster)} | "
                f"battle in {self._format_seconds(max(0, int(remaining_window)))}."
            )
        if p["current_job"] == "adventurer":
            return GameResult.fail("Choose a Job before joining an encounter.")
        blocked = self._activity_block(twitch_id)
        if blocked:
            return GameResult.fail(blocked)
        cooldown = self._cooldown_remaining(twitch_id, "venture")
        if cooldown > 0 and not bypass_cooldown:
            return GameResult.fail(f"Your hero cannot answer the rally yet. Ready in {self._format_seconds(cooldown)}.")
        self.encounter_roster[twitch_id] = {"name": p["display_name"], "username": p["username"], "job_id": p["current_job"]}
        self._set_cooldown(twitch_id, "venture", self.venture_cooldown_seconds)
        self.db.execute(
            "UPDATE players SET ventures=ventures+1, party_encounters=party_encounters+1, "
            "updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
            (twitch_id,),
        )
        monster = self.data.monsters[self.active_encounter["monster_id"]]
        return GameResult.success(
            f"{p['display_name']} joins the fight against {monster['name']}! "
            f"Party: {len(self.encounter_roster)} | "
            f"battle in {self._format_seconds(max(0, int(remaining_window)))}."
        )

    def _initialize_active_combat(self, encounter: dict[str, Any]) -> tuple[int, dict[str, Any], int]:
        """Populate reusable combat state for Ventures and Active Hunts.

        One authoritative round engine serves Venture rallies and
        solo Hunt acceptances differ only in how the encounter is created and
        how victory rewards are persisted; HP/MP/action/status setup lives here
        so future combat changes do not fork between the two modes.
        """
        monster = self.data.monsters[encounter["monster_id"]]
        combatants = 0
        for pid, meta in list(self.encounter_roster.items()):
            self._finish_rest_if_ready(pid)
            p = self._player(pid)
            if not p or p["current_job"] == "adventurer" or int(p["current_hp"]) <= 0:
                meta.update({
                    "hp": 0,
                    "max_hp": 0,
                    "mp": 0,
                    "max_mp": 0,
                    "ap": 0,
                    "max_ap": 0,
                    "statuses": {},
                    "action": None,
                })
                continue

            job_id = meta.get("job_id") if meta.get("job_id") in self.data.jobs else p["current_job"]
            job = self.data.jobs[job_id]
            effects = self._effects(pid, job_id)
            stats = self._stats(p, job, effects)
            traits = self._equipment_traits(p, job)
            resources = self._resource_state_for(p, job, stats)
            max_mp = int(resources["max_mp"])
            max_ap = int(resources["max_ap"])
            meta.update({
                "name": p["display_name"],
                "username": p["username"],
                "job_id": job_id,
                "job_level": self._job_level(pid, job_id),
                "stance": p["stance"],
                "stats": stats,
                "effects": effects,
                "status_immune": traits["status_immune"],
                "status_resist": traits["status_resist"],
                "weapon_element": traits["weapon_element"],
                "on_hit_status": traits["on_hit_status"],
                "lifesteal": traits["lifesteal"],
                "hp": min(int(p["current_hp"]), int(stats["hp"])),
                "max_hp": int(stats["hp"]),
                "mp": int(resources["mp"]),
                "max_mp": max_mp,
                "ap": int(resources["ap"]),
                "max_ap": max_ap,
                "statuses": {},
                "action": None,
                "defending": False,
                "damage": 0,
                "healing": 0,
                "damage_taken": 0,
                "best_hit": 0,
                "actions": 0,
                "abilities_used": 0,
                "items_used": 0,
                "defends": 0,
            })
            combatants += 1

        kind = encounter.get("kind", "venture")
        if kind == "hunt":
            hunt = self.data.hunts[encounter["hunt_id"]]
            monster_max = active_hunt_hp(int(monster["hp"]), hunt["rank"])
            max_rounds = active_hunt_round_limit(hunt["rank"])
        else:
            monster_max = party_monster_hp(int(monster["hp"]), combatants)
            max_rounds = 12

        now = time.time()
        encounter.update({
            "state": "combat",
            "round": 1,
            "max_rounds": max_rounds,
            "monster_hp": monster_max,
            "monster_max_hp": monster_max,
            "monster_statuses": {},
            "enemy_special_ready_round": 1,
            # Hard-control guardrail: after a successful player Stun,
            # the single enemy gets one follow-up round of resistance.
            "monster_stun_resist_until": 0,
            "next_round_at": now + self.encounter_round_seconds,
        })
        return combatants, monster, monster_max

    @_state_guard
    def start_encounter_battle(self, encounter_id: int | None = None) -> GameResult:
        """Close a Venture rally and initialize its Active Battle state."""
        if not self.active_encounter:
            return GameResult.fail("There is no encounter to start.")
        if encounter_id is not None and int(self.active_encounter["id"]) != int(encounter_id):
            return GameResult.fail("That encounter has already ended.")
        if self.active_encounter.get("state", "rally") == "combat":
            return self.encounter_status()

        encounter = self.active_encounter
        combatants, monster, monster_max = self._initialize_active_combat(encounter)
        if combatants == 0:
            self._clear_encounter(int(encounter["id"]))
            return GameResult.success(
                "ACTIVE BATTLE CANCELLED — nobody in the rally was conscious "
                "when the gate closed.",
                encounter_finished=True,
            )

        return GameResult.success(
            f"ACTIVE BATTLE — {combatants} "
            f"hero{'es' if combatants != 1 else ''} vs {monster['name']} | "
            f"{resource_text('Enemy HP', monster_max, monster_max)}.",
            f"ROUND 1 · {self._format_seconds(self.encounter_round_seconds)} | "
            "!attack · !ability <name> [ally] · !defend · !use <item> [ally] | "
            "No action = Attack. Use !encounter for vitals or !battlelog for recent rounds.",
            battle_started=True,
            encounter_id=encounter["id"],
            next_round_at=encounter["next_round_at"],
        )

    # ---------- Battle presentation ----------
    def _queued_action_label(self, row: dict[str, Any]) -> str:
        """Return the player-facing name of one queued action.

        Keep lookup/formatting here rather than in Twitch command handlers so
        every presentation surface describes the same authoritative action.
        """
        action = row.get("action") or {}
        kind = str(action.get("kind", ""))
        if not kind:
            return "WAIT"
        if kind == "ability":
            ability_id = action.get("ability_id")
            ability = next((a for a in self.data.active_abilities.get(row.get("job_id"), []) if a.get("id") == ability_id), None)
            return str(ability.get("name")) if ability else "Ability"
        if kind == "item":
            item = self.data.items.get(action.get("item_id"), {})
            return str(item.get("name") or "Item")
        return "Defend" if kind == "defend" else "Attack"

    def _remember_round(self, round_no: int, log: list[str]) -> None:
        """Store a bounded in-memory round recap for !battlelog.

        This is presentation state only. It is deliberately not written to the
        player database or hosted snapshot, keeping presentation compatible
        with existing 1.x installs and schema version 1.
        """
        if not self.active_encounter or not log:
            return
        history = self.active_encounter.setdefault("round_history", [])
        # Avoid duplicate history when a finishing round flows through
        # _finish_active_encounter after being recorded by another code path.
        if history and int(history[-1].get("round", -1)) == int(round_no):
            history[-1] = {"round": int(round_no), "events": list(log), "summary": round_summary(log)}
        else:
            history.append({"round": int(round_no), "events": list(log), "summary": round_summary(log)})
        del history[:-4]

    def _battle_history_title(self) -> str:
        if not self.active_encounter:
            return "Active Battle"
        monster = self.data.monsters.get(self.active_encounter.get("monster_id"), {})
        kind = self.active_encounter.get("kind", "venture")
        if kind == "hunt":
            hunt = self.data.hunts.get(self.active_encounter.get("hunt_id"), {})
            return f"[{hunt.get('rank', '?')}] {hunt.get('name', 'Hunt')} · {monster.get('name', 'Monster')}"
        if kind == "solo_venture":
            return f"Solo Venture · {monster.get('name', 'Monster')}"
        return str(monster.get("name", "Active Battle"))

    @_state_guard
    def battle_log(self) -> GameResult:
        """Show recent resolved rounds without making automatic chat noisier."""
        if self.active_encounter:
            title = self._battle_history_title()
            history = list(self.active_encounter.get("round_history", []))
        elif self._last_battle_history:
            title = str(self._last_battle_history.get("title", "Previous Battle"))
            history = list(self._last_battle_history.get("history", []))
        else:
            return GameResult.success("BATTLE LOG — no Active Battle has resolved a round yet.")

        if not history:
            return GameResult.success(f"BATTLE LOG — {title}: no completed rounds yet.")
        messages = [f"BATTLE LOG — {title} · latest {min(3, len(history))} round(s)"]
        for entry in history[-3:]:
            messages.append(f"R{int(entry.get('round', 0))} — {entry.get('summary') or round_summary(entry.get('events', []))}")
        return GameResult.success(*messages)

    @_state_guard
    def encounter_status(self) -> GameResult:
        """Return a compact, read-only Active Battle dashboard for Twitch chat.

        The status command is intentionally informational: it
        never advances a timer, consumes an action, or mutates combat state.
        """
        if not self.active_encounter:
            return GameResult.success(
                "No encounter is active. Type !venture to go looking for trouble."
            )

        state = self.active_encounter.get("state", "rally")
        monster = self.data.monsters[self.active_encounter["monster_id"]]
        region = self.data.regions[self.active_encounter["region_id"]]
        now = time.time()
        if state == "rally":
            remaining = max(0, int(float(self.active_encounter["closes_at"]) - now))
            names = ", ".join(v["name"] for v in list(self.encounter_roster.values())[:8])
            timer_state = (
                f"RALLY {self._format_seconds(remaining)}"
                if remaining > 0
                else "RALLY CLOSED · battle start pending"
            )
            return GameResult.success(
                f"Encounter — {monster['name']} Lv.{monster['level']} @ {region['name']} "
                f"| {timer_state} | Party {len(self.encounter_roster)}: {names}"
            )

        due = float(self.active_encounter.get("next_round_at") or 0)
        alive = [m for m in self.encounter_roster.values() if int(m.get("hp", 0)) > 0]
        queued = sum(1 for m in alive if m.get("action"))
        remaining = max(0, int(due - now)) if due else 0
        timer_label = (
            self._format_seconds(remaining)
            if not due or now < due
            else "timer closed · resolving"
        )

        behavior = self.data.enemy_actions.get(monster["id"], {})
        profile = self.data.enemy_profiles.get(behavior.get("profile"), {})
        profile_label = profile.get("name", "Balanced")
        enemy_status = status_text(self.active_encounter.get("monster_statuses", {}), limit=3)
        enemy_hp = int(self.active_encounter["monster_hp"])
        enemy_max = int(self.active_encounter["monster_max_hp"])

        if self.active_encounter.get("kind", "venture") == "hunt":
            hunt = self.data.hunts[self.active_encounter["hunt_id"]]
            battle_label = f"ACTIVE HUNT [{hunt['rank']}] — {hunt['name']} · {monster['name']}"
        elif self.active_encounter.get("kind") == "solo_venture":
            battle_label = f"SOLO VENTURE — {monster['name']}"
        else:
            battle_label = f"ACTIVE BATTLE — {monster['name']}"

        header = (
            f"{battle_label} | {resource_text('HP', enemy_hp, enemy_max)} "
            f"| {profile_label} {enemy_status} | Round {self.active_encounter['round']} "
            f"| actions {queued}/{len(alive)} | {timer_label}"
        )

        roster_rows: list[dict[str, Any]] = []
        action_labels: dict[str, str] = {}
        for pid, row in list(self.encounter_roster.items())[:8]:
            copy = dict(row)
            copy["player_id"] = pid
            roster_rows.append(copy)
            action_labels[str(pid)] = self._queued_action_label(row)
        party_lines = party_status_lines(roster_rows, action_labels=action_labels)

        history = list(self.active_encounter.get("round_history", []))
        last = []
        if history:
            entry = history[-1]
            last = [f"LAST ROUND R{int(entry.get('round', 0))} — {entry.get('summary') or round_summary(entry.get('events', []))}"]
        return GameResult.success(header, *party_lines, *last)

    def _active_actor(self, twitch_id: str) -> tuple[dict[str, Any] | None, GameResult | None]:
        if not self.active_encounter or self.active_encounter.get("state") != "combat":
            return None, GameResult.fail("No Active Battle is accepting actions right now.")

        # Timer gate: once the scheduled deadline passes, the action set is
        # frozen even if the daemon has not acquired the state lock yet. This
        # prevents a late chat message from changing the round being resolved.
        due = float(self.active_encounter.get("next_round_at") or 0)
        if due and time.time() >= due:
            return None, GameResult.fail(
                "That round timer has closed and resolution is already pending. "
                "Wait for the next round announcement."
            )

        meta = self.encounter_roster.get(str(twitch_id))
        if not meta:
            return None, GameResult.fail("You are not part of the active battle.")
        if int(meta.get("hp", 0)) <= 0:
            return None, GameResult.fail("You are KO'd and cannot act. An ally can use Raise or a Phoenix Down on you.")
        return meta, None

    def _all_round_actions_queued(self) -> bool:
        """Return whether every living hero has submitted an action.

        This is informational only. the scheduler deliberately does *not* shorten the
        scheduled round deadline when everyone is ready; only the timer daemon
        advances combat. Keeping this helper pure protects that ownership rule.
        """
        if not self.active_encounter or self.active_encounter.get("state") != "combat":
            return False
        living = [m for m in self.encounter_roster.values() if int(m.get("hp", 0)) > 0]
        return bool(living and all(m.get("action") for m in living))

    def _raid_actor(self, twitch_id: str) -> tuple[dict[str, Any] | None, GameResult | None]:
        """Return one living raid participant while the current round accepts input."""
        if not self.active_boss or self.active_boss.get("state") != "combat":
            return None, GameResult.fail("No active raid is accepting actions right now.")
        due = float(self.active_boss.get("next_round_at") or 0)
        if due and time.time() >= due:
            return None, GameResult.fail(
                "That raid round timer has closed and resolution is already pending. "
                "Wait for the next round announcement."
            )
        meta = self.raid_roster.get(str(twitch_id))
        if not meta:
            return None, GameResult.fail("You are not part of the active raid.")
        # Hotfix compatibility: a Raid recovered from a pre-action-queue runtime
        # checkpoint has the legacy contribution fields but not Active Battle
        # stats/resources. Hydrate it lazily without changing the checkpoint schema.
        if "stats" not in meta or "effects" not in meta:
            self._initialize_raid_combat()
            meta = self.raid_roster.get(str(twitch_id))
            if not meta:
                return None, GameResult.fail("You are not part of the active raid.")
        if int(meta.get("hp", 0)) <= 0:
            return None, GameResult.fail("You are KO'd and cannot act. An ally can use Raise, a Phoenix Down, or !revive on you.")
        return meta, None

    def _all_raid_actions_queued(self) -> bool:
        if not self.active_boss or self.active_boss.get("state") != "combat":
            return False
        living = [m for m in self.raid_roster.values() if int(m.get("hp", 0)) > 0]
        return bool(living and all(m.get("action") for m in living))

    def _raid_target_id(self, query: str, *, default_id: str | None = None) -> str | None:
        token = normalize_action_text(query)
        if not token:
            return default_id
        exact: list[str] = []
        partial: list[str] = []
        for pid, meta in self.raid_roster.items():
            names = {
                normalize_action_text(str(meta.get("name", ""))),
                normalize_action_text(str(meta.get("username", ""))),
                normalize_action_text(str(pid)),
            }
            if token in names:
                exact.append(pid)
            elif any(name and (name.startswith(token) or token.startswith(name)) for name in names):
                partial.append(pid)
        if len(exact) == 1:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    def _queue_raid_ability(self, twitch_id: str, ability_query: str | None) -> GameResult:
        meta, error = self._raid_actor(twitch_id)
        if error:
            return error
        catalog = self.data.active_abilities.get(meta["job_id"], [])
        unlocked = unlocked_abilities(catalog, int(meta.get("job_level", 0)))
        if not ability_query:
            job = self.data.jobs.get(meta["job_id"])
            text = " | ".join(
                f"{ability['name']} ({ability_cost(ability)}{ability_resource(ability, job).upper()}, {ability['target']})"
                for ability in unlocked
            ) or "none"
            return GameResult.success(f"{self.data.jobs[meta['job_id']]['name']} Raid Abilities — {text}")

        ability, target_query = match_ability(unlocked, ability_query)
        if not ability:
            names = ", ".join(row["name"] for row in unlocked) or "none"
            return GameResult.fail(f"Active ability not found or not unlocked. Available: {names}.")
        job = self.data.jobs.get(meta["job_id"])
        resource = ability_resource(ability, job)
        cost = ability_cost(ability)
        if resource == "mp" and has_status(meta.get("statuses", {}), "silence"):
            return GameResult.fail(f"{meta['name']} is Silenced and cannot use MP abilities this raid round.")
        if int(meta.get(resource, 0)) < cost:
            return GameResult.fail(f"{ability['name']} costs {cost} {resource.upper()}; you have {meta.get(resource, 0)}.")

        target_type = ability.get("target")
        needs_ko = any(effect.get("type") == "revive" for effect in ability.get("effects", []))
        if target_type == "enemy":
            target_id = "boss"
        elif target_type == "party":
            target_id = "party"
        elif target_type == "self":
            target_id = str(twitch_id)
        else:
            target_id = self._raid_target_id(target_query, default_id=None if needs_ko else str(twitch_id))
            if not target_id:
                return GameResult.fail(f"Choose a clear raid ally target. Example: !ability {ability['name']} <hero>.")
        if needs_ko:
            target = self.raid_roster.get(target_id)
            if not target or int(target.get("hp", 0)) > 0:
                return GameResult.fail(f"{ability['name']} needs a KO'd ally target. Example: !ability {ability['name']} <hero>.")

        meta["action"] = {
            "kind": "ability", "ability_id": ability["id"], "target_id": target_id,
            "resource": resource, "cost": cost,
        }
        target_name = self.raid_roster.get(target_id, {}).get("name", "boss" if target_id == "boss" else "party")
        return GameResult.success(
            f"RAID QUEUED R{int(self.active_boss.get('round', 0)) + 1} — {meta['name']}: "
            f"{ability['name']} → {target_name} ({cost}{resource.upper()}).",
            all_actions_queued=self._all_raid_actions_queued(),
        )

    def _queue_raid_item(self, twitch_id: str, item_query: str) -> GameResult:
        meta, error = self._raid_actor(twitch_id)
        if error:
            return error
        item, target_query = self._match_battle_item(item_query)
        if not item:
            return GameResult.fail("Battle item not found. Use !inventory consumable to see owned combat items.")
        if self._inventory_qty(twitch_id, item["id"]) <= 0:
            return GameResult.fail(f"You do not own {item['name']}.")
        use = item.get("use", {})
        target_mode = str(use.get("target", "ally"))
        effects = use.get("effects", [])
        if target_mode == "enemy":
            target_id, target_name = "boss", self.active_boss["name"]
        elif target_mode == "party":
            target_id, target_name = "party", "raid party"
        elif target_mode == "self":
            target_id, target_name = str(twitch_id), meta["name"]
        else:
            requires_revive = any(effect.get("type") == "revive" for effect in effects)
            target_id = self._raid_target_id(target_query, default_id=None if requires_revive else str(twitch_id))
            if not target_id:
                return GameResult.fail(f"Choose a clear raid ally target. Example: !use {item['name']} <hero>.")
            target_name = self.raid_roster[target_id]["name"]
        target = self.raid_roster.get(target_id) if target_id not in {"boss", "party"} else None
        if any(effect.get("type") == "revive" for effect in effects) and (not target or int(target.get("hp", 0)) > 0):
            return GameResult.fail(f"{item['name']} needs a KO'd raid ally target. Example: !use {item['name']} <hero>.")
        meta["action"] = {"kind": "item", "item_id": item["id"], "target_id": target_id}
        return GameResult.success(
            f"RAID QUEUED R{int(self.active_boss.get('round', 0)) + 1} — {meta['name']}: {item['name']} → {target_name}.",
            all_actions_queued=self._all_raid_actions_queued(),
        )

    @_state_guard
    def battle_attack(self, twitch_id: str) -> GameResult:
        if self.active_boss and self.active_boss.get("state") == "combat" and str(twitch_id) in self.raid_roster:
            meta, error = self._raid_actor(twitch_id)
            if error:
                return error
            meta["action"] = {"kind": "attack"}
            return GameResult.success(
                f"RAID QUEUED R{int(self.active_boss.get('round', 0)) + 1} — {meta['name']}: Attack.",
                all_actions_queued=self._all_raid_actions_queued(),
            )
        meta, error = self._active_actor(twitch_id)
        if error:
            return error
        meta["action"] = {"kind": "attack"}
        ready = self._all_round_actions_queued()
        return GameResult.success(
            f"QUEUED R{self.active_encounter['round']} — {meta['name']}: Attack.",
            all_actions_queued=ready,
        )

    @_state_guard
    def battle_defend(self, twitch_id: str) -> GameResult:
        if self.active_boss and self.active_boss.get("state") == "combat" and str(twitch_id) in self.raid_roster:
            meta, error = self._raid_actor(twitch_id)
            if error:
                return error
            meta["action"] = {"kind": "defend"}
            return GameResult.success(
                f"RAID QUEUED R{int(self.active_boss.get('round', 0)) + 1} — {meta['name']}: Defend.",
                all_actions_queued=self._all_raid_actions_queued(),
            )
        meta, error = self._active_actor(twitch_id)
        if error:
            return error
        meta["action"] = {"kind": "defend"}
        ready = self._all_round_actions_queued()
        return GameResult.success(
            f"QUEUED R{self.active_encounter['round']} — {meta['name']}: Defend.",
            all_actions_queued=ready,
        )

    def _battle_target_id(self, query: str, *, default_id: str | None = None) -> str | None:
        token = normalize_action_text(query)
        if not token:
            return default_id
        exact = []
        partial = []
        for pid, meta in self.encounter_roster.items():
            names = {
                normalize_action_text(str(meta.get("name", ""))),
                normalize_action_text(str(meta.get("username", ""))),
                normalize_action_text(str(pid)),
            }
            if token in names:
                exact.append(pid)
            elif any(name and (name.startswith(token) or token.startswith(name)) for name in names):
                partial.append(pid)
        if len(exact) == 1:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    @_state_guard
    def battle_ability(self, twitch_id: str, ability_query: str | None = None) -> GameResult:
        """Queue one unlocked Job ability for the current round.

        Queueing is intentionally side-effect free: MP/AP is validated here but
        only spent when the round resolves. A later command may safely replace
        this action without refund bookkeeping.
        """
        if self.active_boss and self.active_boss.get("state") == "combat" and str(twitch_id) in self.raid_roster:
            return self._queue_raid_ability(twitch_id, ability_query)
        meta, error = self._active_actor(twitch_id)
        if error:
            return error
        catalog = self.data.active_abilities.get(meta["job_id"], [])
        unlocked = unlocked_abilities(catalog, int(meta.get("job_level", 0)))
        if not ability_query:
            job = self.data.jobs.get(meta["job_id"])
            text = " | ".join(
                f"{ability['name']} ({ability_cost(ability)}{ability_resource(ability, job).upper()}, {ability['target']})"
                for ability in unlocked
            ) or "none"
            return GameResult.success(
                f"{self.data.jobs[meta['job_id']]['name']} Active Abilities — {text}"
            )

        ability, target_query = match_ability(unlocked, ability_query)
        if not ability:
            names = ", ".join(ability["name"] for ability in unlocked) or "none"
            return GameResult.fail(
                f"Active ability not found or not unlocked. Available: {names}."
            )

        job = self.data.jobs.get(meta["job_id"])
        resource = ability_resource(ability, job)
        cost = ability_cost(ability)
        if resource == "mp" and has_status(meta.get("statuses", {}), "silence"):
            return GameResult.fail(
                f"{meta['name']} is Silenced and cannot use MP abilities this round. "
                "AP abilities, Attack, Defend, or items are still available."
            )
        if int(meta.get(resource, 0)) < cost:
            return GameResult.fail(
                f"{ability['name']} costs {cost} {resource.upper()}; "
                f"you have {meta.get(resource, 0)}."
            )

        target_type = ability.get("target")
        needs_ko = any(effect.get("type") == "revive" for effect in ability.get("effects", []))
        if target_type == "enemy":
            target_id = "monster"
        elif target_type == "party":
            target_id = "party"
        elif target_type == "self":
            target_id = str(twitch_id)
        else:
            default_id = None if needs_ko else str(twitch_id)
            target_id = self._battle_target_id(target_query, default_id=default_id)
            if not target_id:
                return GameResult.fail(
                    f"Choose a clear ally target. Example: !ability {ability['name']} <hero>."
                )

        if needs_ko:
            target = self.encounter_roster.get(target_id)
            if not target or int(target.get("hp", 0)) > 0:
                return GameResult.fail(
                    f"{ability['name']} needs a KO'd ally target. "
                    f"Example: !ability {ability['name']} <hero>."
                )

        meta["action"] = {
            "kind": "ability",
            "ability_id": ability["id"],
            "target_id": target_id,
            "resource": resource,
            "cost": cost,
        }
        ready = self._all_round_actions_queued()
        target_name = self.encounter_roster.get(target_id, {}).get(
            "name", "enemy" if target_id == "monster" else "party"
        )
        return GameResult.success(
            f"QUEUED R{self.active_encounter['round']} — {meta['name']}: "
            f"{ability['name']} → {target_name} ({cost}{resource.upper()}).",
            all_actions_queued=ready,
        )

    def _match_battle_item(self, query: str) -> tuple[dict[str, Any] | None, str]:
        normalized = normalize_action_text(query)
        matches: list[tuple[int, dict[str, Any], str]] = []
        for item in self.data.items.values():
            use = item.get("use")
            if not isinstance(use, dict) or item.get("id") == "tent":
                continue
            for key in {item.get("id", ""), item.get("name", "")}:
                token = normalize_action_text(str(key))
                if normalized == token:
                    matches.append((len(token), item, ""))
                elif normalized.startswith(token + " "):
                    matches.append((len(token), item, normalized[len(token):].strip()))
        if not matches:
            return None, ""
        _, item, remainder = max(matches, key=lambda row: row[0])
        return item, remainder

    @_state_guard
    def battle_item(self, twitch_id: str, item_query: str) -> GameResult:
        if self.active_boss and self.active_boss.get("state") == "combat" and str(twitch_id) in self.raid_roster:
            return self._queue_raid_item(twitch_id, item_query)
        meta, error = self._active_actor(twitch_id)
        if error:
            return error
        item, target_query = self._match_battle_item(item_query)
        if not item:
            return GameResult.fail("Battle item not found. Use !inventory consumable to see owned combat items.")
        if self._inventory_qty(twitch_id, item["id"]) <= 0:
            return GameResult.fail(f"You do not own {item['name']}.")

        use = item.get("use", {})
        target_mode = str(use.get("target", "ally"))
        effects = use.get("effects", [])
        target_id: str | None
        target_name: str
        if target_mode == "enemy":
            target_id = "monster"
            target_name = self.data.monsters[self.active_encounter["monster_id"]]["name"]
        elif target_mode == "party":
            target_id = "party"
            target_name = "party"
        elif target_mode == "self":
            target_id = str(twitch_id)
            target_name = meta["name"]
        else:
            target_id = self._battle_target_id(target_query, default_id=str(twitch_id))
            if not target_id:
                return GameResult.fail(f"Choose a clear ally target. Example: !use {item['name']} <hero>.")
            target_name = self.encounter_roster[target_id]["name"]

        target = self.encounter_roster.get(target_id) if target_id not in {"monster", "party"} else None
        requires_revive = any(effect.get("type") == "revive" for effect in effects)
        if requires_revive and target and int(target.get("hp", 0)) > 0:
            if not target_query and target_mode == "ally":
                return GameResult.fail(f"{item['name']} needs a KO'd ally target. Example: !use {item['name']} <hero>.")
            return GameResult.fail(f"{target['name']} is not KO'd.")
        if target and any(effect.get("type") == "restore_mp" for effect in effects) and int(target.get("max_mp", 0)) <= 0:
            return GameResult.fail(f"{target['name']} does not use MP; {item['name']} has no effect on that Job.")
        if target and any(effect.get("type") == "restore_ap" for effect in effects) and int(target.get("max_ap", 0)) <= 0:
            return GameResult.fail(f"{target['name']} does not use AP; {item['name']} has no effect on that Job.")

        meta["action"] = {"kind": "item", "item_id": item["id"], "target_id": target_id}
        ready = self._all_round_actions_queued()
        return GameResult.success(
            f"QUEUED R{self.active_encounter['round']} — {meta['name']}: {item['name']} → {target_name}.",
            all_actions_queued=ready,
        )

    def _basic_active_damage(
        self,
        meta: dict[str, Any],
        monster: dict[str, Any],
        *,
        scaling: str | None = None,
        power: float = 1.0,
        crit_bonus: float = 0.0,
        pierce: float = 0.0,
        element: str | None = None,
    ) -> tuple[int, bool]:
        stats = meta["stats"]
        effects = meta["effects"]
        job = self.data.jobs[meta["job_id"]]
        stance = meta.get("stance", "balanced")
        chosen = scaling or job.get("combat_type", "physical")
        if chosen == "hybrid":
            physical_base = stats["str"] * 1.65 + stats["attack"]
            magic_base = stats["mag"] * 1.85 + stats["magic_power"]
            chosen = "magic" if magic_base > physical_base else "physical"
        if chosen == "physical" and has_status(meta.get("statuses", {}), "blind"):
            miss_chance = max(0.18, status_magnitude(meta.get("statuses", {}), "blind"))
            if self.rng.random() < min(0.55, miss_chance):
                return 0, False
        if chosen == "magic":
            base = stats["mag"] * 1.85 + stats["magic_power"]
            stance_mult = {"balanced":1.0,"aggressive":0.95,"defensive":0.9,"magical":1.22,"cautious":1.0}.get(stance, 1.0)
            defense = float(monster["spirit"]) * 0.65 * max(0.0, 1.0 - pierce)
            multiplier = 1 + effects.get("damage_mult", 0) + effects.get("magic_mult", 0)
        else:
            base = stats["str"] * 1.65 + stats["attack"]
            stance_mult = {"balanced":1.0,"aggressive":1.15,"defensive":0.82,"magical":0.92,"cautious":0.88}.get(stance, 1.0)
            defense = float(monster["defense"]) * 0.70 * max(0.0, 1.0 - pierce)
            multiplier = 1 + effects.get("damage_mult", 0) + effects.get("physical_mult", 0)
        if self.active_encounter.get("kind", "venture") == "hunt":
            # Preserve long-standing Hunt-focused Job/mastery bonuses now that
            # Hunts use the shared Active Battle damage path.
            multiplier += float(effects.get("hunt_damage_mult", 0))

        support_count = sum(
            1
            for row in self.encounter_roster.values()
            if int(row.get("hp", 0)) > 0 and row.get("job_id") in SUPPORT_JOBS
        )
        support_bonus = min(0.18, 0.04 * support_count)
        # Temporary status semantics are normalized on both sides of the
        # fight. Power Up/Haste raise player pressure, while Weaken/Slow now
        # actually reduce it instead of being display-only on heroes.
        multiplier *= 1 + support_bonus
        multiplier *= player_outgoing_status_multiplier(meta.get("statuses", {}))
        multiplier *= 1 + status_magnitude(self.active_encounter.get("monster_statuses", {}), "vulnerable")

        # Enemy Evasion and Focus share the same generic status semantics.
        # the semantic loop so it affects incoming physical attacks/abilities.
        if chosen == "physical":
            monster_evade = status_magnitude(
                self.active_encounter.get("monster_statuses", {}), "evade"
            )
            if monster_evade and self.rng.random() < min(0.45, monster_evade):
                return 0, False

        dmg = max(1, int((base * job["damage_mod"] * stance_mult * multiplier * float(power) - defense) * self.rng.uniform(0.88, 1.12)))
        monster_protect = status_magnitude(
            self.active_encounter.get("monster_statuses", {}), "protect"
        )
        if monster_protect:
            dmg = max(1, int(dmg * max(0.20, 1 - monster_protect)))
        if element and monster.get("weakness") and str(monster["weakness"]).lower() == str(element).lower():
            dmg = int(dmg * (1.30 + effects.get("weakness_bonus", 0)))
        critical = False
        if chosen == "physical":
            chance = critical_chance(
                stats["lck"],
                job.get("crit_bonus", 0),
                effects.get("crit_bonus", 0)
                + crit_bonus
                + status_magnitude(meta.get("statuses", {}), "focus"),
            )
            if self.rng.random() < chance:
                dmg = int(dmg * (1.65 + effects.get("crit_damage", 0)))
                critical = True
        return max(1, dmg), critical

    def _apply_battle_heal(self, actor: dict[str, Any], target: dict[str, Any], power: float) -> int:
        if int(target.get("hp", 0)) <= 0:
            return 0
        stats = actor["stats"]
        amount = max(30, int((stats["mag"] * 1.8 + 30) * float(power) * (1 + actor["effects"].get("heal_bonus", 0))))
        before = int(target["hp"])
        target["hp"] = min(int(target["max_hp"]), before + amount)
        healed = int(target["hp"]) - before
        actor["healing"] += healed
        return healed

    def _resolve_active_ability(
        self,
        meta: dict[str, Any],
        action: dict[str, Any],
        monster: dict[str, Any],
        log: list[str],
    ) -> None:
        """Resolve one queued active ability.

        IMPORTANT: this is the resource-spend boundary. Commands only queue
        intent; MP/AP is deducted here after the ability is revalidated.
        """
        ability = next(
            (
                row
                for row in self.data.active_abilities.get(meta["job_id"], [])
                if row["id"] == action.get("ability_id")
            ),
            None,
        )
        job = self.data.jobs.get(meta["job_id"])
        resource = ability_resource(ability, job) if ability else "mp"
        cost = ability_cost(ability) if ability else 0
        if not ability or int(meta.get(resource, 0)) < cost:
            log.append(f"{meta['name']}'s ability fizzles; they fall back to Attack.")
            self._resolve_active_attack(meta, monster, log)
            return
        if resource == "mp" and has_status(meta.get("statuses", {}), "silence"):
            log.append(f"{meta['name']}'s spell is sealed by Silence; they fall back to Attack.")
            self._resolve_active_attack(meta, monster, log)
            return

        target_id = action.get("target_id")
        target = (
            self.encounter_roster.get(target_id)
            if target_id not in {"monster", "party"}
            else None
        )
        meta[resource] = int(meta.get(resource, 0)) - cost
        meta["abilities_used"] += 1

        last_damage = 0
        parts: list[str] = []
        for effect in ability.get("effects", []):
            effect_type = effect.get("type")
            recipient = effect.get("recipient") or "target"

            if effect_type == "damage":
                damage, critical = self._basic_active_damage(
                    meta,
                    monster,
                    scaling=effect.get("scaling"),
                    power=float(effect.get("power", 1.0)),
                    crit_bonus=float(effect.get("crit_bonus", 0)),
                    pierce=float(effect.get("pierce", 0)),
                    element=ability.get("element"),
                )
                self.active_encounter["monster_hp"] = max(
                    0, int(self.active_encounter["monster_hp"]) - damage
                )
                meta["damage"] += damage
                meta["best_hit"] = max(int(meta["best_hit"]), damage)
                last_damage = damage
                parts.append(
                    "MISS" if damage <= 0 else f"{damage}{' CRIT' if critical else ''} dmg"
                )
                continue

            if effect_type == "heal":
                if recipient == "party":
                    targets = list(self.encounter_roster.values())
                elif recipient == "self":
                    targets = [meta]
                else:
                    targets = [target] if target else []
                total = sum(
                    self._apply_battle_heal(meta, row, float(effect.get("power", 1.0)))
                    for row in targets
                    if row
                )
                parts.append(f"{total} heal")
                continue

            if effect_type in {"restore_mp", "restore_ap"}:
                resource_key = "mp" if effect_type == "restore_mp" else "ap"
                resource_label = resource_key.upper()
                if recipient == "party":
                    targets = list(self.encounter_roster.values())
                elif recipient == "self" or target is None:
                    targets = [meta]
                else:
                    targets = [target]

                restored = 0
                fraction = float(effect.get("fraction", 0.0))
                for row in targets:
                    maximum = int(row.get(f"max_{resource_key}", 0))
                    if maximum <= 0:
                        continue
                    before = int(row.get(resource_key, 0))
                    amount = max(1, int(maximum * fraction))
                    row[resource_key] = min(maximum, before + amount)
                    restored += int(row[resource_key]) - before
                parts.append(f"{restored} {resource_label} restored")
                continue

            if effect_type == "revive":
                if target and int(target.get("hp", 0)) <= 0:
                    fraction = float(effect.get("fraction", 0.30))
                    target["hp"] = max(1, int(int(target["max_hp"]) * fraction))
                    parts.append(f"revives {target['name']} at {target['hp']} HP")
                else:
                    parts.append("no valid KO target")
                continue

            if effect_type == "cleanse":
                row = meta if recipient == "self" or not target else target
                removed = cleanse(row.get("statuses", {}), int(effect.get("count", 1)))
                parts.append("cleanses " + (", ".join(removed) if removed else "nothing"))
                continue

            if effect_type == "drain":
                missing_hp = int(meta["max_hp"]) - int(meta["hp"])
                healed = min(
                    missing_hp,
                    max(0, int(last_damage * float(effect.get("fraction", 0.0)))),
                )
                meta["hp"] += healed
                meta["healing"] += healed
                parts.append(f"drains {healed} HP")
                continue

            if effect_type == "status":
                status_id = str(effect.get("status"))
                chance = float(effect.get("chance", 1.0))

                # Hunt marks gain rank-based debuff resistance rather than hard
                # immunities. Stun has an additional one-round resistance window
                # after success because Crystal Guild normally fights one enemy.
                if target_id == "monster":
                    if self.active_encounter.get("kind", "venture") == "hunt":
                        hunt = self.data.hunts.get(self.active_encounter.get("hunt_id"), {})
                        chance = active_hunt_status_chance(chance, hunt.get("rank", "C"), status_id)
                    if status_id == "stun":
                        round_no = int(self.active_encounter.get("round", 1))
                        resist_until = int(self.active_encounter.get("monster_stun_resist_until", 0))
                        if round_no <= resist_until:
                            chance = 0.0

                if self.rng.random() >= chance:
                    if target_id == "monster" and status_id == "stun":
                        parts.append("Stun resisted")
                    continue

                turns = int(effect.get("turns", 1))
                magnitude = float(effect.get("magnitude", 0.0))

                if recipient == "party":
                    for row in self.encounter_roster.values():
                        if int(row.get("hp", 0)) > 0:
                            apply_status(
                                row.setdefault("statuses", {}),
                                status_id,
                                turns,
                                magnitude,
                            )
                elif recipient == "self":
                    apply_status(meta.setdefault("statuses", {}), status_id, turns, magnitude)
                elif target_id == "monster":
                    apply_status(
                        self.active_encounter.setdefault("monster_statuses", {}),
                        status_id,
                        turns,
                        magnitude,
                    )
                    if status_id == "stun":
                        round_no = int(self.active_encounter.get("round", 1))
                        self.active_encounter["monster_stun_resist_until"] = (
                            round_no + STUN_RESIST_ROUNDS_AFTER_SUCCESS
                        )
                elif target:
                    apply_status(
                        target.setdefault("statuses", {}),
                        status_id,
                        turns,
                        magnitude,
                    )
                parts.append(status_id.replace("_", " ").title())

        detail = ", ".join(parts[:4]) or "no effect"
        log.append(f"{meta['name']} uses {ability['name']} — {detail}.")

    def _resolve_active_attack(self, meta: dict[str, Any], monster: dict[str, Any], log: list[str]) -> None:
        # Basic Attack retains signature and chain mechanics, with weapon traits
        # layered on top rather than creating a separate combat path.
        dmg, critical = self._basic_active_damage(meta, monster, element=meta.get("weapon_element"))
        if dmg <= 0:
            log.append(f"{meta['name']} attacks but misses while Blinded.")
            return
        job = self.data.jobs[meta["job_id"]]
        effects = meta["effects"]
        flourishes: list[str] = ["CRITICAL"] if critical else []
        if self.rng.random() < float(job.get("signature_chance", 0)) + float(effects.get("signature_chance", 0)):
            dmg = int(dmg * float(job.get("signature_multiplier", 1.0)) * (1 + float(effects.get("signature_mult", 0))))
            flourishes.append(str(job.get("signature", "Signature")))
        if self.rng.random() < float(effects.get("double_strike_chance", 0)):
            dmg += max(1, int(dmg * 0.65))
            flourishes.append("CHAIN")
        self.active_encounter["monster_hp"] = max(0, int(self.active_encounter["monster_hp"]) - dmg)
        meta["damage"] += dmg
        meta["best_hit"] = max(int(meta["best_hit"]), dmg)

        on_hit = meta.get("on_hit_status") or {}
        if on_hit and int(self.active_encounter["monster_hp"]) > 0:
            status_id = str(on_hit.get("status", ""))
            chance = float(on_hit.get("chance", 0))
            if self.active_encounter.get("kind", "venture") == "hunt":
                hunt = self.data.hunts.get(self.active_encounter.get("hunt_id"), {})
                chance = active_hunt_status_chance(chance, hunt.get("rank", "C"), status_id)
            if self.rng.random() < chance:
                apply_status(
                    self.active_encounter.setdefault("monster_statuses", {}),
                    status_id,
                    int(on_hit.get("turns", 1)),
                    float(on_hit.get("magnitude", 0.0)),
                )
                flourishes.append(status_id.replace("_", " ").upper())

        lifesteal = float(meta.get("lifesteal", 0.0))
        if lifesteal > 0 and int(meta.get("hp", 0)) > 0:
            before = int(meta["hp"])
            meta["hp"] = min(int(meta["max_hp"]), before + max(0, int(dmg * lifesteal)))
            healed = int(meta["hp"]) - before
            if healed:
                meta["healing"] += healed
                flourishes.append(f"DRAIN {healed}")

        suffix = f" [{' / '.join(flourishes)}]" if flourishes else ""
        log.append(f"{meta['name']} attacks for {dmg}{suffix}.")

    def _resolve_active_item(
        self,
        pid: str,
        meta: dict[str, Any],
        action: dict[str, Any],
        log: list[str],
    ) -> None:
        """Resolve one data-driven battle item and consume it only on success."""
        item_id = action.get("item_id")
        item = self.data.items.get(item_id)
        if not item or self._inventory_qty(pid, item_id) <= 0:
            log.append(f"{meta['name']}'s item action fails; they keep the item.")
            return
        use = item.get("use") or {}
        target_mode = str(use.get("target", "ally"))
        target_id = action.get("target_id")
        target = self.encounter_roster.get(target_id)
        if target_mode in {"ally", "self"} and not target:
            log.append(f"{meta['name']}'s item action fails; they keep the item.")
            return

        if target_mode == "party":
            targets = [row for row in self.encounter_roster.values()]
        elif target_mode in {"ally", "self"}:
            targets = [target]
        else:
            targets = []

        parts: list[str] = []
        used = False
        for effect in use.get("effects", []):
            effect_type = effect.get("type")

            if effect_type == "damage" and target_mode == "enemy":
                before = int(self.active_encounter.get("monster_hp", 0))
                amount = max(0, int(effect.get("amount", 0)))
                element = effect.get("element")
                monster_weakness = self.data.monsters[self.active_encounter["monster_id"]].get("weakness")
                if element and monster_weakness and str(monster_weakness).lower() == str(element).lower():
                    amount = int(amount * 1.30)
                self.active_encounter["monster_hp"] = max(0, before - amount)
                dealt = before - int(self.active_encounter["monster_hp"])
                if dealt > 0:
                    meta["damage"] += dealt
                    meta["best_hit"] = max(int(meta["best_hit"]), dealt)
                    used = True
                    parts.append(f"deals {dealt} {element or ''} damage".replace("  ", " "))
                continue

            if effect_type == "heal_hp":
                healed_total = 0
                for row in targets:
                    if not row or int(row.get("hp", 0)) <= 0:
                        continue
                    maximum = int(row.get("max_hp", 0))
                    before = int(row.get("hp", 0))
                    amount = max(0, int(effect.get("amount", 0)))
                    if effect.get("fraction") is not None:
                        amount = max(amount, int(maximum * float(effect.get("fraction", 0))))
                    row["hp"] = min(maximum, before + amount)
                    healed_total += int(row["hp"]) - before
                if healed_total > 0:
                    meta["healing"] += healed_total
                    used = True
                    parts.append(f"restores {healed_total} HP")
                continue

            if effect_type in {"restore_mp", "restore_ap"}:
                key = "mp" if effect_type == "restore_mp" else "ap"
                restored_total = 0
                for row in targets:
                    if not row or int(row.get("hp", 0)) <= 0:
                        continue
                    maximum = int(row.get(f"max_{key}", 0))
                    if maximum <= 0:
                        continue
                    before = int(row.get(key, 0))
                    amount = max(0, int(effect.get("amount", 0)))
                    if effect.get("fraction") is not None:
                        amount = max(amount, int(maximum * float(effect.get("fraction", 0))))
                    row[key] = min(maximum, before + amount)
                    restored_total += int(row[key]) - before
                if restored_total > 0:
                    used = True
                    parts.append(f"restores {restored_total} {key.upper()}")
                continue

            if effect_type == "revive":
                revived = 0
                for row in targets:
                    if not row or int(row.get("hp", 0)) > 0 or int(row.get("max_hp", 0)) <= 0:
                        continue
                    fraction = float(effect.get("fraction", 0.30))
                    row["hp"] = max(1, int(int(row["max_hp"]) * fraction))
                    revived += 1
                if revived:
                    used = True
                    parts.append(f"revives {revived} hero{'es' if revived != 1 else ''}")
                continue

            if effect_type == "cleanse":
                removed_total: list[str] = []
                allowed = set(effect.get("statuses", [])) or None
                count = 99 if effect.get("all_harmful") else int(effect.get("count", 1))
                for row in targets:
                    if not row or int(row.get("hp", 0)) <= 0:
                        continue
                    removed_total.extend(cleanse(row.setdefault("statuses", {}), count, allowed=allowed))
                if removed_total:
                    used = True
                    labels = ", ".join(sorted({x.replace("_", " ").title() for x in removed_total}))
                    parts.append(f"cleanses {labels}")
                continue

            if effect_type == "status":
                applied = 0
                for row in targets:
                    if not row or int(row.get("hp", 0)) <= 0:
                        continue
                    apply_status(
                        row.setdefault("statuses", {}),
                        str(effect.get("status")),
                        int(effect.get("turns", 1)),
                        float(effect.get("magnitude", 0.0)),
                    )
                    applied += 1
                if applied:
                    used = True
                    parts.append(str(effect.get("status", "status")).replace("_", " ").title())
                continue

        if used:
            self._change_item(pid, item_id, -1, "active_battle")
            meta["items_used"] += 1
            log.append(f"{meta['name']} uses {item['name']} — {'; '.join(parts)}.")
            return
        log.append(f"{meta['name']} cannot use {item['name']} effectively right now; the item is not consumed.")

    # ---------- Enemy response layer ----------
    # Enemy selection is data-driven. ``enemy_actions.json`` says what a monster
    # can do, ``enemy_profiles.json`` says how often/when it prefers doing it,
    # and this engine section owns only authoritative math/state mutation.
    def _enemy_target_id(self) -> str | None:
        living_ids = [
            pid for pid, row in self.encounter_roster.items()
            if int(row.get("hp", 0)) > 0
        ]
        if not living_ids:
            return None
        weights: list[float] = []
        for pid in living_ids:
            row = self.encounter_roster[pid]
            weight = 2.5 if row.get("job_id") in TANK_JOBS else 1.0
            if has_status(row.get("statuses", {}), "taunt"):
                weight *= 1 + status_magnitude(row.get("statuses", {}), "taunt")
            weights.append(weight)
        return self.rng.choices(living_ids, weights=weights, k=1)[0]

    def _enemy_damage_against(
        self,
        monster: dict[str, Any],
        target: dict[str, Any],
        profile: dict[str, Any],
        *,
        scaling: str = "physical",
        power: float = 1.0,
    ) -> int:
        """Resolve one enemy hit while honoring player stances/status defense."""
        stats = target["stats"]
        statuses = self.active_encounter.setdefault("monster_statuses", {})
        hp_ratio = int(self.active_encounter.get("monster_hp", 0)) / max(
            1, int(self.active_encounter.get("monster_max_hp", 1))
        )
        pressure = enemy_damage_multiplier(profile, hp_ratio, scaling)
        pressure *= max(0.10, float(self.active_encounter.get("enemy_pressure_mult", 1.0) or 1.0))
        if self.active_encounter.get("kind", "venture") == "hunt":
            hunt = self.data.hunts.get(self.active_encounter.get("hunt_id"), {})
            pressure *= active_hunt_pressure(hunt.get("rank", "C"))
        pressure *= 1 + status_magnitude(statuses, "power_up")
        # Enemy Haste remains meaningful under one-action soft targeting by
        # increasing pressure rather than creating an extra target/action slot.
        pressure *= 1 + status_magnitude(statuses, "haste")
        # Enemy Focus uses the same outgoing-damage status semantics.
        # it mechanically meaningful even though monsters do not use crit rolls.
        pressure *= 1 + status_magnitude(statuses, "focus")
        weaken = status_magnitude(statuses, "weaken")
        slow_pressure = max(0.70, 1 - status_magnitude(statuses, "slow") * 0.50)

        if scaling == "magic":
            offense = float(monster["attack"]) * 1.15 + float(monster.get("spirit", 0)) * 0.45
            defense = float(stats["spr"]) * 0.52
        else:
            offense = float(monster["attack"]) * 1.45
            defense = float(stats["vit"]) * 0.55

        stance = target.get("stance", "balanced")
        stance_def = {
            "balanced": 1.0,
            "aggressive": 0.88,
            "defensive": 1.25,
            "magical": 0.95,
            "cautious": 1.15,
        }.get(stance, 1.0)
        raw_damage = (offense * (1 - weaken) * slow_pressure * pressure * float(power)) - defense
        damage = max(
            1,
            int(raw_damage / stance_def * self.rng.uniform(0.88, 1.12)),
        )
        damage = max(1, int(damage / (1 + target["effects"].get("defense_mult", 0))))
        damage = max(1, int(damage * incoming_vulnerability_multiplier(target.get("statuses", {}))))

        reduction = status_magnitude(target.get("statuses", {}), "protect")
        if target.get("defending"):
            reduction = max(reduction, 0.45)
        damage = max(1, int(damage * max(0.15, 1 - reduction)))

        evade = target["effects"].get("evade_chance", 0) + status_magnitude(
            target.get("statuses", {}), "evade"
        )
        if self.rng.random() < min(0.70, evade):
            return 0
        return damage

    def _apply_enemy_hit(
        self,
        monster: dict[str, Any],
        target: dict[str, Any],
        profile: dict[str, Any],
        *,
        scaling: str,
        power: float,
    ) -> int:
        damage = self._enemy_damage_against(
            monster, target, profile, scaling=scaling, power=power
        )
        target["hp"] = max(0, int(target["hp"]) - damage)
        target["damage_taken"] += damage
        return damage

    def _resolve_enemy_special(
        self,
        monster: dict[str, Any],
        profile: dict[str, Any],
        ability: dict[str, Any],
        log: list[str],
    ) -> None:
        """Resolve one named monster skill from ``enemy_actions.json``."""
        target_type = ability.get("target", "single")
        if target_type == "self":
            target_ids: list[str] = []
        elif target_type == "party":
            target_ids = [
                pid for pid, row in self.encounter_roster.items()
                if int(row.get("hp", 0)) > 0
            ]
        else:
            chosen = self._enemy_target_id()
            target_ids = [chosen] if chosen else []

        total_damage = 0
        damage_parts: list[str] = []
        status_parts: list[str] = []
        monster_statuses = self.active_encounter.setdefault("monster_statuses", {})

        for effect in ability.get("effects", []):
            effect_type = effect.get("type")
            if effect_type == "damage":
                for pid in list(target_ids):
                    target = self.encounter_roster.get(pid)
                    if not target or int(target.get("hp", 0)) <= 0:
                        continue
                    damage = self._apply_enemy_hit(
                        monster,
                        target,
                        profile,
                        scaling=str(ability.get("scaling", "physical")),
                        power=float(ability.get("power", 1.0)),
                    )
                    total_damage += damage
                    damage_parts.append(
                        f"{target['name']} {'evades' if damage == 0 else str(damage)}"
                    )
                continue

            if effect_type == "status":
                recipient = effect.get("recipient", "target")
                status_id = str(effect.get("status", ""))
                turns = int(effect.get("turns", 1))
                magnitude = float(effect.get("magnitude", 0.0))
                chance = effective_status_chance(effect, profile)
                if recipient == "self":
                    if self.rng.random() <= chance:
                        apply_status(monster_statuses, status_id, turns, magnitude)
                        status_parts.append(status_id.replace("_", " ").title())
                    continue
                recipients = target_ids if recipient in {"target", "each"} else []
                landed = 0
                for pid in recipients:
                    target = self.encounter_roster.get(pid)
                    if not target or int(target.get("hp", 0)) <= 0:
                        continue
                    adjusted_chance = self._player_status_chance(target, status_id, chance)
                    if self.rng.random() <= adjusted_chance:
                        apply_status(
                            target.setdefault("statuses", {}),
                            status_id,
                            turns,
                            magnitude,
                        )
                        landed += 1
                if landed:
                    status_parts.append(
                        f"{status_id.replace('_', ' ').title()}×{landed}"
                    )
                continue

            if effect_type == "heal_self":
                fraction = float(effect.get("fraction", 0.0))
                before = int(self.active_encounter["monster_hp"])
                amount = max(1, int(int(self.active_encounter["monster_max_hp"]) * fraction))
                self.active_encounter["monster_hp"] = min(
                    int(self.active_encounter["monster_max_hp"]), before + amount
                )
                healed = int(self.active_encounter["monster_hp"]) - before
                if healed:
                    status_parts.append(f"heals {healed}")
                continue

            if effect_type == "drain" and total_damage > 0:
                fraction = float(effect.get("fraction", 0.0))
                before = int(self.active_encounter["monster_hp"])
                healed = min(
                    int(self.active_encounter["monster_max_hp"]) - before,
                    max(0, int(total_damage * fraction)),
                )
                self.active_encounter["monster_hp"] = before + healed
                if healed:
                    status_parts.append(f"drains {healed} HP")
                continue

            if effect_type == "recoil":
                fraction = float(effect.get("fraction", 0.0))
                recoil = max(1, int(int(self.active_encounter["monster_max_hp"]) * fraction))
                self.active_encounter["monster_hp"] = max(
                    0, int(self.active_encounter["monster_hp"]) - recoil
                )
                status_parts.append(f"takes {recoil} recoil")

        detail = []
        if damage_parts:
            detail.append(", ".join(damage_parts[:6]))
        detail.extend(status_parts[:4])
        log.append(
            f"{monster['name']} uses {ability['name']} — "
            + ("; ".join(detail) if detail else "no effect")
            + "."
        )

    def _active_enemy_turn(self, monster: dict[str, Any], log: list[str]) -> None:
        """Resolve the monster response using the data-driven enemy AI layer."""
        statuses = self.active_encounter.setdefault("monster_statuses", {})
        if has_status(statuses, "stun"):
            log.append(f"{monster['name']} is stunned and loses its turn.")
            return

        living_ids = [
            pid for pid, row in self.encounter_roster.items()
            if int(row.get("hp", 0)) > 0
        ]
        if not living_ids:
            return

        behavior = self.data.enemy_actions.get(monster["id"], {"profile": "balanced"})
        profile = self.data.enemy_profiles.get(
            behavior.get("profile"), self.data.enemy_profiles.get("balanced", {})
        )
        # Soft targeting: one enemy action is resolved per round regardless of
        # rally size. Basic attacks and single-target skills choose one living
        # hero; only abilities explicitly marked ``party`` may hit more than one.
        attacks = party_enemy_attacks(len(living_ids))

        round_no = int(self.active_encounter.get("round", 1))
        special_ready = int(self.active_encounter.get("enemy_special_ready_round", 1))
        special_used = False
        for _ in range(attacks):
            if not any(int(row.get("hp", 0)) > 0 for row in self.encounter_roster.values()):
                break
            hp_ratio = int(self.active_encounter.get("monster_hp", 0)) / max(
                1, int(self.active_encounter.get("monster_max_hp", 1))
            )
            action = choose_enemy_action(
                behavior,
                profile,
                hp_ratio=hp_ratio,
                round_no=round_no,
                special_ready_round=special_ready if not special_used else round_no + 999,
                monster_statuses=statuses,
                rng=self.rng,
            )
            if action["kind"] == "special":
                ability = action["ability"]
                self._resolve_enemy_special(monster, profile, ability, log)
                special_used = True
                self.active_encounter["enemy_special_ready_round"] = (
                    round_no + int(ability.get("cooldown", 1)) + 1
                )
                continue

            if action["kind"] == "utility":
                utility = action["utility"]
                status_id = str(utility.get("status", ""))
                apply_status(
                    statuses,
                    status_id,
                    int(utility.get("turns", 1)),
                    float(utility.get("magnitude", 0.0)),
                )
                log.append(
                    f"{monster['name']} uses {utility.get('name', 'Brace')} — "
                    f"{status_id.replace('_', ' ').title()}."
                )
                continue

            target_id = self._enemy_target_id()
            if not target_id:
                break
            target = self.encounter_roster[target_id]
            damage = self._apply_enemy_hit(
                monster, target, profile, scaling="physical", power=1.0
            )
            if damage == 0:
                log.append(f"{target['name']} evades {monster['name']}'s attack.")
            else:
                log.append(f"{monster['name']} attacks {target['name']} for {damage}.")

    @_state_guard
    def advance_encounter_round(self, encounter_id: int | None = None) -> GameResult:
        """Resolve exactly one Active Battle round.

        A living hero without a queued action defaults to Attack. This is the
        anti-stall rule: lurkers can join a rally without being forced to type
        every round, while active players still control their turns.
        """
        if not self.active_encounter:
            return GameResult.fail("There is no encounter to advance.")
        if encounter_id is not None and int(self.active_encounter["id"]) != int(encounter_id):
            return GameResult.fail("That encounter has already ended.")
        if self.active_encounter.get("state", "rally") == "rally":
            return self.start_encounter_battle(encounter_id)

        monster = self.data.monsters[self.active_encounter["monster_id"]]
        round_no = int(self.active_encounter.get("round", 1))
        living = [
            (pid, row)
            for pid, row in self.encounter_roster.items()
            if int(row.get("hp", 0)) > 0
        ]
        if not living:
            return self._finish_active_encounter(False, reason="No heroes remain standing.")

        for _, row in living:
            if not row.get("action"):
                row["action"] = {"kind": "attack", "auto": True}

        ordered = sorted(
            living,
            key=lambda item: (
                action_priority(item[1]["action"], item[1].get("statuses", {})),
                -int(item[1].get("stats", {}).get("dex", 0)),
            ),
        )

        log: list[str] = []
        for pid, meta in ordered:
            if int(meta.get("hp", 0)) <= 0:
                continue

            action = meta.get("action") or {"kind": "attack"}
            meta["actions"] += 1

            # Hero Stun consumes the action just as monster hard control does.
            # Stun had a gameplay effect. Stunned heroes now explicitly lose
            # the current action, making the shared status vocabulary symmetric.
            if has_status(meta.get("statuses", {}), "stun"):
                log.append(f"{meta['name']} is stunned and loses their action.")
                continue

            if action["kind"] == "defend":
                meta["defending"] = True
                meta["defends"] += 1
                recovered: list[str] = []
                if int(meta.get("max_ap", 0)) > 0:
                    before_ap = int(meta.get("ap", 0))
                    restore_ap = defend_ap_restore(int(meta["max_ap"]))
                    meta["ap"] = min(int(meta["max_ap"]), before_ap + restore_ap)
                    gained_ap = int(meta["ap"]) - before_ap
                    if gained_ap:
                        recovered.append(f"{gained_ap} AP")
                if int(meta.get("max_mp", 0)) > 0:
                    before_mp = int(meta.get("mp", 0))
                    restore_mp = defend_mp_restore(int(meta["max_mp"]))
                    meta["mp"] = min(int(meta["max_mp"]), before_mp + restore_mp)
                    gained_mp = int(meta["mp"]) - before_mp
                    if gained_mp:
                        recovered.append(f"{gained_mp} MP")
                detail = " and ".join(recovered) if recovered else "no resources"
                log.append(f"{meta['name']} Defends and recovers {detail}.")
            elif action["kind"] == "item":
                self._resolve_active_item(pid, meta, action, log)
            elif action["kind"] == "ability":
                self._resolve_active_ability(meta, action, monster, log)
            else:
                self._resolve_active_attack(meta, monster, log)

            if int(self.active_encounter["monster_hp"]) <= 0:
                break

        if int(self.active_encounter["monster_hp"]) <= 0:
            return self._finish_active_encounter(
                True,
                round_log=log,
                round_no=round_no,
            )

        self._active_enemy_turn(monster, log)

        if int(self.active_encounter.get("monster_hp", 0)) <= 0:
            return self._finish_active_encounter(
                True, round_log=log, round_no=round_no
            )

        # End-of-round order is deliberate: resolve DoT/regeneration, age
        # statuses, clear transient action flags, then persist wounds.
        # adds Poison for players and lets enemy self-buffs use the same status
        # vocabulary instead of introducing a second timer system.
        for pid, row in self.encounter_roster.items():
            if has_status(row.get("statuses", {}), "poison") and int(row.get("hp", 0)) > 0:
                poison = max(1, int(int(row.get("max_hp", 1)) * max(0.03, status_magnitude(row.get("statuses", {}), "poison"))))
                row["hp"] = max(0, int(row["hp"]) - poison)
                row["damage_taken"] += poison
                log.append(f"{row['name']} suffers {poison} Poison damage.")
            if has_status(row.get("statuses", {}), "regen") and int(row.get("hp", 0)) > 0:
                self._apply_battle_heal(
                    row,
                    row,
                    status_magnitude(row.get("statuses", {}), "regen"),
                )
            tick_statuses(row.setdefault("statuses", {}))
            row["action"] = None
            row["defending"] = False
            self._save_hp(pid, int(row.get("hp", 0)))
            self._save_resources_from_meta(pid, row)

        monster_statuses = self.active_encounter.setdefault("monster_statuses", {})
        if has_status(monster_statuses, "regen") and int(self.active_encounter.get("monster_hp", 0)) > 0:
            before = int(self.active_encounter["monster_hp"])
            heal = max(1, int(int(self.active_encounter["monster_max_hp"]) * status_magnitude(monster_statuses, "regen")))
            self.active_encounter["monster_hp"] = min(
                int(self.active_encounter["monster_max_hp"]), before + heal
            )
            actual = int(self.active_encounter["monster_hp"]) - before
            if actual:
                log.append(f"{monster['name']} regenerates {actual} HP.")
        tick_statuses(monster_statuses)

        if not any(int(row.get("hp", 0)) > 0 for row in self.encounter_roster.values()):
            return self._finish_active_encounter(
                False,
                reason=f"{monster['name']} wipes the party.",
                round_log=log,
                round_no=round_no,
            )
        max_rounds = int(self.active_encounter.get("max_rounds", 12))
        if round_no >= max_rounds:
            return self._finish_active_encounter(
                False,
                reason=f"The battle reaches the {max_rounds}-round safety limit.",
                round_log=log,
                round_no=round_no,
            )

        self._remember_round(round_no, log)
        self.active_encounter["round"] = round_no + 1
        self.active_encounter["next_round_at"] = time.time() + self.encounter_round_seconds
        enemy_hp = int(self.active_encounter["monster_hp"])
        enemy_max = int(self.active_encounter["monster_max_hp"])
        enemy_status = status_text(self.active_encounter.get("monster_statuses", {}), limit=2)
        return GameResult.success(
            f"ROUND {round_no} — {round_summary(log)}",
            f"NEXT R{round_no + 1} · {self._format_seconds(self.encounter_round_seconds)} | "
            f"{monster['name']} {resource_text('HP', enemy_hp, enemy_max)} {enemy_status} | "
            f"{party_condition_text(self.encounter_roster.values())} | "
            "!attack · !ability · !defend · !use",
            round_resolved=True,
            next_round_at=self.active_encounter["next_round_at"],
            notification_limit=2,
        )

    def _finish_active_encounter(
        self,
        won: bool,
        *,
        reason: str | None = None,
        round_log: list[str] | None = None,
        round_no: int | None = None,
    ) -> GameResult:
        """Persist a Venture or Hunt outcome and release field-combat state.

        Ventures and Hunts deliberately share one resolution path. The encounter
        ``kind`` selects only persistence/reward behavior; round math, status
        processing, timer ownership, and action accounting remain identical.
        """
        if not self.active_encounter:
            return GameResult.fail("The encounter is already over.")

        if round_log:
            self._remember_round(round_no or int(self.active_encounter.get("round", 1)), round_log)
        encounter = dict(self.active_encounter)
        active_id = int(encounter["id"])
        monster = self.data.monsters[encounter["monster_id"]]
        kind = encounter.get("kind", "venture")
        hunt = self.data.hunts.get(encounter.get("hunt_id")) if kind == "hunt" else None
        resolved_round = round_no or int(encounter.get("round", 1))
        log = list(round_log or [])
        messages: list[str] = []
        if log:
            messages.append(f"ROUND {resolved_round} — {round_summary(log)}")

        reward_lines: list[str] = []
        first_clear_lines: list[str] = []
        levelup_lines: list[str] = []
        achievement_lines: list[str] = []
        fellowship_lines: list[str] = []
        hunt_results: dict[str, dict[str, Any]] = {}
        solo_rewards: dict[str, Any] = {"xp": 0, "jp": 0, "gil": 0, "loot": [], "levelups": []}
        solo_pid: str | None = next(iter(self.encounter_roster), None) if kind == "solo_venture" else None
        try:
            for pid, meta in self.encounter_roster.items():
                p = self._player(pid)
                if not p or not meta.get("max_hp"):
                    continue

                knocked_out = int(meta.get("hp", 0)) <= 0
                self._save_hp(pid, int(meta.get("hp", 0)))
                self._save_resources_from_meta(pid, meta)
                self._record_combat_metrics(
                    pid,
                    meta.get("job_id", p["current_job"]),
                    monster["id"],
                    battle_type="hunt" if kind == "hunt" else "venture",
                    won=won,
                    knocked_out=knocked_out,
                    damage_dealt=int(meta.get("damage", 0)),
                    damage_taken=int(meta.get("damage_taken", 0)),
                    healing_done=int(meta.get("healing", 0)),
                    best_hit=int(meta.get("best_hit", 0)),
                )
                self.db.update_record_stats(pid, {
                    "active_actions": int(meta.get("actions", 0)),
                    "active_abilities": int(meta.get("abilities_used", 0)),
                    "active_items": int(meta.get("items_used", 0)),
                    "active_defends": int(meta.get("defends", 0)),
                })
                if knocked_out:
                    self.db.execute(
                        "UPDATE players SET deaths=deaths+1 WHERE twitch_id=?",
                        (pid,),
                    )

                if won and hunt:
                    rewards = self._award_hunt_victory(pid, p, hunt, monster)
                    loot_text = ", ".join(rewards["loot"][:3]) if rewards["loot"] else "no extra drops"
                    reward_lines.append(
                        f"{meta['name']} +{rewards['xp']}XP/{rewards['jp']}JP/"
                        f"{rewards['gil']}g/+{rewards['seals']} seals · {loot_text}"
                    )
                    if rewards["first_clear"]:
                        first_clear_lines.extend(rewards["first_rewards"])
                    levelup_lines.extend(rewards["levelups"])
                    fellowship_lines.extend(self.fellowship_system.record_activity(
                        pid, "hunt_win", event_key=f"hunt_win:{active_id}:{pid}"
                    ))
                    chocobo_gain = {"C": 15, "B": 25, "A": 40, "S": 60}.get(str(hunt.get("rank", "C")).upper(), 15)
                    fellowship_lines.extend(self._award_chocobo_xp(pid, chocobo_gain))
                    hunt_results[str(pid)] = {
                        "type": "hunt",
                        "outcome": "victory",
                        "title": "Mark Slain",
                        "hunt_id": str(hunt.get("id") or ""),
                        "hunt_name": str(hunt.get("name") or "Hunt"),
                        "rank": str(hunt.get("rank") or "C"),
                        "monster": {
                            "id": str(monster.get("id") or ""),
                            "name": str(monster.get("name") or "Unknown Mark"),
                            "level": int(monster.get("level", 1)),
                            "hp_remaining": 0,
                            "max_hp": int(monster.get("hp", 0)),
                        },
                        "rounds": int(resolved_round),
                        "rewards": {
                            "xp": int(rewards.get("xp", 0)),
                            "jp": int(rewards.get("jp", 0)),
                            "gil": int(rewards.get("gil", 0)),
                            "seals": int(rewards.get("seals", 0)),
                            "loot": [str(value) for value in rewards.get("loot", [])],
                            "first_clear": bool(rewards.get("first_clear")),
                            "first_rewards": [str(value) for value in rewards.get("first_rewards", [])],
                            "levelups": [str(value) for value in rewards.get("levelups", [])],
                            "achievements": [],
                        },
                        "combat": {
                            "damage_dealt": int(meta.get("damage", 0)),
                            "damage_taken": int(meta.get("damage_taken", 0)),
                            "best_hit": int(meta.get("best_hit", 0)),
                        },
                        "player": self._solo_result_vitals(pid),
                    }
                elif won:
                    rewards = self._award_victory(pid, p, monster, rally_venture=kind == "venture")
                    if kind == "solo_venture" and pid == solo_pid:
                        solo_rewards = {
                            "xp": int(rewards.get("xp", 0)),
                            "jp": int(rewards.get("jp", 0)),
                            "gil": int(rewards.get("gil", 0)),
                            "loot": [str(value) for value in rewards.get("loot", [])],
                            "levelups": [str(value) for value in rewards.get("levelups", [])],
                        }
                    rally_note = (
                        f" · Rally danger +{rewards['rally_bonus_pct']}%"
                        if int(rewards.get("rally_bonus_pct", 0)) > 0 else ""
                    )
                    reward_lines.append(
                        f"{meta['name']} +{rewards['xp']}XP/{rewards['jp']}JP/{rewards['gil']}g"
                        + (f" +{','.join(rewards['loot'][:2])}" if rewards["loot"] else "")
                        + rally_note
                    )
                    levelup_lines.extend(rewards.get("levelups", []))
                    fellowship_lines.extend(self.fellowship_system.record_activity(
                        pid,
                        "venture_complete",
                        renown=SOLO_VENTURE_FELLOWSHIP_RENOWN if kind == "solo_venture" else None,
                        event_key=f"{kind}_complete:{active_id}:{pid}",
                    ))
                    fellowship_lines.extend(self.fellowship_system.record_activity(
                        pid, "encounter_win", renown=0, event_key=f"encounter_win:{active_id}:{pid}"
                    ))
                    fellowship_lines.extend(self._award_chocobo_xp(pid, 12))

                if hunt and not won:
                    hunt_results[str(pid)] = {
                        "type": "hunt",
                        "outcome": "defeat",
                        "title": "Hunt Failed",
                        "hunt_id": str(hunt.get("id") or ""),
                        "hunt_name": str(hunt.get("name") or "Hunt"),
                        "rank": str(hunt.get("rank") or "C"),
                        "monster": {
                            "id": str(monster.get("id") or ""),
                            "name": str(monster.get("name") or "Unknown Mark"),
                            "level": int(monster.get("level", 1)),
                            "hp_remaining": max(0, int(encounter.get("monster_hp", monster.get("hp", 0)))),
                            "max_hp": int(monster.get("hp", 0)),
                        },
                        "rounds": int(resolved_round),
                        "rewards": {"xp": 0, "jp": 0, "gil": 0, "seals": 0, "loot": [], "first_clear": False, "first_rewards": [], "levelups": [], "achievements": []},
                        "combat": {
                            "damage_dealt": int(meta.get("damage", 0)),
                            "damage_taken": int(meta.get("damage_taken", 0)),
                            "best_hit": int(meta.get("best_hit", 0)),
                        },
                        "player": self._solo_result_vitals(pid),
                        "reason": str(reason or "The mark remains on the board."),
                    }

                player_achievements = self._check_achievements(pid)
                achievement_lines.extend(player_achievements)
                if str(pid) in hunt_results:
                    hunt_results[str(pid)]["rewards"]["achievements"] = [str(value) for value in player_achievements[:4]]

            if won and hunt:
                messages.append(
                    f"MARK SLAIN [{hunt['rank']}] — {hunt['name']} falls in "
                    f"{resolved_round} rounds. " + " | ".join(reward_lines[:3])
                )
                if first_clear_lines:
                    messages.append("FIRST CLEAR — " + " | ".join(first_clear_lines[:5]))
            elif won:
                prefix = "SOLO VICTORY" if kind == "solo_venture" else "VICTORY"
                messages.append(
                    f"{prefix} — {monster['name']} falls in {resolved_round} rounds. "
                    + " | ".join(reward_lines[:6])
                )
            elif hunt:
                messages.append(
                    f"HUNT FAILED [{hunt['rank']}] — {hunt['name']}: "
                    f"{monster['name']} survives with "
                    f"{int(encounter.get('monster_hp', monster['hp'])):,} HP. "
                    f"{reason or 'The mark remains on the board.'}"
                )
            else:
                prefix = "SOLO VENTURE FAILED" if kind == "solo_venture" else "PARTY WIPE"
                messages.append(
                    f"{prefix} — {monster['name']} survives with "
                    f"{int(encounter.get('monster_hp', monster['hp'])):,} HP. "
                    f"{reason or 'The campfire is about to become very popular.'}"
                )

            if levelup_lines:
                messages.append("Level up! " + " | ".join(levelup_lines[:6]))
            if achievement_lines:
                messages.append("Achievement unlocked: " + " | ".join(achievement_lines[:4]))
            if fellowship_lines:
                messages.append("Fellowship — " + " | ".join(dict.fromkeys(fellowship_lines[:6])))

            solo_result: dict[str, Any] | None = None
            if kind == "solo_venture" and solo_pid:
                meta = self.encounter_roster.get(solo_pid, {})
                region = self.data.regions.get(encounter.get("region_id"), {})
                solo_result = {
                    "type": "encounter",
                    "outcome": "victory" if won else "defeat",
                    "title": "Victory" if won else "Defeat",
                    "region_name": str(region.get("name") or "Unknown Region"),
                    "enemy": {
                        "id": str(monster.get("id") or ""),
                        "name": str(monster.get("name") or "Unknown Enemy"),
                        "level": int(monster.get("level", 1)),
                    },
                    "rounds": int(resolved_round),
                    "rewards": {
                        **solo_rewards,
                        "fellowship_renown": SOLO_VENTURE_FELLOWSHIP_RENOWN if won else 0,
                        "achievements": [str(value) for value in achievement_lines[:4]],
                    },
                    "notes": [str(value) for value in fellowship_lines if "Chocobo" in str(value)][:2],
                    "combat": {
                        "damage_dealt": int(meta.get("damage", 0)),
                        "damage_taken": int(meta.get("damage_taken", 0)),
                        "best_hit": int(meta.get("best_hit", 0)),
                    },
                    "player": self._solo_result_vitals(solo_pid),
                    "cooldown_seconds": SOLO_VENTURE_COOLDOWN_SECONDS,
                    "resolved_immediately": True,
                }
                self._remember_adventure_result(solo_pid, solo_result)

            self._last_battle_history = {
                "title": self._battle_history_title(),
                "history": list(self.active_encounter.get("round_history", [])) if self.active_encounter else [],
                "won": won,
                "finished_at": time.time(),
                "participants": [str(pid) for pid in self.encounter_roster],
                "messages": list(messages[-4:]),
                "kind": kind,
                "monster_name": str(monster.get("name") or "Unknown Enemy"),
                "hunt_name": str(hunt.get("name")) if hunt else None,
                "hunt_results": hunt_results,
            }
            return GameResult.success(
                *messages,
                encounter_finished=True,
                hunt_finished=kind == "hunt",
                solo_venture_finished=kind == "solo_venture",
                won=won,
                solo_result=solo_result,
                resolved_immediately=kind == "solo_venture",
                notification_limit=4,
            )
        finally:
            self._clear_encounter(active_id)

    @_state_guard
    def _clear_encounter(self, encounter_id: int | None = None) -> bool:
        """Clear encounter state only if the caller still owns that encounter id."""
        if not self.active_encounter:
            return False
        if encounter_id is not None and int(self.active_encounter["id"]) != int(encounter_id):
            return False
        self.active_encounter = None
        self.encounter_roster.clear()
        return True

    @_state_guard
    def abort_encounter(self) -> GameResult:
        if not self.active_encounter:
            return GameResult.success("No encounter is active.")
        monster = self.data.monsters.get(self.active_encounter.get("monster_id"), {})
        name = monster.get("name", "the current encounter")
        self._clear_encounter(int(self.active_encounter["id"]))
        return GameResult.success(f"Encounter cleared: {name}. The Guild has swept the remaining combat paperwork under the rug.")

    @_state_guard
    def resolve_encounter(self, encounter_id: int | None = None) -> GameResult:
        """Compatibility/admin resolver: auto-play an encounter to completion.

        Production scheduling uses start_encounter_battle()/advance_encounter_round().
        Keeping this wrapper gives owner tools, legacy tests and recovery scripts a
        bounded way to force completion without duplicating combat logic.
        """
        if not self.active_encounter:
            return GameResult.fail("There is no encounter to resolve.")
        if encounter_id is not None and int(self.active_encounter["id"]) != int(encounter_id):
            return GameResult.fail("That encounter has already ended.")
        if self.active_encounter.get("state", "rally") == "rally":
            started = self.start_encounter_battle(encounter_id)
            if not started.ok or started.data.get("encounter_finished"):
                return started
        messages: list[str] = []
        for _ in range(12):
            if not self.active_encounter:
                break
            result = self.advance_encounter_round(encounter_id)
            messages.extend(result.messages)
            if result.data.get("encounter_finished"):
                return GameResult.success(*messages[-6:], **result.data)
        if self.active_encounter:
            final = self._finish_active_encounter(False, reason="Admin resolver reached the safety cap.")
            messages.extend(final.messages)
        return GameResult.success(*messages[-6:], encounter_finished=True)


    # Deterministic party simulator retained for balance regression and offline
    # comparison tools. Production random encounters use the
    # Active Battle round engine above; do not add new live mechanics here.
    def _party_battle(self, roster: dict[str, dict[str, str]], monster: dict[str, Any]) -> dict[str, Any]:
        combatants: dict[str, dict[str, Any]] = {}
        for pid, meta in roster.items():
            self._finish_rest_if_ready(pid)
            p = self._player(pid)
            if not p or p["current_job"] == "adventurer" or p["current_hp"] <= 0:
                continue
            job_id = meta.get("job_id", p["current_job"])
            job = self.data.jobs[job_id]
            effects = self._effects(pid, job["id"])
            stats = self._stats(p, job, effects)
            combatants[pid] = {"p": p, "job": job, "effects": effects, "stats": stats, "hp": min(int(p["current_hp"]), stats["hp"]), "damage": 0, "healing": 0, "damage_taken": 0, "best_hit": 0}
        if not combatants:
            return {"won": False, "rounds": 0, "monster_max_hp": monster["hp"], "monster_hp": monster["hp"], "log": ["Nobody was conscious when combat started."], "ko_ids": list(roster)}
        size = len(combatants)
        monster_max = party_monster_hp(monster["hp"], size)
        monster_hp = monster_max
        log: list[str] = []
        support_bonus = min(0.18, 0.04 * sum(1 for c in combatants.values() if c["job"]["id"] in SUPPORT_JOBS))
        for round_no in range(1, 13):
            alive = [c for c in combatants.values() if c["hp"] > 0]
            if not alive:
                break
            for c in list(alive):
                p, job, effects, stats = c["p"], c["job"], c["effects"], c["stats"]
                alive_now = [x for x in combatants.values() if x["hp"] > 0]
                lowest = min(alive_now, key=lambda x: x["hp"] / max(1, x["stats"]["hp"]))
                healer = job["id"] in HEALER_JOBS or (job["id"] == "redmage" and self.rng.random() < 0.45)
                if healer and lowest["hp"] < lowest["stats"]["hp"] * 0.58:
                    amount = max(35, int((stats["mag"] * 1.8 + 30) * (1 + effects.get("heal_bonus", 0))))
                    before = lowest["hp"]
                    lowest["hp"] = min(lowest["stats"]["hp"], lowest["hp"] + amount)
                    c["healing"] += lowest["hp"] - before
                    if round_no <= 2:
                        log.append(f"R{round_no}: {p['display_name']} restores {lowest['p']['display_name']} for {lowest['hp']-before} HP.")
                    continue
                stance = p["stance"]
                use_magic = job["combat_type"] in {"magic", "hybrid"} and (job["combat_type"] == "magic" or self.rng.random() < 0.5)
                if use_magic:
                    base = stats["mag"] * 1.85 + stats["magic_power"]
                    sm = {"balanced":1.0,"aggressive":0.95,"defensive":0.9,"magical":1.22,"cautious":1.0}[stance]
                    dmg = max(1, int((base * job["damage_mod"] * sm * (1 + effects.get("damage_mult",0)+effects.get("magic_mult",0)+support_bonus) - monster["spirit"]*0.65) * self.rng.uniform(0.88,1.12)))
                else:
                    base = stats["str"] * 1.65 + stats["attack"]
                    sm = {"balanced":1.0,"aggressive":1.15,"defensive":0.82,"magical":0.92,"cautious":0.88}[stance]
                    dmg = max(1, int((base * job["damage_mod"] * sm * (1 + effects.get("damage_mult",0)+effects.get("physical_mult",0)+support_bonus) - monster["defense"]*0.70) * self.rng.uniform(0.88,1.12)))
                if monster.get("weakness") and use_magic:
                    dmg = int(dmg * (1.30 + effects.get("weakness_bonus", 0)))
                critical = False
                if not use_magic:
                    chance = critical_chance(stats["lck"], job.get("crit_bonus", 0), effects.get("crit_bonus", 0))
                    if self.rng.random() < chance:
                        dmg = int(dmg * (1.65 + effects.get("crit_damage", 0)))
                        critical = True
                if self.rng.random() < job.get("signature_chance",0)+effects.get("signature_chance",0):
                    dmg = int(dmg * job.get("signature_multiplier",1.0) * (1 + effects.get("signature_mult",0)))
                chained = False
                if self.rng.random() < effects.get("double_strike_chance", 0):
                    dmg += max(1, int(dmg * 0.65))
                    chained = True
                c["damage"] += dmg
                c["best_hit"] = max(c["best_hit"], dmg)
                monster_hp -= dmg
                if round_no <= 2:
                    flourish = " critical" if critical else ""
                    flourish += " chain" if chained else ""
                    log.append(f"R{round_no}: {p['display_name']} deals {dmg} damage{flourish}.")
                if monster_hp <= 0:
                    break
            if monster_hp <= 0:
                for pid,c in combatants.items(): self._save_hp(pid, c["hp"])
                return {
                    "won": True,
                    "rounds": round_no,
                    "monster_max_hp": monster_max,
                    "monster_hp": 0,
                    "log": log,
                    "ko_ids": [pid for pid, c in combatants.items() if c["hp"] <= 0],
                    "contributions": {pid: c["damage"] for pid, c in combatants.items()},
                    "healing": {pid: c["healing"] for pid, c in combatants.items()},
                    "damage_taken": {pid: c["damage_taken"] for pid, c in combatants.items()},
                    "best_hits": {pid: c["best_hit"] for pid, c in combatants.items()},
                }
            alive_ids = [pid for pid,c in combatants.items() if c["hp"] > 0]
            attacks = party_enemy_attacks(size)
            for _ in range(attacks):
                alive_ids = [pid for pid,c in combatants.items() if c["hp"] > 0]
                if not alive_ids: break
                weights = [2.5 if combatants[pid]["job"]["id"] in TANK_JOBS else 1.0 for pid in alive_ids]
                pid = self.rng.choices(alive_ids, weights=weights, k=1)[0]
                c = combatants[pid]
                special = monster.get("special")
                mult = 1.0
                special_name = None
                if special and self.rng.random() < special.get("chance",0):
                    mult = special.get("multiplier",1.0); special_name=special.get("name")
                stance_def={"balanced":1.0,"aggressive":0.88,"defensive":1.25,"magical":0.98,"cautious":1.15}[c["p"]["stance"]]
                dmg=max(1,int(((monster["attack"]*1.45)-c["stats"]["vit"]*0.55)*mult/stance_def*self.rng.uniform(0.88,1.12)))
                dmg=max(1,int(dmg/(1+c["effects"].get("defense_mult",0))))
                if self.rng.random() < c["effects"].get("evade_chance",0): dmg=0
                c["hp"] -= dmg
                c["damage_taken"] += max(0, dmg)
                if round_no <= 2:
                    verb = special_name or "attack"
                    log.append(f"{monster['name']} uses {verb} on {c['p']['display_name']} for {dmg}.")
                if c["hp"] <= 0:
                    if self._inventory_qty(pid,"phoenix_down") > 0:
                        self._change_item(pid,"phoenix_down",-1,"party_auto_revive")
                        c["hp"] = max(1,int(c["stats"]["hp"]*0.30))
                    else:
                        c["hp"] = 0
            for pid,c in combatants.items():
                if 0 < c["hp"] <= c["stats"]["hp"]*0.30 and self._inventory_qty(pid,"potion")>0:
                    self._change_item(pid,"potion",-1,"party_auto_item")
                    c["hp"] = min(c["stats"]["hp"], c["hp"] + max(50,int(c["stats"]["hp"]*0.32)))
        for pid,c in combatants.items(): self._save_hp(pid, max(0,c["hp"]))
        return {
            "won": monster_hp <= 0,
            "rounds": 12,
            "monster_max_hp": monster_max,
            "monster_hp": max(0, monster_hp),
            "log": log,
            "ko_ids": [pid for pid, c in combatants.items() if c["hp"] <= 0],
            "contributions": {pid: c["damage"] for pid, c in combatants.items()},
            "healing": {pid: c["healing"] for pid, c in combatants.items()},
            "damage_taken": {pid: c["damage_taken"] for pid, c in combatants.items()},
            "best_hits": {pid: c["best_hit"] for pid, c in combatants.items()},
        }

    # The former immediate solo Hunt resolver was removed from live gameplay.
    # Live Ventures and Hunts now share the Active Battle round engine above.
    # _party_battle() remains only as a deterministic balance simulator.

    def _award_victory(
        self,
        player_id: str,
        p: Any,
        monster: dict[str, Any],
        *,
        rally_venture: bool = False,
    ) -> dict[str, Any]:
        level_factor = encounter_reward_factor(p["level"], monster["level"])
        job_level = self._job_level(player_id, p["current_job"])
        jp_factor = jp_reward_factor(p["level"], job_level, monster["level"])
        rally_multiplier = rally_venture_reward_multiplier(p["level"], monster["level"]) if rally_venture else 1.0
        xp = max(5, int(monster["xp"] * level_factor * rally_multiplier * self.rng.uniform(0.92, 1.08)))
        jp = self.fellowship_system.apply_jp_bonus(max(2, int(monster["jp"] * jp_factor * rally_multiplier * self.rng.uniform(0.95, 1.10))))
        gil = max(1, int(monster["gil"] * level_factor * rally_multiplier * self.rng.uniform(0.85, 1.18)))
        job = self.data.jobs[p["current_job"]]
        effects = self._effects(player_id, p["current_job"])
        gil = int(gil * (1 + job.get("gil_bonus", 0) + effects.get("gil_bonus", 0)))
        loot_bonus = job.get("loot_bonus", 0) + effects.get("loot_bonus", 0)
        loot: list[str] = []

        with self.db.tx() as conn:
            conn.execute("UPDATE players SET xp=xp+?, gil=gil+?, monsters_defeated=monsters_defeated+1 WHERE twitch_id=?", (xp, gil, player_id))
            conn.execute("UPDATE player_jobs SET jp=jp+? WHERE player_id=? AND job_id=?", (jp, player_id, p["current_job"]))
            conn.execute("INSERT INTO bestiary(player_id, monster_id, defeats) VALUES (?, ?, 1) ON CONFLICT(player_id, monster_id) DO UPDATE SET defeats=defeats+1", (player_id, monster["id"]))
            conn.execute("INSERT INTO transactions(player_id, kind, asset_id, amount, source) VALUES (?, 'gil', 'gil', ?, ?)", (player_id, gil, f"monster:{monster['id']}"))
        for drop in monster.get("drops", []):
            chance = min(0.95, drop["chance"] * (1 + loot_bonus))
            if self.rng.random() <= chance:
                qty = self.rng.randint(drop.get("min", 1), drop.get("max", 1))
                self._change_item(player_id, drop["item_id"], qty, f"drop:{monster['id']}")
                loot.append(f"{self.data.items[drop['item_id']]['name']} x{qty}")
        loot.extend(self._roll_pity_drops(player_id, monster, source=f"monster:{monster['id']}", loot_bonus=loot_bonus))
        loot.extend(self._roll_recipe_drops(player_id, monster, source=f"monster:{monster['id']}", loot_bonus=loot_bonus))
        levelups = self._process_levels(player_id, p["current_job"])
        return {
            "xp": xp, "jp": jp, "gil": gil, "loot": loot, "levelups": levelups,
            "rally_bonus_pct": int(round(max(0.0, rally_multiplier - 1.0) * 100)),
        }

    def _process_levels(self, player_id: str, job_id: str) -> list[str]:
        messages: list[str] = []
        with self.db.tx() as conn:
            p = conn.execute("SELECT level, xp FROM players WHERE twitch_id=?", (player_id,)).fetchone()
            level, xp = p["level"], p["xp"]
            while level < 99 and xp >= xp_to_next(level):
                xp -= xp_to_next(level)
                level += 1
                messages.append(f"Character Lv.{level}")
            conn.execute("UPDATE players SET level=?, xp=? WHERE twitch_id=?", (level, xp, player_id))

            j = conn.execute("SELECT level, jp FROM player_jobs WHERE player_id=? AND job_id=?", (player_id, job_id)).fetchone()
            if j:
                jlevel, jp = j["level"], j["jp"]
                while jlevel < 50 and jp >= jp_to_next(jlevel):
                    jp -= jp_to_next(jlevel)
                    jlevel += 1
                    passive = next((a for a in self.data.jobs[job_id].get("abilities", []) if a["level"] == jlevel), None)
                    active = next((a for a in self.data.active_abilities.get(job_id, []) if int(a.get("level", 0)) == jlevel), None)
                    unlocked_names = []
                    if passive:
                        unlocked_names.append(str(passive["name"]))
                    if active:
                        unlocked_names.append(f"{active['name']} (Battle Ability)")
                    if unlocked_names:
                        messages.append(
                            f"{self.data.jobs[job_id]['name']} JLv.{jlevel} — "
                            + " + ".join(unlocked_names)
                            + " unlocked"
                        )
                    elif jlevel == 50:
                        messages.append(f"{self.data.jobs[job_id]['name']} MASTERED — {self.data.jobs[job_id]['mastery']['name']} available")
                        messages.extend(self.fellowship_system.record_activity(
                            player_id, "job_mastery", event_key=f"job_mastery:{player_id}:{job_id}"
                        )[:1])
                    else:
                        messages.append(f"{self.data.jobs[job_id]['name']} JLv.{jlevel}")
                conn.execute("UPDATE player_jobs SET level=?, jp=? WHERE player_id=? AND job_id=?", (jlevel, jp, player_id, job_id))
        return messages

    # ---------- hunts ----------
    @staticmethod
    def _hunt_duration_seconds(rank: str) -> int:
        return int(HUNT_DURATION_SECONDS.get(str(rank).upper(), HUNT_DURATION_SECONDS["C"]))

    def _active_hunt_public(self, twitch_id: str) -> dict[str, Any] | None:
        assignment = self.active_hunts.get(str(twitch_id))
        if not assignment:
            return None
        hunt = self.data.hunts.get(str(assignment.get("hunt_id"))) or {}
        monster = self.data.monsters.get(str(assignment.get("monster_id"))) or {}
        now = int(time.time())
        resolves_at = int(float(assignment.get("resolves_at") or 0))
        started_at = int(float(assignment.get("started_at") or now))
        duration_seconds = max(1, int(assignment.get("duration_seconds") or (resolves_at - started_at) or 1))
        remaining = max(0, resolves_at - now)
        elapsed = max(0, min(duration_seconds, duration_seconds - remaining))
        return {
            "id": int(assignment.get("id") or 0),
            "hunt_id": str(hunt.get("id") or assignment.get("hunt_id") or ""),
            "name": str(hunt.get("name") or "Hunt"),
            "rank": str(hunt.get("rank") or assignment.get("rank") or "C"),
            "monster": {
                "id": str(monster.get("id") or assignment.get("monster_id") or ""),
                "name": str(monster.get("name") or "Unknown Mark"),
                "level": int(monster.get("level") or hunt.get("min_level") or 1),
            },
            "started_at": started_at,
            "resolves_at": resolves_at,
            "duration_seconds": duration_seconds,
            "remaining_seconds": remaining,
            "progress_percent": max(0, min(100, int(round(100 * elapsed / duration_seconds)))),
            "mode": "autonomous",
        }

    def hunts(self, twitch_id: str, rank: str | None = None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        active = self._active_hunt_public(twitch_id)
        if rank:
            rank = rank.upper()
            if rank not in HUNT_RANKS:
                return GameResult.fail("Hunt rank must be C, B, A, S, or S+.")
            marks = [h for h in self.data.hunts.values() if h["rank"] == rank]
            parts = []
            for hunt in marks:
                met, _ = self._hunt_available(twitch_id, hunt)
                row = self.db.one("SELECT clears FROM player_hunts WHERE player_id=? AND hunt_id=?", (twitch_id, hunt["id"]))
                clears = row["clears"] if row else 0
                state = f"✓x{clears}" if clears else ("READY" if met else "LOCKED")
                parts.append(f"{hunt['name']} [{state}/Lv.{hunt['min_level']}]")
            messages = [
                f"{rank}-Rank Hunts — " + " | ".join(parts),
                f"Dispatch with !hunt <name>. No round commands are required; {rank}-Rank Hunts return in {self._format_seconds(self._hunt_duration_seconds(rank))}.",
            ]
            if active:
                messages.insert(0, f"HUNT IN PROGRESS [{active['rank']}] — {active['name']} returns in {self._format_seconds(active['remaining_seconds'])}.")
            return GameResult.success(*messages)
        counts = []
        ranks = [name for name in ("C", "B", "A", "S", "S+") if any(h.get("rank") == name for h in self.data.hunts.values())]
        for rank_name in ranks:
            total = len([h for h in self.data.hunts.values() if h["rank"] == rank_name])
            cleared = self._rank_unique_clears(twitch_id, rank_name)
            counts.append(f"{rank_name}: {cleared}/{total}")
        ready = []
        for hunt in sorted(self.data.hunts.values(), key=lambda h: (HUNT_RANKS[h["rank"]], h["min_level"])):
            met, _ = self._hunt_available(twitch_id, hunt)
            if met:
                ready.append(hunt)
        suggestion = f" Suggested mark: {ready[0]['name']} ({ready[0]['rank']}-Rank)." if ready else " No marks currently meet your requirements."
        messages = [
            f"Hunt Board | {p['hunt_seals']:,} Hunt Seals | " + " | ".join(counts) + f" | Ready now: {len(ready)}",
            "Timers — C 15m · B 30m · A 2h · S 5h. Dispatch with !hunt <name>; Hunts resolve automatically." + suggestion,
        ]
        if active:
            messages.insert(0, f"HUNT IN PROGRESS [{active['rank']}] — {active['name']} · {active['monster']['name']} | returns in {self._format_seconds(active['remaining_seconds'])}.")
        return GameResult.success(*messages)

    def _hunt_prepare_combat_snapshot(self, twitch_id: str, hunt: dict[str, Any], monster: dict[str, Any], encounter_id: int) -> tuple[dict[str, Any], dict[str, Any], int]:
        """Snapshot the accepted hero into the normal combat model without taking the global battle slot."""
        old_encounter, old_roster = self.active_encounter, self.encounter_roster
        try:
            self.active_encounter = {
                "id": int(encounter_id),
                "kind": "hunt",
                "state": "combat",
                "hunt_id": str(hunt["id"]),
                "hunt_rank": str(hunt["rank"]),
                "monster_id": str(monster["id"]),
                "region_id": str(self._player(twitch_id)["current_region"]),
                "created_at": int(time.time()),
                "starter_id": str(twitch_id),
            }
            p = self._player(twitch_id)
            self.encounter_roster = {
                str(twitch_id): {
                    "name": p["display_name"],
                    "username": p["username"],
                    "job_id": p["current_job"],
                }
            }
            combatants, _, monster_max = self._initialize_active_combat(self.active_encounter)
            if combatants != 1:
                return {}, {}, 0
            self.active_encounter["next_round_at"] = 0
            return copy.deepcopy(self.active_encounter), copy.deepcopy(self.encounter_roster), int(monster_max)
        finally:
            self.active_encounter, self.encounter_roster = old_encounter, old_roster

    @_state_guard
    def hunt(self, twitch_id: str, hunt_query: str, bypass_cooldown: bool = False) -> GameResult:
        """Dispatch a personal timed Hunt that resolves autonomously at its rank deadline.

        Hunts deliberately do not occupy the shared Twitch Active Battle slot and
        do not require round-by-round chat input. The hero's combat build is
        snapshotted at acceptance, then the daemon runs the normal combat engine
        once when the assignment timer expires.
        """
        twitch_id = str(twitch_id)
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if p["current_job"] == "adventurer":
            return GameResult.fail("Choose a Job before accepting a Hunt.")
        if twitch_id in self.active_hunts:
            active = self._active_hunt_public(twitch_id)
            return GameResult.fail(
                f"You already have a Hunt in progress: {active['name']} returns in {self._format_seconds(active['remaining_seconds'])}."
            )
        if twitch_id in self.encounter_roster:
            return GameResult.fail("Finish your active encounter before accepting a Hunt.")
        if twitch_id in self.raid_roster:
            return GameResult.fail("Finish your active raid before accepting a Hunt.")
        blocked = self._activity_block(twitch_id)
        if blocked:
            return GameResult.fail(blocked)

        hunt = self._find_by_name_or_id(self.data.hunts, hunt_query)
        if not hunt:
            return GameResult.fail("Hunt not found. Use !hunts <C|B|A|S|S+> to inspect the board.")
        met, missing = self._hunt_available(twitch_id, hunt)
        if not met:
            return GameResult.fail(f"{hunt['name']} is unavailable — " + "; ".join(missing[:5]))

        remaining = self._cooldown_remaining(twitch_id, f"hunt:{hunt['id']}")
        if remaining > 0 and not bypass_cooldown:
            return GameResult.fail(
                "That mark is still recovering from previous bad decisions. "
                f"Try again in {self._format_seconds(remaining)}."
            )

        monster = self.data.monsters[hunt["monster_id"]]
        now = time.time()
        self._encounter_seq += 1
        encounter_id = int(self._encounter_seq)
        encounter, roster, monster_max = self._hunt_prepare_combat_snapshot(twitch_id, hunt, monster, encounter_id)
        if not encounter or not roster:
            return GameResult.fail("That Hunt cannot begin while your hero is unable to fight.")

        rank = str(hunt.get("rank", "C")).upper()
        duration_seconds = self._hunt_duration_seconds(rank)
        resolves_at = int(now) + duration_seconds
        self.active_hunts[twitch_id] = {
            "id": encounter_id,
            "player_id": twitch_id,
            "hunt_id": str(hunt["id"]),
            "rank": rank,
            "monster_id": str(monster["id"]),
            "started_at": int(now),
            "resolves_at": resolves_at,
            "duration_seconds": duration_seconds,
            "encounter": encounter,
            "roster": roster,
        }

        # Cooldown starts at acceptance, but can never expire before the timed
        # assignment itself is complete.
        cooldown_seconds = max(duration_seconds, int(hunt.get("cooldown_seconds", duration_seconds)))
        self._set_cooldown(twitch_id, f"hunt:{hunt['id']}", cooldown_seconds)
        return GameResult.success(
            f"HUNT DISPATCHED [{rank}] — {hunt['name']} · {monster['name']} Lv.{monster['level']} | expected return in {self._format_seconds(duration_seconds)}.",
            "No chat combat is required. Your hero will automatically Attack, use learned abilities, Defend, and spend a small number of appropriate consumables when survival warrants it.",
            hunt_started=True,
            hunt_id=str(hunt["id"]),
            hunt_run_id=encounter_id,
            resolves_at=resolves_at,
            duration_seconds=duration_seconds,
            enemy_max_hp=monster_max,
        )

    @staticmethod
    def _hunt_harmful_statuses(meta: dict[str, Any]) -> set[str]:
        harmful = {"vulnerable", "weaken", "slow", "stun", "poison", "silence", "blind"}
        return {status for status in harmful if has_status(meta.get("statuses", {}), status)}

    def _hunt_best_ability_action(self, twitch_id: str, meta: dict[str, Any], monster: dict[str, Any], *, urgent_only: bool = False) -> tuple[dict[str, Any] | None, float]:
        job = self.data.jobs.get(str(meta.get("job_id"))) or {}
        hp = int(meta.get("hp", 0)); max_hp = max(1, int(meta.get("max_hp", 1)))
        hp_ratio = hp / max_hp
        harmful = self._hunt_harmful_statuses(meta)
        monster_statuses = self.active_encounter.get("monster_statuses", {}) if self.active_encounter else {}
        best: tuple[dict[str, Any] | None, float] = (None, -999.0)
        for ability in unlocked_abilities(self.data.active_abilities.get(str(meta.get("job_id")), []), int(meta.get("job_level", 0))):
            effects = list(ability.get("effects") or [])
            if any(effect.get("type") == "revive" for effect in effects):
                continue
            resource = ability_resource(ability, job)
            cost = ability_cost(ability)
            current = int(meta.get(resource, 0)); maximum = max(0, int(meta.get(f"max_{resource}", 0)))
            if current < cost or (resource == "mp" and has_status(meta.get("statuses", {}), "silence")):
                continue
            score = 0.0
            urgent = False
            for effect in effects:
                etype = str(effect.get("type") or "")
                if etype == "heal_hp":
                    if hp_ratio <= 0.30: score += 120; urgent = True
                    elif hp_ratio <= 0.45: score += 92; urgent = True
                    elif hp_ratio <= 0.62: score += 52
                    else: score -= 20
                elif etype == "cleanse":
                    if harmful: score += 105; urgent = True
                    else: score -= 25
                elif etype == "damage":
                    power = float(effect.get("power", 1.0) or 1.0)
                    score += 22 + power * 14
                    element = effect.get("element")
                    if element and monster.get("weakness") and str(element).lower() == str(monster.get("weakness")).lower():
                        score += 38
                elif etype == "drain":
                    score += 28 if hp_ratio <= 0.60 else 8
                    urgent = urgent or hp_ratio <= 0.35
                elif etype in {"restore_mp", "restore_ap"}:
                    key = "mp" if etype == "restore_mp" else "ap"
                    pool_max = max(1, int(meta.get(f"max_{key}", 0)))
                    ratio = int(meta.get(key, 0)) / pool_max
                    score += 58 if ratio <= 0.20 else 14
                elif etype == "status":
                    status_id = str(effect.get("status") or "")
                    recipient = str(effect.get("recipient") or ability.get("target") or "")
                    if status_id in {"protect", "regen", "evade"} and recipient in {"self", "ally", "party"}:
                        if not has_status(meta.get("statuses", {}), status_id):
                            score += 62 if hp_ratio <= 0.55 else 28
                            urgent = urgent or hp_ratio <= 0.30
                    elif status_id in {"power_up", "focus", "haste"} and recipient in {"self", "ally", "party"}:
                        if not has_status(meta.get("statuses", {}), status_id): score += 22
                    elif ability.get("target") == "enemy" and not has_status(monster_statuses, status_id):
                        score += 24 if status_id in {"weaken", "vulnerable", "poison", "slow"} else 16
                        if status_id == "stun": score += 10
            if urgent_only and not urgent:
                continue
            if maximum > 0:
                remaining_ratio = (current - cost) / maximum
                if not urgent and remaining_ratio < 0.18:
                    score -= 55
                elif remaining_ratio < 0.32:
                    score -= 18
                score -= (cost / maximum) * 14
            if score > best[1]:
                target_mode = str(ability.get("target") or "enemy")
                target_id = "monster" if target_mode == "enemy" else "party" if target_mode == "party" else str(twitch_id)
                best = ({"kind": "ability", "ability_id": str(ability["id"]), "target_id": target_id, "auto": True}, score)
        return best

    def _hunt_survival_item_action(self, twitch_id: str, meta: dict[str, Any], rank: str) -> dict[str, Any] | None:
        if int(meta.get("items_used", 0)) >= int(HUNT_AUTO_ITEM_CAP.get(rank, 1)):
            return None
        rows = self.db.all("SELECT item_id,quantity FROM inventory WHERE player_id=? AND quantity>0", (str(twitch_id),))
        owned = {str(row["item_id"]): int(row["quantity"] or 0) for row in rows}
        hp = int(meta.get("hp", 0)); max_hp = max(1, int(meta.get("max_hp", 1))); hp_ratio = hp / max_hp
        harmful = self._hunt_harmful_statuses(meta)

        # Prefer cheap, specific cleanses over rare universal remedies.
        if harmful:
            cleanse_candidates: list[tuple[int, str]] = []
            for item_id, qty in owned.items():
                item = self.data.items.get(item_id) or {}; use = item.get("use") or {}
                if item_id == "tent" or str(use.get("target", "ally")) not in {"ally", "self"}: continue
                for effect in use.get("effects", []):
                    if effect.get("type") != "cleanse": continue
                    allowed = set(effect.get("statuses", []))
                    covers = bool(effect.get("all_harmful")) or bool(harmful & allowed)
                    if covers:
                        rarity_cost = {"common": 0, "uncommon": 1, "rare": 3, "epic": 5}.get(str(item.get("rarity", "common")).lower(), 6)
                        specificity = 0 if allowed else 4
                        cleanse_candidates.append((rarity_cost + specificity, item_id))
            if cleanse_candidates:
                _, item_id = min(cleanse_candidates)
                return {"kind": "item", "item_id": item_id, "target_id": str(twitch_id), "auto": True}

        if hp_ratio <= 0.30:
            need = max(1, int(max_hp * 0.68) - hp)
            heals: list[tuple[int, int, str]] = []
            for item_id, qty in owned.items():
                item = self.data.items.get(item_id) or {}; use = item.get("use") or {}
                if item_id in {"tent", "elixir", "megalixir"} or str(use.get("target", "ally")) not in {"ally", "self"}: continue
                for effect in use.get("effects", []):
                    if effect.get("type") != "heal_hp": continue
                    amount = int(effect.get("amount", 0) or 0)
                    if effect.get("fraction") is not None: amount = max(amount, int(max_hp * float(effect.get("fraction", 0))))
                    if amount > 0:
                        waste = abs(amount - need) if amount >= need else (need - amount) * 2
                        rarity_cost = {"common": 0, "uncommon": 40, "rare": 100}.get(str(item.get("rarity", "common")).lower(), 180)
                        heals.append((waste + rarity_cost, amount, item_id))
            if heals:
                _, _, item_id = min(heals)
                return {"kind": "item", "item_id": item_id, "target_id": str(twitch_id), "auto": True}
            if rank in {"S", "S+"} and hp_ratio <= 0.15:
                for item_id in ("elixir",):
                    if owned.get(item_id, 0) > 0:
                        return {"kind": "item", "item_id": item_id, "target_id": str(twitch_id), "auto": True}

        # Resource recovery is deliberately conservative: only basic restoration
        # items at <=10% pool, and only when the hero is not already in HP danger.
        if hp_ratio > 0.42:
            for resource, basic_ids in (("mp", ("ether", "hi_ether")), ("ap", ("stamina_draught", "warriors_tonic"))):
                maximum = int(meta.get(f"max_{resource}", 0)); current = int(meta.get(resource, 0))
                if maximum <= 0 or current / max(1, maximum) > 0.10: continue
                choices = basic_ids if rank in {"A", "S", "S+"} else basic_ids[:1]
                for item_id in choices:
                    if owned.get(item_id, 0) > 0:
                        return {"kind": "item", "item_id": item_id, "target_id": str(twitch_id), "auto": True}
        return None

    def _hunt_auto_action(self, twitch_id: str, meta: dict[str, Any], monster: dict[str, Any], rank: str) -> dict[str, Any]:
        hp_ratio = int(meta.get("hp", 0)) / max(1, int(meta.get("max_hp", 1)))
        urgent_ability, urgent_score = self._hunt_best_ability_action(twitch_id, meta, monster, urgent_only=True)
        if urgent_ability and urgent_score >= 70:
            return urgent_ability
        item_action = self._hunt_survival_item_action(twitch_id, meta, rank)
        if item_action:
            return item_action
        best_ability, score = self._hunt_best_ability_action(twitch_id, meta, monster, urgent_only=False)
        if best_ability and score >= 30:
            return best_ability
        resource_ratios = []
        for resource in ("mp", "ap"):
            maximum = int(meta.get(f"max_{resource}", 0))
            if maximum > 0: resource_ratios.append(int(meta.get(resource, 0)) / maximum)
        if hp_ratio <= 0.26 or (resource_ratios and max(resource_ratios) <= 0.12):
            return {"kind": "defend", "auto": True}
        return {"kind": "attack", "auto": True}

    @_state_guard
    def resolve_hunt(self, twitch_id: str, hunt_run_id: int | None = None, *, force: bool = False) -> GameResult:
        """Resolve one expired timed Hunt in a single autonomous simulation pass."""
        twitch_id = str(twitch_id)
        assignment = self.active_hunts.get(twitch_id)
        if not assignment:
            return GameResult.fail("That Hunt assignment is no longer active.")
        portal_origin = bool(assignment.get("portal_origin"))
        title_before = {
            str(row["title_id"])
            for row in self.db.all("SELECT title_id FROM player_titles WHERE player_id=?", (twitch_id,))
        } if portal_origin else set()
        if hunt_run_id is not None and int(assignment.get("id") or 0) != int(hunt_run_id):
            return GameResult.fail("That Hunt assignment has already been replaced or completed.")
        now = time.time()
        resolves_at = float(assignment.get("resolves_at") or 0)
        if not force and now < resolves_at:
            return GameResult.fail(f"That Hunt returns in {self._format_seconds(max(0, int(resolves_at - now)))}.")

        old_encounter, old_roster = self.active_encounter, self.encounter_roster
        old_history = self._last_battle_history
        result: GameResult | None = None
        try:
            self.active_encounter = copy.deepcopy(assignment.get("encounter") or {})
            self.encounter_roster = copy.deepcopy(assignment.get("roster") or {})
            if not self.active_encounter or twitch_id not in self.encounter_roster:
                raise ValueError("timed Hunt combat snapshot is incomplete")
            encounter_id = int(self.active_encounter["id"])
            monster = self.data.monsters[self.active_encounter["monster_id"]]
            hunt = self.data.hunts[self.active_encounter["hunt_id"]]
            rank = str(hunt.get("rank", "C")).upper()
            safety = max(1, int(self.active_encounter.get("max_rounds", active_hunt_round_limit(rank))))
            last_meta: dict[str, Any] | None = None
            for _ in range(safety + 1):
                if not self.active_encounter:
                    break
                meta = self.encounter_roster.get(twitch_id)
                if not meta or int(meta.get("hp", 0)) <= 0:
                    result = self._finish_active_encounter(False, reason=f"{monster['name']} defeats the hunter.")
                    break
                last_meta = meta
                meta["action"] = self._hunt_auto_action(twitch_id, meta, monster, rank)
                result = self.advance_encounter_round(encounter_id)
                if result.data.get("hunt_finished"):
                    break
            if self.active_encounter:
                result = self._finish_active_encounter(False, reason="The Hunt reaches its combat safety limit.")
            if result is None:
                result = GameResult.fail("The Hunt could not be resolved.")
            self.active_hunts.pop(twitch_id, None)
            # Add one concise auto-combat usage recap; do not replay every round
            # into Twitch chat after a five-minute-to-two-hour assignment.
            if result.ok:
                recap = self._last_battle_history or {}
                history = list(recap.get("history") or [])
                # Metrics were persisted by _finish_active_encounter; derive a
                # lightweight human summary from the snapshotted roster before it
                # is discarded when possible.
                final_meta = last_meta
                if final_meta:
                    auto_plan = {
                        "abilities": int(final_meta.get("abilities_used", 0)),
                        "items": int(final_meta.get("items_used", 0)),
                        "defends": int(final_meta.get("defends", 0)),
                    }
                    result.messages.append(
                        f"AUTO PLAN — {auto_plan['abilities']} abilities · {auto_plan['items']} items · {auto_plan['defends']} defends."
                    )
                    if isinstance(self._last_battle_history, dict):
                        hunt_summary = (self._last_battle_history.get("hunt_results") or {}).get(str(twitch_id))
                        if isinstance(hunt_summary, dict):
                            hunt_summary["auto_plan"] = auto_plan
                            hunt_summary["duration_seconds"] = max(0, int(assignment.get("resolves_at") or now) - int(assignment.get("started_at") or now))
                if isinstance(self._last_battle_history, dict):
                    hunt_summary = (self._last_battle_history.get("hunt_results") or {}).get(str(twitch_id))
                    if isinstance(hunt_summary, dict):
                        # Timed Hunt results are useful Portal history regardless
                        # of whether the Hunt was accepted in chat or the Portal.
                        # Portal-origin only affects Twitch announcement policy.
                        self._remember_portal_hunt_result(
                            twitch_id,
                            hunt_summary,
                            list(result.messages or []),
                            source_action_id=str(assignment.get("portal_action_id") or ""),
                        )
                result.data.update({
                    "timed_hunt": True,
                    "hunt_run_id": int(assignment.get("id") or 0),
                    "resolved_at": int(now),
                    "portal_origin": portal_origin,
                })
                if portal_origin:
                    title_after = {
                        str(row["title_id"])
                        for row in self.db.all("SELECT title_id FROM player_titles WHERE player_id=?", (twitch_id,))
                    }
                    added_titles = sorted(title_after - title_before)
                    if added_titles:
                        player = self._player(twitch_id)
                        display_name = str(player["display_name"] or player["username"]) if player else "Adventurer"
                        for title_id in added_titles:
                            title_name = str((self.data.titles.get(title_id) or {}).get("name") or title_id.replace("_", " ").title())
                            result.messages.append(f"TITLE UNLOCKED — {display_name} earned {title_name}!")
            return result
        finally:
            # Preserve any simultaneously running Rally Venture / raid-facing
            # encounter state. If a shared encounter was active, its recap also
            # remains the relevant !battlelog view.
            if old_encounter:
                self._last_battle_history = old_history
            self.active_encounter, self.encounter_roster = old_encounter, old_roster

    def _award_hunt_victory(self, player_id: str, p: Any, hunt: dict[str, Any], monster: dict[str, Any]) -> dict[str, Any]:
        reward = hunt["rewards"]
        prior = self.db.one("SELECT clears FROM player_hunts WHERE player_id=? AND hunt_id=?", (player_id, hunt["id"]))
        first_clear = not prior or prior["clears"] == 0
        xp, jp, gil = hunt_repeat_rewards(
            reward["xp"], reward["jp"], reward["gil"], first_clear=first_clear
        )
        jp = self.fellowship_system.apply_jp_bonus(jp)
        seals = reward["seals"]
        job = self.data.jobs[p["current_job"]]
        effects = self._effects(player_id, p["current_job"])
        gil = int(gil * (1 + job.get("gil_bonus", 0) + effects.get("gil_bonus", 0)))
        loot_bonus = job.get("loot_bonus", 0) + effects.get("loot_bonus", 0)
        with self.db.tx() as conn:
            conn.execute("UPDATE players SET xp=xp+?, gil=gil+?, hunt_seals=hunt_seals+?, monsters_defeated=monsters_defeated+1 WHERE twitch_id=?", (xp, gil, seals, player_id))
            conn.execute("UPDATE player_jobs SET jp=jp+? WHERE player_id=? AND job_id=?", (jp, player_id, p["current_job"]))
            conn.execute("INSERT INTO bestiary(player_id,monster_id,defeats) VALUES (?,?,1) ON CONFLICT(player_id,monster_id) DO UPDATE SET defeats=defeats+1", (player_id, monster["id"]))
            conn.execute("INSERT INTO player_hunts(player_id,hunt_id,clears,first_cleared_at,last_cleared_at) VALUES (?,?,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP) ON CONFLICT(player_id,hunt_id) DO UPDATE SET clears=clears+1,last_cleared_at=CURRENT_TIMESTAMP", (player_id, hunt["id"]))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,?)", (player_id, gil, f"hunt:{hunt['id']}"))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'hunt_seals','hunt_seals',?,?)", (player_id, seals, f"hunt:{hunt['id']}"))
        loot: list[str] = []
        for drop in monster.get("drops", []):
            chance = min(0.95, drop["chance"] * (1 + loot_bonus))
            if self.rng.random() <= chance:
                qty = self.rng.randint(drop.get("min", 1), drop.get("max", 1))
                self._change_item(player_id, drop["item_id"], qty, f"hunt_drop:{hunt['id']}")
                loot.append(f"{self.data.items[drop['item_id']]['name']} x{qty}")
        loot.extend(self._roll_pity_drops(player_id, monster, source=f"hunt:{hunt['id']}", loot_bonus=loot_bonus))
        loot.extend(self._roll_recipe_drops(player_id, monster, source=f"hunt:{hunt['id']}", loot_bonus=loot_bonus))
        first_rewards: list[str] = []
        if first_clear:
            item_id = hunt.get("first_clear_item")
            if item_id:
                self._change_item(player_id, item_id, 1, f"hunt_first:{hunt['id']}")
                first_rewards.append(self.data.items[item_id]["name"])
            recipe_id = hunt.get("first_clear_recipe")
            if recipe_id and self._unlock_recipe(player_id, recipe_id):
                first_rewards.append(f"Recipe: {self.data.recipes[recipe_id]['name']}")
            title_id = hunt.get("first_clear_title")
            if title_id and self._unlock_title(player_id, title_id):
                first_rewards.append(f"Title: {self.data.titles[title_id]['name']}")
        levelups = self._process_levels(player_id, p["current_job"])
        return {"xp": xp, "jp": jp, "gil": gil, "seals": seals, "loot": loot, "first_clear": first_clear, "first_rewards": first_rewards, "levelups": levelups}

    def quests(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        parts = []
        for quest in self.data.quests.values():
            done = self.db.one("SELECT 1 FROM player_quests WHERE player_id=? AND quest_id=?", (twitch_id, quest["id"]))
            if done:
                state = "DONE"
            else:
                state = "READY" if self._requirements_met(twitch_id, quest["requirements"])[0] else "IN PROGRESS"
            reward_job = self.data.jobs[quest["rewards"]["job"]]["name"]
            parts.append(f"{quest['name']} [{state}→{reward_job}]")
        messages = ["Job Quests — " + " | ".join(parts[:5])]
        if len(parts) > 5:
            messages.append("More Job Quests — " + " | ".join(parts[5:]))
        companion_done = self._chocobo_quest_done(twitch_id)
        companion_ready = self._requirements_met(twitch_id, CHOCOBO_QUEST_REQUIREMENTS)[0]
        companion_state = "DONE" if companion_done else "READY" if companion_ready else "IN PROGRESS"
        messages.append(f"Companion Quest — {CHOCOBO_QUEST_NAME} [{companion_state}] · use !chocoboquest")
        messages.append("Inspect/claim Job quests with !quest <name>.")
        return GameResult.success(*messages)

    def quest(self, twitch_id: str, quest_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        quest = self._find_by_name_or_id(self.data.quests, quest_query)
        if not quest:
            return GameResult.fail("Quest not found. Use !quests to see Job quests.")
        if self.db.one("SELECT 1 FROM player_quests WHERE player_id=? AND quest_id=?", (twitch_id, quest["id"])):
            return GameResult.success(f"{quest['name']} is already complete. The paperwork, tragically, remains filed.")
        met, missing = self._requirements_met(twitch_id, quest["requirements"])
        if not met:
            return GameResult.fail(f"{quest['name']} — {quest['description']} | Still needed: " + "; ".join(missing[:6]))
        rewards = quest["rewards"]
        gil = rewards.get("gil", 0)
        with self.db.tx() as conn:
            conn.execute("INSERT INTO player_quests(player_id,quest_id) VALUES (?,?)", (twitch_id, quest["id"]))
            if gil:
                conn.execute("UPDATE players SET gil=gil+? WHERE twitch_id=?", (gil, twitch_id))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,?)", (twitch_id, gil, f"quest:{quest['id']}"))
        title_id = rewards.get("title")
        title_text = ""
        if title_id and self._unlock_title(twitch_id, title_id):
            title_text = f" | Title: {self.data.titles[title_id]['name']}"
        job_name = self.data.jobs[rewards["job"]]["name"]
        unlocked = self._check_achievements(twitch_id)
        suffix = (" | Achievement: " + " | ".join(unlocked)) if unlocked else ""
        return GameResult.success(f"QUEST COMPLETE — {quest['name']} | {job_name} is now eligible via !job {rewards['job']} | +{gil:,} gil{title_text}{suffix}")

    # ---------- titles ----------
    def titles(self, twitch_id: str, filter_query: str | None = None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        self._check_achievements(twitch_id)
        self._ensure_base_title(twitch_id)
        rows = self.db.all(
            "SELECT title_id, unlocked_at FROM player_titles WHERE player_id=? ORDER BY unlocked_at DESC",
            (twitch_id,),
        )
        unlocked = [self.data.titles[r["title_id"]] for r in rows if r["title_id"] in self.data.titles]
        query = (filter_query or "").strip().lower()
        if query and query not in {"all", "earned"}:
            unlocked = [
                title for title in unlocked
                if query in title.get("category", "").lower()
                or query in title.get("rarity", "").lower()
                or query in title["name"].lower()
            ]
        shown = unlocked[:8]
        entries = [f"{t['name']} [{t.get('rarity','common').title()}]" for t in shown]
        suffix = " | ..." if len(unlocked) > len(shown) else ""
        return GameResult.success(
            f"Titles — Equipped: {p['title']} | Unlocked {len(rows)}/{len(self.data.titles)}",
            (" | ".join(entries) + suffix) if entries else "No unlocked titles match that filter.",
            "Filter with !titles <category|rarity>. Equip with !title <name>.",
        )

    def set_title(self, twitch_id: str, title_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        title = self._find_by_name_or_id(self.data.titles, title_query)
        if not title:
            return GameResult.fail("Title not found. Use !titles to see unlocked titles.")
        if not self.db.one("SELECT 1 FROM player_titles WHERE player_id=? AND title_id=?", (twitch_id, title["id"])):
            return GameResult.fail(f"You haven't unlocked {title['name']} yet.")
        self.db.execute("UPDATE players SET title=? WHERE twitch_id=?", (title["name"], twitch_id))
        return GameResult.success(f"Title equipped: {title['name']} — {title['description']}")

    # ---------- inventory/equipment/shop ----------
    def inventory(self, twitch_id: str, category: str | None = None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        aliases = {"weapons": "weapon", "armors": "armor", "accessories": "accessory", "consumables": "consumable", "materials": "material", "gear": "equipment", "equipment": "equipment"}
        selected = self._norm(category) if category else "all"
        selected = aliases.get(selected, selected)
        valid = {"all", "weapon", "armor", "accessory", "consumable", "material", "equipment"}
        if selected not in valid:
            return GameResult.fail("Inventory filter must be weapon, armor, accessory, consumable, material, equipment, or all.")
        rows = self.db.all("SELECT item_id, quantity FROM inventory WHERE player_id=? AND quantity>0 ORDER BY item_id", (twitch_id,))
        filtered = []
        for row in rows:
            item = self.data.items.get(row["item_id"])
            if not item:
                continue
            item_type = item.get("type")
            if selected == "equipment" and item_type not in {"weapon", "armor", "accessory"}:
                continue
            if selected not in {"all", "equipment"} and item_type != selected:
                continue
            filtered.append((item, int(row["quantity"])))
        label = "All" if selected == "all" else ("Equipment" if selected == "equipment" else selected.title())
        if not filtered:
            return GameResult.success(f"Inventory [{label}] — nothing here. The Moogle has prepared a very small clipboard.")
        entries = [f"{item['name']} x{qty}" for item, qty in filtered]
        total_qty = sum(qty for _, qty in filtered)
        messages = [f"Inventory [{label}] — {len(filtered)} unique / {total_qty} total: " + " | ".join(entries[:12]) + (" | ..." if len(entries) > 12 else "")]
        if selected == "all" and len(entries) > 12:
            messages.append("Filter with !inventory weapon | armor | accessory | consumable | material | equipment.")
        return GameResult.success(*messages)

    def gear(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        eq = self.db.one("SELECT * FROM equipment WHERE player_id=?", (twitch_id,))
        def label(item_id: str | None) -> str:
            if not item_id:
                return "—"
            lvl = self._upgrade_level(twitch_id, item_id)
            suffix = f" +{lvl}" if lvl else ""
            item = self.data.item(item_id)
            inactive = ""
            if item and item.get("allowed_jobs") and p["current_job"] not in item["allowed_jobs"]:
                inactive = " [inactive for current Job]"
            return f"{self._item_name(item_id)}{suffix}{inactive}"
        messages = [f"Gear — Weapon: {label(eq['weapon_id'])} | Armor: {label(eq['armor_id'])} | Accessory: {label(eq['accessory_id'])}"]
        job = self.data.jobs.get(p["current_job"])
        if job:
            stats = self._stats(p, job)
            messages.append(f"Active Stats — STR {stats['str']} | VIT {stats['vit']} | MAG {stats['mag']} | SPR {stats['spr']} | DEX {stats['dex']} | LCK {stats['lck']} | HP {stats['hp']}")
        messages.append("Equip with !equip <item>. Inspect gear with !item <name>. Filter owned gear with !inventory equipment.")
        return GameResult.success(*messages)

    def equip(self, twitch_id: str, item_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before changing equipment.")
        if self._expedition_load(twitch_id):
            return GameResult.fail("Return from your Expedition before changing equipment.")
        if str(twitch_id) in self.active_hunts:
            return GameResult.fail("Equipment is locked while your hero is away on a Hunt.")
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("You cannot change equipment after committing to an active encounter or raid.")
        item = self._find_by_name_or_id(self.data.items, item_query)
        if not item or item["type"] not in {"weapon", "armor", "accessory"}:
            return GameResult.fail("That isn't equippable gear.")
        if self._inventory_qty(twitch_id, item["id"]) <= 0:
            return GameResult.fail(f"You don't own {item['name']}.")
        min_level = int(item.get("min_level", 1) or 1)
        if int(p["level"]) < min_level:
            return GameResult.fail(f"{item['name']} requires Lv.{min_level}.")
        allowed = item.get("allowed_jobs")
        if allowed and p["current_job"] not in allowed:
            names = ", ".join(self.data.jobs[j]["name"] for j in allowed if j in self.data.jobs)
            return GameResult.fail(f"{item['name']} can only be wielded by: {names}.")
        column = {"weapon": "weapon_id", "armor": "armor_id", "accessory": "accessory_id"}[item["type"]]
        current = self.db.one(f"SELECT {column} AS item_id FROM equipment WHERE player_id=?", (twitch_id,))
        if current and current["item_id"] == item["id"]:
            level = self._upgrade_level(twitch_id, item["id"])
            suffix = f" +{level}" if level else ""
            return GameResult.success(f"{item['name']}{suffix} is already equipped as {item['type']}.", slot=item["type"], item_id=item["id"], changed=False)
        self.db.execute(f"UPDATE equipment SET {column}=? WHERE player_id=?", (item["id"], twitch_id))
        self._normalize_after_equipment_change(twitch_id)
        level = self._upgrade_level(twitch_id, item["id"])
        suffix = f" +{level}" if level else ""
        return GameResult.success(f"Equipped {item['name']}{suffix} as {item['type']}.", slot=item["type"], item_id=item["id"], changed=True)

    def unequip(self, twitch_id: str, slot: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before changing equipment.")
        if self._expedition_load(twitch_id):
            return GameResult.fail("Return from your Expedition before changing equipment.")
        if str(twitch_id) in self.active_hunts:
            return GameResult.fail("Equipment is locked while your hero is away on a Hunt.")
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("You cannot change equipment after committing to an active encounter or raid.")
        normalized = self._norm(slot)
        aliases = {"weapon": "weapon", "armor": "armor", "armour": "armor", "accessory": "accessory"}
        slot_id = aliases.get(normalized)
        if not slot_id:
            return GameResult.fail("Choose weapon, armor, or accessory to unequip.")
        column = {"weapon": "weapon_id", "armor": "armor_id", "accessory": "accessory_id"}[slot_id]
        current = self.db.one(f"SELECT {column} AS item_id FROM equipment WHERE player_id=?", (twitch_id,))
        if not current or not current["item_id"]:
            return GameResult.success(f"Your {slot_id} slot is already empty.", slot=slot_id, item_id=None, changed=False)
        item_id = str(current["item_id"])
        item = self.data.item(item_id)
        item_name = item["name"] if item else item_id
        self.db.execute(f"UPDATE equipment SET {column}=NULL WHERE player_id=?", (twitch_id,))
        self._normalize_after_equipment_change(twitch_id)
        return GameResult.success(f"Unequipped {item_name} from {slot_id}.", slot=slot_id, item_id=item_id, changed=True)

    def _normalize_after_equipment_change(self, twitch_id: str) -> None:
        """Clamp persistent vitals after an equipment swap changes maximum pools."""
        p = self._player(twitch_id)
        if not p:
            return
        job = self.data.jobs.get(p["current_job"])
        if not job:
            self.db.execute("UPDATE players SET updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (twitch_id,))
            return
        stats = self._stats(p, job)
        pools = battle_resource_pools(stats, job)
        max_hp = int(stats["hp"])
        max_mp = int(pools["max_mp"])
        max_ap = int(pools["max_ap"])
        current_hp = max(0, min(max_hp, int(p["current_hp"] or 0)))
        raw_mp = p["current_mp"]
        raw_ap = p["current_ap"]
        current_mp = None if raw_mp is None and max_mp <= 0 else max(0, min(max_mp, max_mp if raw_mp is None else int(raw_mp)))
        current_ap = None if raw_ap is None and max_ap <= 0 else max(0, min(max_ap, max_ap if raw_ap is None else int(raw_ap)))
        self.db.execute(
            "UPDATE players SET current_hp=?, current_mp=?, current_ap=?, updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
            (current_hp, current_mp, current_ap, twitch_id),
        )

    def _weighted_shop_sample(self, candidates: list[dict[str, Any]], count: int, player_level: int, job_id: str) -> list[dict[str, Any]]:
        """Select unique shop items while favoring current-Job and near-level gear."""
        pool = list(candidates)
        chosen: list[dict[str, Any]] = []
        rarity_weight = {
            "common": 1.0,
            "uncommon": 1.05,
            "rare": 0.95,
            "epic": 0.70,
            "relic": 0.25,
            "artifact": 0.12,
            "legendary": 0.05,
        }
        while pool and len(chosen) < count:
            weights: list[float] = []
            for item in pool:
                item_level = max(int(item.get("shop_level", 1)), int(item.get("min_level", 1)))
                distance = max(0, player_level - item_level)
                level_weight = max(0.18, 1.9 - (distance / 18.0))
                allowed = item.get("allowed_jobs") or []
                job_weight = 4.0 if allowed and job_id in allowed else 1.0
                weights.append(level_weight * job_weight * rarity_weight.get(item.get("rarity", "common"), 0.8))
            pick = self.rng.choices(pool, weights=weights, k=1)[0]
            chosen.append(pick)
            pool.remove(pick)
        return chosen

    def _roll_shop_stock(self, p: Any) -> list[str]:
        """Build one personalized Moogle Emporium rotation for a player."""
        job_id = p["current_job"]
        level = int(p["level"])
        eligible: list[dict[str, Any]] = []
        for item in self.data.items.values():
            if not item.get("shop"):
                continue
            if level < int(item.get("shop_level", 1)) or level < int(item.get("min_level", 1)):
                continue
            allowed = item.get("allowed_jobs")
            if allowed and job_id not in allowed:
                continue
            eligible.append(item)

        # Adventurers who have not chosen a Job only see supplies/general goods.
        if job_id == "adventurer":
            eligible = [i for i in eligible if i["type"] in {"consumable", "accessory"} and not i.get("allowed_jobs")]

        by_type = {
            kind: [i for i in eligible if i["type"] == kind]
            for kind in ("weapon", "armor", "accessory", "consumable")
        }
        stock: list[dict[str, Any]] = []

        # Core composition: class gear first, then recovery/support supplies.
        for kind, count in (("weapon", 3), ("armor", 2), ("accessory", 1), ("consumable", 3)):
            remaining = [i for i in by_type[kind] if i not in stock]
            stock.extend(self._weighted_shop_sample(remaining, count, level, job_id))

        # Fill any empty slots from other eligible goods without duplicates.
        if len(stock) < 9:
            remaining = [i for i in eligible if i not in stock]
            stock.extend(self._weighted_shop_sample(remaining, 9 - len(stock), level, job_id))

        return [item["id"] for item in stock[:9]]

    def _shop_stock(self, twitch_id: str, force_refresh: bool = False) -> tuple[list[dict[str, Any]], int]:
        p = self._player(twitch_id)
        if not p:
            return [], 0
        now = int(time.time())
        row = self.db.one("SELECT * FROM player_shops WHERE player_id=?", (twitch_id,))
        valid = False
        ids: list[str] = []
        if row and not force_refresh:
            try:
                ids = list(json.loads(row["stock_json"]))
            except (TypeError, ValueError, json.JSONDecodeError):
                ids = []
            valid = (
                int(row["expires_at"]) > now
                and row["job_id"] == p["current_job"]
                and int(row["level_at_roll"]) == int(p["level"])
                and ids
                and all(item_id in self.data.items for item_id in ids)
            )
        if not valid:
            ids = self._roll_shop_stock(p)
            expires = now + self.fellowship_system.effective_shop_refresh_seconds(self.shop_refresh_seconds)
            self.db.execute(
                "INSERT INTO player_shops(player_id,job_id,level_at_roll,stock_json,generated_at,expires_at) "
                "VALUES (?,?,?,?,?,?) ON CONFLICT(player_id) DO UPDATE SET "
                "job_id=excluded.job_id, level_at_roll=excluded.level_at_roll, stock_json=excluded.stock_json, "
                "generated_at=excluded.generated_at, expires_at=excluded.expires_at",
                (twitch_id, p["current_job"], int(p["level"]), json.dumps(ids), now, expires),
            )
        else:
            expires = int(row["expires_at"])
        return [self.data.items[item_id] for item_id in ids if item_id in self.data.items], expires

    def _find_shop_offer(self, twitch_id: str, query: str) -> tuple[dict[str, Any] | None, int]:
        stock, expires = self._shop_stock(twitch_id)
        clean = query.strip()
        if clean.isdigit():
            slot = int(clean)
            return (stock[slot - 1] if 1 <= slot <= len(stock) else None), expires
        q = clean.lower().replace("_", " ")
        for item in stock:
            if item["id"].lower() == clean.lower() or item["name"].lower() == clean.lower() or item["name"].lower().replace("-", " ") == q:
                return item, expires
        return None, expires

    def shop(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        stock, expires = self._shop_stock(twitch_id)
        if not stock:
            return GameResult.fail("The Moogle Emporium has somehow run out of merchandise. This is deeply un-Moogle-like.")
        job = self.data.jobs.get(p["current_job"], {"name": "Adventurer"})["name"]
        remaining = max(0, expires - int(time.time()))
        groups: dict[str, list[str]] = {"weapon": [], "armor": [], "accessory": [], "consumable": []}
        for slot, item in enumerate(stock, start=1):
            groups.setdefault(item["type"], []).append(f"#{slot} {item['name']} {item['price']:,}g")
        messages = [f"Moogle Emporium — {job} stock for Lv.{p['level']} | refresh {self._format_seconds(remaining)} | Buy with !buy <# or item> [qty]"]
        gear_parts: list[str] = []
        if groups["weapon"]:
            gear_parts.append("Weapons — " + " | ".join(groups["weapon"]))
        if groups["armor"]:
            gear_parts.append("Armor — " + " | ".join(groups["armor"]))
        if gear_parts:
            messages.append(" | ".join(gear_parts))
        tail: list[str] = []
        if groups["accessory"]:
            tail.append("Accessories — " + " | ".join(groups["accessory"]))
        if groups["consumable"]:
            tail.append("Supplies — " + " | ".join(groups["consumable"]))
        if tail:
            messages.append(" | ".join(tail))
        return GameResult.success(*messages, stock=[i["id"] for i in stock], expires_at=expires)

    def buy(self, twitch_id: str, item_query: str, quantity: int = 1) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before shopping for new supplies.")
        if quantity < 1 or quantity > 99:
            return GameResult.fail("Quantity must be between 1 and 99.")
        item, _ = self._find_shop_offer(twitch_id, item_query)
        if not item:
            return GameResult.fail("That item is not in your current Moogle Emporium stock. Use !shop to see today's questionable business decisions.")
        if item["type"] in {"weapon", "armor", "accessory"} and quantity != 1:
            return GameResult.fail("Equipment is sold one at a time. The Moogle refuses to explain the inventory policy.")
        cost = int(item["price"]) * quantity
        if p["gil"] < cost:
            return GameResult.fail(f"You need {cost:,} gil, but only have {p['gil']:,}. Kupo-poor.")
        with self.db.tx() as conn:
            conn.execute("UPDATE players SET gil=gil-? WHERE twitch_id=?", (cost, twitch_id))
            conn.execute("INSERT INTO inventory(player_id, item_id, quantity) VALUES (?, ?, ?) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (twitch_id, item["id"], quantity))
            conn.execute("INSERT INTO transactions(player_id, kind, asset_id, amount, source) VALUES (?, 'gil', 'gil', ?, 'shop')", (twitch_id, -cost))
            conn.execute("INSERT INTO transactions(player_id, kind, asset_id, amount, source) VALUES (?, 'item', ?, ?, 'shop')", (twitch_id, item["id"], quantity))
        result = GameResult.success(f"Purchased {item['name']} x{quantity} for {cost:,} gil from your current shop rotation.")
        unlocked = self._check_achievements(twitch_id)
        if unlocked:
            result.messages.append("Achievement unlocked: " + " | ".join(unlocked))
        return result

    def _portal_character_state_data(self, twitch_id: str) -> dict[str, Any]:
        p = self._player(twitch_id)
        if not p:
            return {}
        rows = self.db.all(
            "SELECT job_id,level,jp FROM player_jobs WHERE player_id=?",
            (twitch_id,),
        )
        owned = {str(row["job_id"]): row for row in rows}
        jobs: list[dict[str, Any]] = []
        for job in self.data.jobs.values():
            row = owned.get(job["id"])
            level = int(row["level"]) if row else 0
            jp = int(row["jp"]) if row else 0
            requirements: list[dict[str, Any]] = []
            for req in job.get("unlock", []):
                value = self._requirement_value(twitch_id, req)
                amount = int(req.get("amount", 1))
                requirements.append({
                    "met": value >= amount,
                    "text": self._requirement_text(req, value),
                })
            unlocked = job.get("tier") == "starter" or all(req["met"] for req in requirements)
            jobs.append({
                "id": job["id"],
                "name": job["name"],
                "tier": job.get("tier", "starter"),
                "owned": row is not None,
                "unlocked": bool(unlocked),
                "current": p["current_job"] == job["id"],
                "level": level,
                "jp": jp,
                "jp_next": jp_to_next(level) if level else 0,
                "mastered": level >= 50,
                "signature": job.get("signature", "—"),
                "resource_mode": job_resource_mode(job),
                "mastery": dict(job.get("mastery", {})),
                "requirements": requirements,
            })

        equipped_rows = self.db.all(
            "SELECT slot,job_id FROM mastery_slots WHERE player_id=? ORDER BY slot",
            (twitch_id,),
        )
        equipped = {int(row["slot"]): str(row["job_id"]) for row in equipped_rows}
        mastery_slots: list[dict[str, Any]] = []
        for slot in (1, 2):
            job_id = equipped.get(slot)
            source = self.data.jobs.get(job_id) if job_id else None
            mastery_slots.append({
                "slot": slot,
                "job_id": job_id,
                "job_name": source.get("name") if source else None,
                "name": source.get("mastery", {}).get("name") if source else None,
                "description": source.get("mastery", {}).get("description") if source else None,
            })

        combat_locked = twitch_id in self.encounter_roster or twitch_id in self.raid_roster
        camp_remaining = self._camp_remaining(twitch_id)
        ko_locked = p["current_job"] != "adventurer" and int(p["current_hp"] or 0) <= 0
        job_reason = ""
        if combat_locked:
            job_reason = "Finish the active encounter or raid before changing Jobs."
        elif camp_remaining > 0:
            job_reason = "Finish resting at camp before changing Jobs."
        elif ko_locked:
            job_reason = "Recover from KO before changing Jobs."
        return {
            "current_job_id": str(p["current_job"]),
            "current_job_name": self.data.jobs.get(p["current_job"], {}).get("name", "Adventurer"),
            "stance": str(p["stance"]),
            "jobs": jobs,
            "mastery_slots": mastery_slots,
            "locks": {
                "combat": bool(combat_locked),
                "resting": camp_remaining > 0,
                "ko": bool(ko_locked),
                "job_change": bool(combat_locked or camp_remaining > 0 or ko_locked),
                "job_change_reason": job_reason,
                "stance_change": bool(combat_locked),
                "mastery_change": bool(combat_locked),
            },
        }

    def _portal_recovery_state_data(self, twitch_id: str) -> dict[str, Any]:
        """Return compact live recovery/inventory state for the authenticated Portal.

        The local engine remains authoritative. Camp uses an absolute completion
        timestamp so the browser can render a one-second countdown without
        polling the server every second. Active Battle statuses are exposed
        read-only; Phase 5 intentionally does not turn the Portal into a combat
        action surface.
        """
        self._finish_rest_if_ready(twitch_id)
        p = self._player(twitch_id)
        if not p:
            return {}
        max_hp = int(self._max_hp(p))
        hp = max(0, min(int(p["current_hp"] or 0), max_hp))
        resources = self._resource_state_for(p)
        mp = int(resources.get("mp", 0))
        max_mp = int(resources.get("max_mp", 0))
        ap = int(resources.get("ap", 0))
        max_ap = int(resources.get("max_ap", 0))
        now = int(time.time())
        camp_until = int(p["camp_until"] or 0)
        camp_remaining = max(0, camp_until - now)
        combat_locked = twitch_id in self.encounter_roster or twitch_id in self.raid_roster
        state = "in_battle" if combat_locked else "resting" if camp_remaining > 0 else "ko" if hp <= 0 else "ready"

        active_statuses: list[dict[str, Any]] = []
        encounter_meta = self.encounter_roster.get(twitch_id) if twitch_id in self.encounter_roster else None
        if isinstance(encounter_meta, dict):
            for status_id, status in (encounter_meta.get("statuses") or {}).items():
                turns = int((status or {}).get("turns", 0))
                if turns > 0:
                    active_statuses.append({
                        "id": str(status_id),
                        "name": STATUS_LABELS.get(str(status_id), str(status_id).replace("_", " ").title()),
                        "turns": turns,
                    })

        inventory = {
            str(row["item_id"]): int(row["quantity"])
            for row in self.db.all("SELECT item_id,quantity FROM inventory WHERE player_id=? AND quantity>0", (twitch_id,))
        }
        items: list[dict[str, Any]] = []
        for item_id, qty in inventory.items():
            item = self.data.items.get(item_id)
            if not item or item.get("type") != "consumable":
                continue
            use = item.get("use") if isinstance(item.get("use"), dict) else {}
            effects = list(use.get("effects") or [])
            field_usable = bool(use.get("field"))
            cleanse_effect = any(effect.get("type") == "cleanse" for effect in effects)
            if not field_usable and not cleanse_effect:
                continue

            usable_now = False
            reason = ""
            preview_parts: list[str] = []
            effective_total = 0
            potential_total = 0

            if combat_locked:
                if cleanse_effect and active_statuses:
                    reason = "Use this during Active Battle from Twitch chat."
                else:
                    reason = "Unavailable while you are in active combat."
            elif not field_usable:
                reason = "Active Battle item."
            else:
                for effect in effects:
                    effect_type = effect.get("type")
                    if effect_type == "heal_hp" and hp > 0:
                        amount = max(0, int(effect.get("amount", 0)))
                        if effect.get("fraction") is not None:
                            amount = max(amount, int(max_hp * float(effect.get("fraction", 0))))
                        effective = min(max(0, max_hp - hp), amount)
                        potential_total += amount
                        effective_total += effective
                        if effective > 0:
                            preview_parts.append(f"+{effective} HP")
                    elif effect_type == "restore_mp" and hp > 0 and max_mp > 0:
                        amount = max(0, int(effect.get("amount", 0)))
                        if effect.get("fraction") is not None:
                            amount = max(amount, int(max_mp * float(effect.get("fraction", 0))))
                        effective = min(max(0, max_mp - mp), amount)
                        potential_total += amount
                        effective_total += effective
                        if effective > 0:
                            preview_parts.append(f"+{effective} MP")
                    elif effect_type == "restore_ap" and hp > 0 and max_ap > 0:
                        amount = max(0, int(effect.get("amount", 0)))
                        if effect.get("fraction") is not None:
                            amount = max(amount, int(max_ap * float(effect.get("fraction", 0))))
                        effective = min(max(0, max_ap - ap), amount)
                        potential_total += amount
                        effective_total += effective
                        if effective > 0:
                            preview_parts.append(f"+{effective} AP")
                    elif effect_type == "revive" and hp <= 0:
                        revived = max(1, int(max_hp * float(effect.get("fraction", 0.30))))
                        potential_total += revived
                        effective_total += revived
                        preview_parts.append(f"Revive at {revived} HP")

                if item_id == "tent":
                    needs_any = hp < max_hp or (max_mp > 0 and mp < max_mp) or (max_ap > 0 and ap < max_ap) or camp_remaining > 0
                    if needs_any:
                        effective_total = max(1, (max_hp - hp) + max(0, max_mp - mp) + max(0, max_ap - ap))
                        potential_total = max_hp + max_mp + max_ap
                        preview_parts = ["Full HP/MP/AP", "Ends Camp"] if camp_remaining > 0 else ["Full HP/MP/AP"]
                usable_now = effective_total > 0
                if not usable_now:
                    effect_types = {str(effect.get("type")) for effect in effects}
                    if hp <= 0 and "revive" not in effect_types and item_id != "tent":
                        reason = "Recover from KO with a Phoenix Down, Tent, or Camp."
                    elif effect_types == {"heal_hp"}:
                        reason = "HP is already full."
                    elif effect_types == {"restore_mp"}:
                        reason = "MP is already full or your current Job does not use MP."
                    elif effect_types == {"restore_ap"}:
                        reason = "AP is already full or your current Job does not use AP."
                    else:
                        reason = "No useful recovery effect right now."

            items.append({
                "id": item_id,
                "name": str(item.get("name", item_id)),
                "rarity": str(item.get("rarity", "common")),
                "quantity": qty,
                "description": str(item.get("description") or ""),
                "field_usable": field_usable,
                "usable_now": usable_now,
                "reason": reason,
                "preview": " · ".join(preview_parts),
                "waste": max(0, potential_total - effective_total),
                "effective": effective_total,
                "confirm": item_id == "tent" or str(item.get("rarity", "common")) in {"epic", "legendary"},
                "combat_only": not field_usable,
            })

        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
        usable_items = [item for item in items if item["usable_now"]]
        recommendation = None
        if usable_items:
            if hp <= 0:
                preferred = next((item for item in usable_items if item["id"] == "phoenix_down"), None)
                preferred = preferred or next((item for item in usable_items if item["id"] == "tent"), None)
                recommendation = preferred or usable_items[0]
            else:
                recommendation = min(
                    usable_items,
                    key=lambda item: (int(item["waste"]), rarity_order.get(str(item["rarity"]), 9), -int(item["effective"])),
                )

        items.sort(key=lambda item: (not item["usable_now"], rarity_order.get(item["rarity"], 9), item["name"].lower()))
        return {
            "state": state,
            "state_label": {"ready": "READY", "resting": "RESTING", "ko": "KO", "in_battle": "IN BATTLE"}[state],
            "hp": {"current": hp, "max": max_hp},
            "mp": {"current": mp, "max": max_mp},
            "ap": {"current": ap, "max": max_ap},
            "camp_until": camp_until if camp_remaining > 0 else 0,
            "camp_remaining": camp_remaining,
            "combat_locked": bool(combat_locked),
            "active_statuses": active_statuses,
            "items": items,
            "recommended_item_id": recommendation["id"] if recommendation else None,
            "recommended_item_name": recommendation["name"] if recommendation else None,
        }

    # ---------- v1.2 Expeditions ----------
    def _expedition_load(self, twitch_id: str) -> dict[str, Any] | None:
        row = self.db.one("SELECT state_json FROM player_expeditions WHERE player_id=?", (str(twitch_id),))
        if not row:
            return None
        try:
            state = json.loads(str(row["state_json"]))
            return state if isinstance(state, dict) else None
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    def _expedition_save(self, twitch_id: str, state: dict[str, Any]) -> None:
        now = int(time.time())
        started = int(state.get("started_at") or now)
        state["updated_at"] = now
        self.db.execute(
            "INSERT INTO player_expeditions(player_id,state_json,started_at,updated_at) VALUES (?,?,?,?) "
            "ON CONFLICT(player_id) DO UPDATE SET state_json=excluded.state_json,updated_at=excluded.updated_at",
            (str(twitch_id), json.dumps(state, separators=(",", ":"), sort_keys=True), started, now),
        )

    def _expedition_delete(self, twitch_id: str) -> None:
        self.db.execute("DELETE FROM player_expeditions WHERE player_id=?", (str(twitch_id),))

    def _expedition_board_ready(self) -> bool:
        row = self.db.one("SELECT expedition_board_complete FROM fellowship_state WHERE singleton_id=1")
        return bool(row and int(row["expedition_board_complete"] or 0))

    def _expedition_chocobo_traits(self, twitch_id: str) -> tuple[dict[str, Any] | None, set[str]]:
        row = self.db.one(
            "SELECT name,level,xp,registered_at,portrait_id FROM player_chocobos WHERE player_id=?",
            (str(twitch_id),),
        )
        if not row or not row["registered_at"] or not row["name"]:
            return None, set()
        traits = {
            str(item["trait_id"])
            for item in self.db.all(
                "SELECT trait_id FROM player_chocobo_traits WHERE player_id=? ORDER BY unlocked_at,trait_id",
                (str(twitch_id),),
            )
            if str(item["trait_id"]) in CHOCOBO_TRAITS
        }
        level, xp_current, xp_next = chocobo_level_from_total_xp(int(row["xp"] or 0))
        payload = {
            "name": str(row["name"]),
            "level": int(level),
            "xp_current": int(xp_current),
            "xp_next": int(xp_next),
            "portrait_id": str(row["portrait_id"] or CHOCOBO_DEFAULT_PORTRAIT_ID),
            "traits": [
                {"id": trait_id, **CHOCOBO_TRAITS[trait_id]}
                for trait_id in sorted(traits)
            ],
        }
        payload["specialization"] = chocobo_expedition_specialization(traits, int(level))
        return payload, traits

    def _expedition_chocobo_level(self, twitch_id: str) -> int:
        chocobo, _ = self._expedition_chocobo_traits(twitch_id)
        return max(1, int((chocobo or {}).get("level", 1) or 1))

    def _expedition_stipend(self, state: dict[str, Any], outcome: str) -> int:
        if str(outcome) != "complete":
            return 0
        if bool(state.get("legendary_contract")):
            return 15
        if bool(state.get("boss_contract")):
            return 10
        return {"scout": 2, "journey": 4, "deep": 7}.get(str(state.get("depth") or ""), 0)

    def _award_expedition_stipend(self, twitch_id: str, state: dict[str, Any], outcome: str) -> int:
        seals = self._expedition_stipend(state, outcome)
        if seals <= 0:
            return 0
        with self.db.tx() as conn:
            conn.execute(
                "UPDATE players SET hunt_seals=hunt_seals+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
                (seals, str(twitch_id)),
            )
            conn.execute(
                "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'hunt_seals','hunt_seals',?,'expedition_stipend')",
                (str(twitch_id), seals),
            )
        return seals

    def _expedition_progress(self, twitch_id: str, region_id: str) -> dict[str, Any]:
        row = self.db.one(
            "SELECT progress,stages_cleared,completed_runs,boss_clears FROM player_region_exploration WHERE player_id=? AND region_id=?",
            (str(twitch_id), str(region_id)),
        )
        progress = max(0, min(100, int(row["progress"] or 0))) if row else 0
        region = self.data.expedition_regions.get(str(region_id)) or {}
        objectives = []
        for objective in region.get("objectives", []):
            threshold = max(1, min(100, int(objective.get("threshold", 100))))
            objectives.append({
                "threshold": threshold,
                "name": str(objective.get("name") or f"{threshold}% Survey"),
                "description": str(objective.get("description") or ""),
                "unlock": str(objective.get("unlock") or ""),
                "complete": progress >= threshold,
            })
        next_objective = next((copy.deepcopy(obj) for obj in objectives if not obj["complete"]), None)
        boss = dict(region.get("boss") or {})
        boss_unlock = int(boss.get("unlock_progress", 75) or 75)
        mastery = dict(region.get("mastery") or {})
        landmarks = []
        for landmark in region.get("landmarks", []):
            unlock_progress = max(0, min(100, int(landmark.get("unlock_progress", 0) or 0)))
            landmarks.append({
                "name": str(landmark.get("name") or "Uncharted Landmark"),
                "description": str(landmark.get("description") or ""),
                "unlock_progress": unlock_progress,
                "discovered": progress >= unlock_progress,
            })
        return {
            "progress": progress,
            "stages_cleared": int(row["stages_cleared"] or 0) if row else 0,
            "completed_runs": int(row["completed_runs"] or 0) if row else 0,
            "boss_clears": int(row["boss_clears"] or 0) if row else 0,
            "boss_unlocked": progress >= boss_unlock,
            "boss_unlock_progress": boss_unlock,
            "mastered": progress >= 100,
            "objectives": objectives,
            "next_objective": next_objective,
            "mastery_bonus": str(mastery.get("bonus") or ""),
            "landmarks": landmarks,
            "landmarks_found": sum(1 for landmark in landmarks if landmark["discovered"]),
        }

    def _expedition_atlas(self, twitch_id: str) -> dict[str, Any]:
        region_ids = list(self.data.expedition_regions)
        progress_rows = [self._expedition_progress(twitch_id, region_id) for region_id in region_ids]
        region_count = max(1, len(progress_rows))
        total_progress = sum(int(row.get("progress", 0)) for row in progress_rows)
        average_progress = int(round(total_progress / region_count))
        regions_mastered = sum(1 for row in progress_rows if bool(row.get("mastered")))
        legendary_unlocked = sum(
            1 for row in progress_rows
            if bool(row.get("mastered")) and int(row.get("boss_clears", 0)) > 0
        )
        all_mastered = bool(progress_rows) and regions_mastered == len(progress_rows)
        ranks = [
            (80, "cartographer", "Cartographer"),
            (60, "surveyor", "Surveyor"),
            (40, "pathfinder", "Pathfinder"),
            (20, "trailblazer", "Trailblazer"),
            (0, "guild_scout", "Guild Scout"),
        ]
        if all_mastered:
            rank_id, rank_name = "master_cartographer", "Master Cartographer"
            next_rank = None
        else:
            _, rank_id, rank_name = next(row for row in ranks if average_progress >= row[0])
            next_threshold = next((threshold for threshold, _, _ in reversed(ranks[:-1]) if threshold > average_progress), None)
            next_row = next((row for row in ranks if row[0] == next_threshold), None) if next_threshold is not None else None
            next_rank = {"progress": int(next_threshold), "name": str(next_row[2])} if next_row else {"progress": 100, "name": "Master Cartographer"}
        landmark_count = sum(len(row.get("landmarks", [])) for row in progress_rows)
        landmarks_found = sum(int(row.get("landmarks_found", 0)) for row in progress_rows)
        return {
            "rank_name": rank_name,
            "overall_progress": average_progress,
            "regions_mastered": regions_mastered,
            "region_count": len(progress_rows),
            "all_mastered": all_mastered,
            "legendary_contracts_unlocked": legendary_unlocked,
            "total_boss_clears": sum(int(row.get("boss_clears", 0)) for row in progress_rows),
            "landmarks_found": landmarks_found,
            "landmark_count": landmark_count,
            "next_rank": next_rank,
        }

    def _expedition_add_progress(
        self,
        twitch_id: str,
        region_id: str,
        amount: int,
        *,
        stage_cleared: bool = False,
        completed_run: bool = False,
    ) -> dict[str, Any]:
        amount = max(0, int(amount))
        before = self._expedition_progress(twitch_id, region_id)
        with self.db.tx() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO player_region_exploration(player_id,region_id,progress) VALUES (?,?,0)",
                (str(twitch_id), str(region_id)),
            )
            conn.execute(
                "UPDATE player_region_exploration SET "
                "progress=MIN(100,progress+?), stages_cleared=stages_cleared+?, completed_runs=completed_runs+?, updated_at=CURRENT_TIMESTAMP "
                "WHERE player_id=? AND region_id=?",
                (
                    amount,
                    1 if stage_cleared else 0,
                    1 if completed_run else 0,
                    str(twitch_id),
                    str(region_id),
                ),
            )
        after = self._expedition_progress(twitch_id, region_id)
        crossed = [
            copy.deepcopy(obj) for obj in after.get("objectives", [])
            if int(before.get("progress", 0)) < int(obj.get("threshold", 100)) <= int(after.get("progress", 0))
        ]
        after["new_milestones"] = crossed
        after["achievement_unlocks"] = self._check_achievements(str(twitch_id)) if crossed else []
        return after

    def _expedition_record_boss_clear(self, twitch_id: str, region_id: str) -> dict[str, Any]:
        with self.db.tx() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO player_region_exploration(player_id,region_id,progress) VALUES (?,?,0)",
                (str(twitch_id), str(region_id)),
            )
            conn.execute(
                "UPDATE player_region_exploration SET boss_clears=boss_clears+1,updated_at=CURRENT_TIMESTAMP WHERE player_id=? AND region_id=?",
                (str(twitch_id), str(region_id)),
            )
        return self._expedition_add_progress(str(twitch_id), str(region_id), 10)

    @staticmethod
    def _expedition_cache(state: dict[str, Any]) -> dict[str, Any]:
        cache = state.setdefault("cache", {"xp": 0, "jp": 0, "gil": 0, "items": []})
        cache.setdefault("xp", 0)
        cache.setdefault("jp", 0)
        cache.setdefault("gil", 0)
        cache.setdefault("items", [])
        return cache

    def _expedition_cache_add_item(
        self,
        state: dict[str, Any],
        item_id: str,
        quantity: int,
        *,
        source: str,
    ) -> dict[str, Any] | None:
        item = self.data.items.get(str(item_id))
        quantity = max(0, int(quantity))
        if not item or quantity <= 0:
            return None
        cache = self._expedition_cache(state)
        for row in cache["items"]:
            if str(row.get("id")) == str(item_id) and str(row.get("source")) == str(source):
                row["quantity"] = int(row.get("quantity", 0)) + quantity
                return row
        result = {
            "id": str(item_id),
            "name": str(item.get("name") or item_id),
            "quantity": quantity,
            "source": str(source),
            "rarity": str(item.get("rarity") or "common").title(),
            "category": str(item.get("type") or "item").replace("_", " ").title(),
        }
        cache["items"].append(result)
        return result

    def _expedition_reward_multiplier(self, state: dict[str, Any]) -> float:
        if bool(state.get("boss_contract")):
            region = self.data.expedition_regions.get(str(state.get("region_id") or "")) or {}
            boss = dict(region.get("boss") or {})
            depth = {
                "stages": int(state.get("base_stages") or boss.get("stages", 4) or 4),
                "reward_mult": float(state.get("contract_reward_mult") or boss.get("reward_mult", 1.35) or 1.35),
            }
        else:
            depth = EXPEDITION_DEPTHS.get(str(state.get("depth")), EXPEDITION_DEPTHS["scout"])
        route = EXPEDITION_ROUTES.get(str(state.get("route")), EXPEDITION_ROUTES["unknown"])
        base_stages = int(state.get("base_stages") or depth["stages"])
        stage = int(state.get("stage") or 1)
        bonus = 1.0 + max(0, stage - base_stages) * 0.25
        return float(depth["reward_mult"]) * float(route["reward_mult"]) * bonus

    def _expedition_begin_travel(self, twitch_id: str, state: dict[str, Any], route_id: str) -> int:
        route_id = str(route_id or "unknown").lower()
        if route_id not in EXPEDITION_ROUTES:
            route_id = "unknown"
        chocobo, traits = self._expedition_chocobo_traits(twitch_id)
        if bool(state.get("boss_contract")):
            region = self.data.expedition_regions.get(str(state.get("region_id") or "")) or {}
            boss = dict(region.get("boss") or {})
            base_travel = int(state.get("contract_travel_seconds") or boss.get("travel_seconds", 360) or 360)
        else:
            depth = EXPEDITION_DEPTHS.get(str(state.get("depth")), EXPEDITION_DEPTHS["scout"])
            base_travel = int(depth["travel_seconds"])
        chocobo_level = max(1, int((chocobo or {}).get("level", 1) or 1))
        seconds = expedition_travel_seconds(base_travel, traits, chocobo_level)
        penalty = max(0, int(state.pop("travel_penalty_seconds", 0) or 0))
        if penalty:
            seconds += penalty
        if bool(state.pop("chocobo_travel_boost", False)):
            seconds = max(30, int(round(seconds * 0.80)))
        now = int(time.time())
        state["route"] = route_id
        state["status"] = "travel"
        state["travel_started_at"] = now
        state["travel_ready_at"] = now + seconds
        state["event"] = None
        state["combat"] = None
        state["camp_used_stage"] = False
        self._expedition_save(twitch_id, state)
        return seconds

    def _expedition_select_monster(
        self, twitch_id: str, state: dict[str, Any], region: dict[str, Any]
    ) -> dict[str, Any] | None:
        p = self._player(twitch_id)
        if not p:
            return None
        level = int(p["level"] or 1)
        route = str(state.get("route") or "unknown")
        cap_above = 2 if route == "safe" else 5 if route == "deep" else 3
        region_min = int(region.get("min_level", 1))
        region_max = int(region.get("recommended_max_level", 99))
        minimum = max(region_min, level - 3)
        maximum = min(region_max, level + cap_above) if region_max < 99 else level + cap_above
        candidates: list[dict[str, Any]] = []
        weights: list[float] = []
        entries: list[tuple[dict[str, Any], bool]] = [(dict(entry), False) for entry in region.get("encounters", [])]
        progress = self._expedition_progress(twitch_id, str(region.get("id") or state.get("region_id") or ""))
        if progress.get("boss_unlocked"):
            entries.extend((dict(entry), True) for entry in region.get("rare_encounters", []))
        route_config = EXPEDITION_ROUTES.get(route, EXPEDITION_ROUTES["unknown"])
        rare_mult = float(route_config.get("rare_encounter_mult", 1.0) or 1.0)
        _, traits = self._expedition_chocobo_traits(twitch_id)
        if "keen_eye" in traits:
            rare_mult *= 1.15
        if "lucky_plume" in traits:
            rare_mult *= 1.10
        for entry, is_rare in entries:
            monster = self.data.monsters.get(str(entry.get("monster_id") or ""))
            if not monster:
                continue
            monster_level = int(monster.get("level", 1))
            if minimum <= monster_level <= maximum:
                candidates.append(monster)
                delta = monster_level - level
                danger_bias = 1.0 + max(0, delta) * (0.12 if route == "deep" else 0.04)
                rarity_bias = rare_mult if is_rare else 1.0
                weights.append(max(0.01, float(entry.get("weight", 1)) * danger_bias * rarity_bias))
        if not candidates:
            for entry, is_rare in entries:
                monster = self.data.monsters.get(str(entry.get("monster_id") or ""))
                if monster and int(monster.get("level", 1)) <= maximum:
                    candidates.append(monster)
                    weights.append(max(0.01, float(entry.get("weight", 1)) * (rare_mult if is_rare else 1.0)))
        return self.rng.choices(candidates, weights=weights, k=1)[0] if candidates else None

    def _expedition_roll_treasure(self, twitch_id: str) -> dict[str, Any] | None:
        p = self._player(twitch_id)
        if not p:
            return None
        _, _, candidates = self._venture_treasure_candidates(int(p["level"] or 1))
        items = [item for values in candidates.values() for item in values]
        if not items:
            return None
        return self.rng.choices(
            items,
            weights=[VENTURE_TREASURE_RARITY_WEIGHTS.get(str(item.get("rarity", "common")).lower(), 1) for item in items],
            k=1,
        )[0]

    def _expedition_combat_rewards(
        self, twitch_id: str, state: dict[str, Any], monster: dict[str, Any]
    ) -> dict[str, Any]:
        p = self._player(twitch_id)
        if not p:
            return {"xp": 0, "jp": 0, "gil": 0, "items": []}
        mult = self._expedition_reward_multiplier(state)
        level_factor = encounter_reward_factor(int(p["level"]), int(monster["level"]))
        job_level = self._job_level(twitch_id, p["current_job"])
        jp_factor = jp_reward_factor(int(p["level"]), job_level, int(monster["level"]))
        xp = max(5, int(int(monster["xp"]) * level_factor * mult * self.rng.uniform(0.92, 1.08)))
        jp = self.fellowship_system.apply_jp_bonus(
            max(2, int(int(monster["jp"]) * jp_factor * mult * self.rng.uniform(0.95, 1.10)))
        )
        gil = max(1, int(int(monster["gil"]) * level_factor * mult * self.rng.uniform(0.85, 1.18)))
        job = self.data.jobs[p["current_job"]]
        effects = self._effects(twitch_id, p["current_job"])
        gil = int(gil * (1 + job.get("gil_bonus", 0) + effects.get("gil_bonus", 0)))
        loot_bonus = float(job.get("loot_bonus", 0)) + float(effects.get("loot_bonus", 0))
        drops: list[dict[str, Any]] = []
        for drop in monster.get("drops", []):
            chance = min(0.95, float(drop.get("chance", 0)) * (1 + loot_bonus))
            if self.rng.random() <= chance:
                qty = self.rng.randint(int(drop.get("min", 1)), int(drop.get("max", 1)))
                item_id = str(drop.get("item_id") or "")
                if item_id in self.data.items:
                    drops.append({"id": item_id, "quantity": qty})
        return {"xp": xp, "jp": jp, "gil": gil, "items": drops}

    def _expedition_bank_cache(
        self,
        twitch_id: str,
        state: dict[str, Any],
        *,
        keep_ratio: float = 1.0,
        source: str = "expedition",
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        keep_ratio = max(0.0, min(1.0, float(keep_ratio)))
        cache = self._expedition_cache(state)
        kept = {
            "xp": int(round(int(cache.get("xp", 0)) * keep_ratio)),
            "jp": int(round(int(cache.get("jp", 0)) * keep_ratio)),
            "gil": int(round(int(cache.get("gil", 0)) * keep_ratio)),
            "items": [],
        }
        lost = {
            "xp": max(0, int(cache.get("xp", 0)) - int(kept["xp"])),
            "jp": max(0, int(cache.get("jp", 0)) - int(kept["jp"])),
            "gil": max(0, int(cache.get("gil", 0)) - int(kept["gil"])),
            "items": [],
        }
        for row in list(cache.get("items") or []):
            qty = max(0, int(row.get("quantity", 0)))
            if keep_ratio >= 0.999:
                keep_qty = qty
            else:
                keep_qty = sum(1 for _ in range(qty) if self.rng.random() <= keep_ratio)
            lose_qty = qty - keep_qty
            if keep_qty:
                kept["items"].append({**row, "quantity": keep_qty})
            if lose_qty:
                lost["items"].append({**row, "quantity": lose_qty})

        p = self._player(twitch_id)
        if p:
            with self.db.tx() as conn:
                conn.execute(
                    "UPDATE players SET xp=xp+?,gil=gil+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
                    (int(kept["xp"]), int(kept["gil"]), str(twitch_id)),
                )
                conn.execute(
                    "UPDATE player_jobs SET jp=jp+? WHERE player_id=? AND job_id=?",
                    (int(kept["jp"]), str(twitch_id), str(p["current_job"])),
                )
                if int(kept["gil"]):
                    conn.execute(
                        "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?,'gil','gil',?,?)",
                        (str(twitch_id), int(kept["gil"]), str(source)),
                    )
            for row in kept["items"]:
                self._change_item(str(twitch_id), str(row["id"]), int(row["quantity"]), str(source))
            kept["levelups"] = self._process_levels(str(twitch_id), str(p["current_job"]))
            kept["achievements"] = self._check_achievements(str(twitch_id))
        return kept, lost

    def _expedition_result_summary(
        self,
        twitch_id: str,
        state: dict[str, Any],
        *,
        outcome: str,
        kept: dict[str, Any],
        lost: dict[str, Any],
    ) -> dict[str, Any]:
        region = self.data.expedition_regions.get(str(state.get("region_id"))) or {}
        boss = dict(region.get("boss") or {})
        boss_contract = bool(state.get("boss_contract"))
        legendary_contract = bool(state.get("legendary_contract"))
        depth_name = (
            f"Legendary Contract · {boss.get('name', 'Boss')}"
            if legendary_contract else
            f"Regional Boss · {boss.get('name', 'Boss')}"
            if boss_contract else
            str((EXPEDITION_DEPTHS.get(str(state.get("depth"))) or {}).get("name") or state.get("depth") or "Expedition")
        )
        return {
            "type": "expedition_v12",
            "outcome": str(outcome),
            "title": ("Legendary Contract Complete" if legendary_contract and outcome == "complete" else "Regional Boss Contract Complete" if boss_contract and outcome == "complete" else "Expedition Complete" if outcome == "complete" else "Expedition Returned" if outcome == "returned" else "Expedition Rescue"),
            "region_name": str(region.get("name") or "Unknown Region"),
            "depth": depth_name,
            "boss_contract": boss_contract,
            "legendary_contract": legendary_contract,
            "boss_name": str(boss.get("name") or "") if boss_contract else "",
            "stages": int(state.get("stage") or 1),
            "base_stages": int(state.get("base_stages") or 0),
            "rewards": {
                "xp": int(kept.get("xp", 0)),
                "jp": int(kept.get("jp", 0)),
                "gil": int(kept.get("gil", 0)),
                "seals": int(self._expedition_stipend(state, outcome)),
                "loot": [f"{row.get('name', row.get('id'))} x{int(row.get('quantity', 1))}" for row in kept.get("items", [])],
                "achievements": list(kept.get("achievements") or [])[:4],
                "levelups": list(kept.get("levelups") or [])[:4],
            },
            "lost": {
                "xp": int(lost.get("xp", 0)),
                "jp": int(lost.get("jp", 0)),
                "gil": int(lost.get("gil", 0)),
                "items": [f"{row.get('name', row.get('id'))} x{int(row.get('quantity', 1))}" for row in lost.get("items", [])],
            },
            "history": copy.deepcopy(list(state.get("history") or [])[-10:]),
            "player": self._solo_result_vitals(twitch_id),
            "interactive": True,
        }

    def _remember_expedition_result(self, twitch_id: str, summary: dict[str, Any]) -> None:
        result = {
            "title": str(summary.get("title") or "Expedition Result"),
            "won": str(summary.get("outcome") or "") != "defeat",
            "finished_at": int(time.time()),
            "kind": "expedition",
            "monster_name": "",
            "hunt_name": None,
            "messages": [],
            "summary": copy.deepcopy(summary),
        }
        self._persist_portal_adventure_result(str(twitch_id), "expedition", result)

    def _expedition_finish(
        self,
        twitch_id: str,
        state: dict[str, Any],
        *,
        outcome: str,
        keep_ratio: float = 1.0,
    ) -> GameResult:
        reached_objective = int(state.get("stage") or 0) >= int(state.get("base_stages") or 999)
        kept, lost = self._expedition_bank_cache(
            twitch_id,
            state,
            keep_ratio=keep_ratio,
            source="expedition_return" if keep_ratio >= 0.999 else "expedition_rescue",
        )
        finish_progress = None
        if reached_objective and outcome in {"complete", "returned"}:
            finish_progress = self._expedition_add_progress(
                twitch_id,
                str(state.get("region_id")),
                5,
                completed_run=True,
            )
        stipend_seals = self._award_expedition_stipend(twitch_id, state, outcome)
        if outcome == "complete":
            metrics = {"expeditions_completed": 1}
            if bool(state.get("legendary_contract")):
                metrics["legendary_contracts_completed"] = 1
            elif bool(state.get("boss_contract")):
                metrics["regional_boss_contracts_completed"] = 1
            self.db.update_record_stats(twitch_id, metrics)
        elif outcome == "defeat":
            self.db.update_record_stats(twitch_id, {"expedition_rescues": 1})
        chocobo_xp = max(0, int(state.get("chocobo_xp", 0))) + max(4, int(state.get("stage", 1)) * 3)
        chocobo_notes = self._award_chocobo_xp(twitch_id, chocobo_xp)
        summary = self._expedition_result_summary(twitch_id, state, outcome=outcome, kept=kept, lost=lost)
        summary["chocobo_notes"] = chocobo_notes[:2]
        summary["stipend_seals"] = stipend_seals
        summary["exploration"] = self._expedition_progress(twitch_id, str(state.get("region_id")))
        self._remember_expedition_result(twitch_id, summary)
        self._expedition_delete(twitch_id)
        milestones = list((finish_progress or {}).get("new_milestones") or [])
        announcement = ""
        if milestones:
            newest = milestones[-1]
            announcement = (
                f"REGION MASTERED — {summary['region_name']} reached 100% exploration!"
                if int(newest.get("threshold", 0)) >= 100 else
                f"EXPEDITION DISCOVERY — {summary['region_name']} {int(newest.get('threshold', 0))}%: {newest.get('name', 'Milestone unlocked')}."
            )
        if outcome == "defeat":
            return GameResult.success(
                f"EXPEDITION RESCUE — Your Chocobo gets you home with {int(round(keep_ratio * 100))}% of the Expedition Cache.",
                expedition_finished=True,
                expedition_result=summary,
                expedition_milestones=milestones,
                expedition_announcement=announcement,
                won=False,
            )
        stipend_text = f" / +{int(summary.get('stipend_seals', 0))} Hunt Seals" if int(summary.get("stipend_seals", 0)) else ""
        return GameResult.success(
            f"EXPEDITION RETURN — {summary['region_name']} cache secured: +{kept['xp']} XP / +{kept['jp']} JP / {kept['gil']} Gil{stipend_text}.",
            expedition_finished=True,
            expedition_result=summary,
            expedition_milestones=milestones,
            expedition_announcement=announcement,
            won=True,
        )

    def _expedition_initialize_combat(
        self, twitch_id: str, state: dict[str, Any], monster: dict[str, Any]
    ) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        encounter = {
            "id": int(state.get("started_at", time.time())) * 100 + int(state.get("stage", 1)),
            "kind": "expedition",
            "state": "combat",
            "monster_id": str(monster["id"]),
            "region_id": str(state.get("region_id")),
            "created_at": int(time.time()),
            "starter_id": str(twitch_id),
        }
        roster = {
            str(twitch_id): {
                "name": str(p["display_name"]),
                "username": str(p["username"]),
                "job_id": str(p["current_job"]),
            }
        }
        old_encounter, old_roster = self.active_encounter, self.encounter_roster
        try:
            self.active_encounter, self.encounter_roster = encounter, roster
            combatants, _, _ = self._initialize_active_combat(encounter)
            if combatants == 0:
                return GameResult.fail("Your hero is not in fighting condition for this Expedition encounter.")
            route_config = EXPEDITION_ROUTES.get(str(state.get("route") or "unknown"), EXPEDITION_ROUTES["unknown"])
            route_pressure = float(route_config.get("combat_pressure_mult", 1.0) or 1.0)
            encounter["enemy_pressure_mult"] = route_pressure
            if bool(state.get("legendary_contract")) and bool(state.get("boss_encounter")):
                # Beta 1 balance pass: Legendary bosses remain meaningfully stronger,
                # but the Alpha 3 stack (extra stage + 25% HP + 15% pressure) was
                # too punishing in conservative simulations. Keep the challenge
                # while allowing route choice to matter on the final boss.
                scaled_hp = max(1, int(round(int(encounter.get("monster_max_hp", monster.get("hp", 1))) * 1.20)))
                encounter["monster_max_hp"] = scaled_hp
                encounter["monster_hp"] = scaled_hp
                encounter["enemy_pressure_mult"] = route_pressure * 1.10
                encounter["legendary_contract"] = True
            encounter["enemy_intent"] = self._solo_enemy_intent(monster, encounter)
            state["combat"] = {"encounter": copy.deepcopy(encounter), "roster": copy.deepcopy(self.encounter_roster)}
        finally:
            self.active_encounter, self.encounter_roster = old_encounter, old_roster
        state["event"] = {
            "type": "combat",
            "label": f"{monster['name']} blocks the route.",
            "monster": {"id": str(monster["id"]), "name": str(monster["name"]), "level": int(monster["level"])},
        }
        state["status"] = "combat"
        state.setdefault("history", []).append(
            {"stage": int(state.get("stage", 1)), "type": "combat", "label": f"Encountered {monster['name']}"}
        )
        self._expedition_save(twitch_id, state)
        return GameResult.success(
            f"EXPEDITION · STAGE {int(state.get('stage', 1))} — {monster['name']} (Lv.{monster['level']}) blocks the route.",
            expedition_combat=True,
        )

    def _expedition_stage_resolved(self, twitch_id: str, state: dict[str, Any], event: dict[str, Any], progress_gain: int = 1) -> GameResult:
        state["event"] = event
        state["status"] = "choice"
        state.setdefault("history", []).append(
            {"stage": int(state.get("stage", 1)), "type": str(event.get("type") or "event"), "label": str(event.get("label") or "Stage resolved")}
        )
        progress = self._expedition_add_progress(
            twitch_id,
            str(state.get("region_id")),
            progress_gain,
            stage_cleared=True,
        )
        self._expedition_save(twitch_id, state)
        milestones = list(progress.get("new_milestones") or [])
        region = self.data.expedition_regions.get(str(state.get("region_id") or "")) or {}
        announcement = ""
        if milestones:
            newest = milestones[-1]
            if int(newest.get("threshold", 0)) >= 100:
                announcement = f"REGION MASTERED — {region.get('name', 'Expedition region')} reached 100% exploration!"
            else:
                announcement = f"EXPEDITION DISCOVERY — {region.get('name', 'Region')} {int(newest.get('threshold', 0))}%: {newest.get('name', 'Milestone unlocked')}."
        return GameResult.success(
            f"EXPEDITION · STAGE {int(state.get('stage', 1))} — {event.get('label', 'Stage resolved.')}",
            expedition_stage_complete=True,
            expedition_milestones=milestones,
            expedition_announcement=announcement,
            expedition_progress=progress,
        )

    @_state_guard
    def expedition_start(self, twitch_id: str, region_id: str, depth_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._expedition_load(twitch_id):
            return GameResult.success("Your Expedition is already underway. Continue it from the Adventure Board.", expedition_active=True)
        if not self._expedition_board_ready():
            return GameResult.fail("The Fellowship Expedition Board must be completed before distant Expeditions can launch.")
        chocobo, _ = self._expedition_chocobo_traits(twitch_id)
        if not chocobo:
            return GameResult.fail("A registered Chocobo is required for Expeditions.")
        if p["current_job"] == "adventurer":
            return GameResult.fail("Choose a Job before launching an Expedition.")
        blocked = self._activity_block(twitch_id)
        if blocked:
            return GameResult.fail(blocked)
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return GameResult.fail("Finish your active encounter or raid before launching an Expedition.")
        if self.active_boss or self.active_encounter:
            return GameResult.fail("A Guild battle is already active. Launch the Expedition after it clears.")
        region = self.data.expedition_regions.get(str(region_id))
        if not region:
            return GameResult.fail("That Expedition region is not available.")
        if int(p["level"] or 1) < int(region.get("min_level", 1)):
            return GameResult.fail(f"{region['name']} is recommended from Lv.{int(region.get('min_level', 1))}.")
        contract_kind = str(depth_id).lower()
        boss_contract = contract_kind in {"boss", "legendary"}
        legendary_contract = contract_kind == "legendary"
        if boss_contract:
            progress = self._expedition_progress(twitch_id, str(region["id"]))
            boss = dict(region.get("boss") or {})
            if not boss or not progress.get("boss_unlocked"):
                return GameResult.fail(f"Regional Boss Expeditions unlock at {int(progress.get('boss_unlock_progress', 75))}% exploration.")
            if legendary_contract and not (progress.get("mastered") and int(progress.get("boss_clears", 0)) > 0):
                return GameResult.fail("Legendary Contracts unlock after mastering the region and clearing its Regional Boss at least once.")
            base_stages = int(boss.get("stages", 4) or 4) + (1 if legendary_contract else 0)
            reward_mult = float(boss.get("reward_mult", 1.35) or 1.35) * (1.25 if legendary_contract else 1.0)
            travel_seconds = int(round(int(boss.get("travel_seconds", 360) or 360) * (1.20 if legendary_contract else 1.0)))
            depth = {
                "id": contract_kind,
                "name": (f"Legendary Contract · {boss.get('name', 'Boss')}" if legendary_contract else f"Regional Boss · {boss.get('name', 'Boss')}"),
                "stages": base_stages,
                "travel_seconds": travel_seconds,
                "reward_mult": reward_mult,
            }
        else:
            depth = EXPEDITION_DEPTHS.get(str(depth_id))
            if not depth:
                return GameResult.fail("Choose Scout, Journey, Deep Expedition, or an unlocked Regional Boss contract.")
        now = int(time.time())
        state = {
            "version": 3,
            "started_at": now,
            "updated_at": now,
            "region_id": str(region["id"]),
            "depth": str(depth["id"]),
            "boss_contract": bool(boss_contract),
            "legendary_contract": bool(legendary_contract),
            "contract_reward_mult": float(depth.get("reward_mult", 1.0)) if boss_contract else None,
            "contract_travel_seconds": int(depth.get("travel_seconds", 0)) if boss_contract else None,
            "boss_id": str((region.get("boss") or {}).get("id") or "") if boss_contract else "",
            "stage": 1,
            "base_stages": int(depth["stages"]),
            "max_stages": int(depth["stages"]) if boss_contract else int(depth["stages"]) + int(EXPEDITION_BONUS_STAGES),
            "status": "travel",
            "route": "unknown",
            "cache": {"xp": 0, "jp": 0, "gil": 0, "items": []},
            "history": [],
            "last_round": None,
            "combat": None,
            "event": None,
            "chocobo_xp": 0,
            "discoveries_seen": [],
            "rare_events_seen": [],
        }
        seconds = self._expedition_begin_travel(twitch_id, state, "unknown")
        self.db.update_record_stats(twitch_id, {"expeditions_started": 1})
        return GameResult.success(
            f"EXPEDITION LAUNCHED — {region['name']} · {depth['name']}. Stage 1 travel: {self._format_seconds(seconds)}.",
            expedition_started=True,
            expedition_boss_contract=bool(boss_contract),
            expedition_legendary_contract=bool(legendary_contract),
        )

    def _expedition_regional_flavor(self, region: dict[str, Any], event_type: str) -> str:
        pools = dict(region.get("regional_events") or {})
        values = [str(value) for value in pools.get(str(event_type), []) if str(value).strip()]
        return self.rng.choice(values) if values else ""

    def _expedition_resolve_rare_event(
        self, twitch_id: str, state: dict[str, Any], region: dict[str, Any], traits: set[str], chocobo_level: int, event: dict[str, Any]
    ) -> GameResult:
        kind = str(event.get("kind") or "treasure").lower()
        name = str(event.get("name") or "Rare Discovery")
        description = str(event.get("description") or "An unusual opportunity appears along the route.")
        mult = self._expedition_reward_multiplier(state)
        cache = self._expedition_cache(state)
        stage = int(state.get("stage", 1))
        payload: dict[str, Any] = {"type": "rare", "subtype": kind, "name": name, "rare": True}
        progress_gain = 3
        outcome = ""
        if kind == "resource":
            materials = [str(value) for value in region.get("materials", []) if str(value) in self.data.items]
            item_id = self.rng.choice(materials) if materials else ""
            qty = self.rng.randint(2, 3) + expedition_resource_yield_bonus(traits, chocobo_level)
            row = self._expedition_cache_add_item(state, item_id, qty, source="rare_resource") if item_id else None
            payload["item"] = row
            outcome = f" Recovered {row['name']} x{row['quantity']}." if row else " The opportunity fades before anything can be recovered."
        elif kind == "recovery":
            player = self._player(twitch_id)
            healed = 0
            if player:
                max_hp = self._max_hp(player)
                before = max(0, int(player["current_hp"] or 0))
                healed = max(0, min(max_hp, before + max(1, int(max_hp * 0.20))) - before)
                if healed:
                    self._save_hp(twitch_id, before + healed)
            bonus_gil = max(20, int((30 + stage * 10) * mult))
            cache["gil"] = int(cache.get("gil", 0)) + bonus_gil
            payload.update({"healing": healed, "gil": bonus_gil})
            outcome = f" Restored {healed} HP and added {bonus_gil} Gil to the cache."
        elif kind == "chocobo":
            bond_xp = expedition_chocobo_event_bond_xp(16, chocobo_level)
            state["chocobo_xp"] = int(state.get("chocobo_xp", 0)) + bond_xp
            state["chocobo_travel_boost"] = True
            payload["bond_xp"] = bond_xp
            outcome = f" Your Chocobo earns {bond_xp} Bond XP and shortens the next travel leg."
        elif kind == "survey":
            bonus_gil = max(30, int((45 + stage * 12) * mult))
            cache["gil"] = int(cache.get("gil", 0)) + bonus_gil
            payload["gil"] = bonus_gil
            progress_gain = 7
            outcome = f" The survey advances rapidly and {bonus_gil} Gil is added to the cache."
        else:
            item = self._expedition_roll_treasure(twitch_id)
            row = self._expedition_cache_add_item(state, str(item["id"]), 1, source="rare_treasure") if item else None
            bonus_gil = max(40, int((60 + stage * 18) * mult))
            cache["gil"] = int(cache.get("gil", 0)) + bonus_gil
            payload.update({"item": row, "gil": bonus_gil})
            outcome = (f" Secured {row['name']} and {bonus_gil} Gil." if row else f" Secured {bonus_gil} Gil.")
        payload["label"] = f"RARE — {name}: {description}{outcome}"
        state.setdefault("rare_events_seen", []).append(str(event.get("id") or name))
        self.db.update_record_stats(twitch_id, {"expedition_rare_events": 1})
        return self._expedition_stage_resolved(twitch_id, state, payload, progress_gain=progress_gain)

    @_state_guard
    def expedition_resolve_stage(self, twitch_id: str) -> GameResult:
        state = self._expedition_load(twitch_id)
        if not state:
            return GameResult.fail("No Expedition is currently underway.")
        if str(state.get("status")) != "travel":
            return GameResult.fail("This Expedition stage is not waiting on travel.")
        remaining = max(0, int(state.get("travel_ready_at", 0)) - int(time.time()))
        if remaining > 0:
            return GameResult.fail(f"Travel completes in {self._format_seconds(remaining)}.")
        region = self.data.expedition_regions.get(str(state.get("region_id")))
        if not region:
            return GameResult.fail("This Expedition region is unavailable in the current data build.")
        chocobo, traits = self._expedition_chocobo_traits(twitch_id)
        chocobo_level = max(1, int((chocobo or {}).get("level", 1) or 1))
        if bool(state.get("boss_contract")) and int(state.get("stage", 1)) >= int(state.get("base_stages", 4)):
            boss = dict(region.get("boss") or {})
            monster = self.data.monsters.get(str(boss.get("monster_id") or ""))
            if not monster:
                return GameResult.fail("This Regional Boss contract is missing its combat profile.")
            state["boss_encounter"] = True
            return self._expedition_initialize_combat(twitch_id, state, monster)
        kinds, weights = expedition_event_weights(region, str(state.get("route") or "unknown"), traits, chocobo_level)
        progress = self._expedition_progress(twitch_id, str(region.get("id") or ""))
        mastery = dict(region.get("mastery") or {}) if progress.get("mastered") else {}
        preferred = str(mastery.get("event_type") or "")
        if preferred in kinds:
            weights[kinds.index(preferred)] *= float(mastery.get("event_mult", 1.0) or 1.0)
        if not kinds:
            return GameResult.fail("This Expedition region has no resolvable stage events.")
        rare_events = [dict(value) for value in region.get("rare_events", []) if isinstance(value, dict)]
        route_config = EXPEDITION_ROUTES.get(str(state.get("route") or "unknown"), EXPEDITION_ROUTES["unknown"])
        rare_chance = float(route_config.get("rare_event_chance", 0.05) or 0.05)
        rare_chance += expedition_rare_event_bonus(traits, chocobo_level)
        if progress.get("mastered"):
            rare_chance += 0.010
        if rare_events and self.rng.random() < min(0.15, rare_chance):
            seen = set(str(value) for value in state.get("rare_events_seen", []))
            unseen = [value for value in rare_events if str(value.get("id") or value.get("name")) not in seen]
            rare_event = self.rng.choice(unseen or rare_events)
            return self._expedition_resolve_rare_event(twitch_id, state, region, traits, chocobo_level, rare_event)
        event_type = self.rng.choices(kinds, weights=weights, k=1)[0]
        mult = self._expedition_reward_multiplier(state)
        cache = self._expedition_cache(state)
        stage = int(state.get("stage", 1))

        if event_type == "combat":
            monster = self._expedition_select_monster(twitch_id, state, region)
            if monster:
                return self._expedition_initialize_combat(twitch_id, state, monster)
            event_type = "discovery"

        if event_type == "resource":
            materials = [str(value) for value in region.get("materials", []) if str(value) in self.data.items]
            item_id = self.rng.choice(materials) if materials else ""
            qty = self.rng.randint(1, 2) + expedition_resource_yield_bonus(traits, chocobo_level)
            row = self._expedition_cache_add_item(state, item_id, qty, source="resource") if item_id else None
            flavor = self._expedition_regional_flavor(region, "resource")
            outcome = f"Gathered {row['name']} x{row['quantity']}." if row else "The resource node turns out to be picked clean."
            label = f"{flavor} {outcome}".strip()
            return self._expedition_stage_resolved(twitch_id, state, {"type": "resource", "label": label, "item": row})

        if event_type == "treasure":
            item = self._expedition_roll_treasure(twitch_id)
            row = self._expedition_cache_add_item(state, str(item["id"]), 1, source="treasure") if item else None
            bonus_gil = max(20, int((30 + stage * 12) * mult))
            cache["gil"] = int(cache.get("gil", 0)) + bonus_gil
            flavor = self._expedition_regional_flavor(region, "treasure")
            outcome = f"Found {row['name']} and {bonus_gil} Gil." if row else f"Recovered {bonus_gil} Gil."
            label = f"{flavor} {outcome}".strip()
            return self._expedition_stage_resolved(twitch_id, state, {"type": "treasure", "label": label, "item": row, "gil": bonus_gil})

        if event_type == "hazard":
            p = self._player(twitch_id)
            max_hp = self._max_hp(p) if p else 1
            percent = self.rng.uniform(0.06, 0.12)
            route_config = EXPEDITION_ROUTES.get(str(state.get("route") or "unknown"), EXPEDITION_ROUTES["unknown"])
            percent *= float(route_config.get("hazard_damage_mult", 1.0) or 1.0)
            percent *= expedition_hazard_damage_multiplier(traits, chocobo_level)
            region_progress = self._expedition_progress(twitch_id, str(region.get("id") or ""))
            if region_progress.get("mastered"):
                percent *= float((region.get("mastery") or {}).get("hazard_mult", 1.0) or 1.0)
            damage = max(1, int(max_hp * percent))
            current_hp = max(1, int(p["current_hp"] or 1)) if p else 1
            new_hp = max(1, current_hp - damage)
            self._save_hp(twitch_id, new_hp)
            flavor = self._expedition_regional_flavor(region, "hazard")
            outcome = f"{region.get('hazard', 'Regional hazard')} costs {current_hp - new_hp} HP, but the party keeps moving."
            label = f"{flavor} {outcome}".strip()
            return self._expedition_stage_resolved(twitch_id, state, {"type": "hazard", "label": label, "damage": current_hp - new_hp})

        if event_type == "discovery":
            discoveries = [str(value) for value in region.get("discoveries", [])]
            unseen = [value for value in discoveries if value not in set(state.get("discoveries_seen") or [])]
            landmark = self.rng.choice(unseen or discoveries or ["Uncharted Landmark"])
            if landmark not in state.setdefault("discoveries_seen", []):
                state["discoveries_seen"].append(landmark)
            bonus_gil = max(10, int((20 + stage * 8) * mult))
            cache["gil"] = int(cache.get("gil", 0)) + bonus_gil
            flavor = self._expedition_regional_flavor(region, "discovery")
            outcome = f"Discovered {landmark}. Survey value added to the Guild map."
            label = f"{flavor} {outcome}".strip()
            return self._expedition_stage_resolved(twitch_id, state, {"type": "discovery", "label": label, "landmark": landmark, "gil": bonus_gil}, progress_gain=4)

        if event_type == "traveler":
            p = self._player(twitch_id)
            if p:
                max_hp = self._max_hp(p)
                before = max(0, int(p["current_hp"] or 0))
                healed = max(0, min(max_hp, before + max(1, int(max_hp * 0.12))) - before)
                if healed:
                    self._save_hp(twitch_id, before + healed)
            else:
                healed = 0
            bonus_gil = max(15, int((25 + stage * 10) * mult))
            cache["gil"] = int(cache.get("gil", 0)) + bonus_gil
            flavor = self._expedition_regional_flavor(region, "traveler")
            outcome = f"+{bonus_gil} Gil to the cache" + (f" and {healed} HP restored." if healed else ".")
            label = f"{flavor} {outcome}".strip()
            return self._expedition_stage_resolved(twitch_id, state, {"type": "traveler", "label": label, "gil": bonus_gil, "healing": healed})

        if event_type == "chocobo":
            bond_xp = expedition_chocobo_event_bond_xp(8, chocobo_level)
            state["chocobo_xp"] = int(state.get("chocobo_xp", 0)) + bond_xp
            state["chocobo_travel_boost"] = True
            flavor = self._expedition_regional_flavor(region, "chocobo")
            label = f"{flavor} The next travel leg is shortened and {bond_xp} Bond XP is earned.".strip()
            return self._expedition_stage_resolved(twitch_id, state, {"type": "chocobo", "label": label, "bond_xp": bond_xp})

        return self._expedition_stage_resolved(twitch_id, state, {"type": "event", "label": "The stage passes without incident."})

    def _expedition_combat_public(self, twitch_id: str, state: dict[str, Any]) -> dict[str, Any] | None:
        combat = state.get("combat") or {}
        encounter = combat.get("encounter") or {}
        roster = combat.get("roster") or {}
        meta = roster.get(str(twitch_id))
        monster = self.data.monsters.get(str(encounter.get("monster_id") or ""))
        if not encounter or not meta or not monster:
            return None
        return {
            "round": int(encounter.get("round", 1)),
            "max_rounds": int(encounter.get("max_rounds", 12)),
            "boss": bool(state.get("boss_encounter")),
            "enemy": {
                "id": str(monster["id"]),
                "name": str(monster["name"]),
                "level": int(monster["level"]),
                "hp": max(0, int(encounter.get("monster_hp", 0))),
                "max_hp": max(1, int(encounter.get("monster_max_hp", 1))),
                "intent": str((encounter.get("enemy_intent") or {}).get("label") or "Preparing an action"),
            },
            "player": {
                "name": str(meta.get("name") or "Hero"),
                "job_id": str(meta.get("job_id") or ""),
                "job_name": str((self.data.jobs.get(str(meta.get("job_id"))) or {}).get("name") or "Adventurer"),
                "hp": int(meta.get("hp", 0)),
                "max_hp": int(meta.get("max_hp", 0)),
                "mp": int(meta.get("mp", 0)),
                "max_mp": int(meta.get("max_mp", 0)),
                "ap": int(meta.get("ap", 0)),
                "max_ap": int(meta.get("max_ap", 0)),
                "statuses": status_text(meta.get("statuses", {}), limit=4),
            },
            "abilities": self._solo_ability_rows(meta),
            "items": self._solo_owned_battle_items(twitch_id, meta),
        }

    def _finish_expedition_combat_victory(
        self,
        twitch_id: str,
        state: dict[str, Any],
        monster: dict[str, Any],
        meta: dict[str, Any],
        round_no: int,
        log: list[str],
    ) -> GameResult:
        self._save_hp(twitch_id, int(meta.get("hp", 0)))
        self._save_resources_from_meta(twitch_id, meta)
        rewards = self._expedition_combat_rewards(twitch_id, state, monster)
        cache = self._expedition_cache(state)
        cache["xp"] = int(cache.get("xp", 0)) + int(rewards["xp"])
        cache["jp"] = int(cache.get("jp", 0)) + int(rewards["jp"])
        cache["gil"] = int(cache.get("gil", 0)) + int(rewards["gil"])
        for drop in rewards.get("items", []):
            self._expedition_cache_add_item(state, str(drop["id"]), int(drop["quantity"]), source="combat")
        with self.db.tx() as conn:
            conn.execute(
                "UPDATE players SET monsters_defeated=monsters_defeated+1,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
                (str(twitch_id),),
            )
            conn.execute(
                "INSERT INTO bestiary(player_id,monster_id,defeats) VALUES (?,?,1) "
                "ON CONFLICT(player_id,monster_id) DO UPDATE SET defeats=defeats+1",
                (str(twitch_id), str(monster["id"])),
            )
        self._record_combat_metrics(
            twitch_id,
            meta.get("job_id"),
            monster["id"],
            battle_type="venture",
            won=True,
            knocked_out=False,
            damage_dealt=int(meta.get("damage", 0)),
            damage_taken=int(meta.get("damage_taken", 0)),
            healing_done=int(meta.get("healing", 0)),
            best_hit=int(meta.get("best_hit", 0)),
        )
        state["last_round"] = {"round": round_no, "events": list(log), "summary": round_summary(log)}
        state["combat"] = None
        is_boss = bool(state.get("boss_encounter"))
        boss_progress = None
        guaranteed: list[str] = []
        if is_boss:
            region = self.data.expedition_regions.get(str(state.get("region_id") or "")) or {}
            boss = dict(region.get("boss") or {})
            legendary_mult = 2 if bool(state.get("legendary_contract")) else 1
            for reward in boss.get("guaranteed_rewards", []):
                quantity = int(reward.get("quantity", 1) or 1) * legendary_mult
                row = self._expedition_cache_add_item(
                    state, str(reward.get("item_id") or ""), quantity, source="legendary_regional_boss" if legendary_mult > 1 else "regional_boss"
                )
                if row:
                    guaranteed.append(f"{row['name']} x{quantity}")
            boss_progress = self._expedition_record_boss_clear(twitch_id, str(state.get("region_id") or ""))
            state["boss_encounter"] = False
        event = {
            "type": "regional_boss_victory" if is_boss else "combat_victory",
            "label": (
                (f"Legendary Regional Boss defeated: {monster['name']}. The contract objective is complete." if bool(state.get("legendary_contract")) else f"Regional Boss defeated: {monster['name']}. The contract objective is complete.")
                if is_boss else
                f"Defeated {monster['name']}. +{rewards['xp']} XP / +{rewards['jp']} JP / {rewards['gil']} Gil added to the Expedition Cache."
            ),
            "monster": {"id": str(monster["id"]), "name": str(monster["name"]), "level": int(monster["level"])},
            "rounds": round_no,
            "rewards": {"xp": rewards["xp"], "jp": rewards["jp"], "gil": rewards["gil"], "guaranteed": guaranteed},
        }
        result = self._expedition_stage_resolved(twitch_id, state, event, progress_gain=0 if is_boss else 1)
        if is_boss:
            region = self.data.expedition_regions.get(str(state.get("region_id") or "")) or {}
            result.data["expedition_boss_victory"] = True
            result.data["expedition_boss"] = {"id": str(monster["id"]), "name": str(monster["name"])}
            result.data["expedition_progress"] = boss_progress or self._expedition_progress(twitch_id, str(state.get("region_id") or ""))
            result.data["expedition_milestones"] = list((boss_progress or {}).get("new_milestones") or [])
            result.data["expedition_legendary_contract"] = bool(state.get("legendary_contract"))
            result.data["expedition_announcement"] = (
                f"LEGENDARY CONTRACT — {monster['name']} has been defeated again in {region.get('name', 'an Expedition region')}!"
                if bool(state.get("legendary_contract")) else
                f"REGIONAL BOSS — {monster['name']} has been defeated in {region.get('name', 'an Expedition region')}!"
            )
        return result

    def _finish_expedition_combat_defeat(
        self,
        twitch_id: str,
        state: dict[str, Any],
        monster: dict[str, Any],
        meta: dict[str, Any],
        round_no: int,
        log: list[str],
    ) -> GameResult:
        self._save_hp(twitch_id, max(0, int(meta.get("hp", 0))))
        self._save_resources_from_meta(twitch_id, meta)
        self._record_combat_metrics(
            twitch_id,
            meta.get("job_id"),
            monster["id"],
            battle_type="venture",
            won=False,
            knocked_out=True,
            damage_dealt=int(meta.get("damage", 0)),
            damage_taken=int(meta.get("damage_taken", 0)),
            healing_done=int(meta.get("healing", 0)),
            best_hit=int(meta.get("best_hit", 0)),
        )
        chocobo, traits = self._expedition_chocobo_traits(twitch_id)
        keep_ratio = expedition_defeat_cache_keep(traits, max(1, int((chocobo or {}).get("level", 1) or 1)))
        state.setdefault("history", []).append(
            {"stage": int(state.get("stage", 1)), "type": "defeat", "label": f"Defeated by {monster['name']}"}
        )
        state["last_round"] = {"round": round_no, "events": list(log), "summary": round_summary(log)}
        return self._expedition_finish(twitch_id, state, outcome="defeat", keep_ratio=keep_ratio)

    @_state_guard
    def expedition_combat_action(self, twitch_id: str, action_kind: str) -> GameResult:
        state = self._expedition_load(twitch_id)
        if not state or str(state.get("status")) != "combat":
            return GameResult.fail("No Expedition battle is waiting for an action.")
        combat = state.get("combat") or {}
        encounter = copy.deepcopy(combat.get("encounter") or {})
        roster = copy.deepcopy(combat.get("roster") or {})
        meta = roster.get(str(twitch_id))
        if not encounter or not meta or int(meta.get("hp", 0)) <= 0:
            return GameResult.fail("Your Expedition combat state cannot accept an action.")
        action_kind = str(action_kind or "").lower().strip()
        if action_kind == "attack":
            meta["action"] = {"kind": "attack"}
        elif action_kind == "defend":
            meta["action"] = {"kind": "defend"}
        elif action_kind.startswith("ability:"):
            ability_id = action_kind.split(":", 1)[1]
            ability = next(
                (row for row in self.data.active_abilities.get(str(meta.get("job_id")), []) if str(row.get("id")) == ability_id),
                None,
            )
            job = self.data.jobs.get(str(meta.get("job_id"))) or {}
            if not ability or int(ability.get("level", 1)) > int(meta.get("job_level", 0)):
                return GameResult.fail("That ability is not available to your current Job level.")
            resource = ability_resource(ability, job)
            cost = ability_cost(ability)
            if int(meta.get(resource, 0)) < cost:
                return GameResult.fail(f"{ability['name']} needs {cost} {resource.upper()}.")
            if resource == "mp" and has_status(meta.get("statuses", {}), "silence"):
                return GameResult.fail("Silence prevents that MP ability.")
            if any(effect.get("type") == "revive" for effect in ability.get("effects", [])):
                return GameResult.fail("Revive abilities need another KO'd ally and cannot be used on a solo Expedition.")
            target_mode = str(ability.get("target") or "enemy")
            target_id = "monster" if target_mode == "enemy" else "party" if target_mode == "party" else str(twitch_id)
            meta["action"] = {
                "kind": "ability",
                "ability_id": str(ability["id"]),
                "target_id": target_id,
                "resource": resource,
                "cost": cost,
            }
        elif action_kind.startswith("item:"):
            item_id = action_kind.split(":", 1)[1]
            item = self.data.items.get(item_id)
            use = item.get("use") if item and isinstance(item.get("use"), dict) else None
            if not item or not use or self._inventory_qty(twitch_id, item_id) <= 0:
                return GameResult.fail("That battle item is not available.")
            if any(effect.get("type") == "revive" for effect in use.get("effects", [])):
                return GameResult.fail("Revive items cannot be used on your conscious hero here.")
            target_mode = str(use.get("target", "ally"))
            target_id = "monster" if target_mode == "enemy" else "party" if target_mode == "party" else str(twitch_id)
            meta["action"] = {"kind": "item", "item_id": item_id, "target_id": target_id}
        else:
            return GameResult.fail("Choose Attack, Ability, Use Item, or Defend.")

        old_encounter, old_roster = self.active_encounter, self.encounter_roster
        try:
            self.active_encounter, self.encounter_roster = encounter, roster
            monster = self.data.monsters[str(encounter["monster_id"])]
            round_no = int(encounter.get("round", 1))
            action = self.encounter_roster[str(twitch_id)].get("action")
            actor = self.encounter_roster[str(twitch_id)]
            log: list[str] = []
            actor["actions"] = int(actor.get("actions", 0)) + 1
            if has_status(actor.get("statuses", {}), "stun"):
                log.append(f"{actor['name']} is stunned and loses their action.")
            elif action["kind"] == "defend":
                actor["defending"] = True
                actor["defends"] = int(actor.get("defends", 0)) + 1
                recovered: list[str] = []
                if int(actor.get("max_ap", 0)) > 0:
                    before = int(actor.get("ap", 0))
                    actor["ap"] = min(int(actor["max_ap"]), before + defend_ap_restore(int(actor["max_ap"])))
                    if int(actor["ap"]) > before:
                        recovered.append(f"{int(actor['ap']) - before} AP")
                if int(actor.get("max_mp", 0)) > 0:
                    before = int(actor.get("mp", 0))
                    actor["mp"] = min(int(actor["max_mp"]), before + defend_mp_restore(int(actor["max_mp"])))
                    if int(actor["mp"]) > before:
                        recovered.append(f"{int(actor['mp']) - before} MP")
                log.append(f"{actor['name']} Defends" + (f" and recovers {' and '.join(recovered)}." if recovered else "."))
            elif action["kind"] == "item":
                self._resolve_active_item(str(twitch_id), actor, action, log)
            elif action["kind"] == "ability":
                self._resolve_active_ability(actor, action, monster, log)
            else:
                self._resolve_active_attack(actor, monster, log)

            if int(encounter.get("monster_hp", 0)) <= 0:
                return self._finish_expedition_combat_victory(twitch_id, state, monster, actor, round_no, log)

            self._solo_resolve_enemy_intent(monster, encounter, log)
            if int(encounter.get("monster_hp", 0)) <= 0:
                return self._finish_expedition_combat_victory(twitch_id, state, monster, actor, round_no, log)

            if has_status(actor.get("statuses", {}), "poison") and int(actor.get("hp", 0)) > 0:
                poison = max(1, int(int(actor.get("max_hp", 1)) * max(0.03, status_magnitude(actor.get("statuses", {}), "poison"))))
                actor["hp"] = max(0, int(actor["hp"]) - poison)
                actor["damage_taken"] = int(actor.get("damage_taken", 0)) + poison
                log.append(f"{actor['name']} suffers {poison} Poison damage.")
            if has_status(actor.get("statuses", {}), "regen") and int(actor.get("hp", 0)) > 0:
                healed = self._apply_battle_heal(actor, actor, status_magnitude(actor.get("statuses", {}), "regen"))
                if healed:
                    log.append(f"{actor['name']} regenerates {healed} HP.")
            tick_statuses(actor.setdefault("statuses", {}))
            actor["action"] = None
            actor["defending"] = False
            self._save_hp(twitch_id, int(actor.get("hp", 0)))
            self._save_resources_from_meta(twitch_id, actor)

            monster_statuses = encounter.setdefault("monster_statuses", {})
            if has_status(monster_statuses, "regen") and int(encounter.get("monster_hp", 0)) > 0:
                before = int(encounter["monster_hp"])
                heal = max(1, int(int(encounter["monster_max_hp"]) * status_magnitude(monster_statuses, "regen")))
                encounter["monster_hp"] = min(int(encounter["monster_max_hp"]), before + heal)
                if int(encounter["monster_hp"]) > before:
                    log.append(f"{monster['name']} regenerates {int(encounter['monster_hp']) - before} HP.")
            tick_statuses(monster_statuses)

            state["last_round"] = {"round": round_no, "events": list(log), "summary": round_summary(log)}
            if int(actor.get("hp", 0)) <= 0:
                return self._finish_expedition_combat_defeat(twitch_id, state, monster, actor, round_no, log)
            if round_no >= int(encounter.get("max_rounds", 12)):
                return self._finish_expedition_combat_defeat(
                    twitch_id,
                    state,
                    monster,
                    actor,
                    round_no,
                    log + ["The encounter reaches its round safety limit."],
                )
            encounter["round"] = round_no + 1
            encounter["enemy_intent"] = self._solo_enemy_intent(monster, encounter)
            state["combat"] = {"encounter": copy.deepcopy(encounter), "roster": copy.deepcopy(self.encounter_roster)}
            self._expedition_save(twitch_id, state)
            return GameResult.success(
                f"EXPEDITION ROUND {round_no} — {round_summary(log)}",
                expedition_round=True,
                round_log=list(log),
            )
        finally:
            self.active_encounter, self.encounter_roster = old_encounter, old_roster

    @_state_guard
    def expedition_continue(self, twitch_id: str, route_id: str) -> GameResult:
        state = self._expedition_load(twitch_id)
        if not state or str(state.get("status")) != "choice":
            return GameResult.fail("Clear the current Expedition stage before choosing the next route.")
        if int(state.get("stage", 1)) >= int(state.get("max_stages", 1)):
            return self._expedition_finish(twitch_id, state, outcome="complete", keep_ratio=1.0)
        state["stage"] = int(state.get("stage", 1)) + 1
        state["last_round"] = None
        seconds = self._expedition_begin_travel(twitch_id, state, route_id)
        return GameResult.success(
            f"EXPEDITION — Stage {state['stage']} route selected: {EXPEDITION_ROUTES.get(str(state.get('route')), EXPEDITION_ROUTES['unknown'])['name']}. Travel {self._format_seconds(seconds)}.",
            expedition_continued=True,
        )

    @_state_guard
    def expedition_camp(self, twitch_id: str) -> GameResult:
        state = self._expedition_load(twitch_id)
        if not state or str(state.get("status")) != "choice":
            return GameResult.fail("You can establish Expedition Camp only after clearing a stage.")
        if state.get("camp_used_stage"):
            return GameResult.fail("You already made camp after this stage.")
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        max_hp = self._max_hp(p)
        current_hp = max(0, int(p["current_hp"] or 0))
        region = self.data.expedition_regions.get(str(state.get("region_id") or "")) or {}
        progress = self._expedition_progress(twitch_id, str(state.get("region_id") or ""))
        camp_ratio = 0.55 + (float((region.get("mastery") or {}).get("camp_bonus", 0.0) or 0.0) if progress.get("mastered") else 0.0)
        heal = max(0, min(max_hp, current_hp + max(1, int((max_hp - current_hp) * camp_ratio))) - current_hp)
        if heal:
            self._save_hp(twitch_id, current_hp + heal)
        resources = self._resource_state_for(self._player(twitch_id))
        max_mp = int(resources.get("max_mp", 0)); max_ap = int(resources.get("max_ap", 0))
        new_mp = int(resources.get("mp", 0)); new_ap = int(resources.get("ap", 0))
        if max_mp > 0:
            new_mp = min(max_mp, new_mp + max(1, int((max_mp - new_mp) * camp_ratio)))
        if max_ap > 0:
            new_ap = min(max_ap, new_ap + max(1, int((max_ap - new_ap) * camp_ratio)))
        self._save_resources_from_meta(twitch_id, {"mp": new_mp, "max_mp": max_mp, "ap": new_ap, "max_ap": max_ap})
        state["camp_used_stage"] = True
        state["last_camp_penalty"] = 2 * 60
        state["travel_penalty_seconds"] = 2 * 60
        state.setdefault("history", []).append(
            {"stage": int(state.get("stage", 1)), "type": "camp", "label": "Made Expedition Camp"}
        )
        self._expedition_save(twitch_id, state)
        return GameResult.success(
            f"EXPEDITION CAMP — Restored {heal} HP and part of your battle resources. The next travel leg takes 2 minutes longer.",
            expedition_camped=True,
        )

    @_state_guard
    def expedition_return(self, twitch_id: str) -> GameResult:
        state = self._expedition_load(twitch_id)
        if not state:
            return GameResult.fail("No Expedition is currently underway.")
        if str(state.get("status")) == "combat":
            return GameResult.fail("Retreat from the active encounter before attempting a normal return.")
        outcome = "complete" if int(state.get("stage", 0)) >= int(state.get("base_stages", 999)) else "returned"
        return self._expedition_finish(twitch_id, state, outcome=outcome, keep_ratio=1.0)

    @_state_guard
    def expedition_retreat(self, twitch_id: str) -> GameResult:
        state = self._expedition_load(twitch_id)
        if not state:
            return GameResult.fail("No Expedition is currently underway.")
        if str(state.get("status")) != "combat":
            return GameResult.fail("Use Return to Guild outside of combat; Retreat is for escaping an active Expedition encounter.")
        combat = state.get("combat") or {}
        meta = (combat.get("roster") or {}).get(str(twitch_id)) or {}
        if meta:
            self._save_hp(twitch_id, max(1, int(meta.get("hp", 1))))
            self._save_resources_from_meta(twitch_id, meta)
        chocobo, traits = self._expedition_chocobo_traits(twitch_id)
        keep_ratio = expedition_defeat_cache_keep(traits, max(1, int((chocobo or {}).get("level", 1) or 1)))
        state.setdefault("history", []).append(
            {"stage": int(state.get("stage", 1)), "type": "retreat", "label": "Retreated from an Expedition encounter"}
        )
        return self._expedition_finish(twitch_id, state, outcome="defeat", keep_ratio=keep_ratio)

    def _expedition_public(self, twitch_id: str) -> dict[str, Any] | None:
        state = self._expedition_load(twitch_id)
        if not state:
            return None
        region = self.data.expedition_regions.get(str(state.get("region_id"))) or {}
        if bool(state.get("boss_contract")):
            boss = dict(region.get("boss") or {})
            legendary_contract = bool(state.get("legendary_contract"))
            depth = {
                "id": "legendary" if legendary_contract else "boss",
                "name": f"Legendary Contract · {boss.get('name', 'Boss')}" if legendary_contract else f"Regional Boss · {boss.get('name', 'Boss')}",
                "stages": int(state.get("base_stages") or boss.get("stages", 4) or 4),
            }
        else:
            depth = EXPEDITION_DEPTHS.get(str(state.get("depth")), EXPEDITION_DEPTHS["scout"])
        route = EXPEDITION_ROUTES.get(str(state.get("route")), EXPEDITION_ROUTES["unknown"])
        now = int(time.time())
        ready_at = int(state.get("travel_ready_at", 0) or 0)
        remaining = max(0, ready_at - now) if str(state.get("status")) == "travel" else 0
        stage = int(state.get("stage", 1))
        base_stages = int(state.get("base_stages") or depth["stages"])
        max_stages = int(state.get("max_stages") or (base_stages + EXPEDITION_BONUS_STAGES))
        return {
            "active": True,
            "status": str(state.get("status") or "travel"),
            "region": {"id": str(region.get("id") or state.get("region_id") or ""), "name": str(region.get("name") or "Unknown Region")},
            "depth": {"id": str(depth["id"]), "name": str(depth["name"])},
            "route": {"id": str(route["id"]), "name": str(route["name"])},
            "stage": stage,
            "base_stages": base_stages,
            "max_stages": max_stages,
            "bonus_stage": stage > base_stages,
            "boss_contract": bool(state.get("boss_contract")),
            "legendary_contract": bool(state.get("legendary_contract")),
            "boss_id": str(state.get("boss_id") or ""),
            "objective_complete": str(state.get("status")) == "choice" and stage >= base_stages,
            "travel_ready_at": ready_at,
            "travel_remaining": remaining,
            "travel_ready": str(state.get("status")) == "travel" and remaining <= 0,
            "cache": copy.deepcopy(self._expedition_cache(state)),
            "event": copy.deepcopy(state.get("event")),
            "history": copy.deepcopy(list(state.get("history") or [])[-8:]),
            "last_round": copy.deepcopy(state.get("last_round")),
            "combat": self._expedition_combat_public(twitch_id, state) if str(state.get("status")) == "combat" else None,
            "can_return": str(state.get("status")) != "combat",
            "can_retreat": str(state.get("status")) == "combat",
            "can_camp": str(state.get("status")) == "choice" and not bool(state.get("camp_used_stage")),
            "can_continue": str(state.get("status")) == "choice" and stage < max_stages,
            "progress": self._expedition_progress(twitch_id, str(state.get("region_id"))),
        }

    def _expedition_board_state(self, twitch_id: str) -> dict[str, Any]:
        p = self._player(twitch_id)
        if not p:
            return {}
        chocobo, traits = self._expedition_chocobo_traits(twitch_id)
        if chocobo:
            chocobo = copy.deepcopy(chocobo)
            chocobo.pop("traits", None)
            spec = chocobo.get("specialization") or {}
            if spec:
                chocobo["specialization"] = {
                    "name": str(spec.get("name") or "Expedition Partner"),
                    "tier": int(spec.get("tier", 1) or 1),
                    "effects": list(spec.get("effects") or [])[:2],
                }
        board_ready = self._expedition_board_ready()
        active = self._expedition_public(twitch_id)
        level = int(p["level"] or 1)
        regions = []
        for region in sorted(self.data.expedition_regions.values(), key=lambda row: int(row.get("min_level", 1))):
            progress = self._expedition_progress(twitch_id, str(region["id"]))
            unlocked = level >= int(region.get("min_level", 1))
            compact_progress = {
                "progress": int(progress.get("progress", 0)),
                "boss_clears": int(progress.get("boss_clears", 0)),
                "boss_unlocked": bool(progress.get("boss_unlocked")),
                "mastered": bool(progress.get("mastered")),
                "legendary_unlocked": bool(progress.get("mastered")) and int(progress.get("boss_clears", 0)) > 0,
                "milestones": [
                    [int(obj.get("threshold", 0)), str(obj.get("name") or "Milestone")]
                    for obj in progress.get("objectives", [])
                ],
                "landmarks_found": int(progress.get("landmarks_found", 0)),
                "landmarks": [
                    {
                        "name": str(landmark.get("name") or "Landmark"),
                        "unlock_progress": int(landmark.get("unlock_progress", 0)),
                    }
                    for landmark in progress.get("landmarks", []) if bool(landmark.get("discovered"))
                ],
                "next_landmark_progress": next(
                    (int(landmark.get("unlock_progress", 0)) for landmark in progress.get("landmarks", []) if not bool(landmark.get("discovered"))),
                    None,
                ),
            }
            region_payload = {
                "id": str(region["id"]),
                "name": str(region["name"]),
                "min_level": int(region.get("min_level", 1)),
                "recommended_max_level": int(region.get("recommended_max_level", 99)),
                "identity": str(region.get("identity") or "Exploration"),
                "hazard": str(region.get("hazard") or "Regional Hazards"),
                "materials": [
                    str((self.data.items.get(str(item_id)) or {}).get("name") or item_id)
                    for item_id in region.get("materials", [])
                    if str(item_id) in self.data.items
                ],
                "unlocked": unlocked,
                "progress": compact_progress,
                "boss_name": str((region.get("boss") or {}).get("name") or region.get("boss_name") or "Regional Boss"),
            }
            if not unlocked:
                region_payload["reason"] = f"Requires Lv.{int(region.get('min_level', 1))}."
            regions.append(region_payload)
        return {
            "board_ready": board_ready,
            "chocobo_ready": bool(chocobo),
            "ready": bool(board_ready and chocobo),
            "reason": "" if board_ready and chocobo else "Complete the Fellowship Expedition Board and register a Chocobo first.",
            "chocobo": chocobo,
            "traits_active": [str(value) for value in sorted(traits)],
            "depths": [
                {
                    "id": str(value["id"]), "name": str(value["name"]),
                    "stages": int(value["stages"]), "travel_seconds": int(value["travel_seconds"]),
                    "reward_mult": float(value["reward_mult"]),
                }
                for value in EXPEDITION_DEPTHS.values()
            ],
            "routes": [
                {
                    "id": str(value["id"]), "name": str(value["name"]),
                    "reward_mult": float(value["reward_mult"]),
                    "rare_event_chance": float(value.get("rare_event_chance", 0.05) or 0.05),
                }
                for value in EXPEDITION_ROUTES.values()
            ],
            "regions": regions,
            "atlas": self._expedition_atlas(twitch_id),
            "active": active,
        }


    # ---------- Portal Actions Phase 9: Adventure Board ----------
    def _portal_adventure_state_data(self, twitch_id: str, *, stream_live: bool | None = None) -> dict[str, Any]:
        """Return live, player-safe Adventure Board state.

        This is intentionally sourced from the authoritative engine instead of
        the hosted snapshot because rally/combat/cooldown state can change
        between snapshot uploads. Numeric Twitch IDs and internal runtime keys
        are never exposed to the browser.
        """
        self._finish_rest_if_ready(twitch_id)
        p = self._player(twitch_id)
        if not p:
            return {}
        self._repair_orphaned_chocobo_writ(twitch_id)
        now = int(time.time())
        level = int(p["level"] or 1)
        current_region = self.data.regions.get(p["current_region"], {})
        camp_remaining = self._camp_remaining(twitch_id)
        joined_encounter = twitch_id in self.encounter_roster
        joined_raid = twitch_id in self.raid_roster
        solo_expedition = self._solo_expedition_public(twitch_id)
        solo_expedition_active = bool(solo_expedition)
        field_expedition = self._expedition_public(twitch_id)
        field_expedition_active = bool(field_expedition)
        active_hunt = self._active_hunt_public(twitch_id)
        active_hunt_running = bool(active_hunt)
        ko = bool(p["current_job"] != "adventurer" and int(p["current_hp"] or 0) <= 0)
        resting = camp_remaining > 0
        max_hp = self._max_hp(p)
        camp_resources = self._resource_state_for(p)
        needs_hp = int(p["current_hp"] or 0) < max_hp
        needs_mp = int(camp_resources.get("max_mp", 0)) > 0 and int(camp_resources.get("mp", 0)) < int(camp_resources.get("max_mp", 0))
        needs_ap = int(camp_resources.get("max_ap", 0)) > 0 and int(camp_resources.get("ap", 0)) < int(camp_resources.get("max_ap", 0))
        camp_reason = ""
        if field_expedition_active:
            camp_reason = "Return from your Expedition before using normal Camp."
        elif solo_expedition_active:
            camp_reason = "Return or retreat from your Solo Venture before setting up camp."
        elif active_hunt_running:
            camp_reason = f"Your hunter returns in {self._format_seconds(active_hunt['remaining_seconds'])}."
        elif joined_encounter:
            camp_reason = "Finish your active encounter before setting up camp."
        elif joined_raid:
            camp_reason = "Finish your active raid before setting up camp."
        elif resting:
            camp_reason = f"Camp completes in {self._format_seconds(camp_remaining)}."
        elif not (needs_hp or needs_mp or needs_ap):
            camp_reason = "Your HP and battle resources are already full."
        camp_can_start = not camp_reason
        activity_reason = (
            f"Resting at camp for another {self._format_seconds(camp_remaining)}."
            if resting else
            "Your hero is KO'd. Recover before adventuring."
            if ko else ""
        )

        cooldown_rows = self.db.all(
            "SELECT action,available_at FROM cooldowns WHERE player_id=? AND (action IN ('venture','solo_venture') OR action LIKE 'hunt:%')",
            (twitch_id,),
        )
        cooldowns = {str(row["action"]): int(row["available_at"] or 0) for row in cooldown_rows}
        venture_available_at = int(cooldowns.get("venture", 0))
        venture_remaining = max(0, venture_available_at - now)
        solo_venture_available_at = int(cooldowns.get("solo_venture", 0))
        solo_venture_remaining = max(0, solo_venture_available_at - now)

        regions: list[dict[str, Any]] = []
        for region in sorted(self.data.regions.values(), key=lambda item: int(item.get("min_level", 1))):
            unlocked = level >= int(region.get("min_level", 1))
            reason = ""
            if not unlocked:
                reason = f"Requires Lv.{int(region.get('min_level', 1))}."
            elif resting or ko:
                reason = activity_reason
            elif joined_encounter or joined_raid:
                reason = "Finish your active encounter or raid before traveling."
            elif field_expedition_active:
                reason = "Return from your Expedition before normal regional travel."
            elif solo_expedition_active:
                reason = "Return from your Solo Venture before traveling."
            elif active_hunt_running:
                reason = f"Your hunter returns in {self._format_seconds(active_hunt['remaining_seconds'])}."
            regions.append({
                "id": str(region["id"]),
                "name": str(region["name"]),
                "description": str(region.get("description") or ""),
                "min_level": int(region.get("min_level", 1)),
                "current": str(region["id"]) == str(p["current_region"]),
                "unlocked": unlocked,
                "can_travel": bool(unlocked and not resting and not ko and not joined_encounter and not joined_raid and not field_expedition_active and not solo_expedition_active and not active_hunt_running),
                "reason": reason,
            })

        encounter_payload: dict[str, Any] | None = None
        if self.active_encounter:
            encounter = self.active_encounter
            monster = self.data.monsters.get(encounter.get("monster_id"), {})
            region = self.data.regions.get(encounter.get("region_id"), {})
            state = str(encounter.get("state", "rally"))
            kind = str(encounter.get("kind", "venture"))
            rally_closes_at = int(float(encounter.get("closes_at") or 0)) if state == "rally" else 0
            next_round_at = int(float(encounter.get("next_round_at") or 0)) if state == "combat" else 0
            party = []
            for meta in list(self.encounter_roster.values())[:24]:
                job_id = str(meta.get("job_id") or "adventurer")
                row = {
                    "username": str(meta.get("username") or ""),
                    "display_name": str(meta.get("name") or meta.get("username") or "Adventurer"),
                    "job_id": job_id,
                    "job_name": str(self.data.jobs.get(job_id, {}).get("name") or "Adventurer"),
                }
                if state == "combat":
                    row.update({
                        "hp": max(0, int(meta.get("hp") or 0)),
                        "max_hp": max(0, int(meta.get("max_hp") or 0)),
                    })
                party.append(row)
            can_join = False
            join_reason = ""
            if kind == "solo_venture":
                join_reason = "Solo Venture battles do not open a rally."
            elif kind == "venture":
                join_reason = "Rally Ventures are joined through Twitch chat with !join."
            elif kind != "venture":
                join_reason = "Hunt marks are solo battles."
            hunt_info = None
            if kind == "hunt" and encounter.get("hunt_id") in self.data.hunts:
                active_hunt = self.data.hunts[encounter["hunt_id"]]
                hunt_info = {
                    "id": str(active_hunt["id"]),
                    "name": str(active_hunt["name"]),
                    "rank": str(active_hunt["rank"]),
                }
            encounter_payload = {
                "id": int(encounter.get("id") or 0),
                "kind": kind,
                "state": state,
                "monster": {
                    "id": str(monster.get("id") or ""),
                    "name": str(monster.get("name") or "Unknown Enemy"),
                    "level": int(monster.get("level") or 1),
                },
                "region": {
                    "id": str(region.get("id") or encounter.get("region_id") or ""),
                    "name": str(region.get("name") or encounter.get("region_id") or "Unknown Region"),
                },
                "hunt": hunt_info,
                "rally_closes_at": rally_closes_at,
                "next_round_at": next_round_at,
                "round": int(encounter.get("round") or 0),
                "max_rounds": int(encounter.get("max_rounds") or 0),
                "enemy_hp": max(0, int(encounter.get("monster_hp") or 0)) if state == "combat" else None,
                "enemy_max_hp": max(0, int(encounter.get("monster_max_hp") or 0)) if state == "combat" else None,
                "party": party,
                "party_size": len(self.encounter_roster),
                "you_joined": joined_encounter,
                "can_join": can_join,
                "join_reason": join_reason,
                "web_combat_controls": False,
            }

        global_battle_reason = ""
        if self.active_boss:
            global_battle_reason = f"A raid against {self.active_boss.get('name', 'a raid boss')} is active."
        elif self.active_encounter:
            if self.active_encounter.get("kind", "venture") == "hunt":
                global_battle_reason = "An Active Hunt is already underway."
            else:
                global_battle_reason = "An encounter is already active."

        venture_reason = ""
        if field_expedition_active:
            venture_reason = "Expedition in progress."
        elif p["current_job"] == "adventurer":
            venture_reason = "Choose a Job before venturing."
        elif active_hunt_running:
            venture_reason = f"Hunt in progress — returns in {self._format_seconds(active_hunt['remaining_seconds'])}."
        elif resting or ko:
            venture_reason = activity_reason
        elif global_battle_reason:
            venture_reason = global_battle_reason
        elif venture_remaining > 0:
            venture_reason = f"Venture ready in {self._format_seconds(venture_remaining)}."
        venture_ready = not venture_reason

        solo_venture_reason = ""
        if field_expedition_active:
            solo_venture_reason = "Expedition in progress."
        elif solo_expedition_active:
            solo_venture_reason = "Solo Venture in progress."
        elif active_hunt_running:
            solo_venture_reason = f"Hunt in progress — returns in {self._format_seconds(active_hunt['remaining_seconds'])}."
        elif p["current_job"] == "adventurer":
            solo_venture_reason = "Choose a Job before starting a Solo Venture."
        elif resting or ko:
            solo_venture_reason = activity_reason
        elif joined_encounter or joined_raid:
            solo_venture_reason = "Finish your active encounter or raid before starting a Solo Venture."
        elif solo_venture_remaining > 0:
            solo_venture_reason = f"Solo Venture ready in {self._format_seconds(solo_venture_remaining)}."
        solo_venture_ready = not solo_venture_reason

        hunt_rows = {
            str(row["hunt_id"]): row
            for row in self.db.all("SELECT hunt_id,clears,first_cleared_at,last_cleared_at FROM player_hunts WHERE player_id=?", (twitch_id,))
        }
        hunts: list[dict[str, Any]] = []
        for hunt in sorted(self.data.hunts.values(), key=lambda item: (HUNT_RANKS.get(str(item.get("rank")), 9), int(item.get("min_level", 1)), str(item.get("name", "")))):
            hunt_id = str(hunt["id"])
            progress = hunt_rows.get(hunt_id)
            met, missing = self._hunt_available(twitch_id, hunt)
            available_at = int(cooldowns.get(f"hunt:{hunt_id}", 0))
            remaining = max(0, available_at - now)
            reason_parts: list[str] = []
            if field_expedition_active:
                reason_parts.append("Return from your Expedition before accepting a Hunt.")
            if p["current_job"] == "adventurer":
                reason_parts.append("Choose a Job before accepting a Hunt.")
            if resting or ko:
                reason_parts.append(activity_reason)
            if global_battle_reason:
                reason_parts.append(global_battle_reason)
            if solo_expedition_active:
                reason_parts.append("Return from your Solo Venture before accepting a Hunt.")
            if active_hunt_running:
                reason_parts.append(f"Current Hunt returns in {self._format_seconds(active_hunt['remaining_seconds'])}.")
            if not met:
                reason_parts.extend(str(value) for value in missing[:4])
            if remaining > 0:
                reason_parts.append(f"Mark available in {self._format_seconds(remaining)}.")
            monster = self.data.monsters.get(hunt.get("monster_id"), {})
            rewards = hunt.get("rewards") if isinstance(hunt.get("rewards"), dict) else {}
            first_rewards: list[str] = []
            first_item = hunt.get("first_clear_item")
            if first_item in self.data.items:
                first_rewards.append(str(self.data.items[first_item]["name"]))
            first_recipe = hunt.get("first_clear_recipe")
            if first_recipe in self.data.recipes:
                first_rewards.append(f"Recipe: {self.data.recipes[first_recipe]['name']}")
            first_title = hunt.get("first_clear_title")
            if first_title in self.data.titles:
                first_rewards.append(f"Title: {self.data.titles[first_title]['name']}")
            hunts.append({
                "id": hunt_id,
                "name": str(hunt.get("name") or hunt_id),
                "rank": str(hunt.get("rank") or "C"),
                "min_level": int(hunt.get("min_level", 1)),
                "monster": {
                    "id": str(monster.get("id") or hunt.get("monster_id") or ""),
                    "name": str(monster.get("name") or hunt.get("monster_id") or "Unknown Mark"),
                    "level": int(monster.get("level") or hunt.get("min_level", 1)),
                    "weakness": monster.get("weakness"),
                    "resistance": monster.get("resistance"),
                },
                "rewards": {
                    "xp": int(rewards.get("xp", 0) or 0),
                    "jp": int(rewards.get("jp", 0) or 0),
                    "gil": int(rewards.get("gil", 0) or 0),
                    "seals": int(rewards.get("seals", 0) or 0),
                },
                "clears": int(progress["clears"] or 0) if progress else 0,
                "first_cleared_at": progress["first_cleared_at"] if progress else None,
                "cooldown_available_at": available_at if remaining > 0 else 0,
                "cooldown_remaining": remaining,
                "requirements_met": bool(met),
                "missing": [str(value) for value in missing[:5]],
                "challengeable": bool(not reason_parts),
                "reason": " ".join(value for value in reason_parts if value),
                "first_clear_rewards": first_rewards,
                "duration_seconds": self._hunt_duration_seconds(str(hunt.get("rank", "C"))),
            })

        # Portal-origin Solo/Hunt results are durable and remain on the Adventure
        # Board until the player explicitly confirms them. Do not time-expire
        # these rows or fall back to the in-memory Solo/Hunt caches after an
        # acknowledgement, otherwise a confirmed card could briefly reappear.
        pending_results = self._pending_portal_adventure_results(twitch_id)
        recent_result = pending_results[0] if pending_results else None
        if recent_result is None:
            history = self._last_battle_history if isinstance(self._last_battle_history, dict) else None
            if history and twitch_id in set(history.get("participants") or []):
                history_kind = str(history.get("kind") or "venture")
                finished_at = int(float(history.get("finished_at") or 0))
                if history_kind not in {"solo_venture", "hunt"} and finished_at and now - finished_at <= 15 * 60:
                    recent_result = {
                        "title": str(history.get("title") or "Recent Battle"),
                        "won": bool(history.get("won")),
                        "finished_at": finished_at,
                        "kind": history_kind,
                        "monster_name": str(history.get("monster_name") or "Unknown Enemy"),
                        "hunt_name": history.get("hunt_name"),
                        "messages": [str(value) for value in list(history.get("messages") or [])[:4]],
                        "summary": None,
                        "requires_confirmation": False,
                    }

        return {
            "server_now": now,
            "player": {
                "level": level,
                "job_id": str(p["current_job"]),
                "job_name": str(self.data.jobs.get(p["current_job"], {}).get("name") or "Adventurer"),
                "hunt_seals": max(0, int(p["hunt_seals"] or 0)),
                "resting": resting,
                "ko": ko,
                "in_encounter": joined_encounter,
                "in_raid": joined_raid,
                "on_hunt": active_hunt_running,
                "on_expedition": field_expedition_active,
            },
            "camp": {
                "resting": resting,
                "can_start": bool(camp_can_start),
                "reason": camp_reason,
                "remaining_seconds": int(camp_remaining),
                "until": int(p["camp_until"] or 0) if resting else 0,
                "duration_seconds": int(self._effective_camp_seconds_for_stream(stream_live)),
                "base_duration_seconds": int(CAMP_REST_ONLINE_SECONDS if stream_live is True else CAMP_REST_OFFLINE_SECONDS),
                "stream_live": bool(stream_live is True),
                "hp": max(0, int(p["current_hp"] or 0)),
                "max_hp": int(max_hp),
                "mp": max(0, int(camp_resources.get("mp", 0))),
                "max_mp": max(0, int(camp_resources.get("max_mp", 0))),
                "ap": max(0, int(camp_resources.get("ap", 0))),
                "max_ap": max(0, int(camp_resources.get("max_ap", 0))),
            },
            "current_region": {
                "id": str(current_region.get("id") or p["current_region"]),
                "name": str(current_region.get("name") or p["current_region"]),
                "description": str(current_region.get("description") or ""),
                "min_level": int(current_region.get("min_level", 1) or 1),
            },
            "regions": regions,
            "venture": {
                "ready": bool(venture_ready),
                "reason": venture_reason,
                "available_at": venture_available_at if venture_remaining > 0 else 0,
                "remaining_seconds": venture_remaining,
                "treasure_possible": True,
                "encounter_chance_percent": int(round((1.0 - VENTURE_TREASURE_CHANCE) * 100)),
                "treasure_chance_percent": int(round(VENTURE_TREASURE_CHANCE * 100)),
                "max_enemy_levels_above_player": int(VENTURE_MAX_LEVEL_ABOVE_PLAYER),
                "rally_reward_bonus_per_level_percent": 5,
                "rally_reward_bonus_max_percent": 50,
                "portal_start_enabled": False,
                "portal_join_enabled": False,
            },
            "expeditions": self._expedition_board_state(twitch_id),
            "solo_venture": {
                "ready": bool(solo_venture_ready),
                "reason": solo_venture_reason,
                "available_at": solo_venture_available_at if solo_venture_remaining > 0 else 0,
                "remaining_seconds": solo_venture_remaining,
                "cooldown_seconds": int(SOLO_VENTURE_COOLDOWN_SECONDS),
                "encounter_chance_percent": int(round((1.0 - SOLO_VENTURE_TREASURE_CHANCE) * 100)),
                "treasure_chance_percent": int(round(SOLO_VENTURE_TREASURE_CHANCE * 100)),
                "max_enemy_levels_above_player": int(SOLO_VENTURE_MAX_LEVEL_ABOVE_PLAYER),
                "fellowship_renown": int(SOLO_VENTURE_FELLOWSHIP_RENOWN),
                "fellowship_percent": 50,
                "portal_only": True,
                "interactive": True,
                "max_stages": int(SOLO_EXPEDITION_MAX_STAGES),
                "stage_bonus_percent": int(round(SOLO_EXPEDITION_STAGE_BONUS * 100)),
                "resolves_immediately": False,
                "expedition": solo_expedition,
            },
            "encounter": encounter_payload,
            "active_hunt": active_hunt,
            "hunts": hunts,
            "recent_result": recent_result,
            "pending_results": pending_results,
            "raid_active": bool(self.active_boss),
        }

    # ---------- Chocobo companions ----------
    def _chocobo_stable_tier(self) -> int:
        return int(self.fellowship_system.facility_tiers().get(CHOCOBO_STABLE_FACILITY_ID, 0))

    def _chocobo_quest_done(self, twitch_id: str) -> bool:
        return bool(self.db.one(
            "SELECT 1 FROM player_quests WHERE player_id=? AND quest_id=?",
            (twitch_id, CHOCOBO_QUEST_ID),
        ))

    def _chocobo_quest_requirements(self, twitch_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for req in CHOCOBO_QUEST_REQUIREMENTS:
            current = int(self._requirement_value(twitch_id, req))
            target = int(req.get("amount", 1))
            result.append({
                **req,
                "current": current,
                "target": target,
                "complete": current >= target,
                "label": self._requirement_text(req, current),
            })
        return result

    def _validate_chocobo_name(self, name: str) -> tuple[bool, str]:
        value = " ".join(str(name or "").strip().split())
        if not 2 <= len(value) <= 20:
            return False, "Chocobo names must be 2–20 characters."
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 '\-]{1,19}", value):
            return False, "Use letters, numbers, spaces, apostrophes, or hyphens for the Chocobo name."
        return True, value

    def _repair_orphaned_chocobo_writ(self, twitch_id: str) -> int:
        """Remove an invalid Writ that has no authoritative Stable timer row.

        Legitimate Writ purchases create the inventory item and player_chocobos
        timing row in the same transaction. Older Daily Provisions could award
        the item alone, leaving the player unable to buy or register normally.
        """
        quantity = self._inventory_qty(twitch_id, "chocobo_writ")
        if quantity <= 0:
            return 0
        row = self.db.one(
            "SELECT writ_purchased_at,writ_ready_at,registered_at FROM player_chocobos WHERE player_id=?",
            (twitch_id,),
        )
        if row and (
            int(row["writ_purchased_at"] or 0) > 0
            or int(row["writ_ready_at"] or 0) > 0
            or bool(row["registered_at"])
        ):
            return 0
        with self.db.tx() as conn:
            current = conn.execute(
                "SELECT quantity FROM inventory WHERE player_id=? AND item_id='chocobo_writ'",
                (twitch_id,),
            ).fetchone()
            orphaned = max(0, int(current["quantity"] or 0)) if current else 0
            if orphaned <= 0:
                return 0
            conn.execute(
                "DELETE FROM inventory WHERE player_id=? AND item_id='chocobo_writ'",
                (twitch_id,),
            )
            conn.execute(
                "INSERT INTO transactions(player_id,kind,asset_id,amount,source) "
                "VALUES (?, 'item','chocobo_writ',?,'orphaned_chocobo_writ_cleanup')",
                (twitch_id, -orphaned),
            )
        return orphaned

    def _chocobo_state_data(self, twitch_id: str) -> dict[str, Any]:
        p = self._player(twitch_id)
        if not p:
            return {}
        self._repair_orphaned_chocobo_writ(twitch_id)
        now = int(time.time())
        row = self.db.one("SELECT * FROM player_chocobos WHERE player_id=?", (twitch_id,))
        registered = bool(row and row["registered_at"] and row["name"])
        stable_tier = self._chocobo_stable_tier()
        quest_done = self._chocobo_quest_done(twitch_id)
        quest_requirements = self._chocobo_quest_requirements(twitch_id)
        writ_quantity = self._inventory_qty(twitch_id, "chocobo_writ")
        writ_ready_at = int(row["writ_ready_at"] or 0) if row else 0
        writ_remaining = max(0, writ_ready_at - now) if writ_quantity > 0 else 0
        writ_active = bool(writ_quantity > 0 and writ_ready_at > 0 and writ_remaining <= 0)
        traits: list[dict[str, str]] = []
        if registered:
            for trait_row in self.db.all(
                "SELECT trait_id FROM player_chocobo_traits WHERE player_id=? ORDER BY unlocked_at,trait_id",
                (twitch_id,),
            ):
                trait_id = str(trait_row["trait_id"])
                trait = CHOCOBO_TRAITS.get(trait_id)
                if trait:
                    traits.append({"id": trait_id, **trait})
        total_xp = max(0, int(row["xp"] or 0)) if row else 0
        level, xp_into_level, xp_next = chocobo_level_from_total_xp(total_xp)
        fellowship_state = self.db.one(
            "SELECT expedition_board_complete FROM fellowship_state WHERE singleton_id=1"
        )
        board_ready = bool(fellowship_state and int(fellowship_state["expedition_board_complete"] or 0))
        can_buy_writ = bool(
            not registered and stable_tier >= 1 and quest_done and writ_quantity <= 0
            and int(p["gil"] or 0) >= CHOCOBO_WRIT_COST_GIL
        )
        specialization = chocobo_expedition_specialization({str(row["id"]) for row in traits}, level) if registered else None
        record_rows = {
            str(item["metric"]): int(item["value"] or 0)
            for item in self.db.all(
                "SELECT metric,value FROM player_record_stats WHERE player_id=? AND metric IN ('expeditions_started','expeditions_completed','expedition_rescues','expedition_rare_events','legendary_contracts_completed','regional_boss_contracts_completed')",
                (str(twitch_id),),
            )
        }
        boss_clear_row = self.db.one(
            "SELECT COALESCE(SUM(boss_clears),0) AS n FROM player_region_exploration WHERE player_id=?",
            (str(twitch_id),),
        )
        accomplishments = {
            "started": int(record_rows.get("expeditions_started", 0)),
            "completed": int(record_rows.get("expeditions_completed", 0)),
            "rescues": int(record_rows.get("expedition_rescues", 0)),
            "rare_events": int(record_rows.get("expedition_rare_events", 0)),
            "boss_contracts": int(record_rows.get("regional_boss_contracts_completed", 0)),
            "legendary_contracts": int(record_rows.get("legendary_contracts_completed", 0)),
            "boss_clears": int(boss_clear_row["n"] or 0) if boss_clear_row else 0,
        }
        return {
            "server_now": now,
            "stable": {
                "unlocked": stable_tier >= 1,
                "tier": stable_tier,
                "required_tier": 1,
                "facility_id": CHOCOBO_STABLE_FACILITY_ID,
            },
            "quest": {
                "id": CHOCOBO_QUEST_ID,
                "name": CHOCOBO_QUEST_NAME,
                "description": CHOCOBO_QUEST_DESCRIPTION,
                "complete": quest_done,
                "ready": bool(not quest_done and all(item["complete"] for item in quest_requirements)),
                "reward_gil": CHOCOBO_QUEST_REWARD_GIL,
                "requirements": quest_requirements,
            },
            "writ": {
                "item_id": "chocobo_writ",
                "name": "Chocobo Registration Writ",
                "cost_gil": CHOCOBO_WRIT_COST_GIL,
                "activation_seconds": CHOCOBO_WRIT_ACTIVATION_SECONDS,
                "quantity": writ_quantity,
                "purchased_at": int(row["writ_purchased_at"] or 0) if row else 0,
                "ready_at": writ_ready_at if writ_quantity > 0 else 0,
                "remaining_seconds": writ_remaining,
                "active": writ_active,
                "can_purchase": can_buy_writ,
            },
            "companion": {
                "registered": registered,
                "name": str(row["name"] or "") if row else "",
                "level": level if registered else 0,
                "max_level": CHOC_MAX_LEVEL,
                "total_xp": total_xp if registered else 0,
                "xp_current": xp_into_level if registered else 0,
                "xp_next": xp_next if registered else 0,
                "traits": traits,
                "specialization": specialization,
                "accomplishments": accomplishments,
                "portrait_id": (
                    str(row["portrait_id"] or CHOCOBO_DEFAULT_PORTRAIT_ID)
                    if row and str(row["portrait_id"] or CHOCOBO_DEFAULT_PORTRAIT_ID) in CHOCOBO_PORTRAITS
                    else CHOCOBO_DEFAULT_PORTRAIT_ID
                ),
                "registered_at": str(row["registered_at"] or "") if row else "",
            },
            "portraits": [
                {"id": portrait_id, "name": meta["name"]}
                for portrait_id, meta in CHOCOBO_PORTRAITS.items()
            ],
            "gil": max(0, int(p["gil"] or 0)),
            "expedition": {
                "board_ready": board_ready,
                "chocobo_ready": registered,
                "ready": bool(board_ready and registered),
                "message": (
                    "Expedition ready — registered Chocobo and Guild Expedition Board are prepared."
                    if board_ready and registered
                    else "Expeditions require both a registered Chocobo and the completed Guild Expedition Board."
                ),
            },
        }

    def chocobo_quest(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._chocobo_quest_done(twitch_id):
            return GameResult.success(f"{CHOCOBO_QUEST_NAME} is already complete. The Stable has retained the paperwork.")
        met, missing = self._requirements_met(twitch_id, CHOCOBO_QUEST_REQUIREMENTS)
        if not met:
            return GameResult.fail(
                f"{CHOCOBO_QUEST_NAME} — {CHOCOBO_QUEST_DESCRIPTION} | Still needed: " + "; ".join(missing[:6])
            )
        with self.db.tx() as conn:
            conn.execute(
                "INSERT INTO player_quests(player_id,quest_id) VALUES (?,?)",
                (twitch_id, CHOCOBO_QUEST_ID),
            )
            if CHOCOBO_QUEST_REWARD_GIL:
                conn.execute(
                    "UPDATE players SET gil=gil+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
                    (CHOCOBO_QUEST_REWARD_GIL, twitch_id),
                )
                conn.execute(
                    "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?, 'quest:chocobo')",
                    (twitch_id, CHOCOBO_QUEST_REWARD_GIL),
                )
        return GameResult.success(
            f"QUEST COMPLETE — {CHOCOBO_QUEST_NAME} | +{CHOCOBO_QUEST_REWARD_GIL:,} Gil. "
            "Once the Fellowship Chocobo Stable is built, purchase a Chocobo Registration Writ."
        )

    def buy_chocobo_writ(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        self._repair_orphaned_chocobo_writ(twitch_id)
        if self._chocobo_stable_tier() < 1:
            return GameResult.fail("The Fellowship Chocobo Stable must be constructed before registration writs can be issued.")
        if not self._chocobo_quest_done(twitch_id):
            return GameResult.fail(f"Complete {CHOCOBO_QUEST_NAME} before requesting a Chocobo Registration Writ.")
        row = self.db.one("SELECT * FROM player_chocobos WHERE player_id=?", (twitch_id,))
        if row and row["registered_at"]:
            return GameResult.fail("You already have a registered Chocobo.")
        if self._inventory_qty(twitch_id, "chocobo_writ") > 0:
            remaining = max(0, int(row["writ_ready_at"] or 0) - int(time.time())) if row else 0
            return GameResult.fail(
                "You already hold a Chocobo Registration Writ. "
                + (f"It activates in {self._format_seconds(remaining)}." if remaining else "It is active and ready to use.")
            )
        now = int(time.time())
        ready_at = now + CHOCOBO_WRIT_ACTIVATION_SECONDS
        with self.db.tx() as conn:
            fresh = conn.execute("SELECT gil FROM players WHERE twitch_id=?", (twitch_id,)).fetchone()
            if not fresh or int(fresh["gil"] or 0) < CHOCOBO_WRIT_COST_GIL:
                have = int(fresh["gil"] or 0) if fresh else 0
                return GameResult.fail(f"A Chocobo Registration Writ costs {CHOCOBO_WRIT_COST_GIL:,} Gil ({have:,} owned).")
            conn.execute("UPDATE players SET gil=gil-?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (CHOCOBO_WRIT_COST_GIL, twitch_id))
            conn.execute(
                "INSERT INTO inventory(player_id,item_id,quantity) VALUES (?, 'chocobo_writ', 1) "
                "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=1",
                (twitch_id,),
            )
            conn.execute(
                "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,'chocobo_writ')",
                (twitch_id, -CHOCOBO_WRIT_COST_GIL),
            )
            conn.execute(
                "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item','chocobo_writ',1,'chocobo_writ')",
                (twitch_id,),
            )
            conn.execute(
                "INSERT INTO player_chocobos(player_id,writ_purchased_at,writ_ready_at) VALUES (?,?,?) "
                "ON CONFLICT(player_id) DO UPDATE SET writ_purchased_at=excluded.writ_purchased_at,writ_ready_at=excluded.writ_ready_at,updated_at=CURRENT_TIMESTAMP",
                (twitch_id, now, ready_at),
            )
        result = GameResult.success(
            f"WRIT ISSUED — Chocobo Registration Writ purchased for {CHOCOBO_WRIT_COST_GIL:,} Gil. "
            "The Stable must validate it for 1 hour before registration."
        )
        unlocked = self._check_achievements(twitch_id)
        if unlocked:
            result.messages.append("Achievement unlocked: " + " | ".join(unlocked))
        return result

    def register_chocobo(self, twitch_id: str, name: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        self._repair_orphaned_chocobo_writ(twitch_id)
        valid, clean_name = self._validate_chocobo_name(name)
        if not valid:
            return GameResult.fail(clean_name)
        if self._chocobo_stable_tier() < 1:
            return GameResult.fail("The Fellowship Chocobo Stable is not yet available.")
        if not self._chocobo_quest_done(twitch_id):
            return GameResult.fail(f"Complete {CHOCOBO_QUEST_NAME} first.")
        row = self.db.one("SELECT * FROM player_chocobos WHERE player_id=?", (twitch_id,))
        if row and row["registered_at"]:
            return GameResult.fail(f"{row['name']} is already your registered Chocobo.")
        if self._inventory_qty(twitch_id, "chocobo_writ") <= 0 or not row:
            return GameResult.fail("You need an activated Chocobo Registration Writ first.")
        remaining = max(0, int(row["writ_ready_at"] or 0) - int(time.time()))
        if remaining > 0:
            return GameResult.fail(f"Your Chocobo Registration Writ activates in {self._format_seconds(remaining)}.")
        trait_id = chocobo_trait_for_player(twitch_id)
        with self.db.tx() as conn:
            inventory = conn.execute(
                "SELECT quantity FROM inventory WHERE player_id=? AND item_id='chocobo_writ'",
                (twitch_id,),
            ).fetchone()
            if not inventory or int(inventory["quantity"] or 0) <= 0:
                return GameResult.fail("Your Chocobo Registration Writ is no longer available.")
            conn.execute(
                "UPDATE inventory SET quantity=quantity-1 WHERE player_id=? AND item_id='chocobo_writ'",
                (twitch_id,),
            )
            conn.execute(
                "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item','chocobo_writ',-1,'chocobo_registration')",
                (twitch_id,),
            )
            conn.execute(
                "UPDATE player_chocobos SET name=?,level=1,xp=0,registered_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
                (clean_name, twitch_id),
            )
            conn.execute(
                "INSERT OR IGNORE INTO player_chocobo_traits(player_id,trait_id) VALUES (?,?)",
                (twitch_id, trait_id),
            )
        trait = CHOCOBO_TRAITS[trait_id]
        return GameResult.success(
            f"CHOCOBO REGISTERED — {clean_name} joins {p['display_name']}! Starter trait: {trait['name']} — {trait['description']}"
        )

    def rename_chocobo(self, twitch_id: str, name: str) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        valid, clean_name = self._validate_chocobo_name(name)
        if not valid:
            return GameResult.fail(clean_name)
        row = self.db.one("SELECT name,registered_at FROM player_chocobos WHERE player_id=?", (twitch_id,))
        if not row or not row["registered_at"]:
            return GameResult.fail("Register a Chocobo before trying to rename one.")
        old_name = str(row["name"] or "your Chocobo")
        self.db.execute(
            "UPDATE player_chocobos SET name=?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
            (clean_name, twitch_id),
        )
        return GameResult.success(f"CHOCOBO RENAMED — {old_name} is now {clean_name}.")

    def set_chocobo_portrait(self, twitch_id: str, portrait_id: str) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        clean_id = str(portrait_id or "").strip().lower()
        if clean_id not in CHOCOBO_PORTRAITS:
            return GameResult.fail("That Chocobo portrait is not available.")
        row = self.db.one("SELECT name,registered_at,portrait_id FROM player_chocobos WHERE player_id=?", (twitch_id,))
        if not row or not row["registered_at"]:
            return GameResult.fail("Register a Chocobo before choosing a portrait.")
        current = str(row["portrait_id"] or CHOCOBO_DEFAULT_PORTRAIT_ID)
        if current == clean_id:
            return GameResult.success(
                f"CHOCOBO PORTRAIT — {row['name']} is already using {CHOCOBO_PORTRAITS[clean_id]['name']}."
            )
        self.db.execute(
            "UPDATE player_chocobos SET portrait_id=?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
            (clean_id, twitch_id),
        )
        return GameResult.success(
            f"CHOCOBO PORTRAIT — {row['name']} now uses {CHOCOBO_PORTRAITS[clean_id]['name']}."
        )

    def _award_chocobo_xp(self, twitch_id: str, amount: int) -> list[str]:
        row = self.db.one("SELECT name,xp,registered_at FROM player_chocobos WHERE player_id=?", (twitch_id,))
        if not row or not row["registered_at"]:
            return []
        before_level, _, _ = chocobo_level_from_total_xp(int(row["xp"] or 0))
        total = min(
            chocobo_total_xp_floor_for_level(CHOC_MAX_LEVEL),
            max(0, int(row["xp"] or 0)) + max(0, int(amount)),
        )
        after_level, _, _ = chocobo_level_from_total_xp(total)
        self.db.execute(
            "UPDATE player_chocobos SET xp=?,level=?,updated_at=CURRENT_TIMESTAMP WHERE player_id=?",
            (total, after_level, twitch_id),
        )
        notes = [f"{row['name']} gains {max(0, int(amount))} Chocobo XP."]
        if after_level > before_level:
            notes.append(f"CHOCOBO LEVEL UP — {row['name']} reached Lv.{after_level}!")
        return notes

    def chocobo(self, twitch_id: str) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        state = self._chocobo_state_data(twitch_id)
        companion = state["companion"]
        if companion["registered"]:
            trait_names = ", ".join(item["name"] for item in companion["traits"]) or "None"
            next_text = "MAX" if companion["xp_next"] <= 0 else f"{companion['xp_current']}/{companion['xp_next']} XP"
            return GameResult.success(
                f"CHOCOBO — {companion['name']} | Lv.{companion['level']} | Bond {next_text} | Trait: {trait_names}",
                state["expedition"]["message"],
            )
        quest = state["quest"]
        stable = state["stable"]
        writ = state["writ"]
        parts = [f"Stable: {'READY' if stable['unlocked'] else 'NOT BUILT'}", f"Quest: {'DONE' if quest['complete'] else 'READY' if quest['ready'] else 'IN PROGRESS'}"]
        if writ["quantity"]:
            parts.append("Writ: ACTIVE" if writ["active"] else f"Writ: {self._format_seconds(writ['remaining_seconds'])}")
        else:
            parts.append("Writ: NOT ISSUED")
        return GameResult.success("CHOCOBO STABLE — " + " | ".join(parts), "Use !chocoboquest, !chocobowrit, then !registerchocobo <name>.")

    def portal_chocobo_state(self, twitch_id: str) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        return GameResult.success("Chocobo Stable refreshed.", chocobo_state=self._chocobo_state_data(twitch_id))

    def _portal_chocobo_mutation(self, twitch_id: str, action_id: str, operation) -> GameResult:
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        # The companion mutation and its replay receipt commit together. Nested
        # engine transactions use savepoints, so an acknowledgement/lease retry
        # can never buy a second Writ or register the same Chocobo twice.
        with self.db.tx() as conn:
            result = operation()
            if self._player(twitch_id):
                result.data["chocobo_state"] = self._chocobo_state_data(twitch_id)
            self._portal_action_store_sql(conn, action_id, result)
            return result

    def portal_complete_chocobo_quest(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_chocobo_mutation(twitch_id, action_id, lambda: self.chocobo_quest(twitch_id))

    def portal_purchase_chocobo_writ(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_chocobo_mutation(twitch_id, action_id, lambda: self.buy_chocobo_writ(twitch_id))

    def portal_register_chocobo(self, twitch_id: str, name: str, action_id: str) -> GameResult:
        return self._portal_chocobo_mutation(twitch_id, action_id, lambda: self.register_chocobo(twitch_id, name))

    def portal_rename_chocobo(self, twitch_id: str, name: str, action_id: str) -> GameResult:
        return self._portal_chocobo_mutation(twitch_id, action_id, lambda: self.rename_chocobo(twitch_id, name))

    def portal_set_chocobo_portrait(self, twitch_id: str, portrait_id: str, action_id: str) -> GameResult:
        return self._portal_chocobo_mutation(
            twitch_id, action_id, lambda: self.set_chocobo_portrait(twitch_id, portrait_id)
        )

    def portal_adventure_state(self, twitch_id: str, *, stream_live: bool | None = None) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        return GameResult.success("Adventure Board refreshed.", adventure_state=self._portal_adventure_state_data(twitch_id, stream_live=stream_live))

    def _portal_adventure_mutation(self, twitch_id: str, action_id: str, operation) -> GameResult:
        """Commit an Adventure mutation and its replay receipt atomically.

        A hosted acknowledgement can be lost after the Bot commits locally. By
        placing the gameplay operation inside the same outer SQLite transaction
        as the bounded Portal replay receipt, a retry can never duplicate cache
        banking, Hunt Seals, exploration progress, item use, or stage advances.
        Nested engine write helpers use savepoints and therefore remain safely
        composable inside this release-hardening transaction.
        """
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        with self.db.tx() as conn:
            result = operation()
            if self._player(twitch_id):
                result.data["adventure_state"] = self._portal_adventure_state_data(twitch_id)
            self._portal_action_store_sql(conn, action_id, result)
            return result

    def _portal_adventure_mutation_result(self, action_id: str, result: GameResult, twitch_id: str) -> GameResult:
        """Legacy Adventure receipt helper for mutations with in-memory coordination.

        Timed Hunts still coordinate through the live in-memory hunt registry, so
        they retain their established receipt flow. Persistent Solo/Expedition
        runs use ``_portal_adventure_mutation`` above for crash-atomic commits.
        """
        result.data["adventure_state"] = self._portal_adventure_state_data(twitch_id)
        with self.db.tx() as conn:
            self._portal_action_store_sql(conn, action_id, result)
        return result

    @_state_guard
    def portal_travel_region(self, twitch_id: str, region_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(
            twitch_id, action_id, lambda: self.travel(twitch_id, str(region_id or "").strip())
        )

    @_state_guard
    def portal_solo_venture(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(twitch_id, action_id, lambda: self.solo_venture(twitch_id))

    @_state_guard
    def portal_solo_expedition_action(self, twitch_id: str, action_kind: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(
            twitch_id, action_id, lambda: self.solo_expedition_action(twitch_id, action_kind)
        )

    @_state_guard
    def portal_solo_expedition_continue(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(twitch_id, action_id, lambda: self.solo_expedition_continue(twitch_id))

    @_state_guard
    def portal_solo_expedition_return(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(twitch_id, action_id, lambda: self.solo_expedition_return(twitch_id))

    @_state_guard
    def portal_solo_expedition_retreat(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(twitch_id, action_id, lambda: self.solo_expedition_retreat(twitch_id))

    @_state_guard
    def portal_expedition_start(self, twitch_id: str, region_id: str, depth_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(
            twitch_id, action_id, lambda: self.expedition_start(twitch_id, region_id, depth_id)
        )

    @_state_guard
    def portal_expedition_resolve_stage(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(twitch_id, action_id, lambda: self.expedition_resolve_stage(twitch_id))

    @_state_guard
    def portal_expedition_action(self, twitch_id: str, action_kind: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(
            twitch_id, action_id, lambda: self.expedition_combat_action(twitch_id, action_kind)
        )

    @_state_guard
    def portal_expedition_continue(self, twitch_id: str, route_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(
            twitch_id, action_id, lambda: self.expedition_continue(twitch_id, route_id)
        )

    @_state_guard
    def portal_expedition_camp(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(twitch_id, action_id, lambda: self.expedition_camp(twitch_id))

    @_state_guard
    def portal_expedition_return(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(twitch_id, action_id, lambda: self.expedition_return(twitch_id))

    @_state_guard
    def portal_expedition_retreat(self, twitch_id: str, action_id: str) -> GameResult:
        return self._portal_adventure_mutation(twitch_id, action_id, lambda: self.expedition_retreat(twitch_id))

    @_state_guard
    def portal_challenge_hunt(self, twitch_id: str, hunt_id: str, action_id: str) -> GameResult:
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        result = self.hunt(twitch_id, str(hunt_id or "").strip())
        if result.ok and result.data.get("hunt_started"):
            assignment = self.active_hunts.get(str(twitch_id))
            if isinstance(assignment, dict):
                assignment["portal_origin"] = True
                assignment["portal_action_id"] = str(action_id or "")
            result.data["portal_origin"] = True
        return self._portal_adventure_mutation_result(action_id, result, twitch_id)

    @_state_guard
    def portal_ack_adventure_result(self, twitch_id: str, result_id: int, action_id: str) -> GameResult:
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        if not self._ack_portal_adventure_result(twitch_id, int(result_id)):
            result = GameResult.fail("That Adventure Board result is no longer pending for this hero.")
        else:
            result = GameResult.success("RESULT CONFIRMED — This Adventure Board result has been cleared.")
        return self._portal_adventure_mutation_result(action_id, result, twitch_id)

    def portal_recovery_state(self, twitch_id: str) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        return GameResult.success("Recovery ready.", recovery_state=self._portal_recovery_state_data(twitch_id))

    def _portal_recovery_mutation(self, twitch_id: str, action_id: str, operation) -> GameResult:
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        with self.db.tx() as conn:
            result = operation()
            if self._player(twitch_id):
                result.data["recovery_state"] = self._portal_recovery_state_data(twitch_id)
            self._portal_action_store_sql(conn, action_id, result)
            return result

    def portal_use_field_item(
        self,
        twitch_id: str,
        item_id: str,
        action_id: str,
        *,
        target_query: str | None = None,
        stream_live: bool | None = None,
    ) -> GameResult:
        item = self.data.items.get(str(item_id))
        use = item.get("use") if item and isinstance(item.get("use"), dict) else {}
        if not item or not use.get("field"):
            return self._portal_store_nonmutating_result(
                action_id, GameResult.fail("That item is not available for out-of-combat Portal recovery.")
            )
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return self._portal_store_nonmutating_result(
                action_id, GameResult.fail("Recovery items are unavailable from the Portal during active combat.")
            )
        return self._portal_recovery_mutation(
            twitch_id, action_id,
            lambda: self.use_item(
                twitch_id, str(item_id), target_query=target_query, stream_live=stream_live
            ),
        )

    def portal_start_rest(self, twitch_id: str, action_id: str, *, stream_live: bool | None = None) -> GameResult:
        return self._portal_recovery_mutation(twitch_id, action_id, lambda: self.rest(twitch_id, stream_live=stream_live))

    def _portal_fellowship_state_data(self, twitch_id: str) -> dict[str, Any]:
        """Return live, contribution-safe Fellowship state for the signed-in player.

        Project definitions and progress remain authoritative in the local game
        engine. The browser receives only the currently active requirements plus
        the player's spendable Gil/material quantities; it never supplies project
        progress or determines how much a contribution should count.
        """
        p = self._player(twitch_id)
        if not p:
            return {}
        member = self.fellowship_system.member_snapshot(twitch_id)
        project = self.fellowship_system.project_snapshot()
        project_payload: dict[str, Any] | None = None
        if project:
            requirements: list[dict[str, Any]] = []
            for req in project.get("requirements", []):
                kind = str(req.get("kind") or "")
                asset_id = str(req.get("asset_id") or "")
                current = max(0, int(req.get("current", 0) or 0))
                target = max(0, int(req.get("target", 0) or 0))
                remaining = max(0, target - current)
                owned = 0
                contributable = kind in {"gil", "item"}
                if kind == "gil":
                    owned = max(0, int(p["gil"] or 0))
                elif kind == "item" and asset_id:
                    owned = max(0, int(self._inventory_qty(twitch_id, asset_id)))
                else:
                    owned = current
                requirements.append({
                    "key": str(req.get("key") or ""),
                    "kind": kind,
                    "asset_id": asset_id,
                    "label": str(req.get("label") or asset_id or kind.title()),
                    "current": current,
                    "target": target,
                    "remaining": remaining,
                    "complete": bool(req.get("complete")),
                    "contributable": contributable,
                    "owned": owned,
                    "available": min(owned, remaining) if contributable else 0,
                })
            project_payload = {
                "id": str(project.get("id") or ""),
                "name": str(project.get("name") or "Fellowship Project"),
                "description": str(project.get("description") or ""),
                "facility_id": str(project.get("facility_id") or ""),
                "tier": int(project.get("tier", 0) or 0),
                "complete": bool(project.get("complete")),
                "requirements": requirements,
            }
        return {
            "gil": max(0, int(p["gil"] or 0)),
            "member": member,
            "project": project_payload,
        }

    def portal_fellowship_state(self, twitch_id: str) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        return GameResult.success(
            "Fellowship contribution options ready.",
            fellowship_state=self._portal_fellowship_state_data(twitch_id),
        )

    def _portal_fellowship_mutation(self, twitch_id: str, action_id: str, operation) -> GameResult:
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        with self.db.tx() as conn:
            result = operation()
            if self._player(twitch_id):
                result.data["fellowship_state"] = self._portal_fellowship_state_data(twitch_id)
            self._portal_action_store_sql(conn, action_id, result)
            return result

    def portal_contribute_gil(self, twitch_id: str, amount: int, action_id: str) -> GameResult:
        if amount < 1 or amount > 1_000_000:
            return self._portal_store_nonmutating_result(
                action_id, GameResult.fail("Gil contribution must be between 1 and 1,000,000.")
            )
        return self._portal_fellowship_mutation(
            twitch_id, action_id, lambda: self.contribute_fellowship(twitch_id, f"gil {amount}")
        )

    def portal_contribute_item(self, twitch_id: str, item_id: str, quantity: int, action_id: str) -> GameResult:
        item_id = str(item_id or "").strip()
        if not item_id or item_id not in self.data.items:
            return self._portal_store_nonmutating_result(
                action_id, GameResult.fail("That item is not recognized by the Fellowship quartermaster.")
            )
        if quantity < 1 or quantity > 999:
            return self._portal_store_nonmutating_result(
                action_id, GameResult.fail("Material contribution quantity must be between 1 and 999.")
            )
        return self._portal_fellowship_mutation(
            twitch_id, action_id, lambda: self.contribute_fellowship(twitch_id, f"{quantity} {item_id}")
        )

    def _portal_crafting_state_data(self, twitch_id: str) -> dict[str, Any]:
        """Return live Blacksmith recipe, material, and forge readiness state."""
        p = self._player(twitch_id)
        if not p:
            return {}
        inventory = {
            str(row["item_id"]): max(0, int(row["quantity"] or 0))
            for row in self.db.all(
                "SELECT item_id,quantity FROM inventory WHERE player_id=? AND quantity>0",
                (twitch_id,),
            )
        }
        level = int(p["level"] or 1)
        gil = max(0, int(p["gil"] or 0))
        seals = max(0, int(p["hunt_seals"] or 0))
        combat_locked = twitch_id in self.encounter_roster or twitch_id in self.raid_roster

        recipes: list[dict[str, Any]] = []
        known_recipes = [recipe for recipe in self.data.recipes.values() if self._recipe_known(twitch_id, recipe)]
        known_recipes.sort(key=lambda recipe: (int(recipe.get("min_level", 1) or 1), str(recipe.get("name") or "")))
        for recipe in known_recipes:
            min_level = int(recipe.get("min_level", 1) or 1)
            gil_each = max(0, int(recipe.get("gil", 0) or 0))
            seals_each = max(0, int(recipe.get("seal_cost", 0) or 0))
            material_payload: list[dict[str, Any]] = []
            resource_cap = 20
            if level < min_level:
                resource_cap = 0
            if gil_each > 0:
                resource_cap = min(resource_cap, gil // gil_each)
            if seals_each > 0:
                resource_cap = min(resource_cap, seals // seals_each)
            for material in recipe.get("materials", []):
                item_id = str(material.get("item_id") or "")
                need = max(1, int(material.get("quantity", 1) or 1))
                owned = inventory.get(item_id, 0)
                if item_id in self.data.items:
                    resource_cap = min(resource_cap, owned // need)
                    material_payload.append({
                        "item_id": item_id,
                        "name": str(self.data.items[item_id].get("name") or item_id),
                        "quantity": need,
                        "owned": owned,
                        "enough": owned >= need,
                    })
            output = recipe.get("output") if isinstance(recipe.get("output"), dict) else {}
            output_id = str(output.get("item_id") or "")
            output_item = self.data.items.get(output_id, {})
            recipes.append({
                "id": str(recipe.get("id") or ""),
                "name": str(recipe.get("name") or "Recipe"),
                "min_level": min_level,
                "level_ready": level >= min_level,
                "gil_each": gil_each,
                "seals_each": seals_each,
                "materials": material_payload,
                "output": {
                    "item_id": output_id,
                    "name": str(output_item.get("name") or output_id),
                    "quantity": max(1, int(output.get("quantity", 1) or 1)),
                    "type": str(output_item.get("type") or "item"),
                    "rarity": str(output_item.get("rarity") or "common"),
                    "description": str(output_item.get("description") or ""),
                    "owned": inventory.get(output_id, 0),
                },
                "max_quantity": max(0, min(20, int(resource_cap))),
                "craftable": bool(not combat_locked and resource_cap >= 1),
            })

        forge_rules: list[dict[str, Any]] = []
        for index, rule in enumerate(self.data.forge):
            base_gil = max(0, int(rule.get("gil", 0) or 0))
            effective_gil = self.fellowship_system.effective_forge_gil(base_gil)
            forge_rules.append({
                "current_upgrade": index,
                "next_upgrade": index + 1,
                "base_gil": base_gil,
                "effective_gil": effective_gil,
                "discount_gil": max(0, base_gil - effective_gil),
                "bonus_percent": int(self._forge_bonus_per_level() * (index + 1) * 100),
                "materials": [
                    {
                        "item_id": str(material.get("item_id") or ""),
                        "name": str(self.data.items.get(str(material.get("item_id") or ""), {}).get("name") or material.get("item_id") or "Material"),
                        "quantity": max(1, int(material.get("quantity", 1) or 1)),
                    }
                    for material in rule.get("materials", [])
                ],
            })
        return {
            "gil": gil,
            "hunt_seals": seals,
            "level": level,
            "combat_locked": bool(combat_locked),
            "known_recipe_count": len(known_recipes),
            "recipe_total": len(self.data.recipes),
            "recipes": recipes,
            "forge_rules": forge_rules,
            "forge_max": len(self.data.forge),
        }

    def portal_crafting_state(self, twitch_id: str) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        return GameResult.success(
            "Guild Blacksmith options ready.",
            crafting_state=self._portal_crafting_state_data(twitch_id),
        )

    def _portal_crafting_result(self, action_id: str, result: GameResult, twitch_id: str) -> GameResult:
        if self._player(twitch_id):
            result.data["crafting_state"] = self._portal_crafting_state_data(twitch_id)
        with self.db.tx() as conn:
            self._portal_action_store_sql(conn, action_id, result)
        return result

    def portal_craft_recipe(self, twitch_id: str, recipe_id: str, quantity: int, action_id: str) -> GameResult:
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        recipe_id = str(recipe_id or "").strip()
        recipe = self.data.recipes.get(recipe_id)
        if not recipe:
            return self._portal_store_nonmutating_result(action_id, GameResult.fail("That crafting recipe is not recognized."))
        if quantity < 1 or quantity > 20:
            return self._portal_store_nonmutating_result(action_id, GameResult.fail("Craft quantity must be between 1 and 20."))
        if not self._recipe_known(twitch_id, recipe):
            return self._portal_store_nonmutating_result(action_id, GameResult.fail("That recipe has not been discovered yet."))
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return self._portal_crafting_result(action_id, GameResult.fail("Blacksmith work is locked while you are committed to an active encounter or raid."), twitch_id)

        p = self._player(twitch_id)
        if not p:
            return self._portal_store_nonmutating_result(action_id, self._need_recruit())
        min_level = int(recipe.get("min_level", 1) or 1)
        if int(p["level"] or 1) < min_level:
            return self._portal_crafting_result(action_id, GameResult.fail(f"{recipe['name']} requires Character Lv.{min_level}."), twitch_id)

        total_gil = max(0, int(recipe.get("gil", 0) or 0)) * quantity
        total_seals = max(0, int(recipe.get("seal_cost", 0) or 0)) * quantity
        output = recipe.get("output") if isinstance(recipe.get("output"), dict) else {}
        output_id = str(output.get("item_id") or "")
        output_qty = max(1, int(output.get("quantity", 1) or 1)) * quantity
        with self.db.tx() as conn:
            fresh = conn.execute("SELECT gil,hunt_seals,level FROM players WHERE twitch_id=?", (twitch_id,)).fetchone()
            if not fresh:
                result = self._need_recruit()
                self._portal_action_store_sql(conn, action_id, result)
                return result
            missing: list[str] = []
            if int(fresh["level"] or 1) < min_level:
                missing.append(f"Character Lv.{min_level}")
            if int(fresh["gil"] or 0) < total_gil:
                missing.append(f"{total_gil:,} Gil ({int(fresh['gil'] or 0):,} owned)")
            if int(fresh["hunt_seals"] or 0) < total_seals:
                missing.append(f"{total_seals} Hunt Seals ({int(fresh['hunt_seals'] or 0)} owned)")
            for material in recipe.get("materials", []):
                item_id = str(material.get("item_id") or "")
                need = max(1, int(material.get("quantity", 1) or 1)) * quantity
                row = conn.execute("SELECT quantity FROM inventory WHERE player_id=? AND item_id=?", (twitch_id, item_id)).fetchone()
                owned = max(0, int(row["quantity"] or 0)) if row else 0
                if owned < need:
                    missing.append(f"{self.data.items.get(item_id, {}).get('name', item_id)} x{need} ({owned} owned)")
            if missing:
                result = GameResult.fail("Cannot craft — " + "; ".join(missing[:6]))
                self._portal_action_store_sql(conn, action_id, result)
                return result
            for material in recipe.get("materials", []):
                item_id = str(material.get("item_id") or "")
                need = max(1, int(material.get("quantity", 1) or 1)) * quantity
                conn.execute("UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?", (need, twitch_id, item_id))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, ?)", (twitch_id, item_id, -need, f"craft:{recipe_id}"))
            conn.execute("UPDATE players SET gil=gil-?,hunt_seals=hunt_seals-?,crafts=crafts+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (total_gil, total_seals, quantity, twitch_id))
            if total_gil:
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,?)", (twitch_id, -total_gil, f"craft:{recipe_id}"))
            if total_seals:
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'hunt_seals','hunt_seals',?,?)", (twitch_id, -total_seals, f"craft:{recipe_id}"))
            conn.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (twitch_id, output_id, output_qty))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, ?)", (twitch_id, output_id, output_qty, f"craft:{recipe_id}"))
            output_name = str(self.data.items.get(output_id, {}).get("name") or output_id)
            result = GameResult.success(f"CRAFTED — {output_name} x{output_qty}. The blacksmith nods, which is apparently a five-star review.")
            self._portal_action_store_sql(conn, action_id, result)

        fellowship_notes = self.fellowship_system.record_activity(
            twitch_id, "craft", amount=quantity, event_key=f"portal:craft:{action_id}"
        )
        unlocked = self._check_achievements(twitch_id)
        if unlocked:
            result.messages.append("Achievement unlocked: " + " | ".join(unlocked))
        result.messages.extend(fellowship_notes[:2])
        return self._portal_crafting_result(action_id, result, twitch_id)

    def portal_forge_item(self, twitch_id: str, item_id: str, action_id: str) -> GameResult:
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        item_id = str(item_id or "").strip()
        item = self.data.items.get(item_id)
        if not item or item.get("type") not in {"weapon", "armor", "accessory"}:
            return self._portal_store_nonmutating_result(action_id, GameResult.fail("Only weapons, armor, and accessories can be forged."))
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return self._portal_crafting_result(action_id, GameResult.fail("Blacksmith work is locked while you are committed to an active encounter or raid."), twitch_id)
        if not self._player(twitch_id):
            return self._portal_store_nonmutating_result(action_id, self._need_recruit())

        current = self._upgrade_level(twitch_id, item_id)
        if current >= len(self.data.forge):
            return self._portal_crafting_result(action_id, GameResult.fail(f"{item['name']} is already +{current}, the current forge maximum."), twitch_id)
        rule = self.data.forge[current]
        forge_gil = self.fellowship_system.effective_forge_gil(int(rule.get("gil", 0) or 0))
        with self.db.tx() as conn:
            owned_row = conn.execute("SELECT quantity FROM inventory WHERE player_id=? AND item_id=?", (twitch_id, item_id)).fetchone()
            owned = max(0, int(owned_row["quantity"] or 0)) if owned_row else 0
            fresh = conn.execute("SELECT gil FROM players WHERE twitch_id=?", (twitch_id,)).fetchone()
            missing: list[str] = []
            if owned <= 0:
                missing.append(f"You do not own {item['name']}")
            if not fresh or int(fresh["gil"] or 0) < forge_gil:
                have_gil = int(fresh["gil"] or 0) if fresh else 0
                missing.append(f"{forge_gil:,} Gil ({have_gil:,} owned)")
            for material in rule.get("materials", []):
                mat_id = str(material.get("item_id") or "")
                need = max(1, int(material.get("quantity", 1) or 1))
                row = conn.execute("SELECT quantity FROM inventory WHERE player_id=? AND item_id=?", (twitch_id, mat_id)).fetchone()
                have = max(0, int(row["quantity"] or 0)) if row else 0
                if have < need:
                    missing.append(f"{self.data.items.get(mat_id, {}).get('name', mat_id)} x{need} ({have} owned)")
            if missing:
                result = GameResult.fail(f"Forge +{current + 1} requires — " + "; ".join(missing[:6]))
                self._portal_action_store_sql(conn, action_id, result)
                return result
            for material in rule.get("materials", []):
                mat_id = str(material.get("item_id") or "")
                need = max(1, int(material.get("quantity", 1) or 1))
                conn.execute("UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?", (need, twitch_id, mat_id))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, 'forge')", (twitch_id, mat_id, -need))
            conn.execute("UPDATE players SET gil=gil-?,forge_upgrades=forge_upgrades+1,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (forge_gil, twitch_id))
            if forge_gil:
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,'forge')", (twitch_id, -forge_gil))
            conn.execute("INSERT INTO item_upgrades(player_id,item_id,upgrade_level) VALUES (?,?,?) ON CONFLICT(player_id,item_id) DO UPDATE SET upgrade_level=excluded.upgrade_level", (twitch_id, item_id, current + 1))
            pct = int(self._forge_bonus_per_level() * (current + 1) * 100)
            result = GameResult.success(f"FORGE COMPLETE — {item['name']} is now +{current + 1}. Equipment stat bonuses are now +{pct}% over base.")
            if forge_gil < int(rule.get("gil", 0) or 0):
                result.messages.append(f"Workshop benefit — forge fee reduced to {forge_gil:,} Gil.")
            self._portal_action_store_sql(conn, action_id, result)

        fellowship_notes = self.fellowship_system.record_activity(
            twitch_id, "forge", event_key=f"portal:forge:{action_id}"
        )
        unlocked = self._check_achievements(twitch_id)
        if unlocked:
            result.messages.append("Achievement unlocked: " + " | ".join(unlocked))
        result.messages.extend(fellowship_notes[:2])
        return self._portal_crafting_result(action_id, result, twitch_id)

    def _portal_daily_state_data(self, twitch_id: str, subscriber_tier: int = 0) -> dict[str, Any]:
        p = self._player(twitch_id)
        if not p:
            return {}
        now = int(time.time())
        row = self.db.one("SELECT available_at FROM cooldowns WHERE player_id=? AND action='daily'", (twitch_id,))
        available_at = int(row["available_at"] or 0) if row else 0
        remaining = max(0, available_at - now)
        solo_blocked = bool(self._solo_expedition_load(twitch_id))
        base_low, base_high = daily_gil_range(int(p["level"] or 1))
        low, high = daily_gil_with_perk(base_low, base_high, subscriber_tier)
        preview = provision_preview(int(p["level"] or 1), subscriber_tier)
        return {
            "available": remaining <= 0 and not solo_blocked,
            "available_at": available_at if remaining > 0 else 0,
            "blocked_reason": "Return or retreat from your Solo Venture before collecting new provisions." if solo_blocked else "",
            "remaining_seconds": remaining,
            "gil_min": int(low),
            "gil_max": int(high),
            "base_gil_min": int(base_low),
            "base_gil_max": int(base_high),
            "current_gil": max(0, int(p["gil"] or 0)),
            **preview,
        }

    def portal_daily_state(self, twitch_id: str, subscriber_tier: int = 0) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        return GameResult.success(
            "Daily provisions checked.",
            daily_state=self._portal_daily_state_data(twitch_id, subscriber_tier),
        )

    def _daily_reward(self, twitch_id: str, subscriber_tier: int = 0) -> tuple[int, list[dict[str, Any]], dict[str, Any]]:
        p = self._player(twitch_id)
        if not p:
            return 0, [], subscriber_perk(0)
        perk = subscriber_perk(subscriber_tier)
        base_low, base_high = daily_gil_range(int(p["level"] or 1))
        low, high = daily_gil_with_perk(base_low, base_high, subscriber_tier)
        gil = int(self.rng.randint(low, high))
        provisions = roll_daily_provisions(self.data.items, int(p["level"] or 1), self.rng, subscriber_tier)
        return gil, provisions, perk

    @staticmethod
    def _daily_provision_text(provisions: list[dict[str, Any]]) -> str:
        if not provisions:
            return "No provision bundle"
        return " | ".join(f"{row['name']} x{int(row['quantity'])}" for row in provisions)

    def _grant_daily_sql(
        self,
        conn: Any,
        twitch_id: str,
        gil: int,
        provisions: list[dict[str, Any]],
    ) -> None:
        conn.execute("UPDATE players SET gil=gil+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (gil, twitch_id))
        conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,'daily')", (twitch_id, gil))
        for reward in provisions:
            item_id = str(reward["item_id"])
            quantity = max(1, int(reward["quantity"]))
            conn.execute(
                "INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) "
                "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity",
                (twitch_id, item_id, quantity),
            )
            conn.execute(
                "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, 'daily')",
                (twitch_id, item_id, quantity),
            )

    def portal_claim_daily(self, twitch_id: str, action_id: str, subscriber_tier: int = 0) -> GameResult:
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        p = self._player(twitch_id)
        if not p:
            return self._portal_store_nonmutating_result(action_id, self._need_recruit())
        if self._solo_expedition_load(twitch_id):
            return self._portal_store_nonmutating_result(
                action_id,
                GameResult.fail("Return or retreat from your Solo Venture before collecting new Daily Guild Provisions.", daily_state=self._portal_daily_state_data(twitch_id, subscriber_tier)),
            )
        now = int(time.time())
        with self.db.tx() as conn:
            cooldown = conn.execute("SELECT available_at FROM cooldowns WHERE player_id=? AND action='daily'", (twitch_id,)).fetchone()
            available_at = int(cooldown["available_at"] or 0) if cooldown else 0
            remaining = max(0, available_at - now)
            if remaining > 0:
                result = GameResult.fail(
                    f"Daily provisions already claimed. Return in {self._format_seconds(remaining)}.",
                    daily_state=self._portal_daily_state_data(twitch_id, subscriber_tier),
                )
                self._portal_action_store_sql(conn, action_id, result)
                return result
            gil, provisions, perk = self._daily_reward(twitch_id, subscriber_tier)
            self._grant_daily_sql(conn, twitch_id, gil, provisions)
            next_at = now + 24 * 3600
            conn.execute("INSERT INTO cooldowns(player_id,action,available_at) VALUES (?, 'daily', ?) ON CONFLICT(player_id,action) DO UPDATE SET available_at=excluded.available_at", (twitch_id, next_at))
            perk_note = ""
            if int(perk["tier"]) > 0:
                perk_note = f" [{perk['label']}: +{perk['gil_bonus_percent']}% Gil, {perk['rolls']} provision rolls]"
            result = GameResult.success(
                f"Daily provisions{perk_note}: +{gil} Gil | {self._daily_provision_text(provisions)}.",
                claimed_gil=gil,
                provisions=provisions,
                subscriber_tier=int(perk["tier"]),
                subscriber_label=str(perk["label"]),
            )
            self._portal_action_store_sql(conn, action_id, result)
        result.data["daily_state"] = self._portal_daily_state_data(twitch_id, subscriber_tier)
        with self.db.tx() as conn:
            self._portal_action_store_sql(conn, action_id, result)
        return result

    def portal_character_state(self, twitch_id: str) -> GameResult:
        if not self._player(twitch_id):
            return self._need_recruit()
        return GameResult.success("Character options ready.", **self._portal_character_state_data(twitch_id))

    def _portal_character_mutation(self, twitch_id: str, action_id: str, operation) -> GameResult:
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        with self.db.tx() as conn:
            result = operation()
            if self._player(twitch_id):
                result.data["character_state"] = self._portal_character_state_data(twitch_id)
            self._portal_action_store_sql(conn, action_id, result)
            return result

    def portal_equip(self, twitch_id: str, item_id: str, action_id: str) -> GameResult:
        return self._portal_character_mutation(twitch_id, action_id, lambda: self.equip(twitch_id, item_id))

    def portal_unequip(self, twitch_id: str, slot: str, action_id: str) -> GameResult:
        return self._portal_character_mutation(twitch_id, action_id, lambda: self.unequip(twitch_id, slot))

    def portal_change_job(self, twitch_id: str, job_id: str, action_id: str) -> GameResult:
        return self._portal_character_mutation(twitch_id, action_id, lambda: self.choose_job(twitch_id, job_id))

    def portal_set_stance(self, twitch_id: str, stance: str, action_id: str) -> GameResult:
        return self._portal_character_mutation(twitch_id, action_id, lambda: self.set_stance(twitch_id, stance))

    def portal_set_mastery(self, twitch_id: str, job_id: str, slot: int, action_id: str) -> GameResult:
        return self._portal_character_mutation(twitch_id, action_id, lambda: self.mastery(twitch_id, job_id, slot))

    def portal_clear_mastery(self, twitch_id: str, slot: int, action_id: str) -> GameResult:
        return self._portal_character_mutation(twitch_id, action_id, lambda: self.clear_mastery(twitch_id, slot))

    def portal_shop_state(self, twitch_id: str) -> GameResult:
        """Return the signed-in player's live Moogle Emporium state for Portal Actions.

        This is intentionally produced by the authoritative engine instead of the
        hosted Web mirror. Opening the Portal shop therefore uses the exact same
        personalized rotation and refresh rules as ``!shop``.
        """
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        stock, expires = self._shop_stock(twitch_id)
        equipment = self.db.one(
            "SELECT weapon_id,armor_id,accessory_id FROM equipment WHERE player_id=?",
            (twitch_id,),
        )
        equipped_ids = {
            str(value)
            for value in (
                equipment["weapon_id"] if equipment else None,
                equipment["armor_id"] if equipment else None,
                equipment["accessory_id"] if equipment else None,
            )
            if value
        }
        inventory_rows = self.db.all(
            "SELECT item_id,quantity FROM inventory WHERE player_id=? AND quantity>0",
            (twitch_id,),
        )
        owned = {str(row["item_id"]): int(row["quantity"]) for row in inventory_rows}
        job_id = str(p["current_job"])
        job = self.data.jobs.get(job_id, {"name": "Adventurer"})

        def item_payload(item: dict[str, Any]) -> dict[str, Any]:
            allowed_ids = [value for value in item.get("allowed_jobs", []) if value in self.data.jobs]
            return {
                "id": item["id"],
                "name": item["name"],
                "type": item.get("type", "item"),
                "rarity": item.get("rarity", "common"),
                "price": int(item.get("price", 0) or 0),
                "owned": int(owned.get(item["id"], 0)),
                "min_level": int(item.get("min_level", 1) or 1),
                "allowed_job_ids": allowed_ids,
                "allowed_jobs": [self.data.jobs[value]["name"] for value in allowed_ids],
                "description": str(item.get("description") or ""),
                "equipment": item.get("type") in {"weapon", "armor", "accessory"},
            }

        combat_locked = twitch_id in self.encounter_roster or twitch_id in self.raid_roster
        return GameResult.success(
            "Moogle Emporium stock ready.",
            gil=int(p["gil"]),
            level=int(p["level"]),
            job_id=job_id,
            job_name=str(job.get("name", "Adventurer")),
            expires_at=int(expires),
            stock=[item_payload(item) for item in stock],
            combat_locked=combat_locked,
        )

    def _portal_action_replay(self, action_id: str) -> GameResult | None:
        key = f"portal_action:{str(action_id).strip()}"
        row = self.db.runtime_state(key)
        if not row:
            return None
        try:
            payload = json.loads(row["value_json"])
            if not isinstance(payload, dict):
                return None
            return GameResult(
                bool(payload.get("ok")),
                [str(value) for value in payload.get("messages", [])],
                dict(payload.get("data") or {}),
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def _portal_action_store_sql(conn: Any, action_id: str, result: GameResult) -> None:
        key = f"portal_action:{str(action_id).strip()}"
        encoded = json.dumps(
            {"ok": bool(result.ok), "messages": list(result.messages), "data": dict(result.data)},
            separators=(",", ":"),
            sort_keys=True,
            ensure_ascii=False,
        )
        conn.execute(
            "INSERT INTO runtime_state(state_key,value_json,updated_at) VALUES (?,?,CURRENT_TIMESTAMP) "
            "ON CONFLICT(state_key) DO UPDATE SET value_json=excluded.value_json,updated_at=CURRENT_TIMESTAMP",
            (key, encoded),
        )
        conn.execute(
            "DELETE FROM runtime_state WHERE state_key LIKE 'portal_action:%' AND updated_at < datetime('now','-30 days')"
        )

    def _portal_store_nonmutating_result(self, action_id: str, result: GameResult) -> GameResult:
        with self.db.tx() as conn:
            self._portal_action_store_sql(conn, action_id, result)
        return result

    def portal_buy(self, twitch_id: str, item_id: str, quantity: int, action_id: str) -> GameResult:
        """Replay-safe Portal purchase using authoritative stock and pricing."""
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        p = self._player(twitch_id)
        if not p:
            return self._portal_store_nonmutating_result(action_id, self._need_recruit())
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return self._portal_store_nonmutating_result(
                action_id,
                GameResult.fail("Moogle Emporium purchases are locked while you are committed to an active encounter or raid."),
            )
        if quantity < 1 or quantity > 99:
            return self._portal_store_nonmutating_result(action_id, GameResult.fail("Quantity must be between 1 and 99."))
        item, _ = self._find_shop_offer(twitch_id, str(item_id))
        if not item or str(item["id"]) != str(item_id):
            return self._portal_store_nonmutating_result(
                action_id,
                GameResult.fail("That item is not in your current Moogle Emporium stock. Refresh the shop and try again."),
            )
        if item["type"] in {"weapon", "armor", "accessory"} and quantity != 1:
            return self._portal_store_nonmutating_result(action_id, GameResult.fail("Equipment is sold one at a time."))
        cost = int(item.get("price", 0)) * quantity
        with self.db.tx() as conn:
            fresh = conn.execute("SELECT gil FROM players WHERE twitch_id=?", (twitch_id,)).fetchone()
            gil = int(fresh["gil"] if fresh else 0)
            if gil < cost:
                result = GameResult.fail(f"You need {cost:,} gil, but only have {gil:,}. Kupo-poor.", gil=gil)
                self._portal_action_store_sql(conn, action_id, result)
                return result
            conn.execute("UPDATE players SET gil=gil-?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (cost, twitch_id))
            conn.execute(
                "INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) "
                "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity",
                (twitch_id, item["id"], quantity),
            )
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil', 'gil', ?, 'portal_shop')", (twitch_id, -cost))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, 'portal_shop')", (twitch_id, item["id"], quantity))
            result = GameResult.success(
                f"Purchased {item['name']} x{quantity} for {cost:,} gil from your current shop rotation.",
                item_id=item["id"], quantity=quantity, cost=cost, gil=gil - cost,
            )
            # Store the mutation result in the same transaction first so replay
            # protection remains atomic even if post-purchase presentation work fails.
            self._portal_action_store_sql(conn, action_id, result)

        unlocked = self._check_achievements(twitch_id)
        if unlocked:
            result.messages.append("Achievement unlocked: " + " | ".join(unlocked))
            with self.db.tx() as conn:
                self._portal_action_store_sql(conn, action_id, result)
        return result

    def portal_sell(self, twitch_id: str, item_id: str, quantity: int, action_id: str) -> GameResult:
        """Replay-safe Portal sale with equipped-copy and item-safety validation."""
        replay = self._portal_action_replay(action_id)
        if replay is not None:
            return replay
        p = self._player(twitch_id)
        if not p:
            return self._portal_store_nonmutating_result(action_id, self._need_recruit())
        if twitch_id in self.encounter_roster or twitch_id in self.raid_roster:
            return self._portal_store_nonmutating_result(
                action_id,
                GameResult.fail("Moogle Emporium sales are locked while you are committed to an active encounter or raid."),
            )
        if quantity < 1 or quantity > 99:
            return self._portal_store_nonmutating_result(action_id, GameResult.fail("Quantity must be between 1 and 99."))
        item = self.data.items.get(str(item_id))
        if not item:
            return self._portal_store_nonmutating_result(action_id, GameResult.fail("Item not found."))
        if item.get("unsellable") or item.get("relic_id"):
            return self._portal_store_nonmutating_result(action_id, GameResult.fail("That item cannot be sold."))
        unit = int(sell_value(item.get("price", 0), item.get("type", "item")))
        with self.db.tx() as conn:
            inventory = conn.execute(
                "SELECT quantity FROM inventory WHERE player_id=? AND item_id=?",
                (twitch_id, item["id"]),
            ).fetchone()
            owned = int(inventory["quantity"] if inventory else 0)
            if owned < quantity:
                result = GameResult.fail(f"You only own {owned} {item['name']}.")
                self._portal_action_store_sql(conn, action_id, result)
                return result
            equipment = conn.execute(
                "SELECT weapon_id,armor_id,accessory_id FROM equipment WHERE player_id=?",
                (twitch_id,),
            ).fetchone()
            equipped = bool(equipment and item["id"] in {equipment["weapon_id"], equipment["armor_id"], equipment["accessory_id"]})
            if equipped and owned - quantity < 1:
                result = GameResult.fail(f"Unequip {item['name']} before selling your last equipped copy.")
                self._portal_action_store_sql(conn, action_id, result)
                return result
            proceeds = unit * quantity
            conn.execute("UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?", (quantity, twitch_id, item["id"]))
            conn.execute("UPDATE players SET gil=gil+?,updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?", (proceeds, twitch_id))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, 'portal_sell')", (twitch_id, item["id"], -quantity))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil', 'gil', ?, 'portal_sell')", (twitch_id, proceeds))
            fresh = conn.execute("SELECT gil FROM players WHERE twitch_id=?", (twitch_id,)).fetchone()
            gil_after = int(fresh["gil"] if fresh else int(p["gil"]) + proceeds)
            result = GameResult.success(
                f"Sold {item['name']} x{quantity} for {proceeds:,} gil.",
                item_id=item["id"], quantity=quantity, proceeds=proceeds, gil=gil_after,
            )
            self._portal_action_store_sql(conn, action_id, result)
            return result

    def inspect_item(self, twitch_id: str, item_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        item = self._find_by_name_or_id(self.data.items, item_query)
        if not item:
            return GameResult.fail("Item not found.")
        upgrade = self._upgrade_level(twitch_id, item["id"])
        scale = 1 + self._forge_bonus_per_level() * upgrade
        bonuses = ", ".join(f"{k.upper()} +{int(round(v * scale))}" for k, v in item.get("bonuses", {}).items()) or "no stat bonuses"
        owned = self._inventory_qty(twitch_id, item["id"])
        forge = f" | Forge +{upgrade}" if item["type"] in {"weapon", "armor", "accessory"} else ""
        jobs = ""
        if item.get("allowed_jobs"):
            jobs = " | Jobs: " + ", ".join(self.data.jobs[j]["name"] for j in item["allowed_jobs"] if j in self.data.jobs)
        desc = f" | {item['description']}" if item.get("description") else ""
        return GameResult.success(f"{item['name']} [{item['rarity'].title()} {item['type'].title()}] | Owned: {owned}{forge} | {bonuses}{jobs} | Value: {item.get('price', 0):,} gil{desc}")

    def gil(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        return GameResult.success(f"{p['display_name']} has {p['gil']:,} gil and {p['hunt_seals']:,} Hunt Seals. Please spend at least one of those irresponsibly.")

    # ---------- Fellowship ----------
    def fellowship(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        guild = self.fellowship_system.public_snapshot()
        member = self.fellowship_system.member_snapshot(twitch_id)
        progress = guild["level_progress"]
        if progress["maxed"]:
            level_text = f"{guild['level_label']} MAX | {guild['renown']:,} Renown"
        else:
            level_text = f"{guild['level_label']} | {guild['renown']:,}/{int(progress['next']):,} Renown"
        project = guild.get("active_project")
        project_text = "No active project"
        if project:
            complete = sum(1 for req in project["requirements"] if req["complete"])
            project_text = f"{project['name']} ({complete}/{len(project['requirements'])} requirements)"
        rank = member["rank"]
        rank_text = f"{rank['name']} — {member['renown']:,} personal Renown"
        if rank.get("next_threshold") is not None:
            rank_text += f" | next {rank['next_name']} at {int(rank['next_threshold']):,}"
        founding = " | Founding Member" if member["founding_member"] else ""
        return GameResult.success(
            f"FELLOWSHIP — {level_text} | Members {guild['member_count']} | Weekly Orders {guild['orders']['completed']}/{guild['orders']['total']}",
            f"Your Guild Rank: {rank_text}{founding}",
            f"Active Project: {project_text} | !project · !orders · !facilities · !contributions",
        )

    def fellowship_project(self) -> GameResult:
        project = self.fellowship_system.project_snapshot()
        if not project:
            available = self.fellowship_system.available_projects()
            names = ", ".join(p["name"] for p in available[:5]) or "none currently unlocked"
            return GameResult.success(
                "FELLOWSHIP PROJECT — No active project.",
                f"Unlocked: {names}. The streamer chooses with !fellowshipproject <facility>.",
            )
        parts = []
        for req in project["requirements"]:
            parts.append(f"{req['label']} {int(req['current']):,}/{int(req['target']):,}{' ✓' if req['complete'] else ''}")
        return GameResult.success(
            f"FELLOWSHIP PROJECT — {project['name']} | " + " | ".join(parts[:4]),
            "Contribute with !contribute gil <amount> or !contribute <amount> <item>. Gameplay requirements advance automatically.",
        )

    def fellowship_orders(self) -> GameResult:
        orders = self.fellowship_system.orders_snapshot()
        parts = [f"{o['name']} {o['progress']}/{o['target']}{' ✓' if o['complete'] else ''}" for o in orders["orders"]]
        return GameResult.success(
            f"FELLOWSHIP ORDERS [{orders['period']}] — " + " | ".join(parts),
            "Orders advance automatically from normal Guild activity and reset with the weekly rotation.",
        )

    def fellowship_deeds(self) -> GameResult:
        deeds = self.fellowship_system.deeds_snapshot()
        complete = [d for d in deeds if d["complete"]]
        open_deeds = sorted((d for d in deeds if not d["complete"]), key=lambda d: (d["target"] - d["progress"], d["target"]))
        nearby = " | ".join(f"{d['name']} {d['progress']}/{d['target']}" for d in open_deeds[:4]) or "All current Deeds complete."
        return GameResult.success(
            f"FELLOWSHIP DEEDS — {len(complete)}/{len(deeds)} complete | {nearby}",
            "Permanent community milestones; unlike Orders, Deeds never reset.",
        )

    def fellowship_facilities(self) -> GameResult:
        guild = self.fellowship_system.public_snapshot()
        parts = [f"{f['name']} T{f['tier']}/{f['max_tier']}" for f in guild["facilities"]]
        effects = guild["effects"]
        return GameResult.success(
            "FELLOWSHIP FACILITIES — " + " | ".join(parts),
            f"Current benefits: Camp -{int(effects['camp_reduction']*100)}% time | Forge -{int(effects['forge_discount']*100)}% Gil | Combat JP +{int(effects['jp_bonus']*100)}% | Shop refresh -{int(effects['shop_refresh_reduction']*100)}% time.",
        )

    def fellowship_contributions(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        member = self.fellowship_system.member_snapshot(twitch_id)
        rank = member["rank"]
        return GameResult.success(
            f"FELLOWSHIP RECORD — {p['display_name']} | Guild Rank: {rank['name']} | {member['renown']:,} Renown",
            f"Projects {member['projects_contributed']} | Gil donated {member['gil_donated']:,} | Materials donated {member['materials_donated']:,} | Orders {member['orders_participated']} | Deeds {member['deeds_assisted']}",
        )

    def fellowship_rank(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        member = self.fellowship_system.member_snapshot(twitch_id)
        rank = member["rank"]
        if rank["maxed"]:
            progress = "Current v1.1 rank cap reached."
        else:
            remaining = int(rank["next_threshold"]) - int(member["renown"])
            progress = f"{remaining:,} Renown to {rank['next_name']}."
        founding = " Founding Member." if member["founding_member"] else ""
        return GameResult.success(f"GUILD RANK — {p['display_name']}: {rank['name']} | {member['renown']:,} Renown. {progress}{founding}")

    def contribute_fellowship(self, twitch_id: str, contribution: str) -> GameResult:
        ok, message, notes = self.fellowship_system.contribute(twitch_id, contribution)
        if not ok:
            return GameResult.fail(message)
        result = GameResult.success(message, *notes[:2])
        unlocked = self._check_achievements(twitch_id)
        if unlocked:
            result.messages.append("Achievement unlocked: " + " | ".join(unlocked))
        return result

    def set_fellowship_project(self, project_query: str) -> GameResult:
        ok, message, project = self.fellowship_system.set_active_project(project_query)
        if not ok:
            return GameResult.fail(message)
        requirements = " | ".join(f"{r['label']} {r['current']}/{r['target']}" for r in (project or {}).get("requirements", [])[:4])
        return GameResult.success(message, requirements if requirements else "Project ready for contributions.")

    @_state_guard
    def ready_all_players(self) -> GameResult:
        """Streamer recovery tool: restore every player to a non-resting, fully healed state.

        Active combat owns separate in-memory HP/resource state, so this command
        intentionally refuses to run while an encounter or raid is active. The
        streamer can resolve/clear that combat first, then perform the global
        readiness reset without creating split-brain combat state.
        """
        if self.active_encounter or self.active_boss:
            return GameResult.fail(
                "READY ALL blocked — active combat is still running. Resolve or clear the current encounter/raid first, then use !readyall."
            )

        players = self.db.all("SELECT * FROM players ORDER BY twitch_id")
        if not players:
            return GameResult.success("READY ALL — No recruited players to restore.", players_reset=0)

        now = int(time.time())
        ko_count = 0
        resting_count = 0
        resource_users = 0
        for p in players:
            player_id = str(p["twitch_id"])
            if int(p["current_hp"] or 0) <= 0 and p["current_job"] != "adventurer":
                ko_count += 1
            if int(p["camp_until"] or 0) > now:
                resting_count += 1

            max_hp = self._max_hp(p)
            updates = ["current_hp=?", "camp_until=0", "updated_at=CURRENT_TIMESTAMP"]
            params: list[int | str] = [max_hp]
            job = self.data.jobs.get(p["current_job"])
            if job:
                stats = self._stats(p, job)
                pools = battle_resource_pools(stats, job)
                if int(pools["max_mp"]) > 0:
                    updates.append("current_mp=?")
                    params.append(int(pools["max_mp"]))
                if int(pools["max_ap"]) > 0:
                    updates.append("current_ap=?")
                    params.append(int(pools["max_ap"]))
                if int(pools["max_mp"]) > 0 or int(pools["max_ap"]) > 0:
                    resource_users += 1
            params.append(player_id)
            self.db.execute(
                f"UPDATE players SET {', '.join(updates)} WHERE twitch_id=?",
                tuple(params),
            )

        return GameResult.success(
            f"READY ALL — {len(players)} players restored to full HP and applicable MP/AP; "
            f"{resting_count} camp timer(s) cleared and {ko_count} KO hero(es) revived.",
            players_reset=len(players),
            camps_cleared=resting_count,
            ko_revived=ko_count,
            resource_users_restored=resource_users,
        )

    @_state_guard
    def clear_all_adventures(self) -> GameResult:
        """Streamer emergency recovery: abandon every active non-raid adventure.

        This is intentionally narrower than ``!resettimers`` and safer than a
        database reset. It clears the shared field/Rally encounter, all timed
        Hunt assignments, every persisted Wayfarer Solo Venture, and every
        active v1.2 Expedition. Player progression, inventory, current persisted
        HP/MP/AP, cooldowns, camps, shops, achievements, titles, secured
        Expedition results/exploration progress, and any active raid/world boss
        are left untouched.

        Solo Venture combat writes its vitals/resources after every completed
        round, so deleting an orphaned expedition returns the player to the
        last successfully persisted combat state instead of trying to trust a
        potentially malformed in-flight payload. Unbanked Solo Venture spoils
        and unresolved Hunt rewards are abandoned by design.
        """
        solo_rows = self.db.one("SELECT COUNT(*) AS n FROM solo_expeditions")
        solo_count = int(solo_rows["n"] or 0) if solo_rows else 0
        expedition_rows = self.db.one("SELECT COUNT(*) AS n FROM player_expeditions")
        expedition_count = int(expedition_rows["n"] or 0) if expedition_rows else 0
        hunt_count = len(self.active_hunts)

        encounter_count = 1 if self.active_encounter else 0
        encounter_name = ""
        if self.active_encounter:
            monster = self.data.monsters.get(str(self.active_encounter.get("monster_id") or ""), {})
            encounter_name = str(monster.get("name") or self.active_encounter.get("kind") or "field encounter")

        # Schema 5 makes Solo Ventures authoritative rows, so a single delete
        # is sufficient even when a row can no longer be rendered by Portal.
        self.db.execute("DELETE FROM solo_expeditions")

        # v1.2 Expeditions are authoritative database rows as well. Emergency
        # clearing abandons unbanked cache but keeps already-secured region
        # exploration and persistent result history untouched.
        self.db.execute("DELETE FROM player_expeditions")

        # Timed Hunts live in the runtime checkpoint. Clearing the in-memory
        # map inside @_state_guard atomically persists the empty assignment set.
        self.active_hunts.clear()

        # ``active_encounter`` is the shared non-raid field/Rally battle slot.
        # Raids/world bosses are stored separately in active_boss/raid_roster
        # and are deliberately not touched by this recovery command.
        self.active_encounter = None
        self.encounter_roster.clear()

        # Avoid presenting an old completed adventure card immediately after an
        # emergency clear. This cache is intentionally ephemeral.
        self._last_adventure_result = None
        if encounter_count:
            self._last_battle_history = None

        total = solo_count + expedition_count + hunt_count + encounter_count
        if total == 0:
            return GameResult.success(
                "ADVENTURES CLEAR — No active field encounter, timed Hunt, Solo Venture, or Expedition was found.",
                adventures_cleared=0,
                encounters_cleared=0,
                hunts_cleared=0,
                solo_ventures_cleared=0,
                expeditions_cleared=0,
                cooldowns_unchanged=True,
                raid_unchanged=bool(self.active_boss),
            )

        pieces: list[str] = []
        if encounter_count:
            pieces.append(f"1 field encounter ({encounter_name})")
        if hunt_count:
            pieces.append(f"{hunt_count} timed Hunt assignment{'s' if hunt_count != 1 else ''}")
        if solo_count:
            pieces.append(f"{solo_count} Solo Venture{'s' if solo_count != 1 else ''}")
        if expedition_count:
            pieces.append(f"{expedition_count} Expedition{'s' if expedition_count != 1 else ''}")
        summary = ", ".join(pieces)
        return GameResult.success(
            f"ADVENTURES CLEARED — abandoned {summary}.",
            "Player progression/inventory and current persisted vitals were preserved. "
            "Adventure cooldowns and any active raid/world boss were left untouched; use !resettimers separately if you also want cooldowns cleared.",
            adventures_cleared=total,
            encounters_cleared=encounter_count,
            hunts_cleared=hunt_count,
            solo_ventures_cleared=solo_count,
            expeditions_cleared=expedition_count,
            cooldowns_unchanged=True,
            raid_unchanged=bool(self.active_boss),
        )

    @_state_guard
    def reset_all_player_timers(self) -> GameResult:
        """Streamer recovery tool: clear persistent player-side timers globally.

        This resets Venture/Daily/Hunt cooldowns, cancels camp countdowns, and
        expires personal shop rotations. Active encounter/raid rally and round
        deadlines are intentionally not changed; those have dedicated owner
        recovery commands and are part of the combat checkpoint.
        """
        cooldowns = self.db.one("SELECT COUNT(*) AS n FROM cooldowns")
        camps = self.db.one("SELECT COUNT(*) AS n FROM players WHERE camp_until > 0")
        shops = self.db.one("SELECT COUNT(*) AS n FROM player_shops")
        cooldown_count = int(cooldowns["n"] or 0) if cooldowns else 0
        camp_count = int(camps["n"] or 0) if camps else 0
        shop_count = int(shops["n"] or 0) if shops else 0

        self.db.execute("DELETE FROM cooldowns")
        self.db.execute(
            "UPDATE players SET camp_until=0, updated_at=CURRENT_TIMESTAMP WHERE camp_until <> 0"
        )
        # Removing cached shop rows makes the next !shop request roll fresh stock
        # immediately instead of waiting for the previous refresh deadline.
        self.db.execute("DELETE FROM player_shops")

        active_note = " Active combat timers were left untouched." if (self.active_encounter or self.active_boss) else ""
        return GameResult.success(
            f"TIMERS RESET — cleared {cooldown_count} gameplay cooldown(s), {camp_count} camp timer(s), "
            f"and {shop_count} shop refresh timer(s).{active_note}",
            cooldowns_cleared=cooldown_count,
            camps_cleared=camp_count,
            shops_cleared=shop_count,
            active_combat_unchanged=bool(self.active_encounter or self.active_boss),
        )

    def economy_report(self, days: int = 7) -> GameResult:
        """Owner-facing economy pulse from the authoritative transaction ledger."""
        window = max(1, min(90, int(days)))
        snapshot = self.db.economy_snapshot(window)
        top_source = snapshot.get("top_source") or ("none", 0)
        top_sink = snapshot.get("top_sink") or ("none", 0)
        net = int(snapshot["earned"]) - int(snapshot["spent"])
        sign = "+" if net >= 0 else ""
        return GameResult.success(
            f"GOLD SAUCER ECONOMY [{window}d] — circulation {snapshot['circulating_gil']:,}g across "
            f"{snapshot['players']:,} heroes | +{snapshot['earned']:,}g earned / -{snapshot['spent']:,}g spent | net {sign}{net:,}g",
            f"Top source: {top_source[0]} +{top_source[1]:,}g | Top sink: {top_sink[0]} -{top_sink[1]:,}g | "
            f"transactions {snapshot['transactions']:,}",
        )

    def sell(self, twitch_id: str, item_query: str, quantity: int = 1) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before selling inventory.")
        if quantity < 1 or quantity > 99:
            return GameResult.fail("Quantity must be between 1 and 99.")
        item = self._find_by_name_or_id(self.data.items, item_query)
        if not item:
            return GameResult.fail("Item not found.")
        if item.get("unsellable") or item.get("relic_id"):
            return GameResult.fail("The Guild blacksmith refuses to buy a Relic weapon. Apparently history has paperwork.")
        owned = self._inventory_qty(twitch_id, item["id"])
        if owned < quantity:
            return GameResult.fail(f"You only own {owned} {item['name']}.")
        unit = sell_value(item.get("price", 0), item["type"])
        proceeds = unit * quantity
        with self.db.tx() as conn:
            conn.execute("UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?", (quantity, twitch_id, item["id"]))
            conn.execute("UPDATE players SET gil=gil+? WHERE twitch_id=?", (proceeds, twitch_id))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, 'sell')", (twitch_id, item["id"], -quantity))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil', 'gil', ?, 'sell')", (twitch_id, proceeds))
        return GameResult.success(f"Sold {item['name']} x{quantity} for {proceeds:,} gil.")

    # ---------- bestiary / achievements / leaderboards ----------
    # ---------- blacksmith / crafting / forge / relics ----------
    def blacksmith(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        known = sum(1 for r in self.data.recipes.values() if self._recipe_known(twitch_id, r))
        relic_done = int(p["relics_completed"])
        return GameResult.success(
            f"Guild Blacksmith — Recipes {known}/{len(self.data.recipes)} | Crafts {p['crafts']} | Forge upgrades {p['forge_upgrades']} | Zenith Relics {relic_done}",
            "Use !recipes, !recipe <name>, !craft <recipe> [qty], !upgrade <gear>, !relics, and !relic <name>.",
        )

    def recipes(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        known = [r for r in self.data.recipes.values() if self._recipe_known(twitch_id, r)]
        known.sort(key=lambda r: (r.get("min_level", 1), r["name"]))
        if not known:
            return GameResult.success("Your recipe book is empty. The blacksmith is trying not to look judgmental.")
        parts = []
        for recipe in known[:12]:
            state = "✓" if p["level"] >= recipe.get("min_level", 1) else f"Lv.{recipe.get('min_level',1)}"
            parts.append(f"{recipe['name']} [{state}]")
        hidden = len(self.data.recipes) - len(known)
        return GameResult.success("Recipes — " + " | ".join(parts) + (" | ..." if len(known) > 12 else ""), f"Known {len(known)}/{len(self.data.recipes)}; {hidden} rare recipes remain undiscovered. Inspect with !recipe <name>.")

    def recipe_info(self, twitch_id: str, recipe_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        recipe = self._find_by_name_or_id(self.data.recipes, recipe_query)
        if not recipe:
            return GameResult.fail("Recipe not found.")
        known = self._recipe_known(twitch_id, recipe)
        if not known:
            return GameResult.fail(f"{recipe['name']} is an undiscovered recipe. Certain monsters can teach it after being hit enough times.")
        mats = ", ".join(f"{self.data.items[m['item_id']]['name']} x{m['quantity']}" for m in recipe.get("materials", [])) or "none"
        out = recipe["output"]
        cost = []
        if recipe.get("gil", 0): cost.append(f"{recipe['gil']:,} gil")
        if recipe.get("seal_cost", 0): cost.append(f"{recipe['seal_cost']} seals")
        state = "READY" if self._recipe_affordable(twitch_id, recipe, 1)[0] and p["level"] >= recipe.get("min_level", 1) else "missing requirements/materials"
        return GameResult.success(f"{recipe['name']} — Makes {self.data.items[out['item_id']]['name']} x{out.get('quantity',1)} | Lv.{recipe.get('min_level',1)} | {state}", f"Cost: {', '.join(cost) if cost else 'no currency'} | Materials: {mats}")

    def craft(self, twitch_id: str, recipe_query: str, quantity: int = 1) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before crafting supplies.")
        if quantity < 1 or quantity > 20:
            return GameResult.fail("Craft quantity must be between 1 and 20.")
        recipe = self._find_by_name_or_id(self.data.recipes, recipe_query)
        if not recipe:
            return GameResult.fail("Recipe not found. Use !recipes to inspect your recipe book.")
        if not self._recipe_known(twitch_id, recipe):
            return GameResult.fail(f"You haven't learned {recipe['name']} yet.")
        if p["level"] < recipe.get("min_level", 1):
            return GameResult.fail(f"{recipe['name']} requires Character Lv.{recipe.get('min_level',1)}.")
        ok, missing = self._recipe_affordable(twitch_id, recipe, quantity)
        if not ok:
            return GameResult.fail("Cannot craft — " + "; ".join(missing[:6]))
        total_gil = recipe.get("gil", 0) * quantity
        total_seals = recipe.get("seal_cost", 0) * quantity
        out = recipe["output"]
        out_qty = out.get("quantity", 1) * quantity
        with self.db.tx() as conn:
            for mat in recipe.get("materials", []):
                need = mat["quantity"] * quantity
                conn.execute("UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?", (need, twitch_id, mat["item_id"]))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, ?)", (twitch_id, mat["item_id"], -need, f"craft:{recipe['id']}"))
            conn.execute("UPDATE players SET gil=gil-?, hunt_seals=hunt_seals-?, crafts=crafts+? WHERE twitch_id=?", (total_gil, total_seals, quantity, twitch_id))
            if total_gil:
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,?)", (twitch_id, -total_gil, f"craft:{recipe['id']}"))
            if total_seals:
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'hunt_seals','hunt_seals',?,?)", (twitch_id, -total_seals, f"craft:{recipe['id']}"))
            conn.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (twitch_id, out["item_id"], out_qty))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, ?)", (twitch_id, out["item_id"], out_qty, f"craft:{recipe['id']}"))
        fellowship_notes = self.fellowship_system.record_activity(
            twitch_id, "craft", amount=quantity, event_key=f"craft:{twitch_id}:{time.time_ns()}"
        )
        unlocked = self._check_achievements(twitch_id)
        msg = f"CRAFTED — {self.data.items[out['item_id']]['name']} x{out_qty}. The blacksmith nods, which is apparently a five-star review."
        messages = [msg]
        if unlocked:
            messages.append("Achievement unlocked: " + " | ".join(unlocked))
        messages.extend(fellowship_notes[:2])
        return GameResult.success(*messages)

    def upgrade(self, twitch_id: str, item_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before forging equipment.")
        item = self._find_by_name_or_id(self.data.items, item_query)
        if not item or item["type"] not in {"weapon", "armor", "accessory"}:
            return GameResult.fail("Only weapons, armor, and accessories can be forged.")
        if self._inventory_qty(twitch_id, item["id"]) <= 0:
            return GameResult.fail(f"You don't own {item['name']}.")
        current = self._upgrade_level(twitch_id, item["id"])
        if current >= len(self.data.forge):
            return GameResult.fail(f"{item['name']} is already +{current}, the current forge maximum.")
        rule = self.data.forge[current]
        forge_gil = self.fellowship_system.effective_forge_gil(rule.get("gil", 0))
        missing = []
        if p["gil"] < forge_gil:
            missing.append(f"{forge_gil:,} gil ({p['gil']:,} owned)")
        for mat in rule.get("materials", []):
            have = self._inventory_qty(twitch_id, mat["item_id"])
            if have < mat["quantity"]:
                missing.append(f"{self.data.items[mat['item_id']]['name']} x{mat['quantity']} ({have} owned)")
        if missing:
            return GameResult.fail(f"Forge +{current+1} requires — " + "; ".join(missing))
        with self.db.tx() as conn:
            for mat in rule.get("materials", []):
                conn.execute("UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?", (mat["quantity"], twitch_id, mat["item_id"]))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, 'forge')", (twitch_id, mat["item_id"], -mat["quantity"]))
            conn.execute("UPDATE players SET gil=gil-?, forge_upgrades=forge_upgrades+1 WHERE twitch_id=?", (forge_gil, twitch_id))
            if forge_gil:
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,'forge')", (twitch_id, -forge_gil))
            conn.execute("INSERT INTO item_upgrades(player_id,item_id,upgrade_level) VALUES (?,?,?) ON CONFLICT(player_id,item_id) DO UPDATE SET upgrade_level=excluded.upgrade_level", (twitch_id, item["id"], current + 1))
        fellowship_notes = self.fellowship_system.record_activity(
            twitch_id, "forge", event_key=f"forge:{twitch_id}:{item['id']}:{current+1}:{time.time_ns()}"
        )
        unlocked = self._check_achievements(twitch_id)
        pct = int(self._forge_bonus_per_level() * (current + 1) * 100)
        msg = f"FORGE COMPLETE — {item['name']} is now +{current+1}. Equipment stat bonuses are now +{pct}% over base."
        messages = [msg]
        if forge_gil < int(rule.get("gil", 0)):
            messages.append(f"Workshop benefit — forge fee reduced to {forge_gil:,} Gil.")
        if unlocked:
            messages.append("Achievement unlocked: " + " | ".join(unlocked))
        messages.extend(fellowship_notes[:2])
        return GameResult.success(*messages)

    def sealshop(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        stock = sorted(self.data.seal_shop.values(), key=lambda e: (e.get("min_level", 1), e["cost"]))
        parts = []
        for e in stock[:12]:
            state = "✓" if p["level"] >= e.get("min_level", 1) else f"Lv.{e.get('min_level',1)}"
            parts.append(f"{e['name']} {e['cost']}s [{state}]")
        return GameResult.success(f"Guild Quartermaster — You have {p['hunt_seals']} seals | " + " | ".join(parts), "Buy with !sealbuy <item> [qty].")

    def sealbuy(self, twitch_id: str, entry_query: str, quantity: int = 1) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before visiting the Quartermaster.")
        if quantity < 1 or quantity > 20:
            return GameResult.fail("Quantity must be between 1 and 20.")
        entry = self._find_by_name_or_id(self.data.seal_shop, entry_query)
        if not entry:
            # Also allow searching by the actual output item name.
            item = self._find_by_name_or_id(self.data.items, entry_query)
            if item:
                entry = next((e for e in self.data.seal_shop.values() if e["item_id"] == item["id"]), None)
        if not entry:
            return GameResult.fail("The Quartermaster doesn't stock that item.")
        if p["level"] < entry.get("min_level", 1):
            return GameResult.fail(f"{entry['name']} unlocks at Lv.{entry.get('min_level',1)}.")
        cost = entry["cost"] * quantity
        if p["hunt_seals"] < cost:
            return GameResult.fail(f"You need {cost} Hunt Seals but only have {p['hunt_seals']}.")
        out_qty = entry.get("quantity", 1) * quantity
        with self.db.tx() as conn:
            conn.execute("UPDATE players SET hunt_seals=hunt_seals-? WHERE twitch_id=?", (cost, twitch_id))
            conn.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity", (twitch_id, entry["item_id"], out_qty))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'hunt_seals','hunt_seals',?,'seal_shop')", (twitch_id, -cost))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, 'seal_shop')", (twitch_id, entry["item_id"], out_qty))
        return GameResult.success(f"Quartermaster purchase: {self.data.items[entry['item_id']]['name']} x{out_qty} for {cost} Hunt Seals.")

    def relics(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        parts = []
        for relic in self.data.relics.values():
            row = self.db.one("SELECT stage FROM player_relics WHERE player_id=? AND relic_id=?", (twitch_id, relic["id"]))
            stage = int(row["stage"]) if row else 0
            total = len(relic.get("stages", []))
            eligible = self._job_level(twitch_id, relic["job_id"]) >= 50
            state = "ZENITH" if stage >= total else f"{stage}/{total}" if eligible or stage else "locked"
            parts.append(f"{relic['name']} [{state}]")
        return GameResult.success("Relic Arsenal — " + " | ".join(parts), "Inspect with !relic <name>; advance a ready stage with !awaken <name>.")

    def relic(self, twitch_id: str, relic_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        relic = self._find_by_name_or_id(self.data.relics, relic_query)
        if not relic:
            return GameResult.fail("Relic not found. Use !relics to inspect the arsenal.")
        row = self.db.one("SELECT stage FROM player_relics WHERE player_id=? AND relic_id=?", (twitch_id, relic["id"]))
        stage = int(row["stage"]) if row else 0
        total = len(relic["stages"])
        if stage >= total:
            final_item = relic["stages"][-1]["reward_item"]
            return GameResult.success(f"{relic['name']} — ZENITH COMPLETE | Final weapon: {self.data.items[final_item]['name']}")
        step = relic["stages"][stage]
        met, missing = self._requirements_met(twitch_id, step.get("requirements", []))
        cost_missing = self._cost_missing(twitch_id, step.get("cost", {}))
        cost_text = self._cost_text(step.get("cost", {}))
        status = "READY TO AWAKEN" if met and not cost_missing else "IN PROGRESS"
        detail = missing + cost_missing
        return GameResult.success(f"{relic['name']} — Stage {stage+1}/{total}: {step['name']} | {status}", f"Requirements/Cost: {'; '.join(detail) if detail else cost_text}. Reward: {self.data.items[step['reward_item']]['name']}")

    def awaken_relic(self, twitch_id: str, relic_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before advancing a Relic.")
        relic = self._find_by_name_or_id(self.data.relics, relic_query)
        if not relic:
            return GameResult.fail("Relic not found.")
        row = self.db.one("SELECT stage FROM player_relics WHERE player_id=? AND relic_id=?", (twitch_id, relic["id"]))
        stage = int(row["stage"]) if row else 0
        total = len(relic["stages"])
        if stage >= total:
            return GameResult.fail(f"{relic['name']} is already at Zenith.")
        step = relic["stages"][stage]
        met, missing = self._requirements_met(twitch_id, step.get("requirements", []))
        missing.extend(self._cost_missing(twitch_id, step.get("cost", {})))
        if not met or missing:
            return GameResult.fail("Relic stage not ready — " + "; ".join(missing[:8]))
        cost = step.get("cost", {})
        with self.db.tx() as conn:
            for mat in cost.get("items", []):
                conn.execute("UPDATE inventory SET quantity=quantity-? WHERE player_id=? AND item_id=?", (mat["quantity"], twitch_id, mat["item_id"]))
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, ?)", (twitch_id, mat["item_id"], -mat["quantity"], f"relic:{relic['id']}"))
            gil = cost.get("gil", 0)
            seals = cost.get("hunt_seals", 0)
            conn.execute("UPDATE players SET gil=gil-?, hunt_seals=hunt_seals-? WHERE twitch_id=?", (gil, seals, twitch_id))
            if gil:
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,?)", (twitch_id, -gil, f"relic:{relic['id']}"))
            if seals:
                conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'hunt_seals','hunt_seals',?,?)", (twitch_id, -seals, f"relic:{relic['id']}"))
            reward = step["reward_item"]
            conn.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,1) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=quantity+1", (twitch_id, reward))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, 1, ?)", (twitch_id, reward, f"relic:{relic['id']}"))
            completed = stage + 1 >= total
            conn.execute("INSERT INTO player_relics(player_id,relic_id,stage,completed_at) VALUES (?,?,?,CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END) ON CONFLICT(player_id,relic_id) DO UPDATE SET stage=excluded.stage, completed_at=CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE player_relics.completed_at END", (twitch_id, relic["id"], stage + 1, completed, completed))
            if completed:
                conn.execute("UPDATE players SET relics_completed=relics_completed+1 WHERE twitch_id=?", (twitch_id,))
        reward_name = self.data.items[step["reward_item"]]["name"]
        unlocked = self._check_achievements(twitch_id)
        msg = f"RELIC AWAKENED — {relic['name']} advances to Stage {stage+1}/{total}: {step['name']}. Obtained {reward_name}."
        if stage + 1 >= total:
            msg += " ZENITH COMPLETE. The blacksmith has stopped pretending this is normal equipment."
        if unlocked:
            return GameResult.success(msg, "Achievement unlocked: " + " | ".join(unlocked))
        return GameResult.success(msg)

    def bestiary(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        rows = self.db.all("SELECT monster_id, defeats FROM bestiary WHERE player_id=? ORDER BY defeats DESC, monster_id", (twitch_id,))
        if not rows:
            return GameResult.success("Bestiary: 0 discoveries. The monsters remain blissfully undocumented.")
        entries = [f"{self.data.monsters[r['monster_id']]['name']} x{r['defeats']}" for r in rows[:10] if r["monster_id"] in self.data.monsters]
        return GameResult.success(f"Bestiary {len(rows)}/{len(self.data.monsters)} — " + " | ".join(entries))

    def achievements(self, twitch_id: str, category: str | None = None) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        newly = self._check_achievements(twitch_id)
        rows = self.db.all(
            "SELECT achievement_id, unlocked_at FROM achievements WHERE player_id=? ORDER BY unlocked_at DESC",
            (twitch_id,),
        )
        unlocked_ids = {row["achievement_id"] for row in rows}
        earned_points = sum(
            int(self.data.achievements[aid].get("points", 0))
            for aid in unlocked_ids if aid in self.data.achievements
        )
        total_points = sum(int(a.get("points", 0)) for a in self.data.achievements.values())
        query = (category or "").strip().lower()
        pool = list(self.data.achievements.values())
        if query and query not in {"all", "earned"}:
            pool = [a for a in pool if a.get("category", "").lower() == query]
        if query == "earned":
            pool = [a for a in pool if a["id"] in unlocked_ids]
        visible = []
        for ach in pool:
            unlocked = ach["id"] in unlocked_ids
            if ach.get("secret") and not unlocked:
                continue
            visible.append((unlocked, ach))
        visible.sort(key=lambda pair: (not pair[0], -int(pair[1].get("points", 0)), pair[1]["name"].lower()))
        entries = []
        for unlocked, ach in visible[:7]:
            name = ach.get("reveal_name", ach["name"]) if unlocked else ach["name"]
            marker = "✓" if unlocked else "·"
            entries.append(f"{marker} {name} [{ach.get('tier','bronze').title()}]")
        messages = [
            f"Achievements {len(unlocked_ids)}/{len(self.data.achievements)} | {earned_points:,}/{total_points:,} AP",
            " | ".join(entries) if entries else "No achievements match that category yet.",
            "Use !achievements <category|earned> or !achievement <name> for progress. Portal has the full gallery.",
        ]
        if newly:
            messages.append("New unlocks: " + " | ".join(newly[:3]))
        return GameResult.success(*messages)

    def achievement(self, twitch_id: str, achievement_query: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        self._check_achievements(twitch_id)
        achievement = self._find_by_name_or_id(self.data.achievements, achievement_query)
        if not achievement:
            return GameResult.fail("Achievement not found. Try !achievements <category> or the Adventurer Portal gallery.")
        unlocked = bool(self.db.one(
            "SELECT 1 FROM achievements WHERE player_id=? AND achievement_id=?",
            (twitch_id, achievement["id"]),
        ))
        if achievement.get("secret") and not unlocked:
            return GameResult.success("SECRET ACHIEVEMENT — ??? | Keep adventuring. The Guild refuses to spoil this particular mistake.")
        value = self._requirement_value(twitch_id, achievement["condition"])
        target = int(achievement["condition"].get("amount", 1))
        name = achievement.get("reveal_name", achievement["name"]) if unlocked else achievement["name"]
        reward = self.data.titles.get(achievement.get("reward_title"))
        state = "UNLOCKED" if unlocked else f"PROGRESS {min(value, target):,}/{target:,}"
        reward_text = f" | Title: {reward['name']}" if reward else ""
        return GameResult.success(
            f"{name} [{achievement.get('tier','bronze').upper()} · {achievement.get('category','General')}] — {state}",
            f"{achievement['description']} | {self._requirement_text(achievement['condition'], value)}{reward_text}",
        )

    def records(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()

        stats = {
            row["metric"]: int(row["value"])
            for row in self.db.all(
                "SELECT metric, value FROM player_record_stats WHERE player_id=?",
                (twitch_id,),
            )
        }
        hunts = self.db.one(
            "SELECT COALESCE(SUM(clears),0) AS n FROM player_hunts WHERE player_id=?",
            (twitch_id,),
        )
        bosses = self.db.one(
            "SELECT COALESCE(SUM(clears),0) AS n FROM player_boss_clears WHERE player_id=?",
            (twitch_id,),
        )
        jobs_mastered = self.db.one(
            "SELECT COUNT(*) AS n FROM player_jobs WHERE player_id=? AND level>=50",
            (twitch_id,),
        )
        economy = self.db.one(
            """
            SELECT
              COALESCE(SUM(CASE WHEN kind='gil' AND amount>0 THEN amount ELSE 0 END),0) AS gil_earned,
              COALESCE(-SUM(CASE WHEN kind='gil' AND amount<0 THEN amount ELSE 0 END),0) AS gil_spent,
              COALESCE(SUM(CASE WHEN kind='item' AND amount>0 THEN amount ELSE 0 END),0) AS items_acquired
            FROM transactions WHERE player_id=?
            """,
            (twitch_id,),
        )
        favorite = self.db.one(
            """
            SELECT job_id, battles, victories FROM player_job_records
            WHERE player_id=? ORDER BY battles DESC, victories DESC, job_id LIMIT 1
            """,
            (twitch_id,),
        )
        victim = self.db.one(
            """
            SELECT monster_id, defeats FROM bestiary
            WHERE player_id=? ORDER BY defeats DESC, monster_id LIMIT 1
            """,
            (twitch_id,),
        )
        nemesis = self.db.one(
            """
            SELECT monster_id, defeats FROM player_monster_records
            WHERE player_id=? AND defeats>0
            ORDER BY defeats DESC, victories ASC, monster_id LIMIT 1
            """,
            (twitch_id,),
        )
        favorite_name = (
            self.data.jobs.get(favorite["job_id"], {}).get("name", "—")
            if favorite
            else self.data.jobs.get(p["current_job"], {}).get("name", "—")
        )
        victim_name = self.data.monsters.get(victim["monster_id"], {}).get("name", "—") if victim else "—"
        nemesis_name = self.data.monsters.get(nemesis["monster_id"], {}).get("name", "None yet") if nemesis else "None yet"
        victim_count_text = f" x{int(victim['defeats']):,}" if victim else ""
        nemesis_count_text = f" ({int(nemesis['defeats']):,} KOs)" if nemesis else ""
        return GameResult.success(
            f"RECORDS — {p['display_name']} | Adventures {int(p['ventures']):,} | Monsters {int(p['monsters_defeated']):,} | Hunts {int(hunts['n'] or 0):,} | Boss Clears {int(bosses['n'] or 0):,} | KOs {int(p['deaths']):,}",
            f"Combat — {stats.get('damage_dealt',0):,} damage | Best Hit {stats.get('best_hit',0):,} | Healing {stats.get('healing_done',0):,} | Revives {int(p['raid_revives']):,} | Limits {int(p['limit_breaks']):,} | Summons {stats.get('summons_called',0):,}",
            f"Career — {int(economy['gil_earned'] or 0):,} gil earned | {int(economy['gil_spent'] or 0):,} spent | {int(economy['items_acquired'] or 0):,} items acquired | Jobs Mastered {int(jobs_mastered['n'] or 0)} | Favorite Job {favorite_name}",
            f"Rivalries — Most defeated: {victim_name}{victim_count_text} | Nemesis: {nemesis_name}{nemesis_count_text}. Full dossier: Adventurer Portal → Records.",
        )

    def leaderboard(self, metric: str = "level") -> GameResult:
        metric = self._norm(metric)
        if metric == "hunts":
            rows = self.db.all("SELECT p.display_name, COALESCE(SUM(h.clears),0) AS score, p.level FROM players p LEFT JOIN player_hunts h ON h.player_id=p.twitch_id GROUP BY p.twitch_id ORDER BY score DESC, p.level DESC LIMIT 5")
        elif metric == "mastery":
            rows = self.db.all("SELECT p.display_name, SUM(CASE WHEN j.level>=50 THEN 1 ELSE 0 END) AS score, p.level FROM players p LEFT JOIN player_jobs j ON j.player_id=p.twitch_id GROUP BY p.twitch_id ORDER BY score DESC, p.level DESC LIMIT 5")
        elif metric == "bosses":
            rows = self.db.all("SELECT p.display_name, COALESCE(SUM(b.clears),0) AS score, p.level FROM players p LEFT JOIN player_boss_clears b ON b.player_id=p.twitch_id GROUP BY p.twitch_id ORDER BY score DESC, p.level DESC LIMIT 5")
        else:
            allowed = {"level": "level", "gil": "gil", "slayer": "monsters_defeated", "deaths": "deaths", "ventures": "ventures", "seals": "hunt_seals", "crafts": "crafts", "forge": "forge_upgrades", "relics": "relics_completed", "rests": "rests", "party": "party_encounters", "revives": "raid_revives", "limits": "limit_breaks"}
            column = allowed.get(metric, "level")
            rows = self.db.all(f"SELECT display_name, {column} AS score, level FROM players ORDER BY {column} DESC, level DESC LIMIT 5")
        if not rows:
            return GameResult.success("Leaderboard: nobody has joined the Guild yet.")
        text = " | ".join(f"#{idx} {r['display_name']} {int(r['score'] or 0):,}" for idx, r in enumerate(rows, 1))
        return GameResult.success(f"Leaderboard [{metric}] — {text}")

    def daily(self, twitch_id: str, subscriber_tier: int = 0) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if self._solo_expedition_load(twitch_id):
            return GameResult.fail("Return or retreat from your Solo Venture before collecting new Daily Guild Provisions.")
        remaining = self._cooldown_remaining(twitch_id, "daily")
        if remaining > 0:
            return GameResult.fail(f"Daily provisions already claimed. Return in {self._format_seconds(remaining)}.")
        gil, provisions, perk = self._daily_reward(twitch_id, subscriber_tier)
        with self.db.tx() as conn:
            self._grant_daily_sql(conn, twitch_id, gil, provisions)
        self._set_cooldown(twitch_id, "daily", 24 * 3600)
        perk_note = ""
        if int(perk["tier"]) > 0:
            perk_note = f" [{perk['label']}: +{perk['gil_bonus_percent']}% Gil, {perk['rolls']} provision rolls]"
        return GameResult.success(
            f"Daily provisions{perk_note}: +{gil} Gil | {self._daily_provision_text(provisions)}.",
            claimed_gil=gil,
            provisions=provisions,
            subscriber_tier=int(perk["tier"]),
            subscriber_label=str(perk["label"]),
        )

    # ---------- monster & boss catalog ----------
    def monsters(self, region_query: str | None = None) -> GameResult:
        if region_query:
            region = self._find_by_name_or_id(self.data.regions, region_query)
            if not region:
                return GameResult.fail("Region not found. Use !regions to see available destinations.")
            entries = []
            for encounter in sorted(region["encounters"], key=lambda e: self.data.monsters[e["monster_id"]]["level"]):
                m = self.data.monsters[encounter["monster_id"]]
                entries.append(f"{m['name']} L{m['level']}")
            chunks = [entries[i:i+8] for i in range(0, len(entries), 8)]
            messages = [f"{region['name']} Bestiary — " + " | ".join(chunk) for chunk in chunks]
            return GameResult.success(*messages)
        return GameResult.success(
            f"Monster Catalog — {len(self.data.monsters)} creatures across {len(self.data.regions)} regions.",
            "Use !monsters <region> to list encounters or !monster <name> for details.",
        )

    def monster_info(self, monster_query: str) -> GameResult:
        monster = self._find_by_name_or_id(self.data.monsters, monster_query)
        if not monster:
            return GameResult.fail("Monster not found. Try !monsters <region> to browse the catalog.")
        locations = [r["name"] for r in self.data.regions.values() if any(e["monster_id"] == monster["id"] for e in r["encounters"])]
        drops = [self.data.items[d["item_id"]]["name"] for d in monster.get("drops", []) if d["item_id"] in self.data.items]
        special = monster.get("special", {}).get("name", "—")
        return GameResult.success(
            f"{monster['name']} | Lv.{monster['level']} | HP {monster['hp']:,} | Weakness: {monster.get('weakness','—')} | Signature: {special}",
            "Locations: " + (", ".join(locations) if locations else "Hunt/event only") + " | Drops: " + (", ".join(drops) if drops else "None listed"),
        )

    def bosses(self, tier_query: str | None = None) -> GameResult:
        tiers = ["Primal Boss", "World Boss", "High Boss", "Superboss", "Ultimate Superboss"]
        if tier_query:
            q = self._norm(tier_query)
            aliases = {
                "primal":"Primal Boss", "primals":"Primal Boss",
                "world":"World Boss", "boss":"World Boss",
                "high":"High Boss", "greater":"High Boss",
                "super":"Superboss", "superboss":"Superboss", "superbosses":"Superboss",
                "ultimate":"Ultimate Superboss", "ultimates":"Ultimate Superboss",
            }
            target = aliases.get(q)
            if not target:
                target = next((t for t in tiers if self._norm(t) == q), None)
            if not target:
                return GameResult.fail("Boss tier not found. Use primal, world, high, super, or ultimate.")
            pool = sorted((b for b in self.data.bosses.values() if b.get("tier", "World Boss") == target), key=lambda b: b.get("recommended_level", 1))
            entries = [f"{b['name']} L{b.get('recommended_level','?')} ({b['hp']:,} HP)" for b in pool]
            chunks = [entries[i:i+5] for i in range(0, len(entries), 5)]
            return GameResult.success(*[f"{target} — " + " | ".join(c) for c in chunks])
        counts = {tier: sum(1 for b in self.data.bosses.values() if b.get("tier", "World Boss") == tier) for tier in tiers}
        return GameResult.success(
            f"Raid Board — {len(self.data.bosses)} bosses: " + " | ".join(f"{t}: {counts[t]}" for t in tiers),
            "Browse with !bosses primal | world | high | super | ultimate. Inspect with !bossinfo <name>.",
        )

    def boss_info(self, boss_query: str) -> GameResult:
        boss = self._find_by_name_or_id(self.data.bosses, boss_query)
        if not boss:
            return GameResult.fail("Boss not found. Use !bosses to browse the raid board.")
        drops = [f"{self.data.items[d['item_id']]['name']} ({int(d.get('chance',0)*100)}%)" for d in boss.get("drops", []) if d["item_id"] in self.data.items]
        return GameResult.success(
            f"{boss['name']} [{boss.get('tier','World Boss')}] | Recommended Lv.{boss.get('recommended_level','?')} | HP {boss['hp']:,} | Signature: {boss.get('signature','—')}",
            boss.get("description", "A dangerous raid encounter."),
            "Raid loot: " + (", ".join(drops) if drops else "standard XP and gil only"),
        )

    # ---------- world bosses ----------
    @_state_guard
    def spawn_boss(self, boss_query: str) -> GameResult:
        if self.active_boss:
            return GameResult.fail(f"{self.active_boss['name']} is already menacing the Guild.")
        if self.active_encounter:
            return GameResult.fail("Resolve the current encounter before opening a raid. Even the Guild has scheduling standards.")
        boss = self._find_by_name_or_id(self.data.bosses, boss_query)
        if not boss:
            return GameResult.fail("Boss not found. Use !bosses to browse the raid board.")
        now = int(time.time())
        self.active_boss = dict(boss)
        self.active_boss.update({
            "max_hp": int(boss["hp"]), "current_hp": int(boss["hp"]), "round": 0,
            "state": "rally", "closes_at": now + self.raid_join_seconds, "summon_gauge": 0, "summon_armed": None,
        })
        self.raid_roster.clear()
        self._update_raid_overlay()
        tier = boss.get("tier", "World Boss")
        return GameResult.success(
            f"{tier.upper()} — {boss['name']} has emerged from the Rift! HP {boss['hp']:,} | Recommended Lv.{boss.get('recommended_level','?')} | Signature: {boss.get('signature','Cataclysm')}.",
            f"RAID RALLY OPEN for {self._format_seconds(self.raid_join_seconds)} — type !raid to join. Combat then advances every {self._format_seconds(self.raid_round_seconds)}.",
            raid_spawned=True, boss_id=boss["id"], closes_at=self.active_boss["closes_at"],
        )

    @_state_guard
    def raid_join(self, twitch_id: str) -> GameResult:
        p = self._player(twitch_id)
        if not p:
            return self._need_recruit()
        if not self.active_boss:
            return GameResult.fail("There is no active world boss. Browse potential disasters with !bosses; join the next rally with !raid when one appears.")
        if self.active_boss.get("state") != "rally":
            return GameResult.fail("The raid is already in combat. The doors are closed because apparently insurance exists.")
        if int(time.time()) >= self.active_boss.get("closes_at", 0):
            return GameResult.fail("The raid rally has closed; combat is beginning.")
        if p["current_job"] == "adventurer":
            return GameResult.fail("Choose a Job before joining a raid.")
        blocked = self._activity_block(twitch_id)
        if blocked:
            return GameResult.fail(blocked)
        if twitch_id in self.encounter_roster:
            return GameResult.fail("Finish the active encounter before joining a raid.")
        p = self._player(twitch_id)
        if twitch_id in self.raid_roster:
            return GameResult.success(f"{p['display_name']} is already in the raid. Raiders: {len(self.raid_roster)}.")
        job = self.data.jobs[p["current_job"]]
        max_hp = self._max_hp(p)
        self.raid_roster[twitch_id] = {
            "name": p["display_name"], "username": p["username"], "job_id": job["id"],
            "hp": min(int(p["current_hp"]), max_hp), "max_hp": max_hp,
            "damage": 0, "healing": 0, "damage_taken": 0, "best_hit": 0,
            "mitigation": 0, "limit": 0, "limit_armed": False, "ko_counted": False,
            "action": None, "statuses": {}, "defending": False,
            "actions": 0, "abilities_used": 0, "items_used": 0, "defends": 0,
        }
        self._update_raid_overlay()
        warning = ""
        rec = self.active_boss.get("recommended_level")
        if rec and p["level"] < rec - 15:
            warning = " The Guild healer has already started filling out your paperwork."
        return GameResult.success(f"{p['display_name']} joins as {job['name']} against {self.active_boss['name']}! Raiders: {len(self.raid_roster)}.{warning}")

    @_state_guard
    def boss_status(self) -> GameResult:
        if not self.active_boss:
            return GameResult.success("No active world boss. Use !bosses to inspect the Raid Board.")
        boss = self.active_boss
        if boss.get("state") == "rally":
            remaining = max(0, int(boss.get("closes_at",0)) - int(time.time()))
            return GameResult.success(f"{boss['name']} [{boss.get('tier','World Boss')}] | HP {boss['current_hp']:,}/{boss['max_hp']:,} | RAID RALLY {self._format_seconds(remaining)} | Raiders {len(self.raid_roster)} | !raid to join")
        phase = self._boss_phase(boss)
        alive = sum(1 for m in self.raid_roster.values() if m.get("hp",0) > 0)
        enrage = " | ENRAGED" if boss.get("round",0) >= boss.get("enrage_round",99) else ""
        return GameResult.success(f"{boss['name']} | HP {boss['current_hp']:,}/{boss['max_hp']:,} | R{boss['round']} | Phase: {phase['name']} | Heroes {alive}/{len(self.raid_roster)}{enrage}")

    def _initialize_raid_combat(self) -> int:
        """Hydrate Raid participants with the same action/resource state used by Active Battle."""
        combatants = 0
        for pid, meta in list(self.raid_roster.items()):
            self._finish_rest_if_ready(pid)
            p = self._player(pid)
            if not p or p["current_job"] == "adventurer" or int(p["current_hp"]) <= 0:
                meta.update({"hp": 0, "max_hp": 0, "mp": 0, "max_mp": 0, "ap": 0, "max_ap": 0, "action": None, "statuses": {}})
                continue
            job_id = meta.get("job_id") if meta.get("job_id") in self.data.jobs else p["current_job"]
            job = self.data.jobs[job_id]
            effects = self._effects(pid, job_id)
            stats = self._stats(p, job, effects)
            traits = self._equipment_traits(p, job)
            resources = self._resource_state_for(p, job, stats)
            meta.update({
                "name": p["display_name"], "username": p["username"], "job_id": job_id,
                "job_level": self._job_level(pid, job_id), "stance": p["stance"],
                "stats": stats, "effects": effects,
                "status_immune": traits["status_immune"], "status_resist": traits["status_resist"],
                "weapon_element": traits["weapon_element"], "on_hit_status": traits["on_hit_status"],
                "lifesteal": traits["lifesteal"],
                "hp": min(int(p["current_hp"]), int(stats["hp"])), "max_hp": int(stats["hp"]),
                "mp": int(resources["mp"]), "max_mp": int(resources["max_mp"]),
                "ap": int(resources["ap"]), "max_ap": int(resources["max_ap"]),
                "statuses": {}, "action": None, "defending": False,
                "actions": int(meta.get("actions", 0)), "abilities_used": int(meta.get("abilities_used", 0)),
                "items_used": int(meta.get("items_used", 0)), "defends": int(meta.get("defends", 0)),
            })
            combatants += 1
        if self.active_boss is not None:
            self.active_boss["statuses"] = {}
        return combatants

    def _raid_base_damage(self, meta: dict[str, Any], *, power: float = 1.0, scaling: str | None = None, support_bonus: float = 0.0) -> int:
        """Raid damage keeps the established aggregate formula; abilities only scale its power."""
        stats = meta["stats"]
        effects = meta["effects"]
        job = self.data.jobs[meta["job_id"]]
        base = stats["str"] * 3.0 + stats["mag"] * 2.4 + stats["attack"] * 2.4 + stats["magic_power"] * 2.1
        multiplier = 1 + effects.get("damage_mult", 0) + support_bonus
        multiplier *= player_outgoing_status_multiplier(meta.get("statuses", {}))
        if self.active_boss:
            multiplier *= incoming_vulnerability_multiplier(self.active_boss.get("statuses", {}))
        return max(1, int(base * float(job.get("damage_mod", 1.0)) * float(power) * self.rng.uniform(1.05, 1.45) * multiplier))

    def _apply_raid_limit(self, pid: str, meta: dict[str, Any], damage: int, limit_users: list[str]) -> int:
        if meta.get("limit_armed") and int(meta.get("limit", 0)) >= 100:
            job = self.data.jobs[meta["job_id"]]
            damage = int(damage * 3.25)
            meta["limit"] = 0
            meta["limit_armed"] = False
            limit_users.append(f"{meta['name']} — {job.get('signature', 'Limit Break')}")
            self.db.execute("UPDATE players SET limit_breaks=limit_breaks+1 WHERE twitch_id=?", (pid,))
        else:
            meta["limit"] = min(100, int(meta.get("limit", 0)) + self.rng.randint(10, 18))
        return damage

    def _raid_damage_boss(self, pid: str, meta: dict[str, Any], damage: int, limit_users: list[str], *, use_limit: bool = True) -> int:
        if not self.active_boss:
            return 0
        damage = max(0, int(damage))
        if use_limit:
            damage = self._apply_raid_limit(pid, meta, damage, limit_users)
        before = int(self.active_boss.get("current_hp", 0))
        self.active_boss["current_hp"] = max(0, before - damage)
        dealt = before - int(self.active_boss["current_hp"])
        meta["damage"] = int(meta.get("damage", 0)) + dealt
        meta["best_hit"] = max(int(meta.get("best_hit", 0)), dealt)
        return dealt

    def _resolve_raid_ability(self, pid: str, meta: dict[str, Any], action: dict[str, Any], support_bonus: float, limit_users: list[str], log: list[str]) -> tuple[int, int]:
        ability = next((row for row in self.data.active_abilities.get(meta["job_id"], []) if row["id"] == action.get("ability_id")), None)
        job = self.data.jobs.get(meta["job_id"])
        resource = ability_resource(ability, job) if ability else "mp"
        cost = ability_cost(ability) if ability else 0
        if not ability or int(meta.get(resource, 0)) < cost or (resource == "mp" and has_status(meta.get("statuses", {}), "silence")):
            damage = self._raid_damage_boss(pid, meta, self._raid_base_damage(meta, support_bonus=support_bonus), limit_users)
            log.append(f"{meta['name']}'s ability cannot resolve; Attack deals {damage:,}.")
            return damage, 0
        meta[resource] = int(meta.get(resource, 0)) - cost
        meta["abilities_used"] = int(meta.get("abilities_used", 0)) + 1
        target_id = action.get("target_id")
        target = self.raid_roster.get(target_id) if target_id not in {"boss", "party"} else None
        damage_total = 0
        healing_total = 0
        last_damage = 0
        parts: list[str] = []
        for effect in ability.get("effects", []):
            et = effect.get("type")
            recipient = effect.get("recipient") or "target"
            if et == "damage":
                dealt = self._raid_damage_boss(pid, meta, self._raid_base_damage(meta, power=float(effect.get("power", 1.0)), scaling=effect.get("scaling"), support_bonus=support_bonus), limit_users)
                damage_total += dealt; last_damage = dealt; parts.append(f"{dealt:,} dmg")
            elif et == "heal":
                targets = list(self.raid_roster.values()) if recipient == "party" else [meta] if recipient == "self" else ([target] if target else [])
                healed = sum(self._apply_battle_heal(meta, row, float(effect.get("power", 1.0))) for row in targets if row)
                healing_total += healed; parts.append(f"{healed:,} heal")
            elif et in {"restore_mp", "restore_ap"}:
                key = "mp" if et == "restore_mp" else "ap"
                targets = list(self.raid_roster.values()) if recipient == "party" else [meta] if recipient == "self" or target is None else [target]
                restored = 0
                for row in targets:
                    maximum = int(row.get(f"max_{key}", 0))
                    if maximum <= 0: continue
                    before = int(row.get(key, 0)); amount = max(1, int(maximum * float(effect.get("fraction", 0.0))))
                    row[key] = min(maximum, before + amount); restored += int(row[key]) - before
                parts.append(f"{restored} {key.upper()} restored")
            elif et == "revive":
                if target and int(target.get("hp", 0)) <= 0:
                    target["hp"] = max(1, int(int(target["max_hp"]) * float(effect.get("fraction", 0.30))))
                    target["ko_counted"] = False
                    parts.append(f"revives {target['name']}")
            elif et == "cleanse":
                row = meta if recipient == "self" or not target else target
                removed = cleanse(row.setdefault("statuses", {}), int(effect.get("count", 1)))
                parts.append("cleanses " + (", ".join(removed) if removed else "nothing"))
            elif et == "drain":
                before = int(meta["hp"]); meta["hp"] = min(int(meta["max_hp"]), before + max(0, int(last_damage * float(effect.get("fraction", 0.0)))))
                healed = int(meta["hp"]) - before; meta["healing"] = int(meta.get("healing", 0)) + healed; healing_total += healed; parts.append(f"drains {healed} HP")
            elif et == "status":
                if self.rng.random() >= float(effect.get("chance", 1.0)): continue
                status_id = str(effect.get("status")); turns = int(effect.get("turns", 1)); magnitude = float(effect.get("magnitude", 0.0))
                if recipient == "party":
                    for row in self.raid_roster.values():
                        if int(row.get("hp", 0)) > 0: apply_status(row.setdefault("statuses", {}), status_id, turns, magnitude)
                elif recipient == "self": apply_status(meta.setdefault("statuses", {}), status_id, turns, magnitude)
                elif target_id == "boss": apply_status(self.active_boss.setdefault("statuses", {}), status_id, turns, magnitude)
                elif target: apply_status(target.setdefault("statuses", {}), status_id, turns, magnitude)
                parts.append(status_id.replace("_", " ").title())
        log.append(f"{meta['name']} uses {ability['name']} — {', '.join(parts[:4]) or 'no effect'}.")
        return damage_total, healing_total

    def _resolve_raid_item(self, pid: str, meta: dict[str, Any], action: dict[str, Any], limit_users: list[str], log: list[str]) -> tuple[int, int]:
        item_id = action.get("item_id"); item = self.data.items.get(item_id)
        if not item or self._inventory_qty(pid, item_id) <= 0:
            log.append(f"{meta['name']}'s item action fails; the item is not consumed."); return 0, 0
        use = item.get("use") or {}; target_mode = str(use.get("target", "ally")); target_id = action.get("target_id")
        target = self.raid_roster.get(target_id)
        targets = list(self.raid_roster.values()) if target_mode == "party" else [target] if target_mode in {"ally", "self"} and target else []
        used = False; damage_total = 0; healing_total = 0; parts: list[str] = []
        for effect in use.get("effects", []):
            et = effect.get("type")
            if et == "damage" and target_mode == "enemy":
                dealt = self._raid_damage_boss(pid, meta, max(0, int(effect.get("amount", 0))), limit_users, use_limit=False); damage_total += dealt
                if dealt: used = True; parts.append(f"deals {dealt:,} damage")
            elif et == "heal_hp":
                healed = 0
                for row in targets:
                    if not row or int(row.get("hp", 0)) <= 0: continue
                    maximum=int(row.get("max_hp",0)); before=int(row.get("hp",0)); amount=max(0,int(effect.get("amount",0)))
                    if effect.get("fraction") is not None: amount=max(amount,int(maximum*float(effect.get("fraction",0))))
                    row["hp"]=min(maximum,before+amount); healed += int(row["hp"])-before
                if healed: used=True; healing_total += healed; meta["healing"] = int(meta.get("healing",0))+healed; parts.append(f"restores {healed} HP")
            elif et in {"restore_mp", "restore_ap"}:
                key="mp" if et=="restore_mp" else "ap"; restored=0
                for row in targets:
                    if not row or int(row.get("hp",0))<=0: continue
                    maximum=int(row.get(f"max_{key}",0)); before=int(row.get(key,0)); amount=max(0,int(effect.get("amount",0)))
                    if maximum<=0: continue
                    if effect.get("fraction") is not None: amount=max(amount,int(maximum*float(effect.get("fraction",0))))
                    row[key]=min(maximum,before+amount); restored += int(row[key])-before
                if restored: used=True; parts.append(f"restores {restored} {key.upper()}")
            elif et == "revive":
                revived=0
                for row in targets:
                    if row and int(row.get("hp",0))<=0 and int(row.get("max_hp",0))>0:
                        row["hp"]=max(1,int(int(row["max_hp"])*float(effect.get("fraction",0.30)))); row["ko_counted"]=False; revived += 1
                if revived: used=True; parts.append(f"revives {revived} hero")
            elif et == "cleanse":
                removed=[]; allowed=set(effect.get("statuses",[])) or None; count=99 if effect.get("all_harmful") else int(effect.get("count",1))
                for row in targets:
                    if row and int(row.get("hp",0))>0: removed.extend(cleanse(row.setdefault("statuses",{}),count,allowed=allowed))
                if removed: used=True; parts.append("cleanses " + ", ".join(sorted(set(removed))))
            elif et == "status":
                applied=0
                for row in targets:
                    if row and int(row.get("hp",0))>0:
                        apply_status(row.setdefault("statuses",{}),str(effect.get("status")),int(effect.get("turns",1)),float(effect.get("magnitude",0.0))); applied += 1
                if applied: used=True; parts.append(str(effect.get("status","status")).replace("_"," ").title())
        if used:
            self._change_item(pid,item_id,-1,"raid_battle_use"); meta["items_used"]=int(meta.get("items_used",0))+1
            log.append(f"{meta['name']} uses {item['name']} — {'; '.join(parts)}.")
        else:
            log.append(f"{meta['name']} cannot use {item['name']} effectively; it is not consumed.")
        return damage_total, healing_total

    @_state_guard
    def start_raid(self, boss_id: str | None = None) -> GameResult:
        if not self.active_boss:
            return GameResult.fail("There is no active raid.")
        if boss_id and self.active_boss["id"] != boss_id:
            return GameResult.fail("That raid has already ended.")
        if self.active_boss.get("state") == "combat":
            return GameResult.success(f"{self.active_boss['name']} is already in combat.")
        if not self.raid_roster:
            boss_name = self.active_boss["name"]
            self._write_overlay({"active":False,"status":"ABANDONED","boss":boss_name})
            self.active_boss = None
            return GameResult.fail(f"Nobody joined the raid against {boss_name}. The boss leaves offended but otherwise thriving.")
        self.active_boss["state"] = "combat"
        self.active_boss["round"] = 0
        combatants = self._initialize_raid_combat()
        if combatants <= 0:
            return self._finish_raid(False, reason="No raid participants are able to fight.")
        self.active_boss["next_round_at"] = time.time() + self.raid_round_seconds
        self._update_raid_overlay()
        phase = self._boss_phase(self.active_boss)
        return GameResult.success(f"RAID BEGIN — {self.active_boss['name']} | {len(self.raid_roster)} heroes | Phase: {phase['name']}. Limit gauges start at 0%; survive long enough to regret that.", raid_started=True, boss_id=self.active_boss["id"])

    @_state_guard
    def raid_round(self, boss_id: str | None = None) -> GameResult:
        if not self.active_boss:
            return GameResult.fail("There is no active raid.")
        boss = self.active_boss
        if boss_id and boss["id"] != boss_id:
            return GameResult.fail("That raid has already ended.")
        if boss.get("state") == "rally":
            started = self.start_raid(boss_id)
            if not started.ok:
                return started
            boss = self.active_boss
        elif any("stats" not in row or "effects" not in row for row in self.raid_roster.values()):
            self._initialize_raid_combat()
            boss = self.active_boss
        boss["round"] += 1
        round_no = boss["round"]
        phase = self._boss_phase(boss)
        alive_ids = [pid for pid,m in self.raid_roster.items() if m.get("hp",0) > 0]
        if not alive_ids:
            return self._finish_raid(False, reason="No heroes remain standing.")
        support_bonus = min(0.20, 0.035 * sum(1 for pid in alive_ids if self.raid_roster[pid].get("job_id") in SUPPORT_JOBS))
        round_damage = 0
        round_healing = 0
        limit_users: list[str] = []
        summon_message = None
        armed_summon = boss.get("summon_armed")
        if armed_summon:
            mult = RAID_SUMMONS.get(armed_summon["id"], (armed_summon["name"], 1.0))[1]
            summon_damage = max(250, int(min(75000, boss["max_hp"] * 0.04) * mult))
            boss["current_hp"] = max(0, boss["current_hp"] - summon_damage)
            round_damage += summon_damage
            summon_message = f"SUMMON — {armed_summon['by']} calls {armed_summon['name']} for {summon_damage:,} damage!"
            boss["summon_armed"] = None
        # Hero actions. Explicit chat input overrides the anti-stall default Attack.
        # Queue ownership matches Active Battle: one action per hero per round,
        # replaceable until the timer closes, with MP/AP/items spent only here.
        action_log: list[str] = []
        for pid in alive_ids:
            meta = self.raid_roster[pid]
            meta["defending"] = False
            if not meta.get("action"):
                meta["action"] = {"kind": "attack", "auto": True}

        ordered = sorted(
            [(pid, self.raid_roster[pid]) for pid in alive_ids],
            key=lambda item: (
                action_priority(item[1].get("action") or {"kind": "attack"}, item[1].get("statuses", {})),
                -int(item[1].get("stats", {}).get("dex", 0)),
            ),
        )
        for pid, meta in ordered:
            if int(meta.get("hp", 0)) <= 0:
                continue
            action = meta.get("action") or {"kind": "attack", "auto": True}
            meta["actions"] = int(meta.get("actions", 0)) + 1
            if has_status(meta.get("statuses", {}), "stun"):
                action_log.append(f"{meta['name']} is stunned and loses the action")
                continue
            kind = str(action.get("kind", "attack"))
            if kind == "defend":
                meta["defending"] = True
                meta["defends"] = int(meta.get("defends", 0)) + 1
                restored: list[str] = []
                if int(meta.get("max_ap", 0)) > 0:
                    before_ap = int(meta.get("ap", 0)); meta["ap"] = min(int(meta["max_ap"]), before_ap + defend_ap_restore(int(meta["max_ap"])))
                    if int(meta["ap"]) > before_ap: restored.append(f"{int(meta['ap']) - before_ap} AP")
                if int(meta.get("max_mp", 0)) > 0:
                    before_mp = int(meta.get("mp", 0)); meta["mp"] = min(int(meta["max_mp"]), before_mp + defend_mp_restore(int(meta["max_mp"])))
                    if int(meta["mp"]) > before_mp: restored.append(f"{int(meta['mp']) - before_mp} MP")
                action_log.append(f"{meta['name']} Defends" + (f" (+{'/'.join(restored)})" if restored else ""))
            elif kind == "ability":
                dealt, healed = self._resolve_raid_ability(pid, meta, action, support_bonus, limit_users, action_log)
                round_damage += dealt; round_healing += healed
            elif kind == "item":
                dealt, healed = self._resolve_raid_item(pid, meta, action, limit_users, action_log)
                round_damage += dealt; round_healing += healed
            else:
                dealt = self._raid_damage_boss(pid, meta, self._raid_base_damage(meta, support_bonus=support_bonus), limit_users)
                round_damage += dealt
                action_log.append(f"{meta['name']} attacks for {dealt:,}")
            if boss["current_hp"] <= 0:
                break

        if boss["current_hp"] <= 0:
            # Persist the winning round before clearing Raid runtime state. This
            # matters when the killing action spent MP/AP or consumed an item.
            for pid, meta in self.raid_roster.items():
                meta["action"] = None
                meta["defending"] = False
                self._save_hp(pid, meta.get("hp", 0))
                self._save_resources_from_meta(pid, meta)
            msg = f"R{round_no} — Heroes deal {round_damage:,} damage. " + ("LIMIT BREAK: " + "; ".join(limit_users[:3]) + ". " if limit_users else "")
            finished = self._finish_raid(True)
            extras = [summon_message] if summon_message else []
            return GameResult.success(*extras, msg, *finished.messages, raid_finished=True, won=True)

        # Boss response
        enrage_round = boss.get("enrage_round",10)
        enraged = round_no >= enrage_round
        enrage_mult = 1 + max(0, round_no-enrage_round+1) * 0.18 if enraged else 1.0
        phase_mult = phase.get("damage_mult",1.0)
        signature_round = round_no % max(1,boss.get("aoe_every",3)) == 0
        total_boss_damage = 0
        ko_names: list[str] = []
        boss_statuses = boss.setdefault("statuses", {})
        boss_stunned = has_status(boss_statuses, "stun")
        boss_pressure = max(0.35, 1.0 - status_magnitude(boss_statuses, "weaken"))
        boss_pressure *= max(0.55, 1.0 - 0.5 * status_magnitude(boss_statuses, "slow"))
        if boss_stunned:
            pass
        elif signature_round:
            targets=[pid for pid,m in self.raid_roster.items() if m.get("hp",0)>0]
            for pid in targets:
                meta=self.raid_roster[pid]; p=self._player(pid); job=self.data.jobs[meta["job_id"]]; effects=self._effects(pid,job["id"]); stats=self._stats(p,job,effects)
                raw=max(1,int((boss.get("recommended_level",50)*7 + 90) * 0.62 * phase_mult * enrage_mult * boss_pressure * self.rng.uniform(0.82,1.12)))
                if meta.get("defending"):
                    raw = max(1, int(raw * 0.55))
                raw = max(1, int(raw * max(0.45, 1.0 - status_magnitude(meta.get("statuses", {}), "protect"))))
                reduction = 1 + stats["vit"]*0.006 + effects.get("defense_mult",0)
                dmg=max(1,int(raw/reduction))
                before=meta["hp"]; meta["hp"]=max(0,meta["hp"]-dmg); actual=before-meta["hp"]; total_boss_damage += actual
                meta["damage_taken"] = int(meta.get("damage_taken", 0)) + actual
                if job["id"] in TANK_JOBS: meta["mitigation"] += max(0,int(raw-actual))
                meta["limit"] = min(100, meta.get("limit",0)+max(5,int(actual/max(1,meta["max_hp"])*35)))
                if meta["hp"]<=0 and not meta.get("ko_counted"):
                    meta["ko_counted"]=True; ko_names.append(meta["name"]); self.db.execute("UPDATE players SET deaths=deaths+1 WHERE twitch_id=?",(pid,))
        elif not boss_stunned:
            for _ in range(boss.get("attacks_per_round",2)):
                targets=[pid for pid,m in self.raid_roster.items() if m.get("hp",0)>0]
                if not targets: break
                weights=[]
                for candidate_id in targets:
                    candidate = self.raid_roster[candidate_id]
                    weight = 3.0 if candidate.get("job_id") in TANK_JOBS else 1.0
                    if has_status(candidate.get("statuses", {}), "taunt"):
                        weight *= 1 + status_magnitude(candidate.get("statuses", {}), "taunt")
                    weights.append(weight)
                pid=self.rng.choices(targets,weights=weights,k=1)[0]; meta=self.raid_roster[pid]; p=self._player(pid); job=self.data.jobs[meta["job_id"]]; effects=self._effects(pid,job["id"]); stats=self._stats(p,job,effects)
                raw=max(1,int((boss.get("recommended_level",50)*8+100)*phase_mult*enrage_mult*boss_pressure*self.rng.uniform(0.86,1.16)))
                if meta.get("defending"):
                    raw = max(1, int(raw * 0.55))
                raw = max(1, int(raw * max(0.45, 1.0 - status_magnitude(meta.get("statuses", {}), "protect"))))
                reduction=1+stats["vit"]*0.006+effects.get("defense_mult",0)
                dmg=max(1,int(raw/reduction)); before=meta["hp"]; meta["hp"]=max(0,meta["hp"]-dmg); actual=before-meta["hp"]; total_boss_damage+=actual
                meta["damage_taken"] = int(meta.get("damage_taken", 0)) + actual
                if job["id"] in TANK_JOBS: meta["mitigation"] += max(0,int(raw-actual))
                meta["limit"] = min(100, meta.get("limit",0)+max(5,int(actual/max(1,meta["max_hp"])*40)))
                if meta["hp"]<=0 and not meta.get("ko_counted"):
                    meta["ko_counted"]=True; ko_names.append(meta["name"]); self.db.execute("UPDATE players SET deaths=deaths+1 WHERE twitch_id=?",(pid,))
        for pid,meta in self.raid_roster.items():
            tick_statuses(meta.setdefault("statuses", {}))
            meta["action"] = None
            meta["defending"] = False
            self._save_hp(pid, meta.get("hp",0))
            self._save_resources_from_meta(pid, meta)
        tick_statuses(boss_statuses)
        alive=sum(1 for m in self.raid_roster.values() if m.get("hp",0)>0)
        boss["summon_gauge"] = min(100, int(boss.get("summon_gauge",0)) + max(5, min(25, alive * 3)))
        ready_limits=[m["name"] for m in self.raid_roster.values() if m.get("hp",0)>0 and m.get("limit",0)>=100 and not m.get("limit_armed")]
        self._update_raid_overlay()
        messages=[f"R{round_no} [{phase['name']}] — Party deals {round_damage:,}; {boss['name']} has {boss['current_hp']:,}/{boss['max_hp']:,} HP. Boss damage {total_boss_damage:,}. Heroes {alive}/{len(self.raid_roster)}."]
        if action_log:
            shown = action_log[:4]
            suffix = f" | +{len(action_log) - 4} more" if len(action_log) > 4 else ""
            messages.append("Raid actions — " + " | ".join(shown) + suffix + ".")
        if boss_stunned:
            messages.append(f"{boss['name']} is Stunned and loses the boss response this round.")
        elif signature_round:
            messages.append(f"{boss['name']} unleashes {boss.get('signature','Cataclysm')} across the raid!" + (f" KO: {', '.join(ko_names[:5])}." if ko_names else ""))
        elif ko_names:
            messages.append("KO — " + ", ".join(ko_names[:5]) + ". Another hero can use !revive <name> with a Phoenix Down.")
        if summon_message:
            messages.append(summon_message)
        if limit_users:
            messages.append("LIMIT BREAK — " + " | ".join(limit_users[:4]))
        elif ready_limits:
            messages.append("Limit ready: " + ", ".join(ready_limits[:5]) + " — use !limit to arm it for the next round.")
        if boss.get("summon_gauge",0) >= 100 and not boss.get("summon_armed"):
            messages.append("Guild Summon Gauge: 100% — a raider can use !summon <eidolon>.")
        if enraged:
            messages.append(f"ENRAGE — {boss['name']} is beyond R{enrage_round}; damage escalates every round.")
        if alive <= 0:
            finished=self._finish_raid(False, reason="The entire raid is KO'd.")
            return GameResult.success(*messages,*finished.messages,raid_finished=True,won=False)
        boss["next_round_at"] = time.time() + self.raid_round_seconds
        messages.append(
            f"NEXT RAID R{round_no + 1} · {self._format_seconds(self.raid_round_seconds)} — "
            "!attack · !ability <name> [target] · !defend · !use <item> [target]"
        )
        return GameResult.success(*messages, raid_finished=False, boss_id=boss["id"], next_round_at=boss["next_round_at"])

    @_state_guard
    def limit_break(self, twitch_id: str) -> GameResult:
        if not self.active_boss or self.active_boss.get("state") != "combat":
            return GameResult.fail("Limit Breaks can only be armed during an active raid.")
        meta=self.raid_roster.get(twitch_id)
        if not meta:
            return GameResult.fail("You are not participating in this raid.")
        if meta.get("hp",0)<=0:
            return GameResult.fail("You are KO'd. Even dramatic music has limits.")
        if meta.get("limit_armed"):
            return GameResult.success(f"{meta['name']}'s Limit Break is already armed for the next round.")
        gauge=int(meta.get("limit",0))
        if gauge<100:
            return GameResult.fail(f"Limit Gauge: {gauge}%. Take more damage heroically and try again.")
        meta["limit_armed"]=True
        self._update_raid_overlay()
        job=self.data.jobs[meta["job_id"]]
        return GameResult.success(f"LIMIT ARMED — {meta['name']} prepares {job.get('signature','Limit Break')} for the next raid round.")

    @_state_guard
    def summon_raid(self, twitch_id: str, summon_query: str | None = None) -> GameResult:
        if not self.active_boss or self.active_boss.get("state") != "combat":
            return GameResult.fail("Guild Summons are only available during active raid combat.")
        meta = self.raid_roster.get(twitch_id)
        if not meta or meta.get("hp",0) <= 0:
            return GameResult.fail("You must be alive and participating in the raid to invoke a Summon.")
        gauge = int(self.active_boss.get("summon_gauge",0))
        if not summon_query:
            names = ", ".join(v[0] for k,v in RAID_SUMMONS.items() if k != "bahamut")
            return GameResult.success(f"Guild Summon Gauge: {gauge}% | Available: {names}. Summoner/Sage may also call Bahamut.")
        key = self._norm(summon_query)
        match = next((k for k,v in RAID_SUMMONS.items() if key in {self._norm(k), self._norm(v[0])}), None)
        if not match:
            return GameResult.fail("Unknown raid Summon. Try Ifrit, Shiva, Ramuh, Titan, Garuda, Leviathan, or Bahamut.")
        if match == "bahamut" and meta.get("job_id") not in {"summoner","sage"}:
            return GameResult.fail("Bahamut may only be invoked by a Summoner or Sage.")
        if self.active_boss.get("summon_armed"):
            armed = self.active_boss["summon_armed"]
            return GameResult.fail(f"{armed['name']} is already answering {armed['by']}'s call for the next round.")
        if gauge < 100:
            return GameResult.fail(f"Guild Summon Gauge: {gauge}%. It must reach 100% first.")
        name = RAID_SUMMONS[match][0]
        self.active_boss["summon_gauge"] = 0
        self.active_boss["summon_armed"] = {"id":match,"name":name,"by":meta["name"]}
        self.db.add_record_stat(twitch_id, "summons_called", 1)
        self._update_raid_overlay()
        return GameResult.success(f"SUMMON ARMED — {meta['name']} calls for {name}. The Eidolon will strike at the start of the next raid round.")

    @_state_guard
    def revive_raid(self, reviver_id: str, target_query: str) -> GameResult:
        if not self.active_boss or self.active_boss.get("state") != "combat":
            return GameResult.fail("There is no active raid combat to revive anyone in.")
        reviver=self.raid_roster.get(reviver_id)
        if not reviver or reviver.get("hp",0)<=0:
            return GameResult.fail("You must be alive and participating in the raid to revive someone.")
        q=self._norm(target_query.lstrip('@'))
        target_pid=None
        for pid,meta in self.raid_roster.items():
            p=self._player(pid)
            names={self._norm(meta.get("name",""))}
            if p: names.add(self._norm(p["username"]))
            if q in names:
                target_pid=pid; break
        if not target_pid:
            return GameResult.fail("That hero is not in the raid.")
        target=self.raid_roster[target_pid]
        if target.get("hp",0)>0:
            return GameResult.fail(f"{target['name']} is still standing. Save the Phoenix Down for someone making worse choices.")
        if self._inventory_qty(reviver_id,"phoenix_down")<=0:
            return GameResult.fail("You need a Phoenix Down to revive another hero.")
        self._change_item(reviver_id,"phoenix_down",-1,"raid_revive")
        target["hp"]=max(1,int(target["max_hp"]*0.30)); target["ko_counted"]=False
        self._save_hp(target_pid,target["hp"])
        self.db.execute("UPDATE players SET raid_revives=raid_revives+1 WHERE twitch_id=?",(reviver_id,))
        self._update_raid_overlay()
        return GameResult.success(f"PHOENIX DOWN — {reviver['name']} revives {target['name']} at {target['hp']}/{target['max_hp']} HP.")

    @_state_guard
    def raid_stats(self) -> GameResult:
        if not self.active_boss:
            return GameResult.success("No active raid statistics. The accountants are briefly free.")
        ranked=sorted(
            self.raid_roster.values(),
            key=lambda m: raid_contribution_score(
                damage=m.get("damage", 0), healing=m.get("healing", 0), mitigation=m.get("mitigation", 0)
            ),
            reverse=True,
        )[:5]
        top=" | ".join(
            f"{m['name']} {m.get('damage',0):,} dmg/{m.get('healing',0):,} heal/{m.get('mitigation',0):,} mit/LB {m.get('limit',0)}%"
            for m in ranked
        ) or "no contributions yet"
        return GameResult.success(f"Raid contributions — {top}")

    @_state_guard
    def resolve_boss(self) -> GameResult:
        if not self.active_boss:
            return GameResult.fail("There is no active boss to resolve.")
        if not self.raid_roster:
            return GameResult.fail("Nobody joined the raid. The boss is frankly insulted.")
        if self.active_boss.get("state") == "rally":
            started=self.start_raid(self.active_boss["id"])
            if not started.ok:
                return started
        messages=[]
        for _ in range(30):
            if not self.active_boss:
                break
            result=self.raid_round()
            if result.messages:
                messages.extend(result.messages[:1])
                if result.data.get("raid_finished"):
                    messages.extend(result.messages[1:])
                    break
        if self.active_boss:
            final=self._finish_raid(False,reason="Admin resolution reached the 30-round safety cap.")
            messages.extend(final.messages)
        return GameResult.success(*messages[-5:])

    @_state_guard
    def _finish_raid(self, won: bool, reason: str | None = None) -> GameResult:
        if not self.active_boss:
            return GameResult.fail("The raid is already over.")
        boss=self.active_boss
        total_damage=sum(max(0,int(m.get("damage",0))) for m in self.raid_roster.values())
        contribution_scores = {
            pid: raid_contribution_score(
                damage=meta.get("damage", 0),
                healing=meta.get("healing", 0),
                mitigation=meta.get("mitigation", 0),
            )
            for pid, meta in self.raid_roster.items()
        }
        total_contribution = sum(contribution_scores.values())
        if total_contribution <= 0 and self.raid_roster:
            contribution_scores = {pid: 1.0 for pid in self.raid_roster}
            total_contribution = float(len(self.raid_roster))
        top=sorted(self.raid_roster.items(),key=lambda kv:kv[1].get("damage",0),reverse=True)[:3]
        top_text=", ".join(f"{m['name']} {m.get('damage',0):,}" for _,m in top) or "none"
        messages=[]
        for pid, meta in self.raid_roster.items():
            p = self._player(pid)
            if not p:
                continue
            self.db.update_record_stats(
                pid,
                {
                    "raids_completed": 1,
                    "raid_wins" if won else "raid_wipes": 1,
                    "damage_dealt": int(meta.get("damage", 0)),
                    "raid_damage": int(meta.get("damage", 0)),
                    "healing_done": int(meta.get("healing", 0)),
                    "damage_taken": int(meta.get("damage_taken", 0)),
                    "damage_mitigated": int(meta.get("mitigation", 0)),
                },
                {"best_hit": int(meta.get("best_hit", 0))},
            )
            self.db.record_job_battle(
                pid,
                meta.get("job_id", p["current_job"]),
                won=won,
                knocked_out=int(meta.get("hp", 0)) <= 0,
                damage_dealt=int(meta.get("damage", 0)),
                healing_done=int(meta.get("healing", 0)),
                boss_damage=int(meta.get("damage", 0)),
            )
            raid_key = f"{boss['id']}:{boss.get('closes_at', 0)}"
            self.fellowship_system.record_activity(
                pid, "raid_participation", event_key=f"raid_participation:{raid_key}:{pid}"
            )
        fellowship_raid_notes: list[str] = []
        if won:
            loot_winners=[]
            allocations = raid_reward_allocations(contribution_scores, boss["xp"], boss["gil"])
            for pid,meta in self.raid_roster.items():
                p=self._player(pid)
                if not p: continue
                xp, share = allocations.get(pid, (1, 1))
                with self.db.tx() as conn:
                    conn.execute("UPDATE players SET gil=gil+?, xp=xp+? WHERE twitch_id=?",(share,xp,pid))
                    conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'gil','gil',?,?)",(pid,share,f"boss:{boss['id']}"))
                    conn.execute("INSERT INTO player_boss_clears(player_id,boss_id,clears,best_damage,last_cleared_at) VALUES (?,?,1,?,CURRENT_TIMESTAMP) ON CONFLICT(player_id,boss_id) DO UPDATE SET clears=clears+1,best_damage=MAX(best_damage,excluded.best_damage),last_cleared_at=CURRENT_TIMESTAMP",(pid,boss["id"],meta.get("damage",0)))
                won_items=[]
                for drop in boss.get("drops",[]):
                    if self.rng.random()<=drop.get("chance",0):
                        qty=self.rng.randint(drop.get("min",1),drop.get("max",1)); self._change_item(pid,drop["item_id"],qty,f"boss:{boss['id']}"); won_items.append(f"{self.data.items[drop['item_id']]['name']} x{qty}")
                if won_items: loot_winners.append(f"{meta['name']}: "+", ".join(won_items))
                self._process_levels(pid,p["current_job"]); self._check_achievements(pid)
                fellowship_raid_notes.extend(self.fellowship_system.record_activity(
                    pid, "raid_win", event_key=f"raid_win:{boss['id']}:{boss.get('closes_at',0)}:{pid}"
                ))
            # Guild construction and shared raid-count milestones advance once per
            # resolved victory, not once for every member of the raid roster.
            fellowship_raid_notes.extend(self.fellowship_system.record_shared_activity(
                "raid_clear", event_key=f"raid_clear:{raid_key}"
            ))
            messages.append(f"RAID VICTORY — {boss['name']} falls after {boss['round']} rounds! Total damage {total_damage:,}. Top: {top_text}.")
            if loot_winners: messages.append("Raid loot — " + " | ".join(loot_winners[:5]))
            final_status="VICTORY"
        else:
            messages.append(f"RAID WIPE — {boss['name']} survives at {boss['current_hp']:,}/{boss['max_hp']:,} HP after {boss['round']} rounds. {reason or 'The Guild newsletter will be tasteful.'}")
            final_status="WIPE"
        if fellowship_raid_notes:
            messages.append("Fellowship — " + " | ".join(dict.fromkeys(fellowship_raid_notes[:5])))
        final_overlay=self._overlay_payload(active=False,status=final_status,boss_override=boss)
        self._write_overlay(final_overlay)
        self.active_boss=None; self.raid_roster.clear()
        return GameResult.success(*messages)

    def _boss_phase(self, boss: dict[str, Any]) -> dict[str, Any]:
        ratio=boss.get("current_hp",boss["hp"])/max(1,boss.get("max_hp",boss["hp"]))
        phases=sorted(boss.get("phases",[{"threshold":1.0,"name":"Battle","damage_mult":1.0}]),key=lambda x:x.get("threshold",0),reverse=True)
        chosen=phases[0]
        for phase in phases:
            if ratio <= phase.get("threshold",1.0):
                chosen=phase
        return chosen

    def _overlay_payload(self, active: bool = True, status: str | None = None, boss_override: dict[str, Any] | None = None) -> dict[str, Any]:
        boss=boss_override or self.active_boss
        if not boss:
            return {"active":False,"status":status or "IDLE"}
        phase=self._boss_phase(boss)
        top=sorted(self.raid_roster.values(),key=lambda m:m.get("damage",0),reverse=True)[:5]
        return {
            "active":active, "status":status or boss.get("state","rally").upper(), "boss":boss["name"], "tier":boss.get("tier","World Boss"),
            "hp":boss.get("current_hp",boss["hp"]), "max_hp":boss.get("max_hp",boss["hp"]), "round":boss.get("round",0), "phase":phase.get("name","Battle"),
            "signature":boss.get("signature","Cataclysm"), "raiders":len(self.raid_roster), "alive":sum(1 for m in self.raid_roster.values() if m.get("hp",0)>0),
            "enraged":boss.get("round",0)>=boss.get("enrage_round",999), "summon_gauge":boss.get("summon_gauge",0), "top":[{"name":m["name"],"damage":m.get("damage",0),"healing":m.get("healing",0)} for m in top],
            "updated_at":int(time.time()),
        }

    def _write_overlay(self, payload: dict[str, Any]) -> None:
        try:
            self.overlay_state_path.parent.mkdir(parents=True,exist_ok=True)
            tmp=self.overlay_state_path.with_suffix(self.overlay_state_path.suffix+".tmp")
            tmp.write_text(json.dumps(payload,indent=2),encoding="utf-8")
            tmp.replace(self.overlay_state_path)
        except OSError:
            pass

    def _update_raid_overlay(self) -> None:
        self._write_overlay(self._overlay_payload())

    @_state_guard
    def combat_snapshot(self) -> dict[str, Any]:
        """Return a small immutable view for background scheduling/diagnostics."""
        encounter = dict(self.active_encounter) if self.active_encounter else None
        boss = None
        if self.active_boss:
            boss = {
                "id": self.active_boss.get("id"),
                "name": self.active_boss.get("name"),
                "state": self.active_boss.get("state"),
                "closes_at": self.active_boss.get("closes_at"),
                "next_round_at": self.active_boss.get("next_round_at"),
                "round": self.active_boss.get("round", 0),
            }
        return {
            "encounter": encounter,
            "encounter_roster": len(self.encounter_roster),
            "hunts": [
                {
                    "id": int(row.get("id") or 0),
                    "player_id": str(player_id),
                    "hunt_id": str(row.get("hunt_id") or ""),
                    "rank": str(row.get("rank") or "C"),
                    "resolves_at": float(row.get("resolves_at") or 0),
                }
                for player_id, row in self.active_hunts.items()
            ],
            "boss": boss,
            "raid_roster": len(self.raid_roster),
        }

    def _record_combat_metrics(
        self,
        player_id: str,
        job_id: str,
        monster_id: str,
        *,
        battle_type: str,
        won: bool,
        knocked_out: bool,
        damage_dealt: int,
        damage_taken: int,
        healing_done: int,
        best_hit: int,
    ) -> None:
        self.db.update_record_stats(
            player_id,
            {
                "battles": 1,
                f"{battle_type}_attempts": 1,
                f"{battle_type}_wins" if won else f"{battle_type}_losses": 1,
                "damage_dealt": int(damage_dealt),
                "damage_taken": int(damage_taken),
                "healing_done": int(healing_done),
            },
            {"best_hit": int(best_hit)},
        )
        self.db.record_monster_result(
            player_id,
            monster_id,
            won=won,
            knocked_out=knocked_out,
            damage_dealt=int(damage_dealt),
            damage_taken=int(damage_taken),
            healing_done=int(healing_done),
            best_hit=int(best_hit),
        )
        self.db.record_job_battle(
            player_id,
            job_id,
            won=won,
            knocked_out=knocked_out,
            damage_dealt=int(damage_dealt),
            healing_done=int(healing_done),
        )

    def _recipe_known(self, player_id: str, recipe: dict[str, Any]) -> bool:
        return bool(recipe.get("known_by_default")) or bool(self.db.one("SELECT 1 FROM player_recipes WHERE player_id=? AND recipe_id=?", (player_id, recipe["id"])))

    def _unlock_recipe(self, player_id: str, recipe_id: str) -> bool:
        if recipe_id not in self.data.recipes:
            return False
        if self._recipe_known(player_id, self.data.recipes[recipe_id]):
            return False
        self.db.execute("INSERT INTO player_recipes(player_id,recipe_id) VALUES (?,?)", (player_id, recipe_id))
        return True

    def _recipe_affordable(self, player_id: str, recipe: dict[str, Any], quantity: int) -> tuple[bool, list[str]]:
        p = self._player(player_id)
        missing: list[str] = []
        gil = recipe.get("gil", 0) * quantity
        seals = recipe.get("seal_cost", 0) * quantity
        if p["gil"] < gil:
            missing.append(f"{gil:,} gil ({p['gil']:,} owned)")
        if p["hunt_seals"] < seals:
            missing.append(f"{seals} Hunt Seals ({p['hunt_seals']} owned)")
        for mat in recipe.get("materials", []):
            need = mat["quantity"] * quantity
            have = self._inventory_qty(player_id, mat["item_id"])
            if have < need:
                missing.append(f"{self.data.items[mat['item_id']]['name']} x{need} ({have} owned)")
        return not missing, missing

    def _forge_bonus_per_level(self) -> float:
        return float(self.data.forge[0].get("bonus_per_level", 0.08)) if self.data.forge else 0.08

    def _upgrade_level(self, player_id: str, item_id: str) -> int:
        row = self.db.one("SELECT upgrade_level FROM item_upgrades WHERE player_id=? AND item_id=?", (player_id, item_id))
        return int(row["upgrade_level"]) if row else 0

    def _roll_pity_drops(self, player_id: str, source_data: dict[str, Any], source: str, loot_bonus: float = 0.0) -> list[str]:
        rewards: list[str] = []
        for drop in source_data.get("pity_drops", []):
            item_id = drop["item_id"]
            key = f"item:{source_data['id']}:{item_id}"
            row = self.db.one("SELECT attempts FROM drop_pity WHERE player_id=? AND pity_key=?", (player_id, key))
            attempts = int(row["attempts"]) if row else 0
            chance = min(0.95, drop.get("chance", 0.0) * (1 + loot_bonus))
            guaranteed = attempts + 1 >= int(drop.get("guarantee_after", 999999))
            if guaranteed or self.rng.random() <= chance:
                qty = int(drop.get("quantity", 1))
                self._change_item(player_id, item_id, qty, f"pity_drop:{source}")
                self.db.execute("INSERT INTO drop_pity(player_id,pity_key,attempts) VALUES (?,?,0) ON CONFLICT(player_id,pity_key) DO UPDATE SET attempts=0", (player_id, key))
                note = " [pity guarantee]" if guaranteed else ""
                rewards.append(f"{self.data.items[item_id]['name']} x{qty}{note}")
            else:
                self.db.execute("INSERT INTO drop_pity(player_id,pity_key,attempts) VALUES (?,?,1) ON CONFLICT(player_id,pity_key) DO UPDATE SET attempts=attempts+1", (player_id, key))
        return rewards

    def _roll_recipe_drops(self, player_id: str, source_data: dict[str, Any], source: str, loot_bonus: float = 0.0) -> list[str]:
        rewards: list[str] = []
        for drop in source_data.get("recipe_drops", []):
            recipe_id = drop["recipe_id"]
            if recipe_id not in self.data.recipes or self._recipe_known(player_id, self.data.recipes[recipe_id]):
                continue
            key = f"recipe:{source_data['id']}:{recipe_id}"
            row = self.db.one("SELECT attempts FROM drop_pity WHERE player_id=? AND pity_key=?", (player_id, key))
            attempts = int(row["attempts"]) if row else 0
            chance = min(0.90, drop.get("chance", 0.0) * (1 + loot_bonus))
            guaranteed = attempts + 1 >= int(drop.get("guarantee_after", 999999))
            if guaranteed or self.rng.random() <= chance:
                if self._unlock_recipe(player_id, recipe_id):
                    rewards.append(f"Recipe learned: {self.data.recipes[recipe_id]['name']}" + (" [pity guarantee]" if guaranteed else ""))
                self.db.execute("INSERT INTO drop_pity(player_id,pity_key,attempts) VALUES (?,?,0) ON CONFLICT(player_id,pity_key) DO UPDATE SET attempts=0", (player_id, key))
            else:
                self.db.execute("INSERT INTO drop_pity(player_id,pity_key,attempts) VALUES (?,?,1) ON CONFLICT(player_id,pity_key) DO UPDATE SET attempts=attempts+1", (player_id, key))
        return rewards

    def _cost_missing(self, player_id: str, cost: dict[str, Any]) -> list[str]:
        p = self._player(player_id)
        missing: list[str] = []
        if p["gil"] < cost.get("gil", 0):
            missing.append(f"{cost.get('gil',0):,} gil ({p['gil']:,} owned)")
        if p["hunt_seals"] < cost.get("hunt_seals", 0):
            missing.append(f"{cost.get('hunt_seals',0)} Hunt Seals ({p['hunt_seals']} owned)")
        for mat in cost.get("items", []):
            have = self._inventory_qty(player_id, mat["item_id"])
            if have < mat["quantity"]:
                missing.append(f"{self.data.items[mat['item_id']]['name']} x{mat['quantity']} ({have} owned)")
        return missing

    def _cost_text(self, cost: dict[str, Any]) -> str:
        parts: list[str] = []
        if cost.get("gil", 0):
            parts.append(f"{cost['gil']:,} gil")
        if cost.get("hunt_seals", 0):
            parts.append(f"{cost['hunt_seals']} Hunt Seals")
        parts.extend(f"{self.data.items[m['item_id']]['name']} x{m['quantity']}" for m in cost.get("items", []))
        return ", ".join(parts) or "none"

    def _player(self, twitch_id: str):
        return self.db.one("SELECT * FROM players WHERE twitch_id=?", (str(twitch_id),))

    def _need_recruit(self) -> GameResult:
        return GameResult.fail("You haven't joined the Crystal Guild yet. Start with !recruit — or use !guild start for the short version.")

    def _job_level(self, player_id: str, job_id: str) -> int:
        row = self.db.one("SELECT level FROM player_jobs WHERE player_id=? AND job_id=?", (player_id, job_id))
        return int(row["level"]) if row else 0

    def _effects(self, player_id: str, job_id: str) -> dict[str, float]:
        effects: dict[str, float] = {}
        jlevel = self._job_level(player_id, job_id)
        job = self.data.jobs[job_id]
        for ability in job.get("abilities", []):
            if jlevel >= ability["level"]:
                for key, value in ability.get("effects", {}).items():
                    effects[key] = effects.get(key, 0.0) + float(value)
        rows = self.db.all("SELECT job_id FROM mastery_slots WHERE player_id=? ORDER BY slot", (player_id,))
        for row in rows:
            mastered_id = row["job_id"]
            if self._job_level(player_id, mastered_id) < 50 or mastered_id not in self.data.jobs:
                continue
            for key, value in self.data.jobs[mastered_id].get("mastery", {}).get("effects", {}).items():
                effects[key] = effects.get(key, 0.0) + float(value)
        return effects

    def _equipment_traits(self, p: Any, job: dict[str, Any]) -> dict[str, Any]:
        traits: dict[str, Any] = {
            "status_immune": [],
            "status_resist": {},
            "weapon_element": None,
            "on_hit_status": None,
            "lifesteal": 0.0,
        }
        eq = self.db.one("SELECT * FROM equipment WHERE player_id=?", (p["twitch_id"],))
        if not eq:
            return traits
        immunities: set[str] = set()
        resistance: dict[str, float] = {}
        for slot, item_id in (("weapon", eq["weapon_id"]), ("armor", eq["armor_id"]), ("accessory", eq["accessory_id"])):
            item = self.data.item(item_id)
            if not item:
                continue
            if item.get("allowed_jobs") and job["id"] not in item["allowed_jobs"]:
                continue
            immunities.update(str(x) for x in item.get("status_immune", []))
            for status_id, amount in (item.get("status_resist") or {}).items():
                resistance[str(status_id)] = max(resistance.get(str(status_id), 0.0), float(amount))
            if slot == "weapon":
                if item.get("element"):
                    traits["weapon_element"] = str(item["element"])
                if item.get("on_hit_status"):
                    traits["on_hit_status"] = dict(item["on_hit_status"])
                traits["lifesteal"] = max(float(traits["lifesteal"]), float(item.get("lifesteal", 0.0)))
        traits["status_immune"] = sorted(immunities)
        traits["status_resist"] = resistance
        return traits

    def _player_status_chance(self, target: dict[str, Any], status_id: str, chance: float) -> float:
        if status_id in set(target.get("status_immune", [])):
            return 0.0
        resist = max(0.0, min(0.95, float((target.get("status_resist") or {}).get(status_id, 0.0))))
        return max(0.0, min(1.0, float(chance) * (1.0 - resist)))

    def _stats(self, p: Any, job: dict[str, Any], effects: dict[str, float] | None = None) -> dict[str, int]:
        effects = effects or self._effects(p["twitch_id"], job["id"])
        level = p["level"]
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
        eq = self.db.one("SELECT * FROM equipment WHERE player_id=?", (p["twitch_id"],))
        if eq:
            for item_id in (eq["weapon_id"], eq["armor_id"], eq["accessory_id"]):
                item = self.data.item(item_id)
                if not item:
                    continue
                if item.get("allowed_jobs") and job["id"] not in item["allowed_jobs"]:
                    continue
                upgrade = self._upgrade_level(p["twitch_id"], item_id)
                scale = 1 + self._forge_bonus_per_level() * upgrade
                for key, value in item.get("bonuses", {}).items():
                    if key in stats:
                        stats[key] += int(round(value * scale))
        stats["hp"] = int(stats["hp"] * (1 + effects.get("hp_mult", 0)))
        stats["mag"] = int(stats["mag"] * (1 + effects.get("mag_mult", 0)))
        return stats

    def _requirement_value(self, player_id: str, req: dict[str, Any]) -> int:
        p = self._player(player_id)
        kind = req["type"]
        if kind == "character_level":
            return int(p["level"])
        if kind == "job_level":
            if "job_id" in req:
                return self._job_level(player_id, req["job_id"])
            row = self.db.one("SELECT COALESCE(MAX(level),0) AS n FROM player_jobs WHERE player_id=?", (player_id,))
            return int(row["n"]) if row else 0
        if kind == "bestiary_unique":
            return int(self.db.one("SELECT COUNT(*) AS n FROM bestiary WHERE player_id=?", (player_id,))["n"])
        if kind == "monster_kills":
            row = self.db.one("SELECT defeats FROM bestiary WHERE player_id=? AND monster_id=?", (player_id, req["monster_id"]))
            return int(row["defeats"]) if row else 0
        if kind == "ventures":
            return int(p["ventures"])
        if kind == "hunt_clear":
            row = self.db.one("SELECT clears FROM player_hunts WHERE player_id=? AND hunt_id=?", (player_id, req["hunt_id"]))
            return int(row["clears"]) if row else 0
        if kind == "hunt_rank_clears":
            return self._rank_unique_clears(player_id, req["rank"])
        if kind == "hunt_rank_total":
            rows = self.db.all("SELECT hunt_id, clears FROM player_hunts WHERE player_id=?", (player_id,))
            return sum(
                int(row["clears"]) for row in rows
                if row["hunt_id"] in self.data.hunts and self.data.hunts[row["hunt_id"]]["rank"] == req["rank"]
            )
        if kind == "quest_complete":
            return 1 if self.db.one("SELECT 1 FROM player_quests WHERE player_id=? AND quest_id=?", (player_id, req["quest_id"])) else 0
        if kind == "mastery_count":
            return int(self.db.one("SELECT COUNT(*) AS n FROM player_jobs WHERE player_id=? AND level>=50", (player_id,))["n"])
        if kind == "quest_count":
            return int(self.db.one("SELECT COUNT(*) AS n FROM player_quests WHERE player_id=?", (player_id,))["n"])
        if kind == "hunt_total":
            return int(self.db.one("SELECT COALESCE(SUM(clears),0) AS n FROM player_hunts WHERE player_id=?", (player_id,))["n"])
        if kind == "stat":
            return int(p[req["field"]])
        if kind == "record_stat":
            metric = str(req["metric"])
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
                row = self.db.one(
                    f"SELECT COALESCE({amount_sql},0) AS value FROM transactions WHERE player_id=? AND kind=? AND amount {direction} 0",
                    (player_id, asset_kind),
                )
                return int(row["value"] or 0) if row else 0
            row = self.db.one(
                "SELECT value FROM player_record_stats WHERE player_id=? AND metric=?",
                (player_id, metric),
            )
            return int(row["value"]) if row else 0
        if kind == "monster_record_defeats":
            row = self.db.one(
                "SELECT defeats FROM player_monster_records WHERE player_id=? AND monster_id=?",
                (player_id, req["monster_id"]),
            )
            return int(row["defeats"]) if row else 0
        if kind == "boss_clear":
            row = self.db.one(
                "SELECT clears FROM player_boss_clears WHERE player_id=? AND boss_id=?",
                (player_id, req["boss_id"]),
            )
            return int(row["clears"]) if row else 0
        if kind == "boss_unique":
            row = self.db.one(
                "SELECT COUNT(*) AS n FROM player_boss_clears WHERE player_id=? AND clears>0",
                (player_id,),
            )
            return int(row["n"]) if row else 0
        if kind == "expedition_region_progress":
            row = self.db.one(
                "SELECT progress FROM player_region_exploration WHERE player_id=? AND region_id=?",
                (player_id, str(req.get("region_id") or "")),
            )
            return int(row["progress"] or 0) if row else 0
        if kind == "expedition_regions_mastered":
            row = self.db.one(
                "SELECT COUNT(*) AS n FROM player_region_exploration WHERE player_id=? AND progress>=100",
                (player_id,),
            )
            return int(row["n"] or 0) if row else 0
        if kind == "job_battles":
            if req.get("job_id"):
                row = self.db.one(
                    "SELECT battles FROM player_job_records WHERE player_id=? AND job_id=?",
                    (player_id, req["job_id"]),
                )
            else:
                row = self.db.one(
                    "SELECT COALESCE(MAX(battles),0) AS battles FROM player_job_records WHERE player_id=?",
                    (player_id,),
                )
            return int(row["battles"]) if row else 0
        if kind == "item_quantity":
            return self._inventory_qty(player_id, req["item_id"])
        if kind == "hunt_seals":
            return int(p["hunt_seals"])
        if kind == "gil":
            return int(p["gil"])
        if kind == "item_upgrade":
            return self._upgrade_level(player_id, req["item_id"])
        if kind == "relic_complete":
            row = self.db.one("SELECT stage FROM player_relics WHERE player_id=? AND relic_id=?", (player_id, req["relic_id"]))
            relic = self.data.relics.get(req["relic_id"])
            return 1 if row and relic and row["stage"] >= len(relic.get("stages", [])) else 0
        return 0

    def _requirement_text(self, req: dict[str, Any], value: int) -> str:
        amount = req.get("amount", 1)
        kind = req["type"]
        if kind == "character_level":
            return f"Character Lv.{amount} ({value}/{amount})"
        if kind == "job_level":
            if "job_id" in req:
                return f"{self.data.jobs[req['job_id']]['name']} JLv.{amount} ({value}/{amount})"
            return f"Any Job JLv.{amount} ({value}/{amount})"
        if kind == "bestiary_unique":
            return f"Bestiary {amount} species ({value}/{amount})"
        if kind == "monster_kills":
            return f"Defeat {self.data.monsters[req['monster_id']]['name']} x{amount} ({value}/{amount})"
        if kind == "ventures":
            return f"Complete {amount} ventures ({value}/{amount})"
        if kind == "hunt_clear":
            return f"Clear {self.data.hunts[req['hunt_id']]['name']} ({value}/{amount})"
        if kind == "hunt_rank_clears":
            return f"Clear {amount} unique {req['rank']}-Rank Hunts ({value}/{amount})"
        if kind == "hunt_rank_total":
            return f"Clear {req['rank']}-Rank Hunts x{amount} total ({value}/{amount})"
        if kind == "quest_complete":
            return f"Complete quest {self.data.quests[req['quest_id']]['name']}"
        if kind == "mastery_count":
            return f"Master {amount} Jobs ({value}/{amount})"
        if kind == "item_quantity":
            return f"Own {self.data.items[req['item_id']]['name']} x{amount} ({value}/{amount})"
        if kind == "hunt_seals":
            return f"Hold {amount} Hunt Seals ({value}/{amount})"
        if kind == "gil":
            return f"Hold {amount:,} gil ({value:,}/{amount:,})"
        if kind == "item_upgrade":
            return f"Forge {self.data.items[req['item_id']]['name']} to +{amount} (+{value}/+{amount})"
        if kind == "relic_complete":
            return f"Complete Relic: {self.data.relics[req['relic_id']]['name']}"
        if kind == "record_stat":
            label = req["metric"].replace("_", " ").title()
            return f"{label} {amount:,} ({value:,}/{amount:,})"
        if kind == "monster_record_defeats":
            monster = self.data.monsters[req["monster_id"]]["name"]
            return f"Be KO'd by {monster} x{amount} ({value}/{amount})"
        if kind == "boss_clear":
            boss = self.data.bosses[req["boss_id"]]["name"]
            return f"Defeat {boss} x{amount} ({value}/{amount})"
        if kind == "boss_unique":
            return f"Defeat {amount} unique raid bosses ({value}/{amount})"
        if kind == "expedition_region_progress":
            region = self.data.expedition_regions.get(str(req.get("region_id") or "")) or {}
            return f"Explore {region.get('name', 'region')} to {amount}% ({value}/{amount})"
        if kind == "expedition_regions_mastered":
            return f"Master {amount} Expedition regions ({value}/{amount})"
        if kind == "job_battles":
            job = self.data.jobs.get(req.get("job_id"), {}).get("name")
            subject = job or "a single Job"
            return f"Fight {amount} battles on {subject} ({value}/{amount})"
        return f"{kind} {value}/{amount}"

    def _requirements_met(self, player_id: str, requirements: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        missing = []
        for req in requirements:
            value = self._requirement_value(player_id, req)
            if value < req.get("amount", 1):
                missing.append(self._requirement_text(req, value))
        return not missing, missing

    def _hunt_available(self, player_id: str, hunt: dict[str, Any]) -> tuple[bool, list[str]]:
        p = self._player(player_id)
        missing = []
        if p["level"] < hunt["min_level"]:
            missing.append(f"Character Lv.{hunt['min_level']} ({p['level']}/{hunt['min_level']})")
        _, req_missing = self._requirements_met(player_id, hunt.get("requirements", []))
        missing.extend(req_missing)
        return not missing, missing

    def _rank_unique_clears(self, player_id: str, rank: str) -> int:
        rows = self.db.all("SELECT hunt_id, clears FROM player_hunts WHERE player_id=? AND clears>0", (player_id,))
        return sum(1 for row in rows if row["hunt_id"] in self.data.hunts and self.data.hunts[row["hunt_id"]]["rank"] == rank)

    def _unlock_title(self, player_id: str, title_id: str) -> bool:
        if title_id not in self.data.titles:
            return False
        if self.db.one("SELECT 1 FROM player_titles WHERE player_id=? AND title_id=?", (player_id, title_id)):
            return False
        self.db.execute("INSERT INTO player_titles(player_id,title_id) VALUES (?,?)", (player_id, title_id))
        return True

    def _ensure_base_title(self, player_id: str) -> None:
        if not self.db.one("SELECT 1 FROM player_titles WHERE player_id=? AND title_id='fresh_meat'", (player_id,)):
            self.db.execute("INSERT INTO player_titles(player_id,title_id) VALUES (?, 'fresh_meat')", (player_id,))

    def _streamer_player_match(self, query: str):
        raw = str(query or "").strip().lstrip("@").strip()
        if not raw:
            return None
        rows = self.db.all("SELECT twitch_id,username,display_name FROM players ORDER BY username")
        lowered = raw.lower()
        exact = [
            row for row in rows
            if str(row["twitch_id"]) == raw
            or str(row["username"] or "").lower() == lowered
            or str(row["display_name"] or "").lower() == lowered
        ]
        unique = {str(row["twitch_id"]): row for row in exact}
        if len(unique) == 1:
            return next(iter(unique.values()))
        if exact:
            return None
        normalized = self._norm(raw)
        fuzzy = [
            row for row in rows
            if normalized in {self._norm(str(row["username"] or "")), self._norm(str(row["display_name"] or ""))}
        ]
        unique = {str(row["twitch_id"]): row for row in fuzzy}
        return next(iter(unique.values())) if len(unique) == 1 else None

    def streamer_item_admin(self, request: str, *, remove: bool = False, action_id: str = "") -> GameResult:
        """Streamer-only inventory adjustment shared by chat and Portal controls.

        Syntax is ``player | item | quantity`` with quantity defaulting to one.
        Portal calls pass ``action_id`` so the inventory mutation and replay marker
        commit atomically; a lost hosted acknowledgement can never double-add or
        double-remove an item.
        """
        if action_id:
            replay = self._portal_action_replay(action_id)
            if replay is not None:
                return replay

        def finish(result: GameResult) -> GameResult:
            return self._portal_store_nonmutating_result(action_id, result) if action_id else result

        parts = [part.strip() for part in str(request or "").split("|")]
        if len(parts) not in {2, 3} or not parts[0] or not parts[1]:
            return finish(GameResult.fail(
                "Usage: !removeitem <player> | <item> | [quantity]" if remove
                else "Usage: !additem <player> | <item> | [quantity]"
            ))
        player_query, item_query = parts[0], parts[1]
        try:
            quantity = int(parts[2]) if len(parts) == 3 and parts[2] else 1
        except (TypeError, ValueError):
            return finish(GameResult.fail("Item quantity must be a whole number between 1 and 999."))
        if quantity < 1 or quantity > 999:
            return finish(GameResult.fail("Item quantity must be between 1 and 999."))

        player = self._streamer_player_match(player_query)
        if not player:
            return finish(GameResult.fail(
                f"Player '{player_query}' was not found or is ambiguous. Use the exact Twitch username."
            ))
        item = self._find_by_name_or_id(self.data.items, item_query)
        if not item:
            return finish(GameResult.fail(f"Item '{item_query}' was not found. Use the exact item name or ID."))

        player_id = str(player["twitch_id"])
        display_name = str(player["display_name"] or player["username"] or player_id)
        item_id = str(item["id"])
        item_name = str(item["name"])
        auto_unequipped = False
        slot = ""
        delta = -quantity if remove else quantity
        source = "streamer_admin:remove" if remove else "streamer_admin:add"

        with self.db.tx() as conn:
            row = conn.execute(
                "SELECT quantity FROM inventory WHERE player_id=? AND item_id=?",
                (player_id, item_id),
            ).fetchone()
            before = max(0, int(row["quantity"] if row else 0))
            if remove and before < quantity:
                result = GameResult.fail(
                    f"{display_name} only owns {before} × {item_name}; cannot remove {quantity}."
                )
                if action_id:
                    self._portal_action_store_sql(conn, action_id, result)
                return result

            after = before + delta
            conn.execute(
                "INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) "
                "ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=excluded.quantity",
                (player_id, item_id, after),
            )
            conn.execute(
                "INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, ?)",
                (player_id, item_id, delta, source),
            )

            if remove and after == 0 and item.get("type") in {"weapon", "armor", "accessory"}:
                slot = str(item["type"])
                column = {"weapon": "weapon_id", "armor": "armor_id", "accessory": "accessory_id"}[slot]
                equipped = conn.execute(
                    f"SELECT {column} AS item_id FROM equipment WHERE player_id=?",
                    (player_id,),
                ).fetchone()
                if equipped and str(equipped["item_id"] or "") == item_id:
                    conn.execute(f"UPDATE equipment SET {column}=NULL WHERE player_id=?", (player_id,))
                    auto_unequipped = True

            verb = "Removed" if remove else "Added"
            direction = "from" if remove else "to"
            note = f" Last equipped copy was unequipped from {slot}." if auto_unequipped else ""
            result = GameResult.success(
                f"STREAMER ITEM — {verb} {quantity} × {item_name} {direction} {display_name} ({before} → {after}).{note}",
                operation="remove" if remove else "add",
                player_id=player_id,
                username=str(player["username"] or ""),
                display_name=display_name,
                item_id=item_id,
                item_name=item_name,
                quantity=quantity,
                owned_before=before,
                owned_after=after,
                auto_unequipped=auto_unequipped,
                slot=slot or None,
            )
            if action_id:
                self._portal_action_store_sql(conn, action_id, result)

        if auto_unequipped:
            self._normalize_after_equipment_change(player_id)
        return result

    def _change_item(self, player_id: str, item_id: str, amount: int, source: str) -> None:
        with self.db.tx() as conn:
            conn.execute("INSERT INTO inventory(player_id,item_id,quantity) VALUES (?,?,?) ON CONFLICT(player_id,item_id) DO UPDATE SET quantity=MAX(0, quantity+excluded.quantity)", (player_id, item_id, amount))
            conn.execute("INSERT INTO transactions(player_id,kind,asset_id,amount,source) VALUES (?, 'item', ?, ?, ?)", (player_id, item_id, amount, source))

    def _inventory_qty(self, player_id: str, item_id: str) -> int:
        row = self.db.one("SELECT quantity FROM inventory WHERE player_id=? AND item_id=?", (player_id, item_id))
        return int(row["quantity"]) if row else 0

    def _item_name(self, item_id: str | None) -> str:
        item = self.data.item(item_id)
        return item["name"] if item else "—"

    def _resource_state_for(
        self,
        p: Any,
        job: dict[str, Any] | None = None,
        stats: dict[str, int] | None = None,
        *,
        initialize: bool = True,
    ) -> dict[str, Any]:
        """Return persistent current/max MP/AP for the supplied player's Job.

        ``NULL`` current values mean that resource has never been initialized for
        this character. The first Job that uses it starts full; after that the
        absolute remaining amount persists across battles and Job changes.
        """
        if job is None:
            job = self.data.jobs.get(p["current_job"])
        if not job:
            return {"mode": "none", "mp": 0, "max_mp": 0, "ap": 0, "max_ap": 0}
        stats = stats or self._stats(p, job)
        pools = battle_resource_pools(stats, job)
        max_mp = int(pools["max_mp"])
        max_ap = int(pools["max_ap"])
        raw_mp = p["current_mp"]
        raw_ap = p["current_ap"]
        mp = 0 if max_mp <= 0 else (max_mp if raw_mp is None else max(0, min(max_mp, int(raw_mp))))
        ap = 0 if max_ap <= 0 else (max_ap if raw_ap is None else max(0, min(max_ap, int(raw_ap))))

        if initialize:
            updates: list[str] = []
            params: list[int | str] = []
            if max_mp > 0 and (raw_mp is None or int(raw_mp) != mp):
                updates.append("current_mp=?")
                params.append(mp)
            if max_ap > 0 and (raw_ap is None or int(raw_ap) != ap):
                updates.append("current_ap=?")
                params.append(ap)
            if updates:
                params.append(str(p["twitch_id"]))
                self.db.execute(
                    f"UPDATE players SET {', '.join(updates)}, updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
                    tuple(params),
                )
        return {
            "mode": str(job.get("resource_mode") or "none"),
            "mp": mp,
            "max_mp": max_mp,
            "ap": ap,
            "max_ap": max_ap,
        }

    def _save_resources_from_meta(self, player_id: str, meta: dict[str, Any]) -> None:
        """Persist resources used by the current combat Job without erasing inactive pools."""
        updates: list[str] = []
        params: list[int | str] = []
        max_mp = max(0, int(meta.get("max_mp", 0)))
        max_ap = max(0, int(meta.get("max_ap", 0)))
        if max_mp > 0:
            updates.append("current_mp=?")
            params.append(max(0, min(max_mp, int(meta.get("mp", 0)))))
        if max_ap > 0:
            updates.append("current_ap=?")
            params.append(max(0, min(max_ap, int(meta.get("ap", 0)))))
        if updates:
            params.append(str(player_id))
            self.db.execute(
                f"UPDATE players SET {', '.join(updates)}, updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
                tuple(params),
            )

    def _restore_current_job_resources(self, player_id: str) -> dict[str, Any]:
        p = self._player(player_id)
        if not p:
            return {"mode": "none", "mp": 0, "max_mp": 0, "ap": 0, "max_ap": 0}
        job = self.data.jobs.get(p["current_job"])
        if not job:
            return {"mode": "none", "mp": 0, "max_mp": 0, "ap": 0, "max_ap": 0}
        stats = self._stats(p, job)
        pools = battle_resource_pools(stats, job)
        updates: list[str] = []
        params: list[int | str] = []
        if int(pools["max_mp"]) > 0:
            updates.append("current_mp=?")
            params.append(int(pools["max_mp"]))
        if int(pools["max_ap"]) > 0:
            updates.append("current_ap=?")
            params.append(int(pools["max_ap"]))
        if updates:
            params.append(str(player_id))
            self.db.execute(
                f"UPDATE players SET {', '.join(updates)}, updated_at=CURRENT_TIMESTAMP WHERE twitch_id=?",
                tuple(params),
            )
        refreshed = self._player(player_id)
        return self._resource_state_for(refreshed, job, stats, initialize=False)

    @staticmethod
    def _resource_text_parts(resources: dict[str, Any]) -> list[str]:
        parts: list[str] = []
        if int(resources.get("max_mp", 0)) > 0:
            parts.append(f"MP {int(resources.get('mp', 0))}/{int(resources['max_mp'])}")
        if int(resources.get("max_ap", 0)) > 0:
            parts.append(f"AP {int(resources.get('ap', 0))}/{int(resources['max_ap'])}")
        return parts

    def _max_hp(self, p: Any) -> int:
        if p["current_job"] == "adventurer" or p["current_job"] not in self.data.jobs:
            return 100
        return self._stats(p, self.data.jobs[p["current_job"]])["hp"]

    def _save_hp(self, player_id: str, hp: int) -> None:
        p = self._player(player_id)
        if not p:
            return
        self.db.execute("UPDATE players SET current_hp=? WHERE twitch_id=?", (max(0, min(int(hp), self._max_hp(p))), player_id))

    def _camp_remaining(self, player_id: str) -> int:
        p = self._player(player_id)
        if not p:
            return 0
        return max(0, int(p["camp_until"] or 0) - int(time.time()))

    def _finish_rest_if_ready(self, player_id: str) -> bool:
        p = self._player(player_id)
        if not p or not p["camp_until"]:
            return False
        if int(p["camp_until"]) > int(time.time()):
            return False
        max_hp = self._max_hp(p)
        self.db.execute("UPDATE players SET current_hp=?, camp_until=0 WHERE twitch_id=?", (max_hp, player_id))
        self._restore_current_job_resources(player_id)
        return True

    def _activity_block(self, player_id: str) -> str | None:
        self._finish_rest_if_ready(player_id)
        p = self._player(player_id)
        if not p:
            return "You haven't joined the Guild."
        remaining = self._camp_remaining(player_id)
        if remaining > 0:
            return f"Your hero is resting at camp for another {self._format_seconds(remaining)}. Full HP/MP/AP recovery awaits; patience is apparently a stat now."
        if p["current_hp"] <= 0 and p["current_job"] != "adventurer":
            return "Your hero is KO'd. Use !rest for Camp recovery (15m LIVE / 1h OFFLINE base), !use phoenix down, or !use tent."
        if self._expedition_load(player_id):
            return "Your hero is currently on an Expedition. Return from the Adventure Board first."
        if self._solo_expedition_load(player_id):
            return "Your hero is currently on a Solo Venture. Return or retreat from the Adventure Board first."
        if str(player_id) in self.active_hunts:
            assignment = self.active_hunts[str(player_id)]
            hunt = self.data.hunts.get(str(assignment.get("hunt_id"))) or {}
            remaining = max(0, int(float(assignment.get("resolves_at") or 0) - time.time()))
            return f"Your hero is away on the {hunt.get('name', 'Hunt')} mark for another {self._format_seconds(remaining)}."
        return None

    def _set_cooldown(self, player_id: str, action: str, seconds: int) -> None:
        available = int(time.time()) + seconds
        self.db.execute("INSERT INTO cooldowns(player_id,action,available_at) VALUES (?,?,?) ON CONFLICT(player_id,action) DO UPDATE SET available_at=excluded.available_at", (player_id, action, available))

    def _cooldown_remaining(self, player_id: str, action: str) -> int:
        row = self.db.one("SELECT available_at FROM cooldowns WHERE player_id=? AND action=?", (player_id, action))
        return max(0, int(row["available_at"] - time.time())) if row else 0

    @staticmethod
    def _format_seconds(seconds: int) -> str:
        return format_duration(seconds)

    @staticmethod
    def _norm(value: str) -> str:
        return value.strip().lower().replace(" ", "").replace("_", "").replace("-", "").replace("'", "")

    def _find_by_name_or_id(self, mapping: dict[str, dict[str, Any]], query: str) -> dict[str, Any] | None:
        q = self._norm(query)
        for item in mapping.values():
            names = {self._norm(item["id"]), self._norm(item["name"])}
            if item.get("reveal_name"):
                names.add(self._norm(item["reveal_name"]))
            if q in names:
                return item
        return None

    def _check_achievements(self, player_id: str) -> list[str]:
        unlocked: list[str] = []
        for ach in self.data.achievements.values():
            if self.db.one("SELECT 1 FROM achievements WHERE player_id=? AND achievement_id=?", (player_id, ach["id"])):
                continue
            value = self._requirement_value(player_id, ach["condition"])
            if value >= ach["condition"].get("amount", 1):
                self.db.execute("INSERT INTO achievements(player_id, achievement_id) VALUES (?, ?)", (player_id, ach["id"]))
                unlock_name = ach.get("reveal_name", ach["name"])
                tier = ach.get("tier", "bronze").upper()
                text = f"[{tier}] {unlock_name} — {ach['description']} (+{int(ach.get('points', 0))} AP)"
                title_id = ach.get("reward_title")
                if title_id and self._unlock_title(player_id, title_id):
                    text += f" [Title: {self.data.titles[title_id]['name']}]"
                unlocked.append(text)
        return unlocked

from __future__ import annotations

import json
import logging
import os
import socket
import ssl
import threading
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import __version__ as APP_VERSION
from .engine import CrystalGuildEngine, GameResult

LOGGER = logging.getLogger("CrystalGuild.PortalActions")
ACTION_PROTOCOL_VERSION = 26


class PortalActionWorker:
    """Poll authenticated website actions and execute them in the live Bot process.

    Keeping execution inside the authoritative Bot process means current combat
    state, SQLite serialization, and all existing engine validation remain the
    single source of truth. Phase 3 adds Moogle Emporium state, purchase, and sale actions on top of
    the authenticated relay while keeping the local Bot authoritative.
    """

    def __init__(
        self,
        game: CrystalGuildEngine,
        public_url: str,
        sync_key: str,
        poll_seconds: float = 3.0,
        timeout_seconds: float = 10.0,
        verify_tls: bool = True,
        notify_result: Callable[[Any], None] | None = None,
        wake_encounter: Callable[[], None] | None = None,
        subscription_lookup: Callable[[str], dict[str, Any]] | None = None,
        stream_live_lookup: Callable[[], bool] | None = None,
        owner_id: str = "",
    ) -> None:
        self.game = game
        self.public_url = str(public_url or "").rstrip("/")
        self.sync_key = str(sync_key or "")
        self.poll_seconds = max(1.0, float(poll_seconds))
        self.timeout_seconds = max(2.0, float(timeout_seconds))
        self.verify_tls = bool(verify_tls)
        self.notify_result = notify_result
        self.wake_encounter = wake_encounter
        self.subscription_lookup = subscription_lookup
        self.stream_live_lookup = stream_live_lookup
        self.owner_id = str(owner_id or "").strip()
        self._post_ack_notifications: dict[str, list[Any]] = {}
        self.worker_id = f"bot:{socket.gethostname()}:{os.getpid()}"
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._state_lock = threading.Lock()
        self._state = "disabled" if not self.enabled else "stopped"
        self._last_success = 0
        self._last_error = ""
        self._processed = 0

    @property
    def enabled(self) -> bool:
        return bool(self.public_url and self.sync_key)

    def start(self) -> None:
        if not self.enabled:
            LOGGER.info("Portal action worker disabled: PORTAL_PUBLIC_URL/PORTAL_SYNC_KEY not configured")
            return
        with self._state_lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._wake.clear()
            self._state = "starting"
            self._thread = threading.Thread(target=self._run, name="CrystalGuildPortalActions", daemon=True)
            self._thread.start()

    def stop(self, timeout: float | None = None) -> None:
        self._stop.set()
        self._wake.set()
        thread = self._thread
        wait = max(5.0, self.timeout_seconds + 2.0) if timeout is None else max(0.0, float(timeout))
        if thread and thread.is_alive():
            thread.join(timeout=wait)
        with self._state_lock:
            if self.enabled:
                self._state = "stopped"

    def wake(self) -> None:
        self._wake.set()

    def status(self) -> dict[str, Any]:
        with self._state_lock:
            return {
                "enabled": self.enabled,
                "state": self._state,
                "last_success": self._last_success,
                "last_error": self._last_error,
                "processed": self._processed,
                "protocol_version": ACTION_PROTOCOL_VERSION,
            }

    def poll_once(self) -> int:
        if not self.enabled:
            return 0
        response = self._post(
            "/api/actions/claim",
            {"worker_id": self.worker_id, "limit": 8, "protocol_version": ACTION_PROTOCOL_VERSION},
        )
        protocol = int(response.get("protocol_version") or 0)
        if protocol != ACTION_PROTOCOL_VERSION:
            raise RuntimeError(f"Hosted Portal action protocol mismatch: {protocol} != {ACTION_PROTOCOL_VERSION}")
        actions = response.get("actions")
        if not isinstance(actions, list):
            raise RuntimeError("Hosted Portal returned an invalid action claim response.")
        processed = 0
        for action in actions:
            # Render may send SIGTERM while a claim request is in flight. Once
            # shutdown begins, leave any not-yet-executed lease to expire and be
            # reclaimed after restart instead of beginning a fresh mutation.
            if self._stop.is_set():
                break
            if not isinstance(action, dict):
                continue
            action_type = str(action.get("type") or "").strip().upper()
            twitch_id = str(action.get("twitch_id") or "").strip()
            track_titles = action_type not in {"RECRUIT", "STREAMER_COMMAND", "ACK_ADVENTURE_RESULT"}
            title_before = self._player_title_ids(twitch_id) if track_titles else set()
            ok, message, data = self._execute(action)
            if ok:
                self._stage_notable_portal_result(action, message, data)
                if track_titles:
                    self._stage_new_title_announcement(action, title_before)
            result = {
                "protocol_version": ACTION_PROTOCOL_VERSION,
                "id": str(action.get("id") or ""),
                "lease_token": str(action.get("lease_token") or ""),
                "ok": ok,
                "message": message,
                "data": data,
            }
            action_id = str(action.get("id") or "")
            try:
                self._post("/api/actions/result", result)
            except Exception:
                self._post_ack_notifications.pop(action_id, None)
                # Do not execute the same action again during this worker pass.
                # The hosted lease will expire and a later claim may retry it;
                # future mutating actions must therefore remain idempotent at the
                # game-action layer as well as in the hosted submission queue.
                LOGGER.exception("Unable to acknowledge Portal action %s", action.get("id"))
                raise
            pending = self._post_ack_notifications.pop(action_id, [])
            if pending and self.notify_result is not None:
                for announcement in pending:
                    try:
                        self.notify_result(announcement)
                    except Exception:
                        LOGGER.exception("Unable to enqueue Twitch announcement for Portal action %s", action_id)
            processed += 1
        return processed

    def _stage_post_ack_announcement(self, action_id: str, result: Any, *, live_only: bool = False) -> None:
        if self.notify_result is None or not getattr(result, "ok", False) or not getattr(result, "messages", None):
            return
        if live_only and not self._stream_live():
            return
        key = str(action_id or "").strip()
        if key:
            self._post_ack_notifications.setdefault(key, []).append(result)

    def _player_title_ids(self, twitch_id: str) -> set[str]:
        if not str(twitch_id or "").isdigit():
            return set()
        rows = self.game.db.all("SELECT title_id FROM player_titles WHERE player_id=?", (str(twitch_id),))
        return {str(row["title_id"]) for row in rows}

    def _stage_new_title_announcement(self, action: dict[str, Any], before: set[str]) -> None:
        twitch_id = str(action.get("twitch_id") or "").strip()
        after = self._player_title_ids(twitch_id)
        added = sorted(after - before)
        if not added:
            return
        player = self.game.db.one("SELECT display_name,username FROM players WHERE twitch_id=?", (twitch_id,))
        display_name = str(player["display_name"] or player["username"]) if player else "An adventurer"
        names = [str((self.game.data.titles.get(title_id) or {}).get("name") or title_id.replace("_", " ").title()) for title_id in added]
        if len(names) == 1:
            message = f"TITLE UNLOCKED — {display_name} earned {names[0]}!"
        else:
            message = f"TITLE UNLOCKED — {display_name} earned " + ", ".join(names) + "!"
        self._stage_post_ack_announcement(str(action.get("id") or ""), GameResult.success(message), live_only=True)

    def _stage_notable_portal_result(self, action: dict[str, Any], message: str, data: dict[str, Any]) -> None:
        action_type = str(action.get("type") or "").strip().upper()
        if action_type.startswith("EXPEDITION_"):
            announcement = " ".join(str(data.get("expedition_announcement") or "").split())[:360]
            if announcement:
                twitch_id = str(action.get("twitch_id") or "").strip()
                player = self.game.db.one("SELECT display_name,username FROM players WHERE twitch_id=?", (twitch_id,))
                display_name = str(player["display_name"] or player["username"]) if player else "Adventurer"
                self._stage_post_ack_announcement(
                    str(action.get("id") or ""),
                    GameResult.success(f"EXPEDITION — {display_name}: {announcement}"),
                    live_only=True,
                )
            return
        if action_type not in {
            "SOLO_VENTURE", "SOLO_EXPEDITION_ACTION", "SOLO_EXPEDITION_CONTINUE",
            "SOLO_EXPEDITION_RETURN", "SOLO_EXPEDITION_RETREAT",
        }:
            return
        # Portal Solo play can produce a result every combat round. Twitch only
        # gets the memorable beats: a completed/failed/returned run, or treasure.
        notable = bool(data.get("solo_result")) or (
            bool(data.get("solo_expedition_stage_complete")) and "treasure found" in str(message).lower()
        )
        if not notable:
            return
        twitch_id = str(action.get("twitch_id") or "").strip()
        player = self.game.db.one("SELECT display_name,username FROM players WHERE twitch_id=?", (twitch_id,))
        display_name = str(player["display_name"] or player["username"]) if player else "Adventurer"
        concise = " ".join(str(message or "Completed.").split())[:360]
        self._stage_post_ack_announcement(
            str(action.get("id") or ""),
            GameResult.success(f"SOLO — {display_name}: {concise}"),
            live_only=True,
        )

    def _wake_encounter_scheduler(self) -> None:
        if self.wake_encounter is None:
            return
        try:
            self.wake_encounter()
        except Exception:
            LOGGER.exception("Unable to wake encounter scheduler after Portal gameplay action")

    def _stream_live(self) -> bool:
        if not self.stream_live_lookup:
            return False
        try:
            return bool(self.stream_live_lookup())
        except Exception:
            LOGGER.exception("Unable to resolve Twitch stream state for Portal action; treating stream as OFFLINE.")
            return False

    def _subscriber_tier(self, twitch_id: str) -> int:
        if not self.subscription_lookup:
            return 0
        try:
            status = self.subscription_lookup(str(twitch_id)) or {}
            return max(0, min(3, int(status.get("tier") or 0)))
        except Exception:
            LOGGER.exception("Unable to resolve Twitch subscriber perk for Portal action; continuing without a perk.")
            return 0

    def _execute(self, action: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        if int(action.get("protocol_version") or 0) != ACTION_PROTOCOL_VERSION:
            return False, "Portal action protocol mismatch.", {}
        twitch_id = str(action.get("twitch_id") or "").strip()
        username = str(action.get("username") or "").strip().lower()
        action_type = str(action.get("type") or "").strip().upper()
        if not twitch_id.isdigit():
            return False, "Portal action has an invalid player identity.", {}
        payload = action.get("payload") if isinstance(action.get("payload"), dict) else {}
        if action_type == "RECRUIT":
            if not username or not username.replace("_", "a").isalnum() or len(username) > 25:
                return False, "Portal recruitment has an invalid Twitch login.", {}
            if set(payload) - {"display_name"}:
                return False, "Portal recruitment contains unsupported fields.", {}
            display_name = " ".join(str(payload.get("display_name") or username).strip().split())[:50] or username
            action_id = str(action.get("id") or "")
            result = self.game.portal_recruit(twitch_id, username, display_name, action_id)
            if result.ok and result.data.get("recruited"):
                self._stage_post_ack_announcement(action_id, result)
            return self._game_result(result)
        if action_type == "STREAMER_COMMAND":
            if not self.owner_id or twitch_id != self.owner_id:
                return False, "This Twitch account is not authorized for Streamer Controls.", {}
            return self._execute_streamer_command(action, payload)
        row = self.game.db.one(
            "SELECT username,display_name FROM players WHERE twitch_id=?",
            (twitch_id,),
        )
        if not row:
            return False, "That Crystal Guild adventurer no longer exists.", {}
        if username and str(row["username"]).lower() != username:
            return False, "Portal ownership no longer matches the authoritative character.", {}
        if action_type == "PING":
            display_name = str(row["display_name"] or row["username"])
            return True, f"Portal link verified for {display_name}.", {
                "username": str(row["username"]),
                "display_name": display_name,
            }
        passive_state_actions = {
            "CHARACTER_STATE", "SHOP_STATE", "RECOVERY_STATE", "FELLOWSHIP_STATE",
            "CRAFTING_STATE", "DAILY_STATE", "CHOCOBO_STATE", "ADVENTURE_STATE", "GOLD_SAUCER_STATE",
        }
        if action_type not in passive_state_actions:
            # Only intentional Portal mutations reset the Long Rest inactivity
            # clock. Background/read-only state polling must never keep a hero
            # artificially awake.
            self.game.record_player_action(twitch_id)
        if action_type == "EQUIP_ITEM":
            item_id = str(payload.get("item_id") or "").strip()
            if not item_id:
                return False, "Portal equipment request is missing an item.", {}
            result = self.game.equip(twitch_id, item_id)
            return self._game_result(result)
        if action_type == "UNEQUIP_SLOT":
            slot = str(payload.get("slot") or "").strip().lower()
            if slot not in {"weapon", "armor", "accessory"}:
                return False, "Portal unequip request has an invalid equipment slot.", {}
            result = self.game.unequip(twitch_id, slot)
            return self._game_result(result)
        if action_type == "SET_TITLE":
            if set(payload) != {"title_id"}:
                return False, "Portal Title request has unsupported fields.", {}
            title_id = str(payload.get("title_id") or "").strip().lower()
            if not title_id:
                return False, "Portal Title request is missing a Title.", {}
            result = self.game.set_title(twitch_id, title_id)
            return self._game_result(result)
        if action_type == "CHARACTER_STATE":
            result = self.game.portal_character_state(twitch_id)
            return self._game_result(result)
        if action_type == "CHANGE_JOB":
            job_id = str(payload.get("job_id") or "").strip()
            if not job_id:
                return False, "Character request is missing a Job.", {}
            result = self.game.portal_change_job(twitch_id, job_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SET_STANCE":
            stance = str(payload.get("stance") or "").strip().lower()
            if not stance:
                return False, "Character request is missing a stance.", {}
            result = self.game.portal_set_stance(twitch_id, stance, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SET_MASTERY":
            job_id = str(payload.get("job_id") or "").strip()
            try:
                slot = int(payload.get("slot"))
            except (TypeError, ValueError):
                return False, "Character request has an invalid Mastery slot.", {}
            if not job_id:
                return False, "Character request is missing a Mastery.", {}
            result = self.game.portal_set_mastery(twitch_id, job_id, slot, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "CLEAR_MASTERY":
            try:
                slot = int(payload.get("slot"))
            except (TypeError, ValueError):
                return False, "Character request has an invalid Mastery slot.", {}
            result = self.game.portal_clear_mastery(twitch_id, slot, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SHOP_STATE":
            result = self.game.portal_shop_state(twitch_id)
            return self._game_result(result)
        if action_type == "BUY_ITEM":
            item_id = str(payload.get("item_id") or "").strip()
            try:
                quantity = int(payload.get("quantity", 1))
            except (TypeError, ValueError):
                return False, "Portal purchase request has an invalid quantity.", {}
            if not item_id:
                return False, "Portal purchase request is missing an item.", {}
            result = self.game.portal_buy(twitch_id, item_id, quantity, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SELL_ITEM":
            item_id = str(payload.get("item_id") or "").strip()
            try:
                quantity = int(payload.get("quantity", 1))
            except (TypeError, ValueError):
                return False, "Portal sale request has an invalid quantity.", {}
            if not item_id:
                return False, "Portal sale request is missing an item.", {}
            result = self.game.portal_sell(twitch_id, item_id, quantity, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "RECOVERY_STATE":
            result = self.game.portal_recovery_state(twitch_id)
            return self._game_result(result)
        if action_type == "USE_FIELD_ITEM":
            item_id = str(payload.get("item_id") or "").strip()
            target_username = str(payload.get("target_username") or "").strip()
            if not item_id:
                return False, "Recovery request is missing an item.", {}
            result = self.game.portal_use_field_item(
                twitch_id, item_id, str(action.get("id") or ""),
                target_query=target_username or None, stream_live=self._stream_live(),
            )
            return self._game_result(result)
        if action_type == "START_REST":
            result = self.game.portal_start_rest(twitch_id, str(action.get("id") or ""), stream_live=self._stream_live())
            return self._game_result(result)
        if action_type == "FELLOWSHIP_STATE":
            result = self.game.portal_fellowship_state(twitch_id)
            return self._game_result(result)
        if action_type == "CONTRIBUTE_GIL":
            try:
                amount = int(payload.get("amount"))
            except (TypeError, ValueError):
                return False, "Fellowship contribution has an invalid Gil amount.", {}
            project_id = str(payload.get("project_id") or "").strip()
            if not project_id:
                return False, "Fellowship contribution is missing the project version. Refresh Fellowship and try again.", {}
            result = self.game.portal_contribute_gil(
                twitch_id, amount, str(action.get("id") or ""), expected_project_id=project_id
            )
            return self._game_result(result)
        if action_type == "CONTRIBUTE_ITEM":
            item_id = str(payload.get("item_id") or "").strip()
            try:
                quantity = int(payload.get("quantity"))
            except (TypeError, ValueError):
                return False, "Fellowship contribution has an invalid item quantity.", {}
            if not item_id:
                return False, "Fellowship contribution is missing an item.", {}
            project_id = str(payload.get("project_id") or "").strip()
            if not project_id:
                return False, "Fellowship contribution is missing the project version. Refresh Fellowship and try again.", {}
            result = self.game.portal_contribute_item(
                twitch_id, item_id, quantity, str(action.get("id") or ""), expected_project_id=project_id
            )
            return self._game_result(result)
        if action_type == "WORKSHOP_EXCHANGE":
            exchange_id = str(payload.get("exchange_id") or "").strip().lower()
            try:
                batches = int(payload.get("batches"))
            except (TypeError, ValueError):
                return False, "Workshop request has an invalid batch quantity.", {}
            if not exchange_id:
                return False, "Workshop request is missing a refining service.", {}
            result = self.game.portal_workshop_exchange(twitch_id, exchange_id, batches, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "CRAFTING_STATE":
            result = self.game.portal_crafting_state(twitch_id)
            return self._game_result(result)
        if action_type == "CRAFT_RECIPE":
            recipe_id = str(payload.get("recipe_id") or "").strip()
            try:
                quantity = int(payload.get("quantity"))
            except (TypeError, ValueError):
                return False, "Crafting request has an invalid quantity.", {}
            if not recipe_id:
                return False, "Crafting request is missing a recipe.", {}
            result = self.game.portal_craft_recipe(twitch_id, recipe_id, quantity, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "FORGE_ITEM":
            item_id = str(payload.get("item_id") or "").strip()
            if not item_id:
                return False, "Forge request is missing an equipment item.", {}
            result = self.game.portal_forge_item(twitch_id, item_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "GOLD_SAUCER_STATE":
            if payload:
                return False, "Gold Saucer state does not accept parameters.", {}
            return self._game_result(self.game.portal_gold_saucer_state(twitch_id))
        if action_type == "CACTPOT_START":
            if payload:
                return False, "Mini Cactpot start does not accept parameters.", {}
            return self._game_result(self.game.portal_cactpot_start(twitch_id, str(action.get("id") or "")))
        if action_type == "CACTPOT_REVEAL":
            if set(payload) != {"cell"}:
                return False, "Mini Cactpot reveal requires only cell.", {}
            try:
                cell = int(payload.get("cell"))
            except (TypeError, ValueError):
                return False, "Mini Cactpot cell is invalid.", {}
            return self._game_result(self.game.portal_cactpot_reveal(twitch_id, cell, str(action.get("id") or "")))
        if action_type == "CACTPOT_LINE":
            if set(payload) != {"line"}:
                return False, "Mini Cactpot line requires only line.", {}
            try:
                line_index = int(payload.get("line"))
            except (TypeError, ValueError):
                return False, "Mini Cactpot line is invalid.", {}
            return self._game_result(self.game.portal_cactpot_line(twitch_id, line_index, str(action.get("id") or "")))
        if action_type == "SLOTS_SPIN":
            if payload:
                return False, "Crystal Slots spin does not accept parameters.", {}
            return self._game_result(self.game.portal_slots_spin(twitch_id, str(action.get("id") or "")))
        if action_type == "SAUCER_BUY":
            if set(payload) != {"prize_id"}:
                return False, "Gold Saucer prize purchase requires only prize_id.", {}
            prize_id = str(payload.get("prize_id") or "").strip().lower()
            if not prize_id:
                return False, "Gold Saucer prize purchase is missing a prize.", {}
            return self._game_result(self.game.portal_saucer_buy(twitch_id, prize_id, str(action.get("id") or "")))
        if action_type == "DAILY_STATE":
            result = self.game.portal_daily_state(twitch_id, self._subscriber_tier(twitch_id))
            return self._game_result(result)
        if action_type == "CLAIM_DAILY":
            result = self.game.portal_claim_daily(twitch_id, str(action.get("id") or ""), self._subscriber_tier(twitch_id))
            return self._game_result(result)
        if action_type == "CHOCOBO_STATE":
            result = self.game.portal_chocobo_state(twitch_id)
            return self._game_result(result)
        if action_type == "COMPLETE_CHOCOBO_QUEST":
            result = self.game.portal_complete_chocobo_quest(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "PURCHASE_CHOCOBO_WRIT":
            result = self.game.portal_purchase_chocobo_writ(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "REGISTER_CHOCOBO":
            name = str(payload.get("name") or "").strip()
            if not name:
                return False, "Chocobo registration is missing a name.", {}
            result = self.game.portal_register_chocobo(twitch_id, name, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "RENAME_CHOCOBO":
            name = str(payload.get("name") or "").strip()
            if not name:
                return False, "Chocobo rename request is missing a name.", {}
            result = self.game.portal_rename_chocobo(twitch_id, name, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SET_CHOCOBO_PORTRAIT":
            portrait_id = str(payload.get("portrait_id") or "").strip().lower()
            if not portrait_id:
                return False, "Chocobo portrait request is missing a portrait.", {}
            result = self.game.portal_set_chocobo_portrait(
                twitch_id, portrait_id, str(action.get("id") or "")
            )
            return self._game_result(result)
        if action_type == "ADVENTURE_STATE":
            result = self.game.portal_adventure_state(twitch_id, stream_live=self._stream_live())
            return self._game_result(result)
        if action_type == "TRAVEL_REGION":
            region_id = str(payload.get("region_id") or "").strip()
            if not region_id:
                return False, "Travel request is missing a region.", {}
            result = self.game.portal_travel_region(twitch_id, region_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "EXPEDITION_START":
            region_id = str(payload.get("region_id") or "").strip().lower()
            depth_id = str(payload.get("depth") or "").strip().lower()
            if not region_id or not depth_id:
                return False, "Expedition launch requires a region and depth.", {}
            result = self.game.portal_expedition_start(twitch_id, region_id, depth_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "EXPEDITION_RESOLVE_STAGE":
            result = self.game.portal_expedition_resolve_stage(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "EXPEDITION_ACTION":
            action_kind = str(payload.get("action") or "").strip().lower()
            if not action_kind:
                return False, "Expedition combat action is missing.", {}
            result = self.game.portal_expedition_action(twitch_id, action_kind, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "EXPEDITION_CONTINUE":
            route_id = str(payload.get("route") or "unknown").strip().lower()
            result = self.game.portal_expedition_continue(twitch_id, route_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "EXPEDITION_CAMP":
            result = self.game.portal_expedition_camp(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "EXPEDITION_RETURN":
            result = self.game.portal_expedition_return(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "EXPEDITION_RETREAT":
            result = self.game.portal_expedition_retreat(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "DUNGEON_START":
            dungeon_id = str(payload.get("dungeon_id") or "").strip().lower()
            if not dungeon_id:
                return False, "Dungeon launch requires a dungeon ID.", {}
            result = self.game.portal_dungeon_start(twitch_id, dungeon_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "DUNGEON_ACTION":
            run_id = str(payload.get("run_id") or "").strip().lower()
            room_id = str(payload.get("room_id") or "").strip().lower()
            revision = max(0, int(payload.get("revision", 0) or 0))
            action_kind = str(payload.get("action") or "").strip().lower()
            if not run_id or not room_id or revision <= 0 or not action_kind:
                return False, "Dungeon action is missing its run, room, revision, or action.", {}
            result = self.game.portal_dungeon_action(twitch_id, run_id, room_id, revision, action_kind, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "DUNGEON_CONTINUE":
            run_id = str(payload.get("run_id") or "").strip().lower()
            room_id = str(payload.get("room_id") or "").strip().lower()
            revision = max(0, int(payload.get("revision", 0) or 0))
            if not run_id or not room_id or revision <= 0:
                return False, "Dungeon continue is missing its run, room, or revision.", {}
            result = self.game.portal_dungeon_continue(twitch_id, run_id, room_id, revision, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "DUNGEON_CHOICE":
            run_id = str(payload.get("run_id") or "").strip().lower()
            room_id = str(payload.get("room_id") or "").strip().lower()
            revision = max(0, int(payload.get("revision", 0) or 0))
            choice_id = str(payload.get("choice_id") or "").strip().lower()
            if not run_id or not room_id or revision <= 0 or not choice_id:
                return False, "Dungeon choice is missing its run, room, revision, or route.", {}
            result = self.game.portal_dungeon_choice(twitch_id, run_id, room_id, revision, choice_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "DUNGEON_RETREAT":
            run_id = str(payload.get("run_id") or "").strip().lower()
            room_id = str(payload.get("room_id") or "").strip().lower()
            revision = max(0, int(payload.get("revision", 0) or 0))
            if not run_id or not room_id or revision <= 0:
                return False, "Dungeon retreat is missing its run, room, or revision.", {}
            result = self.game.portal_dungeon_retreat(twitch_id, run_id, room_id, revision, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SOLO_VENTURE":
            action_id = str(action.get("id") or "")
            result = self.game.portal_solo_venture(twitch_id, action_id)
            return self._game_result(result)
        if action_type == "SOLO_EXPEDITION_ACTION":
            action_kind = str(payload.get("action") or "").strip()
            if not action_kind:
                return False, "Solo Venture action is missing.", {}
            result = self.game.portal_solo_expedition_action(twitch_id, action_kind, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SOLO_EXPEDITION_CONTINUE":
            result = self.game.portal_solo_expedition_continue(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SOLO_EXPEDITION_RETURN":
            result = self.game.portal_solo_expedition_return(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SOLO_EXPEDITION_RETREAT":
            result = self.game.portal_solo_expedition_retreat(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "CHALLENGE_HUNT":
            hunt_id = str(payload.get("hunt_id") or "").strip()
            if not hunt_id:
                return False, "Hunt request is missing a mark.", {}
            action_id = str(action.get("id") or "")
            result = self.game.portal_challenge_hunt(twitch_id, hunt_id, action_id)
            if result.ok and result.data.get("hunt_started"):
                self._wake_encounter_scheduler()
            return self._game_result(result)
        if action_type == "ACK_ADVENTURE_RESULT":
            try:
                result_id = int(payload.get("result_id") or 0)
            except (TypeError, ValueError):
                return False, "Adventure result confirmation is invalid.", {}
            if result_id <= 0:
                return False, "Adventure result confirmation is invalid.", {}
            return self._game_result(
                self.game.portal_ack_adventure_result(twitch_id, result_id, str(action.get("id") or ""))
            )
        return False, "That Portal action is not supported by this Bot build.", {}

    def _execute_streamer_command(self, action: dict[str, Any], payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        if set(payload) - {"command", "argument"} or "command" not in payload:
            return False, "Streamer Control request contains unsupported fields.", {}
        command = str(payload.get("command") or "").strip().lower().lstrip("!")
        argument = payload.get("argument", "")
        action_id = str(action.get("id") or "")

        no_arg = {
            "health", "cgversion", "encounterdebug", "directtest", "readyall",
            "resettimers", "clearadventures", "resolveencounter", "clearencounter", "resolveboss",
        }
        if command in no_arg and str(argument or "").strip():
            return False, f"{command} does not accept a Portal argument.", {}

        if command == "health":
            runtime = self.game.runtime_status()
            status = self.status()
            result = GameResult.success(
                f"CG HEALTH v{APP_VERSION} — DB={'OK' if self.game.db.health_check() else 'FAIL'} | "
                f"actions={status['state']} processed={status['processed']} | "
                f"stream={'LIVE' if self._stream_live() else 'OFFLINE'} | state={runtime['active']}.",
                runtime=runtime, portal_actions=status,
            )
            return self._game_result(result)
        if command == "economy":
            try:
                days = int(argument or 7)
            except (TypeError, ValueError):
                return False, "Economy days must be between 1 and 90.", {}
            return self._game_result(self.game.economy_report(days))
        if command == "cgversion":
            status = self.status()
            result = GameResult.success(
                f"Crystal Guild v{APP_VERSION} | Portal Action protocol {ACTION_PROTOCOL_VERSION} | "
                f"actions={status['state']} | DB={'OK' if self.game.db.health_check() else 'FAIL'}.",
                version=APP_VERSION, protocol_version=ACTION_PROTOCOL_VERSION, portal_actions=status,
            )
            return self._game_result(result)
        if command == "encounterdebug":
            snapshot = self.game.combat_snapshot()
            active = snapshot.get("encounter")
            if active:
                result = GameResult.success(
                    f"Encounter debug — id={active.get('id')} kind={active.get('kind','encounter')} "
                    f"round={active.get('round', 0)} roster={snapshot.get('encounter_roster', 0)}.",
                    encounter=active, roster=snapshot.get("encounter_roster"),
                )
            else:
                result = GameResult.success("Encounter debug — no active field encounter.", encounter=None)
            return self._game_result(result)
        if command == "directtest":
            if not self._stream_live():
                return self._game_result(GameResult.success(
                    "Direct Twitch API test not sent because the stream is OFFLINE.", sent=False
                ))
            self._stage_post_ack_announcement(
                action_id,
                GameResult.success("Crystal Guild direct API PASS. Streamer Portal announcements can reach Twitch chat."),
                live_only=True,
            )
            return self._game_result(GameResult.success("Direct Twitch API test queued for Twitch chat.", sent=True))
        if command == "fellowshipproject":
            text = " ".join(str(argument or "").strip().split())
            if not text:
                return False, "Choose a Fellowship project first.", {}
            return self._game_result(self.game.set_fellowship_project(text))
        if command == "airshipmission":
            text = " ".join(str(argument or "").strip().split())
            if not text:
                return False, "Choose an Airship mission first.", {}
            return self._game_result(self.game.set_airship_mission(text))
        if command == "readyall":
            return self._game_result(self.game.ready_all_players())
        if command == "resettimers":
            return self._game_result(self.game.reset_all_player_timers())
        if command == "clearadventures":
            result = self.game.clear_all_adventures()
            if result.ok:
                self._wake_encounter_scheduler()
            return self._game_result(result)
        if command == "resolveencounter":
            return self._game_result(self.game.resolve_encounter())
        if command == "clearencounter":
            return self._game_result(self.game.abort_encounter())
        if command == "spawnboss":
            text = " ".join(str(argument or "").strip().split())
            if not text:
                return False, "Choose a boss first.", {}
            result = self.game.spawn_boss(text)
            if result.ok and result.data.get("raid_spawned"):
                self._wake_encounter_scheduler()
                # Portal-origin raid spawns should behave like the owner chat
                # command while LIVE: publish the boss + rally call only after
                # the hosted action acknowledgement succeeds.
                self._stage_post_ack_announcement(action_id, result, live_only=True)
            return self._game_result(result)
        if command == "resolveboss":
            return self._game_result(self.game.resolve_boss())
        if command == "saucergrant":
            text = str(argument or "").strip()
            if not text:
                return False, "saucergrant requires player | amount.", {}
            return self._game_result(self.game.streamer_saucer_grant(text, action_id=action_id))
        if command == "saucerreset":
            text = str(argument or "").strip()
            if not text:
                return False, "saucerreset requires an exact player username.", {}
            return self._game_result(self.game.streamer_saucer_reset(text, action_id=action_id))
        if command in {"additem", "removeitem"}:
            text = str(argument or "").strip()
            if not text:
                return False, f"{command} requires player | item | quantity.", {}
            result = self.game.streamer_item_admin(
                text, remove=(command == "removeitem"), action_id=action_id
            )
            return self._game_result(result)
        return False, "That streamer command is not available through the Portal.", {}

    @staticmethod
    def _game_result(result: Any) -> tuple[bool, str, dict[str, Any]]:
        messages = list(getattr(result, "messages", []) or [])
        message = " ".join(str(value).strip() for value in messages if str(value).strip())
        data = getattr(result, "data", {})
        return bool(getattr(result, "ok", False)), message or ("Completed." if getattr(result, "ok", False) else "Action failed."), dict(data) if isinstance(data, dict) else {}

    def _run(self) -> None:
        failures = 0
        with self._state_lock:
            self._state = "running"
        while not self._stop.is_set():
            try:
                processed = self.poll_once()
                failures = 0
                with self._state_lock:
                    self._state = "running"
                    self._last_success = int(time.time())
                    self._last_error = ""
                    self._processed += processed
                delay = 0.4 if processed else self.poll_seconds
            except Exception as exc:
                failures += 1
                delay = min(60.0, self.poll_seconds * (2 ** min(failures, 4)))
                with self._state_lock:
                    self._state = "degraded"
                    self._last_error = f"{type(exc).__name__}: {exc}"
                LOGGER.warning("Portal action poll failed: %s | retrying in %.1fs", exc, delay)
            self._wake.wait(timeout=delay)
            self._wake.clear()
        with self._state_lock:
            self._state = "stopped"

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        request = Request(
            f"{self.public_url}{path}",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "X-Crystal-Guild-Key": self.sync_key,
                "User-Agent": "CrystalGuildPortalActions/1.0",
            },
        )
        context = None
        if self.public_url.lower().startswith("https://") and not self.verify_tls:
            context = ssl._create_unverified_context()  # noqa: SLF001 - explicit local-testing opt-out.
        try:
            with urlopen(request, timeout=self.timeout_seconds, context=context) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {text[:500]}") from exc
        except URLError as exc:
            raise RuntimeError(f"Cannot reach hosted Portal: {exc.reason}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("Hosted Portal returned an invalid response.")
        if not data.get("ok"):
            raise RuntimeError(str(data.get("error") or "Hosted Portal rejected the action request."))
        return data

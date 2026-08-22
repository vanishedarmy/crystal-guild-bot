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

from .engine import CrystalGuildEngine

LOGGER = logging.getLogger("CrystalGuild.PortalActions")
ACTION_PROTOCOL_VERSION = 12


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
    ) -> None:
        self.game = game
        self.public_url = str(public_url or "").rstrip("/")
        self.sync_key = str(sync_key or "")
        self.poll_seconds = max(1.0, float(poll_seconds))
        self.timeout_seconds = max(2.0, float(timeout_seconds))
        self.verify_tls = bool(verify_tls)
        self.notify_result = notify_result
        self.wake_encounter = wake_encounter
        self._post_ack_notifications: dict[str, Any] = {}
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
            ok, message, data = self._execute(action)
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
            pending = self._post_ack_notifications.pop(action_id, None)
            if pending is not None and self.notify_result is not None:
                try:
                    self.notify_result(pending)
                except Exception:
                    LOGGER.exception("Unable to enqueue Twitch announcement for Portal action %s", action_id)
            processed += 1
        return processed

    def _stage_post_ack_announcement(self, action_id: str, result: Any) -> None:
        if self.notify_result is None or not getattr(result, "ok", False) or not getattr(result, "messages", None):
            return
        key = str(action_id or "").strip()
        if key:
            self._post_ack_notifications[key] = result

    def _wake_encounter_scheduler(self) -> None:
        if self.wake_encounter is None:
            return
        try:
            self.wake_encounter()
        except Exception:
            LOGGER.exception("Unable to wake encounter scheduler after Portal gameplay action")

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
            if not item_id:
                return False, "Recovery request is missing an item.", {}
            result = self.game.portal_use_field_item(twitch_id, item_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "START_REST":
            result = self.game.portal_start_rest(twitch_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "FELLOWSHIP_STATE":
            result = self.game.portal_fellowship_state(twitch_id)
            return self._game_result(result)
        if action_type == "CONTRIBUTE_GIL":
            try:
                amount = int(payload.get("amount"))
            except (TypeError, ValueError):
                return False, "Fellowship contribution has an invalid Gil amount.", {}
            result = self.game.portal_contribute_gil(twitch_id, amount, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "CONTRIBUTE_ITEM":
            item_id = str(payload.get("item_id") or "").strip()
            try:
                quantity = int(payload.get("quantity"))
            except (TypeError, ValueError):
                return False, "Fellowship contribution has an invalid item quantity.", {}
            if not item_id:
                return False, "Fellowship contribution is missing an item.", {}
            result = self.game.portal_contribute_item(twitch_id, item_id, quantity, str(action.get("id") or ""))
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
        if action_type == "DAILY_STATE":
            result = self.game.portal_daily_state(twitch_id)
            return self._game_result(result)
        if action_type == "CLAIM_DAILY":
            result = self.game.portal_claim_daily(twitch_id, str(action.get("id") or ""))
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
        if action_type == "ADVENTURE_STATE":
            result = self.game.portal_adventure_state(twitch_id)
            return self._game_result(result)
        if action_type == "TRAVEL_REGION":
            region_id = str(payload.get("region_id") or "").strip()
            if not region_id:
                return False, "Travel request is missing a region.", {}
            result = self.game.portal_travel_region(twitch_id, region_id, str(action.get("id") or ""))
            return self._game_result(result)
        if action_type == "SOLO_VENTURE":
            action_id = str(action.get("id") or "")
            # Solo Venture is a Portal-only, one-click activity. Encounter
            # rounds resolve synchronously inside the engine, so there is no
            # lingering battle to wake and nothing is bridged into Twitch.
            result = self.game.portal_solo_venture(twitch_id, action_id)
            return self._game_result(result)
        if action_type == "CHALLENGE_HUNT":
            hunt_id = str(payload.get("hunt_id") or "").strip()
            if not hunt_id:
                return False, "Hunt request is missing a mark.", {}
            action_id = str(action.get("id") or "")
            result = self.game.portal_challenge_hunt(twitch_id, hunt_id, action_id)
            if result.ok and result.data.get("hunt_started"):
                self._stage_post_ack_announcement(action_id, result)
                self._wake_encounter_scheduler()
            return self._game_result(result)
        return False, "That Portal action is not supported by this Bot build.", {}

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

from __future__ import annotations

import json
import logging
import queue
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from .engine import CrystalGuildEngine, GameResult

LOGGER = logging.getLogger("CrystalGuild")


class TwitchChatDeliveryError(RuntimeError):
    """Raised when Twitch accepted a request but did not send the chat message."""


def _packed_messages(messages: list[str], *, max_length: int = 480, max_messages: int = 4) -> list[str]:
    """Pack result lines into fewer Twitch messages without exceeding limits."""
    packed: list[str] = []
    current = ""
    for raw in messages:
        message = " ".join(str(raw).split())
        if not message:
            continue
        # Preserve all content by chunking unusually long engine lines.
        chunks = [message[i : i + max_length] for i in range(0, len(message), max_length)]
        for chunk in chunks:
            candidate = f"{current} | {chunk}" if current else chunk
            if len(candidate) <= max_length:
                current = candidate
            else:
                if current:
                    packed.append(current)
                current = chunk
            if len(packed) >= max_messages:
                return packed[:max_messages]
    if current and len(packed) < max_messages:
        packed.append(current)
    return packed[:max_messages]


class TwitchRESTChatSender:
    """Synchronous Twitch Send Chat Message API client.

    Timed combat announcements deliberately do not depend on TwitchIO/EventSub.
    Requests are retried conservatively for transient Twitch/network failures,
    and a HTTP 200 is not considered successful unless Twitch says is_sent=true.
    """

    TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    CHAT_URL = "https://api.twitch.tv/helix/chat/messages"
    USER_AGENT = "CrystalGuild/1.1.17-Arsenal-II"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        bot_id: str,
        owner_id: str,
        *,
        timeout: float = 8.0,
        max_attempts: int = 3,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.bot_id = str(bot_id)
        self.owner_id = str(owner_id)
        self.timeout = max(2.0, float(timeout))
        self.max_attempts = max(1, int(max_attempts))
        self._access_token = ""
        self._token_expires_at = 0.0
        self._token_lock = threading.RLock()

    def _read_json(self, response: Any) -> dict[str, Any]:
        raw = response.read()
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _get_app_token(self, *, force_refresh: bool = False) -> str:
        with self._token_lock:
            now = time.time()
            if not force_refresh and self._access_token and now < self._token_expires_at - 90:
                return self._access_token

            form = urllib.parse.urlencode(
                {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                self.TOKEN_URL,
                data=form,
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": self.USER_AGENT,
                },
            )
            last_exc: Exception | None = None
            for attempt in range(self.max_attempts):
                try:
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        payload = self._read_json(response)
                    token = str(payload["access_token"])
                    expires_in = int(payload.get("expires_in", 3600))
                    self._access_token = token
                    self._token_expires_at = time.time() + expires_in
                    LOGGER.info("Crystal Guild acquired Twitch App Access Token")
                    return token
                except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
                    last_exc = exc
                    if attempt + 1 >= self.max_attempts:
                        break
                    time.sleep(0.35 * (2**attempt))
            raise RuntimeError(f"Unable to acquire Twitch App Access Token: {last_exc}") from last_exc

    def _send_once(self, message: str, token: str) -> None:
        body = json.dumps(
            {
                "broadcaster_id": self.owner_id,
                "sender_id": self.bot_id,
                "message": message[:480],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.CHAT_URL,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Client-Id": self.client_id,
                "Content-Type": "application/json",
                "User-Agent": self.USER_AGENT,
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = self._read_json(response)
        data = payload.get("data") or []
        if not data or not bool(data[0].get("is_sent")):
            reason = (data[0].get("drop_reason") if data else None) or {}
            code = reason.get("code", "unknown")
            detail = reason.get("message", "Twitch did not confirm delivery")
            raise TwitchChatDeliveryError(f"{code}: {detail}")

    @staticmethod
    def _retry_delay(exc: urllib.error.HTTPError, attempt: int) -> float:
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if retry_after:
            try:
                return min(5.0, max(0.25, float(retry_after)))
            except ValueError:
                pass
        reset = exc.headers.get("Ratelimit-Reset") if exc.headers else None
        if reset:
            try:
                return min(5.0, max(0.25, float(reset) - time.time()))
            except ValueError:
                pass
        return min(4.0, 0.4 * (2**attempt))

    def send(self, message: str) -> None:
        token = self._get_app_token()
        last_exc: Exception | None = None
        refreshed = False
        for attempt in range(self.max_attempts):
            try:
                self._send_once(message, token)
                return
            except TwitchChatDeliveryError:
                # Automod/blocked-content style failures are definitive, not transient.
                raise
            except urllib.error.HTTPError as exc:
                last_exc = exc
                if exc.code == 401 and not refreshed:
                    token = self._get_app_token(force_refresh=True)
                    refreshed = True
                    continue
                if exc.code == 429 or 500 <= exc.code <= 599:
                    if attempt + 1 < self.max_attempts:
                        time.sleep(self._retry_delay(exc, attempt))
                        continue
                raise
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = exc
                if attempt + 1 < self.max_attempts:
                    time.sleep(min(4.0, 0.4 * (2**attempt)))
                    continue
                raise
        if last_exc:
            raise last_exc

    def send_result(self, result: GameResult, limit: int | None = None) -> None:
        """Send one engine result using its presentation-aware message budget.

        Timed battle results may request a smaller automatic-chat
        budget without changing command responses or combat resolution. Final
        Venture/Raid settlements can also carry one personal result line per
        participant. Those lines deliberately bypass message packing so every
        viewer keeps their own @-mentioned, easy-to-scan result.
        """
        resolved_limit = int(limit if limit is not None else result.data.get("notification_limit", 4))
        resolved_limit = max(1, min(6, resolved_limit))
        packed = _packed_messages(result.messages, max_messages=resolved_limit)
        for message in packed:
            self.send(message)
        personal = [
            " ".join(str(message).split())[:480]
            for message in list(result.data.get("participant_result_messages") or [])
            if str(message).strip()
        ]
        delay = max(0.0, min(2.5, float(result.data.get("participant_message_delay_seconds", 1.5) or 0.0)))
        for index, message in enumerate(personal):
            if delay > 0 and (packed or index > 0):
                time.sleep(delay)
            self.send(message)


class NotificationDispatcher:
    """Non-blocking outbound queue for autonomous game announcements."""

    def __init__(
        self,
        sender: TwitchRESTChatSender,
        *,
        max_queue: int = 256,
        delivery_allowed: Callable[[], bool] | None = None,
    ) -> None:
        self.sender = sender
        self.delivery_allowed = delivery_allowed
        self._queue: queue.Queue[GameResult | None] = queue.Queue(maxsize=max_queue)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_error: str | None = None
        self._sent_batches = 0
        self._failed_batches = 0
        self._suppressed_batches = 0

    @property
    def is_alive(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        if self.is_alive:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="crystal-guild-notifier", daemon=True)
        self._thread.start()
        LOGGER.info("Crystal Guild notification dispatcher STARTED")

    def stop(self, timeout: float = 4.0) -> None:
        self._stop.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=timeout)
        LOGGER.info("Crystal Guild notification dispatcher STOPPED")

    def enqueue(self, result: GameResult) -> None:
        if not result.messages:
            return
        try:
            self._queue.put_nowait(result)
        except queue.Full:
            self._failed_batches += 1
            self._last_error = "notification queue full"
            LOGGER.error("Crystal Guild notification queue is full; announcement dropped")

    def status(self) -> dict[str, Any]:
        return {
            "state": "ALIVE" if self.is_alive else "DEAD",
            "queued": self._queue.qsize(),
            "sent_batches": self._sent_batches,
            "failed_batches": self._failed_batches,
            "suppressed_batches": self._suppressed_batches,
            "last_error": self._last_error or "none",
        }

    def _run(self) -> None:
        while not self._stop.is_set() or not self._queue.empty():
            try:
                item = self._queue.get(timeout=0.4)
            except queue.Empty:
                continue
            if item is None:
                self._queue.task_done()
                continue
            try:
                if self.delivery_allowed is not None and not bool(self.delivery_allowed()):
                    self._suppressed_batches += 1
                    self._last_error = None
                    LOGGER.info("Crystal Guild suppressed autonomous Twitch announcement because the stream is offline or unavailable")
                else:
                    self.sender.send_result(item)
                    self._sent_batches += 1
                    self._last_error = None
            except Exception as exc:
                self._failed_batches += 1
                self._last_error = f"{type(exc).__name__}: {exc}"
                LOGGER.exception("Crystal Guild autonomous Twitch announcement failed")
            finally:
                self._queue.task_done()


class EncounterDaemon:
    """Independent combat director for encounters and raid progression.

    Despite the historical class name, this director owns every autonomous combat deadline:
    Rally Venture rounds, personal timed-Hunt returns, raid rally start, and raid combat rounds.
    Legacy pre-hotfix Hunt round checkpoints are also allowed to finish safely. It does not
    require Twitch chat activity or the TwitchIO asyncio scheduler.
    """

    def __init__(
        self,
        game: CrystalGuildEngine,
        notify: Callable[[GameResult], None],
        *,
        poll_interval: float = 0.75,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.game = game
        self.notify = notify
        # poll_interval is now a recovery/self-check ceiling, not timer
        # granularity. Known combat deadlines wake at their actual due time.
        self.poll_interval = max(0.05, float(poll_interval))
        self._clock = clock
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._ticks = 0
        self._last_tick = 0.0
        self._last_error: str | None = None
        self._last_resolved_id: int | None = None
        self._last_raid_id: str | None = None
        self._last_action = "idle"
        self._last_deadline = "none"
        self._last_timer_lag_ms = 0
        self._next_due_in_ms = -1
        self._consecutive_failures = 0
        self._retry_backoff_ms = 0
        self._next_passive_recovery_scan = 0.0

    @property
    def is_alive(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def ticks(self) -> int:
        return self._ticks

    @property
    def last_tick_age(self) -> int:
        if not self._last_tick:
            return -1
        return max(0, int(time.monotonic() - self._last_tick))

    @property
    def last_resolved_id(self) -> int | None:
        return self._last_resolved_id

    def start(self) -> None:
        if self.is_alive:
            return
        self._stop.clear()
        self._wake.clear()
        self._thread = threading.Thread(target=self._run, name="crystal-guild-game-daemon", daemon=True)
        self._thread.start()
        LOGGER.info("Crystal Guild combat daemon STARTED")

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        self._wake.set()
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=timeout)
        LOGGER.info("Crystal Guild combat daemon STOPPED")

    def wake(self) -> None:
        self._wake.set()

    def status(self) -> dict[str, Any]:
        return {
            "state": "ALIVE" if self.is_alive else "DEAD",
            "ticks": self.ticks,
            "last_tick_age": self.last_tick_age,
            "last_error": self.last_error or "none",
            "last_resolved_id": self.last_resolved_id if self.last_resolved_id is not None else "none",
            "last_raid_id": self._last_raid_id or "none",
            "last_action": self._last_action,
            "last_deadline": self._last_deadline,
            "timer_lag_ms": self._last_timer_lag_ms,
            "next_due_in_ms": self._next_due_in_ms,
            "consecutive_failures": self._consecutive_failures,
            "retry_backoff_ms": self._retry_backoff_ms,
        }

    @staticmethod
    def _deadlines(snapshot: dict[str, Any]) -> list[tuple[str, float]]:
        """Return currently scheduled live-combat deadlines.

        Keep this extraction side-effect free. Chat commands may wake the daemon
        after *creating* a timer, but only this scheduler decides when it is due.
        """
        deadlines: list[tuple[str, float]] = []
        encounter = snapshot.get("encounter")
        if encounter:
            if encounter.get("state", "rally") == "rally":
                due = float(encounter.get("closes_at") or 0)
                if due:
                    deadlines.append(("encounter-rally", due))
            else:
                due = float(encounter.get("next_round_at") or 0)
                if due:
                    label = "hunt-round" if encounter.get("kind") == "hunt" else "encounter-round"
                    deadlines.append((label, due))
        for hunt in snapshot.get("hunts") or []:
            due = float(hunt.get("resolves_at") or 0)
            if due:
                deadlines.append((f"hunt:{hunt.get('player_id')}:{hunt.get('id')}", due))
        boss = snapshot.get("boss")
        if boss:
            if boss.get("state") == "rally":
                due = float(boss.get("closes_at") or 0)
                if due:
                    deadlines.append(("raid-rally", due))
            elif boss.get("state") == "combat":
                due = float(boss.get("next_round_at") or 0)
                if due:
                    deadlines.append(("raid-round", due))
        return deadlines

    def _wait_timeout(self, snapshot: dict[str, Any]) -> float:
        deadlines = self._deadlines(snapshot)
        if not deadlines:
            self._next_due_in_ms = -1
            return self.poll_interval
        _, due = min(deadlines, key=lambda item: item[1])
        remaining = due - self._clock()
        self._next_due_in_ms = max(0, int(remaining * 1000))
        if remaining <= 0:
            return 0.005
        return max(0.005, min(self.poll_interval, remaining))

    def _record_deadline(self, label: str, due: float, now: float) -> None:
        self._last_deadline = label
        self._last_timer_lag_ms = max(0, int((now - due) * 1000))

    def _publish(self, result: GameResult) -> bool:
        if not result.messages:
            return True
        try:
            self.notify(result)
            if (self._last_error or "").startswith("notify "):
                self._last_error = None
            return True
        except Exception as exc:
            self._last_error = f"notify {type(exc).__name__}: {exc}"
            LOGGER.exception("Combat resolved, but notification dispatch failed")
            return False

    def _tick_encounter(self, snapshot: dict[str, Any], now: float) -> bool:
        """Advance one encounter deadline without collapsing the whole battle.

        Active Battle uses the same autonomous daemon as raids: rally close
        starts combat, then each round deadline resolves exactly one round.
        """
        active = snapshot.get("encounter")
        if not active:
            return False
        encounter_id = int(active["id"])
        state = active.get("state", "rally")
        if state == "rally":
            due = float(active.get("closes_at") or 0)
            if due > now:
                return False
            self._record_deadline("encounter-rally", due, now)
            LOGGER.info("Combat daemon starting active encounter %s", encounter_id)
            result = self.game.start_encounter_battle(encounter_id)
            self._last_action = f"encounter-start:{encounter_id}"
        else:
            due = float(active.get("next_round_at") or 0)
            if not due or due > now:
                return False
            label = "hunt-round" if active.get("kind") == "hunt" else "encounter-round"
            self._record_deadline(label, due, now)
            LOGGER.info(
                "Combat daemon advancing %s %s round %s",
                "hunt" if active.get("kind") == "hunt" else "encounter",
                encounter_id,
                active.get("round"),
            )
            result = self.game.advance_encounter_round(encounter_id)
            self._last_action = f"encounter-round:{encounter_id}:{active.get('round')}"
        if result.ok:
            if result.data.get("encounter_finished"):
                self._last_resolved_id = encounter_id
            # New Solo Ventures resolve inside the Portal request. Keep this
            # silence rule for any pre-hotfix Solo battle recovered from saved
            # runtime state; normal Rally Venture and Hunts keep announcements.
            if active.get("kind") != "solo_venture":
                self._publish(result)
        return True

    def _tick_hunts(self, snapshot: dict[str, Any], now: float) -> bool:
        """Resolve all personal Hunt assignments whose rank timer has expired."""
        acted = False
        for hunt in list(snapshot.get("hunts") or []):
            due = float(hunt.get("resolves_at") or 0)
            if not due or due > now:
                continue
            player_id = str(hunt.get("player_id") or "")
            run_id = int(hunt.get("id") or 0)
            self._record_deadline(f"hunt:{player_id}:{run_id}", due, now)
            LOGGER.info("Combat daemon resolving timed Hunt %s for player %s", run_id, player_id)
            result = self.game.resolve_hunt(player_id, run_id)
            self._last_action = f"hunt-resolve:{player_id}:{run_id}"
            if result.ok:
                self._last_resolved_id = run_id
                self._publish(result)
            acted = True
        return acted

    def _tick_raid(self, snapshot: dict[str, Any], now: float) -> bool:
        boss = snapshot.get("boss")
        if not boss:
            return False
        boss_id = str(boss["id"])
        state = boss.get("state")
        if state == "rally" and float(boss.get("closes_at") or 0) <= now:
            due = float(boss.get("closes_at") or 0)
            self._record_deadline("raid-rally", due, now)
            LOGGER.info("Combat daemon starting raid %s after rally", boss_id)
            result = self.game.start_raid(boss_id)
            self._last_raid_id = boss_id
            self._last_action = f"raid-start:{boss_id}"
            self._publish(result)
            return True
        if state == "combat":
            due = float(boss.get("next_round_at") or 0)
            if due and due <= now:
                self._record_deadline("raid-round", due, now)
                LOGGER.info("Combat daemon advancing raid %s round", boss_id)
                result = self.game.raid_round(
                    boss_id,
                    expected_instance_id=boss.get("raid_instance_id"),
                    expected_round=int(boss.get("round", 0)),
                )
                self._last_raid_id = boss_id
                self._last_action = f"raid-round:{boss_id}:{int(boss.get('round', 0))}"
                self._publish(result)
                return True
        return False

    def _run(self) -> None:
        while not self._stop.is_set():
            self._ticks += 1
            self._last_tick = time.monotonic()
            snapshot: dict[str, Any] = {}
            failed = False
            try:
                now = self._clock()
                if now >= self._next_passive_recovery_scan:
                    recovery = self.game.refresh_due_long_rests(now=int(now))
                    self._next_passive_recovery_scan = now + 60.0
                    if int(recovery.get("count") or 0) > 0:
                        self._last_action = f"long-rest:{int(recovery['count'])}"
                snapshot = self.game.combat_snapshot()
                hunt_acted = self._tick_hunts(snapshot, now)
                if hunt_acted:
                    snapshot = self.game.combat_snapshot()
                acted = self._tick_encounter(snapshot, self._clock())
                # Re-snapshot after every autonomous transition so the next
                # calculated sleep is based on the newly-created deadline.
                if acted:
                    snapshot = self.game.combat_snapshot()
                raid_acted = self._tick_raid(snapshot, self._clock())
                if raid_acted:
                    snapshot = self.game.combat_snapshot()
                # Preserve a notification-delivery diagnostic until a later
                # notification succeeds. A successful game tick must not erase
                # evidence that Twitch transport failed after resolution.
                if not (self._last_error or "").startswith("notify "):
                    self._last_error = None
                self._consecutive_failures = 0
                self._retry_backoff_ms = 0
            except Exception as exc:
                failed = True
                self._consecutive_failures += 1
                backoff = min(15.0, 0.5 * (2 ** min(self._consecutive_failures - 1, 5)))
                self._retry_backoff_ms = int(backoff * 1000)
                self._last_error = f"{type(exc).__name__}: {exc}"
                LOGGER.exception(
                    "Crystal Guild combat daemon failed tick %s; retry backoff %.2fs",
                    self._consecutive_failures,
                    backoff,
                )
                # The atomic Crystal state guard restores the last committed
                # combat checkpoint. Retry that same deadline instead of
                # abandoning the battle or spinning the CPU/logs.
                snapshot = self.game.combat_snapshot()

            timeout = self._wait_timeout(snapshot)
            if failed:
                timeout = max(timeout, self._retry_backoff_ms / 1000.0)
            self._wake.wait(timeout=timeout)
            self._wake.clear()

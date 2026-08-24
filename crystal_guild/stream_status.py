from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

LOGGER = logging.getLogger("CrystalGuild")


class TwitchStreamStatus:
    """Cached Twitch channel-live probe used to gate live-stream gameplay.

    Crystal Guild stays online even when the Twitch channel is offline, so chat
    commands that represent live-stream participation need a separate presence
    check. Twitch's Get Streams endpoint accepts an app access token and returns
    an empty data list when the broadcaster is not currently live.

    Successful results are cached briefly to avoid turning chat traffic into an
    API request storm. If Twitch has a temporary API/network failure, the last
    successful result remains authoritative only for ``stale_seconds``; after
    that the effective state becomes UNKNOWN and live-only mutations fail
    closed until Twitch can be checked again.
    """

    TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    STREAMS_URL = "https://api.twitch.tv/helix/streams"
    USER_AGENT = "CrystalGuild/1.1.16-Arsenal-H1"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        broadcaster_id: str,
        *,
        cache_seconds: float = 15.0,
        stale_seconds: float = 90.0,
        timeout: float = 6.0,
    ) -> None:
        self.client_id = str(client_id)
        self.client_secret = str(client_secret)
        self.broadcaster_id = str(broadcaster_id)
        self.cache_seconds = max(2.0, float(cache_seconds))
        self.stale_seconds = max(self.cache_seconds, float(stale_seconds))
        self.timeout = max(2.0, float(timeout))

        self._lock = threading.RLock()
        self._access_token = ""
        self._token_expires_at = 0.0
        self._state = "UNKNOWN"
        self._last_checked_at = 0.0
        self._last_success_at = 0.0
        self._last_error = ""
        self._checks = 0
        self._title = ""
        self._game_name = ""
        self._started_at = ""

    @staticmethod
    def _read_json(response: Any) -> dict[str, Any]:
        raw = response.read()
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _get_app_token(self, *, force_refresh: bool = False) -> str:
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
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = self._read_json(response)
        token = str(payload["access_token"])
        expires_in = int(payload.get("expires_in", 3600))
        self._access_token = token
        self._token_expires_at = time.time() + expires_in
        return token

    def _query_stream(self, token: str) -> dict[str, Any]:
        query = urllib.parse.urlencode({"user_id": self.broadcaster_id})
        request = urllib.request.Request(
            f"{self.STREAMS_URL}?{query}",
            method="GET",
            headers={
                "Authorization": f"Bearer {token}",
                "Client-Id": self.client_id,
                "User-Agent": self.USER_AGENT,
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return self._read_json(response)

    def _effective_state_locked(self, now: float | None = None) -> str:
        now = time.time() if now is None else float(now)
        if not self._last_success_at:
            return "UNKNOWN"
        if now - self._last_success_at > self.stale_seconds:
            return "UNKNOWN"
        return self._state

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            now = time.time()
            effective = self._effective_state_locked(now)
            return {
                "state": effective,
                "live": effective == "LIVE",
                "last_checked_age": None if not self._last_checked_at else max(0, int(now - self._last_checked_at)),
                "last_success_age": None if not self._last_success_at else max(0, int(now - self._last_success_at)),
                "last_error": self._last_error,
                "checks": self._checks,
                "title": self._title if effective == "LIVE" else "",
                "game_name": self._game_name if effective == "LIVE" else "",
                "started_at": self._started_at if effective == "LIVE" else "",
            }

    def refresh(self, force: bool = False) -> dict[str, Any]:
        with self._lock:
            now = time.time()
            if (
                not force
                and self._last_checked_at
                and now - self._last_checked_at < self.cache_seconds
            ):
                return self.snapshot()
            self._last_checked_at = now
            self._checks += 1

            try:
                token = self._get_app_token()
                try:
                    payload = self._query_stream(token)
                except urllib.error.HTTPError as exc:
                    if exc.code != 401:
                        raise
                    token = self._get_app_token(force_refresh=True)
                    payload = self._query_stream(token)

                rows = payload.get("data") or []
                row = rows[0] if rows else None
                self._state = "LIVE" if row else "OFFLINE"
                self._last_success_at = time.time()
                self._last_error = ""
                if row:
                    self._title = str(row.get("title") or "")
                    self._game_name = str(row.get("game_name") or "")
                    self._started_at = str(row.get("started_at") or "")
                else:
                    self._title = ""
                    self._game_name = ""
                    self._started_at = ""
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError, json.JSONDecodeError) as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                LOGGER.warning("Unable to verify Twitch live status: %s", self._last_error)

            return self.snapshot()

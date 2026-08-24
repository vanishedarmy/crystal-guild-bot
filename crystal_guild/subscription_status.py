from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .daily_provisions import normalize_subscriber_tier
from .token_store import TwitchTokenStore

LOGGER = logging.getLogger("CrystalGuild.SubscriptionStatus")


class TwitchSubscriptionStatus:
    """Cached broadcaster-authoritative Twitch subscription tier lookup.

    Get Broadcaster Subscriptions requires the broadcaster's user access token
    with ``channel:read:subscriptions``. Crystal Guild reads that token from the
    durable Twitch token database, which TwitchIO keeps refreshed in cloud mode.

    A failed lookup never blocks normal gameplay. The effective result falls
    back to a recently confirmed status for a bounded stale window, then to
    UNKNOWN/no perk until Twitch can be checked again.
    """

    SUBSCRIPTIONS_URL = "https://api.twitch.tv/helix/subscriptions"
    USER_AGENT = "CrystalGuild/1.1.17-Arsenal-II"

    def __init__(
        self,
        client_id: str,
        broadcaster_id: str,
        token_store: TwitchTokenStore | None,
        *,
        cache_seconds: float = 300.0,
        stale_seconds: float = 900.0,
        timeout: float = 6.0,
    ) -> None:
        self.client_id = str(client_id)
        self.broadcaster_id = str(broadcaster_id)
        self.token_store = token_store
        self.cache_seconds = max(15.0, float(cache_seconds))
        self.stale_seconds = max(self.cache_seconds, float(stale_seconds))
        self.timeout = max(2.0, float(timeout))
        self._lock = threading.RLock()
        self._cache: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _read_json(response: Any) -> dict[str, Any]:
        raw = response.read()
        return json.loads(raw.decode("utf-8")) if raw else {}

    def _owner_access_token(self) -> str:
        if not self.token_store:
            raise RuntimeError("Twitch token database is not configured")
        row = self.token_store.get(self.broadcaster_id)
        if not row:
            raise RuntimeError("Broadcaster Twitch token is missing from the token database")
        return str(row["access_token"])

    def _query(self, token: str, user_id: str) -> dict[str, Any]:
        query = urllib.parse.urlencode(
            {"broadcaster_id": self.broadcaster_id, "user_id": str(user_id), "first": 1}
        )
        request = urllib.request.Request(
            f"{self.SUBSCRIPTIONS_URL}?{query}",
            method="GET",
            headers={
                "Authorization": f"Bearer {token}",
                "Client-Id": self.client_id,
                "User-Agent": self.USER_AGENT,
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return self._read_json(response)

    @staticmethod
    def _fresh_result(row: dict[str, Any] | None, checked_at: float) -> dict[str, Any]:
        tier_code = str((row or {}).get("tier") or "")
        tier = normalize_subscriber_tier(tier_code)
        subscribed = tier > 0
        return {
            "state": "SUBSCRIBED" if subscribed else "NOT_SUBSCRIBED",
            "subscribed": subscribed,
            "tier": tier,
            "tier_code": tier_code if subscribed else "",
            "is_gift": bool((row or {}).get("is_gift", False)) if subscribed else False,
            "checked_at": checked_at,
            "last_success_at": checked_at,
            "last_error": "",
            "scope_required": False,
        }

    def _snapshot_locked(self, user_id: str, now: float | None = None) -> dict[str, Any]:
        now = time.time() if now is None else float(now)
        cached = dict(self._cache.get(str(user_id), {}))
        if not cached:
            return {
                "state": "UNKNOWN", "subscribed": False, "tier": 0, "tier_code": "",
                "is_gift": False, "last_checked_age": None, "last_success_age": None,
                "last_error": "", "scope_required": False,
            }
        success_at = float(cached.get("last_success_at") or 0)
        checked_at = float(cached.get("checked_at") or 0)
        if not success_at or now - success_at > self.stale_seconds:
            cached["state"] = "UNKNOWN"
            cached["subscribed"] = False
            cached["tier"] = 0
            cached["tier_code"] = ""
            cached["is_gift"] = False
        cached["last_checked_age"] = None if not checked_at else max(0, int(now - checked_at))
        cached["last_success_age"] = None if not success_at else max(0, int(now - success_at))
        cached.pop("checked_at", None)
        cached.pop("last_success_at", None)
        return cached

    def snapshot(self, user_id: str) -> dict[str, Any]:
        with self._lock:
            return self._snapshot_locked(str(user_id))

    def refresh(self, user_id: str, force: bool = False) -> dict[str, Any]:
        uid = str(user_id or "").strip()
        if not uid:
            return self.snapshot(uid)
        with self._lock:
            now = time.time()
            current = self._cache.get(uid)
            checked_at = float((current or {}).get("checked_at") or 0)
            if not force and checked_at and now - checked_at < self.cache_seconds:
                return self._snapshot_locked(uid, now)

            try:
                token = self._owner_access_token()
                payload = self._query(token, uid)
                rows = payload.get("data") or []
                self._cache[uid] = self._fresh_result(rows[0] if rows else None, time.time())
            except urllib.error.HTTPError as exc:
                previous = dict(self._cache.get(uid, {}))
                previous["checked_at"] = time.time()
                previous["last_error"] = f"HTTP {exc.code}"
                previous["scope_required"] = exc.code in {401, 403}
                self._cache[uid] = previous
                if previous["scope_required"]:
                    LOGGER.warning(
                        "Unable to verify Twitch subscriber tier (HTTP %s). Re-authorize the broadcaster token with channel:read:subscriptions.",
                        exc.code,
                    )
                else:
                    LOGGER.warning("Unable to verify Twitch subscriber tier: HTTP %s", exc.code)
            except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError, ValueError, json.JSONDecodeError) as exc:
                previous = dict(self._cache.get(uid, {}))
                previous["checked_at"] = time.time()
                previous["last_error"] = f"{type(exc).__name__}: {exc}"
                previous.setdefault("scope_required", False)
                self._cache[uid] = previous
                LOGGER.warning("Unable to verify Twitch subscriber tier: %s", previous["last_error"])

            return self._snapshot_locked(uid)

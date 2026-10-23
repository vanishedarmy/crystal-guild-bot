from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import time
import logging
import threading
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import load_dotenv
from .player_snapshot import PortalRepository


SYNC_VERSION = "1.9.8-airship-expedition"
LOGGER = logging.getLogger("CrystalGuild.PortalSync")
SCHEMA_VERSION = 1
MODULES = (
    "overview",
    "jobs",
    "inventory",
    "hunts",
    "bestiary",
    "relics",
    "achievements",
    "records",
    "guild_board",
    "trophies",
    "seasonal",
)


class PortalSyncClient:
    def __init__(
        self,
        repository: PortalRepository,
        public_url: str,
        sync_key: str,
        interval: float = 5.0,
        timeout: float = 10.0,
        verify_tls: bool = True,
        heartbeat_seconds: float = 60.0,
        overlay_state_path: str | Path | None = None,
        owner_twitch_id: str | None = None,
        fellowship_prepare: Callable[[], Any] | None = None,
        player_prepare: Callable[[str], Any] | None = None,
    ):
        self.repository = repository
        self.public_url = public_url.rstrip("/")
        self.sync_key = sync_key
        self.interval = max(2.0, float(interval))
        self.timeout = max(2.0, float(timeout))
        self.verify_tls = verify_tls
        self.heartbeat_seconds = max(5.0, float(heartbeat_seconds))
        self.overlay_state_path = Path(overlay_state_path).resolve() if overlay_state_path else None
        self.owner_twitch_id = str(owner_twitch_id or os.getenv("TWITCH_OWNER_ID", "")).strip()
        self.fellowship_prepare = fellowship_prepare
        self.player_prepare = player_prepare
        self._hashes: dict[str, str] = {}
        self._fellowship_hash: str | None = None
        self._overlay_hash: str | None = None
        self._last_source_stamp: tuple[int, ...] | None = None
        self._last_overlay_stamp: tuple[int, int] | None = None
        self._last_manifest: tuple[str, ...] = ()
        self._last_heartbeat = 0.0
        self._force_full = True

    def source_stamp(self) -> tuple[int, ...]:
        db = self.repository.database_path
        paths = [db, Path(f"{db}-wal"), Path(f"{db}-shm")]
        values: list[int] = []
        for path in paths:
            try:
                stat = path.stat()
                # Keep mtime and size separate instead of XORing them; this avoids
                # a rare collision that could make a changed database look idle.
                values.extend((int(stat.st_mtime_ns), int(stat.st_size)))
            except FileNotFoundError:
                values.extend((0, 0))
        return tuple(values)

    def build_snapshot(self, username: str) -> dict[str, Any]:
        player_twitch_id = self.repository.twitch_id_for(username)
        if not player_twitch_id:
            raise RuntimeError(f"Player Twitch ID disappeared while building snapshot: {username}")
        if callable(self.player_prepare):
            # Reconcile before opening the consistent read transaction so the
            # snapshot reflects any retroactive achievement/title repairs.
            self.player_prepare(str(player_twitch_id))
        methods = {
            "overview": self.repository.overview,
            "jobs": self.repository.jobs,
            "inventory": self.repository.inventory,
            "hunts": self.repository.hunts,
            "bestiary": self.repository.bestiary,
            "relics": self.repository.relics,
            "achievements": self.repository.achievements,
            "records": self.repository.records,
            "guild_board": self.repository.guild_board,
            "trophies": getattr(self.repository, "trophies", lambda _username: {"player": {}, "unlocked": []}),
            "seasonal": getattr(self.repository, "seasonal", lambda _username: {"player": {}, "seasonal": {"state":"disabled"}}),
        }
        snapshot: dict[str, Any] = {}
        # One SQLite read transaction keeps all modules on the same WAL snapshot,
        # so a reward write cannot split overview/records/inventory across moments.
        with self.repository.consistent_read():
            for module in MODULES:
                value = methods[module](username)
                if value is None:
                    raise RuntimeError(f"Player disappeared while building snapshot: {username}")
                snapshot[module] = value
        return {
            "schema_version": SCHEMA_VERSION,
            "sync_version": SYNC_VERSION,
            "username": username,
            # Private transport metadata used only by the hosted Portal to bind
            # a Twitch OAuth session to the authoritative local character. The
            # hosted public player APIs never return this numeric Twitch ID.
            "player_twitch_id": player_twitch_id,
            "generated_at": int(time.time()),
            "snapshot": snapshot,
        }

    def build_fellowship_snapshot(self) -> dict[str, Any] | None:
        if callable(self.fellowship_prepare):
            self.fellowship_prepare()
        getter = getattr(self.repository, "fellowship", None)
        if not callable(getter):
            return None
        with self.repository.consistent_read():
            snapshot = getter()
        return {
            "schema_version": SCHEMA_VERSION,
            "sync_version": SYNC_VERSION,
            "generated_at": int(time.time()),
            "fellowship": snapshot,
        }

    def overlay_source_stamp(self) -> tuple[int, int]:
        if not self.overlay_state_path:
            return (0, 0)
        try:
            stat = self.overlay_state_path.stat()
            return (int(stat.st_mtime_ns), int(stat.st_size))
        except FileNotFoundError:
            return (0, 0)

    def build_overlay_snapshot(self) -> dict[str, Any] | None:
        path = self.overlay_state_path
        if not path or not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(raw, dict):
            return None
        allowed = {
            "active", "status", "boss", "tier", "encounter_type", "encounter_name", "hp", "max_hp", "round", "phase",
            "signature", "raiders", "alive", "ready_actions", "actionable_raiders", "enraged", "summon_gauge", "top", "adds", "mechanic", "last_mechanic", "next_round_at", "updated_at",
            "members", "boss_statuses", "rally_closes_at", "rounds_to_enrage",
        }
        overlay = {key: raw[key] for key in allowed if key in raw}
        top = overlay.get("top")
        if isinstance(top, list):
            overlay["top"] = [
                {
                    "name": str(item.get("name") or "Adventurer")[:80],
                    "role": str(item.get("role") or "DPS")[:24],
                    "damage": max(0, int(item.get("damage") or 0)),
                    "healing": max(0, int(item.get("healing") or 0)),
                    "mitigation": max(0, int(item.get("mitigation") or 0)),
                    "score": max(0, int(item.get("score") or 0)),
                }
                for item in top[:5] if isinstance(item, dict)
            ]
        else:
            overlay["top"] = []
        adds = overlay.get("adds")
        if isinstance(adds, list):
            overlay["adds"] = [
                {
                    "name": str(item.get("name") or "Add")[:80],
                    "hp": max(0, int(item.get("hp") or 0)),
                    "max_hp": max(1, int(item.get("max_hp") or 1)),
                }
                for item in adds[:4] if isinstance(item, dict)
            ]
        else:
            overlay["adds"] = []
        for field in ("mechanic", "last_mechanic"):
            mechanic = overlay.get(field)
            if not isinstance(mechanic, dict):
                overlay[field] = None
                continue
            clean = {}
            for key in ("name", "kind", "warning", "target", "result"):
                if key in mechanic and mechanic[key] is not None:
                    clean[key] = str(mechanic[key])[:160]
            for key in ("rounds_remaining", "required", "progress"):
                if key in mechanic and mechanic[key] is not None:
                    clean[key] = max(0, int(mechanic[key]))
            overlay[field] = clean or None
        # Joined-party rows and telegraphs are public overlay data. Prior
        # allowlisting silently discarded them, leaving the raid roster blank.
        members = overlay.get("members")
        if isinstance(members, list):
            safe_members = []
            for row in members[:64]:
                if not isinstance(row, dict):
                    continue
                safe = {}
                for key, size in {"name":80,"role":24,"job":40,"resource":2,
                                  "state":12,"action":56,"action_kind":24,"target":80}.items():
                    safe[key] = str(row.get(key) or "")[:size]
                for key in ("hp", "max_hp", "resource_value", "resource_max"):
                    safe[key] = max(0, int(row.get(key) or 0))
                safe["statuses"] = self._public_overlay_statuses(row.get("statuses"))
                safe_members.append(safe)
            overlay["members"] = safe_members
        else:
            overlay["members"] = []
        overlay["boss_statuses"] = self._public_overlay_statuses(overlay.get("boss_statuses"))
        for key in ("ready_actions", "actionable_raiders", "rally_closes_at"):
            overlay[key] = max(0, int(overlay.get(key) or 0))
        return {
            "schema_version": SCHEMA_VERSION,
            "sync_version": SYNC_VERSION,
            "generated_at": int(time.time()),
            "overlay": overlay,
        }

    @staticmethod
    def _public_overlay_statuses(rows: Any) -> list[dict[str, Any]]:
        if not isinstance(rows, list):
            return []
        result = []
        for entry in rows[:12]:
            if not isinstance(entry, dict):
                continue
            token = str(entry.get("id") or "")
            turns = int(entry.get("turns") or 0)
            if token and len(token) <= 32 and all(c.isalnum() or c == "_" for c in token) and 1 <= turns <= 99:
                result.append({"id": token, "turns": turns})
        return result

    @staticmethod
    def snapshot_hash(payload: dict[str, Any]) -> str:
        stable = dict(payload)
        stable.pop("generated_at", None)
        encoded = json.dumps(stable, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def sync_once(
        self,
        force: bool = False,
        should_stop: Callable[[], bool] | None = None,
    ) -> dict[str, int]:
        stamp = self.source_stamp()
        overlay_stamp = self.overlay_source_stamp()
        now = time.monotonic()
        source_changed = force or self._force_full or stamp != self._last_source_stamp
        overlay_changed = force or self._force_full or overlay_stamp != self._last_overlay_stamp
        heartbeat_due = force or self._force_full or (now - self._last_heartbeat) >= self.heartbeat_seconds
        if not source_changed and not overlay_changed and not heartbeat_due:
            return {"players": len(self._hashes), "changed": 0, "removed": 0, "overlay": 0}

        players = self.repository.list_players()
        usernames = tuple(sorted(str(player["username"]).lower() for player in players))
        changed = 0

        def stopping() -> bool:
            return bool(should_stop and should_stop())

        if stopping():
            self._force_full = True
            return {"players": len(usernames), "changed": 0, "removed": 0}
        uploaded: set[str] = set()
        overlay_uploaded = 0

        fellowship_payload = None
        fellowship_digest = None
        if source_changed:
            if stopping():
                self._force_full = True
                return {"players": len(usernames), "changed": changed, "removed": 0, "overlay": 0}
            fellowship_payload = self.build_fellowship_snapshot()
            if fellowship_payload is not None:
                fellowship_digest = self.snapshot_hash(fellowship_payload)
                if force or self._fellowship_hash != fellowship_digest:
                    self._post("/api/sync/fellowship", fellowship_payload)
                    self._fellowship_hash = fellowship_digest

        overlay_payload = None
        overlay_digest = None
        if overlay_changed:
            overlay_payload = self.build_overlay_snapshot()
            if overlay_payload is not None:
                overlay_digest = self.snapshot_hash(overlay_payload)
                if force or self._overlay_hash != overlay_digest:
                    self._post("/api/sync/overlay", overlay_payload)
                    self._overlay_hash = overlay_digest
                    overlay_uploaded = 1

        if source_changed:
            for username in usernames:
                if stopping():
                    self._force_full = True
                    return {"players": len(usernames), "changed": changed, "removed": 0, "overlay": overlay_uploaded}
                payload = self.build_snapshot(username)
                digest = self.snapshot_hash(payload)
                # _force_full means "inspect every local hero", not "re-upload
                # every hero on every retry". A successful player upload records
                # its hash immediately so a later failure resumes at the first
                # unsent/changed hero instead of creating a recovery storm.
                if force or self._hashes.get(username) != digest:
                    self._post("/api/sync/player", payload)
                    self._hashes[username] = digest
                    uploaded.add(username)
                    changed += 1

        removed_local = set(self._hashes) - set(usernames)
        for username in removed_local:
            self._hashes.pop(username, None)

        removed = 0
        if heartbeat_due or usernames != self._last_manifest:
            response = self._post(
                "/api/sync/manifest",
                {
                    "schema_version": SCHEMA_VERSION,
                    "sync_version": SYNC_VERSION,
                    "usernames": list(usernames),
                    "owner_twitch_id": self.owner_twitch_id if self.owner_twitch_id.isdigit() else "",
                    "generated_at": int(time.time()),
                },
            )
            removed = int(response.get("removed", 0))
            if response.get("needs_fellowship"):
                if fellowship_payload is None:
                    fellowship_payload = self.build_fellowship_snapshot()
                if fellowship_payload is not None:
                    self._post("/api/sync/fellowship", fellowship_payload)
                    self._fellowship_hash = self.snapshot_hash(fellowship_payload)
            if response.get("needs_overlay"):
                if overlay_payload is None:
                    overlay_payload = self.build_overlay_snapshot()
                if overlay_payload is not None:
                    self._post("/api/sync/overlay", overlay_payload)
                    self._overlay_hash = self.snapshot_hash(overlay_payload)
                    overlay_uploaded = 1
            missing = [str(name).lower() for name in response.get("missing", [])]
            for username in missing:
                if stopping():
                    self._force_full = True
                    return {"players": len(usernames), "changed": changed, "removed": removed, "overlay": overlay_uploaded}
                if username not in usernames or username in uploaded:
                    continue
                payload = self.build_snapshot(username)
                self._post("/api/sync/player", payload)
                self._hashes[username] = self.snapshot_hash(payload)
                uploaded.add(username)
                changed += 1
            self._last_manifest = usernames
            self._last_heartbeat = now

        self._last_source_stamp = stamp
        self._last_overlay_stamp = overlay_stamp
        self._force_full = False
        return {"players": len(usernames), "changed": changed, "removed": removed, "overlay": overlay_uploaded}

    def run_forever(self) -> None:
        print(f"Crystal Guild hosted portal sync v{SYNC_VERSION}")
        print(f"Destination: {self.public_url}")
        print(f"Sync interval: {self.interval:g}s")
        failures = 0
        while True:
            try:
                result = self.sync_once()
                if result["changed"] or result["removed"] or failures:
                    print(
                        "Portal sync OK: "
                        f"players={result['players']} "
                        f"changed={result['changed']} "
                        f"removed={result['removed']}"
                    )
                failures = 0
                time.sleep(self.interval)
            except KeyboardInterrupt:
                self.repository.close()
                return
            except Exception as exc:
                failures += 1
                delay = min(60.0, self.interval * (2 ** min(failures, 4)))
                print(f"Portal sync error: {exc} | retrying in {delay:g}s")
                time.sleep(delay)

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
                "User-Agent": f"CrystalGuildPortalSync/{SYNC_VERSION}",
            },
        )
        context = None
        if self.public_url.lower().startswith("https://") and not self.verify_tls:
            context = ssl._create_unverified_context()  # noqa: SLF001 - explicit owner opt-out for local testing only.
        try:
            with urlopen(request, timeout=self.timeout, context=context) as response:
                data = json.loads(response.read().decode("utf-8"))
                if not data.get("ok"):
                    raise RuntimeError(data.get("error") or "Hosted portal rejected sync request.")
                return data
        except HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {text[:500]}") from exc
        except URLError as exc:
            raise RuntimeError(f"Cannot reach hosted portal: {exc.reason}") from exc



class PortalSyncWorker:
    """Threaded in-process hosted Portal synchronization for cloud runtime.

    The legacy standalone run_portal_sync.py entry point remains supported for
    local installations. Cloud mode uses this worker so the authoritative bot,
    action relay, and sanitized snapshot heartbeat share one Render process.
    """

    def __init__(self, client: PortalSyncClient) -> None:
        self.client = client
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._state_lock = threading.Lock()
        self._state = "stopped"
        self._last_success = 0
        self._last_error = ""
        self._syncs = 0
        self._changed = 0

    def start(self) -> None:
        with self._state_lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._wake.clear()
            self._state = "starting"
            self._thread = threading.Thread(target=self._run, name="CrystalGuildPortalSync", daemon=True)
            self._thread.start()

    def stop(self, timeout: float | None = None) -> None:
        self._stop.set()
        self._wake.set()
        thread = self._thread
        client_timeout = float(getattr(self.client, "timeout", 10.0))
        wait = max(8.0, client_timeout + 2.0) if timeout is None else max(0.0, float(timeout))
        if thread and thread.is_alive():
            thread.join(timeout=wait)
        try:
            self.client.repository.close()
        finally:
            with self._state_lock:
                self._state = "stopped"

    def wake(self) -> None:
        self._wake.set()

    def status(self) -> dict[str, Any]:
        with self._state_lock:
            return {
                "state": self._state,
                "last_success": self._last_success,
                "last_error": self._last_error,
                "syncs": self._syncs,
                "changed": self._changed,
            }

    def _run(self) -> None:
        failures = 0
        with self._state_lock:
            self._state = "running"
        while not self._stop.is_set():
            # Consume a prior wake before performing the sync. A new mutation
            # arriving during sync_once must remain set and trigger a second
            # pass, rather than being cleared after the potentially long run.
            self._wake.clear()
            try:
                result = self.client.sync_once(should_stop=self._stop.is_set)
                failures = 0
                with self._state_lock:
                    self._state = "running"
                    self._last_success = int(time.time())
                    self._last_error = ""
                    self._syncs += 1
                    self._changed += int(result.get("changed", 0))
                delay = self.client.interval
            except Exception as exc:
                failures += 1
                delay = min(60.0, self.client.interval * (2 ** min(failures, 4)))
                with self._state_lock:
                    self._state = "degraded"
                    self._last_error = f"{type(exc).__name__}: {exc}"
                LOGGER.warning("Portal sync failed: %s | retrying in %.1fs", exc, delay)
            if self._stop.is_set():
                break
            self._wake.wait(timeout=delay)
        with self._state_lock:
            self._state = "stopped"

def env_bool(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Sync local Crystal Guild player data to a hosted Adventurer Portal")
    parser.add_argument("--once", action="store_true", help="Perform one sync and exit")
    parser.add_argument("--force", action="store_true", help="Force every player to be uploaded")
    args = parser.parse_args()

    public_url = os.getenv("PORTAL_PUBLIC_URL", "").strip()
    sync_key = os.getenv("PORTAL_SYNC_KEY", "").strip()
    if not public_url:
        raise SystemExit("PORTAL_PUBLIC_URL is missing from .env")
    if not sync_key:
        raise SystemExit("PORTAL_SYNC_KEY is missing from .env")

    repository = PortalRepository(
        os.getenv("DATABASE_PATH", "crystal_guild.db"),
        os.getenv("DATA_DIR", "data"),
    )
    client = PortalSyncClient(
        repository=repository,
        public_url=public_url,
        sync_key=sync_key,
        interval=float(os.getenv("PORTAL_SYNC_SECONDS", "5")),
        timeout=float(os.getenv("PORTAL_SYNC_TIMEOUT_SECONDS", "10")),
        verify_tls=env_bool("PORTAL_SYNC_VERIFY_TLS", True),
        heartbeat_seconds=float(os.getenv("PORTAL_SYNC_HEARTBEAT_SECONDS", "60")),
        overlay_state_path=os.getenv("OVERLAY_STATE_PATH", "overlay/state.json"),
        owner_twitch_id=os.getenv("TWITCH_OWNER_ID", ""),
    )
    if args.once:
        print(client.sync_once(force=args.force or True))
    else:
        client.run_forever()


if __name__ == "__main__":
    main()

from __future__ import annotations

import hashlib
from contextlib import closing
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable


class TwitchTokenStore:
    """Small durable SQLite store for TwitchIO managed user tokens.

    This database is separate from the player database on purpose: token material
    is operational secret state and should never be copied into a public Portal
    snapshot or normal player-data backup.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 10000")
        return conn

    def _initialize(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS twitch_tokens(
                    user_id TEXT PRIMARY KEY,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()
        self._tighten_permissions()

    def _tighten_permissions(self) -> None:
        # Best-effort owner-only permissions on POSIX cloud hosts. Windows ACLs
        # are left to the operating system.
        try:
            if os.name == "posix" and self.path.exists():
                self.path.chmod(0o600)
        except OSError:
            pass

    def upsert(self, user_id: str, access_token: str, refresh_token: str) -> None:
        uid = str(user_id or "").strip()
        token = str(access_token or "").strip()
        refresh = str(refresh_token or "").strip()
        if not uid or not token or not refresh:
            raise ValueError("user_id, access_token, and refresh_token are required")
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO twitch_tokens(user_id,access_token,refresh_token,updated_at)
                VALUES (?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET
                    access_token=excluded.access_token,
                    refresh_token=excluded.refresh_token,
                    updated_at=excluded.updated_at
                """,
                (uid, token, refresh, int(time.time())),
            )
            conn.commit()
        self._tighten_permissions()

    def delete(self, user_id: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("DELETE FROM twitch_tokens WHERE user_id=?", (str(user_id),))
            conn.commit()

    def load(self) -> list[dict[str, str]]:
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "SELECT user_id,access_token,refresh_token FROM twitch_tokens ORDER BY user_id"
            ).fetchall()
        return [dict(row) for row in rows]

    def count(self) -> int:
        with closing(self._connect()) as conn, conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM twitch_tokens").fetchone()
        return int(row["n"])

    def get(self, user_id: str) -> dict[str, str] | None:
        """Return one managed Twitch token row without exposing it elsewhere."""
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT user_id,access_token,refresh_token FROM twitch_tokens WHERE user_id=?",
                (str(user_id),),
            ).fetchone()
        return dict(row) if row else None

    def user_ids(self) -> set[str]:
        return {row["user_id"] for row in self.load()}


def _candidate_from_mapping(value: dict[str, Any], fallback_user_id: str | None = None) -> tuple[str | None, str, str] | None:
    access = value.get("access_token") or value.get("token")
    refresh = value.get("refresh_token") or value.get("refresh")
    if not isinstance(access, str) or not isinstance(refresh, str) or not access.strip() or not refresh.strip():
        return None
    user_id = value.get("user_id") or value.get("id") or fallback_user_id
    uid = str(user_id).strip() if user_id is not None else None
    return uid or None, access.strip(), refresh.strip()


def extract_token_pairs(payload: Any) -> list[tuple[str | None, str, str]]:
    """Extract common TwitchIO token JSON shapes without printing token material."""
    found: list[tuple[str | None, str, str]] = []
    seen: set[str] = set()

    def add(candidate: tuple[str | None, str, str] | None) -> None:
        if not candidate:
            return
        uid, access, refresh = candidate
        fingerprint = hashlib.sha256((access + "\0" + refresh).encode("utf-8")).hexdigest()
        if fingerprint in seen:
            return
        seen.add(fingerprint)
        found.append((uid, access, refresh))

    def walk(node: Any, key_hint: str | None = None) -> None:
        if isinstance(node, dict):
            add(_candidate_from_mapping(node, key_hint if key_hint and key_hint.isdigit() else None))
            for key, value in node.items():
                hint = str(key) if str(key).isdigit() else None
                if isinstance(value, (list, tuple)) and len(value) >= 2 and all(isinstance(v, str) for v in value[:2]):
                    if hint:
                        add((hint, str(value[0]).strip(), str(value[1]).strip()))
                walk(value, hint)
        elif isinstance(node, list):
            for value in node:
                walk(value, key_hint)

    walk(payload)
    return found


def copy_token_database(source: str | Path, target: str | Path, expected_user_ids: Iterable[str] = ()) -> dict[str, Any]:
    """Copy an existing Crystal Guild token DB without mutating the source."""
    source_path = Path(source).expanduser().resolve()
    target_path = Path(target).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    try:
        with closing(sqlite3.connect(f"file:{source_path}?mode=ro", uri=True, timeout=5.0)) as conn:
            rows = conn.execute(
                "SELECT user_id,access_token,refresh_token FROM twitch_tokens ORDER BY user_id"
            ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Invalid Twitch token database: {exc}") from exc
    if target_path.exists():
        target_path.unlink()
    store = TwitchTokenStore(target_path)
    for uid, access, refresh in rows:
        store.upsert(str(uid), str(access), str(refresh))
    expected = {str(value).strip() for value in expected_user_ids if str(value).strip()}
    present = store.user_ids()
    return {
        "stored": store.count(),
        "user_ids": sorted(present),
        "missing_expected_user_ids": sorted(expected - present),
    }


def import_twitchio_json(source: str | Path, target: str | Path, expected_user_ids: Iterable[str] = ()) -> dict[str, Any]:
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    pairs = extract_token_pairs(payload)
    identified = [(uid, access, refresh) for uid, access, refresh in pairs if uid]
    if not identified:
        raise RuntimeError(
            "No user-ID keyed Twitch token pairs were found. Re-authorize once with this build locally, "
            "or seed the cloud token database with known user IDs before deploying."
        )
    target_path = Path(target).expanduser().resolve()
    if target_path.exists():
        target_path.unlink()
    store = TwitchTokenStore(target_path)
    for uid, access, refresh in identified:
        store.upsert(str(uid), access, refresh)
    expected = {str(value).strip() for value in expected_user_ids if str(value).strip()}
    present = store.user_ids()
    missing = sorted(expected - present)
    return {
        "imported": len(identified),
        "stored": store.count(),
        "user_ids": sorted(present),
        "missing_expected_user_ids": missing,
    }

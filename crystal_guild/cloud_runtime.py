from __future__ import annotations

import logging
import shutil
import sqlite3
import time
from pathlib import Path

from .config import Settings
from .token_store import TwitchTokenStore

LOGGER = logging.getLogger("CrystalGuild.Cloud")


def ensure_runtime_directories(settings: Settings) -> None:
    for raw in (settings.database_path, settings.overlay_state_path, settings.log_dir, settings.twitch_token_db):
        if not raw:
            continue
        path = Path(raw).expanduser()
        target = path if raw == settings.log_dir else path.parent
        target.mkdir(parents=True, exist_ok=True)


def cloud_bootstrap_ready(settings: Settings) -> tuple[bool, list[str]]:
    """Return whether the cloud worker has the private persistent state it needs."""
    if not settings.cloud_runtime:
        return True, []
    missing: list[str] = []
    database = Path(settings.database_path).expanduser()
    if settings.cloud_require_existing_database and not database.is_file():
        missing.append(f"authoritative database: {database}")
    elif database.is_file():
        # Fail closed before Database() can create or migrate anything. A wrong,
        # empty, or damaged upload must never become the authoritative Guild.
        try:
            with sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True, timeout=5.0) as conn:
                quick = conn.execute("PRAGMA quick_check").fetchone()
                players = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='players'"
                ).fetchone()
                migrations = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
                ).fetchone()
                if not quick or str(quick[0]).lower() != "ok":
                    missing.append(f"healthy authoritative database (quick_check={quick})")
                if not players:
                    missing.append("valid Crystal Guild database (players table missing)")
                if not migrations:
                    missing.append("valid Crystal Guild database (schema_migrations table missing)")
        except sqlite3.Error as exc:
            missing.append(f"readable authoritative database ({exc})")
    if not settings.twitch_token_db:
        missing.append("TWITCH_TOKEN_DB setting")
    else:
        token_db = Path(settings.twitch_token_db).expanduser()
        if not token_db.is_file():
            missing.append(f"Twitch token database: {token_db}")
        else:
            try:
                users = TwitchTokenStore(token_db).user_ids()
            except sqlite3.Error as exc:
                missing.append(f"readable Twitch token database ({exc})")
            else:
                for uid, label in ((settings.bot_id, "bot"), (settings.owner_id, "broadcaster")):
                    if uid not in users:
                        missing.append(f"{label} Twitch token for user ID {uid}")
    return not missing, missing


def wait_for_cloud_bootstrap(settings: Settings) -> None:
    if not settings.cloud_runtime:
        return
    ensure_runtime_directories(settings)
    announced = False
    while True:
        ready, missing = cloud_bootstrap_ready(settings)
        if ready:
            if announced:
                LOGGER.info("Cloud bootstrap state detected; starting Crystal Guild.")
            return
        announced = True
        LOGGER.warning(
            "CLOUD BOOTSTRAP REQUIRED — worker is intentionally idle to protect player progression. Missing: %s. "
            "Upload the prepared crystal_guild.db and twitch_tokens.db to /var/data, then the worker will start automatically.",
            "; ".join(missing),
        )
        time.sleep(settings.cloud_bootstrap_wait_seconds)


def create_startup_backup(settings: Settings, keep: int = 5) -> Path | None:
    """Create a SQLite-consistent startup backup on the persistent disk in cloud mode."""
    if not settings.cloud_runtime:
        return None
    source = Path(settings.database_path).expanduser().resolve()
    if not source.exists():
        return None
    backup_dir = source.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    target = backup_dir / f"crystal_guild-startup-{stamp}.db"
    src = sqlite3.connect(source)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    backups = sorted(backup_dir.glob("crystal_guild-startup-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[max(1, int(keep)):]:
        try:
            old.unlink()
        except OSError:
            LOGGER.warning("Could not remove old startup backup: %s", old)
    LOGGER.info("Cloud startup backup created: %s", target)
    return target


def copy_database_for_migration(source: str | Path, destination: str | Path) -> Path:
    """Make a consistent SQLite copy suitable for private transfer to Render."""
    src_path = Path(source).expanduser().resolve()
    dst_path = Path(destination).expanduser().resolve()
    if not src_path.exists():
        raise FileNotFoundError(src_path)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    if dst_path.exists():
        dst_path.unlink()
    src = sqlite3.connect(src_path)
    dst = sqlite3.connect(dst_path)
    try:
        src.backup(dst)
        row = dst.execute("PRAGMA quick_check").fetchone()
        if not row or str(row[0]).lower() != "ok":
            raise RuntimeError(f"Migration database quick_check failed: {row}")
    finally:
        dst.close()
        src.close()
    return dst_path

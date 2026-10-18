from __future__ import annotations

import logging
from contextlib import closing
import os
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
            with closing(sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True, timeout=5.0)) as conn:
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


STARTUP_BACKUP_DEFAULT_KEEP = 2
STARTUP_BACKUP_FREE_RESERVE_BYTES = 64 * 1024 * 1024


def _startup_backups(backup_dir: Path) -> list[Path]:
    backups: list[tuple[float, Path]] = []
    try:
        candidates = list(backup_dir.glob("crystal_guild-startup-*.db"))
    except OSError:
        return []
    for path in candidates:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        backups.append((mtime, path))
    backups.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in backups]


def _unlink_quietly(path: Path) -> bool:
    try:
        path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def prepare_cloud_storage(settings: Settings, keep: int = STARTUP_BACKUP_DEFAULT_KEEP) -> list[Path]:
    """Reclaim predictable cloud disk usage before logging or a new startup backup.

    The old startup-backup path pruned *after* creating a new copy. On a small
    persistent disk that eventually deadlocked: five valid backups could leave
    too little space to create the sixth copy, so the cleanup code was never
    reached. Keep only the number of historical copies that can coexist with
    the backup we are about to create, and remove abandoned partial copies.
    """
    if not settings.cloud_runtime:
        return []
    source = Path(settings.database_path).expanduser().resolve()
    backup_dir = source.parent / "backups"
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return []

    removed: list[Path] = []
    for partial in backup_dir.glob(".crystal_guild-startup-*.partial"):
        if _unlink_quietly(partial):
            removed.append(partial)

    # Reserve one slot for the backup this boot is about to create.
    precreate_keep = max(0, int(keep) - 1)
    for old in _startup_backups(backup_dir)[precreate_keep:]:
        if _unlink_quietly(old):
            removed.append(old)
    return removed


def create_startup_backup(
    settings: Settings,
    keep: int = STARTUP_BACKUP_DEFAULT_KEEP,
    reserve_bytes: int = STARTUP_BACKUP_FREE_RESERVE_BYTES,
) -> Path | None:
    """Create a SQLite-consistent cloud startup backup without bricking startup.

    Old backups are pruned before copying. If the persistent disk still cannot
    safely fit a full database copy plus a small reserve, the backup is skipped
    and startup continues. A failed copy is always removed so it cannot consume
    the last bytes on the disk.
    """
    if not settings.cloud_runtime:
        return None
    source = Path(settings.database_path).expanduser().resolve()
    if not source.exists():
        return None
    backup_dir = source.parent / "backups"
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        LOGGER.warning("Cloud startup backup skipped: backup directory is unavailable (%s).", exc)
        return None

    prepare_cloud_storage(settings, keep=keep)

    try:
        source_bytes = max(0, source.stat().st_size)
        required_free = source_bytes + max(0, int(reserve_bytes))
        free_bytes = shutil.disk_usage(backup_dir).free
    except OSError as exc:
        LOGGER.warning("Cloud startup backup skipped: could not inspect persistent disk space (%s).", exc)
        return None

    # If the retained previous copy prevents a safe new copy, release it too.
    if free_bytes < required_free:
        for old in reversed(_startup_backups(backup_dir)):
            if not _unlink_quietly(old):
                continue
            try:
                free_bytes = shutil.disk_usage(backup_dir).free
            except OSError:
                break
            if free_bytes >= required_free:
                break

    if free_bytes < required_free:
        LOGGER.warning(
            "Cloud startup backup skipped: persistent disk has %.1f MiB free; %.1f MiB is required for a safe copy. "
            "Crystal Guild will continue without creating a new startup backup.",
            free_bytes / (1024 * 1024),
            required_free / (1024 * 1024),
        )
        return None

    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    target = backup_dir / f"crystal_guild-startup-{stamp}.db"
    partial = backup_dir / f".crystal_guild-startup-{stamp}-{os.getpid()}-{time.time_ns()}.partial"
    src: sqlite3.Connection | None = None
    dst: sqlite3.Connection | None = None
    try:
        src = sqlite3.connect(source)
        dst = sqlite3.connect(partial)
        src.backup(dst)
        row = dst.execute("PRAGMA quick_check").fetchone()
        if not row or str(row[0]).lower() != "ok":
            raise sqlite3.DatabaseError(f"startup backup quick_check failed: {row}")
        dst.close()
        dst = None
        src.close()
        src = None
        partial.replace(target)
    except (OSError, sqlite3.Error) as exc:
        if dst is not None:
            try:
                dst.close()
            except sqlite3.Error:
                pass
        if src is not None:
            try:
                src.close()
            except sqlite3.Error:
                pass
        _unlink_quietly(partial)
        LOGGER.warning(
            "Cloud startup backup failed and was cleaned up (%s). Crystal Guild will continue using the authoritative database.",
            exc,
        )
        return None
    finally:
        if dst is not None:
            dst.close()
        if src is not None:
            src.close()

    for old in _startup_backups(backup_dir)[max(1, int(keep)):]:
        if not _unlink_quietly(old):
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

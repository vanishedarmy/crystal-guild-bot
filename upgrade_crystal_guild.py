from __future__ import annotations

import os
from pathlib import Path

from crystal_guild.config import load_dotenv
from crystal_guild.database import Database


def _upgrade_command_prefix(env_path: Path = Path(".env")) -> None:
    """Keep Cloud Runtime on the established ``!`` Twitch command prefix.

    Clean Phase 4 installations already use ``!``. This also repairs an
    installation that briefly received the abandoned ``&`` experiment without
    touching any unrelated environment values.
    """
    if not env_path.exists():
        return
    text = env_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    changed = False
    found = False
    for index, raw in enumerate(lines):
        if raw.strip().startswith("BOT_PREFIX="):
            found = True
            value = raw.split("=", 1)[1].strip().strip('"').strip("'")
            if value == "&":
                lines[index] = "BOT_PREFIX=!"
                changed = True
            break
    if not found:
        lines.append("BOT_PREFIX=!")
        changed = True
    if changed:
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("PASS — Twitch command prefix set to !.")


def _upgrade_combat_timing_defaults(env_path: Path = Path(".env")) -> None:
    """Preserve the H9 combat timing defaults while upgrading into v1.2.

    Explicit non-default operator overrides are preserved. Only the exact
    values shipped by the previous release are rewritten.
    """
    if not env_path.exists():
        return
    replacements = {
        "ENCOUNTER_JOIN_SECONDS": ("45", "60"),
        "ENCOUNTER_ROUND_SECONDS": ("20", "30"),
        "RAID_JOIN_SECONDS": ("60", "90"),
        "RAID_ROUND_SECONDS": ("15", "60"),
    }
    lines = env_path.read_text(encoding="utf-8").splitlines()
    changed = []
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        for key, (old, new) in replacements.items():
            if not stripped.startswith(f"{key}="):
                continue
            value = raw.split("=", 1)[1].strip().strip('"').strip("'")
            if value == old:
                lines[index] = f"{key}={new}"
                changed.append(f"{key}={new}")
            break
    if changed:
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("PASS — updated prior stock combat timers: " + ", ".join(changed))


def main() -> int:
    _upgrade_command_prefix()
    _upgrade_combat_timing_defaults()
    load_dotenv()
    db_path = Path(os.getenv("DATABASE_PATH", "crystal_guild.db"))
    print("Crystal Guild v1.3.0 Guild Expansion Alpha 1 — In-place Upgrade Check")
    print(f"Database: {db_path}")
    if not db_path.exists():
        print("INFO — no existing Guild database found; nothing to migrate.")
        return 0

    db = Database(db_path)
    try:
        print(f"PASS — local database schema v{db.schema_version()}")
        if db.pre_migration_backup_path:
            print(f"PASS — verified pre-migration backup: {db.pre_migration_backup_path}")
        report = db.integrity_report()
        if not report["ok"]:
            print("FAIL — database integrity validation did not pass.")
            for problem in report["quick_check"]:
                print(f"  quick_check: {problem}")
            for problem in report["foreign_key_violations"][:25]:
                print(f"  foreign_key: {problem}")
            return 2
        print(
            "PASS — SQLite integrity / runtime pragmas "
            f"(players={report['players']:,}, transactions={report['transactions']:,})"
        )
        print("UPGRADE COMPLETE — existing player progression is preserved.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

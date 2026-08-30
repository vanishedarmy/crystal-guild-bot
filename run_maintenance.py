from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from crystal_guild.config import load_dotenv
from crystal_guild.data import GameData
from crystal_guild.database import Database


def main() -> int:
    parser = argparse.ArgumentParser(description="Crystal Guild release-readiness checks, backup, and recovery drill")
    parser.add_argument("--backup", action="store_true", help="Create a consistent SQLite backup after checks pass")
    parser.add_argument("--backup-dir", default="backups", help="Backup directory (default: backups)")
    parser.add_argument("--clear-runtime-state", action="store_true", help="Clear only the live-combat recovery checkpoint (player progression is untouched)")
    parser.add_argument("--recovery-drill", action="store_true", help="Back up and restore the live DB into a temporary sandbox, then verify counts/integrity without touching the live DB")
    args = parser.parse_args()

    load_dotenv()
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    db_path = Path(os.getenv("DATABASE_PATH", "crystal_guild.db"))

    print("Crystal Guild v1.5.0 — Trails & Raids Alpha 2 Release Readiness")
    print(f"Data: {data_dir}")
    data = GameData(data_dir)
    errors = data.validate()
    if errors:
        print(f"FAIL — game-data validation returned {len(errors)} issue(s):")
        for error in errors[:25]:
            print(f"  - {error}")
        return 1
    print("PASS — game-data references, ranges, and balance guardrails")

    if not db_path.exists():
        print(f"INFO — database does not exist yet: {db_path}")
        print("PASS — nothing to integrity-check before first launch")
        return 0

    db = Database(db_path)
    try:
        print(f"PASS — local database schema v{db.schema_version()}")
        if db.pre_migration_backup_path:
            print(f"PASS — verified pre-migration backup: {db.pre_migration_backup_path}")
        integrity = db.integrity_report()
        failures = list(integrity["quick_check"])
        foreign_keys = list(integrity["foreign_key_violations"])
        if failures:
            print("FAIL — SQLite quick_check reported:")
            for failure in failures:
                print(f"  - {failure}")
            return 2
        print("PASS — SQLite quick_check")
        if foreign_keys:
            print("FAIL — SQLite foreign_key_check reported:")
            for failure in foreign_keys[:25]:
                print(f"  - {failure}")
            return 2
        print("PASS — SQLite foreign_key_check")
        if integrity["journal_mode"] != "wal" or int(integrity["busy_timeout_ms"]) < 1000:
            print(
                "FAIL — runtime SQLite pragmas are not release-safe: "
                f"journal={integrity['journal_mode']} busy_timeout={integrity['busy_timeout_ms']}ms"
            )
            return 2
        print(
            "PASS — SQLite runtime pragmas "
            f"(journal={integrity['journal_mode']}, busy_timeout={integrity['busy_timeout_ms']}ms)"
        )

        runtime = db.runtime_state("combat")
        if runtime is None:
            print("PASS — runtime checkpoint is idle / absent")
        else:
            try:
                payload = json.loads(runtime["value_json"])
                if int(payload.get("schema", 0)) != 1:
                    raise ValueError(f"unsupported runtime schema {payload.get('schema')!r}")
                encounter = payload.get("active_encounter")
                raid = payload.get("active_boss")
                if encounter and raid:
                    raise ValueError("checkpoint contains both encounter and raid state")
                active = "encounter" if encounter else ("raid" if raid else "idle")
                print(f"PASS — runtime checkpoint JSON / schema (state={active}, updated={runtime['updated_at']})")
            except Exception as exc:
                print(f"WARN — runtime checkpoint is unreadable and will be ignored at next bot launch: {type(exc).__name__}: {exc}")

        if args.clear_runtime_state:
            db.delete_runtime_state("combat")
            print("PASS — live-combat runtime checkpoint cleared; player progression was not changed")

        db.optimize()
        print("PASS — WAL checkpoint / PRAGMA optimize")

        if args.backup:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            destination = Path(args.backup_dir) / f"crystal_guild-{timestamp}.db"
            saved = db.backup(destination)
            verify = Database(saved)
            try:
                backup_report = verify.integrity_report()
            finally:
                verify.close()
            if not backup_report["ok"]:
                problems = list(backup_report["quick_check"]) + list(backup_report["foreign_key_violations"])
                print("FAIL — backup verification failed: " + "; ".join(problems or ["runtime pragma mismatch"]))
                return 3
            print(f"PASS — verified backup: {saved}")

        if args.recovery_drill:
            # The drill never overwrites the live database. It creates a real
            # SQLite backup, copies it as a pretend restore target, reopens that
            # target through the normal Database bootstrap, then compares the
            # authoritative row counts and combat checkpoint.
            live_runtime = db.runtime_state("combat")
            live_runtime_json = str(live_runtime["value_json"]) if live_runtime else None
            live_players = int(integrity["players"])
            live_transactions = int(integrity["transactions"])
            with tempfile.TemporaryDirectory(prefix="crystal-guild-recovery-") as tmp:
                tmp_path = Path(tmp)
                backup_path = db.backup(tmp_path / "backup.db")
                restored_path = tmp_path / "restored.db"
                shutil.copy2(backup_path, restored_path)
                restored = Database(restored_path)
                try:
                    restored_report = restored.integrity_report()
                    restored_runtime = restored.runtime_state("combat")
                    restored_runtime_json = str(restored_runtime["value_json"]) if restored_runtime else None
                finally:
                    restored.close()
                if not restored_report["ok"]:
                    print("FAIL — recovery drill restored database failed integrity validation")
                    return 4
                if int(restored_report["players"]) != live_players or int(restored_report["transactions"]) != live_transactions:
                    print(
                        "FAIL — recovery drill row-count mismatch: "
                        f"players {restored_report['players']}/{live_players}, "
                        f"transactions {restored_report['transactions']}/{live_transactions}"
                    )
                    return 4
                if restored_runtime_json != live_runtime_json:
                    print("FAIL — recovery drill combat checkpoint mismatch")
                    return 4
            print(
                "PASS — non-destructive backup/restore drill "
                f"({live_players:,} players, {live_transactions:,} transactions, runtime checkpoint preserved)"
            )
    finally:
        db.close()

    print("CLOUD RUNTIME READINESS CHECK COMPLETE — persistence, recovery, and database checks nominal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import os
from pathlib import Path

from crystal_guild.cloud_runtime import cloud_bootstrap_ready, ensure_runtime_directories
from crystal_guild.config import Settings
from crystal_guild.data import GameData
from crystal_guild.database import Database
from crystal_guild.token_store import TwitchTokenStore


def main() -> None:
    settings = Settings.from_env()
    ensure_runtime_directories(settings)
    print(f"Crystal Guild cloud preflight | mode={settings.runtime_mode}")
    GameData(settings.data_dir).validate_or_raise()
    print("PASS — static game data validated")

    if settings.cloud_runtime:
        ready, missing = cloud_bootstrap_ready(settings)
        if not ready:
            print("WAITING — private persistent state is not complete:")
            for item in missing:
                print(f"  - {item}")
            raise SystemExit(2)

    db_path = Path(settings.database_path)
    if db_path.exists():
        db = Database(db_path)
        try:
            report = db.integrity_report()
            if not report["ok"]:
                raise SystemExit(f"FAIL — database integrity: {report}")
            print(f"PASS — player DB quick-check / FK check | players={report['players']}")
        finally:
            db.close()

    if settings.twitch_token_db:
        store = TwitchTokenStore(settings.twitch_token_db)
        missing_ids = {settings.bot_id, settings.owner_id} - store.user_ids()
        if missing_ids:
            raise SystemExit("FAIL — Twitch token DB missing IDs: " + ", ".join(sorted(missing_ids)))
        print(f"PASS — Twitch token DB contains bot + broadcaster rows ({store.count()} total)")

    if settings.portal_sync_in_process:
        if not settings.portal_public_url or not settings.portal_sync_key:
            raise SystemExit("FAIL — in-process Portal sync requires PORTAL_PUBLIC_URL and PORTAL_SYNC_KEY")
        print("PASS — in-process Portal sync/action credentials configured")

    print("ALL CLOUD PREFLIGHT CHECKS PASSED.")


if __name__ == "__main__":
    main()

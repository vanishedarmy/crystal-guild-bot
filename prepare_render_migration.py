from __future__ import annotations

import argparse
import os
from pathlib import Path

from crystal_guild.cloud_runtime import copy_database_for_migration
from crystal_guild.config import load_dotenv
from crystal_guild.token_store import copy_token_database, import_twitchio_json


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Prepare private Crystal Guild state files for first Render cloud deployment."
    )
    parser.add_argument("--output", default="render_migration", help="Private output folder")
    parser.add_argument("--database", default=os.getenv("DATABASE_PATH", "crystal_guild.db"))
    parser.add_argument("--token-file", default=".tio.tokens.json")
    parser.add_argument("--token-db", default="", help="Use an already prepared twitch_tokens.db instead of token JSON")
    args = parser.parse_args()

    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    database_target = output / "crystal_guild.db"
    token_target = output / "twitch_tokens.db"

    copy_database_for_migration(args.database, database_target)

    expected = [os.getenv("TWITCH_BOT_ID", ""), os.getenv("TWITCH_OWNER_ID", "")]
    if args.token_db:
        src = Path(args.token_db).expanduser().resolve()
        if not src.exists():
            raise SystemExit(f"Token DB does not exist: {src}")
        result = copy_token_database(src, token_target, expected_user_ids=expected)
        if result["missing_expected_user_ids"]:
            raise SystemExit("Prepared token DB is missing required Twitch user IDs: " + ", ".join(result["missing_expected_user_ids"]))
        token_rows = result["stored"]
        user_ids = result["user_ids"]
    else:
        token_file = Path(args.token_file).expanduser().resolve()
        fallback_db = Path("twitch_tokens.db").resolve()
        if not token_file.exists() and fallback_db.exists():
            result = copy_token_database(fallback_db, token_target, expected_user_ids=expected)
            if result["missing_expected_user_ids"]:
                raise SystemExit("Prepared token DB is missing required Twitch user IDs: " + ", ".join(result["missing_expected_user_ids"]))
            token_rows = result["stored"]
            user_ids = result["user_ids"]
        elif not token_file.exists():
            raise SystemExit(
                f"TwitchIO token file does not exist: {token_file}\n"
                "If your install has no .tio.tokens.json, run run_cloud_token_authorization.bat, authorize both accounts, "
                "then rerun this command with --token-db twitch_tokens.db."
            )
        else:
            result = import_twitchio_json(token_file, token_target, expected_user_ids=expected)
            if result["missing_expected_user_ids"]:
                raise SystemExit(
                    "Token import did not contain both bot and broadcaster IDs: "
                    + ", ".join(result["missing_expected_user_ids"])
                )
            token_rows = result["stored"]
            user_ids = result["user_ids"]

    manifest = output / "MIGRATION_MANIFEST.txt"
    manifest.write_text(
        "Crystal Guild v1.1.16 — Arsenal private migration bundle\n"
        f"Database: crystal_guild.db ({database_target.stat().st_size} bytes)\n"
        f"Token database: twitch_tokens.db ({token_target.stat().st_size} bytes)\n"
        f"Token rows: {token_rows}\n"
        f"Twitch user IDs: {', '.join(user_ids)}\n"
        "\nPRIVATE: do not commit or upload this folder to GitHub.\n",
        encoding="utf-8",
    )
    print("PASS — Render migration files prepared.")
    print(f"Private folder: {output}")
    print("Contains: crystal_guild.db, twitch_tokens.db, MIGRATION_MANIFEST.txt")
    print("Do NOT commit this folder to GitHub.")


if __name__ == "__main__":
    main()

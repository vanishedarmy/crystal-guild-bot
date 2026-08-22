from __future__ import annotations

import argparse
import os
from pathlib import Path

from crystal_guild.config import load_dotenv
from crystal_guild.token_store import import_twitchio_json


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Import local TwitchIO .tio.tokens.json into Crystal Guild's durable cloud token database."
    )
    parser.add_argument("--source", default=".tio.tokens.json", help="Path to the local TwitchIO token JSON")
    parser.add_argument("--target", default="twitch_tokens.db", help="Output SQLite token database")
    args = parser.parse_args()

    expected = [os.getenv("TWITCH_BOT_ID", ""), os.getenv("TWITCH_OWNER_ID", "")]
    try:
        result = import_twitchio_json(args.source, args.target, expected_user_ids=expected)
    except Exception as exc:
        raise SystemExit(f"Token import failed: {type(exc).__name__}: {exc}") from exc

    print("Twitch token migration complete.")
    print(f"Source: {Path(args.source).resolve()}")
    print(f"Target: {Path(args.target).resolve()}")
    print(f"Stored token rows: {result['stored']}")
    print("Stored Twitch user IDs: " + ", ".join(result["user_ids"]))
    if result["missing_expected_user_ids"]:
        print("WARNING — missing required IDs: " + ", ".join(result["missing_expected_user_ids"]))
        raise SystemExit(2)
    print("PASS — bot and broadcaster token rows are ready for private Render transfer.")


if __name__ == "__main__":
    main()

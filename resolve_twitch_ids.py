from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from crystal_guild.config import load_dotenv
import os

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
USERS_URL = "https://api.twitch.tv/helix/users"


def _clean_login(value: str) -> str:
    return value.strip().lstrip("@").lower()


def _replace_env_values(text: str, values: dict[str, str]) -> str:
    lines = text.splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in values:
                out.append(f"{key}={values[key]}")
                seen.add(key)
                continue
        out.append(line)
    for key, value in values.items():
        if key not in seen:
            out.append(f"{key}={value}")
    return "\n".join(out).rstrip() + "\n"


def _json_request(request: Request, timeout: float = 15.0) -> dict:
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Twitch returned HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Twitch: {exc.reason}") from exc


def _app_token(client_id: str, client_secret: str) -> str:
    body = urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
    ).encode("utf-8")
    payload = _json_request(Request(TOKEN_URL, data=body, method="POST"))
    token = str(payload.get("access_token", "")).strip()
    if not token:
        raise RuntimeError("Twitch did not return an app access token. Re-check Client ID and Client Secret.")
    return token


def _lookup_user(client_id: str, token: str, login: str) -> tuple[str, str]:
    url = f"{USERS_URL}?{urlencode({'login': login})}"
    request = Request(
        url,
        headers={
            "Client-Id": client_id,
            "Authorization": f"Bearer {token}",
        },
    )
    payload = _json_request(request)
    rows = payload.get("data") or []
    if not rows:
        raise RuntimeError(f"Twitch user @{login} was not found. Check the spelling and try again.")
    row = rows[0]
    return str(row["id"]), str(row.get("display_name") or row.get("login") or login)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve Crystal Guild Bot/Owner Twitch usernames to numeric user IDs and write them to .env."
    )
    parser.add_argument("--owner", help="Broadcaster/streamer Twitch username")
    parser.add_argument("--bot", help="Dedicated Bot Twitch username")
    parser.add_argument("--env", default=".env", help="Path to .env (default: .env)")
    parser.add_argument("--no-write", action="store_true", help="Print IDs without changing .env")
    args = parser.parse_args()

    env_path = Path(args.env)
    if not env_path.exists():
        example = Path(".env.example")
        if example.exists():
            env_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Created {env_path} from .env.example.")
        else:
            print("ERROR: .env does not exist and .env.example was not found.")
            return 2

    load_dotenv(env_path)
    client_id = os.getenv("TWITCH_CLIENT_ID", "").strip()
    client_secret = os.getenv("TWITCH_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print("ERROR: Fill TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET in .env first.")
        print("Create/manage your Twitch app at: https://dev.twitch.tv/console/apps")
        return 2

    owner = _clean_login(args.owner or input("Broadcaster/owner Twitch username (your channel): "))
    bot = _clean_login(args.bot or input("Dedicated Bot Twitch username: "))
    if not owner or not bot:
        print("ERROR: Both usernames are required.")
        return 2

    print("Contacting Twitch to resolve numeric user IDs...")
    try:
        token = _app_token(client_id, client_secret)
        owner_id, owner_display = _lookup_user(client_id, token, owner)
        bot_id, bot_display = _lookup_user(client_id, token, bot)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"Owner: @{owner} ({owner_display}) -> {owner_id}")
    print(f"Bot:   @{bot} ({bot_display}) -> {bot_id}")

    if not args.no_write:
        text = env_path.read_text(encoding="utf-8")
        env_path.write_text(
            _replace_env_values(text, {"TWITCH_BOT_ID": bot_id, "TWITCH_OWNER_ID": owner_id}),
            encoding="utf-8",
        )
        print(f"Updated {env_path} with TWITCH_BOT_ID and TWITCH_OWNER_ID.")
        print("Next: start run_bot.bat, then run open_twitch_authorization.bat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

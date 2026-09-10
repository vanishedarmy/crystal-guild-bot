from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    """Tiny .env loader so the project has no dotenv dependency."""
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _env_int(name: str, default: int, minimum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer; got {raw!r}.") from exc
    if value < minimum:
        raise RuntimeError(f"{name} must be at least {minimum}; got {value}.")
    return value


def _env_float(name: str, default: float, minimum: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be numeric; got {raw!r}.") from exc
    if value < minimum:
        raise RuntimeError(f"{name} must be at least {minimum}; got {value}.")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return raw.strip().lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    bot_id: str
    owner_id: str
    prefix: str = "!"
    database_path: str = "crystal_guild.db"
    data_dir: str = "data"
    venture_cooldown_seconds: int = 600
    encounter_join_seconds: int = 60
    encounter_round_seconds: int = 30
    camp_rest_seconds: int = 3600
    shop_refresh_seconds: int = 1800
    raid_join_seconds: int = 90
    raid_round_seconds: int = 60
    overlay_state_path: str = "overlay/state.json"
    portal_public_url: str = ""
    portal_sync_key: str = ""
    portal_sync_seconds: float = 5.0
    portal_sync_heartbeat_seconds: float = 60.0
    portal_sync_timeout_seconds: float = 10.0
    portal_sync_verify_tls: bool = True
    portal_sync_in_process: bool = False
    portal_action_poll_seconds: float = 3.0
    portal_action_timeout_seconds: float = 10.0
    portal_action_verify_tls: bool = True
    runtime_mode: str = "local"
    log_dir: str = "logs"
    twitch_token_db: str = ""
    cloud_require_existing_database: bool = True
    cloud_bootstrap_wait_seconds: int = 30
    stream_status_cache_seconds: float = 15.0
    stream_status_stale_seconds: float = 90.0
    subscription_status_cache_seconds: float = 300.0
    subscription_status_stale_seconds: float = 900.0

    @property
    def cloud_runtime(self) -> bool:
        return self.runtime_mode == "cloud"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        required = {
            "TWITCH_CLIENT_ID": os.getenv("TWITCH_CLIENT_ID", ""),
            "TWITCH_CLIENT_SECRET": os.getenv("TWITCH_CLIENT_SECRET", ""),
            "TWITCH_BOT_ID": os.getenv("TWITCH_BOT_ID", ""),
            "TWITCH_OWNER_ID": os.getenv("TWITCH_OWNER_ID", ""),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Missing required environment variables: " + ", ".join(missing) + ". Copy .env.example to .env."
            )
        if not required["TWITCH_BOT_ID"].isdigit() or not required["TWITCH_OWNER_ID"].isdigit():
            raise RuntimeError("TWITCH_BOT_ID and TWITCH_OWNER_ID must be numeric Twitch user IDs.")

        prefix = os.getenv("BOT_PREFIX", "!").strip()
        if not prefix or len(prefix) > 5:
            raise RuntimeError("BOT_PREFIX must contain between 1 and 5 characters.")

        runtime_mode = os.getenv("CRYSTAL_GUILD_RUNTIME_MODE", "local").strip().lower()
        if runtime_mode not in {"local", "cloud"}:
            raise RuntimeError("CRYSTAL_GUILD_RUNTIME_MODE must be either 'local' or 'cloud'.")
        cloud = runtime_mode == "cloud"
        default_database = "/var/data/crystal_guild.db" if cloud else "crystal_guild.db"
        default_overlay = "/var/data/overlay/state.json" if cloud else "overlay/state.json"
        default_logs = "/tmp/crystal-guild-logs" if cloud else "logs"
        default_token_db = "/var/data/twitch_tokens.db" if cloud else ""

        return cls(
            client_id=required["TWITCH_CLIENT_ID"],
            client_secret=required["TWITCH_CLIENT_SECRET"],
            bot_id=required["TWITCH_BOT_ID"],
            owner_id=required["TWITCH_OWNER_ID"],
            prefix=prefix,
            database_path=os.getenv("DATABASE_PATH", default_database).strip() or default_database,
            data_dir=os.getenv("DATA_DIR", "data").strip() or "data",
            venture_cooldown_seconds=_env_int("VENTURE_COOLDOWN_SECONDS", 600, 0),
            encounter_join_seconds=_env_int("ENCOUNTER_JOIN_SECONDS", 60, 5),
            encounter_round_seconds=_env_int("ENCOUNTER_ROUND_SECONDS", 30, 5),
            camp_rest_seconds=_env_int("CAMP_REST_SECONDS", 3600, 60),
            shop_refresh_seconds=_env_int("SHOP_REFRESH_SECONDS", 1800, 60),
            raid_join_seconds=_env_int("RAID_JOIN_SECONDS", 90, 10),
            raid_round_seconds=_env_int("RAID_ROUND_SECONDS", 60, 5),
            overlay_state_path=os.getenv("OVERLAY_STATE_PATH", default_overlay).strip() or default_overlay,
            portal_public_url=os.getenv("PORTAL_PUBLIC_URL", "").strip(),
            portal_sync_key=os.getenv("PORTAL_SYNC_KEY", "").strip(),
            portal_sync_seconds=_env_float("PORTAL_SYNC_SECONDS", 5.0, 2.0),
            portal_sync_heartbeat_seconds=_env_float("PORTAL_SYNC_HEARTBEAT_SECONDS", 60.0, 5.0),
            portal_sync_timeout_seconds=_env_float("PORTAL_SYNC_TIMEOUT_SECONDS", 10.0, 2.0),
            portal_sync_verify_tls=_env_bool("PORTAL_SYNC_VERIFY_TLS", True),
            portal_sync_in_process=_env_bool("PORTAL_SYNC_IN_PROCESS", cloud),
            portal_action_poll_seconds=_env_float("PORTAL_ACTION_POLL_SECONDS", 3.0, 1.0),
            portal_action_timeout_seconds=_env_float("PORTAL_ACTION_TIMEOUT_SECONDS", 10.0, 2.0),
            portal_action_verify_tls=_env_bool("PORTAL_ACTION_VERIFY_TLS", True),
            runtime_mode=runtime_mode,
            log_dir=os.getenv("LOG_DIR", default_logs).strip() or default_logs,
            twitch_token_db=os.getenv("TWITCH_TOKEN_DB", default_token_db).strip(),
            cloud_require_existing_database=_env_bool("CLOUD_REQUIRE_EXISTING_DATABASE", True),
            cloud_bootstrap_wait_seconds=_env_int("CLOUD_BOOTSTRAP_WAIT_SECONDS", 30, 5),
            stream_status_cache_seconds=_env_float("STREAM_STATUS_CACHE_SECONDS", 15.0, 2.0),
            stream_status_stale_seconds=_env_float("STREAM_STATUS_STALE_SECONDS", 90.0, 15.0),
            subscription_status_cache_seconds=_env_float("SUBSCRIPTION_STATUS_CACHE_SECONDS", 300.0, 15.0),
            subscription_status_stale_seconds=_env_float("SUBSCRIPTION_STATUS_STALE_SECONDS", 900.0, 60.0),
        )

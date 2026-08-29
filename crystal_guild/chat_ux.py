from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
import time

from .time_format import format_duration

# Keep command guidance in one small, dependency-free module so error
# handling never needs to know gameplay rules or touch the authoritative DB.
COMMAND_USAGE: dict[str, str] = {
    "guild": "!guild [topic]",
    "recruit": "!recruit",
    "hero": "!hero",
    "next": "!next",
    "job": "!job [name]",
    "jobinfo": "!jobinfo <job>",
    "abilities": "!abilities [job]",
    "mastery": "!mastery [job slot]",
    "stance": "!stance [name]",
    "venture": "!venture",
    "join": "!join",
    "encounter": "!encounter",
    "battlelog": "!battlelog",
    "attack": "!attack",
    "ability": "!ability <name> [target]",
    "defend": "!defend",
    "rest": "!rest",
    "use": "!use <item> [target]",
    "regions": "!regions",
    "travel": "!travel <region>",
    "inventory": "!inventory [category]",
    "gear": "!gear",
    "equip": "!equip <item>",
    "shop": "!shop",
    "item": "!item <name>",
    "gil": "!gil",
    "fellowship": "!fellowship",
    "project": "!project",
    "contribute": "!contribute gil <amount> | !contribute <amount> <item>",
    "orders": "!orders",
    "workshop": "!workshop | !refine <service> [batches]",
    "deeds": "!deeds",
    "facilities": "!facilities",
    "contributions": "!contributions",
    "rank": "!rank",
    "buy": "!buy <slot or item> [qty]",
    "sell": "!sell <item> [qty]",
    "hunts": "!hunts [C|B|A|S]",
    "hunt": "!hunt [name]",
    "quests": "!quests",
    "quest": "!quest [name]",
    "titles": "!titles [category|rarity]",
    "title": "!title <name>",
    "blacksmith": "!blacksmith",
    "recipes": "!recipes",
    "recipe": "!recipe <name>",
    "craft": "!craft <recipe> [qty]",
    "upgrade": "!upgrade <item>",
    "sealshop": "!sealshop",
    "sealbuy": "!sealbuy <item> [qty]",
    "relics": "!relics",
    "relic": "!relic <name>",
    "awaken": "!awaken <name>",
    "monsters": "!monsters [region]",
    "monster": "!monster <name>",
    "bestiary": "!bestiary",
    "achievements": "!achievements [category]",
    "achievement": "!achievement <name>",
    "records": "!records",
    "leaderboard": "!leaderboard [metric]",
    "daily": "!daily",
    "bosses": "!bosses [tier]",
    "bossinfo": "!bossinfo <name>",
    "raid": "!raid",
    "limit": "!limit",
    "summon": "!summon [name]",
    "revive": "!revive <hero>",
    "raidstats": "!raidstats",
    "boss": "!boss",
    "health": "!health",
    "economy": "!economy [days]",
    "cgversion": "!cgversion",
    "encounterdebug": "!encounterdebug",
    "directtest": "!directtest",
    "readyall": "!readyall",
    "resettimers": "!resettimers",
    "clearadventures": "!clearadventures",
    "fellowshipproject": "!fellowshipproject <project>",
    "additem": "!additem <player> | <item> | [quantity]",
    "removeitem": "!removeitem <player> | <item> | [quantity]",
    "resolveencounter": "!resolveencounter",
    "clearencounter": "!clearencounter",
    "spawnboss": "!spawnboss <name>",
    "resolveboss": "!resolveboss",
}

ALIASES: dict[str, str] = {
    "rpghelp": "guild", "cghelp": "guild", "cgcommands": "guild", "rpg": "guild",
    "me": "hero", "profile": "hero", "status": "hero",
    "guildinfo": "fellowship", "guildrecord": "contributions", "guildrank": "rank",
    "class": "job", "jobs": "job", "skills": "abilities",
    "adv": "venture", "adventure": "venture", "fight": "join", "rally": "join",
    "battle": "encounter", "enc": "encounter", "roundlog": "battlelog", "combatlog": "battlelog",
    "skill": "ability", "cast": "ability", "guard": "defend", "camp": "rest", "region": "regions",
    "inv": "inventory", "equipment": "gear", "huntboard": "hunts", "marks": "hunts", "mark": "hunt",
    "smith": "blacksmith", "forge": "blacksmith", "enhance": "upgrade", "quartermaster": "sealshop",
    "mob": "monster", "enemy": "monster", "beasts": "bestiary", "ach": "achievements", "achinfo": "achievement",
    "career": "records", "stats": "records", "lb": "leaderboard", "raidcontrib": "raidstats", "raidboard": "raidstats",
}


SILENT_COMMAND_ERRORS: frozenset[str] = frozenset({"CommandNotFound"})


def should_silence_command_error(error_name: str | None) -> bool:
    """Return True for command-framework errors that do not belong to Crystal Guild.

    Twitch channels commonly run several bots with the same prefix. An unknown
    ``!command`` is therefore treated as foreign traffic, not as a Crystal Guild
    typo. The live Twitch adapter drops it before logging, feedback, or gameplay
    code. Local simulator tooling may still call ``format_command_error`` directly
    when explicit typo feedback is useful during development.
    """
    return str(error_name or "") in SILENT_COMMAND_ERRORS


def registered_command_names() -> frozenset[str]:
    """Names Crystal Guild intentionally owns on the shared Twitch prefix."""
    return frozenset(COMMAND_USAGE) | frozenset(ALIASES)


def is_crystal_guild_command(name: str | None) -> bool:
    key = (name or "").strip().lower().lstrip("!")
    return bool(key) and key in registered_command_names()


def canonical_command(name: str | None) -> str:
    key = (name or "").strip().lower().lstrip("!")
    return ALIASES.get(key, key)


def command_usage(name: str | None) -> str | None:
    return COMMAND_USAGE.get(canonical_command(name))


def suggest_command(name: str | None) -> str | None:
    key = (name or "").strip().lower().lstrip("!")
    if not key:
        return None
    choices = sorted(set(COMMAND_USAGE) | set(ALIASES))
    matches = get_close_matches(key, choices, n=1, cutoff=0.68)
    if not matches:
        return None
    return canonical_command(matches[0])


def format_command_error(
    error_name: str,
    invoked: str | None,
    command_name: str | None = None,
    remaining: float | int | None = None,
) -> str:
    invoked_key = (invoked or "command").strip().lower().lstrip("!")
    canonical = canonical_command(command_name or invoked_key)
    if error_name in {"MissingRequiredArgument", "BadArgument", "ConversionError"}:
        usage = command_usage(canonical)
        if usage:
            return f"MOGNET — Usage: {usage} | Need details? !guild {canonical}"
        return f"MOGNET — I couldn't read !{canonical}. Try !guild {canonical} for the short command guide."
    if error_name == "CommandOnCooldown":
        seconds = max(1, int(float(remaining or 1)))
        return f"MOGNET — !{canonical} is cooling down. Ready in about {format_duration(seconds)}."
    if error_name == "CommandNotFound":
        suggestion = suggest_command(invoked_key)
        if suggestion:
            return f"MOGNET — Unknown command !{invoked_key}. Did you mean !{suggestion}? | Command map: !guild"
        return f"MOGNET — Unknown command !{invoked_key}. Try !guild for the command map or !next for your next action."
    return "MOGNET — Crystal Guild hit a command error. It was logged; try again in a moment."


@dataclass
class FeedbackGate:
    """Tiny per-user anti-noise gate for repeated UX/error feedback."""

    cooldown_seconds: float = 8.0

    def __post_init__(self) -> None:
        self._last: dict[tuple[str, str], float] = {}

    def allow(self, user_id: str, bucket: str, now: float | None = None) -> bool:
        stamp = time.monotonic() if now is None else float(now)
        key = (str(user_id), str(bucket))
        previous = self._last.get(key)
        if previous is not None and stamp - previous < self.cooldown_seconds:
            return False
        self._last[key] = stamp
        if len(self._last) > 2048:
            cutoff = stamp - max(60.0, self.cooldown_seconds * 4)
            self._last = {k: v for k, v in self._last.items() if v >= cutoff}
        return True

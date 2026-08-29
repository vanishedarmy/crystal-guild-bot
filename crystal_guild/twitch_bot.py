from __future__ import annotations

import asyncio
import logging
import signal
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import twitchio
from twitchio import eventsub
from twitchio.ext import commands

from . import __version__
from .config import Settings
from .data import GameData
from .database import Database
from .engine import CrystalGuildEngine, GameResult
from .help_system import help_messages
from .portal_actions import PortalActionWorker
from .portal_sync import PortalSyncClient, PortalSyncWorker
from .player_snapshot import PortalRepository
from .token_store import TwitchTokenStore
from .stream_status import TwitchStreamStatus
from .subscription_status import TwitchSubscriptionStatus
from .daily_provisions import subscriber_perk
from .cloud_runtime import ensure_runtime_directories, wait_for_cloud_bootstrap, create_startup_backup
from .chat_ux import FeedbackGate, format_command_error, should_silence_command_error
from .time_format import format_duration
from .encounter_daemon import EncounterDaemon, NotificationDispatcher, TwitchRESTChatSender, _packed_messages

LOGGER = logging.getLogger("CrystalGuild")
APP_VERSION = __version__


def _configure_file_logging(log_dir_value: str = "logs") -> None:
    log_dir = Path(log_dir_value)
    log_dir.mkdir(parents=True, exist_ok=True)
    path = (log_dir / "crystal_guild.log").resolve()
    root = logging.getLogger()
    if any(isinstance(h, RotatingFileHandler) and Path(getattr(h, "baseFilename", "")).resolve() == path for h in root.handlers):
        return
    handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root.addHandler(handler)


def _identity(ctx: commands.Context) -> tuple[str, str, str]:
    chatter = ctx.chatter
    uid = str(chatter.id)
    username = getattr(chatter, "name", None) or uid
    display = getattr(chatter, "display_name", None) or username
    return uid, username, display


async def send_result(ctx: commands.Context, result: GameResult, limit: int = 3) -> None:
    for message in _packed_messages(result.messages, max_messages=limit):
        await ctx.send(message)


class RPGCommands(commands.Component):
    def __init__(self, bot: "CrystalGuildBot") -> None:
        self.bot = bot
        self.game = bot.game

    def _identity(self, ctx: commands.Context) -> tuple[str, str, str]:
        uid, username, display = _identity(ctx)
        # Every intentional Twitch command counts as player activity. Long Rest
        # recovery is applied before the command reaches gameplay validation.
        self.game.record_player_action(uid)
        return uid, username, display

    async def _owner_only(self, ctx: commands.Context) -> bool:
        uid, _, _ = self._identity(ctx)
        if uid == self.bot.settings.owner_id:
            return True
        if self.bot.feedback_gate.allow(uid, "owner-only"):
            await ctx.send("MOGNET — That command is streamer-only. Player commands: !guild | Your next action: !next")
        return False

    async def _require_stream_live(self, ctx: commands.Context, activity: str) -> bool:
        status = await asyncio.to_thread(self.bot.stream_status.refresh)
        if status["live"]:
            return True
        uid, _, _ = self._identity(ctx)
        bucket = f"stream-live:{activity.lower()}"
        if not self.bot.feedback_gate.allow(uid, bucket):
            return False
        if status["state"] == "OFFLINE":
            await ctx.send(
                f"MOGNET — {activity} is live-stream only. The channel is currently OFFLINE. "
                "Portal Solo Venture and other Portal activities remain available off-stream."[:480]
            )
        else:
            await ctx.send(
                f"MOGNET — I can't confirm the channel is LIVE right now, so {activity} is temporarily paused. "
                "Portal Solo Venture remains available off-stream."[:480]
            )
        return False

    @commands.command()
    async def recruit(self, ctx: commands.Context) -> None:
        uid, username, display = self._identity(ctx)
        await send_result(ctx, self.game.recruit(uid, username, display))

    @commands.command(aliases=["me", "profile", "status"])
    async def hero(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.hero(uid))

    @commands.command()
    async def next(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.next_step(uid))

    @commands.command(aliases=["class", "jobs"])
    async def job(self, ctx: commands.Context, *, job_name: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.choose_job(uid, job_name))

    @commands.command()
    async def jobinfo(self, ctx: commands.Context, *, job_name: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.job_info(uid, job_name))

    @commands.command(aliases=["skills"])
    async def abilities(self, ctx: commands.Context, *, job_name: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.abilities(uid, job_name))

    @commands.command()
    async def mastery(self, ctx: commands.Context, *, selection: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        if not selection:
            await send_result(ctx, self.game.mastery(uid))
            return
        parts = selection.rsplit(" ", 1)
        slot = None
        query = selection
        if len(parts) == 2 and parts[1].isdigit():
            query, slot = parts[0], int(parts[1])
        await send_result(ctx, self.game.mastery(uid, query, slot))

    @commands.command()
    async def stance(self, ctx: commands.Context, stance_name: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.set_stance(uid, stance_name))

    @commands.command(aliases=["adv", "adventure"])
    async def venture(self, ctx: commands.Context) -> None:
        if not await self._require_stream_live(ctx, "Rally Venture"):
            return
        uid, _, _ = self._identity(ctx)
        result = self.game.venture(uid)
        await send_result(ctx, result, limit=4)
        if result.ok and result.data.get("encounter_started"):
            self.bot.encounter_daemon.wake()

    @commands.command(aliases=["fight", "rally"])
    async def join(self, ctx: commands.Context) -> None:
        if not await self._require_stream_live(ctx, "Rally participation"):
            return
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.join_encounter(uid))

    @commands.command(aliases=["battle", "enc"])
    async def encounter(self, ctx: commands.Context) -> None:
        await send_result(ctx, self.game.encounter_status(), limit=4)

    @commands.command(aliases=["roundlog", "combatlog"])
    async def battlelog(self, ctx: commands.Context) -> None:
        # Keep automatic announcements compact; detailed recent
        # round recaps remain available on demand without affecting timers.
        await send_result(ctx, self.game.battle_log(), limit=4)

    # Active Battle commands (also reused by Raid rounds) intentionally remain thin adapters. All validation,
    # targeting and combat math live in CrystalGuildEngine so Twitch delivery
    # cannot become a second source of gameplay rules.
    @commands.command()
    async def attack(self, ctx: commands.Context) -> None:
        if not await self._require_stream_live(ctx, "Combat actions"):
            return
        uid, _, _ = self._identity(ctx)
        # Queue intent only. The scheduler owns the round deadline.
        await send_result(ctx, self.game.battle_attack(uid))

    @commands.command(aliases=["skill", "cast"])
    async def ability(self, ctx: commands.Context, *, ability_name: str | None = None) -> None:
        if not await self._require_stream_live(ctx, "Combat actions"):
            return
        uid, _, _ = self._identity(ctx)
        # Queue intent only. Never use chat traffic as a timer callback.
        await send_result(ctx, self.game.battle_ability(uid, ability_name), limit=3)

    @commands.command(aliases=["guard"])
    async def defend(self, ctx: commands.Context) -> None:
        if not await self._require_stream_live(ctx, "Combat actions"):
            return
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.battle_defend(uid))

    @commands.command(aliases=["camp"])
    async def rest(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        try:
            stream = await asyncio.to_thread(self.bot.stream_status.refresh)
            stream_live = bool(stream.get("live"))
        except Exception:
            LOGGER.exception("Unable to resolve Twitch stream state for Camp; using OFFLINE timer.")
            stream_live = False
        await send_result(ctx, self.game.rest(uid, stream_live=stream_live), limit=3)

    @commands.command()
    async def use(self, ctx: commands.Context, *, item_name: str) -> None:
        uid, _, _ = self._identity(ctx)
        in_timed_combat = (
            bool(self.game.active_encounter and self.game.active_encounter.get("state") == "combat" and uid in self.game.encounter_roster)
            or bool(self.game.active_boss and self.game.active_boss.get("state") == "combat" and uid in self.game.raid_roster)
        )
        if in_timed_combat and not await self._require_stream_live(ctx, "Combat actions"):
            return
        if in_timed_combat:
            await send_result(ctx, self.game.use_item(uid, item_name))
            return

        # Outside battle, field items may support another adventurer while LIVE.
        # Existing `!use <item>` remains self-targeted; social targeting uses the
        # explicit separator so multi-word item names stay unambiguous.
        raw = str(item_name or "").strip()
        target_query = None
        if "|" in raw:
            item_query, target = [part.strip() for part in raw.split("|", 1)]
            if item_query and target:
                raw = item_query
                target_query = target
        elif " on @" in raw.lower():
            marker = raw.lower().rfind(" on @")
            item_query, target = raw[:marker].strip(), raw[marker + 4:].strip()
            if item_query and target:
                raw = item_query
                target_query = target
        else:
            parts = raw.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].startswith("@") and parts[0].strip():
                raw = parts[0].strip()
                target_query = parts[1].strip()
        if target_query and not await self._require_stream_live(ctx, "Using field items on other adventurers"):
            return
        await send_result(
            ctx,
            self.game.use_item(uid, raw, target_query=target_query, stream_live=True if target_query else None),
        )

    @commands.command(aliases=["region"])
    async def regions(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.regions(uid))

    @commands.command()
    async def travel(self, ctx: commands.Context, *, region: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.travel(uid, region))

    @commands.command(aliases=["inv"])
    async def inventory(self, ctx: commands.Context, category: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.inventory(uid, category))

    @commands.command(aliases=["equipment"])
    async def gear(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.gear(uid))

    @commands.command()
    async def equip(self, ctx: commands.Context, *, item: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.equip(uid, item))

    @commands.command()
    async def shop(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.shop(uid))

    @commands.command()
    async def item(self, ctx: commands.Context, *, item_name: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.inspect_item(uid, item_name))

    @commands.command()
    async def gil(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.gil(uid))

    @commands.command(aliases=["guildinfo"])
    async def fellowship(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.fellowship(uid), limit=4)

    @commands.command()
    async def project(self, ctx: commands.Context) -> None:
        await send_result(ctx, self.game.fellowship_project(), limit=3)

    @commands.command()
    async def contribute(self, ctx: commands.Context, *, contribution: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.contribute_fellowship(uid, contribution), limit=3)

    @commands.command()
    async def orders(self, ctx: commands.Context) -> None:
        await send_result(ctx, self.game.fellowship_orders(), limit=3)

    @commands.command(aliases=["guildairship"])
    async def airship(self, ctx: commands.Context) -> None:
        await send_result(ctx, self.game.fellowship_airship(), limit=3)

    @commands.command()
    async def deeds(self, ctx: commands.Context) -> None:
        await send_result(ctx, self.game.fellowship_deeds(), limit=3)

    @commands.command(aliases=["guildlegacy"])
    async def legacy(self, ctx: commands.Context) -> None:
        await send_result(ctx, self.game.fellowship_legacy(), limit=3)

    @commands.command()
    async def facilities(self, ctx: commands.Context) -> None:
        await send_result(ctx, self.game.fellowship_facilities(), limit=3)

    @commands.command(aliases=["guildworkshop"])
    async def workshop(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.fellowship_workshop(uid), limit=3)

    @commands.command()
    async def refine(self, ctx: commands.Context, *, request: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.fellowship_refine(uid, request), limit=3)

    @commands.command(aliases=["guildrecord"])
    async def contributions(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.fellowship_contributions(uid), limit=3)

    @commands.command(aliases=["guildrank"])
    async def rank(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.fellowship_rank(uid), limit=2)

    @commands.command()
    async def buy(self, ctx: commands.Context, *, purchase: str) -> None:
        uid, _, _ = self._identity(ctx)
        parts = purchase.rsplit(" ", 1)
        qty = 1
        query = purchase
        if len(parts) == 2 and parts[1].isdigit():
            query, qty = parts[0], int(parts[1])
        await send_result(ctx, self.game.buy(uid, query, qty))

    @commands.command()
    async def sell(self, ctx: commands.Context, *, sale: str) -> None:
        uid, _, _ = self._identity(ctx)
        parts = sale.rsplit(" ", 1)
        qty = 1
        query = sale
        if len(parts) == 2 and parts[1].isdigit():
            query, qty = parts[0], int(parts[1])
        await send_result(ctx, self.game.sell(uid, query, qty))

    @commands.command(aliases=["huntboard", "marks"])
    async def hunts(self, ctx: commands.Context, rank: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.hunts(uid, rank))

    @commands.command(aliases=["mark"])
    async def hunt(self, ctx: commands.Context, *, hunt_name: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        if not hunt_name:
            await send_result(ctx, self.game.hunts(uid))
            return
        if not await self._require_stream_live(ctx, "Active Hunt"):
            return
        result = self.game.hunt(uid, hunt_name)
        await send_result(ctx, result, limit=5)
        if result.ok and result.data.get("hunt_started"):
            # Timed Hunts create a rank-based return deadline. Wake the
            # scheduler so it can sleep toward that timestamp even if no
            # further chat message is ever sent.
            self.bot.encounter_daemon.wake()

    @commands.command(aliases=["stable"])
    async def chocobo(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.chocobo(uid), limit=3)

    @commands.command()
    async def chocoboquest(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.chocobo_quest(uid), limit=3)

    @commands.command(aliases=["writ"])
    async def chocobowrit(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.buy_chocobo_writ(uid), limit=3)

    @commands.command()
    async def registerchocobo(self, ctx: commands.Context, *, name: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.register_chocobo(uid, name), limit=3)

    @commands.command()
    async def chocoboname(self, ctx: commands.Context, *, name: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.rename_chocobo(uid, name), limit=2)

    @commands.command()
    async def quests(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.quests(uid))

    @commands.command()
    async def quest(self, ctx: commands.Context, *, quest_name: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        if not quest_name:
            await send_result(ctx, self.game.quests(uid), limit=4)
            return
        await send_result(ctx, self.game.quest(uid, quest_name))

    @commands.command()
    async def titles(self, ctx: commands.Context, *, filter_query: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.titles(uid, filter_query))

    @commands.command()
    async def title(self, ctx: commands.Context, *, title_name: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.set_title(uid, title_name))

    @commands.command(aliases=["smith", "forge"])
    async def blacksmith(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.blacksmith(uid))

    @commands.command()
    async def recipes(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.recipes(uid))

    @commands.command()
    async def recipe(self, ctx: commands.Context, *, recipe_name: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.recipe_info(uid, recipe_name))

    @commands.command()
    async def craft(self, ctx: commands.Context, *, selection: str) -> None:
        uid, _, _ = self._identity(ctx)
        parts = selection.rsplit(" ", 1)
        qty = 1
        query = selection
        if len(parts) == 2 and parts[1].isdigit():
            query, qty = parts[0], int(parts[1])
        await send_result(ctx, self.game.craft(uid, query, qty))

    @commands.command(aliases=["enhance"])
    async def upgrade(self, ctx: commands.Context, *, item_name: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.upgrade(uid, item_name))

    @commands.command(aliases=["quartermaster"])
    async def sealshop(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.sealshop(uid))

    @commands.command()
    async def sealbuy(self, ctx: commands.Context, *, selection: str) -> None:
        uid, _, _ = self._identity(ctx)
        parts = selection.rsplit(" ", 1)
        qty = 1
        query = selection
        if len(parts) == 2 and parts[1].isdigit():
            query, qty = parts[0], int(parts[1])
        await send_result(ctx, self.game.sealbuy(uid, query, qty))

    @commands.command()
    async def relics(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.relics(uid))

    @commands.command()
    async def relic(self, ctx: commands.Context, *, relic_name: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.relic(uid, relic_name))

    @commands.command()
    async def awaken(self, ctx: commands.Context, *, relic_name: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.awaken_relic(uid, relic_name), limit=4)

    @commands.command()
    async def monsters(self, ctx: commands.Context, *, region_name: str | None = None) -> None:
        await send_result(ctx, self.game.monsters(region_name), limit=4)

    @commands.command(aliases=["mob", "enemy"])
    async def monster(self, ctx: commands.Context, *, monster_name: str) -> None:
        await send_result(ctx, self.game.monster_info(monster_name))

    @commands.command(aliases=["beasts"])
    async def bestiary(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.bestiary(uid))

    @commands.command(aliases=["ach"])
    async def achievements(self, ctx: commands.Context, *, category: str | None = None) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.achievements(uid, category), limit=4)

    @commands.command(aliases=["achinfo"])
    async def achievement(self, ctx: commands.Context, *, achievement_name: str) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.achievement(uid, achievement_name))

    @commands.command(aliases=["career", "stats"])
    async def records(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.records(uid), limit=4)

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context, metric: str = "level") -> None:
        await send_result(ctx, self.game.leaderboard(metric))

    @commands.command()
    async def daily(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        status = await asyncio.to_thread(self.bot.subscription_status.refresh, uid)
        await send_result(ctx, self.game.daily(uid, int(status.get("tier") or 0)))

    @commands.command()
    async def substatus(self, ctx: commands.Context) -> None:
        uid, _, _ = self._identity(ctx)
        status = await asyncio.to_thread(self.bot.subscription_status.refresh, uid, True)
        if status["state"] == "UNKNOWN":
            scope_note = " Broadcaster reauthorization for channel:read:subscriptions may be required." if status.get("scope_required") else ""
            await ctx.send(("CG SUB — UNKNOWN. Twitch subscriber status could not be verified; standard rewards apply for now." + scope_note)[:480])
            return
        perk = subscriber_perk(int(status.get("tier") or 0))
        if not status.get("subscribed"):
            await ctx.send("CG SUB — Not currently subscribed | Daily: standard Gil + 1 random provision bundle."[:480])
            return
        gifted = " · gifted" if status.get("is_gift") else ""
        await ctx.send(
            f"CG SUB — Tier {perk['tier']}{gifted} | Daily perk: +{perk['gil_bonus_percent']}% Gil + {perk['rolls']} random provision rolls."[:480]
        )

    @commands.command()
    async def bosses(self, ctx: commands.Context, tier: str | None = None) -> None:
        await send_result(ctx, self.game.bosses(tier), limit=5)

    @commands.command()
    async def bossinfo(self, ctx: commands.Context, *, boss_name: str) -> None:
        await send_result(ctx, self.game.boss_info(boss_name))

    @commands.command()
    async def raid(self, ctx: commands.Context) -> None:
        if not await self._require_stream_live(ctx, "Raid participation"):
            return
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.raid_join(uid))

    @commands.command()
    async def limit(self, ctx: commands.Context) -> None:
        if not await self._require_stream_live(ctx, "Raid actions"):
            return
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.limit_break(uid))

    @commands.command()
    async def summon(self, ctx: commands.Context, *, summon_name: str | None = None) -> None:
        if not await self._require_stream_live(ctx, "Raid actions"):
            return
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.summon_raid(uid, summon_name))

    @commands.command()
    async def revive(self, ctx: commands.Context, *, target: str) -> None:
        if not await self._require_stream_live(ctx, "Raid actions"):
            return
        uid, _, _ = self._identity(ctx)
        await send_result(ctx, self.game.revive_raid(uid, target))

    @commands.command(aliases=["raidcontrib", "raidboard"])
    async def raidstats(self, ctx: commands.Context) -> None:
        await send_result(ctx, self.game.raid_stats())

    @commands.command()
    async def boss(self, ctx: commands.Context) -> None:
        await send_result(ctx, self.game.boss_status())

    @commands.command()
    async def resolveencounter(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        await send_result(ctx, self.game.resolve_encounter(), limit=5)

    @commands.command()
    async def clearencounter(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        await send_result(ctx, self.game.abort_encounter(), limit=2)

    @commands.command()
    async def encounterdebug(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        snapshot = self.game.combat_snapshot()
        active = snapshot["encounter"]
        daemon = self.bot.encounter_daemon.status()
        notifier = self.bot.notifier.status()
        if not active:
            await ctx.send(
                f"Encounter debug: none active | daemon={daemon['state']} ticks={daemon['ticks']} "
                f"last_tick={daemon['last_tick_age']}s last_resolved={daemon['last_resolved_id']} "
                f"notifier={notifier['state']} queued={notifier['queued']} last_error={daemon['last_error']}"[:480]
            )
            return
        encounter_id = int(active["id"])
        remaining = max(0, int(float(active["closes_at"]) - time.time()))
        await ctx.send(
            f"Encounter debug: id={encounter_id} state={'OPEN' if remaining > 0 else 'OVERDUE'} "
            f"remaining={format_duration(remaining)} daemon={daemon['state']} ticks={daemon['ticks']} "
            f"roster={snapshot['encounter_roster']} notifier={notifier['state']} "
            f"last_error={daemon['last_error']}"[:480]
        )

    @commands.command()
    async def directtest(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        await ctx.send("Direct Twitch API test queued. A second message should appear without another chat command."[:480])
        try:
            await asyncio.to_thread(
                self.bot.direct_sender.send,
                "Crystal Guild direct API PASS. Autonomous combat announcements can bypass TwitchIO.",
            )
        except Exception as exc:
            LOGGER.exception("Direct Twitch API test failed")
            await ctx.send(f"Direct Twitch API FAIL: {type(exc).__name__}: {exc}"[:480])

    @commands.command()
    async def cgversion(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        daemon = self.bot.encounter_daemon.status()
        notifier = self.bot.notifier.status()
        portal = self.bot.portal_actions.status()
        sync = self.bot.portal_sync.status() if self.bot.portal_sync else {"state": "external"}
        await ctx.send(
            f"Crystal Guild v{APP_VERSION} | mode={self.bot.settings.runtime_mode} twitch_ready={self.bot._ready_count} reconnects={max(0, self.bot._ready_count-1)} | "
            f"daemon={daemon['state']} ticks={daemon['ticks']} notifier={notifier['state']} queue={notifier['queued']} actions={portal['state']} sync={sync['state']} db={'OK' if self.bot.db.health_check() else 'FAIL'} | "
            f"loaded={Path(__file__).resolve()}"[:480]
        )

    @commands.command()
    async def health(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        daemon = self.bot.encounter_daemon.status()
        notifier = self.bot.notifier.status()
        portal = self.bot.portal_actions.status()
        sync = self.bot.portal_sync.status() if self.bot.portal_sync else {"state": "external", "syncs": 0}
        runtime = self.game.runtime_status()
        stream = self.bot.stream_status.snapshot()
        stream_age = "never" if stream["last_success_age"] is None else f"{stream['last_success_age']}s"
        tx = self.bot.db.transaction_stats()
        due = daemon.get("next_due_in_ms", -1)
        due_text = "none" if due < 0 else f"{due}ms"
        recovery = " recovered" if runtime["recovered"] else ""
        rollback_total = tx["rollbacks"] + tx["savepoint_rollbacks"]
        await ctx.send(
            f"CG HEALTH v{APP_VERSION} | DB={'OK' if self.bot.db.health_check() else 'FAIL'} rb={rollback_total} | "
            f"twitch_ready={self.bot._ready_count} reconnects={max(0, self.bot._ready_count-1)} | "
            f"daemon={daemon['state']}/{daemon['last_tick_age']}s lag={daemon['timer_lag_ms']}ms due={due_text} "
            f"err={daemon['consecutive_failures']} backoff={daemon['retry_backoff_ms']}ms | "
            f"notifier={notifier['state']} q={notifier['queued']} fail={notifier['failed_batches']} | "
            f"actions={portal['state']} done={portal['processed']} sync={sync['state']}/{sync.get('syncs', 0)} mode={self.bot.settings.runtime_mode} | "
            f"stream={stream['state']} age={stream_age} | state={runtime['active']}{recovery} | last={daemon['last_action']}"[:480]
        )


    @commands.command()
    async def streamstatus(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        status = await asyncio.to_thread(self.bot.stream_status.refresh, True)
        age = "never" if status["last_success_age"] is None else f"{status['last_success_age']}s"
        extra = ""
        if status["state"] == "LIVE":
            details = " · ".join(part for part in (status.get("game_name"), status.get("title")) if part)
            extra = f" | {details}" if details else ""
        error = f" | error={status['last_error']}" if status["state"] == "UNKNOWN" and status["last_error"] else ""
        await ctx.send(f"CG STREAM — {status['state']} | last confirmed {age} | checks={status['checks']}{extra}{error}"[:480])


    @commands.command()
    async def fellowshipproject(self, ctx: commands.Context, *, project_name: str) -> None:
        if not await self._owner_only(ctx):
            return
        await send_result(ctx, self.game.set_fellowship_project(project_name), limit=3)

    @commands.command()
    async def airshipmission(self, ctx: commands.Context, *, mission_name: str) -> None:
        if not await self._owner_only(ctx):
            return
        await send_result(ctx, self.game.set_airship_mission(mission_name), limit=3)

    @commands.command()
    async def readyall(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        await send_result(ctx, self.game.ready_all_players(), limit=2)

    @commands.command()
    async def resettimers(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        await send_result(ctx, self.game.reset_all_player_timers(), limit=2)

    @commands.command(aliases=["clearventures"])
    async def clearadventures(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        result = self.game.clear_all_adventures()
        await send_result(ctx, result, limit=2)
        if result.ok:
            # A clear is a recovery operation: wake the hosted snapshot worker
            # immediately so Portal drops orphaned Solo/Hunt state promptly.
            if self.bot.portal_sync:
                self.bot.portal_sync.wake()
            self.bot.encounter_daemon.wake()

    @commands.command(aliases=["giveitem"])
    async def additem(self, ctx: commands.Context, *, request: str) -> None:
        if not await self._owner_only(ctx):
            return
        result = self.game.streamer_item_admin(request, remove=False)
        await send_result(ctx, result, limit=2)
        if result.ok and self.bot.portal_sync:
            self.bot.portal_sync.wake()

    @commands.command(aliases=["takeitem"])
    async def removeitem(self, ctx: commands.Context, *, request: str) -> None:
        if not await self._owner_only(ctx):
            return
        result = self.game.streamer_item_admin(request, remove=True)
        await send_result(ctx, result, limit=2)
        if result.ok and self.bot.portal_sync:
            self.bot.portal_sync.wake()

    @commands.command()
    async def economy(self, ctx: commands.Context, days: int = 7) -> None:
        if not await self._owner_only(ctx):
            return
        await send_result(ctx, self.game.economy_report(days), limit=2)

    @commands.command()
    async def spawnboss(self, ctx: commands.Context, *, boss_name: str) -> None:
        if not await self._owner_only(ctx):
            return
        result = self.game.spawn_boss(boss_name)
        await send_result(ctx, result, limit=3)
        if result.ok and result.data.get("raid_spawned"):
            self.bot.encounter_daemon.wake()

    @commands.command()
    async def resolveboss(self, ctx: commands.Context) -> None:
        if not await self._owner_only(ctx):
            return
        await send_result(ctx, self.game.resolve_boss())

    @commands.command(aliases=["rpg", "cghelp", "cgcommands", "rpghelp"])
    async def guild(self, ctx: commands.Context, *, topic: str | None = None) -> None:
        if topic:
            for message in help_messages(topic):
                await ctx.send(message[:480])
            return
        uid, _, _ = self._identity(ctx)
        await ctx.send(
            "MOGNET — !next = what to do now | !hero = character | !venture = adventure | "
            "!inventory = items | !hunts = marks | !guild <topic> = focused help"
        )
        await send_result(ctx, self.game.next_step(uid), limit=1)



class CrystalGuildBot(commands.AutoBot):
    def __init__(
        self,
        settings: Settings,
        db: Database,
        game: CrystalGuildEngine,
        encounter_daemon: EncounterDaemon,
        direct_sender: TwitchRESTChatSender,
        notifier: NotificationDispatcher,
        portal_actions: PortalActionWorker,
        portal_sync: PortalSyncWorker | None = None,
        token_store: TwitchTokenStore | None = None,
        stream_status: TwitchStreamStatus | None = None,
        subscription_status: TwitchSubscriptionStatus | None = None,
    ) -> None:
        self.settings = settings
        self.db = db
        self.game = game
        self.encounter_daemon = encounter_daemon
        self.direct_sender = direct_sender
        self.notifier = notifier
        self.portal_actions = portal_actions
        self.portal_sync = portal_sync
        self.token_store = token_store
        self.stream_status = stream_status or TwitchStreamStatus(
            settings.client_id, settings.client_secret, settings.owner_id,
            cache_seconds=settings.stream_status_cache_seconds,
            stale_seconds=settings.stream_status_stale_seconds,
        )
        self.subscription_status = subscription_status or TwitchSubscriptionStatus(
            settings.client_id, settings.owner_id, token_store,
            cache_seconds=settings.subscription_status_cache_seconds,
            stale_seconds=settings.subscription_status_stale_seconds,
        )
        self.feedback_gate = FeedbackGate(cooldown_seconds=8.0)
        self._ready_count = 0
        self._last_ready_at = 0.0
        subscriptions = [
            eventsub.ChatMessageSubscription(
                broadcaster_user_id=settings.owner_id,
                user_id=settings.bot_id,
            )
        ]
        super().__init__(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            bot_id=settings.bot_id,
            owner_id=settings.owner_id,
            prefix=settings.prefix,
            subscriptions=subscriptions,
            force_subscribe=True,
        )

    async def add_token(self, token: str, refresh: str):
        response = await super().add_token(token, refresh)
        if self.token_store:
            self.token_store.upsert(str(response.user_id), token, refresh)
        return response

    async def load_tokens(self, path: str | None = None, /) -> None:
        if not self.token_store:
            await super().load_tokens(path)
            return
        rows = self.token_store.load()
        if not rows:
            LOGGER.error("Twitch token database is empty: %s", self.token_store.path)
            return
        for row in rows:
            # Use the base implementation here so loading existing rows does not
            # rewrite the token database on every process start.
            await super().add_token(row["access_token"], row["refresh_token"])
        LOGGER.info("Loaded %s managed Twitch token(s) from persistent SQLite.", len(rows))

    async def save_tokens(self, path: str | None = None, /) -> None:
        if not self.token_store:
            await super().save_tokens(path)
            return
        # add_token() and event_token_refreshed() persist every mutation. There
        # is no end-of-process JSON write in cloud mode.
        return None

    async def remove_token(self, user_id: str, /):
        result = await super().remove_token(user_id)
        if self.token_store:
            self.token_store.delete(str(user_id))
        return result

    async def event_token_refreshed(self, payload: twitchio.TokenRefreshedPayload) -> None:
        if self.token_store:
            self.token_store.upsert(str(payload.user_id), payload.token, payload.refresh_token)
            LOGGER.info("Persisted refreshed Twitch token for user ID %s", payload.user_id)

    async def setup_hook(self) -> None:
        await self.add_component(RPGCommands(self))
        LOGGER.info(
            "Crystal Guild v%s loaded from %s | mode=%s | combat daemon=%s | notifier=%s | portal_actions=%s | portal_sync=%s | token_store=%s",
            APP_VERSION,
            Path(__file__).resolve(),
            self.settings.runtime_mode,
            self.encounter_daemon.status()["state"],
            self.notifier.status()["state"],
            self.portal_actions.status()["state"],
            self.portal_sync.status()["state"] if self.portal_sync else "external",
            str(self.token_store.path) if self.token_store else "twitchio-file",
        )

    async def event_ready(self) -> None:
        self._ready_count += 1
        self._last_ready_at = time.monotonic()
        # A reconnect must never leave an already-due Crystal-owned timer asleep.
        self.encounter_daemon.wake()
        self.portal_actions.wake()
        if self.portal_sync:
            self.portal_sync.wake()
        try:
            stream = await asyncio.to_thread(self.stream_status.refresh, True)
            LOGGER.info("Twitch stream presence: %s", stream["state"])
        except Exception:
            LOGGER.exception("Unable to initialize Twitch stream presence; live-only gameplay will fail closed.")
        LOGGER.info(
            "Crystal Guild v%s connected. Bot ID: %s | ready_count=%s reconnects=%s | combat daemon=%s | notifier=%s",
            APP_VERSION,
            self.bot_id,
            self._ready_count,
            max(0, self._ready_count - 1),
            self.encounter_daemon.status()["state"],
            self.notifier.status()["state"],
        )

    async def event_command_error(self, payload: commands.CommandErrorPayload) -> None:
        exc = payload.exception
        error_name = type(exc).__name__
        # Shared-prefix coexistence rule: if TwitchIO could not resolve the
        # command to Crystal Guild, it belongs to somebody else (or nobody).
        # Ignore it before logging, feedback, or any gameplay/database path.
        if should_silence_command_error(error_name):
            return
        LOGGER.error(
            "Crystal Guild command failed: %s",
            exc,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        try:
            invoked = getattr(payload.context, "invoked_with", None) or "command"
            command = getattr(payload.context, "command", None)
            command_name = getattr(command, "name", None) or invoked
            remaining = getattr(exc, "remaining", None)
            try:
                uid, _, _ = _identity(payload.context)
            except Exception:
                uid = "unknown"
            bucket = f"command-error:{invoked}:{error_name}"
            if not self.feedback_gate.allow(uid, bucket):
                return
            message = format_command_error(error_name, invoked, command_name, remaining)
            await payload.context.send(message[:480])
        except Exception:
            LOGGER.exception("Unable to report command failure to Twitch chat")


def main() -> None:
    settings = Settings.from_env()
    ensure_runtime_directories(settings)
    wait_for_cloud_bootstrap(settings)
    twitchio.utils.setup_logging(level=logging.INFO)
    _configure_file_logging(settings.log_dir)
    LOGGER.info("Starting Crystal Guild v%s | runtime_mode=%s", APP_VERSION, settings.runtime_mode)

    if settings.cloud_runtime:
        create_startup_backup(settings)

    # Validate static content before creating persistent runtime resources.
    data = GameData(settings.data_dir)
    data.validate_or_raise()
    db = Database(settings.database_path)
    game = CrystalGuildEngine(
        db, data, settings.venture_cooldown_seconds, settings.encounter_join_seconds,
        settings.camp_rest_seconds, settings.raid_join_seconds, settings.raid_round_seconds,
        settings.overlay_state_path, shop_refresh_seconds=settings.shop_refresh_seconds,
        encounter_round_seconds=settings.encounter_round_seconds,
    )

    stream_status = TwitchStreamStatus(
        settings.client_id,
        settings.client_secret,
        settings.owner_id,
        cache_seconds=settings.stream_status_cache_seconds,
        stale_seconds=settings.stream_status_stale_seconds,
        on_live=lambda stream: game.refresh_all_players_for_stream(str(stream.get("started_at") or "")),
    )
    direct_sender = TwitchRESTChatSender(
        settings.client_id, settings.client_secret, settings.bot_id, settings.owner_id
    )
    notifier = NotificationDispatcher(
        direct_sender,
        delivery_allowed=lambda: bool(stream_status.refresh().get("live")),
    )
    encounter_daemon = EncounterDaemon(game, notifier.enqueue)
    token_store = TwitchTokenStore(settings.twitch_token_db) if settings.twitch_token_db else None
    subscription_status = TwitchSubscriptionStatus(
        settings.client_id,
        settings.owner_id,
        token_store,
        cache_seconds=settings.subscription_status_cache_seconds,
        stale_seconds=settings.subscription_status_stale_seconds,
    )
    portal_actions = PortalActionWorker(
        game,
        settings.portal_public_url,
        settings.portal_sync_key,
        poll_seconds=settings.portal_action_poll_seconds,
        timeout_seconds=settings.portal_action_timeout_seconds,
        verify_tls=settings.portal_action_verify_tls,
        notify_result=notifier.enqueue,
        wake_encounter=encounter_daemon.wake,
        subscription_lookup=subscription_status.refresh,
        stream_live_lookup=lambda: bool(stream_status.refresh().get("live")),
        owner_id=settings.owner_id,
    )

    portal_sync: PortalSyncWorker | None = None
    if settings.portal_sync_in_process and settings.portal_public_url and settings.portal_sync_key:
        repository = PortalRepository(settings.database_path, settings.data_dir)
        sync_client = PortalSyncClient(
            repository=repository,
            public_url=settings.portal_public_url,
            sync_key=settings.portal_sync_key,
            interval=settings.portal_sync_seconds,
            timeout=settings.portal_sync_timeout_seconds,
            verify_tls=settings.portal_sync_verify_tls,
            heartbeat_seconds=settings.portal_sync_heartbeat_seconds,
            overlay_state_path=settings.overlay_state_path,
            owner_twitch_id=settings.owner_id,
            fellowship_prepare=lambda: game.fellowship_system.airship_snapshot(),
        )
        portal_sync = PortalSyncWorker(sync_client)
    elif settings.cloud_runtime:
        LOGGER.warning("Cloud runtime has in-process Portal sync disabled or Portal credentials are missing.")

    notifier.start()
    encounter_daemon.start()
    portal_actions.start()
    if portal_sync:
        portal_sync.start()

    async def runner() -> None:
        async with CrystalGuildBot(
            settings, db, game, encounter_daemon, direct_sender, notifier, portal_actions, portal_sync, token_store, stream_status, subscription_status
        ) as bot:
            await bot.start()

    def _sigterm(_signum, _frame) -> None:
        raise KeyboardInterrupt

    previous_sigterm = None
    try:
        previous_sigterm = signal.signal(signal.SIGTERM, _sigterm)
    except (AttributeError, ValueError):
        pass

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down gracefully.")
    finally:
        # Stop mutation ingress before closing read-only sync and game timers.
        # This keeps Render SIGTERM shutdown ordered around the authoritative DB.
        portal_actions.stop()
        if portal_sync:
            portal_sync.stop()
        encounter_daemon.stop()
        notifier.stop()
        db.close()
        if previous_sigterm is not None:
            try:
                signal.signal(signal.SIGTERM, previous_sigterm)
            except (AttributeError, ValueError):
                pass


if __name__ == "__main__":
    main()

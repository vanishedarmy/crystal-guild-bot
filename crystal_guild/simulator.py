from __future__ import annotations

import argparse
import shlex

from .data import GameData
from .database import Database
from .engine import CrystalGuildEngine, GameResult
from .help_system import help_messages
from .chat_ux import format_command_error


def show(result: GameResult) -> None:
    for message in result.messages:
        print("BOT>", message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Crystal Guild chat simulator")
    parser.add_argument("--db", default="simulator.db")
    parser.add_argument("--data", default="data")
    args = parser.parse_args()
    data = GameData(args.data)
    data.validate_or_raise()
    db = Database(args.db)
    game = CrystalGuildEngine(db, data, venture_cooldown_seconds=0)
    uid, username = "local-van", "Van"
    print("Crystal Guild local simulator. Type !guild or quit.")
    while True:
        try:
            raw = input(f"{username}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        if raw.lower() in {"quit", "exit"}:
            break
        if not raw.startswith("!"):
            continue
        parts = shlex.split(raw[1:])
        cmd, rest = parts[0].lower(), parts[1:]
        try:
            if cmd in {"guild", "rpghelp", "rpg", "cghelp", "cgcommands"}:
                topic = " ".join(rest) if rest else None
                for message in help_messages(topic):
                    print("BOT>", message)
                if not topic:
                    show(game.next_step(uid))
            elif cmd == "switch":
                if not rest:
                    print("Current simulator hero:", username)
                else:
                    username = " ".join(rest)
                    uid = "local-" + "".join(ch.lower() for ch in username if ch.isalnum())
                    print(f"Switched to simulator chatter {username} ({uid})")
            elif cmd == "recruit": show(game.recruit(uid, username, username))
            elif cmd in {"hero", "me", "profile", "status"}: show(game.hero(uid))
            elif cmd == "next": show(game.next_step(uid))
            elif cmd == "job": show(game.choose_job(uid, " ".join(rest) if rest else None))
            elif cmd == "jobinfo": show(game.job_info(uid, " ".join(rest) if rest else None))
            elif cmd in {"abilities", "skills"}: show(game.abilities(uid, " ".join(rest) if rest else None))
            elif cmd == "mastery":
                slot = int(rest[-1]) if rest and rest[-1].isdigit() else None
                query = " ".join(rest[:-1] if slot else rest) or None
                show(game.mastery(uid, query, slot))
            elif cmd == "stance": show(game.set_stance(uid, rest[0] if rest else None))
            elif cmd in {"venture", "adv"}: show(game.venture(uid, bypass_cooldown=True))
            elif cmd in {"join", "fight", "rally"}: show(game.join_encounter(uid, bypass_cooldown=True))
            elif cmd in {"encounter", "battle", "enc"}: show(game.encounter_status())
            elif cmd == "resolveencounter": show(game.resolve_encounter())
            elif cmd == "clearencounter": show(game.abort_encounter())
            elif cmd == "readyall": show(game.ready_all_players())
            elif cmd == "resettimers": show(game.reset_all_player_timers())
            elif cmd in {"clearadventures", "clearventures"}: show(game.clear_all_adventures())
            elif cmd in {"rest", "camp"}: show(game.rest(uid))
            elif cmd == "use": show(game.use_item(uid, " ".join(rest)))
            elif cmd == "regions": show(game.regions(uid))
            elif cmd == "travel": show(game.travel(uid, " ".join(rest)))
            elif cmd == "monsters": show(game.monsters(" ".join(rest) if rest else None))
            elif cmd in {"monster", "mob", "enemy"}: show(game.monster_info(" ".join(rest)))
            elif cmd in {"inventory", "inv"}: show(game.inventory(uid, rest[0] if rest else None))
            elif cmd in {"gear", "equipment"}: show(game.gear(uid))
            elif cmd == "equip": show(game.equip(uid, " ".join(rest)))
            elif cmd == "shop": show(game.shop(uid))
            elif cmd == "item": show(game.inspect_item(uid, " ".join(rest)))
            elif cmd == "gil": show(game.gil(uid))
            elif cmd in {"fellowship", "guildinfo"}: show(game.fellowship(uid))
            elif cmd == "project": show(game.fellowship_project())
            elif cmd == "contribute": show(game.contribute_fellowship(uid, " ".join(rest)))
            elif cmd == "orders": show(game.fellowship_orders())
            elif cmd == "deeds": show(game.fellowship_deeds())
            elif cmd == "facilities": show(game.fellowship_facilities())
            elif cmd in {"airship", "guildairship"}: show(game.fellowship_airship())
            elif cmd in {"contributions", "guildrecord"}: show(game.fellowship_contributions(uid))
            elif cmd in {"rank", "guildrank"}: show(game.fellowship_rank(uid))
            elif cmd == "fellowshipproject": show(game.set_fellowship_project(" ".join(rest)))
            elif cmd == "airshipmission": show(game.set_airship_mission(" ".join(rest)))
            elif cmd == "buy":
                qty = int(rest[-1]) if rest and rest[-1].isdigit() else 1
                query = " ".join(rest[:-1] if rest and rest[-1].isdigit() else rest)
                show(game.buy(uid, query, qty))
            elif cmd == "sell":
                qty = int(rest[-1]) if rest and rest[-1].isdigit() else 1
                query = " ".join(rest[:-1] if rest and rest[-1].isdigit() else rest)
                show(game.sell(uid, query, qty))
            elif cmd in {"hunts", "huntboard", "marks"}: show(game.hunts(uid, rest[0] if rest else None))
            elif cmd in {"hunt", "mark"}: show(game.hunt(uid, " ".join(rest), bypass_cooldown=True))
            elif cmd == "quests": show(game.quests(uid))
            elif cmd == "quest": show(game.quest(uid, " ".join(rest)))
            elif cmd == "titles": show(game.titles(uid, " ".join(rest) if rest else None))
            elif cmd == "title": show(game.set_title(uid, " ".join(rest)))
            elif cmd in {"blacksmith", "smith", "forge"}: show(game.blacksmith(uid))
            elif cmd == "recipes": show(game.recipes(uid))
            elif cmd == "recipe": show(game.recipe_info(uid, " ".join(rest)))
            elif cmd == "craft":
                qty = int(rest[-1]) if rest and rest[-1].isdigit() else 1
                query = " ".join(rest[:-1] if rest and rest[-1].isdigit() else rest)
                show(game.craft(uid, query, qty))
            elif cmd in {"upgrade", "enhance"}: show(game.upgrade(uid, " ".join(rest)))
            elif cmd in {"sealshop", "quartermaster"}: show(game.sealshop(uid))
            elif cmd == "sealbuy":
                qty = int(rest[-1]) if rest and rest[-1].isdigit() else 1
                query = " ".join(rest[:-1] if rest and rest[-1].isdigit() else rest)
                show(game.sealbuy(uid, query, qty))
            elif cmd == "relics": show(game.relics(uid))
            elif cmd == "relic": show(game.relic(uid, " ".join(rest)))
            elif cmd == "awaken": show(game.awaken_relic(uid, " ".join(rest)))
            elif cmd == "bestiary": show(game.bestiary(uid))
            elif cmd in {"achievements", "ach"}: show(game.achievements(uid, " ".join(rest) if rest else None))
            elif cmd in {"achievement", "achinfo"}: show(game.achievement(uid, " ".join(rest)))
            elif cmd == "daily": show(game.daily(uid))
            elif cmd in {"leaderboard", "lb"}: show(game.leaderboard(rest[0] if rest else "level"))
            elif cmd == "bosses": show(game.bosses(rest[0] if rest else None))
            elif cmd == "bossinfo": show(game.boss_info(" ".join(rest)))
            elif cmd == "spawnboss": show(game.spawn_boss(" ".join(rest)))
            elif cmd == "raid": show(game.raid_join(uid))
            elif cmd == "boss": show(game.boss_status())
            elif cmd == "startraid": show(game.start_raid())
            elif cmd == "raidround": show(game.raid_round())
            elif cmd == "limit": show(game.limit_break(uid))
            elif cmd == "summon": show(game.summon_raid(uid, " ".join(rest) if rest else None))
            elif cmd == "revive": show(game.revive_raid(uid, " ".join(rest)))
            elif cmd == "raidstats": show(game.raid_stats())
            elif cmd == "resolveboss": show(game.resolve_boss())
            else: print("BOT>", format_command_error("CommandNotFound", cmd))
        except Exception as exc:
            print("ERROR>", type(exc).__name__, exc)
    db.close()


if __name__ == "__main__":
    main()

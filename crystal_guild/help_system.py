from __future__ import annotations

HELP_TOPICS = {
    "start": (
        "START HERE — !recruit creates your hero. Then choose a starter Job with !job warrior, monk, thief, blackmage, whitemage, or redmage.",
        "After choosing a Job, use !venture to adventure, !hero to inspect yourself, and !next whenever you are unsure what to do next.",
    ),
    "character": (
        "CHARACTER — !hero shows your live character summary. Aliases: !me, !profile, !status.",
        "Use !next for a contextual suggestion, !daily for randomized Daily Guild Provisions, !substatus to check subscriber perks, !titles to browse titles, and !title <name> to equip one.",
    ),
    "jobs": (
        "JOBS — !job lists Jobs or switches Job. !jobinfo <job> shows requirements; !abilities [job] shows passive milestones and Active Battle abilities.",
        "Master a Job at JLv.50, then use !mastery and !mastery <job> <1|2> to equip cross-Job Masteries. !stance still modifies battle math.",
    ),
    "adventure": (
        "VENTURES — Twitch Rally Venture is live-stream gameplay: !venture is available only while the channel is LIVE. Portal Solo Venture remains available off-stream as a private, player-paced three-stage run.",
        "ACTIVE BATTLE — ENCOUNTER Ventures open a rally and !join enters it. When combat begins, each living hero queues one action per round: !attack, !ability <name> [target], !defend, or !use <item> [target].",
        "!encounter shows a compact battle dashboard with enemy HP, party HP/MP/AP, statuses, queued actions and the timer. Ordinary enemy attacks target one hero; explicit party skills can hit multiple heroes. !battlelog shows recent resolved rounds without adding automatic chat spam.",
        "MIST SUPPORT — During a live Venture, World Event, or Raid battle, !healparty (100 Gil), !healparty 2 (250 Gil), !healparty 3 (500 Gil), or !healparty 4 (1,000 Gil) immediately heals the living party’s HP/MP. Once per participating hero per Venture, World Event, or Raid (each run has separate uses). No Gil spent if it cannot be used.",
    ),
    "recovery": (
        "RECOVERY — !rest starts a free camp recovery; use !rest again to check the timer. !use tent restores you immediately outside combat. While LIVE, use !use <item> | <username> to apply eligible field recovery to another adventurer.",
        "In Active Battle, healing/Ether/Phoenix Down plus Antidote, Echo Herbs, and Remedy can be queued. Poison, Silence, and Blind are real battle statuses; items are consumed only on successful resolution.",
    ),
    "inventory": (
        "INVENTORY — !inventory lists items. Filter with !inventory weapon, armor, accessory, consumable, or material. Alias: !inv.",
        "!gear shows equipped items and active stats. Alias: !equipment. Use !equip <item>, !item <name>, !shop, !buy, and !sell to manage gear and supplies.",
        "For quick chat-only gearing, !buyweapon, !buyarmor, or !buyaccessory picks the best current Emporium stock for your Job and level, buys it, and equips it. Not enough Gil? The command tells you the exact shortfall.",
    ),
    "shop": (
        "SHOP — !shop shows your personal Moogle Emporium rotation. Buy with !buy <slot or item> [qty]; consumables can be bought in quantity.",
        "Stock is Job- and level-aware and does not reroll every time you type !shop. Use !item <name> to inspect something you own or discover.",
        "No Portal required: !buyweapon | !buyarmor | !buyaccessory buys and equips suitable current stock automatically. Already owned? It equips for free. Insufficient Gil? No purchase is made.",
    ),
    "hunts": (
        "HUNTS — !hunts shows C/B/A/S progress and remains readable off-stream. !hunt <name> dispatches your hero while the channel is LIVE; the Adventurer Portal Hunt Board remains available off-stream.",
        "Hunts return automatically after their rank timer: C 15m, B 30m, A 2h, S/S+ 5h, SS 6h. No round commands are needed; your hero conserves supplies, uses learned abilities/Defend when useful, and only spends limited survival items when warranted. Rewards and first-clear prizes are committed when the Hunt resolves.",
    ),
    "mercs": (
        "MERC SERVICE — hire up to three unlocked Heroes from Adventurer Portal → Guild Services → Hero Merc Service: one Hunt contract, one Venture contract, and one Raid contract. Contracts use Hunt Seals earned through Hunts.",
        "Hunts already award Hunt Seals, which are used for Merc contracts as well as other Guild services. Alpha 2 fees: Aerith 5, Tifa 6, Zidane 5, Yuna 7, Balthier 9, Cloud 12 Hunt Seals.",
        "Each job type has its own slot; a Hero already contracted cannot take another job, unsupported Heroes are unavailable for that job type, and the Portal explains the exact unavailable reason. Hunt Seals are consumed only when a Merc contract is successfully created; cancelling before deployment frees that slot but does not refund those Hunt Seals. Once the assignment begins, the Hero is Deployed and stays unavailable until that Hunt, Venture, or Raid resolves.",
    ),
    "quests": (
        "QUESTS — !quests lists Job-unlock quests. Ready Job quests complete automatically and retroactively; !quest <name> inspects a specific quest.",
        "Use !jobinfo <job> to see what an advanced Job still needs. Many unlocks combine Character Level, Job Levels, Hunts and quests.",
    ),
    "crafting": (
        "CRAFTING — !blacksmith opens the forge overview. !recipes lists discoveries; !recipe <name> inspects one; !craft <recipe> [qty] crafts it.",
        "Use !upgrade <item> to forge equipment toward +5. Use !resynthesize <weapon or armor> to break down unwanted gear into crafting materials. Relic and Artifact gear is protected.",
    ),
    "relics": (
        "RELICS — !relics shows Classic lines; !relics ultimate shows Lv.90 Ultimate lines; !relic <name> shows stage requirements; !awaken <name> advances a completed stage.",
        "Relics are long-term Job-specific weapons and intentionally sit above ordinary shop gear. Expect Hunts, crafting, boss loot and poor life choices.",
    ),
    "raids": (
        "RAIDS — live-stream participation requires the channel to be LIVE: when a boss rally is active, !raid joins it and !boss shows status. Combat advances automatically after the rally closes.",
        "During live Raids, Ventures and World Events use !revive <hero> (Phoenix Down required). During Raids use !limit, !summon [name], and !raidstats. !healparty [1|2|3|4] pays 100/250/500/1,000 Gil to restore the living Raid party HP/MP, once per raider per Raid. Browse the catalog with !bosses and !bossinfo <name>.",
    ),
    "bestiary": (
        "BESTIARY — !bestiary shows discovery progress. !monsters [region] browses encounters and !monster <name> inspects a creature.",
        "Bestiary discoveries feed progression, achievements and unlock requirements. The Portal/Player Guide also show each discovered enemy's Active Battle temperament and named skill.",
    ),
    "achievements": (
        "ACHIEVEMENTS — !achievements shows Achievement Points and unlocks. Filter by category, such as !achievements combat, raids, jobs, hunts, or comedy.",
        "Use !achievement <name> for exact progress. !titles [category|rarity] browses earned titles; !title <name> equips one. Secret achievements stay hidden until unlocked.",
    ),
    "records": (
        "RECORDS — !records shows lifetime career, combat, economy and rivalry highlights. Aliases: !career and !stats.",
        "The Adventurer Portal Records tab has the full dossier: damage, healing, boss history, favorite Job, Nemesis and progression totals.",
    ),
    "fellowship": (
        "FELLOWSHIP — !fellowship shows the shared Guild LVL, your personal Guild Rank, active project, and weekly progress. !rank shows your personal standing and next promotion.",
        "Use !project for the current project, !contribute gil <amount> or !contribute <amount> <item> to donate, !orders for weekly objectives, !facilities for Guild upgrades, !workshop for refining services, !airship for Guild Airship status, !airshipregions for sky routes, !airshipexpedition <region> <depth> to launch a personal sky Expedition, !legacy for Guild accomplishments, and !contributions for your Fellowship record.",
    ),
    "chocobos": (
        "CHOCOBOS — the Fellowship first builds the Chocobo Stable. Then complete !chocoboquest, purchase a 500 Gil Registration Writ with !chocobowrit, and wait one hour for it to activate.",
        "Use !registerchocobo <name> to register your companion, !chocobo to view Bond Level/traits/readiness, and !chocoboname <name> to rename it. Chocobos gain Bond XP from Ventures, treasure, and Hunts; Chocobo traits currently add no combat bonus.",
    ),
    "portal": (
        "PLAYER PORTAL — the hosted Crystal Guild site shows live heroes, Jobs, equipment, inventory, Adventure Board, Chocobo Stable, Bestiary, Relics, achievements and records. Portal Solo Venture is a private three-stage Wayfarer run: 7-minute separate cooldown, 80% ENCOUNTER / 20% TREASURE per stage, roughly Lv.-2 to Lv.+5 enemies, player-paced Attack/Ability/Item/Defend combat, and Return-or-Press-On risk/reward.",
        "Use the Player Guide link on the Adventurer Portal for the full command and progression reference. The website receives sanitized game-only data.",
    ),
}

ALIASES = {
    "recruit": "start", "begin": "start", "new": "start",
    "hero": "character", "profile": "character", "status": "character", "me": "character", "daily": "character", "substatus": "character",
    "job": "jobs", "jobinfo": "jobs", "abilities": "jobs", "mastery": "jobs", "stance": "jobs",
    "venture": "adventure", "join": "adventure", "encounter": "adventure", "battlelog": "adventure", "roundlog": "adventure", "combatlog": "adventure", "attack": "adventure", "ability": "adventure", "defend": "adventure", "guard": "adventure", "travel": "adventure", "regions": "adventure",
    "rest": "recovery", "camp": "recovery", "use": "recovery", "healparty": "adventure",
    "inv": "inventory", "gear": "inventory", "equipment": "inventory", "equip": "inventory", "item": "inventory",
    "buy": "shop", "buyweapon": "shop", "buyarmor": "shop", "buyaccessory": "shop", "sell": "shop",
    "hunt": "hunts", "huntboard": "hunts", "marks": "hunts", "sealshop": "hunts", "sealbuy": "hunts",
    "merc": "mercs", "mercs": "mercs", "mercenary": "mercs", "mercenaries": "mercs",
    "quest": "quests",
    "blacksmith": "crafting", "forge": "crafting", "recipes": "crafting", "recipe": "crafting", "craft": "crafting", "upgrade": "crafting", "resynthesize": "crafting", "desynth": "crafting", "dismantle": "crafting",
    "relic": "relics", "awaken": "relics",
    "raid": "raids", "boss": "raids", "bosses": "raids", "bossinfo": "raids", "limit": "raids", "summon": "raids", "revive": "raids",
    "monster": "bestiary", "monsters": "bestiary",
    "achievement": "achievements", "achievements": "achievements", "ach": "achievements", "titles": "achievements", "title": "achievements",
    "records": "records", "career": "records", "stats": "records",
    "fellowship": "fellowship", "guildinfo": "fellowship", "project": "fellowship", "contribute": "fellowship", "orders": "fellowship", "deeds": "fellowship", "facilities": "fellowship", "workshop": "fellowship", "guildworkshop": "fellowship", "refine": "fellowship", "airship": "fellowship", "guildairship": "fellowship", "legacy": "fellowship", "guildlegacy": "fellowship", "contributions": "fellowship", "guildrecord": "fellowship", "rank": "fellowship", "guildrank": "fellowship",
    "chocobo": "chocobos", "stable": "chocobos", "chocoboquest": "chocobos", "chocobowrit": "chocobos", "writ": "chocobos", "registerchocobo": "chocobos", "chocoboname": "chocobos",
    "web": "portal", "website": "portal", "guide": "portal",
}


def help_messages(topic: str | None = None) -> tuple[str, ...]:
    if topic:
        key = topic.strip().lower().lstrip("!")
        key = ALIASES.get(key, key)
        if key in HELP_TOPICS:
            return HELP_TOPICS[key]
        return (
            f"No help topic named '{topic}'. Try !guild start, jobs, adventure, recovery, inventory, shop, hunts, mercs, crafting, relics, raids, fellowship, chocobos, achievements, records, or portal.",
        )
    return (
        "MOGNET COMMAND MAP — !guild start | character | jobs | adventure | recovery | inventory | shop | hunts | mercs | quests | crafting | relics | raids | fellowship | chocobos",
        "More: !guild bestiary | achievements | records | portal — or use !next for exactly what your hero should do now. Aliases: !cghelp jobs or !cgcommands jobs.",
    )

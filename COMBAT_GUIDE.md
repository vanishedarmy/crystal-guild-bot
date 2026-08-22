# Crystal Guild v1.1.14 — Active Battle & Recovery Guide

## Venture events

`!venture` now rolls one of two adventure outcomes:

- **70% ENCOUNTER** — opens the normal joinable rally. The initiating hero joins automatically and the rally stays open for `ENCOUNTER_JOIN_SECONDS` (45 seconds by default). The monster roll is filtered so it can never be more than **10 levels above the initiating hero**. Other eligible heroes join with `!join` or `!venture`.
- **30% TREASURE CHEST** — immediately awards one level-appropriate item and ends the Venture without starting combat. Chest items are selected from roughly **5 levels below through 2 levels above** the venturing hero. Consumables, weapons, armor and accessories are eligible; Relic-progression weapons and explicitly unsellable progression pieces are excluded.

Treasure Ventures consume the normal Venture cooldown and increment the player's Venture total, but they do **not** create a party encounter or rally.

When the rally timer ends, the **combat scheduler starts Active Battle automatically** rather than waiting for the next chat command.

```text
Rally → Round action window → Resolve → Next round / Finish
```

The default action window is `ENCOUNTER_ROUND_SECONDS=20`. Every round resolves on its original scheduled deadline—even if all living heroes submit early. If a player submits nothing, their action safely defaults to Attack at that same deadline. Late actions are rejected instead of becoming the event that resolves the round.

Useful commands:

```text
!venture
!join
!encounter
!attack
!ability <name> [target]
!defend
!use <item> [target]
```

`!skill` / `!cast` alias `!ability`; `!guard` aliases `!defend`. You may change your queued action before the round resolves.

## Battle MP & AP

Active abilities use **persistent combat resources** based on the Job and technique. Magic-focused actions spend **MP (Magic Points)**; physical/melee techniques spend **AP (Action Points)**. Paladin and Bard are dual-resource Jobs because their kits mix martial and magical/support actions. Normal `!attack` remains resource-free.

MP/AP now persist between encounters. Starting a new battle uses the amount the hero actually has remaining instead of silently refilling the pool. `!defend` restores **6% of maximum MP** and **8% of maximum AP** for pools the current Job uses. Camp, Tents, Ether-family items, Stamina Draughts/Tonics, and Elixirs provide recovery outside combat.

## Active Job abilities

Every Job ships with three Active Battle abilities at JLv.1, JLv.15, and JLv.30. Use:

```text
!abilities
!abilities white mage
```

to see passive Job milestones plus current active abilities. Active ability content lives in `data/active_abilities.json`; passive Job milestone effects remain in `data/jobs.json`.

Abilities can deal physical/magical/hybrid damage, heal, restore MP/AP, revive, cleanse, drain, or apply timed status effects. Each ability declares its resource and cost in `data/active_abilities.json`.

## Status effects

The shared combat helper layer includes timed effects such as:

- Protect — incoming damage reduction.
- Taunt — increases enemy target pressure.
- Evasion — improved dodge chance.
- Power Up / Focus — offensive boosts.
- Haste — improves action priority.
- Regen — healing over time.
- Vulnerable — enemy takes increased damage.
- Weaken — enemy deals reduced damage.
- Slow — reduces enemy pressure.
- Stun — can cancel the enemy turn.
- Poison — end-of-round damage.
- Silence — blocks **MP-based magical abilities** while leaving AP techniques, Attack, Defend, and items available.
- Blind — can make physical attacks and physical abilities miss.

Status duration/formatting/cleanse behavior is centralized in `crystal_guild/active_battle.py` so new effects should not open-code duration handling in multiple places.

## Items during Active Battle

Supported battle items include healing potions, Ether, Phoenix Down, cleanse items, and AP recovery supplies. Ether-family items restore MP; Stamina Draught/Warrior’s Tonic/Hero’s Brew restore AP. These recovery items can also be used outside battle. The item is consumed only when its effect successfully resolves.

Outside battle, field recovery still supports items such as Potions, Phoenix Down, and Tent according to their normal rules.

## Persistent HP / KO

HP persists between encounters, Hunts and raids. Surviving a battle at 421/1800 HP means the next eligible fight starts at 421/1800 HP. Active Battle saves HP after each resolved round.

A KO hero cannot Venture, Hunt, or join another combat until recovered. During an Active Battle, allies can use Raise-capable abilities or Phoenix Down on a KO party member.

## Stances

Stance remains part of Active Battle math:

- Balanced — neutral.
- Aggressive — stronger physical pressure, lower defense.
- Defensive — lower offense, stronger survival.
- Magical — stronger magic.
- Cautious — conservative offense, improved defense.

```text
!stance
!stance aggressive
```

## Party roles

Enemy target pressure still derives partly from the active Job. Under soft targeting, the monster gets one ordinary response per round and a basic/single-target action chooses one living hero, with tank Jobs and Taunt carrying extra target weight. Only enemy abilities explicitly marked as party-targeted may hit more than one hero. Healing/support behavior is no longer a fully automatic party turn in ENCOUNTER Ventures; players actively choose those abilities.

Broadly:

- Warrior / Paladin / Dark Knight: tank pressure and mitigation.
- White Mage / Sage: strong healing/recovery tools.
- Red Mage: hybrid damage/healing.
- Bard / Time Mage: support/control.
- Other Jobs: primarily offensive or specialist contribution.

## Camp

`!rest` or `!camp` begins a free camp rest. The default duration is 1800 seconds (30 minutes). A resting hero cannot join combat. When the timer completes, the hero returns at full calculated maximum HP for the current Job.

## Enemy combat

Enemies in Active Battle have a **Temperament** and, for most monsters, a named **Active Skill**. Temperament affects pressure/skill behavior through the shared enemy-combat data layer. An ordinary enemy response targets one hero; named skills may be single-target or explicitly party-targeted. Hunts reuse the same behavior instead of maintaining a separate monster-AI path.

New harmful statuses include **Poison** (end-of-round damage), **Silence** (blocks MP-based magical abilities), and **Blind** (can make physical attacks/abilities miss). Antidote removes Poison, Echo Herbs remove Silence, and Remedy remains the broad harmful-status cleanser. Enemy Protect, Regen, Haste, Slow, drain, recoil, and utility actions use the same round/status framework as the rest of Active Battle.

## Active Hunts

`!hunt <mark>` now starts a **solo Active Battle** immediately. Hunts do not open a public rally: the accepting hero enters Round 1 and uses the same Attack / Ability / Defend / Item action vocabulary as Venture combat.

```text
!hunts [rank]
!hunt <mark>
!encounter
!attack
!ability <name>
!defend
!use <item>
```

The combat scheduler owns Hunt round deadlines too. Acceptance creates the first timer and wakes the daemon; typing another command never becomes the event that advances an overdue round. Missing actions default to Attack at the scheduled deadline.

C/B/A/S marks keep their existing rewards and first-clear unlocks. Rank scaling is deliberately conservative because Hunt monsters already have bespoke stats: higher ranks receive modest HP/enemy-pressure increases plus a larger round safety window. Hunt-focused Job/mastery damage bonuses still apply. Rewards and Hunt-clear records are committed **only on victory**.

The former immediate solo Hunt resolver has been removed from live code. This keeps one authoritative field-combat engine for both Ventures and Hunts.

## Community raids — established raid engine retained

The broadcaster opens a raid with:

```text
!spawnboss <boss>
```

The raid rally remains open for `RAID_JOIN_SECONDS` (60 seconds by default). Viewers join with `!raid`. The existing raid daemon continues to advance autonomous timed rounds every `RAID_ROUND_SECONDS` (15 seconds by default), including phases, enrage, Limit Breaks, Summons, revival, and contribution tracking.

```text
!limit
!summon ifrit
!revive <hero>
!raidstats
```

Raid rewards retain the role-aware contribution score using damage, healing, and mitigation.

## Reliability architecture

Active field battles (Ventures and Hunts) retain the same production separation:

```text
Encounter daemon
    -> owns rally/round deadlines
    -> calls engine advancement
    -> queues GameResult for delivery
Game engine/database
    -> owns validation, math, item/MP/AP spending, HP/rewards
Notification worker
    -> sends/packs Twitch output
Twitch commands
    -> submit intent only; never resolve combat math
```

A Twitch delivery failure therefore cannot hold an encounter open. Missing chat actions also cannot stall a round.

## Broadcaster diagnostics

```text
!health
!cgversion
!encounterdebug
!directtest
!readyall
!resettimers
!resolveencounter
!clearencounter
!spawnboss <boss name>
!resolveboss
```

`!readyall` restores every player to READY with full HP and applicable MP/AP, but intentionally refuses to run during active combat. `!resettimers` clears persistent player cooldowns, camp timers, and personal shop refresh timers; it does not force active encounter/raid countdowns to advance.

Emergency resolver/clear commands remain available for recovery, but normal Active Battles should need no owner intervention.

For code changes, see `COMBAT_DEVELOPER_GUIDE.md`.


## Twitch battle presentation

Automatic Active Battle chat is intentionally compact:

- action commands acknowledge with `QUEUED R#`;
- a normal timed round emits one bounded recap plus one `NEXT R#` line;
- `!encounter` shows the live read-only dashboard;
- `!battlelog`, `!roundlog`, or `!combatlog` shows recent resolved rounds on demand.

The presentation layer does not advance timers or decide combat. The scheduler still owns deadlines, and resources are still spent only by authoritative resolution.

## Combat balance notes

- MP is persistent and bounded to **15–75 MP** for Jobs that use MP; typical starter Jobs begin around **16–17 MP**.
- AP is persistent and bounded to **15–70 AP** for Jobs that use AP; typical starter Jobs begin around **16 AP**.
- Defend restores **6% MP** and **8% AP** of the relevant maximum pool(s) while retaining its defensive role.
- Aetherflow restores **22%** of maximum battle MP.
- Hero Stun loses the current action.
- Hero Weaken/Slow reduce outgoing pressure; Slow also worsens action priority.
- Hero Vulnerable increases incoming enemy damage.
- Monster Evasion can avoid physical player attacks/abilities; monster Focus
  increases enemy pressure.
- After a successful player Stun, the enemy resists Stun for the following round.
- Hunt marks gain gradual rank-based debuff resistance; they are not status-immune.

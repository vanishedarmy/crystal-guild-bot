# Crystal Guild v1.1.15 — Wayfarer Hotfix 3

Hotfix 3 brings earned Title selection into the authenticated Adventurer Portal.

## Title Collection controls

Open **Achievements & Titles → Title Collection** on your own signed-in profile. Every earned Title now has an **Equip** action. The active Title is highlighted and marked **Equipped Now**. Locked Titles remain visible according to the existing filters but cannot be selected.

The Portal still supports the existing Twitch `!title <name>` command; both surfaces now update the same authoritative `players.title` value.

The Bot re-checks the request against `player_titles`, so a browser cannot equip a Title the character has not earned. Public/read-only profiles never expose Title mutation controls.

## Compatibility

- Bot/Web runtime: `1.1.15-wayfarer-h3`
- Frontend asset revision: `1.1.15-wayfarer1h3`
- Local DB schema: **5** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Hosted sync compatibility: `1.1.15-wayfarer`
- Portal Action protocol: **14** (from 13)
- Twitch prefix: `!`

No database migration, player reset, new Render secret, or new Twitch OAuth scope is required. Because the action protocol changes, deploy the matching Hotfix 3 Bot and Web together.


---

# Crystal Guild v1.1.15 — Wayfarer

Wayfarer turns the Portal-only **Solo Venture** into a compact, interactive RPG run while preserving Rally Venture as Crystal Guild's higher-risk live-stream cooperative mode. It also reorganizes the Adventurer Portal so the most frequently used character actions appear first.

## Interactive Solo Venture

- Solo Venture remains Portal-only and now resolves **one player-selected combat round at a time**.
- Battle controls are **Attack**, **Ability**, **Use Item**, and **Defend**.
- The current enemy intent is shown before the player's choice so defensive and resource decisions can react to incoming attacks or specials.
- Ability choices show learned/unlocked state, MP/AP cost, target, and description.
- Battle inventory shows eligible owned consumables and quantities.
- HP, MP, AP, statuses, and consumed items persist through the run.
- Solo combat is player-paced: there is **no round timer** and no autonomous scheduler advance while waiting for the next Portal action.

## Three-stage Wayfarer run

Every stage rolls **60% Encounter / 40% Treasure**. A run ends after at most three stages.

- **Stage I:** normal Solo rewards.
- **Stage II:** +15% XP / JP / Gil from encounter rewards.
- **Stage III:** +30% XP / JP / Gil from encounter rewards.
- Deeper Treasure events keep the same 40% event chance but bias the chest toward better rarity.
- Solo enemies are selected roughly from **two levels below through three levels above** the hero, with deeper stages weighting the stronger end of that range more heavily.

After Stage I or II is cleared, the player chooses:

- **Return to Guild — Bank Spoils:** safely ends the run and awards unbanked Gil/items.
- **Press On:** carries current HP/MP/AP and consumed inventory forward into the next stage for better reward potential.

XP and JP from defeated enemies are secured immediately. Encounter Gil and ordinary item drops remain **Venture Spoils** until banked. Rare pity drops and recipe discoveries remain secured progression rewards.

If the hero is defeated, secured XP/JP and secured progression loot remain, **50% of unbanked Gil is recovered**, and loose item spoils are lost. Retreating from combat preserves secured progression but abandons all unbanked Venture Spoils.

## Independent persistent Solo state

Interactive Solo Ventures no longer borrow the Guild-wide live encounter slot as their authoritative state. Each active run is persisted per player in the local database. This means a player may leave the Portal and return later without a timer advancing their fight, and an unattended Solo Venture does not block unrelated Rally Ventures or Hunts for the Guild.

While a Solo Venture is active, build/recovery/economy mutations that could bypass the run's resource pressure—such as changing Jobs, re-equipping, resting, field-item use, shopping, crafting, or forging—are blocked until the player Returns or Retreats. Battle items remain usable through the Solo Venture combat interface.

## Portal navigation order

Profile tabs now prioritize the normal player journey:

1. Overview
2. Adventure Board
3. Jobs
4. Equipment & Inventory
5. Moogle Emporium
6. Blacksmith
7. Chocobo Stable
8. Fellowship
9. Bestiary
10. Relics
11. Achievements & Titles
12. Records
13. Trophy Hall

## Compatibility and migration

- Bot/Web runtime: `1.1.15-wayfarer`
- Frontend asset revision: `1.1.15-wayfarer1`
- Local DB schema: **5** (from 4)
- Hosted sync schema: **1**
- Portal Action protocol: **13** (from 12)
- Twitch prefix: `!`

Schema 5 adds only the persistent per-player Solo Venture state table. When an existing schema-4 Guild database is opened, Crystal Guild automatically creates and verifies `backups/pre_schema_5_<timestamp>.db` before applying the additive migration. Existing progression is preserved.

No player reset, new Render secret, hosted sync schema change, or new Twitch OAuth scope is required. The existing `channel:read:subscriptions` broadcaster authorization remains required only for the subscriber perks introduced previously.

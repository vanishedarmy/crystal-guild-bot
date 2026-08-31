# Crystal Guild v1.6.0 — Gold Saucer Alpha 1 Release Audit

## Frozen Alpha 1 scope
- Dedicated Gold Saucer Portal hub.
- Separate non-purchasable **Saucer Point (SP)** economy.
- One-time **500 SP** welcome purse plus **50 SP daily floor allowance** beginning after the welcome day.
- Persistent daily Mini Cactpot.
- Replay-safe Crystal Slots.
- Cosmetic-only Prize Counter with three Gold Saucer Titles.
- Personal Gold Saucer records and recent transaction history.
- Streamer SP grant and attraction-reset controls.
- Monster Toss, Chocobo Racing, and Triple Triad remain Coming Soon.
- Existing v1.5.1 Relic Arsenal, 54-asset Relic Artwork Refresh, v1.5.0 Trails & Raids Hotfix 4 scenic behavior, Dungeons, Expeditions, and all existing progression are carried forward.

## Frozen contract
Runtime `1.6.0-gold-saucer-a1`; local DB schema **11**; hosted sync **1**; Portal Action protocol **26**; Twitch prefix `!`.

Schema 11 is additive and verified against a genuine schema-10 database. No player reset, OAuth/environment change, new required variable, or hosted sync migration.

## Release gate
**607/607 Bot**, **472/472 frontend**, **49/49 hosted**, **113/113 Python parse**, **216/216 frontend parser**, **174/174 Node syntax**, CSS parse clean, **0 PNG / 665 WebP decode**, **54/54 Relic v2 assets**.

The local Vite production build was attempted but cannot run in this source-only container because the pinned Vite executable is not installed; no Vite-build pass is claimed.

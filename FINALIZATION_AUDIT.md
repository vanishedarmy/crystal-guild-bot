# Crystal Guild v1.6.0 — Gold Saucer Alpha 2 Release Audit

## Frozen Alpha 2 scope
- Opens **Monster Toss** as the third playable Gold Saucer attraction.
- Five persistent throws per game with player-selected target and throw style.
- **20 SP** entry, **3 games per UTC day**, bounded score-to-SP settlement.
- Monster Toss records are derived from the existing Gold Saucer ledger.
- Adds cosmetic-only **Toss Tactician** and **Pot Shot Pro** Prize Counter Titles.
- Carries Alpha 1 H1 Gold Saucer scenic artwork and Alpha 1 H2 Cactpot/Slots UX and records forward unchanged.

## Frozen contract
Runtime `1.6.0-gold-saucer-a2`; local DB schema **12**; hosted sync **1**; Portal Action protocol **27**; Twitch prefix `!`.

Schema 12 adds only persistent active Monster Toss state. No player reset, OAuth/environment change, new required variable, normal Gil economy change, combat progression change, Mini Cactpot payout change, or Crystal Slots payout change.

## Release gate
**615/615 Bot**, **481/481 frontend**, **51/51 hosted**, **116/116 Python parse**, **217/217 frontend parser**, **177/177 Node syntax**, **8/8 CSS parse**, **0 PNG / 675 WebP decode**, **0 GameData errors**.

A genuine Alpha 1 H2 schema-11 database upgraded to schema 12 with a verified pre-migration backup and preserved the validation hero at **Lv.17 / 4,321 Gil**.

The local Vite production build was attempted but cannot execute because this source-only environment does not contain the pinned local Vite executable; no Vite-build pass is claimed.

## Packaging
- Clean Bot tree: **169 files**; H2 → Alpha 2 delta: **48 changed/new, 0 deleted**.
- Clean Web tree: **951 files**; H2 → Alpha 2 delta: **60 changed/new, 0 deleted**.
- Individual Bot/Web patches are verified by file hash to reconstruct the final clean trees exactly.
- Full Bot, full Web, Complete, Bot patch, Web patch, and paired updater are ZIP CRC/integrity checked.
- Runtime/private-state hygiene exclusions cover databases, WAL/SHM files, token/environment secrets, caches, logs, and runtime overlay/checkpoint files.

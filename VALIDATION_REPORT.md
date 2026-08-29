# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 2 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **504 / 504 PASS**.
- Frontend Node regression suite: **376 / 376 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

The Bot suite includes intentional simulated acknowledgement loss, temporary Twitch/live-status failures, corrupt checkpoint recovery, restart recovery, database recovery drills, and synthetic stress scenarios. Their warning/error log lines are expected test fixtures.

## Alpha 2 Dungeon coverage
- Local schema remains **10**; Alpha 1 persistent Dungeon tables and migration path remain covered.
- Portal Action protocol advances **23 → 24** for typed `DUNGEON_CHOICE` mutations.
- The Dungeon Board exposes **2 Dungeons**, both with **8 chambers** and one Crossroads route decision.
- **The Forgotten Ossuary** retains its Lv.10 + 25% Emerald Wilds unlock and gains the Forked Crypt Crossroads.
- **The Emberglass Foundry** unlocks at Lv.18 + 35% Ashen Highlands and carries its own combat, treasure, Crossroads, hazard, miniboss, sanctuary, boss, completion bonus, and scene art.
- Crossroads effects cover HP damage/healing, MP/AP recovery, Cache Gil/material rewards, and named discoveries.
- Route choices are replay-safe and remain bound to the exact run/chamber shown in the browser.
- Alpha 1 HP/MP/AP persistence, item consumption, Bestiary credit, Cache settlement, retreat/defeat rules, restart recovery, stale-tab protection, and `!clearadventures` continuity remain green.
- Adventure-state serialization remains below the existing **16 KiB** guardrail with the expanded Dungeon catalog.

## Shared collapse-pointer correction
- Closed controls render the **right-pointing hand**; open controls render the **down-pointing hand**.
- Portal collapse controls use one canonical **1.35rem** pointer box.
- Player Guide disclosure hands use the matching **22px** rendered size.
- The What’s New control is regression-covered by the same shared sizing rule rather than inheriting a larger local icon size.
- Obsolete pre-Alpha-2 pointer files are removed from the final Web tree; the cache-busted `-a2.webp` pair is authoritative.

## Source / asset validation
- Python compilation sweep: **93 / 93 PASS** across Bot + Web Python source/tests/tools.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **190 / 190 PASS**.
- Plain JS/MJS `node --check`: **150 / 150 PASS**.
- Game data validation: **0 errors**; **2 Dungeons** loaded.
- New/current Dungeon scene routes and collapse-pointer assets resolve in the full frontend regression suite.
- Public artwork remains **0 PNG / 575 WebP**.

## Continuity
- v1.3.1 Asset Optimization and UI4 behavior remain covered.
- v1.3 Guild Expansion shared-state, Fellowship, Airship, Workshop, Weekly Order, Legacy, and recovery protections remain covered by the full suites.
- v1.2 Expedition behavior remains covered.
- Public Previous major updates remains stable-release-only beneath the current Alpha 2 What’s New card.
- Existing non-Dungeon gameplay/economy balance is unchanged.
- Bot/Web/frontend runtime: `1.4.0-dungeons-a2`.
- Local DB schema: **10** unchanged.
- Hosted sync schema: **1** unchanged.
- Portal Action protocol: **24**.
- Twitch prefix: `!`.
- Database migration from Alpha 1: **none**.
- Player reset: **none**.
- OAuth change: **none**.
- New environment variables: **none**.

## Packaging verification
- Alpha 1 → Alpha 2 Bot patch: **25 changed/new files, 0 deletions**; reconstructs **148 / 148** shipping Bot files exactly.
- Alpha 1 → Alpha 2 Web patch: **58 changed/new files, 2 obsolete pointer deletions**; reconstructs **817 / 817** shipping Web files exactly.
- Final ZIP CRC/integrity, runtime/private-artifact hygiene, exact reconstruction, and SHA-256 verification: **PASS**.

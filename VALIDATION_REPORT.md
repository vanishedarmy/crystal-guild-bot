# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 1 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **498 / 498 PASS**.
- Frontend Node regression suite: **372 / 372 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

The Bot suite includes intentional simulated acknowledgement loss, temporary Twitch/live-status failures, corrupt checkpoint recovery, restart recovery, database recovery drills, and synthetic stress scenarios. Their warning/error log lines are expected test fixtures and are not Alpha 1 failures.

## Dungeon Alpha 1 coverage
- Schema **9 → 10** migration creates a verified pre-schema-10 backup and preserves existing player/Guild progression.
- Active Dungeon state persists in the database and survives engine/database restart.
- The Forgotten Ossuary unlock requires character Lv. 10 plus 25% Emerald Wilds Expedition exploration.
- Seven-chamber progression covers entrance, combat, treasure, hazard, miniboss, sanctuary, and boss room types.
- HP, MP/AP, consumed items, combat state, and Dungeon Cache persist across chambers.
- Full clear banks 100% of the cache plus completion bonus; retreat banks 50%; defeat recovers 25%.
- Dungeon victories feed existing Bestiary/monster-defeat records.
- Active-run and permanent Dungeon-progress records are separate; `!clearadventures` clears the active run without erasing completed Dungeon history.
- Portal Dungeon actions are bound to the exact run ID and chamber ID visible in the browser. Stale tabs fail closed after another tab advances/replaces the Dungeon state.
- Dungeon actions remain covered by the existing Portal replay/idempotency path.
- Existing incompatible Adventure/Portal mutations are blocked while a Dungeon run is active.

## Source and asset validation
- Python source compilation: **92 / 92 PASS** across Alpha 1 Bot + Web source trees.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **189 / 189 PASS**.
- Plain JS/MJS `node --check`: **149 / 149 PASS**.
- Explicit literal asset-route audit: **148 routes checked / 0 missing**.
- Game data validation: **0 errors**; **1 Dungeon** loaded.
- Public artwork remains **0 PNG / 575 WebP**.

## Continuity
- v1.3.1 Asset Optimization and UI4 behavior remain regression-covered.
- v1.3 Guild Expansion shared-state, Fellowship, Airship, Workshop, Weekly Order, Legacy, and recovery protections remain covered by the full suites.
- v1.2 Expedition behavior remains covered by the full suites.
- Public Previous major updates remains stable-release-only.
- Existing non-Dungeon gameplay/economy balance is unchanged.
- Bot/Web/frontend runtime: `1.4.0-dungeons-a1`.
- Local DB schema: **10**.
- Hosted sync schema: **1** unchanged.
- Portal Action protocol: **23**.
- Twitch prefix: `!`.
- Player reset: **none**.
- OAuth change: **none**.
- New environment variables: **none**.

## Packaging verification
- v1.3.1 Bot → Alpha 1 Bot patch: **36 changed/new files, 0 deletions**; reconstructs **147 / 147** shipping Bot files exactly.
- v1.3.1 UI4 Web → Alpha 1 Web patch: **57 changed/new files, 0 deletions**; reconstructs **816 / 816** shipping Web files exactly.
- Final archive CRC/integrity, runtime/private-artifact hygiene, and SHA-256 verification: **PASS**.

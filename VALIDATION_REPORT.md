# Crystal Guild v1.4.0 — Dungeons & Delves Beta 1 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **522 / 522 PASS**.
- Frontend Node regression suite: **386 / 386 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

The Bot suite includes intentional simulated acknowledgement loss, Twitch/live-status outages, corrupt checkpoint recovery, and restart/recovery fixtures; their warning/error log lines are expected.

## Beta 1 Dungeon hardening coverage
- GameData validation: **4 Dungeons / 0 errors**; feature catalog remains frozen at Alpha 4 content.
- Portal Dungeon mutations are bound to exact **run ID + chamber ID + persisted revision**.
- A stale same-room tab cannot spend a second combat turn after another tab advances the room state.
- Stale revisions also fail closed for Continue, Crossroads Choice, and Retreat.
- Same action-ID replay is resolved from the existing idempotency receipt before the stale revision check and cannot advance twice.
- Dungeon revision survives engine restart/reconnect.
- Round-limit UI presents current round and room limit for pressure encounters.
- Adventure Board with all four Dungeons unlocked serializes to **15,368 bytes**, leaving **1,016 bytes** below the 16 KiB guardrail.

## Source / asset validation
- Python compile sweep: **95 / 95 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **194 / 194 PASS**.
- Plain JS/MJS `node --check`: **154 / 154 PASS**.
- Active literal image-route audit: **149 routes / 0 missing**.
- Public artwork: **0 PNG / 576 WebP**.

## Compatibility
- Bot/Web/frontend runtime: `1.4.0-dungeons-b1`.
- Local DB schema: **10** unchanged from Alpha 4.
- Hosted sync schema: **1** unchanged.
- Portal Action protocol: **25** (24 → 25).
- Twitch prefix: `!`.
- Database migration: **none from Alpha 4**.
- Player reset: **none**.
- OAuth/environment changes: **none**.
- Non-Dungeon gameplay/economy rebalance: **none**.

## Patch/package verification
- Alpha 4 → Beta 1 Bot patch: **26 changed/new files, 0 deletions**; reconstructs **152 / 152** shipping Bot files exactly.
- Alpha 4 → Beta 1 Web patch: **54 changed/new files, 0 deletions**; reconstructs **822 / 822** shipping Web files exactly.
- Individual patch helpers and paired updater reconstruct the exact Beta 1 trees.
- Six release ZIPs: CRC/integrity **PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **PASS**.


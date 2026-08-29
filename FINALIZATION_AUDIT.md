# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 2 Release Audit

## Scope
Dungeon content/choice expansion on the validated Alpha 1 foundation.

## Current-package identity
- Bot runtime: `1.4.0-dungeons-a2`
- Hosted Web/runtime: `1.4.0-dungeons-a2`
- Frontend asset revision: `1.4.0-dungeons-a2`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **24**
- Twitch prefix: `!`

## Audit targets
- Add a second persistent Dungeon without requiring another schema migration.
- Add replay-safe, run/chamber-bound Crossroads actions and preserve stale-tab failure behavior.
- Preserve Alpha 1 HP/MP/AP, Cache, restart persistence, Bestiary integration, retreat/defeat/clear settlement, and Dungeon records.
- Keep Portal Adventure state beneath the existing bounded-payload regression ceiling.
- Normalize collapse-pointer rendered size while keeping right/closed and down/open state behavior.
- Preserve v1.3 Guild Expansion, v1.2 Expeditions, optimized WebP assets, and UI4 behavior.
- No player reset, OAuth change, or new environment variable.

## Result
**PASS** once full automated validation, exact patch reconstruction, archive integrity/hygiene, and SHA-256 verification complete.

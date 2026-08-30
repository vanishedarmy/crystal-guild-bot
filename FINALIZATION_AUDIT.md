# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 3 Release Audit

## Release identity
- Bot runtime: `1.4.0-dungeons-a3`
- Hosted Web runtime: `1.4.0-dungeons-a3`
- Frontend asset revision: `1.4.0-dungeons-a3`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **24**
- Twitch prefix: `!`

## Scope lock
Alpha 3 is the Dungeon depth/reward pass: Whiteglass Bastion, forward route effects, first-clear bonuses, Dungeon Board/Guide clarity, payload headroom, and packaging hygiene. No non-Dungeon balance pass is included.

## Continuity
- Alpha 2 Dungeon run JSON remains readable; missing `modifiers` defaults safely.
- Existing Dungeon progress rows determine first-clear eligibility without schema changes.
- Portal Dungeon mutations remain run/chamber bound and replay-safe.
- Existing Guild, Expedition, Hunt, inventory, recovery, Airship, and Fellowship persistence contracts are unchanged.
- Shipping archives contain no `.env`, database, token JSON, cache, log, or other runtime-private state.

# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 4 Release Audit

## Release identity
- Bot runtime: `1.4.0-dungeons-a4`
- Hosted Web runtime: `1.4.0-dungeons-a4`
- Frontend asset revision: `1.4.0-dungeons-a4`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **24**
- Twitch prefix: `!`

## Scope lock
Alpha 4 is the Dungeon encounter/content expansion pass: Riftglass Observatory, weighted Event chambers, shared room-effect handling, encounter-specific pressure/mechanics, four-Dungeon payload headroom, and matching Board/Guide presentation. No non-Dungeon balance pass is included.

## Continuity
- Alpha 3 Dungeon run JSON remains readable; new Event/mechanic fields are additive and optional.
- Existing Crossroads modifiers, first-clear records, completed Dungeon records, and run/chamber stale-tab/replay protections remain intact.
- Existing Guild, Expedition, Hunt, inventory, recovery, Airship, and Fellowship persistence contracts are unchanged.
- Shipping archives contain no `.env`, database, token JSON, cache, log, or other runtime-private state.

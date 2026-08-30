# Crystal Guild v1.4.0 — Dungeons & Delves Beta 1 Release Audit

## Release identity
- Bot runtime: `1.4.0-dungeons-b1`
- Hosted Web runtime: `1.4.0-dungeons-b1`
- Frontend asset revision: `1.4.0-dungeons-b1`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`

## Scope lock
Beta 1 is the v1.4 feature-freeze and stabilization pass. The Dungeon catalog remains exactly four delves. No fifth Dungeon, new currency, new progression layer, or non-Dungeon balance change is included.

## Reliability closure
- Run/chamber binding is strengthened with a persisted state revision, closing stale actions from a second tab that is still viewing the same room.
- Action-ID replay/idempotency remains authoritative and restart-safe.
- Existing Crossroads modifiers, Event outcomes, first-clear records, retreat/defeat settlement, and completed Dungeon records remain intact.
- Existing Guild, Expedition, Hunt, inventory, recovery, Airship, and Fellowship persistence contracts are unchanged.
- Shipping archives must contain no `.env`, live database, token JSON, cache, log, or other runtime-private state.

## Upgrade contract
- Alpha 4 → Beta 1: **no DB migration**.
- Portal Action protocol advances **24 → 25**, therefore Web and Bot deploy together.
- No player reset, OAuth change, or new environment variable.

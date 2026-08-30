# Crystal Guild v1.4.0 — Dungeons & Delves Beta 3 Release Audit

## Release identity
- Bot runtime: `1.4.0-dungeons-b3`
- Hosted Web runtime: `1.4.0-dungeons-b3`
- Frontend asset revision: `1.4.0-dungeons-b3`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`

## Scope lock
Beta 3 is final Beta hardening. The Dungeon catalog remains exactly four delves. No fifth Dungeon, new currency, progression layer, reward tuning, combat tuning, or non-Dungeon balance change is included.

## Reliability closure
- State-guarded authoritative mutations obtain database write intent before live-state validation, extending serialization across separate connections.
- Run/chamber/revision stale-state binding remains authoritative.
- Same action-ID replay remains idempotent and restart-safe.
- Existing Dungeon persistence, Crossroads modifiers, Event outcomes, first clears, settlements, records, Bestiary, Guild, Expedition, Hunt, inventory, Airship, and Fellowship continuity remain intact.
- Shipping archives must contain no `.env`, live database, token JSON, cache, log, or other runtime-private state.

## Upgrade contract
- Expected baseline is Beta 2 Web + Beta 1 Bot.
- Schema remains **10** and Portal Action protocol remains **25**.
- Deploy Beta 3 Web and Bot together.
- No player reset, OAuth change, or new environment variable.

## Release packaging
- Bot patch baseline: Beta 1 Bot; **17 changed/new, 0 deletions**; exact **153-file** reconstruction.
- Web patch baseline: Beta 2 Web; **56 changed/new, 0 deletions**; exact **824-file** reconstruction.
- Individual and paired patch helpers: **PASS**.
- Six release ZIPs: CRC/integrity **PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 set: **PASS**.

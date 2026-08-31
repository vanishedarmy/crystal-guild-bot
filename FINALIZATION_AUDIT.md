# Crystal Guild v1.6.0 — Gold Saucer Alpha 3 Release Audit

## Alpha 3 scope
- Makes **MGP** the canonical Gold Saucer currency name.
- Adds canonical MGP fields to the Gold Saucer Portal state while retaining Alpha 2 `points` compatibility aliases.
- Keeps the physical schema-12 balance storage unchanged to avoid a live-data migration.
- Updates Mini Cactpot, Crystal Slots, Monster Toss, Prize Counter, and streamer grant Bot messages to MGP wording.
- Carries all Alpha 2 Monster Toss behavior, limits, records, and payouts forward unchanged.

## Frozen contract
Runtime `1.6.0-gold-saucer-a3`; local DB schema **12**; hosted sync **1**; Portal Action protocol **27**; Twitch prefix `!`.

No player reset, OAuth/environment change, new required variable, ordinary Gil economy change, combat progression change, Mini Cactpot payout change, Crystal Slots payout change, Monster Toss payout change, or Gold Saucer balance reset.

## Release gate
**619 / 619 Bot regression tests PASS**, including **4 / 4 Alpha 3 MGP-specific tests**. Python compile sweep: **PASS**.

## Packaging scope
This artifact is the authoritative **Bot-side Alpha 3 MGP package** created from the v1.6.0 Gold Saucer Alpha 2 Hotfix 2 canonical Bot baseline. The matching canonical Web archive was not available in the working Library, so no Alpha 3 Web package or frontend-build claim is included in this audit.

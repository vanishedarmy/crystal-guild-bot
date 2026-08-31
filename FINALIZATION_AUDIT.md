# Crystal Guild v1.6.0 — Gold Saucer Alpha 4 Release Audit

## Alpha 4 scope
- Opens Chocobo Racing using the existing registered Chocobo system.
- Adds three daily courses with Bond-level gates, course-favored trait bonuses, and three pace profiles.
- Resolves races atomically through the authoritative Bot with exactly-once Portal action replay.
- Adds racing records/history and two cosmetic Prize Counter titles.
- Preserves Alpha 3 MGP balances and all existing Gold Saucer attraction economics.

## Frozen contract
Runtime `1.6.0-gold-saucer-a4`; local DB schema **12**; hosted sync **1**; Portal Action protocol **28**; Twitch prefix `!`.

No player reset, database migration, OAuth/environment change, new required variable, ordinary Gil economy change, Mini Cactpot payout change, Crystal Slots payout change, Monster Toss payout change, or existing MGP balance reset.

## Release gate
Release gate: **623 / 623 Bot tests PASS**; matched source Python parse **119 / 119 PASS**. See `VALIDATION_REPORT.md` for the focused Alpha 4 coverage.

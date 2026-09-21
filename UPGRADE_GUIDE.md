# Crystal Guild v1.9.0 Alpha 3 — Title Expansion Upgrade Guide

## From v1.9.0 Alpha 2
Deploy the matching Alpha 3 Bot and Web packages together and restart the services. Existing player data, MGP, titles, achievements, Trading Post listings, inventories, Fellowship state, Mercs, and Gold Saucer records are preserved.

No database migration is required for Alpha 2 → Alpha 3. The release continues to use:
- Runtime/frontend: `1.9.0-title-expansion-alpha3`
- Local schema: **19**
- Hosted sync: **1**
- Portal Action protocol: **36**

## Existing migration history
Older installations still upgrade through the existing verified migrations. v1.8.1 introduced schema **17 → 18** for Merc recruitment. v1.9.0 Alpha 1 introduced schema **18 → 19** for the Moogle Trading Post, creating a verified `pre_schema_19_*.db` backup before migration.

## After deployment
1. Confirm `!cgversion` reports `1.9.0-title-expansion-alpha3`.
2. Open Gold Saucer and confirm **Challenge Titles** appear separately from Prize Counter purchases.
3. Confirm the four new Prize Counter titles cost 750 / 1,000 / 1,250 / 1,500 MGP.
4. Confirm previously earned achievement progress is preserved; qualifying titles are granted when achievement checks next run.
5. Keep the live database at its existing persistent path (for Render, normally `/var/data/crystal_guild.db`).

No player reset is required.

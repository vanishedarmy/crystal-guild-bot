# Crystal Guild v1.9.0 Alpha 6 — World Events Upgrade Guide

Upgrade from **v1.9.0 Alpha 5 — Title Status Hardening** by deploying the matching Alpha 6 Bot and Web packages together, then restarting both services.

## Compatibility
- Runtime/frontend: `1.9.0-world-events-alpha6`
- Local database schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**
- Database migration required: **No**
- Player reset required: **No**

World Event timing state uses the existing runtime-state table, so no schema migration is needed. Existing player progress, Titles, achievements, inventory, Fellowship state, Gold Saucer data, Mercs, Retainers, and Trading Post state remain intact.

## Deployment
1. Stop the current Alpha 5 Bot and Web services.
2. Replace them with the matching Alpha 6 packages (or apply the Alpha 5 → Alpha 6 overlay patch).
3. Preserve the existing database and environment configuration.
4. Start the Web service, then the Bot worker.
5. Confirm `!cgversion` reports `1.9.0-world-events-alpha6`.
6. Confirm schema **19**, hosted sync **1**, and Portal Action protocol **36**.
7. Open **Stream Activities → World Events** and verify the ten-monster roster/artwork loads.

No manual World Event seed data is required. The live scheduler begins automatically while the configured Twitch stream is live.

## Older persistent-database lineage
Installations coming from the older Merc Recruitment line may previously have crossed schema **17 → 18**, and the Trading Post migration to schema 19 uses the verified `pre_schema_19_<timestamp>.db` backup path. Alpha 6 itself does not perform a new schema migration.

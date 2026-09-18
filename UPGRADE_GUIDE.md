# Crystal Guild v1.8.1 — Merc Recruitment Upgrade Guide

v1.8.1 upgrades directly from the v1.8.0 Merc Service release line. Existing players, inventories, jobs, Hunts, Dungeons, Expeditions, retainers, Gold Saucer progress, and active Merc contracts remain intact.

## Database migration

The local player database advances from schema **17 → 18**. On the first launch against an existing database, Crystal Guild automatically creates and verifies a `pre_schema_18_<timestamp>.db` backup before applying the migration.

Schema 18 adds `player_merc_recruits`, which stores permanent recruitment for expansion Heroes. The founding roster does not need rows in this table and keeps its existing progression behavior.

No player reset is required.

## Portal compatibility

- Runtime/frontend: `1.8.1-merc-recruitment`
- Local database schema: **18**
- Hosted sync schema: **1**
- Portal Action protocol: **35**

Deploy the v1.8.1 Bot and Web packages together so the new `MERC_RECRUIT` action and Dungeon `revision` fields use the same protocol on both sides.

## Dungeon repair

v1.8.1 also repairs the hosted Portal validation path for Dungeon actions. `DUNGEON_ACTION`, `DUNGEON_CHOICE`, `DUNGEON_CONTINUE`, and `DUNGEON_RETREAT` preserve the authoritative room `revision` sent by the frontend. Existing active Dungeon runs do not need to be cleared or restarted solely for this fix.

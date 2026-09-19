# Crystal Guild v1.8.2 — Elite Mercs Upgrade Guide

## Upgrade from v1.8.1

Replace the **Bot and Web packages together**. v1.8.2 adds the six Elite Hero definitions on the Bot side and their Merc Service presentation/artwork on the Web side, so both components should remain on the same release.

No database migration is required for **v1.8.1 → v1.8.2**:

- Runtime/frontend: `1.8.2-elite-mercs`
- Local database schema: **18** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Portal Action protocol: **35** (unchanged)
- No player reset is required.

Existing player data, inventories, jobs, Hunts, Dungeons, Expeditions, retainers, Gold Saucer progress, permanent Merc recruitment records, and active Merc contracts are preserved.

## Elite Merc assets

The Web package adds `/frontend/public/merc-service/a3/cards/` with 18 optimized WebP cards:

- `*-locked.webp` — silhouette; Hero has not been recruited.
- `*-unavailable.webp` — Hero is recruited but currently hired/deployed.
- `*-available.webp` — Hero is recruited and ready to hire.

The six Elite Heroes are Lightning, Sephiroth, Rikku, Y’shtola, Noctis, and Cid.

## Upgrading from an older schema-17 build

If the installation predates v1.8.1 and still uses local database schema 17, the existing **17 → 18** migration remains required. Crystal Guild creates and verifies a `pre_schema_18_<timestamp>.db` backup before applying that migration. Schema 18 adds permanent Merc recruitment storage; v1.8.2 does not introduce another schema change.

## Deployment check

After updating, verify that both Bot and Web identify as `1.8.2-elite-mercs`. A mixed v1.8.1/v1.8.2 deployment should be avoided even though the Portal protocol number itself remains 35.

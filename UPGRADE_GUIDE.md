# Crystal Guild v1.9.0 Alpha 7 — Hall of Trophies Upgrade Guide

Upgrade from the latest **v1.9.0 Alpha 6 — World Events** Hotfix 10 baseline by deploying the matching Alpha 7 Bot and Web packages together.

## Compatibility
- Runtime/frontend: `1.9.0-hall-of-trophies-alpha7`
- Local database schema: **20**
- Hosted sync schema: **1**
- Portal Action protocol: **36**
- Database migration required: **Yes — automatic 19 → 20**
- Player reset required: **No**

The schema-20 migration adds permanent Trophy ownership and exact World Event clear history. A verified `pre_schema_20_<timestamp>.db` backup is created before migration.

## Deployment
1. Preserve the live database, token stores, `.env`, hosted secrets, and persistent-disk data.
2. Stop the current Alpha 6 Bot and Web services.
3. Deploy the matching Alpha 7 Web and Bot packages (or apply the Hotfix 10 → Alpha 7 overlay patch).
4. Start the Web service, then the Bot worker.
5. Confirm `!cgversion` reports `1.9.0-hall-of-trophies-alpha7`.
6. Confirm local schema **20**, hosted sync **1**, and Portal Action protocol **36**.
7. Open **Adventurer Profile → Hall of Trophies** and verify the 30-trophy catalog and artwork load.
8. Existing provable Raid, Hunt, Triple Triad, and Fellowship trophies reconcile automatically. Older World Event variants are credited only where exact participation history can prove them.

No manual trophy seed data or player reset is required.

## Older database lineage
Installations from older Merc Service lines continue through the established **17 → 18** Merc Recruitment migration and **18 → 19** Trading Post migration before the new **19 → 20** Hall of Trophies migration. Each structural step retains the verified backup behavior.

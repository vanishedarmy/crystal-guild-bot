# Crystal Guild v1.9.0 Alpha 1 — Moogle Trading Post Upgrade Guide

## Upgrade from v1.8.2

Replace the **Bot and Web packages together**. Trading Post transactions depend on Bot schema 19 and Portal Action protocol 36, while the matching Web package provides the marketplace UI and artwork.

Release contract:

- Runtime/frontend: `1.9.0-trading-post-alpha1`
- Local database schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**
- No player reset is required.

## Database migration

The first launch against an existing Guild automatically migrates the local database to schema 19. Before the schema-19 migration is applied, Crystal Guild creates and verifies a backup named:

`pre_schema_19_<timestamp>.db`

Schema 19 adds only the `trading_post_listings` ledger and its indexes. Existing players, inventory, equipment, jobs, Fellowship progress, Merc contracts, Retainers, Gold Saucer progress, Hunts, Dungeons, Expeditions, and other saved systems are retained.

### Older installations

Crystal Guild still applies the earlier **17 → 18** permanent Merc recruitment migration automatically when upgrading from an older schema-17 installation, followed by the new **18 → 19** Trading Post migration. Each structural step uses the existing verified pre-migration backup flow; the final Trading Post step creates `pre_schema_19_<timestamp>.db`.

## Deployment order

1. Stop the running Bot and Portal sync processes.
2. Back up the existing installation as normal.
3. Replace the Bot and Web files with the matching v1.9.0 Alpha 1 packages.
4. Start the Bot once and confirm the local database reports schema 19.
5. Start the matching Web/hosted Portal package and confirm Portal Action protocol 36.
6. Verify the Fellowship page shows the Moogle Trading Post construction card and the Moogle Emporium shows the Trading Post tab.

Do not mix a protocol-36 Web package with a protocol-35 Bot package.

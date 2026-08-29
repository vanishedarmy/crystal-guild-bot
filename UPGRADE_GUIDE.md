# Upgrade Guide — Crystal Guild v1.2.0 Expeditions Beta 4

## Recommended path from Beta 3
Beta 3 used the Beta 1 Bot, so Beta 4 is a paired Web + Bot update.

1. Back up the live database and persistent Twitch/token storage.
2. Stop the Bot.
3. Apply the **B1 → B4 Bot patch** or replace application files with the full Beta 4 Bot package, preserving `.env`, databases, and token storage.
4. Apply the **B3 → B4 Web patch** or deploy the full Beta 4 Web package.
5. Start the Bot and verify `!cgversion` reports `1.2.0-expeditions-b4`, schema 8, protocol 20.
6. Verify `/api/health` reports Web `1.2.0-expeditions-beta4`, frontend `1.2.0-expeditions-b4`, hosted sync schema 1, protocol 20.
7. Hard-refresh the Portal once so the Beta 4 release identity/Guide metadata is loaded.

No migration is required from any v1.2 Alpha/Beta build already on schema 8.

## Direct upgrade from v1.1.19 RC1 Hotfix 9
The established v1.2 migration path remains supported. Preserve the H9 schema-7 database, replace the Bot/Web application files with the Beta 4 full packages, and start the Beta 4 Bot. Opening the schema-7 database applies migration 8 and creates/verifies a `pre_schema_8_<timestamp>.db` backup before structural migration. No player reset is required. H9's existing combat timing values remain valid.

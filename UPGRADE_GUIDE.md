# Upgrade Guide — Crystal Guild v1.2.0 Expeditions RC1

## From Beta 4
1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot.
3. Apply the Beta 4 → RC1 Bot patch, or replace Bot application files with the RC1 Bot package while preserving `.env`, database files, and token storage.
4. Deploy the Beta 4 → RC1 Web patch or the full RC1 Web package.
5. Start the Bot and confirm `!cgversion` reports `1.2.0-expeditions-rc1`, schema 8, and Portal Action protocol 20.
6. Confirm `/api/health` reports Web/frontend revision `1.2.0-expeditions-rc1`.
7. Open the Player Guide → Expeditions section and confirm it contains player instructions rather than Alpha/Beta release-engineering blocks.
8. Test one saved/active Expedition by leaving the Portal and returning before resolving the next step.

No database migration, player reset, OAuth change, or new environment variable is required from Beta 4.

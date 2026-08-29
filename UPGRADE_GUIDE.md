# Upgrade Guide — Crystal Guild v1.2.0 Expeditions

## From v1.2 RC1
1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot.
3. Apply the RC1 → v1.2.0 Bot patch, or replace Bot application files with the final Bot package while preserving `.env`, database files, and token storage.
4. Deploy the RC1 → v1.2.0 Web patch or the full final Web package.
5. Start the Bot and confirm `!cgversion` reports `1.2.0-expeditions`, schema 8, and Portal Action protocol 20.
6. Confirm `/api/health` reports Web/frontend revision `1.2.0-expeditions`.
7. Open the Player Guide → Expeditions section and verify the final player-facing guide loads normally.
8. Resume an existing character and verify profile, Chocobo, Fellowship, inventory, and Expedition progress are unchanged.

No database migration, player reset, OAuth change, or new environment variable is required from RC1.

## From v1.1.19 RC1 Hotfix 9
Use the full v1.2.0 Bot and Web packages while preserving `.env`, the player database, and persistent Twitch token data. Run `python upgrade_crystal_guild.py` before starting the final Bot. The additive schema 7 → 8 migration creates and verifies a pre-schema-8 backup and preserves existing progression.

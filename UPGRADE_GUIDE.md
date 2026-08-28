# Upgrade Guide — Crystal Guild v1.2.0 Expeditions Beta 1

## Supported direct baseline
This release includes direct patches from **Expeditions Alpha 5 → Beta 1** for both Web and Bot.

## Recommended upgrade
1. Stop the local Crystal Guild Bot.
2. Back up the current database, `.env`, and persistent Twitch token data as normal.
3. Apply the **A5 → B1 Bot patch** (or replace application files with the full Beta 1 Bot package), preserving `.env`, database files, and token storage.
4. Deploy the **A5 → B1 Web patch** or full Beta 1 Web package.
5. Start the Bot and confirm `!cgversion` reports runtime `1.2.0-expeditions-b1`, local DB schema 8, and Portal Action protocol 20.
6. Confirm `/api/health` reports Web `1.2.0-expeditions-beta1` and frontend revision `1.2.0-expeditions-b1`.
7. Open the Expedition Board and verify Safe describes lower combat/hazard pressure while Push Deeper warns of harder combat/hazards.

No database migration, player reset, OAuth reconfiguration, or new environment variable is required. Existing Alpha 5 Chocobo specialties, Expedition records, region exploration, Atlas/Mastery, landmarks, Legendary unlocks, inventory, and progression remain intact.

# Upgrade Guide — v1.2.0 Expeditions Alpha 1

Baseline: v1.1.19 Retro Phase III RC1 Hotfix 9.

1. Stop the current Bot.
2. Back up the existing database and persistent Twitch token data.
3. Apply the H9 -> v1.2 Bot patch or replace the Bot application files with the full v1.2 Bot package while preserving `.env`, the database, and token storage.
4. Run `python upgrade_crystal_guild.py`.
5. The Database constructor migrates local schema **7 -> 8** and creates/verifies a pre-migration backup before structural changes.
6. Deploy the matching v1.2 Web package.
7. Start the Bot and verify `!cgversion` reports runtime `1.2.0-expeditions-a1` and Portal Action protocol **20**.
8. Verify an existing player can still load, then test the Chocobo Stable and Adventure Board.
9. Complete/verify the Fellowship Expedition Board and registered Chocobo requirement, then launch an Emerald Wilds Scout Expedition.

Existing progression is preserved. Hosted sync schema remains **1**. H9 timer environment overrides remain compatible.

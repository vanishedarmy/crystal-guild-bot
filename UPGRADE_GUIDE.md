# Upgrade Guide — v1.1.19 Retro Phase III RC1 Hotfix 7

1. Stop the current Bot.
2. Back up the database as usual.
3. Replace the Bot files with RC1H7 while preserving `.env`, database, Twitch token database, and other persistent runtime data.
4. No database migration is required; schema remains **7**.
5. Deploy the matching RC1H7 Web package.
6. Start the Bot and verify `!cgversion` reports `1.1.19-retro-phase-iii-rc1h7` and Portal Action protocol 18.
7. Test `!additem <testplayer> | potion | 1`, then `!removeitem <testplayer> | potion | 1`, or use the matching Streamer Dashboard controls.

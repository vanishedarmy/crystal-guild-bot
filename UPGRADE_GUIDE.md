# Upgrade Guide — v1.1.19 Retro Phase III RC1 Hotfix 9

1. Stop the current Bot.
2. Back up the database and persistent token data.
3. Replace the Bot files with H9 while preserving `.env`, database, and Twitch token DB.
4. Run `python upgrade_crystal_guild.py`. No DB migration is required. The helper updates only the exact prior stock timer values to the H9 defaults.
5. If timer variables are explicitly configured in Render, set `ENCOUNTER_JOIN_SECONDS=60`, `ENCOUNTER_ROUND_SECONDS=30`, `RAID_JOIN_SECONDS=90`, and `RAID_ROUND_SECONDS=60`.
6. Deploy the matching H9 Web package.
7. Start the Bot and verify `!cgversion` reports `1.1.19-retro-phase-iii-rc1h9` and Portal Action protocol 19.
8. Test a Streamer Portal boss spawn while LIVE, a Rally Venture, and cross-player field recovery.

Schema remains **7** and all progression is preserved.

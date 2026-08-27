# Upgrade Guide — Facility Supply Balance

Baseline: **Bot v1.1.18 Passive Recovery Hotfix** + **Web v1.1.19 Retro Phase III iii11**.

1. Back up the live `crystal_guild.db` as normal.
2. Stop the Bot worker cleanly.
3. Apply the Facility Supply Balance Bot patch, or replace the Bot source with the full Bot package.
4. Preserve `.env`, Twitch token storage, `crystal_guild.db`, and Render persistent-disk paths.
5. Deploy the matching Web iii12 package or apply the iii11 → iii12 Web patch.
6. Restart/redeploy both services.
7. Verify `!cgversion` reports `1.1.19-retro-phase-iii-balance1`.
8. Verify hosted `/api/health` reports Web runtime `1.1.19-retro-phase-iii` and frontend revision `1.1.19-retro-phase-iii12`.
9. Open the Player Guide Bestiary and confirm examples such as Imp → Demon Horn, Cockatrice → Wyvern Scale, Spriggan → Mythril Ore, and Ossuary Knight → Ancient Coin are visible with their new drop percentages.

No database migration, manual SQLite edit, player reset, OAuth reconfiguration, or new environment variable is required.

# Upgrade Guide — Facility Supply Balance → Chocobo Portraits

1. Stop the Bot/worker cleanly.
2. Preserve `.env`, Twitch token storage, `crystal_guild.db`, and Render persistent-disk paths.
3. Make your normal manual database backup as an additional safeguard.
4. Apply the Chocobo Portrait Bot patch over `1.1.19-retro-phase-iii-balance1`, or replace the Bot source with the full Chocobo Portrait package.
5. On first start, the Bot performs the additive **schema 5 → 6** migration and automatically creates/verifies a `pre_schema_6_<timestamp>.db` backup.
6. Deploy the matching Web iii13 package/patch. Bot and Web must match because Portal Action protocol advances **14 → 15**.
7. Restart/redeploy both services.
8. Verify `!cgversion` reports `1.1.19-retro-phase-iii-chocobo1`.
9. Verify hosted `/api/health` reports runtime `1.1.19-retro-phase-iii-chocobo1`, frontend revision `1.1.19-retro-phase-iii13`, and Portal Action protocol `15`.
10. Open a registered player’s Chocobo Stable, apply a portrait, refresh, and confirm it persists.

No player reset, OAuth change, or new environment variable is required.

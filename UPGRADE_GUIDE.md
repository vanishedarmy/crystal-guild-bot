# Upgrade Guide — v1.1.19 Retro Phase III RC1

Baseline: **v1.1.19 Retro Phase III / Chocobo Portraits + Facility Supply Balance**.

1. Stop the Bot cleanly.
2. Preserve `.env`, Twitch token storage, the live `crystal_guild.db`, and any persistent-disk paths.
3. Back up the database as usual.
4. Apply the RC1 Bot patch or replace the Bot source with the RC1 full Bot package.
5. Apply the matching RC1 Web patch/full Web package and redeploy the hosted Web service.
6. Restart the Bot.
7. Verify `!cgversion` reports `1.1.19-retro-phase-iii-rc1`.
8. Verify `/api/health` reports Web runtime `1.1.19-retro-phase-iii-rc1`, frontend revision `1.1.19-retro-phase-iii14-rc1`, and Portal Action protocol `15`.
9. Open Camp, Blacksmith, Chocobo Stable, and Moogle Emporium and confirm the scenic background art is visible but controls remain readable.

No database migration is required from the Chocobo Portrait checkpoint; schema 6 remains current. No player reset, OAuth change, or new environment variable is required.

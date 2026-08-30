# Upgrade Guide — Crystal Guild v1.5.0 Trails & Raids Alpha 1

Baseline: **v1.4.0 Dungeons & Delves production Web + Bot**.

1. Back up the live database and preserve `.env`, Twitch token storage, hosted secrets, and persistent-disk data.
2. Stop the Bot cleanly.
3. Apply the **v1.4.0 → Alpha 1 Bot patch** or replace the Bot source with the full Alpha 1 package while preserving private/runtime state.
4. Apply the **v1.4.0 → Alpha 1 Web patch** or deploy the full Alpha 1 Web package.
5. Restart/redeploy matching Web + Bot. No database migration should run; local schema remains **10**.
6. Verify `!cgversion` reports `1.5.0-trails-raids-a1`.
7. Verify `/api/health` reports Web/frontend `1.5.0-trails-raids-a1`, hosted sync schema **1**, and Portal Action protocol **25**.
8. Spawn Ifrit in staging and confirm the opening **Incinerate** telegraph, then **Radiant Plume**, **Infernal Nails**, and weakened/empowered **Hellfire** resolution.
9. Confirm the Adventure Board and OBS overlay show public mechanic/contribution data without player IDs or internal target IDs.
10. Spot-check an existing Dungeon and existing player progression to confirm v1.4 state is unchanged.

No player reset, OAuth/environment change, or new environment variable is required.

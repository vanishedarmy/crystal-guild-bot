# Upgrade Guide — v1.4.0 Dungeons & Delves Alpha 4

Baseline: **Dungeons & Delves Alpha 3 Bot + Web**.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the **Alpha 3 → Alpha 4 Bot patch**, or replace the Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the matching **Alpha 3 → Alpha 4 Web patch** or full Alpha 4 Web package.
5. Restart/redeploy Bot and Web.
6. Verify `!cgversion` reports `1.4.0-dungeons-a4` with local schema **10**.
7. Verify `/api/health` reports Web/frontend `1.4.0-dungeons-a4`, hosted sync schema **1**, and Portal Action protocol **24**.
8. Open Dungeon Board and confirm all four Dungeons appear, including **The Riftglass Observatory** at Lv.34 + 55% The Astral Scar.
9. Spot-check an Event chamber and an encounter-rules battle card; confirm outcomes/mechanics survive a refresh/reconnect as appropriate.
10. Confirm existing Alpha 3 Dungeon runs, progress, Crossroads effects, first-clear records, Guild data, and player progression remain intact.

No database migration, player reset, OAuth change, or new environment variable is required from Alpha 3.

# Upgrade Guide — v1.5.0 Trails & Raids Beta 1

Baseline: **v1.5.0 Trails & Raids Alpha 7**.

1. Back up the live player database and persistent Twitch/token data as usual.
2. Stop the Bot cleanly.
3. Apply the **Alpha 7 → Beta 1 Bot patch**, or replace Bot source while preserving `.env`, the live database, tokens, and persistent-disk configuration.
4. Deploy the matching **Alpha 7 → Beta 1 Web patch**, or replace the Web source.
5. Start the Bot and confirm `!cgversion` reports `1.5.0-trails-raids-b1` with local schema **10** and Portal protocol **25**.
6. Redeploy/restart the hosted Web service and confirm `/api/health` reports Web/frontend `1.5.0-trails-raids-b1`, hosted sync schema **1**, and Portal protocol **25**.
7. Open Adventure Board → Trial & Raid Board. Confirm the Chronicle shows existing Trial clears and per-Trial records.
8. Resolve a Trial in staging if practical and confirm tracked wipes/fastest clear/contribution bests update after Portal sync.
9. Open Records → Trial Chronicle and confirm the same personal records are shown there.
10. Verify existing players, inventories, Fellowship, Expeditions, Dungeons, boss clears, and all seven Trial encounters remain intact.

No database migration, player reset, OAuth/environment change, or new environment variable is required.

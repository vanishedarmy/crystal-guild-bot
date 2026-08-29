# Upgrade Guide — Crystal Guild v1.3.0 Guild Expansion Alpha 2

Baseline: **v1.3.0 Guild Expansion Alpha 1**.

1. Back up the current Crystal Guild player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the **Alpha 1 → Alpha 2 Bot patch**, or replace the Bot application files with the full Alpha 2 Bot package while preserving `.env`, database files, and token storage.
4. Deploy the matching **Alpha 1 → Alpha 2 Web patch** or full Alpha 2 Web package.
5. Restart the Bot and redeploy/restart the hosted Web service.
6. Confirm `!cgversion` reports `1.3.0-guild-expansion-a2`.
7. Confirm `/api/health` reports Web/frontend revision `1.3.0-guild-expansion-a2`, hosted sync schema **1**, and Portal Action protocol **20**.
8. Open Fellowship and confirm Available Guild Work includes Construction plus unlocked Supply Drives/Guild Objectives.
9. Check `!orders` and confirm each weekly Order shows its contributor reward and the full-week bonus.

No schema migration is required. Existing Fellowship Renown, facility tiers, current projects, Guild Rank, Order/Deed history, Chocobos, Expeditions, inventories, and character progression remain in place.

# Upgrade Guide — Crystal Guild v1.3.0 Guild Expansion Alpha 3

Baseline: **v1.3.0 Guild Expansion Alpha 2**. Because Alpha 3 advances Portal Action protocol **20 → 21**, deploy the matching Web and Bot together.

1. Back up the current Crystal Guild player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the **Alpha 2 → Alpha 3 Bot patch**, or replace the Bot application files with the full Alpha 3 Bot package while preserving `.env`, database files, and token storage.
4. Deploy the matching **Alpha 2 → Alpha 3 Web patch** or full Alpha 3 Web package.
5. Restart the Bot and redeploy/restart the hosted Web service.
6. Confirm `!cgversion` reports `1.3.0-guild-expansion-a3`.
7. Confirm `/api/health` reports runtime/frontend revision `1.3.0-guild-expansion-a3`, hosted sync schema **1**, and Portal Action protocol **21**.
8. Open the Fellowship page and confirm **Facility Services** shows Workshop, Chocobo Stable, and Guild Archive benefits.
9. On a player whose Guild Workshop is Lv. 2+, open their own Fellowship tab and confirm Workshop Refining is available. Test one eligible exchange.
10. In chat, check `!workshop`; if desired, test `!refine <service> [batches]`.
11. Confirm existing Guild projects, Weekly Orders, facility tiers, Expeditions, Chocobo state, inventories, and player progression remain unchanged.

No database migration is required. Local DB schema remains **8**. Existing Fellowship Renown, project progress, facility tiers, Guild Rank, Order/Deed history, Chocobos, Expeditions, inventories, and character progression remain in place.

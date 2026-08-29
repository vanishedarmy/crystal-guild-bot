# Upgrade Guide — v1.3.0 Guild Expansion Beta 1

Recommended baseline: **Alpha 5 Hotfix 1 Web + Alpha 5 Bot**.

1. Back up the live Crystal Guild database and persistent Twitch/token data.
2. Stop the Bot.
3. Apply the **Alpha 5 → Beta 1 Bot patch** or replace the Bot source with the full Beta 1 Bot package while preserving `.env`, database files, and token stores.
4. Deploy the **Alpha 5 Hotfix 1 → Beta 1 Web patch** or full Beta 1 Web package.
5. Start the Bot and redeploy/restart the hosted Web service.
6. Verify `!cgversion` reports `1.3.0-guild-expansion-b1`.
7. Verify `/api/health` reports hosted runtime/frontend revision `1.3.0-guild-expansion-b1`, hosted sync schema **1**, and Portal Action protocol **21**.
8. Open Fellowship and confirm the Guild/Airship surfaces load normally. Existing Founding Hall art and collapsible inventory groups should remain intact.

No database migration is required. Local schema remains **9** and all player, Fellowship, Airship, Legacy, Expedition, and inventory progression is preserved.

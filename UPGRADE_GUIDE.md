# Upgrade Guide — Crystal Guild v1.3.0 Guild Expansion Alpha 1

Baseline: **v1.2.0 — Expeditions final**.

1. Back up the current Crystal Guild database and persistent Twitch/token data.
2. Stop the Bot.
3. Apply the v1.2.0 → v1.3 Alpha 1 Bot patch, or replace the Bot application files with the full Alpha 1 Bot package while preserving `.env`, database files, and token storage.
4. Apply the matching Web patch or full Alpha 1 Web package and redeploy the hosted Web service.
5. Start the Bot.
6. Confirm `!cgversion` reports `1.3.0-guild-expansion-a1`, local DB schema **8**, and Portal Action protocol **20**.
7. Confirm `/api/health` reports Web/frontend revision `1.3.0-guild-expansion-a1`.
8. Open Fellowship and confirm the five major facility cards appear, with Airship Dock shown as locked future construction.
9. Confirm the current Guild project and existing contribution controls still work.

No database migration or player reset is required. On startup the existing Fellowship table simply seeds the new `airship_dock` facility row at Lv. 0 if it is missing. Existing facility tiers, contributions, Orders, Deeds, Guild Rank, Chocobos, Expeditions, inventory, and character progression are preserved.

# Upgrade Guide — v1.4.0 Dungeons & Delves Alpha 2

Baseline: **v1.4.0 Dungeons & Delves Alpha 1 Web + Bot**. Portal Action protocol advances **23 → 24**, so deploy the matching Alpha 2 Web and Bot together.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the **Alpha 1 → Alpha 2 Bot patch**, or replace the Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the matching **Alpha 1 → Alpha 2 Web patch** or full Alpha 2 Web package.
5. Restart the Bot and hosted Web service.
6. Verify `!cgversion` reports `1.4.0-dungeons-a2` and local schema **10**.
7. Verify `/api/health` reports Web/frontend `1.4.0-dungeons-a2`, hosted sync schema **1**, and Portal Action protocol **24**.
8. Open **Adventure Board → Dungeons & Delves** and confirm both The Forgotten Ossuary and The Emberglass Foundry appear with their unlock requirements.
9. On an eligible character, reach a Crossroads and verify a route choice applies once, records its discovery, and advances back to the normal Continue/Retreat state.
10. If practical, leave a stale browser tab open at that Crossroads and confirm a second stale mutation cannot change the resolved route.
11. Confirm the shared collapse hand is consistently sized and shows **right when closed / down when open**, including What’s New.
12. Confirm active Dungeon condition, Cache, discoveries, and current chamber survive a Portal refresh and Bot restart.

No database migration is required from Alpha 1; schema **10** remains current. Existing player, Fellowship, Airship, Expedition, inventory, Bestiary, achievement, title, equipment, and Dungeon progress are preserved. No player reset, OAuth change, or new environment variable is required.

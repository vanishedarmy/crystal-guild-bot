# Upgrade Guide — v1.5.0 Trails & Raids Alpha 7

Baseline: **v1.5.0 Trails & Raids Alpha 6**.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the **Alpha 6 → Alpha 7 Bot patch**, or replace the Bot source while preserving `.env`, database files, token storage, and persistent-disk state.
4. Deploy the matching **Alpha 6 → Alpha 7 Web patch** or full Alpha 7 Web package.
5. Restart/redeploy both services.
6. Verify `!cgversion` and `/api/health` report `1.5.0-trails-raids-a7`; local schema remains 10, hosted sync 1, Portal protocol 25.
7. Open the collapsible **Trial & Raid Board** and confirm **Bahamut — The Final Coil** appears as the full-width capstone card.
8. In staging, verify Flare Breath → Akh Morn → Megaflare Towers. Lower Bahamut below 30% HP and confirm the one-time Teraflare Charge appears.
9. Confirm existing players, Guild/Fellowship state, Expeditions, Dungeons, inventories, records, and the six earlier Trials remain intact.

No migration, reset, OAuth/environment change, or new environment variable is required.

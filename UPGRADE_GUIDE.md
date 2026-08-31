# Upgrade Guide — v1.5.0 Trails & Raids Alpha 6

Baseline: **v1.5.0 Trails & Raids Alpha 5**.

1. Back up the live player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the **Alpha 5 → Alpha 6 Bot patch**, or replace the Bot source while preserving `.env`, database files, token storage, and persistent-disk state.
4. Deploy the matching **Alpha 5 → Alpha 6 Web patch** or full Alpha 6 Web package.
5. Start the Bot and redeploy/restart the hosted Web service.
6. Verify `!cgversion` and `/api/health` report `1.5.0-trails-raids-a6`; local schema remains 10, hosted sync 1, Portal protocol 25.
7. Open the collapsible **Trial & Raid Board** and confirm Leviathan — Tidebreak Expanse appears with Tidal Sweep, Undertow, Maelstrom Surge, and Tidal Wave guidance.
8. In staging, spawn Leviathan with `!spawnboss leviathan`, join with `!raid`, and confirm telegraphs/Defend responses appear on both the Portal board and OBS overlay.
9. Confirm Ifrit, Shiva, Ramuh, Titan, Garuda, ordinary raids, Dungeons, Expeditions, Fellowship, inventory, and player progression remain intact.

No migration, reset, OAuth change, or new environment variable is required from Alpha 5.

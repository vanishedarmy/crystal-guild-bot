# Upgrade Guide — v1.5.0 Trails & Raids Alpha 5

Baseline: **v1.5.0 Trails & Raids Alpha 4**. No database migration is required.

1. Back up the live database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the Alpha 4 → Alpha 5 Bot patch, or replace the Bot source while preserving `.env`, database files, token storage, and persistent-disk state.
4. Deploy the matching Alpha 4 → Alpha 5 Web patch or full Alpha 5 Web package.
5. Start/redeploy Bot and Web together.
6. Verify `!cgversion` and `/api/health` report `1.5.0-trails-raids-a5`; schema remains 10, hosted sync 1, Portal protocol 25.
7. Open Adventure Board → Trial & Raid Board. Confirm the board remains collapsible and now uses two roomy Trial cards per desktop row, one per row on narrower screens.
8. Stage **Garuda** and confirm the Trial reports **Eye of the Storm**.
9. During **Slipstream**, Defend on the marked raider and confirm the brace result; miss a later response and confirm brief Slow pressure.
10. During **Friction**, confirm Defend contains the mark while an undefended mark splashes party damage.
11. During **Plume Squadron**, confirm Satin/Razor Plumes intercept normal enemy-directed damage and that Aerial Blast strength reflects how many Plumes survive.
12. Confirm Ifrit, Shiva, Ramuh, Titan, ordinary raids, all four Dungeons, inventories, Fellowship, Expeditions, and player progression remain intact.

No reset, OAuth change, environment change, or new environment variable is required.

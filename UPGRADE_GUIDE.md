# Upgrade Guide — Crystal Guild v1.5.0 Trails & Raids Alpha 4

Baseline: **v1.5.0 Trails & Raids Alpha 3**. Alpha 4 is a paired Bot/Web update. Local schema remains **10**, hosted sync remains **1**, and Portal Action protocol remains **25**.

1. Back up the live player database and persistent Twitch/token state.
2. Stop the Bot cleanly.
3. Apply the **Alpha 3 → Alpha 4 Bot patch** or replace Bot source with the full Alpha 4 package while preserving `.env`, database files, token storage, and persistent-disk state.
4. Apply the **Alpha 3 → Alpha 4 Web patch** or deploy the full Alpha 4 Web package.
5. Start the Bot and redeploy/restart the hosted Web service. No database migration should run.
6. Verify `!cgversion` reports `1.5.0-trails-raids-a4`.
7. Verify `/api/health` reports Web/frontend `1.5.0-trails-raids-a4`, hosted sync schema **1**, and Portal Action protocol **25**.
8. Open Adventure Board → Trial & Raid Board. Confirm the board remains collapsible, points right when closed / down when open, and remembers its state after refresh.
9. Stage **Titan** and confirm the Trial reports **Heart of the Crag**.
10. During **Landslide**, have the marked raider Defend and confirm the knockback is braced; allow a later marked raider to miss the response and confirm knockdown costs their next action.
11. During **Granite Gaol**, confirm the restrained raider cannot act and that party damage breaks the Gaol and releases them.
12. During **Heart of the Crag**, destroy the Heart within the two-round check and confirm **Earthen Fury** resolves weakened. If practical in staging, also verify a failed Heart check produces the empowered raidwide version.
13. Confirm Ifrit, Shiva, Ramuh, unscripted raids, Dungeons, Expeditions, Fellowship, inventories, records, and existing player progression remain intact.

No player reset, OAuth/environment change, new environment variable, or schema migration is required.

# Upgrade Guide — Crystal Guild v1.5.0 Trails & Raids Alpha 2

Baseline: **Alpha 1 Bot + Alpha 1 Hotfix 2 Web**. Alpha 2 is a paired Bot/Web update. Local schema remains **10**, hosted sync remains **1**, and Portal Action protocol remains **25**.

1. Back up the live player database and preserve `.env`, Twitch token storage, hosted secrets, and persistent-disk state.
2. Stop the Bot cleanly.
3. Apply the **Alpha 1 → Alpha 2 Bot patch** or replace Bot source with the full Alpha 2 package while preserving private/runtime state.
4. Apply the **Alpha 1 Hotfix 2 → Alpha 2 Web patch** or deploy the full Alpha 2 Web package.
5. Start the Bot and confirm no schema migration runs; schema must remain **10**.
6. Redeploy/restart the hosted Web service.
7. Verify `!cgversion` reports `1.5.0-trails-raids-a2`.
8. Verify `/api/health` reports Web/frontend `1.5.0-trails-raids-a2`, hosted sync schema **1**, and Portal Action protocol **25**.
9. Stage **Shiva** and confirm the Trial reports **Diamond Throne**. Verify Frostbrand Cleave → Icebound Mirrors → Diamond Aegis behavior.
10. During Mirrors, confirm boss-directed damage reduces Mirror HP while Shiva HP does not move until the adds are cleared.
11. Meet Diamond Aegis's Break target and confirm the next round is a Stagger vulnerability window with no Shiva response.
12. Confirm Ifrit — Inferno Crucible, Dungeons, Expeditions, Fellowship, inventories, records, and existing player progression remain intact.

No player reset, OAuth/environment change, new environment variable, or database migration is required.

# Upgrade Guide — Crystal Guild v1.5.0 Trails & Raids Alpha 3

Baseline: **v1.5.0 Trails & Raids Alpha 2**. Alpha 3 is a paired Bot/Web update. Local schema remains **10**, hosted sync remains **1**, and Portal Action protocol remains **25**.

1. Back up the live player database and persistent Twitch/token state.
2. Stop the Bot cleanly.
3. Apply the **Alpha 2 → Alpha 3 Bot patch** or replace Bot source with the full Alpha 3 package while preserving `.env`, database files, token storage, and persistent-disk state.
4. Apply the **Alpha 2 → Alpha 3 Web patch** or deploy the full Alpha 3 Web package.
5. Start the Bot and redeploy/restart the hosted Web service. No database migration should run.
6. Verify `!cgversion` reports `1.5.0-trails-raids-a3`.
7. Verify `/api/health` reports Web/frontend `1.5.0-trails-raids-a3`, hosted sync schema **1**, and Portal Action protocol **25**.
8. Open Adventure Board → Trial & Raid Board. Confirm the disclosure hand points right when closed and down when open, and the remembered state survives a refresh.
9. Stage **Ramuh** and confirm the Trial reports **Judgment Spire**. Verify Rolling Thunder → Levinshare → Judgment Charge behavior.
10. During Levinshare, have at least one non-marked raider Defend and confirm the hit is shared.
11. During Judgment Charge, coordinate Defend actions and confirm meeting the Grounding target weakens Judgment Bolt.
12. Confirm Ifrit — Inferno Crucible, Shiva — Diamond Throne, unscripted raids, Dungeons, Expeditions, Fellowship, inventories, records, and existing player progression remain intact.

No player reset, OAuth/environment change, new environment variable, or schema migration is required.

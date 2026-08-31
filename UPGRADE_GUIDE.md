# Upgrade Guide — v1.5.0 Trails & Raids RC1

Baseline: **v1.5.0 Trails & Raids Beta 3** with matching Beta 3 Web + Bot.

1. Back up the live player database and persistent Twitch/token data as usual.
2. Stop the Bot cleanly.
3. Apply the **Beta 3 → RC1 Bot patch**, or replace Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the matching **Beta 3 → RC1 Web patch**, or replace the Web source.
5. Start the Bot and confirm `!cgversion` reports `1.5.0-trails-raids-rc1` with local schema **10** and Portal protocol **25**.
6. Redeploy/restart the hosted Web service and confirm `/api/health` reports Web/frontend `1.5.0-trails-raids-rc1`, hosted sync schema **1**, and Portal protocol **25**.
7. Open **Adventure Board → Trial & Raid Board** and verify the seven-Trial catalog, Chronicle, repeat mastery, Last Trial Result, and remembered collapse state remain intact.
8. During a staging Trial, queue actions from several raiders and confirm **Round Readiness** counts only the current run/upcoming round.
9. Confirm a stale previous-round or wrong-run queued action does not increase the ready count and safely becomes the normal auto-Attack if it reaches resolution.
10. Confirm Beta 3 cross-connection action merging and exact timer-tick stale-state protection remain green.
11. Resolve a Trial and verify Beta 2 settlement receipts still prevent duplicate rewards/records on replay.
12. Verify existing players, inventories, Fellowship, Expeditions, Dungeons, boss clears, Trial Chronicle records, repeat mastery, and all seven Trial encounters remain intact.

No database migration, player reset, OAuth/environment change, or new environment variable is required. An in-progress Beta 3 Raid checkpoint is compatible in place.

# Upgrade Guide — v1.5.0 Trails & Raids Beta 2

Baseline: **v1.5.0 Trails & Raids Beta 1** with matching Beta 1 Web + Bot.

1. Back up the live player database and persistent Twitch/token data as usual.
2. Stop the Bot cleanly.
3. Apply the **Beta 1 → Beta 2 Bot patch**, or replace Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the matching **Beta 1 → Beta 2 Web patch**, or replace the Web source.
5. Start the Bot and confirm `!cgversion` reports `1.5.0-trails-raids-b2` with local schema **10** and Portal protocol **25**.
6. Redeploy/restart the hosted Web service and confirm `/api/health` reports Web/frontend `1.5.0-trails-raids-b2`, hosted sync schema **1**, and Portal protocol **25**.
7. Open **Adventure Board → Trial & Raid Board** and confirm existing Trial Chronicle clears/records are intact, repeat-clear mastery is visible, and a Trial with existing clears shows the appropriate next milestone.
8. During a staging Trial, confirm the live Board reports **Actions X / Y queued** without exposing player IDs or internal mechanic targets.
9. Resolve a staging Trial and confirm **Last Trial Result** remains visible after the encounter, while rewards and Chronicle metrics settle once.
10. If practical in staging, restart/reconnect around an active Raid and verify the run resumes normally; a duplicate settlement attempt must replay the committed result without applying rewards again.
11. Verify existing players, inventories, Fellowship, Expeditions, Dungeons, boss clears, Trial Chronicle records, and all seven Trial encounters remain intact.

No database migration, player reset, OAuth/environment change, or new environment variable is required. A Raid already active at upgrade receives a stable compatibility settlement identity automatically.

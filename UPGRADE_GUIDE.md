# Upgrade Guide — v1.5.0 Trails & Raids Beta 3

Baseline: **v1.5.0 Trails & Raids Beta 2** with matching Beta 2 Web + Bot.

1. Back up the live player database and persistent Twitch/token data as usual.
2. Stop the Bot cleanly.
3. Apply the **Beta 2 → Beta 3 Bot patch**, or replace Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the matching **Beta 2 → Beta 3 Web patch**, or replace the Web source.
5. Start the Bot and confirm `!cgversion` reports `1.5.0-trails-raids-b3` with local schema **10** and Portal protocol **25**.
6. Redeploy/restart the hosted Web service and confirm `/api/health` reports Web/frontend `1.5.0-trails-raids-b3`, hosted sync schema **1**, and Portal protocol **25**.
7. Open **Adventure Board → Trial & Raid Board** and confirm the Trial Chronicle, repeat-clear mastery, and remembered collapse state remain intact.
8. During a staging Trial, queue actions from multiple raiders and confirm the **Round Readiness** strip updates queued/waiting counts without exposing player IDs or internal run IDs.
9. If practical in staging, briefly overlap/reconnect two Bot processes against a test copy of the same database. Different raiders' queued actions in the same round must merge rather than overwrite one another.
10. Confirm a stale timer snapshot cannot advance an already-resolved round a second time, and that Beta 2 exactly-once settlement behavior still prevents duplicate rewards at victory/wipe.
11. Resolve a staging Trial and confirm **Last Trial Result** shows contribution score, role, damage, healing, and mitigation for the leading contributors.
12. Verify existing players, inventories, Fellowship, Expeditions, Dungeons, boss clears, Trial Chronicle records, repeat mastery, and all seven Trial encounters remain intact.

No database migration, player reset, OAuth/environment change, or new environment variable is required. An active Beta 2 Raid checkpoint and one already-queued unstamped Beta 2 action are accepted automatically by Beta 3.

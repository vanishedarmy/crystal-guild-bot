# Upgrade Guide — Crystal Guild v1.4.0 — Dungeons & Delves Beta 3

Expected live baseline: **Beta 2 Web + Beta 1 Bot**.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the **Beta 1 Bot → Beta 3 Bot patch**, or replace the Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the **Beta 2 Web → Beta 3 Web patch** or full Beta 3 Web package.
5. Restart/redeploy Bot and Web together.
6. Verify `!cgversion` reports `1.4.0-dungeons-b3` with local schema **10**.
7. Verify `/api/health` reports Web/frontend `1.4.0-dungeons-b3`, hosted sync schema **1**, and Portal Action protocol **25**.
8. Open one Dungeon state in multiple tabs/connections; after one action advances the run, confirm the older state fails closed.
9. Retry the exact same pending action ID and confirm the original committed result is replayed rather than resolved twice.
10. Refresh/reconnect during an active Dungeon and confirm run, chamber, revision, Cache, resources, and pending route effects persist.
11. Confirm all four Dungeons, completed records, first-clear state, Guild/Fellowship data, Expeditions, inventory, and player progression remain intact.

No database migration, player reset, OAuth change, protocol change, or new environment variable is required. Protocol remains **25**, but deploy Beta 3 Web and Bot together to receive the complete hardening pass.

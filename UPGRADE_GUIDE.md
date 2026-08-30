# Upgrade Guide — Crystal Guild v1.4.0 — Dungeons & Delves Beta 1

Baseline: **v1.4.0 Dungeons & Delves Alpha 4 Web + Bot**.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the **Alpha 4 → Beta 1 Bot patch**, or replace the Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the matching **Alpha 4 → Beta 1 Web patch** or full Beta 1 Web package.
5. Restart/redeploy Bot and Web together.
6. Verify `!cgversion` reports `1.4.0-dungeons-b1` with local schema **10**.
7. Verify `/api/health` reports Web/frontend `1.4.0-dungeons-b1`, hosted sync schema **1**, and Portal Action protocol **25**.
8. Open an active Dungeon in two browser tabs. Advance one combat round in the first tab and confirm the older tab cannot spend another action against the newer revision.
9. Refresh/reconnect during a Dungeon and confirm the current run/chamber/revision and pending route effects are preserved.
10. Confirm all four Dungeons, existing clear records, first-clear state, Guild/Fellowship data, Expeditions, inventory, and player progression remain intact.

No database migration, player reset, OAuth change, or new environment variable is required from Alpha 4. Protocol 25 requires the matching Beta 1 Web and Bot to be deployed together.

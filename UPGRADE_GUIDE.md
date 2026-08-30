# Upgrade Guide — v1.4.0 Dungeons & Delves Alpha 3

Baseline: **Alpha 2 Bot + Alpha 2 Web Hotfix 1**.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the **Alpha 2 → Alpha 3 Bot patch**, or replace the Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the matching **Alpha 2 Web Hotfix 1 → Alpha 3 Web patch** or full Alpha 3 Web package.
5. Restart/redeploy Bot and Web.
6. Verify `!cgversion` reports `1.4.0-dungeons-a3` with local schema **10**.
7. Verify `/api/health` reports Web/frontend `1.4.0-dungeons-a3`, hosted sync schema **1**, and Portal Action protocol **24**.
8. Open Dungeon Board and confirm Forgotten Ossuary, Emberglass Foundry, and Whiteglass Bastion appear with correct unlock state.
9. Spot-check a Crossroads choice and confirm any forward route effect appears in the active run before it is consumed by the relevant later room.
10. Existing Alpha 2 Dungeon runs and records remain compatible.

No database migration, player reset, OAuth change, or new environment variable is required.

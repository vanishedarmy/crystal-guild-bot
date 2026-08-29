# Upgrade Guide — v1.3.0 Guild Expansion RC1

Baseline: **v1.3.0 Guild Expansion Beta 3 Web + Bot**.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the Beta 3 → RC1 Bot patch, or replace the Bot source with the full RC1 Bot package while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the Beta 3 → RC1 Web patch or the full RC1 Web package.
5. Restart the Bot.
6. Verify `!cgversion` reports `1.3.0-guild-expansion-rc1`.
7. Verify `/api/health` reports Web/frontend `1.3.0-guild-expansion-rc1`, hosted sync schema **1**, and Portal Action protocol **22**.
8. Open Fellowship and verify the current project, Airship state, Weekly Orders, Guild Legacy, and existing construction/mission history are intact.
9. Open the Player Guide → Fellowship/Expeditions references and confirm major Guild facilities use **Lv.** terminology.
10. Test one normal Fellowship contribution and, if practical, one stale-tab contribution after switching projects to confirm Beta 3 safety behavior remains intact.

No database migration is required from Beta 3; local schema **9** remains current. Existing facilities, project progress, Weekly Orders, Workshop services, Airship state/upgrades/history, Guild Legacy, Expeditions, inventories, and character progression are preserved. No player reset, OAuth change, or new environment variable is required.

# Upgrade Guide — v1.3.0 Guild Expansion RC2

Baseline: **v1.3.0 Guild Expansion RC1 Web + Bot**.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the RC1 → RC2 Bot patch, or replace the Bot source with the full RC2 Bot package while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the RC1 → RC2 Web patch or the full RC2 Web package.
5. Restart the Bot and redeploy/restart the hosted Web service.
6. Verify `!cgversion` reports `1.3.0-guild-expansion-rc2`.
7. Verify `/api/health` reports Web/frontend `1.3.0-guild-expansion-rc2`, hosted sync schema **1**, and Portal Action protocol **22**.
8. Open Fellowship and verify the current project, Airship state, Weekly Orders, Guild Legacy, construction/mission history, and current facilities are intact.
9. Open What's New / Player Guide and confirm the public release identifies **Guild Expansion RC2** without release-engineering jargon in gameplay guidance.
10. Test one normal Fellowship contribution and, if practical, one stale-tab contribution after switching projects.

No database migration is required from RC1; local schema **9** remains current. Existing facilities, project progress, Weekly Orders, Workshop services, Airship state/upgrades/history, Guild Legacy, Expeditions, Chocobos, inventories, and character progression are preserved. No player reset, OAuth change, or new environment variable is required.

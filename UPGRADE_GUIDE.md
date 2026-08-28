# Upgrade Guide — Crystal Guild v1.2.0 Expeditions Alpha 3

## Supported direct baseline
- **Web:** Expeditions Alpha 2 Hotfix 3 — Scenic Backdrops
- **Bot:** Expeditions Alpha 2

## Upgrade
1. Stop the Bot.
2. Back up the current database and persistent Twitch token data as normal.
3. Apply the **A2 → A3 Bot patch** or replace application files with the full Alpha 3 Bot package, preserving `.env`, database files, and token storage.
4. Deploy the **A2H3 → A3 Web patch** or the full Alpha 3 Web package.
5. Start the Bot and confirm `!cgversion` reports `1.2.0-expeditions-a3`, local schema **8**, and Portal Action protocol **20**.
6. Hard-refresh the Portal once and open **Adventure Board → Distant Expedition Board**. Confirm the new **Expedition Atlas** appears.
7. Existing regional exploration should be unchanged. A mastered region with a prior boss clear should expose **Launch Legendary Contract** immediately.

No database migration, player reset, OAuth reconfiguration, hosted sync change, or new environment variable is required. Deploy the paired Web/Bot update because Alpha 3 adds the new `legendary` Expedition launch depth to the existing protocol-20 action shape.

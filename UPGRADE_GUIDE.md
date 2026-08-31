# Upgrade Guide — v1.6.0 Gold Saucer Alpha 4

Supported baseline: **v1.6.0 Gold Saucer Alpha 3 — MGP**.

1. Preserve the live `crystal_guild.db`, `.env`, Twitch token storage, hosted secrets, and persistent-disk state.
2. Deploy the matching Alpha 4 Bot and Web packages together because Portal Action protocol advances to **28**.
3. Restart/redeploy both services.
4. Verify `!cgversion` reports `1.6.0-gold-saucer-a4` and Portal Action protocol **28**.
5. Verify local DB schema remains **12** and hosted sync remains **1**.
6. Open Gold Saucer → Chocobo Racing. A player with no registered Chocobo should see the Stable requirement; a registered companion should show name, portrait, Bond level, course gates, and daily race entries.
7. Run one race and confirm the MGP balance changes exactly by `-entry + payout`, the race appears once in Recent Activity, and the Saucer Ledger increments once.

## Data safety
Alpha 4 introduces **no database migration**. Races resolve immediately and use the existing `gold_saucer_history` ledger, so schema 12 remains sufficient. Existing MGP, Gil, inventory, Fellowship, Chocobo, Expedition, Dungeon, Trial/Raid, Relic, Title, Mini Cactpot, Crystal Slots, Monster Toss, and Prize Counter state is preserved.

## Deployment note
Alpha 3 Web/Bot protocol 27 does not understand `CHOCOBO_RACE`; deploy the Alpha 4 Bot and Web as a matched protocol-28 pair rather than leaving one side on Alpha 3.

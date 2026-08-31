# Upgrade Guide — v1.6.0 Gold Saucer Alpha 3

Supported baseline: **v1.6.0 Gold Saucer Alpha 2 Hotfix 2 / Canonical Baseline**.

1. Preserve the live `crystal_guild.db`, `.env`, Twitch token storage, hosted secrets, and persistent-disk state.
2. Replace the Bot source with the Alpha 3 Bot package.
3. Restart the Bot worker.
4. Verify `!cgversion` reports `1.6.0-gold-saucer-a3`.
5. Verify the local DB remains schema **12**, hosted sync remains **1**, and Portal Action protocol remains **27**.
6. Open Gold Saucer and verify the existing balance is shown unchanged as **MGP**.
7. Verify Mini Cactpot, Crystal Slots, Monster Toss, and Prize Counter all use MGP wording while retaining their existing costs and payouts.

## Data safety
There is **no schema migration** in Alpha 3. The physical `player_gold_saucer.points` column remains the authoritative stored balance and is re-exposed as canonical `mgp` in the Portal state. Existing characters, Gil, inventory, Fellowship, Chocobos, Expeditions, Dungeons, Trials/Raids, Relics, Titles, Gold Saucer balance, Prize Counter purchases, and records are preserved.

## Web compatibility
Portal Action protocol remains **27**, so the Alpha 2 Hotfix 2 relay remains action-compatible. The Alpha 3 state also retains legacy `points` aliases. A frontend source update is still needed for any UI text that hardcodes SP/Saucer Points rather than reading the currency metadata.

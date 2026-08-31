# Web Sync — Gold Saucer Alpha 2

Gold Saucer Alpha 2 keeps hosted sync schema **1** and advances Portal Action protocol to **27**. The authenticated relay adds bounded `MONSTER_TOSS_START` and `MONSTER_TOSS_THROW` actions while the local Bot remains authoritative for SP balances, persistent Monster Toss state, Mini Cactpot, Crystal Slots, replay receipts, and records.

Deploy matching runtime `1.6.0-gold-saucer-a2` Bot and Web together. Preserve existing `PORTAL_PUBLIC_URL`, `PORTAL_SYNC_KEY`, Twitch tokens, and live database state. No new environment variable is required.

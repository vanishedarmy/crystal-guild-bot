# Crystal Guild v1.6.0 — Gold Saucer Alpha 1 Web Sync

Gold Saucer Alpha 1 keeps hosted sync schema **1** and advances Portal Action protocol to **26**. The authenticated action relay adds bounded Gold Saucer state/game actions while the local Bot remains authoritative for SP balances, Mini Cactpot tickets, Crystal Slots results, cooldowns, replay receipts, and records.

Deploy matching runtime `1.6.0-gold-saucer-a1` Bot and Web together. Preserve existing `PORTAL_PUBLIC_URL`, `PORTAL_SYNC_KEY`, Twitch tokens, and live database state. No new environment variable is required.

The existing Dungeon, Expedition, Fellowship, Shop, Recovery, Chocobo, and Trial/Raid contracts remain compatible. Raid Overlay state stays sanitized and read-only on the Portal.

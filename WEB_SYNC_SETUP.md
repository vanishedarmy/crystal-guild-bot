# Web Sync — Crystal Guild v1.6.0 Gold Saucer RC1 — Chocobo Racing

Gold Saucer RC1 keeps hosted sync schema **1** and advances Portal Action protocol to **28** for `CHOCOBO_RACE`. The local Bot remains authoritative for MGP balances, Mini Cactpot, Crystal Slots, Monster Toss, Chocobo Racing, Prize Counter purchases, replay receipts, and records.

The Gold Saucer state now exposes canonical `mgp`, `welcome_mgp`, `daily_allowance_mgp`, `account.mgp`, `records.net_mgp`, `currency_name: "MGP"`, and `currency_code: "MGP"` fields. Legacy Alpha 2 `points` fields remain available as compatibility aliases.

No new environment variable or action route is required. Preserve existing `PORTAL_PUBLIC_URL`, `PORTAL_SYNC_KEY`, Twitch tokens, secrets, and live database state.

Deploy the matching Alpha 4 Web with this Bot. Alpha 3 Web/Bot protocol 27 does not understand `CHOCOBO_RACE`, so the Alpha 4 Bot and Web should be deployed as a matched protocol-28 pair.

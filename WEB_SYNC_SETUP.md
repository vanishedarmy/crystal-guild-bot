# Web Sync — Crystal Guild v1.6.0 Gold Saucer Alpha 3 MGP Contract

Gold Saucer Alpha 3 keeps hosted sync schema **1** and Portal Action protocol **27** unchanged. The local Bot remains authoritative for MGP balances, Mini Cactpot, Crystal Slots, Monster Toss, Prize Counter purchases, replay receipts, and records.

The Gold Saucer state now exposes canonical `mgp`, `welcome_mgp`, `daily_allowance_mgp`, `account.mgp`, `records.net_mgp`, `currency_name: "MGP"`, and `currency_code: "MGP"` fields. Legacy Alpha 2 `points` fields remain available as compatibility aliases.

No new environment variable or action route is required. Preserve existing `PORTAL_PUBLIC_URL`, `PORTAL_SYNC_KEY`, Twitch tokens, secrets, and live database state.

A frontend source update is required only where the UI hardcodes the old SP/Saucer Points text. The canonical Alpha 2 Hotfix 2 Web archive was not present in the working Library for this package, so no Alpha 3 Web build is included here.

# Web Sync — Crystal Guild v1.9.0 Alpha 5 Title Status Hardening

Hosted sync schema remains **1**. Portal Action protocol is **36**. The Trading Post adds `TRADING_POST_STATE`, `TRADING_POST_LIST`, `TRADING_POST_BUY`, and `TRADING_POST_CANCEL` to the established authoritative action relay; no sync-key or environment change is required.

Deploy the matching v1.9.0 Alpha 1 Bot and Web together. The Bot remains authoritative for inventory, Gil, listings, expiry returns, taxes, and seller payouts. Public Fellowship snapshots now expose the Trading Post service state without exposing private player inventory.

# Portal Actions — Hotfix 5 Gear Favorites Authority Fix

Portal Action protocol is **33**. The new `SET_GEAR_FAVORITES` action persists the signed-in player's complete equipment Favorite set in the authoritative Bot database. It is preference-only: it does not reset Long Rest inactivity, does not affect combat, and uses normal action idempotency/replay receipts.

Deploy the protocol-33 Bot and Web together. Existing OAuth, sync key, and environment configuration remain unchanged.

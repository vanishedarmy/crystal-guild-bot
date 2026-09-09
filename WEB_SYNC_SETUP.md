# Web Sync — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 5 Gear Favorites Authority Fix

Hosted sync schema remains **1** and Portal Action protocol is **33**. The normal private player snapshot now includes `inventory.favorite_item_ids`; the hosted public inventory endpoint strips that field, while the authenticated owner Favorites endpoint uses it as canonical synced state.

Deploy the matching v1.7.1 Bot and Web together. No sync-key or environment change is required.

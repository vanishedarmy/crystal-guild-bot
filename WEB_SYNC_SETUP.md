# Hosted Web Sync — Alpha 8

Hosted sync schema remains **1**; authoritative Portal Action protocol is **37**. Run the matching `1.9.0-seasonal-events-alpha8` Bot and Web together. The Bot remains authoritative for combat, inventory, Gil, Trading Post, trophies and seasonal event progress/shop claims.

Maintain the existing private sync key and `PORTAL_PUBLIC_URL` configuration; no new environment variable or hosted sync migration is required for this cleanup hotfix. The live local database must be at schema **21**.

# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 3c

Hotfix 3c advances from the Hotfix 3b baseline. It preserves the Raid action repair, Rally Venture consolidation, subscriber-aware Daily system, and all existing schema/protocol contracts while correcting lifetime Gil-spent achievement accounting.

`Stimulating the Economy` and other transaction-derived record conditions now read the authoritative `transactions` ledger instead of relying on a stale cached record value. Successful shop purchases, Chocobo Registration Writ purchases, and Fellowship contributions also run achievement checks immediately.

Runtime `1.1.14-cloud-continuity-h3c` · DB schema 4 · hosted sync schema 1 · Portal Action protocol 12 · Twitch prefix `!`.

No new Render secret, database migration, player reset, or OAuth scope is introduced. The existing subscriber feature still requires `channel:read:subscriptions` if it was not already authorized.

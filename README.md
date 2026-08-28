# Crystal Guild v1.2.0 — Expeditions Alpha 5

Expeditions Alpha 5 adds automatic Chocobo Expedition Specialization, Bond-scaled specialty tiers, Expedition accomplishment records, and modest Hunt Seal completion stipends. Alpha 4 Regional Discovery, the Expedition Atlas, Regional Boss Contracts, Legendary Contracts, and permanent Mastery remain intact.

Runtime `1.2.0-expeditions-a5` · local DB schema **8** · hosted sync schema **1** · hosted sync compatibility `1.1.15-wayfarer` · Portal Action protocol **20** · Twitch prefix `!`.


Latest Hunt timing: C 15m · B 30m · A 2h · S 5h. Hunts resolve autonomously with no round-by-round chat input.

## RC1 Hotfix 9 — Raid Timing & Field Support
Rally Venture now uses 60s rallies and 30s combat rounds; Raids use 90s rallies and 60s rounds. Streamer Portal boss spawns announce their rally in Twitch chat while LIVE, and field recovery items may support another adventurer outside battle while LIVE. Portal Action protocol is 19; DB schema remains 7.

## RC1 Hotfix 7 — Streamer Inventory Admin
Adds owner-only `!additem <player> | <item> | [quantity]` and `!removeitem <player> | <item> | [quantity]`, plus matching authenticated Streamer Portal controls. Inventory changes use the authoritative item catalog, reject over-removal, ledger every delta, auto-unequip the final removed equipped copy, and are replay-safe for Portal acknowledgement retries. Local DB schema remains 7; Portal Action protocol advances to 18.

## RC1 Hotfix 6 — Persistent Adventure Results
Adds a durable per-player Adventure Board result inbox. Portal Solo Venture outcomes and Portal-origin timed Hunt results persist across page changes, time away, and Bot restarts until the player confirms the individual card. Hotfix 5 Streamer Controls and LIVE-only notable Portal announcements remain intact. Deploy with the matching Web build because local DB schema 7 and Portal Action protocol 17 are required.

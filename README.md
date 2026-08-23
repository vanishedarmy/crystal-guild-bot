# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 3

Hotfix 3 restores explicit Raid round actions while preserving the Cloud Continuity/stream-presence/Daily subscriber systems already in v1.1.14.

During an active Raid, participants can queue `!attack`, `!ability <name> [target]`, `!defend`, or `!use <item> [target]`. The last queued choice before the round closes is used; no input defaults to Attack. MP/AP, items, status effects, healing, Defend, and winning-round resource persistence are handled by the authoritative Raid engine.

Recovered pre-Hotfix-3 active Raid state is hydrated on demand without changing the database schema.

Runtime `1.1.14-cloud-continuity-h3` · DB schema 4 · hosted sync schema 1 · Portal Action protocol 12 · Twitch prefix `!`.

No new Render secret, database migration, player reset, or OAuth scope is introduced. The existing Hotfix 2 subscriber feature still requires `channel:read:subscriptions` if not already authorized.

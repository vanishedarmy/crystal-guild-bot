Crystal Guild v1.3.0 — Guild Expansion Beta 3 Bot
Runtime: 1.3.0-guild-expansion-b3
DB schema: 9
Hosted sync schema: 1
Portal Action protocol: 22
Twitch prefix: !

Beta 3 is the shared-state hardening pass. It protects simultaneous Fellowship contributions, stale browser tabs, project switching, Portal retries, and Guild Airship launch/return settlement while preserving Beta 1 balance and Beta 2 UX. Deploy the matching Beta 3 Web because Portal Action protocol 22 binds contributions to the project the player actually had open.

No database migration is required; schema 9 remains current.

Preserve .env, database files, Twitch tokens, and persistent storage when upgrading.

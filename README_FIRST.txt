Crystal Guild v1.9.0 Alpha 10 — Records & Moments
Runtime/frontend: 1.9.0-records-moments-alpha10
Local DB schema 23 | Hosted sync schema 1 | Portal Action protocol 37

The existing Records page now has 15 expanded personal bests and 12 unusual Moments, with seven secrets, cosmetic Titles, separate badge art and two exceptional Hall of Trophies displays. Original career, Trial, rivalry and boss records remain intact; qualifying historical Gil purchases and paid Mini Cactpot streaks can be recognized only when persisted evidence proves them.

Preserve existing player data, Bestiary discoveries, trophy ownership, seasonal editions, credentials and runtime volumes. An existing schema-22 database upgrades automatically to schema 23 with a verified pre-migration backup. Never run an old schema-22 Bot against a migrated database without restoring the matching old database.

Deploy matching Alpha 10 Bot + Web together. The Web source does not contain node_modules or a production dist. Install pinned dependencies, build Vite, and smoke-test the Portal on staging before replacing the live service. Halloween stays disabled until the owner activates it.

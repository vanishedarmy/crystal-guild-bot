Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 5 — Gear Favorites Authority Fix
Bot runtime: 1.7.1-resynthesis-a2h5
Paired Web frontend: 1.7.1-resynthesis-a2h5
Local DB schema: 16
Hosted sync schema: 1
Portal Action protocol: 33
Command prefix: !

Deploy Bot and Web together. Gear Favorites now persist in the authoritative Crystal Guild player database and sync through the normal player snapshot, eliminating device/browser-local divergence. The upgrade performs an automatic in-place schema 15 → 16 migration with a verified pre-migration backup. Preserve the live database, secrets, tokens, and persistent runtime files; no player reset is performed.

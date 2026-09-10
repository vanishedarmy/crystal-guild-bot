Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 5 — HTTP Response Efficiency
Bot runtime: 1.7.1-resynthesis-a2h5
Paired Web frontend: 1.7.1-resynthesis-a2h5
Local DB schema: 16
Hosted sync schema: 1
Portal Action protocol: 33
Command prefix: !

Deploy Bot and Web together. This transport-focused hotfix reduces idle HTTP response count and repeated JSON payload bytes through long-poll Portal actions, manifest-first sync heartbeats, and slower recovery polling. Preserve the live database, secrets, tokens, and persistent runtime files. No schema migration or player reset is performed.

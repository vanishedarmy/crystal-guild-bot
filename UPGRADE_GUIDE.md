# Upgrade to v1.7.0 Retainer Service Alpha 2

Upgrade Bot and Web together. Alpha 2 uses runtime `1.7.0-retainer-a2`, local schema **15**, hosted sync **1**, and Portal Action protocol **31**.

The schema 14→15 migration is additive and creates `retainer_history`. Existing player progression, inventory, Gil, MGP, Retainer Rank/EXP, and any active or returned Alpha 1 Retainer assignment are preserved. The normal verified `pre_schema_15_*.db` backup is created before migration.

`RETAINER_DISPATCH` accepts `{ "assignment": "...", "priority": "..." }`. An empty priority keeps the Alpha 1 general mixed-haul behavior. A valid priority must be a material offered by the selected assignment.

Preserve your existing database and secrets. Do not copy packaged example environment files over live credentials.

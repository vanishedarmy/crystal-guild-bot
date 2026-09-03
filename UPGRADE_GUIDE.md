# Upgrade to Crystal Guild v1.7.1 — Resynthesis Alpha 1

1. Preserve the live `crystal_guild.db`, token database, persistent storage, and environment secrets.
2. Upgrade **Bot and Web together** because Portal Action protocol advances from **31 to 32**.
3. Do not replace or reset the live database. Local schema remains **15** and hosted sync remains **1**.
4. Restart the Bot and Web after deployment.
5. Confirm the Bot reports runtime `1.7.1-resynthesis-a1` and Portal protocol **32**.
6. Confirm the Web reports runtime/frontend revision `1.7.1-resynthesis-a1`.
7. Open Blacksmith → **Resynthesize Gear** and verify the player's eligible weapon/armor list loads.

Existing active gameplay/progression state is preserved. No database migration is required, and no migration command is needed.

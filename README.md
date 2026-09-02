# Crystal Guild v1.7.0 — Production Final

Production Bot runtime: **1.7.0**. Local database schema **15**, hosted sync **1**, Portal Action protocol **31**, Twitch prefix `!`.

v1.7.0 finalizes the Retainer Service and Moogle Emporium Annex feature line, including the cloud-storage startup hardening required for Render. Startup backups are pruned before copying, retained backups are capped, failed partial copies are removed, and insufficient free space no longer prevents the Bot from starting.

Preserve the existing live database, token database, persistent state, and secrets when upgrading. No schema migration is required from the final Alpha 3/Hotfix line.

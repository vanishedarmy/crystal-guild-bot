# Crystal Guild v1.7.0 — Moogle Emporium Annex Alpha 3 — Cloud Storage Hotfix 3

Hotfix 3 hardens the Render cloud worker against persistent-disk exhaustion during startup backup creation.

The previous cloud path retained five startup database copies and removed old copies only after a new backup completed. On a small persistent disk this could deadlock startup: the existing database plus retained backups could leave too little free space for the next copy, so the backup failed before retention cleanup was reached.

Hotfix 3 now prunes startup-backup history before the new copy begins, retains at most two startup backups, reserves 64 MiB of free disk space, removes abandoned partial copies, and verifies each completed backup with SQLite `PRAGMA quick_check`. If a safe copy cannot fit, Crystal Guild logs a warning and continues startup without creating a new startup backup rather than entering a crash/restart loop.

Render file logging is moved to `/tmp/crystal-guild-logs` so routine rotating logs do not consume the authoritative `/var/data` disk. The database, Twitch token database, overlay state, migration backups, and all player progression remain on the persistent disk.

Bot runtime: `1.7.0-emporium-annex-a3h3`. The Web frontend is unchanged and remains `1.7.0-emporium-annex-a3h2`; it is fully compatible because local DB schema remains **15**, hosted sync remains **1**, Portal Action protocol remains **31**, and no Portal payload or gameplay contract changes.

# Cloud Storage Audit — Alpha 3 Hotfix 3

**Result: PASS — startup backup exhaustion root cause corrected.**

The failing Render trace showed two symptoms from the same condition: `sqlite3.OperationalError: database or disk is full` during `src.backup(dst)`, followed by logging `Errno 28: No space left on device`.

The prior algorithm retained five full startup copies and pruned them only after the next copy completed. On the 1 GB persistent disk, enough retained backups could consume the free space needed to create the next full database copy. Because cleanup occurred afterward, the worker could enter a permanent restart loop.

Hotfix 3 changes the storage contract:

- prune startup backups before creating the new copy;
- retain at most two completed startup copies;
- require enough free space for the current DB size plus a 64 MiB reserve;
- delete a retained startup copy if necessary to make room for the next safe copy;
- if safe space still does not exist, skip the startup backup and continue boot;
- write to a unique partial file and remove it after any failed copy;
- run `PRAGMA quick_check` before promoting a completed copy;
- move routine Render file logs to `/tmp`, outside the persistent data disk.

Automatic cleanup only targets `crystal_guild-startup-*.db` and hotfix-created partial files. It does not delete `crystal_guild.db`, Twitch tokens, overlay state, or `pre_schema_*.db` migration backups.

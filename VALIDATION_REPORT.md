# Validation Report — Crystal Guild v1.7.0 — Cloud Storage Hotfix 3

**Result: PASS**

## Release contract

- Bot runtime: `1.7.0-emporium-annex-a3h3`
- Compatible Web frontend: `1.7.0-emporium-annex-a3h2` (unchanged)
- Local DB schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **31**
- Twitch command prefix: `!`
- Baseline: Item Usage Copy Hotfix 2
- Gameplay changes: **none**

## Automated regression

- Bot: **668 / 668 PASS**
- Bot Python parse: **117 / 117 PASS**
- Compatible Web H2 baseline remains byte-identical and previously passed **544 / 544 frontend**, **61 / 61 hosted Web/API**, **15 / 15 Web Python**, **200 / 200 JS/MJS**, **8 / 8 CSS**, **843 / 843 WebP decode**, and **0 public PNGs**.

## Cloud-storage checks

**PASS.** Five retained startup-backup files are pruned before a new backup is attempted, preventing the previous create-first/prune-after deadlock.

**PASS.** Startup backup retention is capped at two completed copies.

**PASS.** A forced zero-free-space condition returns cleanly without raising `sqlite3.OperationalError`; the Bot continues startup without a new backup.

**PASS.** Abandoned partial backup files are removed.

**PASS.** Completed startup backups pass SQLite `PRAGMA quick_check` before becoming the retained backup.

**PASS.** Cloud-storage reclamation runs before Twitch/file logging initialization, allowing an already-full Render disk to free old startup backups before the first file-log write.

**PASS.** Shipping Render configuration writes rotating file logs to `/tmp/crystal-guild-logs`, not `/var/data/logs`.

The authoritative database, token database, `pre_schema_*.db` migration backups, schema, protocol, and player progression are not modified by this cleanup.

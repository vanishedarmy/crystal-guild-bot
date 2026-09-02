# Crystal Guild v1.7.0 — Moogle Emporium Annex Alpha 3

Current Bot baseline: **Cloud Storage Hotfix 3** (`1.7.0-emporium-annex-a3h3`), local DB schema **15**, hosted sync **1**, Portal Action protocol **31**, Twitch prefix `!`.

The compatible Web frontend remains **Item Usage Copy Hotfix 2** (`1.7.0-emporium-annex-a3h2`). No Web or Portal protocol change is required for this operational fix.

Hotfix 3 prevents Render persistent-disk exhaustion from trapping the Bot in a startup-backup crash loop. Startup backups are pruned before copying, capped at two retained copies, checked for sufficient free space, and cleaned up after failed partial writes. Render file logs use temporary storage rather than the authoritative `/var/data` disk.

Moogle Emporium Annex, Retainer Service, Gold Saucer, restorative item values, player progression, and all gameplay systems remain unchanged.

See `RELEASE_NOTES.md`, `UPGRADE_GUIDE.md`, and `VALIDATION_REPORT.md`.

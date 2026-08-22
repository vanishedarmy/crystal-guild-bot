# Crystal Guild v1.1.14 — Cloud Continuity Bot Release Notes

- Fellowship snapshots are resent on heartbeat for hosted Web restart recovery.
- Sanitized raid overlay state is synced to `/api/sync/overlay` and refreshed on heartbeat.
- Overlay file changes can trigger sync independently of database changes.
- Cloud in-process sync is wired to the configured `OVERLAY_STATE_PATH`.
- Render Blueprint keeps the persistent disk and removes the unsupported disk + shutdown-delay combination.
- Python 3.11-compatible `engine.py` Records rivalry string formatting is included.
- Runtime advances to `1.1.14-cloud-continuity`; DB schema 4, hosted sync schema 1, Portal Action protocol 12, gameplay balance, and `!` prefix remain unchanged.

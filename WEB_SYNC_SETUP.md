# Crystal Guild v1.1.14 — Portal Sync + Hosted Overlay

Cloud mode uses in-process Portal synchronization. The Bot sends sanitized player snapshots, Fellowship state, manifest heartbeats, and a sanitized raid-overlay snapshot to the hosted Web service using the existing `PORTAL_SYNC_KEY`.

v1.1.14 keeps hosted sync schema **1** and Portal Action protocol **12**. Fellowship and overlay snapshots are deliberately republished on heartbeat so an ephemeral Web restart can recover without a Bot restart.

No separate `run_portal_sync.bat` or `run_overlay.bat` process is needed for the cloud worker. Local mode retains the standalone tools for development/legacy operation.

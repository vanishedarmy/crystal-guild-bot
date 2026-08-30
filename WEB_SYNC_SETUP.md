# Crystal Guild v1.5.0 — Trails & Raids Alpha 2 Portal Sync + Hosted Overlay

Cloud mode uses in-process Portal synchronization. The Bot publishes sanitized player/Fellowship/adventure state and hosted overlay state using the existing `PORTAL_SYNC_KEY`.

Alpha 2 keeps hosted sync schema **1**, Portal Action protocol **25**, and the existing sync compatibility contract. No new action type or environment variable is introduced. Dungeon mutations retain exact run/chamber/revision validation and replay-safe receipts.

No separate Portal-sync or overlay process is required for the cloud worker. Local development may continue using the standalone tools.

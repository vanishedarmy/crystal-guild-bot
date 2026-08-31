# Crystal Guild v1.5.0 — Trails & Raids Beta 3 Web Sync

Beta 1 keeps hosted sync schema **1**, Portal Action protocol **25**, and the existing sync compatibility contract. No new action type or environment variable is introduced. Dungeon mutations retain exact run/chamber/revision validation and replay-safe receipts; Raid Overlay state remains sanitized and read-only on the Portal. Trial Chronicle records are exposed through the existing authenticated player-record endpoint.

Deploy matching runtime `1.5.0-trails-raids-b3` Bot and Web together. Preserve existing `PORTAL_PUBLIC_URL`, `PORTAL_SYNC_KEY`, Twitch tokens, and live database state.

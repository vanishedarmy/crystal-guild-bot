# Validation Report — Crystal Guild v1.2.0 Expeditions

## Result
**PASS — final release candidate promoted to v1.2.0 with no gameplay changes.**

## Automated regression suites
- Bot Python suite: **443 / 443 PASS**.
- Hosted Web/API Python suite: **47 / 47 PASS**.
- Frontend Node suite: **326 / 326 PASS**.
- Focused persistent-Adventure / migration hardening suite: **6 / 6 PASS**.

The Bot suite includes expected simulated Twitch/API outage and recovery warnings; those resilience scenarios pass and are not release failures.

## Release hardening retained
- Active Expeditions and persistent Solo Ventures block passive Long Rest and stream-start HP/MP/AP refreshes until the run ends.
- Persistent Solo/Expedition mutations and their replay receipts commit atomically, preventing duplicate stage/reward processing after acknowledgement retries.
- Active Expedition stage, route, Cache, Journal, resources, and pending choices survive database/engine restart.
- Representative schema **7 → 8** migration preserves character progression, Gil, HP/MP/AP, inventory, Fellowship/Chocobo state, and creates the verified pre-schema-8 backup.
- Portal Action protocol remains **20** and hosted sync schema remains **1**.

## Player-facing finalization
- Public product identity is **v1.2.0 — Expeditions** with runtime/frontend identity `1.2.0-expeditions`.
- The Player Guide Expeditions chapter contains play and usage guidance only; Alpha/Beta release-history blocks and backend/release-engineering jargon are excluded by regression coverage.
- What's New leads with the final Expeditions launch summary.
- The Bot control-panel title no longer carries the old Alpha label.
- Scene-background manifest metadata is synchronized to the final release and all live routed artwork paths resolve.

## Source / asset checks
- JS / JSX / MJS parse sweep: **174 / 174 PASS**.
- Python compile sweep: **78 / 78 PASS**.
- Explicit routed artwork references checked: **230**, missing: **0**.
- Player-facing guide jargon guard: **PASS**.
- Production Vite bundle was not run locally because the shipping source intentionally excludes `node_modules` and no local Vite executable is present. Normal hosted deployment installs the pinned frontend dependencies before building.

## Packaging verification
- RC1 → v1.2.0 Web patch: **28 changed/new files, 0 deletions**, exact reconstruction.
- RC1 → v1.2.0 Bot patch: **11 changed/new files, 0 deletions**, exact reconstruction.
- Full Web archive versus finalized Web tree: **795 / 795 files exact**.
- Full Bot archive versus finalized Bot tree: **136 / 136 files exact**.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- Final SHA-256 manifest generated after archive verification.

## Compatibility
- Bot runtime: `1.2.0-expeditions`
- Hosted Web runtime: `1.2.0-expeditions`
- Frontend asset revision: `1.2.0-expeditions`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Twitch prefix: `!`
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**

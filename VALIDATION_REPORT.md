# Crystal Guild Bot v1.1.14 — Cloud Continuity Validation Report

## Result

**PASS — Cloud Continuity Bot/Web regression and compatibility validation completed.**

## Automated validation

- Bot regression: **322 / 322 PASS**
- Hosted Portal/API regression: **39 / 39 PASS**
- Frontend source/unit regression: **146 / 146 PASS**
- Python 3.11 grammar parse: **67 Python files PASS**
- Frontend JS/JSX parser/transpile sweep: **49 source files PASS**
- Non-JSX JavaScript `node --check`: **PASS**
- Synthetic stress: **1,000 players / 10,000 operations / 4 Portal readers PASS**
  - elapsed: 15.03 s
  - throughput: 665.4 ops/s
  - Portal reads: 7,208
  - ledger rows: 12,112
  - SQLite quick-check failures: 0
  - foreign-key violations: 0
  - negative-Gil states: 0
  - negative-inventory states: 0
  - Portal read errors: 0
  - rollbacks: 0

## Continuity behavior verified

- Fellowship snapshot is republished on the normal heartbeat, allowing a restarted/redeployed hosted Web mirror to self-heal without a Bot restart.
- Sanitized raid overlay state is synced independently when the overlay file changes and is also republished on heartbeat.
- Hosted Web accepts the bounded overlay payload, exposes `/api/overlay/state`, and serves the transparent `/overlay` OBS route.
- Render Bot Blueprint retains `/var/data` persistence and does not include the unsupported `maxShutdownDelaySeconds` + disk combination.
- Python 3.11-compatible Records rivalry formatting is included.

## Website continuity/accessibility verified

- Shared keyboard skip navigation and focusable main-content targets are present.
- Primary navigation/actions have a 44px minimum interaction target.
- Higher-contrast preference support is present.
- Compact profile navigation is grouped by task.
- Fellowship Expedition coming-soon content is consolidated into one disclosure.
- Streamer Dashboard exposes the hosted OBS overlay and shared Crystal Guild roundel.
- Level-oriented Portal and Guide lists use explicit ascending level ordering where appropriate.
- Removed Privacy Policy phone number remains absent from the v1.1.14 source tree.

## Production-build note

A local `npm install`/Vite production build could not be completed in this sandbox because dependency installation timed out. The pinned dependency manifest is unchanged, all 146 frontend source/unit regressions passed, and all 49 JS/JSX source files were independently parsed/transpiled successfully. Render will perform the normal Vite production build from the packaged source.

## Compatibility

- Product: **Crystal Guild v1.1.14 — Cloud Continuity**
- Bot/Web runtime: **`1.1.14-cloud-continuity`**
- Frontend asset revision: **`1.1.14-continuity1`**
- Local DB schema: **4**
- Hosted sync schema: **1**
- Portal Action protocol: **12**
- Twitch prefix: **`!`**
- Database migration: **none**
- Player reset: **none**
- New Render secrets: **none**
- Twitch OAuth reauthorization: **none**

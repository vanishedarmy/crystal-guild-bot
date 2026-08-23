# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 3 Consolidated Validation

**PASS — Raid action restoration, Rally Venture layout consolidation, and selectable-control clarity certified.**

- Bot tests: **342 / 342 PASS**
- Frontend tests: **150 / 150 PASS**
- Hosted Portal/API tests: **39 / 39 PASS**
- Python grammar sweep: **72 / 72 files PASS**
- Cloud stress: **1,000 players / 10,000 operations / 4 readers PASS**
- Stress Portal reads: **8,547**
- Stress ledger rows: **12,112**
- Stress throughput: **361.8 ops/s**
- SQLite quick-check failures: **0**
- Foreign-key violations: **0**
- Negative Gil/inventory states: **0**
- Portal read errors: **0**
- Transaction rollbacks: **0**

## Hotfix 3 regression coverage

Automated coverage verifies that Raid participants can queue and resolve abilities, items, and Defend; recovered legacy Raid runtime state is hydrated before accepting actions; and the normal no-input Attack fallback remains available. The winning-round persistence path saves HP/MP/AP state before Raid cleanup.

Frontend regression coverage verifies that a live Rally Venture is embedded in the existing Rally Venture panel and that target-specific labels/readability rules remain present for selectable controls.

## Compatibility

- Runtime: `1.1.14-cloud-continuity-h3`
- Hosted sync version/snapshots: `1.1.14-cloud-continuity`
- Frontend asset revision: `1.1.14-continuity3`
- Local DB schema: 4
- Hosted sync schema: 1
- Portal Action protocol: 12
- Twitch prefix: `!`

No DB schema migration, hosted sync schema change, Portal Action protocol change, player reset, new Render secret, or new OAuth scope is introduced by Hotfix 3. Hotfix 2's `channel:read:subscriptions` broadcaster permission remains required only if subscriber-tier support has not already been authorized.

Build-environment note: the source/unit regression suite is the local frontend certification path for this package; Render continues to perform the normal production Vite dependency install/build during deployment.

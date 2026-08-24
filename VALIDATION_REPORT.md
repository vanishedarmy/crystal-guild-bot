# Crystal Guild v1.1.17 — Arsenal II Validation Report

## Source release validation

- Bot unittest suite: **377 / 377 PASS**
- Frontend Node tests: **178 / 178 PASS**
- Hosted Portal/API tests: **46 / 46 PASS**
- Python grammar/compile sweep: **75 / 75 PASS**
- JS/JSX source syntax parse: **52 / 52 PASS**
- Static game-data validation: **PASS**
- Active Battle ability catalog: **172 abilities across 18 Jobs**
  - 7 core caster Jobs: 12 abilities each
  - 11 other Jobs: 8 abilities each

## Arsenal II targeted coverage

PASS — core caster spellbooks use the new 12-step JLv progression.

PASS — every non-caster Job retains the existing six abilities and gains JLv.12/JLv.35 additions.

PASS — all 172 active abilities resolve through the existing Active Battle resource/effect path under the combat-balance suite.

PASS — off-stream autonomous Twitch announcements are suppressed; live announcements still deliver.

PASS — Adventure Board state exposes authoritative Camp recovery state and START_REST remains the mutation path.

PASS — Moogle Buy/Sell category UI, Blacksmith active view state, compact mobile header, and Streamer Overlay placement have dedicated frontend regression coverage.

## Synthetic cloud-runtime stress profile

Configuration: **1,000 players / 10,000 operations / 4 concurrent Portal readers**.

- Throughput: **554.8 ops/sec**
- Portal reads: **8,449**
- SQLite journal mode: WAL
- SQLite quick-check failures: **0**
- Foreign-key violations: **0**
- Negative Gil rows: **0**
- Negative inventory rows: **0**
- Portal read errors: **0**
- Transaction rollbacks: **0**

Result: **CLOUD RUNTIME STRESS PASS**.

## Compatibility

- Bot runtime: `1.1.17-arsenal-ii`
- Hosted Web runtime: `1.1.17-arsenal-ii`
- Frontend asset revision: `1.1.17-arsenal-ii1`
- DB schema: **5**
- Hosted sync schema: **1**
- Portal Action protocol: **14**

No database migration, reset, OAuth change, or new environment variable is required.

Package extraction/overlay verification and checksum verification are recorded after final archive generation.

## Final archive verification

The release archives were generated from the finalized source and independently extracted for verification.

- Complete archive vs finalized complete tree: **0 differences**
- Bot archive vs finalized Bot tree: **0 differences**
- Web archive vs finalized Web tree: **0 differences**
- Hotfix 6 + direct Arsenal II update overlay vs finalized tree: **0 differences**
- Tests from extracted Complete archive: **377 / 377 Bot PASS**
- Tests from extracted Complete archive: **178 / 178 frontend PASS**
- Tests from extracted Complete archive: **46 / 46 hosted Portal/API PASS**

The standalone SHA-256 manifest is generated after the final archive rebuild so its hashes describe the exact files delivered to the user.

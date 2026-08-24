# Crystal Guild v1.1.17 — Arsenal II Hotfix 4 Validation Report

## Automated validation

- Bot unittest suite: **378 / 378 PASS**
- Frontend Node tests: **187 / 187 PASS**
- Hosted Portal/API tests: **46 / 46 PASS**
- Bot + hosted Web Python compile sweep: **PASS**
- Frontend JS/JSX syntax parse: **51 files / 0 diagnostics**

## Hotfix 4 targeted coverage

PASS — Solo Venture authoritative state reports **80% Encounter / 20% Treasure** and the Portal reads those values instead of hard-coding the previous odds.

PASS — Solo Venture chest-quality bias at deeper stages remains separate from event frequency, so Stage II/III improve chest quality without silently raising the 20% published chance.

PASS — timed Hunt completion exposes a structured Portal result containing Hunt identity, outcome, mark data, post-Hunt vitals, combat totals, reward data, and automatic action-plan usage.

PASS — the Portal renders Hunt victory/failure information as a structured result card with readable reward/combat groups and keeps a compact fallback for legacy results.

PASS — duplicate Solo result summary text, duplicated current-region header copy, and repeated Rally reward explanation were removed while functional state remains visible.

PASS — shared Portal action-status areas use lower-density presentation, muted text contrast is stronger, outcome labels do not depend on color alone, disabled controls remain readable, and high-contrast/mobile reflow rules are present.

## Synthetic cloud-runtime stress profile

Configuration: **1,000 players / 10,000 operations / 4 concurrent Portal readers**.

- Throughput: **638.3 ops/sec**
- Portal reads: **9,857**
- SQLite journal mode: WAL
- SQLite quick-check failures: **0**
- Foreign-key violations: **0**
- Negative Gil rows: **0**
- Negative inventory rows: **0**
- Portal read errors: **0**
- Transaction rollbacks: **0**

Result: **CLOUD RUNTIME STRESS PASS**.

## Compatibility

- Bot runtime: `1.1.17-arsenal-ii-h4`
- Hosted Web runtime: `1.1.17-arsenal-ii-h4`
- Frontend asset revision: `1.1.17-arsenal-ii1h4`
- Local DB schema: **5**
- Hosted sync schema: **1**
- Portal Action protocol: **14**
- Twitch prefix: `!`

No database migration, player reset, OAuth change, or new environment variable is required.

## Final archive / overlay verification

The release package layout was independently extracted and compared against the finalized source tree.

- Full Bot archive vs finalized Bot tree: **0 differences**
- Full Web archive vs finalized Web tree: **0 differences**
- Complete archive vs finalized complete tree: **0 differences**
- Hotfix 3 + Bot patch overlay vs finalized Bot tree: **0 differences**
- Hotfix 3 + Web patch overlay vs finalized Web tree: **0 differences**
- Hotfix 3 + combined update overlay vs finalized complete tree: **0 differences**

The standalone SHA-256 manifest is generated only after the final archive rebuild so its hashes describe the exact delivered ZIPs.

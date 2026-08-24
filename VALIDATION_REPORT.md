# Crystal Guild v1.1.16 — Arsenal Hotfix 6 Validation Report

## Scope

Hotfix 6 changes Daily Guild Provisions from broad type/rarity inference to an explicit opt-in item pool. Special/progression items such as the Chocobo Registration Writ are not eligible.

## Daily provisions checks

PASS — Daily pool is explicit and opt-in.

PASS — `chocobo_writ`, `ancient_coin`, `goblin_medallion`, and `gigas_brace` are outside the approved pool.

PASS — every approved Daily item exists in the current item catalog, is an ordinary consumable/material, and is not marked unsellable.

PASS — a synthetic future common, low-value, unsellable special material cannot enter the pool merely by matching type/rarity/value.

PASS — orphaned Chocobo Writ inventory with no authoritative Stable purchase/timer row is removed and audit-recorded; legitimately purchased/timed Writs are preserved.

PASS — level gates for consumables, randomized quantities, subscriber-tier provision roll counts, subscriber Gil bonuses, and the 24-hour cooldown remain unchanged.

## Automated tests

- Bot: **372 / 372 PASS**
- Frontend: **171 / 171 PASS**
- Hosted Portal/API: **46 / 46 PASS**
- Python grammar/compile: **74 / 74 PASS**
- JS/JSX/MJS syntax: **103 / 103 PASS**

The Bot suite emits expected simulated outage/acknowledgement-loss warnings from resilience tests; these tests pass.

## Stress profile

PASS — 1,000 synthetic players, 10,000 gameplay/read operations, 4 concurrent Portal readers.

- Throughput: **770.7 ops/sec**
- SQLite quick-check failures: **0**
- Foreign-key violations: **0**
- Negative Gil rows: **0**
- Negative inventory rows: **0**
- Portal read errors: **0**
- Transaction rollbacks: **0**

## Compatibility

- Bot runtime: `1.1.16-arsenal-h6`
- Web runtime: `1.1.16-arsenal-h5` unchanged
- Frontend asset revision: `1.1.16-arsenal1h5` unchanged
- Local DB schema: **5** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **14** unchanged
- Twitch prefix: `!`

No database migration, player reset, OAuth change, new Render secret, or Web replacement is required.

## Package verification

PASS — the standalone Bot archive reproduces the finalized Bot tree exactly: **0 diff lines**.

PASS — the Complete archive reproduces the finalized release tree exactly: **0 diff lines**.

PASS — applying `CrystalGuild-v1.1.16-Arsenal-Hotfix6-Update-from-Hotfix5.zip` over an untouched Hotfix 5 Complete tree reproduces the finalized Hotfix 6 tree exactly: **0 diff lines**.

PASS — tests executed again from the extracted release package: **372 Bot**, **171 frontend**, **46 hosted Portal/API**.

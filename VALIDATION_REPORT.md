# Crystal Guild v1.8.0 Alpha 2 — Validation Report

## Automated suites
- `Web/frontend`: **645/645** Node unit/regression tests pass.
- `Web`: **78/78** hosted Portal/API Python tests pass.
- `Bot`: **729/729** Python tests pass.

## Merc-specific coverage
- Rebalanced fee table is authoritative in `mercenary.py`.
- Bot returns per-mission availability state/reason for all six Heroes.
- Occupied mission slots identify the contracted Hero blocking that slot.
- Progression locks remain distinct from mission eligibility and active-contract states.
- Deployment board renders open/assigned Hunt, Venture, and Raid slots.
- Available/unavailable Merc artwork still follows the live selected mission state.
- Hotfix 3 mission-scoped contract consumption remains intact.

## Build environment note
`npm run build` reaches the package script but cannot execute Vite because this extracted source workspace does not contain installed Node dependencies. The shipped source archive does not contain a prebuilt bundle, and all frontend source tests pass.

## Contract
Runtime/frontend `1.8.0-merc-a2`; schema 17; hosted sync 1; Portal protocol 34; no reset/migration.

# Hotfix 3 validation

- Mission-scoped Merc contract slots validated.
- Existing schema-17 single-slot layout upgrades in place without player reset.
- Hunt/Venture/Raid consumption remains independent.

# Validation Report — Merc Service Alpha 1 Batch 4

**PASS**

- Frontend unit/regression: **631 / 631 PASS**
- Hosted Web/API: **78 / 78 PASS**
- Bot regression: **726 / 726 PASS** plus **30 / 30 subtests**
- Focused Merc frontend (Batch 3 + Batch 4): **7 / 7 PASS**
- Focused Merc/Portal hosted actions: **17 / 17 PASS**
- Focused Merc/help Bot checks: **34 / 34 PASS**
- Merc Service remains artwork-free in Batch 4 by focused regression guard.
- Hunt Seals remain distinct from Hunt Seals in player-facing Guide/help copy.
- Current release identity is `v1.8.0 Alpha 2 — Merc Service` / `1.8.0-merc-a2`.
- Release contract remains schema **17**, hosted sync **1**, Portal protocol **34**.

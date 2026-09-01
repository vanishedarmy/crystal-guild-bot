# Validation Report — Crystal Guild v1.6.0 — Gold Saucer RC1

**PASS**

## Regression suites
- Bot: **636 / 636 PASS**
- RC1-specific hardening: included in the Bot suite (same-day entry counting, midnight-crossing Toss/Triad accounting, five-attraction freeze).

## Source / release gates
- Bot Python parse: **111 / 111 PASS**
- Database integrity / non-destructive recovery drill / synthetic stress guardrails: **PASS** through the release-readiness suite.
- Balance freeze audit: **PASS** (`reports/GOLD_SAUCER_BALANCE_AUDIT_RC1.md`).

## Focused RC1 checks
- Monster Toss consumes its daily entry at start and writes settlement history against the original `started_at`.
- Triple Triad consumes its daily entry at start and writes settlement history against the original `started_at`.
- Sessions carried over 00:00 UTC remain attached to their original entry day.
- All five planned Gold Saucer attractions report `open`.
- MGP values/economy, Triple Triad card values, Chocobo Racing tuning, schema, sync, and Portal protocol are frozen from the validated H5/H6 baseline.

Contract: runtime `1.6.0-gold-saucer-rc1`, schema **13**, hosted sync **1**, Portal protocol **29**, prefix `!`, MGP canonical.

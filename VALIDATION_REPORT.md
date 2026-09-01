# Validation Report — Crystal Guild v1.6.0 — Gold Saucer RC2

**PASS**

## Regression suites
- Bot: **641 / 641 PASS**
- RC2 balance tests: included in the Bot suite (Cactpot scale/WDL, exact Slots RTP, Monster Toss fixed-profile bound, Racing/Triad stake relationships).

## Source / release gates
- Bot Python parse: **112 / 112 PASS**
- Database integrity / non-destructive recovery drill / synthetic stress guardrails: **PASS** through the release-readiness suite.
- RC2 win/draw/loss balance audit: **PASS** (`reports/GOLD_SAUCER_BALANCE_AUDIT_RC2.md`).

## Focused RC2 checks
- Mini Cactpot random-line EV is ~36.19 MGP on a 10 MGP daily ticket; sum 6 pays 1,000 MGP.
- Mini Cactpot records net win/draw/loss against wager and preserves legacy RC1 history.
- Crystal Slots remains 87.453% theoretical return.
- Monster Toss best fixed profile remains below break-even (~85.87% return).
- Chocobo Racing remains progression-sensitive and daily-bounded.
- Triple Triad win/draw/loss stakes remain profit / exact refund / forfeited entry.
- RC1 start-day accounting hardening remains active.

Contract: runtime `1.6.0-gold-saucer-rc2`, schema **13**, hosted sync **1**, Portal protocol **29**, prefix `!`, MGP canonical.

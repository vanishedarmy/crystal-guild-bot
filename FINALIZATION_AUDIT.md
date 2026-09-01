# Crystal Guild v1.6.0 — Gold Saucer Alpha 5 Release Audit

## Alpha 5 scope
- Opens persistent, authoritative Triple Triad with a 15-card collection, saved five-card deck, three NPC tiers, daily matches, MGP settlement, and card rewards.
- Adds schema 13 using additive Triple Triad profile and match-state tables.
- Advances Portal Action protocol to 29 for `TRIAD_SET_DECK`, `TRIAD_START`, and `TRIAD_PLAY`.
- Adds Triple Triad records and two cosmetic Prize Counter titles.
- Preserves all existing MGP balances and Alpha 1–4 attraction economics.

## Frozen contract
Runtime `1.6.0-gold-saucer-a5`; local DB schema **13**; hosted sync **1**; Portal Action protocol **29**; Twitch prefix `!`.

No player reset, MGP conversion, OAuth/environment change, ordinary Gil economy change, Mini Cactpot payout change, Crystal Slots payout change, Monster Toss payout change, or Chocobo Racing balance change.

## Release gate
Validation results are recorded in `VALIDATION_REPORT.md` after the final full regression and source-integrity pass.

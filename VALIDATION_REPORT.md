# Validation Report — Crystal Guild v1.7.0 — Moogle Emporium Annex Alpha 3

**Result: PASS**

## Release contract

- Runtime/frontend revision: `1.7.0-emporium-annex-a3`
- Local DB schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **31**
- Twitch command prefix: `!`
- Baseline: verified v1.7.0 Retainer Service Alpha 2 Mobile Visual Hotfix 3
- Artwork changes: **none**

## Automated regression

- Bot: **660 / 660 PASS**
- Frontend: **543 / 543 PASS**
- Hosted Web/API: **61 / 61 PASS**
- Bot Python parse: **116 / 116 PASS**
- Web Python parse: **15 / 15 PASS**
- JS/MJS syntax: **199 / 199 PASS**
- CSS structural checks: **8 / 8 PASS**
- WebP decode: **843 / 843 PASS**
- Public PNG count: **0**

The source-only Web package does not contain installed `node_modules`, so no local Vite production-build pass is claimed.

## Alpha 3 feature checks

The Moogle Emporium Annex was verified to:

- appear as a one-time shared Fellowship construction project at **Fellowship LVL 3**;
- require **20,000 Gil**, **12 Mythril Ore**, and **20 crafted items**;
- construct the `emporium_annex` facility exactly once;
- expand personal Emporium rotations from **9 to 12** stock slots after completion;
- retain the original nine-slot category composition and fill the three Annex slots from the same eligible weighted merchandise pool without duplicates;
- preserve prices, sell values, refresh timing, item definitions, level/job eligibility, and purchase validation;
- invalidate an existing nine-item cached rotation after Annex completion so the next shop request immediately rebuilds at 12 slots;
- report Annex state and stock capacity through the existing shop/Fellowship snapshots without adding a new Portal action;
- preserve the original five-major-facility Legacy accounting while exposing the Annex as an additional public Guild facility.

## Compatibility

**PASS.** Alpha 3 remains on schema 15. Existing databases receive the new `fellowship_facilities` static row through the established idempotent facility-seeding path; no destructive migration or reset is required. Existing player progression, inventory, Gil, MGP, Fellowship progression, Retainer state/history, Gold Saucer records, adventures, and shop data remain compatible.

Portal Action protocol remains 31 and hosted sync remains 1, so the Annex uses existing state payloads rather than introducing a new action contract.

## Balance

See `MOOGLE_EMPORIUM_ANNEX_ALPHA3_BALANCE_AUDIT.md`. The Annex adds **+3 visible shop choices (+33.3%)** after a shared construction investment. It does not grant free items, alter prices, speed refreshes, or change per-pick rarity weighting. The broader rotation naturally improves the chance of seeing a desirable eligible item; that bounded convenience is the intended facility benefit.

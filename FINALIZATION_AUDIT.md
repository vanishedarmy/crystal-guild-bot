# Finalization Audit — Crystal Guild v1.7.0 Moogle Emporium Annex Alpha 3 — Item Usage Copy Hotfix 2

**Decision: PASS — canonical Alpha 3 Hotfix 2 baseline.**

## Release contract

- Runtime/frontend: `1.7.0-emporium-annex-a3h2`
- Local database schema: **15**
- Hosted sync: **1**
- Portal Action protocol: **31**
- Command prefix: `!`
- Baseline: Item Recovery Integrity Hotfix 1

## Scope freeze

Hotfix 2 is deliberately narrow:

1. Recover & Equip shows only the declared restorative effect.
2. “Effective now” and explanatory recovery jargon are removed from the item buttons.
3. Field-use success messages report only the restored amount/effect.
4. The trailing technical HP/MP/AP snapshot is removed from field-use success text.
5. Regression coverage prevents the removed wording from returning.

Restorative values, max-resource behavior, inventory consumption, battle item behavior, Moogle Emporium Annex, Retainer Service, Gold Saucer, Fellowship, Guild systems, and player progression are unchanged.

## Regression and source gates

- Bot: **664/664 PASS**
- Frontend: **544/544 PASS**
- Hosted Web/API: **61/61 PASS**
- Bot Python parse: **117/117 PASS**
- Web Python parse: **15/15 PASS**
- JS/MJS syntax: **200/200 PASS**
- CSS structural checks: **8/8 PASS**
- WebP decode: **843/843 PASS**
- Public PNG count: **0**

The source-only Web package does not contain installed `node_modules`, so no local Vite production-build pass is claimed.

## Compatibility

Schema **15**, hosted sync **1**, and Portal protocol **31** remain unchanged. Existing databases, player progression, inventories, Gil/MGP, Retainer state, Fellowship facilities, and Emporium Annex completion state are preserved.

# Validation Report — Crystal Guild v1.7.1 — Resynthesis Alpha 1

**Result: PASS**

## Release contract

- Runtime/frontend: `1.7.1-resynthesis-a1`
- Local DB schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **32**
- Twitch command prefix: `!`
- Baseline: v1.7.0 Moogle Retainer UI Hotfix 3
- Database migration: **none**

## Automated regression

- Bot: **675 / 675 PASS**
- Frontend: **561 / 561 PASS**
- Hosted Web/API: **65 / 65 PASS**
- Bot Python parse: **118 / 118 PASS**
- Web Python parse: **16 / 16 PASS**
- Combined Python parse: **134 / 134 PASS**
- JS/MJS syntax: **204 / 204 PASS**
- CSS structural checks: **8 / 8 PASS**
- WebP decode: **843 / 843 PASS**
- Public PNG count: **0**

The source-only Web package does not include installed `node_modules`, so no local Vite production-build result is claimed.

## Resynthesis checks

- Eligible state exposes weapons and armor only.
- Accessories, Relic, Artifact, unsellable/protected equipment are rejected.
- Last equipped copies are blocked until unequipped.
- Recovery previews and committed rewards are deterministic.
- Portal mutation is replay-safe and destructive confirmation is present in the Web UI.
- Duplicate forged copies do not duplicate forge-material recovery.
- Final-copy forged resynthesis grants the bounded forge bonus and clears the per-item forge row.
- Across the eligible catalog, base recovery resale value remains below the original equipment's normal direct-sale value.

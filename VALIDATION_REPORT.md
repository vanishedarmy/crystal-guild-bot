# Validation Report — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 3

**PASS**

## Release contract
- Bot runtime: `1.7.1-resynthesis-a2h3`
- Paired Web: `1.7.1-resynthesis-a2` (unchanged)
- Local DB schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **32**
- Twitch prefix: `!`

## Regression
- Bot: **686 / 686 PASS**
- Job Resource Persistence focused tests: **3 / 3 PASS**
- Frontend: **562 / 562 PASS** (unchanged Alpha 2 Web)
- Hosted Web/API: **65 / 65 PASS**

## Source / asset gates
- Bot Python AST parse: **121 / 121 PASS**
- Web Python AST parse: **16 / 16 PASS**
- JS/MJS syntax: **205 / 205 PASS**
- CSS structural checks: **8 / 8 PASS**
- WebP decode: **843 / 843 PASS**
- Public PNG count: **0**

## Resource persistence checks
- Stream-live/Long Rest refresh preserves the inactive resource family.
- Equipment normalization preserves the inactive resource family.
- One-time legacy inactive-zero repair is receipt-protected.
- Legitimately depleted zero resources remain zero after Job swaps, preventing a refill exploit.
- Job Quest H2 and Encounter Variety H1 regression coverage remains included in the Bot suite.

No database migration or player reset is required.

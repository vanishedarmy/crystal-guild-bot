# Validation Report — Crystal Guild v1.3.0 Guild Expansion Alpha 2

## Result
**PASS**

## Automated validation
- Bot unittest suite: **453 / 453 PASS**.
- Frontend Node regression suite: **331 / 331 PASS**.
- Hosted Web/API unittest suite: **47 / 47 PASS**.
- Focused Guild Expansion Alpha 2 tests: **5 / 5 PASS** (included in Bot total).
- Python source compilation: **83 / 83 PASS** across Bot + hosted Web.
- Plain JS/MJS syntax checks: **138 / 138 PASS**.
- Explicit routed artwork audit: **144 unique references checked, 0 missing**.

## Alpha 2 coverage
- Supply Drives and Guild Objectives coexist with permanent Construction projects without changing facility tiers.
- Moogle Relief Shipment can be completed through normal contribution controls and cannot pay twice.
- Activity-only objectives advance from authoritative gameplay events.
- Completed Expeditions now feed the `Chart the Frontier` Fellowship objective.
- Weekly Order contributor payouts award Gil and personal Fellowship Renown exactly once per completed Order.
- The full weekly set pays the existing +500 shared Renown and a one-time 1,000 Gil +50 personal Renown bonus to each player who helped with at least one Order.
- Existing Alpha 1 Guild facilities and v1.2 Expedition behavior remain covered by the full regression suites.
- Player-facing Fellowship/Guide copy distinguishes Construction, Supply Drives, Guild Objectives, and Weekly Order rewards without adding backend jargon.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion-a2`
- Hosted Web runtime: `1.3.0-guild-expansion-a2`
- Frontend asset revision: `1.3.0-guild-expansion-a2`
- Local DB schema: **8** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **20** unchanged
- Twitch prefix: `!` unchanged
- Database migration: **none**
- Player reset: **none**
- New environment variables: **none**

## Frontend build note
The clean shipping source intentionally does not include `node_modules`, so a local Vite production bundle was not run. The complete frontend regression suite and all plain JavaScript/module syntax checks pass against the shipping source; normal hosted deployment installs the pinned dependencies before building.

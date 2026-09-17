# Crystal Guild v1.8.0 RC1 — Merc Service Finalization Audit

**Decision: PASS.** RC1 completes the planned Merc Service lifecycle, recovery, and release-hardening pass.

## Verified changes
- Deployed Hero/slot remains unavailable from mission start through actual resolution.
- Deployed contracts cannot be cancelled or rehired mid-mission.
- Timed Hunt deployment survives runtime checkpoint/restart recovery.
- Solo Venture pre-start setup failure restores the paid Merc reservation.
- Three independent Hunt / Venture / Raid slots remain isolated during resolution.
- Alpha 2 Hunt Seal fees, Hero effects, artwork, Guide behavior, and availability rules remain intact.

## Regression result
- Frontend: **648/648 PASS**
- Hosted Web/API: **78/78 PASS**
- Bot: **733/733 PASS**

## Release contract
- Runtime/frontend: `1.8.0-merc-rc1`
- Local schema: **17**
- Hosted sync: **1**
- Portal Action protocol: **34**
- New migration: **none**
- Player reset: **none**

# Crystal Guild v1.8.0 RC1 — Validation Report

## Automated suites
- `Web/frontend`: **648/648 PASS**.
- `Web`: **78/78 hosted Portal/API tests PASS**.
- `Bot`: **733/733 Python tests PASS**.

## RC1 hardening coverage
- A matching Merc reservation becomes **Deployed** when Hunt, Venture, or Raid begins.
- Deployed Heroes and their mission slots remain unavailable until assignment resolution.
- Mid-mission cancellation and rehire are rejected.
- Timed Hunt deployment state survives runtime checkpoint/restart recovery.
- Hunt/Venture/Raid slots continue to resolve independently.
- Solo Venture pre-start setup failure restores the already-paid reservation.
- Alpha 2 Hunt Seal pricing and Hero signature effects remain unchanged.

## Compatibility
- Runtime/frontend: `1.8.0-merc-rc1`
- Local schema: **17**
- Hosted sync: **1**
- Portal Action protocol: **34**
- New migration: **none**
- Player reset: **none**

## Build environment note
The extracted source workspace does not include installed Vite dependencies, so the production bundle command is not used as a release gate here. Frontend source/unit/regression coverage is complete and all referenced source assets remain packaged.

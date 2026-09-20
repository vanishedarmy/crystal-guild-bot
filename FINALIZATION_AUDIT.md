# Crystal Guild v1.9.0 Alpha 1 — Moogle Trading Post Finalization Audit

**Decision: PASS.** The Moogle Trading Post is additive, replay-safe, migration-safe, and integrated into the existing Fellowship and Moogle Emporium architecture.

## Release contract

- Visible release: **v1.9.0 Alpha 1 — Moogle Trading Post**
- Runtime/frontend: `1.9.0-trading-post-alpha1`
- Frontend package: `1.9.0-alpha.1`
- Local database schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**
- Existing player data is preserved; no reset is required.

## Trading Post scope

- Level 1 Fellowship service project: 25,000 Gil, 3 Mythril Ore, 15 Expeditions, Fellowship LVL 1.
- 48-hour fixed-price player listings.
- 2% listing fee and 5% completed-sale tax.
- 24 active listings per seller, quantity cap 99, unit-price cap 1,000,000 Gil.
- Atomic buyer debit, seller payout, listing-state update, and item transfer.
- Automatic expired-item returns and seller cancellation returns.
- Portal idempotency/replay protection for list, buy, and cancel mutations.
- Combat mutation lock plus protected-item and equipped-last-copy safeguards.
- Full locked/open marketplace UI and dedicated generated Trading Post artwork.

## Validation

- Bot regression suite: **757 / 757 passed**.
- Web/hosted Python suite: **80 / 80 passed**.
- Python compile, JavaScript syntax, JSX parser, and JSON parse checks passed.
- Vite bundling was not run because the isolated source snapshot lacks installed frontend dependencies and dependency installation was unavailable to completion in this environment; see `VALIDATION_REPORT.md`.

## Compatibility

The feature reuses existing Fellowship project/facility patterns and the hosted Portal action queue. Hosted sync schema remains 1; only the local Bot database schema and Portal Action protocol require bumps.

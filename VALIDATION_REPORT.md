# Crystal Guild v1.3.0 — Guild Expansion Alpha 4 Validation Report

## Result
**PASS**

## Automated regression suites
- Bot unittest suite: **464 / 464 PASS**.
- Frontend Node regression suite: **338 / 338 PASS**.
- Hosted Web/API unittest suite: **47 / 47 PASS**.
- Focused Guild Airship Alpha 4 suite: **6 / 6 PASS**.

The Bot regression log includes intentional simulated outage/recovery warnings from resilience tests; those scenarios pass and are not release failures.

## Airship behavior verified
- Airship Dock Lv. 1 becomes a live construction path and unlocks the one-time Crystal Guild Airship project at the required Fellowship level.
- Completing Airship construction persists the built state and awards its shared Fellowship Renown once.
- Merchant Escort mission progress is supplied by normal Venture activity, does not pay early when the target is reached, settles at the return deadline, and cannot duplicate contributor rewards on repeated snapshot/settlement calls.
- Airship upgrade tiers change effective mission target/duration and Crystal Core Tier II unlocks Relic Recovery as designed.
- Airship upgrade construction follows the current Airship Dock tier.
- A direct **schema 8 → schema 9** migration preserves representative player/Fellowship/Workshop progress, creates all Airship tables and five Tier-0 upgrade rows, produces a verified pre-schema-9 backup, and passes SQLite quick-check.

## Persistence and replay safety
Schema 9 persists:
- Airship built/current mission state;
- mission start, return, progress, and effective target;
- Hull / Engine / Cargo Hold / Survey Array / Crystal Core tiers;
- contributing players and contribution totals;
- recent mission history and success/failure totals.

Successful mission settlement uses the existing Fellowship event ledger so the shared reward and each eligible contributor payout are replay-safe. Airship return settlement is also invoked by the normal Fellowship sync heartbeat, so a completed deployment does not depend on a new chat message to return.

## Source and asset validation
- Python compile sweep: **85 / 85 PASS**.
- JavaScript/MJS `node --check`: **139 / 139 PASS**.
- Literal routed artwork audit: **144 unique routes checked, 0 missing**.
- Alpha 4 reuses the established Crystal Guild Airship/environment art; no new artwork dependency is introduced.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion-a4`
- Hosted Web runtime: `1.3.0-guild-expansion-a4`
- Frontend asset revision: `1.3.0-guild-expansion-a4`
- Local DB schema: **9**
- Hosted sync schema: **1**
- Portal Action protocol: **21**
- Twitch prefix: `!`
- Player reset: **none**
- OAuth change: **none**
- New environment variables: **none**

## Patch/release-tree verification
- Alpha 3 → Alpha 4 Bot patch: **32 changed/new files, 0 deletions**; reconstructs the **140-file** final Bot tree exactly.
- Alpha 3 → Alpha 4 Web patch: **39 changed/new files, 0 deletions**; reconstructs the **799-file** final Web tree exactly.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations** across all six archives.
- Full Bot archive vs finalized Bot tree: **140 / 140 files exact**.
- Full Web archive vs finalized Web tree: **799 / 799 files exact**.
- Complete archive Bot/Web subtrees vs finalized source trees: **exact**.
- SHA-256 manifest verification: **PASS** for all six archives and three release documents.

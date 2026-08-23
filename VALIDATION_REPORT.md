# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 2 Validation

## Result

PASS.

## Automated validation

- Bot regression suite: **335 / 335 PASS**.
- Python compile sweep: PASS.
- Python 3.11 grammar parse: PASS as part of the consolidated source sweep.
- Synthetic cloud stress test: **1,000 players / 10,000 operations / 4 Portal readers**.
  - 0 SQLite quick-check failures
  - 0 foreign-key violations
  - 0 negative-Gil rows
  - 0 negative-inventory rows
  - 0 Portal reader errors
  - 0 rollbacks

## Hotfix 2 checks

- Randomized Daily provisions always produce at least one eligible reward roll.
- Daily consumables respect the hero's current level/shop-level availability.
- Daily crafting materials are limited to bounded common/uncommon materials; relic/artifact material rewards are excluded.
- Tier perk table is monotonic: Standard 1 roll/0%, T1 2/+10%, T2 3/+20%, T3 4/+30%.
- Twitch subscription codes `1000`, `2000`, and `3000` normalize to Tier 1/2/3.
- Gift subscriptions preserve their tier.
- Subscription lookups are cached and a missing/unauthorized broadcaster scope fails soft to standard rewards rather than blocking gameplay.
- Portal Daily resolves the Twitch tier in the authoritative Bot worker and remains replay-safe.
- OAuth helper requests `channel:read:subscriptions` only for the broadcaster token; no subscriber data or token material is exposed to the public Web service.

## Compatibility

- Runtime: `1.1.14-cloud-continuity-h2`
- DB schema: 4
- Hosted sync schema: 1
- Portal Action protocol: 12
- Twitch prefix: `!`
- Database migration: none
- Player reset: none
- New Render secrets: none
- Broadcaster OAuth reauthorization: required once to activate subscriber-tier lookup

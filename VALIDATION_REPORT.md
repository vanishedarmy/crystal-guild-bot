# Crystal Guild v1.6.0 — Gold Saucer Alpha 3 Validation Report

## Result
**PASS — Bot / authoritative gameplay package**

## Automated validation
- Full Bot regression suite: **619 / 619 PASS**.
- Alpha 3 MGP-specific tests: **4 / 4 PASS**.
- Python compile sweep: **PASS**.

## Alpha 3 MGP coverage
- Runtime reports `1.6.0-gold-saucer-a3`.
- Local DB schema remains **12** and Portal Action protocol remains **27**.
- `currency_name` and `currency_code` return **MGP**.
- Canonical `mgp`, `welcome_mgp`, `daily_allowance_mgp`, `account.mgp`, and `records.net_mgp` fields are present.
- Legacy Alpha 2 `points` aliases resolve to exactly the same values.
- A manually seeded existing Gold Saucer balance was read back unchanged through both `mgp` and `points` fields.
- Mini Cactpot and Monster Toss player-facing result messages use **MGP**.
- Streamer `!saucergrant` returns the canonical `mgp` balance while retaining `points` as a compatibility alias.
- Existing attraction costs/payouts and daily limits were not rebalanced.

## Compatibility contract
- Runtime: `1.6.0-gold-saucer-a3`
- Local DB schema: **12**
- Hosted sync schema: **1**
- Portal Action protocol: **27**
- Twitch prefix: **`!`**
- No database migration, player reset, OAuth/environment change, or new required environment variable.

## Web validation scope
The canonical Alpha 2 Hotfix 2 Web archive was not available in the working Library for this continuation, so this report does **not** claim an Alpha 3 frontend build or frontend regression pass. The Bot-side API deliberately keeps protocol 27 and legacy `points` aliases to preserve relay compatibility until the canonical Web source is available for the UI rename pass.

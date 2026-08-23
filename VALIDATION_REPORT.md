# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 3c Validation

## Certification summary

**PASS — Current Loadout clarity, authoritative Gil-spent achievement tracking, and recoverable mobile header behavior certified.**

Hotfix 3c is an in-place Bot + Web update from Hotfix 3b. It preserves the existing database, hosted sync schema, Portal Action protocol, Twitch configuration, and player progression.

## Automated validation

- Bot automated tests: **345 / 345 PASS**
- Frontend source/unit/regression tests: **157 / 157 PASS**
- Hosted Portal/API tests: **39 / 39 PASS**
- JavaScript/JSX independent TypeScript syntax parse: **50 / 50 PASS**
- Python grammar sweep: **72 / 72 PASS**
- Cloud stress: **1,000 players / 10,000 operations / 4 readers PASS**
- Stress elapsed: **17.30 s**
- Stress throughput: **578.1 ops/s**
- Stress Portal reads: **6,954**
- Stress ledger rows: **12,146**
- SQLite quick-check failures: **0**
- Foreign-key violations: **0**
- Negative Gil/inventory states: **0**
- Portal read errors: **0**
- Transaction rollbacks: **0**
- Exact extracted Bot/Web/Complete package validation: **PASS**
- Hotfix 3b → 3c consolidated update overlay: **PASS — byte-for-byte final tree**

## Hotfix 3c regression coverage

Validation confirms that:

- Items & Equipment now starts with a dedicated **Current Loadout** summary for Weapon, Armor, and Accessory;
- each equipped slot shows the active item and its effective stat bonuses;
- empty equipment slots are explicitly identified;
- equipped inventory entries sort to the top of their equipment group and carry a clear **EQUIPPED NOW** marker and highlighted state;
- existing equipment detail, comparison, forge-upgrade, equip, and unequip behavior remains available;
- `gil_spent` achievement progress is derived from the authoritative transaction ledger instead of stale cached record-stat state;
- historical negative-Gil transactions already recorded for an existing player are recognized automatically without a migration/backfill;
- Twitch and Portal shop purchases can unlock **Stimulating the Economy** immediately after the qualifying spend;
- replaying a completed Portal purchase remains idempotent and does not double-spend Gil or duplicate inventory writes;
- other transaction-derived record metrics use the same authoritative ledger path;
- on mobile, downward scrolling hides the sticky Portal header once the user has moved away from the top of the page;
- any upward scroll restores the header immediately;
- the header is always visible near the top of the page and when keyboard focus moves inside it;
- the behavior is limited to mobile widths and respects reduced-motion preferences.

## Compatibility

- Bot runtime: `1.1.14-cloud-continuity-h3c`
- Hosted Web runtime: `1.1.14-cloud-continuity-h3c`
- Hosted sync runtime compatibility: `1.1.14-cloud-continuity`
- Frontend asset revision: `1.1.14-continuity3c`
- Local DB schema: **4**
- Hosted sync schema: **1**
- Portal Action protocol: **12**
- Twitch prefix: `!`

No database migration, player reset, new Render secret, new OAuth scope, hosted sync schema change, or Portal Action protocol change is introduced by Hotfix 3c. Existing Hotfix 2+ subscriber authorization for `channel:read:subscriptions` remains unchanged.

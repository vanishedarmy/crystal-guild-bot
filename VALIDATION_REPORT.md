# Crystal Guild v1.9.0 Alpha 2 — Economy Balance Validation

Validation target: runtime `1.9.0-economy-balance-alpha2`, local schema **19**, hosted sync schema **1**, and Portal Action protocol **36**.

## Automated results

- Bot regression suite: **759 / 759 passed**.
- Web/hosted Python suite: **80 / 80 passed** (52 non-hosted + 28 hosted-route tests).
- Economy Balance frontend regression set: **3 / 3 passed**.
- Python compile checks: **passed** for Bot and Web packages.
- JSON parsing checks: **passed** for shipping manifests/data touched by packaging.
- ZIP integrity checks: **passed** for final archives.

## Economy-specific coverage

- Retainer expected NPC liquidation is below the normal dispatch fee for every assignment.
- Workshop material conversions cannot be immediately liquidated to an NPC for guaranteed profit.
- Mineral Survey and Specialist Acquisition retain their reward pools and quantities; only service fees changed.
- Press Adamantite preserves Adamantite item value while removing the Workshop-specific flip.
- Trading Post remains Fellowship Level 1 and now requires 15 Ventures rather than inaccessible Level-6 Expeditions.
- Monster Toss low-score floor now pays 10 MGP at 75 points, and its strongest fixed strategy remains bounded by the three-games-per-day limit.
- Mini Cactpot, Crystal Slots, Chocobo Racing, Triple Triad, daily MGP credits, Prize Counter prices, Trading Post fees, normal Gil income, shop prices, Hunts, and Raid pools remain unchanged.

## Frontend legacy-suite note

The repository's broad historical Node test collection contains old assertions that intentionally pin earlier release identities (`v1.8.2`, older Gold Saucer phases, etc.) and an old global PNG-free policy. Those assertions already conflict with the v1.9 Trading Post asset set and are not used as release gates for this economy-only patch. The new Alpha 2 frontend regression tests covering current version identity, Trading Post requirement copy, and Monster Toss guidance all pass.

## Compatibility

- Database migration: **none** (schema remains 19).
- Player reset: **not required**.
- Portal Action protocol: **unchanged at 36**.
- Hosted sync schema: **unchanged at 1**.

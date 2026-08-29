# Crystal Guild v1.3.0 — Guild Expansion Alpha 5 Validation Report

## Result
**PASS**

## Automated regression suites
- Bot unittest suite: **470 / 470 PASS**.
- Frontend Node regression suite: **343 / 343 PASS**.
- Hosted Web/API unittest suite: **47 / 47 PASS**.
- Focused Guild Legacy Alpha 5 suite: **6 / 6 PASS**.

The Bot regression log includes intentional simulated outage/recovery and acknowledgement-loss warnings from resilience tests; those scenarios pass and are not release failures.

## Guild Legacy behavior verified
- Ten permanent Guild Legacy accomplishments derive from existing Fellowship, facility, Expedition, raid, Airship, donation, Deed, and Weekly Order history.
- Existing Alpha 4 Guilds are evaluated retroactively on Alpha 5 startup, so accomplishments already earned are recognized without resetting progress.
- Every Legacy reward uses a stable `legacy_accomplishment:<id>` Fellowship event key; repeated startup/evaluation cannot award the same shared Renown twice.
- Hall progression advances through **Founding Hall**, **Bannered Hall**, **Hall of Heroes**, and **Legendary Guild Hall** as total accomplishments rise.
- Unlocked trophy/decorations remain represented in the public Fellowship Legacy snapshot.
- Airship construction, completed missions, and all five Tier-III upgrade tracks feed their intended Legacy accomplishments.

## Guild Service Record verified
The personal Fellowship record now reports existing contribution history plus:
- Ventures completed;
- Hunts won;
- Raid participation;
- Expeditions completed;
- crafting and forge service;
- Workshop refining batches;
- Airship missions supported.

Automatic distinctions are derived from existing history and do not require a new progression table. `!legacy` / `!guildlegacy` exposes shared Legacy progress, while `!contributions` / `!guildrecord` continues to expose the personal service record.

## Player-facing Web / Guide verification
- Public Fellowship includes the Guild Legacy Hall stage, trophy shelf, next goals, accomplishment progress, and reward summaries.
- Personal Fellowship uses the broader **Guild Service Record** presentation and displays earned distinctions.
- Player Guide explains Legacy and Service Records only in gameplay/usage terms; backend/release-engineering details remain outside the Guide.
- Alpha 4 Guild Airship, Alpha 3 services, Alpha 2 projects/Order rewards, and Alpha 1 facility Board regressions remain green.

## Source and asset validation
- Python compile sweep: **86 / 86 PASS**.
- JavaScript/MJS `node --check`: **141 / 141 PASS**.
- Explicit quoted artwork-route audit: **221 unique routes checked, 0 missing**.
- Alpha 5 introduces no new required artwork files; the existing scenic, Airship, monster, item, job, region, and boss art routes remain intact.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion-a5`
- Hosted Web runtime: `1.3.0-guild-expansion-a5`
- Frontend asset revision: `1.3.0-guild-expansion-a5`
- Local DB schema: **9** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **21** unchanged
- Twitch prefix: `!`
- Database migration from Alpha 4: **none**
- Player reset: **none**
- OAuth change: **none**
- New environment variables: **none**

## Patch/release-tree verification
- Alpha 4 → Alpha 5 Bot patch: **21 changed/new files, 0 deletions**; reconstructs the **141-file** final Bot tree exactly.
- Alpha 4 → Alpha 5 Web patch: **39 changed/new files, 0 deletions**; reconstructs the **800-file** final Web tree exactly.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations** across all six archives.
- Full Bot archive vs finalized Bot tree: **141 / 141 files exact**.
- Full Web archive vs finalized Web tree: **800 / 800 files exact**.
- Complete archive Bot/Web subtrees vs finalized source trees: **exact**.
- SHA-256 manifest verification: **PASS** for all six archives and three release documents.

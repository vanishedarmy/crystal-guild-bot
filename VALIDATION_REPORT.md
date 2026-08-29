# Crystal Guild v1.3.0 — Guild Expansion Beta 1 Validation Report

## Result
**PASS**

## Regression suites
- Bot unittest suite: **475 / 475 PASS**.
- Frontend Node regression suite: **349 / 349 PASS**.
- Hosted Web/API unittest suite: **47 / 47 PASS**.
- Focused Beta 1 balance regressions: **5 / 5 PASS** (included in the Bot total).

The Bot log still includes intentional simulated Twitch outage, acknowledgement-loss, checkpoint recovery, and temporary availability warnings from resilience tests; those scenarios pass and are not Beta 1 failures.

## Guild balance simulation
- Fixed seed: **1301**.
- **1,000** seasons each for Casual, Core, and Active Guild profiles.
- Total: **3,000 simulated Guild seasons**.
- Conservative Core profile medians: Fellowship LVL 8 **6.1 weeks**; Airship Dock Lv.1 **11.1 weeks**; Airship built **13.3 weeks**; all five major facilities Lv.3 **24.0 weeks**; all Airship upgrades Tier III **33.4 weeks**.
- Contribution Renown is excluded from the model, intentionally biasing the simulation toward slower progression.

The complete report is packaged at `reports/GUILD_BALANCE_SIMULATION.md` and the underlying result set at `reports/GUILD_BALANCE_SIMULATION.json`.

## Balance verification
- Airship Dock costs use the Beta 1 60k/100k/170k Gil, 25/35/55 Ancient Coin, and 4/6/9 raid-clear curve.
- Crystal Guild Airship construction uses 140k Gil, 35 Mythril Ore, 18 Wyvern Scales, 20 Elemental Crystals, 10 Ancient Coins, and 6 Guild raid wins.
- Airship upgrade Gil is 25k/55k/95k and raid requirements are 1/2/2 per track.
- Artifact tracks use fewer materials than common-material tracks: Adamantite/Dark Matter 2/4/6; Magitek Capacitors 3/5/8; Mythril Ore/Elemental Crystals 4/7/10.
- Weekly Order rewards, Supply Drives, Guild Objectives, Workshop refining, Fellowship thresholds, Airship mission formulas, and Legacy milestones are unchanged.

## Source and asset validation
- Python compile sweep: **88 / 88 PASS** across Web + Bot source/tests/tools.
- Web JavaScript/MJS `node --check`: **143 / 143 PASS**.
- Frontend JS/JSX TypeScript-parser syntax sweep: **65 / 65 PASS**.
- Explicit literal image/font route audit: **145 unique routes checked, 0 missing**.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion-b1`
- Hosted Web runtime: `1.3.0-guild-expansion-b1`
- Frontend asset revision: `1.3.0-guild-expansion-b1`
- Local DB schema: **9** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **21** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth change: **none**
- New environment variables: **none**

## Packaging verification
- Alpha 5 → Beta 1 Bot patch: **17 changed/new files, 0 deletions**; reconstructs **145 / 145** final Bot files exactly.
- Alpha 5 Hotfix 1 → Beta 1 Web patch: **38 changed/new files, 0 deletions**; reconstructs **803 / 803** final Web files exactly.
- Full Bot archive vs final Bot tree: **145 / 145 exact**.
- Full Web archive vs final Web tree: **803 / 803 exact**.
- Complete archive Bot/Web subtrees: **exact**.
- ZIP CRC/integrity: **6 / 6 PASS**.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **PASS**.

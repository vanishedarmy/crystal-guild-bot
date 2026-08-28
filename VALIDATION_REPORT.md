# Validation Report — RC1 Hotfix 9 Raid Timing & Field Support

## Identity
- Runtime: `1.1.19-retro-phase-iii-rc1h9`
- Local DB schema: 7
- Hosted sync schema: 1
- Portal Action protocol: 19
- Twitch prefix: `!`

## Automated validation
- **408 tests plus 30 subtests across all Bot test modules passed**.
- H9 timer, field-support, Portal announcement, Solo Venture +5 ceiling, release-contract, and setup/upgrade regression groups pass.
- Changed Python modules compile successfully.

## H9 coverage
- Engine defaults are 60s Venture rally / 30s Venture rounds / 90s Raid rally / 60s Raid rounds.
- LIVE cross-player field recovery succeeds and consumes the actor's item only on useful effect.
- OFFLINE cross-player field recovery fails closed without changing HP or inventory.
- Portal Spawn Boss posts a rally announcement only on the LIVE owner Portal path and only after action acknowledgement.
- Upgrade helper changes prior stock combat timers and preserves unrelated/custom environment values.
- Solo Venture selection is capped at **player level +5** and regression-tested against an exact +5 encounter.

No DB migration or player reset is introduced.

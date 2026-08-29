# Crystal Guild v1.3.0 — Guild Expansion RC1

## Release Candidate 1

RC1 freezes the complete v1.3 Guild Expansion feature set and prepares it for final release. No Guild economy, Airship, Workshop, Weekly Order, Legacy, character, Expedition, combat, or reward balance is changed from Beta 3.

### Final release-candidate cleanup
- Normalizes the Bot, hosted Web, frontend, Windows control panel, Guide metadata, scene manifest, README/package identity, and deployment documentation to `1.3.0-guild-expansion-rc1`.
- Removes a stale Beta-era control-panel banner/assertion so the packaged Bot reports one release identity everywhere.
- Corrects the player Guide's Expedition unlock wording from the retired `Guild Hall Tier 1` label to the current **Guild Hall Lv. 1** terminology. The requirement itself is unchanged.
- Replaces the current What's New entry with a concise player-facing RC1 summary. Release engineering details remain in release/validation documentation rather than the Player Guide.

### Release-readiness verification
- Keeps the Beta 3 shared-state protections for simultaneous Fellowship contributions, stale project tabs, project completion/switching, Portal retries, and Airship launch/return settlement.
- Re-verifies restart persistence for Fellowship/Airship state and the existing additive schema-8 → schema-9 Airship migration path.
- Re-runs recovery-drill and synthetic-stress release checks, full Bot/Web suites, source parsing/compilation, and routed artwork checks.

### Preserved v1.3 systems
RC1 includes the complete Guild Expansion feature set: five major Guild facilities, Construction/Supply Drives/Guild Objectives, Weekly Order contributor rewards, Workshop services, Chocobo Stable and Archive benefits, the Crystal Guild Airship and upgrades, Guild Legacy/Hall progression, Guild Service Records, the Founding Hall portrait, collapsible inventory groups, Beta 1 economy tuning, Beta 2 Fellowship/mobile consolidation, and Beta 3 shared-state hardening.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion-rc1`
- Hosted Web runtime: `1.3.0-guild-expansion-rc1`
- Frontend asset revision: `1.3.0-guild-expansion-rc1`
- Local DB schema: **9** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **22** unchanged from Beta 3
- Twitch prefix: `!`
- Database migration from Beta 3: **none**
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**

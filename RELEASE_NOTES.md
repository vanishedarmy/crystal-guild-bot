# Crystal Guild v1.3.0 — Guild Expansion RC2

## Release Candidate 2 — Final Package Hardening

RC2 keeps the complete v1.3 Guild Expansion feature set frozen and performs the final package/metadata hardening pass before production release. No Guild economy, Airship, Workshop, Weekly Order, Legacy, character, Expedition, combat, item, or reward balance changes are included.

### RC2 cleanup
- Advances Bot, hosted Web, frontend, Windows control panel, Guide metadata, scene manifest, package manifests, README surfaces, and deployment documentation to `1.3.0-guild-expansion-rc2`.
- Refreshes the bundled `FINALIZATION_AUDIT.md` files so the current package no longer presents old v1.1.19 / Expeditions Alpha-era headings as the active finalization audit.
- Strengthens release-contract coverage so current package metadata, control-panel identity, and finalization audits must agree on RC2.
- Updates What's New with a concise player-facing RC2 summary while keeping release-engineering detail out of gameplay instructions.

### Preserved reliability
- Beta 3 simultaneous-contribution serialization and live remaining-requirement recomputation remain intact.
- Stale project tabs continue to fail closed using the project ID that was actually displayed to the player.
- Portal replay protection, project completion/switching serialization, concurrent Airship launch protection, restart/reconnect recovery, and exact-once Airship return settlement remain intact.
- RC1 Fellowship/Airship persistence, migration recovery, database integrity, and synthetic stress guardrails remain covered.

### Preserved v1.3 systems
RC2 includes the complete Guild Expansion: five major Guild facilities, Construction/Supply Drives/Guild Objectives, Weekly Order contributor rewards, Workshop services, Chocobo Stable and Archive benefits, Crystal Guild Airship construction/missions/upgrades, Guild Legacy/Hall progression, Guild Service Records, the Founding Hall portrait, collapsible inventory groups, Beta 1 economy tuning, Beta 2 Fellowship/mobile consolidation, and Beta 3 shared-state hardening.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion-rc2`
- Hosted Web runtime: `1.3.0-guild-expansion-rc2`
- Frontend asset revision: `1.3.0-guild-expansion-rc2`
- Local DB schema: **9** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **22** unchanged
- Twitch prefix: `!`
- Database migration from RC1: **none**
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**

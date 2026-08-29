# Crystal Guild v1.3.0 — Guild Expansion

## Final Release

Guild Expansion is the complete v1.3.0 release. It promotes the RC2 codebase without changing Guild economy, Airship, Workshop, Weekly Order, Legacy, character, Expedition, combat, item, or reward balance.

### Final release cleanup
- Promotes Bot, hosted Web, frontend, Windows control panel, Guide metadata, scene manifest, package manifests, README surfaces, and deployment documentation to `1.3.0-guild-expansion`.
- Cleans the player-facing **Previous major updates** history so only shipped releases are listed; Alpha, Beta, and release-candidate milestones are no longer shown to players.
- Refreshes stale Hosting Guide and Portal Actions Setup headings/details so operational documentation matches schema **9**, hosted sync schema **1**, and Portal Action protocol **22**.
- Keeps engineering Alpha/Beta/RC history in internal changelogs for traceability while removing it from the public update feed.

### Guild Expansion systems
- Five major Guild facilities: Guild Hall, Workshop, Chocobo Stables, Guild Archive, and Airship Dock.
- Permanent Construction projects plus shorter Supply Drives and gameplay-driven Guild Objectives.
- Weekly Order contributor payouts and full-week participation rewards.
- Workshop refining, Chocobo Stable training benefits, and Guild Archive Expedition research bonuses.
- Crystal Guild Airship construction, missions, contribution progress, history, and five upgrade tracks.
- Guild Legacy accomplishments, trophy shelf, Guild Hall stage progression, and personal Guild Service Records.
- Founding Hall presentation and remembered/collapsible Fellowship and inventory sections.

### Preserved reliability
- Simultaneous Guild contributions recompute live remaining requirements before resources are deducted.
- Stale project tabs fail closed instead of contributing to a replacement project.
- Portal retries remain idempotent; project completion/switching and Airship launch/return mutations remain serialized.
- Airship mission settlement is restart/reconnect safe and contributor rewards settle exactly once.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion`
- Hosted Web runtime: `1.3.0-guild-expansion`
- Frontend asset revision: `1.3.0-guild-expansion`
- Local DB schema: **9** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **22** unchanged
- Twitch prefix: `!`
- Database migration from RC2: **none**
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**

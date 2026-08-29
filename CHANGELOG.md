# Crystal Guild v1.2.0 — Expeditions Beta 4
## Release Hardening

Beta 4 keeps the v1.2 feature set frozen and hardens the persistent Adventure/release path before RC1.

### Persistent resource-pressure protection
- Long Rest no longer restores HP/MP/AP through an active distant Expedition or player-paced Wayfarer run.
- Stream-start roster refreshes skip players with those persistent runs active while still refreshing idle heroes once per Twitch stream session.
- The rule survives Portal reconnects and Bot/database restarts because active-run ownership is checked from SQLite.

### Crash-atomic persistent Adventure actions
- Persistent Solo/Expedition Portal mutations now execute inside the same outer SQLite transaction as their Portal replay receipt.
- If the receipt cannot commit, nested stage/cache/progress/reward/result writes roll back with it.
- A lost hosted acknowledgement can therefore be retried without duplicating Expedition stages, banked cache, Hunt Seals, result cards, or other persistent rewards.
- Timed Hunts retain their established live in-memory coordination/replay path.

### Restart, migration, and integrity drills
- Active Expedition stage, route, cache, Journal, and saved state are verified across a database/engine restart.
- A representative pre-v1.2 schema-7 Guild migrates to schema 8 with level, XP, Gil, HP/MP/AP, inventory, Chocobo data, and the verified pre-schema-8 backup preserved.
- Existing recovery-drill, database-integrity, synthetic stress, queue/replay, LIVE/OFFLINE, and outage-recovery suites remain enabled.

### Published timing cleanup
The Player Guide metadata is synchronized to the authoritative current defaults: 60-second Venture rally / 30-second rounds and 90-second Raid rally / 60-second rounds.

### Compatibility
- Bot runtime: `1.2.0-expeditions-b4`
- Hosted Web runtime: `1.2.0-expeditions-beta4`
- Frontend asset revision: `1.2.0-expeditions-b4`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Twitch prefix: `!`
- Player reset: **none**
- New environment variables: **none**

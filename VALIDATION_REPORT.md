# Validation Report — v1.2.0 Expeditions Alpha 2

## Identity
- Bot runtime: `1.2.0-expeditions-a2`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Twitch prefix: `!`

## Automated validation
- Bot regression suite: **422 tests + 30 subtests passed**.
- Alpha 2 Expedition coverage verifies regional objective chains, 75% boss unlocks, guaranteed Regional Boss final stages, persistent boss clears, guaranteed boss rewards, 100% Mastery, and Mastery title/achievement awards.
- Existing Alpha 1 travel, route, combat, cache, Camp, rescue, persistence, equipment locks, and Streamer Clear Adventures coverage remains passing.

## Compatibility
- Local database schema remains **8**; no migration is introduced.
- Existing Alpha 1 Expedition state and region-exploration rows remain compatible.
- Portal Action protocol remains **20**.
- Portal-origin Expedition announcements are staged only for notable milestones and remain LIVE-only.

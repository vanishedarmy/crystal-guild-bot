# Crystal Guild v1.1.18 — Hunt Board Hotfix 1 Validation

## Gameplay contract
- C-Rank timed Hunt: 15 minutes.
- B-Rank timed Hunt: 30 minutes.
- A-Rank timed Hunt: 2 hours.
- S-Rank timed Hunt: 5 hours.
- All 17 current Hunt catalog cooldowns match their rank assignment timer.
- Hunts remain per-player autonomous assignments and do not occupy the shared Rally/Active Battle slot.
- No round-by-round chat input is required.
- Rewards remain deferred until timed resolution.

## Automated validation
- Bot test suite: **379/379 PASS**.
- Active Hunt + release-contract focused tests: **24/24 PASS**.

## Release identity
- Bot runtime: `1.1.18-hunt-board-h1`
- Local DB schema: 5 unchanged
- Hosted sync schema: 1 unchanged
- Hosted sync compatibility: `1.1.15-wayfarer` unchanged
- Portal Action protocol: 14 unchanged
- Twitch prefix: `!`
- No migration or player reset required.

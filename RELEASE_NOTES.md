# Crystal Guild v1.1.18 — Hunt Board Hotfix 1

This gameplay hotfix aligns the Hunt Board with the autonomous timed-Hunt system and rebalances current Hunt assignment timers.

## Hunt behavior
- Hunts remain personal timed assignments and do not occupy the shared Rally/Active Battle slot.
- Dispatch from the Adventurer Portal Hunt Board or with `!hunt <name>`.
- No round-by-round chat commands are required.
- The hero automatically uses learned abilities, Defend, and a limited number of appropriate survival items.
- Rewards, first-clear prizes, resource changes, and records are committed only when the Hunt resolves.
- A hero may have only one Hunt active at a time.

## New rank timers
- C-Rank: **15 minutes**
- B-Rank: **30 minutes**
- A-Rank: **2 hours**
- S-Rank: **5 hours**
- S+ has no current marks and inherits the S timer internally until separately balanced.

The per-mark cooldown catalog now matches the rank assignment timer, so a completed Hunt does not expose a contradictory shorter cooldown.

## Release identity
- Bot runtime: `1.1.18-hunt-board-h1`
- Local DB schema: 5 (unchanged)
- Hosted sync schema: 1 (unchanged)
- Hosted sync compatibility: `1.1.15-wayfarer` (unchanged)
- Portal Action protocol: 14 (unchanged)
- Twitch prefix: `!`
- No DB migration or player reset required.

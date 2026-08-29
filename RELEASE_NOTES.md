# Crystal Guild v1.3.0 — Guild Expansion Alpha 2

## Guild Projects II
Alpha 2 expands the Fellowship beyond permanent facility construction. The Guild can now choose among three kinds of shared work:

- **Construction** — permanent Guild Hall, Workshop, Chocobo Stable, Guild Archive, and future Airship Dock progression.
- **Supply Drives** — shorter resource projects that consume only requested Gil/materials and award shared Fellowship Renown on completion.
- **Guild Objectives** — activity-only projects that advance automatically from normal play such as Hunts, Expeditions, and Raid victories.

### New Supply Drives
- **Moogle Relief Shipment** — 15,000 Gil, 25 Potions, 10 Hi-Potions; +300 shared Renown.
- **Forge Stockpile** — 20,000 Gil, 20 Mythril Ore, 10 Elemental Crystals; +400 shared Renown.
- **Frontier Stores** — 30,000 Gil, 20 Ancient Coins, 8 Tents; +450 shared Renown.

### New Guild Objectives
- **Clear the Roads** — 30 Hunt victories; +450 shared Renown.
- **Chart the Frontier** — 20 completed Expeditions; +500 shared Renown.
- **Raid Preparedness** — 8 Guild raid victories; +600 shared Renown.

These Alpha 2 initiatives are one-time Fellowship projects. Permanent facility construction remains the long-term Guild progression path.

## Weekly Fellowship Order rewards
The existing shared Renown payout remains intact. Alpha 2 adds modest personal participation rewards to give individual players a clearer reason to help:

| Weekly Order | Guild reward | Contributor reward |
|---|---:|---:|
| Into the Wilds | 300 Renown | 500 Gil + 25 personal Renown |
| Monster Hunters | 350 Renown | 500 Gil + 25 personal Renown |
| Bounty Board | 400 Renown | 600 Gil + 25 personal Renown |
| Hammer & Tongs | 300 Renown | 500 Gil + 25 personal Renown |
| Treasure Seekers | 300 Renown | 500 Gil + 25 personal Renown |
| Stand Together | 450 Renown | 750 Gil + 30 personal Renown |

When all three weekly Orders are completed, the Guild still receives **+500 shared Renown**. Every player who helped with at least one Order that week also receives one **1,000 Gil + 50 personal Fellowship Renown** weekly participation bonus. Each Order and weekly payout is replay-safe and can only be awarded once per eligible player.

## Fellowship presentation
- The public Fellowship page distinguishes Construction, Supply Drives, and Guild Objectives.
- Active activity-only objectives clearly state that no donation is required.
- Weekly Order cards show both the shared Guild reward and personal contributor payout.
- The Player Guide explains Guild Projects II in player-facing language.
- `!project` and `!orders` now explain the active project type and relevant rewards.

## Compatibility
- Bot runtime: `1.3.0-guild-expansion-a2`
- Hosted Web runtime: `1.3.0-guild-expansion-a2`
- Frontend asset revision: `1.3.0-guild-expansion-a2`
- Local DB schema: **8** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **20** unchanged
- Twitch prefix: `!` unchanged
- Database migration: **none**
- Player reset: **none**
- New environment variables: **none**

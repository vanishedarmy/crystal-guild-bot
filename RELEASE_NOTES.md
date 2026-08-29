# Crystal Guild v1.3.0 — Guild Expansion Alpha 4
## Guild Airship

Alpha 4 adds the Crystal Guild Airship as a shared Fellowship-scale system. The Airship is built and upgraded through normal Guild construction, then dispatched on timed missions whose progress comes from the activities players already perform across Crystal Guild.

## Airship Dock and construction
The Airship Dock is now part of the live major-facility path instead of a future placeholder.

- **Dock Lv. 1** establishes the construction berth and opens the Crystal Guild Airship project.
- **Dock Lv. 2** enables Tier II Airship upgrades.
- **Dock Lv. 3** enables Tier III Airship upgrades.

Once Dock Lv. 1 and Fellowship LVL 8 are reached, the Guild can complete the one-time **Crystal Guild Airship** construction project. It requires shared Gil, Mythril Ore, Wyvern Scales, Elemental Crystals, Ancient Coins, and Guild raid victories, and awards **1,500 shared Fellowship Renown** when completed.

## Shared Airship Missions
One Airship mission can be active at a time. The streamer launches a mission with `!airshipmission <mission>`; everyone can inspect the current deployment with `!airship` / `!guildairship` or from the Fellowship page.

| Mission | Base time | Base target | Progress comes from | Success reward |
|---|---:|---:|---|---|
| Merchant Escort | 24h | 50 | Ventures | 600 Guild Renown + 750 Gil / 25 personal Renown per contributor |
| Monster Suppression | 30h | 30 | Hunts and combat victories | 700 + 850 Gil / 30 Renown |
| Aether Survey | 36h | 15 | Expeditions | 800 + 900 Gil / 35 Renown |
| Salvage Run | 30h | 35 | Treasure, crafting, forging | 900 + 1,100 Gil / 40 Renown |
| Crystal Resonance Survey | 42h | 20 | Expeditions and raid victories | 1,000 + 1,200 Gil / 45 Renown |
| Relic Recovery | 48h | 24 | Raid participation and Expeditions | 1,250 + 1,500 Gil / 55 Renown |

Advanced missions require Crystal Core upgrades. Meeting the target early does not immediately resolve the deployment: rewards are issued when the Airship returns. Only players who actually added mission progress receive the personal payout. Mission settlement and contributor rewards are replay-safe.

## Airship upgrades
Five upgrade tracks use the normal Fellowship construction/project system and each advance through Tier I–III, gated by Airship Dock level.

- **Hull** — reduces mission progress targets by **4% per tier**.
- **Engine** — reduces mission duration by **6% per tier**.
- **Cargo Hold** — increases contributor Gil rewards by **10% per tier**.
- **Survey Array** — increases shared Fellowship Renown mission rewards by **5% per tier**.
- **Crystal Core** — unlocks advanced mission tiers.

## Fellowship presentation
- The public Fellowship page now has a dedicated Guild Airship surface with construction state, current mission, mission catalog, upgrade tiers, and recent mission history.
- A signed-in player's Fellowship tab shows Airship status and upgrade tiers without exposing streamer-only launch controls.
- The Player Guide explains Airship construction, missions, and upgrades in player-facing language.
- The Streamer Dashboard includes the allow-listed **Launch Airship Mission** control.
- What's New leads with the Alpha 4 Airship rollout.

## Persistence and compatibility
Alpha 4 advances the local database **schema 8 → 9** through an additive verified-backup migration. The new schema stores Airship build state, upgrade tiers, active mission state, mission contributors, and mission history. Existing characters, inventories, Fellowship projects, facilities, Weekly Orders, Chocobos, and Expeditions remain intact.

Portal Action protocol remains **21**; no new Portal action type is required for Airship missions.

## Technical identity
- Bot runtime: `1.3.0-guild-expansion-a4`
- Hosted Web runtime: `1.3.0-guild-expansion-a4`
- Frontend asset revision: `1.3.0-guild-expansion-a4`
- Local DB schema: **9**
- Hosted sync schema: **1**
- Portal Action protocol: **21**
- Twitch prefix: `!`
- Player reset: **none**
- OAuth change: **none**
- New environment variables: **none**

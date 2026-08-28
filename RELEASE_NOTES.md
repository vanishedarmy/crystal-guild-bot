# Crystal Guild v1.2.0 — Expeditions Alpha 5

## Chocobo Expedition Specialization
Alpha 5 turns the existing Chocobo trait and Bond progression into an automatic Expedition specialty. No respec screen, new stat allocation, or migration is required.

### Five specialties
- **Guardian** — derived from Steady Strider; improves hazard resistance and Chocobo rescue cache protection.
- **Scout** — derived from Keen Eye; improves discovery weighting and rare-event chance.
- **Pathfinder** — derived from Fleet Feet; improves Expedition travel time as Bond grows.
- **Forager** — derived from Forager; improves resource weighting and, at higher Bond, material yield.
- **Treasure Hunter** — derived from Lucky Plume; improves treasure weighting, rare-event chance, and rescue cache protection.

Specialties scale through five Bond tiers at Chocobo levels **1 / 5 / 10 / 15 / 20**. Existing Chocobos immediately receive the specialty and tier implied by their current trait and Bond level.

## Expedition accomplishments
The Chocobo Stable now surfaces shared Expedition records without adding a new persistence table: completed Expeditions, regional boss clears, rare regional discoveries, Chocobo rescues, and Legendary Contract completions. The system reuses existing player record statistics and regional exploration state.

## Guild completion stipends
Successful completed Expeditions now award a modest stipend in the existing **Hunt Seal** economy:
- Scout — **2 Seals**
- Journey — **4 Seals**
- Deep Expedition — **7 Seals**
- Regional Boss Contract — **10 Seals**
- Legendary Contract — **15 Seals**

Early returns and defeats do not receive the completion stipend. Regional and Legendary Contracts retain their material-focused reward identity; Alpha 5 does not introduce another wallet or currency.

## Portal presentation
- The Adventure Board shows the active Chocobo specialty, Bond tier, specialty effects, and completion stipend without expanding the compact payload beyond its established 16 KB guardrail.
- The Chocobo Stable shows the richer specialization breakdown, next Bond milestone, and Expedition accomplishment records.
- What's New and the Player Guide document the Alpha 5 system and stipend values.

## Compatibility
- Bot runtime: `1.2.0-expeditions-a5`
- Hosted Web runtime: `1.2.0-expeditions-alpha5`
- Frontend asset revision: `1.2.0-expeditions-a5`
- Local DB schema: **8** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Portal Action protocol: **20** (unchanged)
- Twitch prefix: `!`
- Player reset: **none**
- New environment variables: **none**
- New currency/table: **none**

# Crystal Guild v1.2.0 — Expeditions Alpha 2

## Regional progression
- Expands all five Expedition regions with persistent **25% / 50% / 75% / 100% exploration milestones** and named regional objective chains.
- Region progress now exposes the next objective, boss-unlock state, boss-clear count, and permanent Mastery state.
- At 75% exploration, each region unlocks a dedicated Regional Boss Contract and begins admitting level-appropriate rare regional encounters.

## Regional Boss Contracts
- **Emerald Wilds — Elder Ochu**
- **Ashen Highlands — Inferno Drake**
- **Mistfen Marshes — Malboro Sovereign**
- **Frostveil Reach — Frost Behemoth**
- **The Astral Scar — Rift Wyrm**
- Boss Contracts are persistent multi-stage Expeditions with a guaranteed boss encounter on the final stage, stronger reward multipliers, and guaranteed regional material rewards on victory.
- Regional boss victories increment a persistent clear counter and add additional regional exploration progress.

## Region Mastery
Reaching 100% exploration permanently masters the region and awards a dedicated achievement/title. Each Mastery provides a small region-only Expedition benefit:
- Emerald Wilds: +5% Discovery event weighting.
- Ashen Highlands: +5% Resource event weighting.
- Mistfen Marshes: 5% less Expedition hazard damage.
- Frostveil Reach: +5% Expedition Camp recovery.
- The Astral Scar: +5% Treasure event weighting.

## LIVE Portal milestones
Portal-origin Expedition gameplay remains quiet by default. While Twitch is confirmed LIVE, only notable milestones may post to chat: regional discoveries/milestones, Region Mastery, and Regional Boss victories. Offline Portal play remains silent.

## Continuity
- Existing Alpha 1 Expedition state, exploration progress, Chocobos, Fellowship progress, inventory, and character progression are preserved.
- Alpha 1 Hotfix 1 Fellowship balance and the Alpha 1 Hotfix 3 Web presentation/artwork fixes remain intact.

## Technical identity
- Bot runtime: `1.2.0-expeditions-a2`
- Local DB schema: **8** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Portal Action protocol: **20** (unchanged)
- Twitch prefix: `!`

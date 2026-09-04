# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 1

## Encounter Variety

The encounter audit found that the base bestiary weights were not the source of the Magic Pot streak. Magic Pot already carries a rare region weight of 1. The actual issue was the Solo Venture hard near-level filter: at certain player/region level combinations the preferred pool could collapse to one monster, making that monster effectively 100% despite its rare base weight.

Hotfix 1 changes the shared random-monster selection rules:

- **Solo Venture** widens a narrow near-level pool to at least **5** closest valid monsters when available.
- **Expeditions** use the same minimum-variety protection when their level band narrows too far.
- **Rally Venture, Solo Venture, and Expeditions** apply recent-monster suppression per player/region.
- An immediate repeat receives only **10%** of its normal effective weight.
- A **third identical encounter in a row is impossible** when any alternative valid monster exists.
- A single monster may hold at most about **45%** of the effective roll weight when 3+ candidates exist.
- Existing region rarity weights, enemy levels, drops, XP, JP, Gil, treasure odds, +10 Rally cap, and +5 Solo cap remain unchanged.

The concrete Magic Pot case is fixed: a Lv.25 Solo Venture in Whispering Caverns previously had only Magic Pot in its preferred band; it now rolls from five valid monsters while Magic Pot remains rare-weighted.

Bot runtime advances to `1.7.1-resynthesis-a2h1`. Paired Web remains `1.7.1-resynthesis-a2`. Local schema **15**, hosted sync **1**, Portal protocol **32**, prefix `!`. No migration or player reset.

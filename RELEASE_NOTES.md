# Crystal Guild v1.2.0 — Expeditions Alpha 3

## Expedition Atlas
Alpha 3 turns the five regional progression tracks into one permanent player-facing Atlas. The Adventure Board now derives an overall survey percentage, cartography rank, mastered-region count, total Regional Boss clears, and the number of Legendary routes unlocked from the schema-8 exploration records already earned in Alpha 2.

Cartography ranks progress through **Guild Scout → Trailblazer → Pathfinder → Surveyor → Cartographer**, with **Master Cartographer** reserved for players who master all five launch regions.

## Legendary Regional Contracts
A mastered region with at least one Regional Boss clear now unlocks a repeatable **Legendary Contract** through the existing Expedition launch action. Legendary Contracts:
- use five stages;
- guarantee the region boss on the final stage;
- increase the boss to **125% HP** and **115% outgoing pressure**;
- use a **25% stronger contract reward multiplier** than the normal Regional Boss Contract;
- take **20% longer base travel**; and
- double the boss contract's guaranteed regional material quantities.

The original 75%-exploration Regional Boss Contract remains available and unchanged.

## All-region mastery reward
Mastering all five Expedition regions unlocks the **No Blank Spots Left** achievement and the equippable **Master Cartographer** title. Existing Alpha 2 exploration is reused directly; no progress needs to be repeated.

## Portal & Guide
- Adds the **Expedition Atlas** summary to the Distant Expedition Board.
- Adds Legendary Contract controls only when a selected region is mastered; before the first boss clear the control explains the remaining requirement.
- Updates active-run labels and saved result copy for Legendary Contracts.
- Adds Alpha 3 to **What's New** while retaining Alpha 2 in the major-update history.
- Expands the Player Guide Expeditions chapter with Atlas ranks, Legendary unlock rules, and the all-region mastery reward.
- Retains the Alpha 2 Hotfix 3 Solo Venture and Relic Arsenal scenic backdrops.

## Compatibility
- Bot runtime: `1.2.0-expeditions-a3`
- Hosted Web runtime: `1.2.0-expeditions-alpha3`
- Frontend asset revision: `1.2.0-expeditions-a3`
- Local DB schema: **8** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Portal Action protocol: **20** (unchanged)
- Twitch prefix: `!`
- Player reset: **none**
- New environment variables: **none**

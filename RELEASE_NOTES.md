# Crystal Guild v1.2.0 — Expeditions Alpha 1

## Expedition foundation
- Adds five launch regions: **Emerald Wilds**, **Ashen Highlands**, **Mistfen Marshes**, **Frostveil Reach**, and **The Astral Scar**.
- Adds three expedition depths: **Scout (3 base stages)**, **Journey (5)**, and **Deep Expedition (8)**, plus up to two optional push-deeper stages.
- Expeditions require both a registered Chocobo and the completed Fellowship Expedition Board.
- Expedition state is authoritative and persistent across Portal refreshes, browser closure, reconnects, and Bot restarts.

## Stage loop
- Authoritative travel timers lead into weighted regional events: combat, resources, treasure, hazards, discoveries, travelers, and Chocobo events.
- Route choices support Safe Route, Unknown Route, and Push Deeper risk/reward profiles.
- HP/MP/AP persist through the journey.
- Expedition Camp restores part of HP/resources at the cost of additional travel time.
- Safe Return banks 100% of the current Expedition Cache outside combat.
- Retreat/defeat uses Chocobo rescue and keeps 70–85% of the carried cache depending on traits.
- Completed results use the persistent Adventure result inbox and remain until Confirm Result.

## Chocobo integration
- Existing Chocobo Bond level/XP and traits are active in Expeditions.
- Traits affect travel speed, hazard weighting, discoveries, resource finds, treasure/Chocobo events, and rescue cache protection.
- Expeditions award additional Chocobo Bond XP.

## Region progression
- Per-player region exploration progress, stages cleared, completed runs, and boss-clear counters are persisted for future Expedition milestones.
- Region progress survives emergency Clear Adventures and normal upgrades.

## Safety / continuity
- Equipment, Jobs, Masteries, stance, normal Camp, and conflicting Adventure modes are locked while an Expedition is active.
- Streamer **Clear Adventures** now also clears active v1.2 Expeditions without touching secured exploration progress, inventory, player progression, cooldowns, or raids.
- H9 Rally/Raid timing, LIVE field support, persistent Adventure results, Streamer Inventory Admin, dynamic Camp, Relic visuals, and overlay fixes remain intact.

## Technical identity
- Bot runtime: `1.2.0-expeditions-a1`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Twitch prefix: `!`

# Crystal Guild v1.5.0 — Trails & Raids Alpha 4

## Rescue, Resolve & Heart of the Crag
Alpha 4 continues the cooperative boss-combat overhaul with **Titan — Heart of the Crag**, a fourth scripted Trial built around personal telegraph response, temporary restraint/rescue, and a party damage-check phase. The collapsible Trial & Raid Board introduced in Alpha 3 remains intact. The four production Dungeons remain frozen and unchanged.

### Titan — Heart of the Crag
- Titan becomes the fourth flagship **Trial** while retaining his existing **Primal Boss** catalog classification, level band, and rewards.
- **Landslide** marks one raider. Defending braces against the knockback; failing to respond applies a knockdown that costs the target their next action.
- **Granite Gaol** restrains one raider and prevents them from acting until the party destroys the Gaol.
- Existing boss-directed attacks and enemy-targeted abilities automatically strike the active Gaol/Heart add, so no new targeting command is required.
- **Heart of the Crag** creates a two-round party damage check against Titan's Heart.
- Destroying the Heart weakens **Earthen Fury**; failing the check resolves an empowered raidwide blast.

### Trial & Raid presentation
- The Adventure Board Trial & Raid Board remains collapsible with the established right-hand closed / down-hand open pointer behavior and remembered open/closed preference.
- Live presentation now distinguishes **Landslide**, **Rescue / Granite Gaol**, and the **Heart Check** while retaining Ifrit damage-check, Shiva add/Break/Stagger, Ramuh chain/stack/Grounding, add HP, and role-aware contribution presentation.
- Hosted Overlay payloads remain sanitized and display-only; internal restraint/release target IDs are never published.

### Continuity
- Ifrit — **Inferno Crucible**, Shiva — **Diamond Throne**, and Ramuh — **Judgment Spire** remain fully supported.
- Existing non-scripted raids retain their established phases, enrages, target weighting, Limit Breaks, Summons, revives, items, abilities, and reward math.
- Raid actions remain Twitch/Bot-authoritative; the Portal Raid Board remains read-only.
- Existing Dungeons, Expeditions, Fellowship, inventories, records, and progression are unchanged.

### Compatibility
- Bot/Web/frontend: `1.5.0-trails-raids-a4`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Database migration / player reset / OAuth change / new environment variables: **none**

Deploy matching Alpha 4 Web + Bot together.

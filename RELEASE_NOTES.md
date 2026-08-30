# Crystal Guild v1.5.0 — Trails & Raids Alpha 3

## Chains, Stacks & Grounding
Alpha 3 continues the cooperative boss-combat overhaul with a third scripted Trial and coordinated defensive mechanics that use the existing Twitch action surface. It also makes the Adventure Board Trial & Raid Board collapsible. The four production Dungeons remain frozen and unchanged.

### Ramuh — Judgment Spire
- Ramuh becomes the third flagship **Trial** while retaining his existing Primal Boss catalog classification and rewards.
- **Rolling Thunder** marks one raider and chains through up to three standing heroes with diminishing damage.
- **Levinshare** marks one raider for a heavy strike; allies who choose **Defend** join the stack and split the incoming pressure.
- **Judgment Charge** opens a two-round shared **Grounding Gauge**. Each Defend action contributes one point.
- Meeting the Grounding target weakens **Judgment Bolt**; failing the target resolves an empowered raidwide discharge.
- No new chat targeting or action command is required.

### Trial & Raid Board
- The Adventure Board Trial & Raid Board is now collapsible.
- It uses the established right-hand closed / down-hand open disclosure language and remembers the player's last open/closed preference.
- The Board understands chain, shared-hit, and Grounding Gauge telegraphs while retaining add HP, Break/Stagger state, and role-aware contribution from Alpha 2.

### Continuity
- Ifrit — **Inferno Crucible** and Shiva — **Diamond Throne** remain fully supported.
- Existing non-scripted raids retain their established phases, enrages, target weighting, Limit Breaks, Summons, revives, items, abilities, and reward math.
- Raid actions remain Twitch/Bot-authoritative; the Portal Raid Board remains read-only.
- Existing Dungeons, Expeditions, Fellowship, inventories, records, and progression are unchanged.

### Compatibility
- Bot/Web/frontend: `1.5.0-trails-raids-a3`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Database migration / player reset / OAuth change / new environment variables: **none**

Deploy matching Alpha 3 Web + Bot together.

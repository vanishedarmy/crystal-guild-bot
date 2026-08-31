# Crystal Guild v1.5.0 — Trails & Raids Alpha 7

## The Final Coil
Alpha 7 adds **Bahamut — The Final Coil** as Crystal Guild's first capstone scripted Trial. The six elemental flagship Trials remain supported, the roomy collapsible Trial & Raid Board remains the presentation baseline, and all four production Dungeons remain unchanged.

### Bahamut mechanics
- **Flare Breath** cleaves a marked raider and one nearby ally.
- **Akh Morn** marks one raider; Defending allies join the stack and split the blast.
- **Megaflare Towers** requires enough standing raiders to Defend in the same round to contain Megaflare.
- At critical HP, **Teraflare Charge** begins a one-time three-round damage race. Meeting the target contains Teraflare; failure unleashes the full blast.
- No new target or mechanic command is required; the existing raid command vocabulary remains authoritative.

### Presentation
- Bahamut receives a **full-width capstone card** on desktop while the six elemental Trials retain the roomy two-column layout.
- Portal and OBS telegraphs understand **Tower Check** and **Final Damage Check** states.
- Player Guide coverage documents the complete Final Coil mechanic set.
- The Trial & Raid Board remains collapsible, remembers its open/closed state, and keeps the canonical right-hand closed / down-hand open pointer.

### Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a7`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth/environment changes: **none**
- New environment variables: **none**

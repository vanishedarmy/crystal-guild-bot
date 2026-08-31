# Crystal Guild v1.5.0 — Trails & Raids Alpha 6

## Tidebreak Expanse
Alpha 6 adds **Leviathan — Tidebreak Expanse** as the sixth scripted Trial. Alpha 5's spacious, collapsible Trial & Raid Board remains the presentation baseline, while Ifrit, Shiva, Ramuh, Titan, Garuda, unscripted raids, and all four production Dungeons remain supported.

### Leviathan mechanics
- **Tidal Sweep** marks roughly half of the standing raid on alternating Port/Starboard pressure. Each marked raider can Defend to brace and avoid lingering Slow.
- **Undertow** targets one raider. Defend protects the target; an unbraced target loses MP/AP and releases splash pressure into allies.
- **Maelstrom Surge** is a two-round survival phase. Coordinated Defends fill a shared Stability Gauge while repeated water pressure hits the raid.
- **Tidal Wave** resolves weakened when the Stability Gauge succeeds and empowered when the raid fails to stabilize.
- No new target or mechanic command is required; existing `!attack`, `!ability`, `!defend`, item, Limit Break, Summon, and revive commands remain the combat surface.

### Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a6`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth/environment changes: **none**
- New environment variables: **none**

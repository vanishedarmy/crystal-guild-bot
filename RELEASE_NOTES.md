# Crystal Guild v1.5.0 — Trails & Raids Alpha 5

## Eye of the Storm & Trial Board Readability
Alpha 5 adds **Garuda — Eye of the Storm** as the fifth scripted Trial and gives the flagship Trial Board a dedicated readability redesign. Ifrit, Shiva, Ramuh, Titan, unscripted raids, and the four production Dungeons remain supported without balance changes.

### Garuda — Eye of the Storm
- **Slipstream** marks one raider. Defend to brace the focused gust and avoid a brief Slow.
- **Friction** marks one raider. Defending contains the wind pressure; failing to contain it splashes the rest of the party.
- **Plume Squadron** spawns Satin and Razor Plumes for a two-round add phase. Existing boss-directed attacks and abilities automatically strike the active Plume, so no new target command is required.
- **Aerial Blast** resolves weakened if both Plumes are destroyed, pressurized if one survives, or empowered if both survive.

### Trial & Raid Board visual pass
- Desktop flagship Trial cards now use a spacious **two-column grid** instead of compressing four cards across one row.
- Cards gain wider copy, larger artwork, separated Trial/level metadata, dedicated stat blocks, and a clearer command footer.
- Tablet and mobile layouts fall back to one card per row while preserving the Alpha 3 collapsible disclosure and remembered state.

### Compatibility
- Runtime/frontend: `1.5.0-trails-raids-a5`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged
- Twitch prefix: `!`
- Player reset: **none**
- OAuth/environment changes: **none**
- New environment variables: **none**

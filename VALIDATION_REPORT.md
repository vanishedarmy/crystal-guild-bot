# Validation Report — Full Rest & Combat Continuity

**PASS**

## Release contract
- Runtime/frontend: `1.7.1-resynthesis-a2h5`
- Local DB schema: **16**
- Hosted sync schema: **1**
- Portal Action protocol: **33**
- New database migration: **none**
- Player reset: **none**

## Source regression
- Bot: **704 / 704 PASS**
- Frontend: **588 / 588 PASS**
- Hosted Web/API: **71 / 71 PASS**

## Focused behavior
- Full Rest restores HP and both MP/AP families across Job switches.
- Same-family Jobs with different resource maxima resolve fully after Rest.
- Portal snapshots interpret the full-resource state at the selected Job's maximum.
- Rally/normal encounter, Solo Venture, Expedition, Dungeon, Hunt, admin encounter, and admin Raid paths no longer use round count as a defeat condition.
- Technical auto-resolution watchdogs preserve living combat instead of forcing defeat.
- Dungeon public/UI state uses unlimited round telemetry and no obsolete denominator.

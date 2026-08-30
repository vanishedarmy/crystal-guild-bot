# Crystal Guild v1.5.0 — Trails & Raids Alpha 1

## Raid Combat Engine & First Trial

Alpha 1 begins the Trails & Raids expansion from the stable v1.4.0 Dungeons & Delves production baseline. It upgrades cooperative boss encounters without changing the frozen four-Dungeon catalog or established player progression.

### Ifrit — Inferno Crucible
- Ifrit is the first flagship **Trial** encounter.
- **Incinerate** telegraphs a heavy targeted strike.
- **Radiant Plume** telegraphs raidwide pressure.
- **Infernal Nails** opens a two-round shared damage check.
- Meeting the check weakens **Hellfire**; failing it empowers the raidwide blast.

### Raid presentation & contribution
- Adventure Board gains a read-only live Trial/Raid panel driven by the public raid overlay state.
- OBS raid presentation exposes the current telegraph, Trial identity, boss state, and weighted contribution leaders.
- Contribution combines damage, healing, and mitigation instead of ranking damage alone.
- Public hosted state is sanitized and never exposes Twitch IDs or internal mechanic target IDs.

### Continuity
- Existing raid rounds, revives, Limit Breaks, Summons, phases, enrages, persistence, and recovery behavior remain intact.
- Existing v1.4 Dungeons remain unchanged and production-frozen.
- No economy, progression, Dungeon reward, OAuth, or environment rebalance is introduced.

### Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a1`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- New environment variables: **none**

Deploy matching Alpha 1 Web + Bot together.

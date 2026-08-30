# Crystal Guild v1.5.0 — Trails & Raids Alpha 2

## Break, Stagger & Encounter Adds
Alpha 2 continues the cooperative boss-combat overhaul from Alpha 1 and the Hotfix 2 Web baseline. It adds a second scripted Trial and general raid-state support for encounter adds, Break checks, Stagger windows, and role-aware contribution presentation. The four production Dungeons remain frozen and unchanged.

### Shiva — Diamond Throne
- Shiva becomes the second flagship **Trial** while retaining her existing Primal Boss catalog classification and rewards.
- **Frostbrand Cleave** telegraphs a marked raider and strikes that target plus a second standing raider.
- **Icebound Mirrors** spawn as persistent encounter adds. While a Mirror survives, ordinary boss-directed damage is automatically intercepted by the active add; no new targeting command is required.
- **Diamond Aegis** opens a two-round shared Break gauge.
- Meeting the Break target makes Shiva **Staggered** for the following round: she is vulnerable and loses her boss response.
- Failing the Break target resolves **Diamond Dust** as raidwide pressure.

### Raid engine / roles
- Active raid checkpoints can persist sanitized add HP and scripted Break/Stagger state without a database migration.
- Contribution rows now label raiders as **Tank, Healer, Support, or DPS**. Existing damage/healing/mitigation contribution scoring and reward allocation are unchanged.
- Ifrit — **Inferno Crucible** remains fully supported with Incinerate, Radiant Plume, Infernal Nails, and weakened/empowered Hellfire.
- Existing non-scripted raids retain their established phase, enrage, target weighting, Limit Break, Summon, revive, item, and ability behavior.

### Portal / overlay
- Adventure Board Trial & Raid Board displays active adds, Break progress, Stagger state, and role labels.
- OBS raid overlay mirrors the same sanitized public state.
- Hosted Overlay validation accepts optional `adds` and contribution `role` fields while retaining forbidden-private-field checks and bounded payload validation.
- Raid actions remain Twitch/Bot-authoritative; the Portal Raid Board remains read-only.

### Compatibility
- Bot/Web/frontend: `1.5.0-trails-raids-a2`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Database migration / player reset / OAuth change / new environment variables: **none**

Deploy matching Alpha 2 Web + Bot together.

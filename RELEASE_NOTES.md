# Crystal Guild v1.5.0 — Trails & Raids Beta 1

## Trial Chronicle & Records Consolidation
Beta 1 freezes the seven scripted Trial encounters introduced during Alpha and turns them into durable personal progression records. No new boss, currency, reward table, combat mechanic, or Portal mutation is added in this pass.

### Trial Chronicle
- The Trial & Raid Board now shows a persistent **Trial Chronicle** for the viewed adventurer.
- Existing Alpha-era Trial clears are preserved automatically from the authoritative boss-clear ledger.
- From Beta 1 onward, each flagship Trial tracks **wipes, fastest clear round, best contribution score, best damage, best healing, and best mitigation**.
- Unique Trial clears advance a visible mastery rank: **Unproven → Trial Initiate → Trial Vanguard → Primal Conqueror → Coilbreaker**.
- The Records page now includes the same seven-Trial Chronicle and personal-best breakdown.

### Continuity
- Existing boss clears and best clear damage remain authoritative and require no conversion.
- Historical wipes/fastest rounds/contribution bests cannot be reconstructed from Alpha data, so those metrics begin tracking with Beta 1.
- Trial rewards, loot, encounter scripts, contribution reward weighting, unscripted raids, and the four production Dungeons are unchanged.

### Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-b1`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth/environment changes: **none**
- New environment variables: **none**

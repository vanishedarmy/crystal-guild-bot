# Crystal Guild v1.5.0 — Trails & Raids Beta 2

## Repeat Mastery & Settlement Hardening

Beta 2 turns repeat Trial clears into visible mastery progress and hardens Raid/Trial settlement against duplicate rewards from stale or recovered Bot connections. The seven flagship Trial encounters remain content-frozen; there is no new boss, currency, reward rebalance, database table, or Portal mutation.

### Repeat-clear mastery
- Every flagship Trial now derives a repeat-clear tier from the existing authoritative clear ledger: **Proven (1)**, **Seasoned (3)**, **Veteran (5)**, and **Mastered (10)**.
- Repeat mastery is retroactive because it is calculated from existing clear counts; no conversion or backfill job is required.
- The Trial & Raid Board and Records page show the current tier and next clear milestone.
- The Trial Chronicle summary shows how many of the seven Trials have reached **Mastered**.
- Repeat mastery is presentation/progression only. It does not add bonus loot, currency, or reward multipliers.

### Last Trial Result & live readiness
- After a victory or wipe, the Trial & Raid Board retains a **Last Trial Result** recap instead of immediately falling back to a generic Standby presentation.
- The recap shows the encounter, result, final round, standing raiders, last mechanic, and leading contribution rows from the existing final Overlay state.
- Active raids now expose sanitized **ready actions / actionable raiders** counts so the Portal and OBS presentation can show how many eligible raiders have queued an action.
- Raid combat remains Twitch/Bot-authoritative; no new Portal combat action is introduced.

### Exactly-once Raid settlement
- Every newly spawned Raid/Trial receives an exact **raid instance identity**.
- Victory/wipe settlement writes a bounded atomic receipt before the authoritative runtime checkpoint is cleared.
- If a stale or recovered second Bot connection tries to settle the same run, it detects the committed receipt, applies **no rewards, Fellowship credit, clear records, or Chronicle records again**, and reloads authoritative runtime state.
- Up to the latest **64** settlement receipts are retained in the existing runtime-state store to keep the guard bounded.
- A Raid already active during a Beta 1 → Beta 2 upgrade receives a stable legacy identity derived from its original boss/rally identity, so in-progress encounters receive the same protection without migration.

### Continuity
- Beta 1 Trial Chronicle metrics remain intact and continue tracking wipes, fastest successful clear round, best contribution score, best damage, best healing, and best mitigation.
- Trial rewards, contribution reward weighting, encounter scripts, unscripted raids, and the four production Dungeons are unchanged.
- Ifrit, Shiva, Ramuh, Titan, Garuda, Leviathan, and Bahamut remain the frozen scripted Trial catalog.

### Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-b2`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth/environment changes: **none**
- New environment variables: **none**

Deploy matching Beta 2 Web + Bot together.

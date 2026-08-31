# Crystal Guild v1.5.0 — Trails & Raids Beta 3

## Shared-State Hardening & Trial UX Consolidation

Beta 3 is the final active-Raid stability pass before release-candidate work. The seven flagship Trials remain content-frozen. This release does not add a boss, currency, reward rebalance, database table, Portal combat mutation, or new player command.

### Authoritative active-Raid revisions
- The existing runtime checkpoint now carries an additive combat **revision** inside the same runtime-state JSON contract.
- Outermost guarded combat writes acquire SQLite write intent, then refresh from a newer committed revision before mutating state.
- Two Bot connections can therefore queue different raiders in the same round without a stale connection overwriting an action committed by the other.
- Nested guarded operations share the same authoritative transaction and persist only once at the outer boundary.
- This is a runtime-state compatibility extension only; local DB schema remains **10** and hosted sync schema remains **1**.

### Exact run + round serialization
- Newly queued Raid actions are internally stamped to the exact Raid run and target round.
- A restored Beta 2 action that has no stamp is accepted once for compatibility and then replaced by normal Beta 3 round-scoped state.
- Raid timer work is now bound to both the observed `raid_instance_id` and observed round number.
- If another Bot connection has already advanced that same snapshot, the stale timer worker returns a silent no-op rather than resolving a second round.
- Beta 2 exactly-once victory/wipe settlement receipts remain intact and continue preventing duplicate rewards after the encounter ends.

### Trial & Raid Board clarity
- Live encounters now include a dedicated **Round Readiness** strip showing queued actions, actionable raiders, and how many are still waiting.
- **Last Trial Result** keeps the leading contributors visible with role, contribution score, damage, healing, and mitigation rather than only a condensed score row.
- The roomy two-column Trial catalog, full-width Bahamut capstone card, remembered collapse state, Trial Chronicle, and repeat-clear mastery remain unchanged.

### Privacy and authority
- Internal action stamps, exact Raid run IDs, and internal mechanic target IDs remain Bot-side and are not exposed through the public Overlay payload.
- Raid combat remains Twitch/Bot-authoritative; the Portal Trial & Raid Board remains read-only.

### Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-b3`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth/environment changes: **none**
- New environment variables: **none**

Deploy matching Beta 3 Web + Bot together.

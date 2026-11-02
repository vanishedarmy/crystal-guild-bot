# Crystal Guild v1.9.97.7 — Bot Integration V2.8 (Source Candidate)

## Starting point
- Based on the complete **V2.7 integrated Python Bot**, not the untouched older uploaded ZIP.
- The user's original Bot and live Bot/Web deployment are **not** changed.
- The full 618-item catalog, prior equipment buffs, and 108 Relic reward definitions are unmodified.

## Implemented in real Bot paths
1. **Monk — Combo Momentum:** The enhanced Classic/Ultimate Relic grants its own configured amount of AP only when a Monk lands three successive damaging attacks. The hit counter is encounter-local and server-owned, never a Twitch-supplied claim. Invalid/zero hits reset the chain when processed by the helper. AP cannot exceed max AP. This is connected to real active-battle ability and basic-attack resolvers, and raid ability and basic-attack resolvers.
2. **Monk — Fiststorm:** The existing Ultimate signature bonus is applied to Phantom Rush or Hundred Fists only when it is the verified third hit in a three-hit sequence; ordinary casts do not receive an unconditional finisher bonus.
3. **Paladin — Sacred Guard in raids:** Successfully using Cover on a *living, other* ally arms a one-hit protection charge when the appropriate Relic is equipped. The charge reduces the next positive direct incoming hit in scripted raid mechanics or standard raid boss attacks; a non-hit does not consume it. Reduction is calculated after ordinary defenses.
4. **Paladin — Aegis Reprisal in raids:** Surviving that protected hit arms the Ultimate signature. The next successful raid basic attack gains the configured bonus (Eternal: +18%) and consumes it once. No extra automatic counterattack is created.

## Deliberately not done
- No production Twitch deployment, real shared database migration or Web publishing was performed.
- The Thief has a `mug` offensive ability but **no verified Steal rewards pipeline**. No artificial loot was granted.
- Blue Mage currently unlocks its Blue Magic through job ability progression; no verified **learn-from-enemy** event exists. The learn-chance Relic trait remains inactive.
- Beastmaster's current `call_beast`/`king_of_beasts` are damage abilities, not a persisted **owned-tamed-pet** system; per-pet bonuses remain a future task.
- Raid edge cases, advanced encounter modes, and full Twitch/Portal integration still need a live-like QA pass.

## Validation
- New V2.8 tests: **11/11 pass** (Monk AP and Fiststorm, verified raid/active ability hits, Paladin Cover + scripted hit + Reprisal and entitlement denial).
- Combined focused regressions: **90/90 pass** across nine test modules, including previous V2.7, active battle, combat balance, selected raids and Relic integration.
- Separate legacy raid RC1 identity test expects version `1.9.9-skybound-singularity` rather than `1.9.97.7-regional-progression`; the same failure reproduces on V2.7 and is not introduced here.
- Python compilation passes; full project-wide suite has **not** been rerun end to end.

## Installation
Use either the **full Bot/** ZIP or the **delta Bot/** ZIP, not both. Stop the running Bot first, back up the player SQLite database and the old source, merge into a test deployment, then run representative hunts, ventures, raids and world events before production release.

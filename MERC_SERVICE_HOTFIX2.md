# Crystal Guild v1.8.0 Alpha 1 — Merc Service — Hotfix 2

## Contracted Hero roster state

Hotfix 2 repairs the Hero selection state after a Merc is hired.

- The active Hero now reports a distinct `contracted` roster state from the Bot Merc snapshot.
- The contracted Hero immediately displays the unavailable/locked-style card artwork in the Portal.
- The status badge reads **CONTRACTED**, with the reserved mission shown on the card.
- The active Hero no longer shows a Hire control while contracted.
- Other unlocked Heroes remain visibly **AVAILABLE**, but their Hire action reads **Contract Slot Occupied** while the one-contract limit is in use.
- Cancelling or consuming the contract removes the contracted state and returns the Hero to normal progression-based availability.
- Progression `available` remains separate from contract occupancy, so unlock state is not lost or rewritten.

### Currency follow-up

Merc contracts continue to use the existing **Hunt Seals** economy from Hotfix 1. No Hunt Marks currency is restored or introduced.

### Release contract

- Runtime/frontend: `1.8.0-merc-a1`
- Local DB schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- Migration: **none**
- Player reset: **none**

### Validation

- Frontend: **638/638** tests pass.
- Hosted Web/API: **78/78** tests pass.
- Bot: **726/726** tests + **30/30 subtests** pass.

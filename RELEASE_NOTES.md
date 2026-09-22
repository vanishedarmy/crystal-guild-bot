# Crystal Guild v1.9.0 Alpha 7 — Hall of Trophies

Alpha 7 rebuilds the profile Trophy Hall as a permanent, illustrated collection system.

## Trophy system
- Adds **30 trophies**: 11 World Events, 5 Raids, 4 Hunts, 4 Triple Triad, and 6 Fellowship construction trophies.
- Stable Trophy IDs are stored independently from display copy and artwork.
- New awards are idempotent and participant-specific for World Events and Raids.
- Fellowship trophies require an authoritative contribution to the completed project.
- Category-completion trophies derive from their required accomplishments and self-repair during reconciliation.

## Safe retroactive reconciliation
- Existing Raid, Hunt, Triple Triad, and Fellowship accomplishments are credited when current persistent records prove the requirement.
- Older World Events are **not guessed** from generic battle history. Exact variant participation is required.
- Reconciliation runs on Bot startup and before in-process Portal profile snapshots.

## Persistence
- Local schema: **20** (automatic migration from schema 19 with verified `pre_schema_20` backup).
- Hosted sync schema: **1**.
- Portal Action protocol: **36**.
- No player reset, economy rebalance, or combat/reward rebalance.

# Finalization Audit — Crystal Guild v1.7.0 Moogle Retainer

**Decision: PASS — production release baseline.**

## Frozen release contract

- Bot runtime: `1.7.0`
- Web runtime: `1.7.0`
- Frontend asset revision: `1.7.0-final`
- Local database schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **31**
- Twitch prefix: `!`

## Feature freeze

v1.7.0 closes with the complete Retainer Service and Moogle Emporium Annex feature set. Retainers provide personal timed material procurement with priority targeting and recent-haul history. The shared Moogle Emporium Annex expands personal shop rotations from 9 to 12 stock slots after construction. Gold Saucer production content carries forward unchanged.

The release also includes the final Render storage hardening, item-recovery verification and concise copy, Retainer artwork/UI, mobile/compactness fixes, text-spacing consistency, lazy loading, bounded static-art streaming, and browser ETag revalidation.

## Upgrade safety

No schema change is introduced by the production promotion. Existing schema-15 databases, player progression, inventories, Gil/MGP, Fellowship state, facilities, Retainer assignments/history, Gold Saucer records, Chocobo state, and raid/dungeon records are preserved. Keep the live database and secrets in place.

## Validation

Bot **668/668**, frontend **554/554**, hosted Web/API **63/63**, Python parse **132/132**, JS/MJS **202/202**, CSS **8/8**, WebP **843/843**, public PNG **0**.

The production package is feature-frozen. Future feature work should branch from this v1.7.0 baseline.

## Package hygiene

Superseded development release manifests, duplicate historical audit notes, and generated report folders are excluded from the production archives. Current deployment/setup documents use the v1.7.0 Moogle Retainer identity. Regression tests and active technical asset manifests remain available for the next development branch.

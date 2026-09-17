# Crystal Guild v1.8.0 Final — Merc Service

v1.8.0 Final promotes the RC3 candidate to the completed Merc Service release. No new gameplay features or balance changes are introduced in the Final pass; this release seals the tested RC feature set, release identity, documentation, and packages.

## Final feature set

- Hero Merc Service with Aerith, Tifa, Zidane, Yuna, Balthier, and Cloud.
- Existing **Hunt Seals** are the Merc contract currency; no separate Hunt Marks economy is used.
- Three independent assignment slots: one Hero for Hunt, one for Venture, and one for Raid.
- Mission eligibility, progression locks, occupied slots, contracted Heroes, and deployed Heroes all produce explicit availability states in the Portal.
- Deployed Heroes remain unavailable until their Hunt, Venture, or Raid resolves, including timed-Hunt restart recovery.
- Signature Hero contributions cover burst damage, healing, protection, extra finds, and rare-spoil support.
- Complete available/unavailable Merc artwork and service presentation.
- Responsive Portal hardening for desktop, tablet, and mobile layouts.
- Readable profile navigation with roomier desktop breakpoints and contained single-line labels.
- One shared manual **Refresh** control at the bottom of live Portal pages; automatic/live synchronization remains active.

## Release contract

- Runtime/frontend: `1.8.0-merc-final`
- Frontend package: `1.8.0`
- Local database schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- No player reset or Final-specific database migration.

## Upgrade path

RC3 upgrades directly to Final. Existing schema-17 player databases and active Merc state remain compatible. The original v1.8 schema migration remains the only database migration in this release line.

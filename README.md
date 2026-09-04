# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 1

Bot hotfix for **Encounter Variety**. Runtime: `1.7.1-resynthesis-a2h1`; paired Web remains `1.7.1-resynthesis-a2`; local database schema **15**; hosted sync **1**; Portal Action protocol **32**; command prefix `!`.

This hotfix fixes pathological repeated random monsters without changing rewards or the region rarity tables. Solo Venture and Expedition selectors widen a too-narrow level band to at least five valid monsters when the region can provide them. Rally Venture, Solo Venture, and Expeditions all use recent-encounter suppression: an immediate repeat is heavily reduced, and a third identical encounter in a row is blocked whenever another valid monster exists.

No database migration or player reset is required. See `RELEASE_NOTES.md`, `UPGRADE_GUIDE.md`, `ENCOUNTER_VARIETY_AUDIT.md`, and `VALIDATION_REPORT.md`.

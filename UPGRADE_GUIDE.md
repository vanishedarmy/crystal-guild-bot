# Crystal Guild v1.9.0 Alpha 5 — Title Status Hardening Upgrade Guide

## From v1.9.0 Alpha 4
Deploy the matching Alpha 5 Bot and Web packages together and restart the services. Existing player data, Titles, achievements, MGP, Trading Post listings, inventories, Fellowship state, Mercs, and Gold Saucer records are preserved.

No database migration is required for Alpha 4 → Alpha 5. The release continues to use:
- Runtime/frontend: `1.9.0-title-status-hardening-alpha5`
- Local schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**

On Bot startup, Alpha 5 performs a safe idempotent reconciliation of existing achievement and reward-Title state. Players who already satisfy a newly introduced requirement do not need to repeat the activity. Missing reward Titles attached to already-earned achievements are repaired automatically.

## Verification
1. Confirm `!cgversion` reports `1.9.0-title-status-hardening-alpha5`.
2. Open **Achievements & Titles** for an established hero and confirm previously earned Titles show **Unlocked**.
3. Confirm a permanent achievement remains visually complete even if a reversible current value (for example held Gil or inventory quantity) has since fallen below the original threshold.
4. Confirm secret achievements remain concealed until earned.
5. No manual SQL migration, Title reset, or player reset should be performed.

Older installations still upgrade through the existing verified migrations. v1.8.1 introduced schema **17 → 18** for Merc recruitment. v1.9.0 Alpha 1 introduced schema **18 → 19** for the Moogle Trading Post with its verified pre-migration backup. That migration preserves the existing `pre_schema_19` backup checkpoint before schema 19 is committed.

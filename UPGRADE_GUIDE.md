# v1.8.0 RC2 Upgrade Notes

RC2 upgrades cleanly from the sealed v1.8.0 RC1 Complete baseline. No database migration or player reset is required. Replace the Bot/Web trees with RC2 or apply the matching incremental patches.

The build changes presentation and release identity only: schema 17, hosted sync 1, Portal Action protocol 34, Merc Service rules, Hunt Seal economy, and player progression remain compatible.

## Existing v1.8 migration history

The earlier Merc Service Alpha migration from local schema **16 → 17** remains the only database migration in the v1.8 line. RC2 itself does not advance the schema; installations already on RC1 remain at schema 17 with no additional migration or player reset.

During that 16 → 17 migration, the upgrader creates the verified `pre_schema_17` backup before applying the schema change. RC2 does not recreate or require that backup on already-upgraded databases.

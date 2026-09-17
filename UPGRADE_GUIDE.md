# v1.8.0 RC3 Upgrade Notes

RC3 upgrades cleanly from v1.8.0 RC2. No database migration or player reset is required. Replace the Bot/Web trees with RC3 or apply the matching incremental patches.

RC3 changes Portal presentation and manual refresh placement only: schema 17, hosted sync 1, Portal Action protocol 34, Merc Service rules, Hunt Seal economy, and player progression remain compatible.

## Existing v1.8 migration history

The earlier Merc Service Alpha migration from local schema **16 → 17** remains the only database migration in the v1.8 line. RC3 itself does not advance the schema.

During the original 16 → 17 upgrade, the migration creates the verified `pre_schema_17` backup before applying schema changes. RC3 does not recreate or require that backup on databases already at schema 17.

# v1.8.0 Final Upgrade Notes

Crystal Guild v1.8.0 Final upgrades cleanly from v1.8.0 RC3. No player reset or Final-specific database migration is required. Replace the Bot/Web trees with the Final package or apply the matching RC3 → Final incremental patches.

## Compatibility

- Runtime/frontend: `1.8.0-merc-final`
- Local database schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- Existing Hunt Seal balances, Merc contracts/deployments, progression, inventory, equipment, Fellowship state, and Gold Saucer state remain compatible.

## Existing v1.8 migration history

The original Merc Service upgrade from local schema **16 → 17** remains the only database migration in the v1.8 line. That migration creates and verifies the `pre_schema_17` backup before applying schema changes. Players already on schema 17 do not repeat that migration or recreate the backup during the RC3 → Final upgrade.

Final does not advance the local schema, hosted sync schema, or Portal Action protocol.

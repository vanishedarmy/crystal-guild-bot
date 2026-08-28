# Validation Report — v1.2.0 Expeditions Alpha 1

## Identity
- Bot runtime: `1.2.0-expeditions-a1`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Twitch prefix: `!`

## Automated validation
- Bot regression suite: **417 tests + 30 subtests passed**.
- Expedition-specific tests cover schema/region catalog, Chocobo + Fellowship gates, travel timing, persistent run state, route choices, resource cache/banking, internal Camp, rescue protection, Adventure Board payload size, active-Expedition equipment locks, and Streamer Clear Adventures integration.
- Python package compilation completed without errors.

## Migration validation
- Built a real H9/schema-7 test database using the H9 runtime.
- Upgraded it through the v1.2 `upgrade_crystal_guild.py` path.
- Migration produced schema **8** and a verified `backups/pre_schema_8_<timestamp>.db` backup before structural changes.
- Existing player level/XP/Gil, Job state, and inventory remained present after migration.
- New `player_expeditions` and `player_region_exploration` tables were present after upgrade.

## Integration checks
- Equipment cannot be equipped or unequipped during an active Expedition.
- `!clearadventures` / Streamer Clear Adventures removes active Expedition rows in addition to field encounter, Hunt, and Solo Venture state while leaving secured regional exploration untouched.
- Existing raid/world-boss state and normal cooldowns remain outside Clear Adventures.
- H9 combat timing, LIVE field support, dynamic Camp, persistent Adventure results, and Streamer Inventory Admin regression coverage remains passing.

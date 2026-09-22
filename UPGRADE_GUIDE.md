# Crystal Guild v1.9.0 Alpha 8 — Seasonal Event Framework Upgrade Guide

Upgrade directly from **v1.9.0 Alpha 7 — Hall of Trophies** by deploying the matching Alpha 8 Bot and Web packages together.

## Compatibility
- Runtime/frontend: `1.9.0-seasonal-events-alpha8`
- Local database schema: **21**
- Hosted sync schema: **1**
- Portal Action protocol: **37**
- Database migration required: **Yes — automatic 20 → 21**
- Player reset required: **No**

The schema-21 migration adds reusable seasonal-event editions, player event progress, daily objective claims, exact seasonal monster clears, reward ownership, event trophies, and idempotent action receipts. A verified `pre_schema_21_<timestamp>.db` backup is created before migration.

## Deployment
1. Preserve the live database, Twitch token storage, `.env`, hosted secrets, and persistent-disk files.
2. Stop the paired Alpha 7 Bot and Web services.
3. Deploy the matching Alpha 8 Web and Bot packages (or apply the Alpha 7 → Alpha 8 overlay patch).
4. Start the Web service, then the Bot worker.
5. Confirm runtime/frontend `1.9.0-seasonal-events-alpha8`.
6. Confirm local schema **21**, hosted sync **1**, and Portal Action protocol **37**.
7. Open **Adventurer Profile → Seasonal Event** and verify **Night of the Hollow Crystal** appears.
8. Confirm the event initially reports **Disabled**. Seasonal monsters, the Hollow Warden, Moonlit Tokens, objectives, and seasonal shop rewards must not activate until the owner enables or schedules the event.
9. In **Streamer Control Center → Seasonal Event Control**, use the owner control to enable, pause/resume, disable, or select scheduled operation.

No player reset or manual event seeding is required.

## Older database lineage
Older installations continue through their existing verified migrations before Alpha 8: schema **17 → 18** Merc recruitment, **18 → 19** Trading Post, **19 → 20** Hall of Trophies, then **20 → 21** Seasonal Event Framework. Each structural step preserves verified backup behavior.

## Maintenance update: Alpha 8 package cleanup Hotfix 1
Already running Alpha 8? **No migration or protocol change.** Deploy the cleaned matching Bot/Web packages, or overlay the cleanup patch **and apply its deletion manifest** so previously deployed obsolete files are actually removed. Back up the existing installation/database/secrets first; the deletion list is restricted to superseded documentation and duplicate static art. Do not delete any database, token, `.env`, or overlay-state file.

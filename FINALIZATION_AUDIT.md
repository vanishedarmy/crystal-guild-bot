# Crystal Guild v1.4.0 — Dungeons & Delves RC1 Release Audit

## Frozen release contract
- Bot/Web/frontend: `1.4.0-dungeons-rc1`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`
- Dungeon catalog: **4**, feature frozen

## RC1 scope
No Dungeon content, reward, economy, combat, progression, schema, protocol, OAuth, or environment changes. RC1 is release identity cleanup, deployment/upgrade verification, stale setup-document cleanup, package hygiene, asset-route verification, and complete regression validation.

## Cleanup confirmed
- Bot Python project metadata now reports v1.4.0.
- Generated `overlay/state.json` is not shipped and is explicitly ignored.
- Legacy `RELEASE_NOTES_HOTFIX4.md` and `UPGRADE_GUIDE_HOTFIX4.md` are removed from the Bot release tree.
- Operational setup/maintenance/stress/migration/auth labels are current to v1.4.0 RC1.
- Player-facing Previous major updates remains stable-release-only.

## Deployment
Deploy matching RC1 Web + Bot together. Preserve the live database, `.env`, Twitch token storage, hosted secrets, and persistent-disk state. No migration is required from Beta 3.

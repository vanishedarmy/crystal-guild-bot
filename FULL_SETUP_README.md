# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 5 Setup

**Current Hotfix 5 note:** Gear Favorites now persist in the authoritative Crystal Guild player database. Deploy the matching Bot and Web together; the Bot performs an automatic schema **15 → 16** migration after creating a verified `pre_schema_16_*.db` backup. No player reset occurs.

## Existing installation
Preserve the live `crystal_guild.db`, Twitch token storage, `.env`, hosted secrets, and persistent-disk data. Deploy the matching Bot and Web source together, then restart the worker. The additive schema 15 → 16 migration is automatic and does not reset players.

## Release verification
- Bot runtime → `1.7.1-resynthesis-a2h5`
- Paired Web → `1.7.1-resynthesis-a2h5`
- Local DB schema → **16**
- Hosted sync schema → **1**
- Portal Action protocol → **33**
- Twitch prefix → `!`

## Hotfix verification
- AP survives switching to an MP Job, including equipment changes/refreshes while the AP family is inactive.
- MP survives switching to an AP Job under the same conditions.
- A genuinely depleted resource remains depleted after switching away and back.
- The one-time inactive-zero compatibility repair is receipt-protected and does not rerun.

## Carried-forward systems
- Resynthesis with permanent-destruction warning and deterministic material recovery.
- Gold Saucer Alpha 2 MGP rebalance and daily MGP reward.
- Encounter Variety Hotfix 1.
- Retroactive Job Quest Unlock Repair Hotfix 2.
- Moogle Retainer / Emporium Annex and existing player progression.

See `UPGRADE_GUIDE.md`, `RENDER_CLOUD_SETUP.md`, `WEB_SYNC_SETUP.md`, and `VALIDATION_REPORT.md` for deployment details.

## Twitch application and authorization
For fresh installs, register the local callback in the Twitch Developer Console:

https://dev.twitch.tv/console/apps

Redirect URL: `http://localhost:4343/oauth/callback`

The dedicated Bot authorization uses `user:read:chat`, `user:write:chat`, and `user:bot`. The broadcaster authorization includes `channel:bot` and the established subscription scope.

## Hosted Web and secret separation
Manage hosted services from:

https://dashboard.render.com

Keep `PORTAL_PUBLIC_URL` and `PORTAL_SYNC_KEY` in the appropriate environment configuration. Never put `crystal_guild.db`, Twitch token databases, `.env`, OAuth secrets, or live player state into public Web assets or source-control releases.

# Crystal Guild v1.5.0 — Trails & Raids Beta 2 Full Setup

This guide covers the supported local Windows runtime and Render cloud runtime. Beta 2 uses local DB schema **10**, hosted sync schema **1**, Portal Action protocol **25**, Twitch prefix **`!`**, and runtime `1.5.0-trails-raids-b2`.

## Existing installation
Preserve the live `crystal_guild.db`, `.env`, Twitch token storage, and persistent-disk data. Beta 2 requires no database migration from Beta 1 and introduces no new environment variables. Deploy the matching v1.5.0 Beta 2 Web + Bot together.

## Requirements
- Python 3.11+
- Twitch broadcaster account and dedicated Bot account
- Twitch Developer application
- Hosted Adventurer Portal for Portal sync/actions
- Render account/private repository when using cloud mode

## Twitch application and authorization
Register the local redirect URL in the Twitch Developer Console:

https://dev.twitch.tv/console/apps

Redirect URL: `http://localhost:4343/oauth/callback`

The dedicated Bot authorization uses the established `user:read:chat`, `user:write:chat`, and `user:bot` scopes. The broadcaster authorization includes `channel:bot` and `channel:read:subscriptions`. Use the packaged authorization helpers/control panel rather than copying tokens by hand.

## Hosted Web / secret separation
Render services are managed from https://dashboard.render.com. Keep `PORTAL_PUBLIC_URL` and `PORTAL_SYNC_KEY` in the appropriate Bot/Web environment configuration. **Never put** `crystal_guild.db`, Twitch token databases, `.env`, OAuth secrets, or live player state into a public repository or Web static assets.

## Local setup
1. Copy `.env.example` to `.env` only for a fresh installation; never overwrite an existing `.env` during an upgrade.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Complete Twitch authorization using the control-panel helpers.
4. Run `python run_maintenance.py --check` or the control-panel readiness option.
5. Start the Bot with `python run_bot.py`.

The established local OAuth redirect URL remains `http://localhost:4343/oauth/callback`.

## Cloud setup
The Render worker uses the persistent `/var/data` location for the live Guild database and Twitch token database. Existing secrets remain valid. Keep the old Bot stopped before the cloud worker connects, and run `python run_cloud_preflight.py` before first live startup or after moving private state.

Expected persistent paths are configured by `render.yaml`, including `/var/data/crystal_guild.db`, `/var/data/twitch_tokens.db`, and `/var/data/overlay/state.json`.

## Release verification
- `!cgversion` → `1.5.0-trails-raids-b2`
- `/api/health` → Web/frontend `1.5.0-trails-raids-b2`
- Local DB schema → **10**
- Hosted sync schema → **1**
- Portal Action protocol → **25**

Use `UPGRADE_GUIDE.md`, `RENDER_CLOUD_SETUP.md`, and `WEB_SYNC_SETUP.md` for focused deployment notes.

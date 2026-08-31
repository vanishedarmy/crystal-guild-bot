# Crystal Guild v1.6.0 — Gold Saucer Alpha 1 Full Setup

This guide covers the supported local Windows runtime and Render cloud runtime. Gold Saucer Alpha 1 uses local DB schema **11**, hosted sync schema **1**, Portal Action protocol **26**, Twitch prefix **`!`**, and runtime `1.6.0-gold-saucer-a1h2`.

## Existing installation
Preserve the live `crystal_guild.db`, `.env`, Twitch token storage, hosted secrets, and persistent-disk data. Upgrading from v1.5.1 performs the additive schema **10 → 11** migration after a verified pre-migration backup. No player reset, OAuth reauthorization, or new environment variable is required. Deploy the matching v1.6.0 Alpha 1 Web + Bot together.

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

The dedicated Bot authorization uses the established `user:read:chat`, `user:write:chat`, and `user:bot` scopes. The broadcaster authorization includes `channel:bot` and `channel:read:subscriptions`. Existing authorized installs do not need to reauthorize for Gold Saucer Alpha 1.

## Hosted Web / secret separation
Keep `PORTAL_PUBLIC_URL` and `PORTAL_SYNC_KEY` in the appropriate Bot/Web environment configuration. Never put `crystal_guild.db`, Twitch token databases, `.env`, OAuth secrets, or live player state into public Web assets or source-control releases.

## Local setup
1. Copy `.env.example` to `.env` only for a fresh installation; never overwrite an existing `.env` during an upgrade.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Complete Twitch authorization using the control-panel helpers if this is a fresh install.
4. Run `python run_maintenance.py --check` or the control-panel readiness option.
5. Start the Bot with `python run_bot.py`.

The established local OAuth redirect URL remains `http://localhost:4343/oauth/callback`.

## Cloud setup
Open the Render dashboard when creating or updating the hosted worker/Web services:

https://dashboard.render.com

The Render worker uses the persistent `/var/data` location for the live Guild database and Twitch token database. Existing secrets remain valid. Keep the old Bot stopped before the cloud worker connects, and run `python run_cloud_preflight.py` before first live startup or after moving private state.

Expected persistent paths are configured by `render.yaml`, including `/var/data/crystal_guild.db`, `/var/data/twitch_tokens.db`, and `/var/data/overlay/state.json`.

## Gold Saucer verification
- Open your own Adventurer Portal character and select **Gold Saucer**.
- First visit grants the one-time **500 SP** welcome purse; from the next UTC day onward, the first Saucer visit each day grants the **50 SP floor allowance**.
- Mini Cactpot opens a persistent daily ticket and survives refresh/restart.
- Crystal Slots resolves through the authoritative Bot and observes its server cooldown.
- The Prize Counter spends SP only on cosmetic Gold Saucer Titles and never changes combat power or Gil.
- Ordinary Gil is unchanged by Gold Saucer play.

## Release verification
- `!cgversion` → `1.6.0-gold-saucer-a1h2`
- `/api/health` → Web/frontend `1.6.0-gold-saucer-a1h2`
- Local DB schema → **11**
- Hosted sync schema → **1**
- Portal Action protocol → **26**

Use `UPGRADE_GUIDE.md`, `RENDER_CLOUD_SETUP.md`, and `WEB_SYNC_SETUP.md` for focused deployment notes.

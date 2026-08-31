# Crystal Guild v1.6.0 — Gold Saucer Alpha 1 Render Cloud Setup

## Existing cloud deployment
Gold Saucer Alpha 1 is an in-place paired update from v1.5.1. Preserve the worker's persistent state and existing Render secrets. Do not upload packaged databases or token files with source.

Typical persistent paths:
```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
/var/data/overlay/state.json
```

Deploy the matching v1.6.0 Alpha 1 Web + Bot together. On first Bot startup, the local database performs the additive **schema 10 → 11** migration after creating and verifying a pre-migration backup. Hosted sync remains **1** and Portal Action protocol advances to **26**. No player reset, OAuth reauthorization, or new environment variable is required.

After deployment verify `!cgversion`, `!health`, and `/api/health`, then open **Gold Saucer** from your own Portal profile and confirm the one-time 500 SP welcome purse, Mini Cactpot, and Crystal Slots.

## Fresh Render deployment
Create the worker from `render.yaml`, configure the required Twitch/Portal secrets, place private persistent state only on the persistent disk, and run:
```bash
python run_cloud_preflight.py
```
Continue only after the preflight passes. Keep any old local/cloud Bot instance stopped before the v1.6.0 Alpha 1 worker connects.

The hosted raid overlay remains available from the matching Web service at `/overlay`.

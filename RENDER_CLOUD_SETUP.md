# Crystal Guild v1.5.1 — Relic Arsenal Complete Render Cloud Setup

## Existing cloud deployment
Beta 3 is an in-place paired source update from Beta 3 and remains compatible with the existing schema-10 production data. Preserve the worker's persistent state and existing Render secrets. Do not upload packaged databases or token files with source.

Typical persistent paths:
```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
/var/data/overlay/state.json
```

Deploy the matching v1.5.1 Web + Bot together, then verify `!cgversion`, `!health`, and `/api/health`. Local DB schema remains **10**, hosted sync schema **1**, and Portal Action protocol **25**. No player reset or database migration is required from v1.5.0.

## Fresh Render deployment
Create the worker from `render.yaml`, configure the required Twitch/Portal secrets, place private persistent state only on the persistent disk, and run:
```bash
python run_cloud_preflight.py
```
Continue only after the preflight passes. Keep any old local/cloud Bot instance stopped before the v1.5.1 worker connects.

The hosted raid overlay remains available from the matching Web service at `/overlay`.

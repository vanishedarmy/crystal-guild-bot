# Crystal Guild v1.9.0 Alpha 8 — Seasonal Event Framework Render Cloud Setup

Preserve the live persistent disk and secrets before deployment. Deploy the **Alpha 8 Seasonal Event Framework Bot and matching Web build together**, then restart the services.

Verify `!cgversion` reports `1.9.0-seasonal-events-alpha8`, local schema **21**, hosted sync **1**, Portal Action protocol **37**, and `!health` is clean. Existing schema 20 databases receive a verified `pre_schema_21_<timestamp>.db` backup before migration.

The installed **Night of the Hollow Crystal** event is disabled by default. Use Streamer Control Center seasonal controls only when you are ready to activate or schedule it.

## Persistent Render paths
- Main database: `/var/data/crystal_guild.db`
- Twitch token store: `/var/data/twitch_tokens.db`
- Run `python run_cloud_preflight.py` before a production migration when validating persistent-disk readiness.
- The paired Web service continues to serve the `/overlay` route used by the OBS/live presentation layer.

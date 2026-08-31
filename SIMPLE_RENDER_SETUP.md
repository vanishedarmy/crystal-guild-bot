# Crystal Guild v1.5.0 — Trails & Raids Alpha 7 Simplified Render Setup

**Existing cloud install:** deploy the Alpha 7 Bot source without touching `/var/data`, then deploy the matching v1.5.0 Alpha 7 Web source. Verify `!cgversion` = `1.5.0-trails-raids-a7`, `!health`, and `/api/health`.

1. Preserve Render environment variables and persistent disk.
2. Stop any duplicate/local Bot instance.
3. Deploy the Alpha 7 worker source.
4. Confirm the worker reaches Twitch and Portal Sync.
5. Deploy/restart the matching Alpha 7 Web service.
6. Confirm the Trial & Raid Board shows Bahamut — The Final Coil.

Schema **10**, hosted sync **1**, protocol **25**. Alpha 7 adds no environment variables.

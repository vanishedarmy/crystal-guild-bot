# Crystal Guild v1.5.0 — Trails & Raids Beta 3 Simplified Render Setup

**Existing cloud install:** deploy the Beta 3 Bot source without touching `/var/data`, then deploy the matching v1.5.0 Beta 3 Web source. Verify `!cgversion` = `1.5.0-trails-raids-b3`, `!health`, and `/api/health`.

1. Preserve Render environment variables and persistent disk.
2. Stop any duplicate/local Bot instance.
3. Deploy the Beta 3 worker source.
4. Confirm the worker reaches Twitch and Portal Sync.
5. Deploy/restart the matching Beta 3 Web service.
6. Confirm the Trial & Raid Board shows the Trial Chronicle and retained Bahamut — The Final Coil capstone.

Schema **10**, hosted sync **1**, protocol **25**. Beta 3 adds no environment variables.

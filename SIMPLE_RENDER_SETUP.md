# Crystal Guild v1.4.0 — Dungeons & Delves RC1 Simplified Render Setup

**Existing cloud install:** push/deploy the RC1 Bot source without touching `/var/data`, then deploy the matching RC1 Web source. Verify `!cgversion` = `1.4.0-dungeons-rc1`, `!health`, and `/api/health`.

**Fresh setup:**
1. Prepare the Bot source in a private repository.
2. Configure the secrets required by `render.yaml`.
3. Put live databases/token storage only on the persistent disk.
4. Run `python run_cloud_preflight.py`.
5. Ensure no older Bot instance is connected.
6. Start the worker and deploy the matching RC1 Web service.

Schema **10**, hosted sync **1**, protocol **25**. RC1 adds no environment variables.

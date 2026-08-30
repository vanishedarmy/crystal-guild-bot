# Crystal Guild v1.5.0 — Trails & Raids Alpha 2 Simplified Render Setup

**Existing cloud install:** deploy the Alpha 2 Bot source without touching `/var/data`, then deploy the matching v1.5.0 Alpha 2 Web source. Verify `!cgversion` = `1.5.0-trails-raids-a2`, `!health`, and `/api/health`.

**Fresh setup:**
1. Prepare the Bot source in a private repository.
2. Configure the secrets required by `render.yaml`.
3. Put live databases/token storage only on the persistent disk.
4. Run `python run_cloud_preflight.py`.
5. Ensure no older Bot instance is connected.
6. Start the worker and deploy the matching v1.5.0 Alpha 2 Web service.

Schema **10**, hosted sync **1**, protocol **25**. Alpha 2 adds no environment variables.

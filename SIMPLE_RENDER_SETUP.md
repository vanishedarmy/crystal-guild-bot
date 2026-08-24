# Crystal Guild v1.1.16 — Arsenal Simplified Render Bot Setup

**Already on v1.1.13 cloud?** Push this Bot source to the existing private repository. Do not touch `/var/data`. After Render restarts, verify `!cgversion` and `!health`, then update the matching Web service.

**Fresh setup?**
1. Preserve `.env` + live `crystal_guild.db` locally and make a verified backup.
2. Create/import `twitch_tokens.db` with the included authorization/migration helpers.
3. Put source only in a private GitHub repository.
4. Create the Render worker from `render.yaml` and set the six required secrets.
5. Transfer `crystal_guild.db` and `twitch_tokens.db` to `/var/data`.
6. Run `python run_cloud_preflight.py`.
7. Keep the old local Bot OFF and restart the worker.
8. Verify `!cgversion` = `1.1.16-arsenal-h1` and `!health` is healthy.
9. Deploy matching v1.1.16 Web and point OBS to `https://YOUR-SITE/overlay`.

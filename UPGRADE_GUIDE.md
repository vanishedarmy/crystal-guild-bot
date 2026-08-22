# Crystal Guild Bot v1.1.14 — Cloud Continuity Upgrade

## Existing v1.1.13 Render worker

1. Do not delete or replace the `/var/data` disk.
2. Do not re-transfer `crystal_guild.db` or `twitch_tokens.db`.
3. Update the private Bot GitHub repository with this package.
4. Let Render redeploy `crystal-guild-bot`.
5. Verify `!cgversion` reports `1.1.14-cloud-continuity` and `mode=cloud`.
6. Verify `!health` is healthy and one known hero retains progression.
7. Deploy the matching v1.1.14 Web package.

No player reset, DB migration, OAuth reauthorization, token migration, new environment variable, hosted sync-schema bump, or Portal Action protocol change is required.

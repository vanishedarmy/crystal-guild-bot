# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 1 Upgrade

For an already-running v1.1.14 Render Bot:

1. Do **not** modify `/var/data`, `crystal_guild.db`, or `twitch_tokens.db`.
2. Overlay the Hotfix 1 Bot Patch into the private Bot GitHub repository.
3. Commit and push.
4. Let Render redeploy `crystal-guild-bot`.
5. Run `!cgversion` and confirm `1.1.14-cloud-continuity-h1`.
6. Run `!streamstatus`; while the channel is offline it should report `OFFLINE`.
7. While offline, try `!venture`; it should be refused with the live-stream-only message.
8. Go live (or test during the next stream), run `!streamstatus`, and confirm `LIVE`; `!venture` should then behave normally.
9. Verify a Portal Solo Venture still works while Twitch is offline.

No Web deploy, DB migration, OAuth reauthorization, new Render secret, or player reset is required.

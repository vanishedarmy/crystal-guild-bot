# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 2 Upgrade

This update keeps DB schema 4 and does not modify player progression. It does require one broadcaster OAuth refresh so Crystal Guild can read subscriber tiers.

## 1. Update the Bot source

1. Back up/commit the current private Bot GitHub repository.
2. Overlay the Hotfix 2 Bot patch.
3. Commit and push.
4. Let Render redeploy.
5. `!cgversion` should report `1.1.14-cloud-continuity-h2`.

Subscriber perks may report UNKNOWN until the broadcaster token is refreshed. Normal gameplay remains available.

## 2. Refresh the broadcaster Twitch token locally

Use a private local Hotfix 2 Bot folder containing your existing `.env`.

If you still have the previous `twitch_tokens.db`, place it in the Bot folder. Otherwise authorize both accounts again.

1. Stop any local Crystal Guild Bot.
2. Run `run_cloud_token_authorization.bat` and let the temporary OAuth server start.
3. Run `open_twitch_authorization.bat` in a second window.
4. Choose **Authorize BROADCASTER / OWNER account** and approve the requested `channel:read:subscriptions` permission while logged in as the broadcaster.
5. If the local token DB did not already contain the dedicated bot account, authorize the dedicated Bot account too.
6. Stop the temporary authorization session cleanly with Ctrl+C.
7. Run `python prepare_render_migration.py --token-db twitch_tokens.db` if you want the helper to validate/copy the token database.

Never commit `twitch_tokens.db` to GitHub.

## 3. Replace the private token database on Render

1. Stop/restart-safe the `crystal-guild-bot` worker before replacing token state.
2. Transfer the refreshed `twitch_tokens.db` privately to Render (the same Magic Wormhole method used for v1.1.13 is fine).
3. Place it exactly at `/var/data/twitch_tokens.db`.
4. Restart the worker.
5. Run `!substatus` from a subscribed account. It should report the Twitch tier instead of UNKNOWN.

Do **not** replace `crystal_guild.db`; there is no player-data migration in Hotfix 2.

## 4. Deploy the matching Web update

Overlay/push the Hotfix 2 Web patch into the existing Web repository. No Web OAuth or secret change is required.

Verify the signed-in Overview Daily Guild Provisions card describes randomized provision bundles and shows the detected subscriber perk when applicable.

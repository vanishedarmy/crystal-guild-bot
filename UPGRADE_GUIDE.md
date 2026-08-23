# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 3 Upgrade

Hotfix 3 is an in-place-safe Bot + Web update for v1.1.14 Cloud Continuity Hotfix 2. Local DB schema 4, hosted sync schema 1, and Portal Action protocol 12 are unchanged.

## Upgrade from Hotfix 2

1. Back up/commit the current private Bot and Web repositories.
2. Preserve all runtime/private state, especially `.env`, `crystal_guild.db`, `twitch_tokens.db`, and Render persistent-disk contents.
3. Overlay the **Hotfix 3 Bot Patch from Hotfix 2** into the Bot repository and deploy it.
4. Overlay the **Hotfix 3 Web Patch from Hotfix 2** into the Web repository and deploy it.
5. Restart/redeploy the Bot and Web services normally.
6. Verify `!cgversion` / `!health` reports Bot runtime `1.1.14-cloud-continuity-h3`.
7. Verify Web `/api/health` reports runtime `1.1.14-cloud-continuity-h3` and frontend revision `1.1.14-continuity3`.
8. During a live Raid, join a hero and verify `!attack`, `!ability`, `!defend`, and `!use` queue and resolve on the next Raid round.
9. Start a live Rally Venture and confirm its active encounter information remains inside the existing Rally Venture panel rather than appearing below Current Region.
10. Check Portal action/filter buttons on desktop and narrow/mobile widths for clear labels, selected states, focus states, and readable disabled states.

No database migration helper is required and `crystal_guild.db` must not be replaced.

## If upgrading from Hotfix 1 or earlier

Use the Complete/Bot/Web packages rather than the surgical Hotfix-2-to-Hotfix-3 patches. Existing player progression remains schema-4 compatible.

Cloud installs that have not yet completed Hotfix 2's Twitch subscriber authorization must still authorize the broadcaster token with `channel:read:subscriptions` and refresh the private `twitch_tokens.db`. That is an inherited Hotfix 2 requirement, not a new Hotfix 3 scope.

## Release identity

- Bot runtime: `1.1.14-cloud-continuity-h3`
- Hosted sync version/snapshots: `1.1.14-cloud-continuity`
- Frontend asset revision: `1.1.14-continuity3`
- Local DB schema: 4
- Hosted sync schema: 1
- Portal Action protocol: 12
- Twitch prefix: `!`

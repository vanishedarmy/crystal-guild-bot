# Crystal Guild Bot v1.1.14 — Cloud Continuity Hotfix 1

Hotfix 1 adds an authoritative Twitch **stream-presence gate** for chat gameplay that belongs to the live show. Crystal Guild itself remains online 24/7 on Render, while live-stream gameplay is available only when Twitch reports the broadcaster as actively live.

## Live-stream-only Twitch gameplay

The following Twitch chat mutations now require the channel to be LIVE:

- `!venture` / Rally Venture
- `!join` / Rally participation
- `!hunt <name>` / starting an Active Hunt
- `!attack`, `!ability`, `!defend` / Active Battle actions
- `!raid`, `!limit`, `!summon`, `!revive` / Raid participation and actions

Read-only commands remain available while offline, including hero/inventory/catalog/status/help commands. Non-stream progression such as recovery, equipment, shops, crafting, Fellowship contributions, Daily, and Chocobo management also remains available.

The authenticated Portal remains deliberately off-stream capable. **Portal Solo Venture and Portal Challenge Hunt are not blocked by the Twitch live gate.**

## Twitch live check

Crystal Guild checks Twitch's Get Streams API using the existing `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET`. No additional OAuth scopes or Render secrets are required. Results are briefly cached to avoid API spam. If Twitch cannot be checked and the last successful result becomes stale, live-only mutations fail closed until status can be confirmed again.

Streamer diagnostics:

```text
!streamstatus
!health
```

`!health` now includes `stream=LIVE`, `stream=OFFLINE`, or `stream=UNKNOWN`.

## Compatibility

- Runtime: `1.1.14-cloud-continuity-h1`
- Hosted sync runtime remains compatible with `1.1.14-cloud-continuity`
- DB schema: 4
- Hosted sync schema: 1
- Portal Action protocol: 12
- Twitch prefix: `!`
- Database migration: none
- Player reset: none
- New required environment variables: none
- Web redeploy required: no

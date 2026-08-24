# Crystal Guild v1.1.17 — Arsenal II Full Setup

This guide covers both supported operating modes:

1. **Local Windows runtime** — the traditional Crystal Guild setup.
2. **Render Cloud Continuity** — the authoritative Bot runs continuously online.

v1.1.16 keeps the established local/cloud deployment model and Wayfarer Solo Venture persistence while expanding Job abilities and early-game Hunts, World Bosses, and consumable crafting. Local database schema remains **5**, hosted sync schema remains **1**, Portal Action protocol remains **14**, and the Twitch prefix remains **`!`**.

---

## 1. Requirements

Local mode requires Python 3.11+ and internet access. Cloud mode uses the included Render Blueprint with Python 3.11.11.

You need:

- a Twitch broadcaster account;
- a dedicated Twitch bot account;
- a Twitch Developer application;
- the existing hosted Adventurer Portal if Portal sync/actions are desired;
- for cloud mode, a Render account and private GitHub repository.

---

## 2. Twitch application and local authorization

The established local OAuth Redirect URL is:

```text
http://localhost:4343/oauth/callback
```

Register that exact callback in the Twitch Developer Console:

```text
https://dev.twitch.tv/console/apps
```

Start the Bot locally before authorizing. For the dedicated bot account use:

```text
http://localhost:4343/oauth?scopes=user:read:chat%20user:write:chat%20user:bot&force_verify=true
```

For the broadcaster account use:

```text
http://localhost:4343/oauth?scopes=channel:bot%20channel:read:subscriptions&force_verify=true
```

Use the authorization helper if desired:

```text
open_twitch_authorization.bat
```

TwitchIO normally saves these managed tokens in `.tio.tokens.json`. Keep that file private.

---

## 3. Local Windows setup

Run:

```text
setup_windows.bat
```

Then configure `.env`. Core values include:

```text
TWITCH_CLIENT_ID=
TWITCH_CLIENT_SECRET=
TWITCH_BOT_ID=
TWITCH_OWNER_ID=
BOT_PREFIX=!
DATABASE_PATH=crystal_guild.db
DATA_DIR=data
```

If using the hosted Portal, also configure:

```text
PORTAL_PUBLIC_URL=https://your-public-portal.example
PORTAL_SYNC_KEY=<private shared key>
PORTAL_SYNC_SECONDS=5
PORTAL_SYNC_HEARTBEAT_SECONDS=30
PORTAL_SYNC_TIMEOUT_SECONDS=10
PORTAL_SYNC_VERIFY_TLS=true
```

Start local services with `CRYSTAL_GUILD_CONTROL_PANEL.bat`, or individually with:

```text
run_bot.bat
run_portal_sync.bat
run_overlay.bat
```

The standalone Portal sync is intentionally still supported in local mode.

---

## 4. Local validation

Run:

```text
run_selftest.bat
run_recovery_drill.bat
run_stress_test.bat
```

Owner diagnostics in Twitch:

```text
!cgversion
!health
```

`!cgversion` should report **v1.1.17 Arsenal II**.

---

## 5. Moving the live Guild to Render

Render dashboard:

```text
https://dashboard.render.com
```


Use the dedicated guide:

```text
RENDER_CLOUD_SETUP.md
```

The short version is:

```bat
python run_maintenance.py --backup --recovery-drill
python prepare_render_migration.py
```

If the current install has no `.tio.tokens.json`, first run `run_cloud_token_authorization.bat`, authorize both Twitch accounts locally, and prepare with `python prepare_render_migration.py --token-db twitch_tokens.db`.

Then deploy the source with `render.yaml`, privately transfer the prepared `crystal_guild.db` and `twitch_tokens.db` into `/var/data`, and run:

```bash
python run_cloud_preflight.py
```

Cloud mode runs the Bot, autonomous combat service, notification dispatcher, Portal Actions, and sanitized Portal sync in one Render Background Worker.

---

## 6. Render environment variables

The Blueprint provides non-secret defaults. Render asks you for:

```text
TWITCH_CLIENT_ID
TWITCH_CLIENT_SECRET
TWITCH_BOT_ID
TWITCH_OWNER_ID
PORTAL_PUBLIC_URL
PORTAL_SYNC_KEY
```

Cloud persistent paths are:

```text
DATABASE_PATH=/var/data/crystal_guild.db
TWITCH_TOKEN_DB=/var/data/twitch_tokens.db
LOG_DIR=/var/data/logs
OVERLAY_STATE_PATH=/var/data/overlay/state.json
```

The worker defaults to:

```text
CRYSTAL_GUILD_RUNTIME_MODE=cloud
PORTAL_SYNC_IN_PROCESS=true
CLOUD_REQUIRE_EXISTING_DATABASE=true
```

The bootstrap guard is deliberately fail-closed. If the private DB/token state is missing or invalid, the worker waits instead of creating a new Guild.

---

## 7. Never put these in GitHub or the public Web service

```text
.env
.tio.tokens.json
crystal_guild.db
crystal_guild.db-wal
crystal_guild.db-shm
twitch_tokens.db
render_migration/
TWITCH_CLIENT_SECRET
PORTAL_SYNC_KEY
Bot logs
Bot backups
```

The hosted Portal is a sanitized mirror/relay. It does not receive the authoritative game database or Twitch credential database.

---

## 8. Database and progression

v1.1.15 advances the local schema **4 → 5** by adding persistent per-player Solo Venture state. Existing player IDs, levels, XP/JP, Gil, Hunt Seals, HP/MP/AP, Jobs, Masteries, equipment, inventory, crafting and forge progression, cooldowns, region, Bestiary, achievements, titles, records, Relics, Fellowship, Chocobo progression, and runtime state remain authoritative in the same database.

For an existing populated schema-4 Guild, the `Database` class creates and verifies `backups/pre_schema_5_<timestamp>.db` before applying the additive migration. Verification includes SQLite `quick_check` and player-count parity. No player reset is required.

---

## 9. Portal operation

The public Portal keeps hosted sync schema **1** and advances Portal Action protocol to **13** for the typed interactive Solo Venture actions.

Local mode:

```text
Bot --> standalone run_portal_sync.py --> hosted Web
```

Cloud mode:

```text
Render Bot worker --> integrated Portal sync/actions --> hosted Web
```

Do not run both sync methods against the same authoritative Guild at once.

The consolidated v1.1.16 Complete build includes a matching Web package. Deploy the v1.1.16 Web package with the Arsenal Bot so gameplay data, Guide content, and frontend ability references remain aligned.

---

## 10. OBS overlay

The traditional OBS raid overlay remains a local optional tool. `run_overlay.bat` can still be run on the streaming PC if desired. Moving the authoritative Bot to Render does not automatically turn the local overlay into a hosted overlay.

---

## 11. Updating after cloud cutover

For later Bot releases:

1. Keep a verified backup.
2. Push source changes to the GitHub repository linked to the worker.
3. Render rebuilds/restarts the worker.
4. `/var/data` persists across deployments.
5. Run the release-specific migration procedure only when a future release explicitly advances the DB schema.

Because the worker uses a persistent disk, a deployment may have a brief stop/start interruption. Player state remains on the disk and the Bot reconnects after startup.

---

## 12. Troubleshooting

### Worker says CLOUD BOOTSTRAP REQUIRED

The worker is protecting the existing Guild. Confirm these files exist:

```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
```

Then run `python run_cloud_preflight.py`.

### Token DB missing bot/owner ID

Re-run `prepare_render_migration.py` locally using the working `.tio.tokens.json`, or explicitly specify the correct token file. Do not paste tokens into source code.

### Portal is OFFLINE

Check `PORTAL_PUBLIC_URL`, `PORTAL_SYNC_KEY`, worker logs, and `!health`. In cloud mode, Portal sync should report `running` rather than `external`.

### Bot is responding twice

The old local Bot is probably still running. Only one authoritative Bot instance should be connected after cutover.

### Need to remain local

Set or leave:

```text
CRYSTAL_GUILD_RUNTIME_MODE=local
```

Local operation remains a supported v1.1.14 mode.

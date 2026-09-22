# Crystal Guild — Bot (v1.9.0 Alpha 8)

Twitch/chat and gameplay authority for Crystal Guild. Deploy this package with the matching Alpha 8 Web/Portal package.

**Runtime:** `1.9.0-seasonal-events-alpha8` · **Local schema:** 21 · **Hosted sync:** 1 · **Portal Action protocol:** 37. No player reset.

**Upgrading Alpha 8 installations:** this cleanup hotfix changes documentation and static art only; it does not require a migration or configuration changes. See `UPGRADE_GUIDE.md` for removing obsolete files from an existing directory.

**Other upgrades:** preserve the live database, Twitch tokens, `.env` and persistent secrets. The database automatically applies sequential migrations, with a verified backup before schema 21.

**Key guides:** `FULL_SETUP_README.md` (new installations), `RENDER_CLOUD_SETUP.md` (Render), `WEB_SYNC_SETUP.md` (hosted synchronization), `PORTAL_ACTIONS_SETUP.md` (action authority), `MANUAL_TEST_CHECKLIST.md` (verification). See `CHANGELOG.md` for the condensed release history and `RELEASE_NOTES.md` for current features.

Halloween content is **disabled by default**; enable it from the Streamer Control Center when ready.

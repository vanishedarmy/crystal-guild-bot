# Crystal Guild — Bot (v1.9.0 Alpha 13: Trading Post QoL)

The authoritative Twitch/chat game engine, Trading Post economy and player database. **Deploy this Bot with the matching Alpha 13 Web source**, not an earlier Portal version.

- Release: `1.9.0-trading-post-qol-alpha13`
- Local Bot SQLite schema: **25** (automatic upgrade from Alpha 12 schema 24 with verified backup)
- Hosted sync schema: **1** (unchanged)
- Portal Action protocol: **39** (must match hosted Web)

This release persists each player's 30-item Trading Post watchlist, supplies completed-sale price history, shows owned quantities, and supports quick relist through the existing authoritative listing action. Existing listing fees, taxes and anti-duplication safeguards are preserved. See root `RELEASE_NOTES.md` and `TRADING_POST_ALPHA13_VALIDATION.md`.

**Upgrade:** Preserve the live database, credentials, secrets and runtime volumes, back them up, and consult root `START_HERE.md` or this folder's `UPGRADE_GUIDE.md`. Do not run the previous Bot against an upgraded schema-25 database. `FULL_SETUP_README.md`, `RENDER_CLOUD_SETUP.md` and `WEB_SYNC_SETUP.md` contain additional hosting guidance; historical feature documents are retained as history, not a current release contract.

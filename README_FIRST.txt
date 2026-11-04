CRYSTAL GUILD v2.1.1 — ADVENTURE TALES
Version-only patch on top of v2.1.0 Dungeon Art / Expedition XP / Adventure Board.
Game content, Portal Action protocol 40, database schema and assets unchanged.
See RELEASE_NOTES.md. Earlier release notes below are historical.
=============================================

> **v2.1.0 Activity Resolution Hotfix (November 4, 2026):** Deploy matching Bot and Web together. Portal Action protocol is now **40** (previously 39); timed Hunts have automatic overdue recovery plus a safe **Finish Hunt** action. No database migration or new artwork is required. See `INSTALL_ACTIVITY_RESOLUTION_V210.md` in the release root. Older version/protocol references below are historical.

CRYSTAL GUILD v2.1.0 — ADVENTURE TALES
CURRENT SOURCE RELEASE: Read RELEASE_NOTES.md for update and installation details.
Preserve the live database and configuration. Complete active battles before upgrading.
Previous release instructions follow for historical reference.
=============================================

CRYSTAL GUILD v2.0.0 — ITEM RECLASSIFICATION
CURRENT SOURCE RELEASE: Read RELEASE_V2.0.0_README.md and RELEASE_NOTES.md.
Back up existing databases/config, and rebuild the Web frontend before deploying.
Older setup and historical release notes follow below for reference only.
=============================================

# CURRENT RELEASE: v1.9.8 — Airship Expedition

See `RELEASE_NOTES.md` and the `AIRSHIP_EXPEDITION_198.md` release guide. Existing setup and Queen’s Blood instructions remain relevant to previously released features.

# Crystal Guild v1.9.7 — Queen’s Blood

This is the complete Bot + Web release. It includes all 48 approved Queen’s Blood portraits, the solo circuit, live invitations, correspondence duels, and the prebuilt frontend.

## Upgrade an existing installation

1. Stop the Bot and hosted Web services. Back up both live databases and your current installation.
2. Copy the contents of `Bot/` and `Web/` into their corresponding deployment roots. Preserve your private configuration, environment variables, tokens, session secrets, live databases, backups, and persistent data mounts. Do not replace live data with a new empty database.
3. Replace the deployed `Web/frontend/dist/` with the complete included `dist/` folder so retired frontend chunks do not accumulate. The complete source artwork is also included in `Web/frontend/public/`.
4. Restart both services and refresh the Portal. The release label should read **v1.9.7 — Queen’s Blood**. Sign in, open your own adventurer profile, and choose **Card Hall**.

**No npm rebuild is needed.** `Web/Dockerfile.prebuilt` serves the included production output. The normal `Web/Dockerfile` keeps its usual source-build workflow. For an optional local rebuild, run `npm ci --include=dev` and `npm run build` in `Web/frontend/`.

For a new installation, use `Bot/FULL_SETUP_README.md`, `Bot/RENDER_CLOUD_SETUP.md`, `Bot/WEB_SYNC_SETUP.md`, and `Web/HOSTING_GUIDE.md` to configure the services. The release contains no live databases or configured secrets.

## Compatibility

Bot database schema stays **27**, hosted sync schema stays **1**, and Portal Action protocol stays **39**. Queen’s Blood creates its own tables in the hosted Web database as needed. Preserve that database: it holds card unlocks, saved decks, solo matches, and player duels. Existing matches keep their frozen card definitions and rules. Existing correspondence invitations retain their original deadlines and play style.

Triple Triad is played in the standalone Card Hall, separate from Gold Saucer. Queen's Blood is also available in Card Hall. The latest compact UI, wrapping corrections, Camp contrast, Emporium, Seasonal Cache, and Triple Triad progression fixes are carried forward from the approved source. Abandoned Living World 1A/1B and Accessibility v1.9.4.4 packages are not used.

See `RELEASE_NOTES.md` for features and `VALIDATION_v1_9_7.json` for checks and limitations. This package has not been deployed to your live services.

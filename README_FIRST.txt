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

Triple Triad remains in Gold Saucer. Card Hall is separate. The latest compact UI, wrapping corrections, Camp contrast, Emporium, Seasonal Cache, and Triple Triad progression fixes are carried forward from the approved source. Abandoned Living World 1A/1B and Accessibility v1.9.4.4 packages are not used.

See `RELEASE_NOTES.md` for features and `VALIDATION_v1_9_7.json` for checks and limitations. This package has not been deployed to your live services.

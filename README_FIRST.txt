# Crystal Guild — v1.9.7 + Living World LW-1 / ART-1

This is the full combined Bot + Web build. The Bot runtime baseline remains v1.9.7 Queen's Blood; the release adds the LW-1 Verdant Wilds foundation and ART-1 while retaining current Card Hall and economy changes.

**Important:** Triple Triad now lives in the Card Hall independently of the Gold Saucer, without MGP charges or rewards. Both Queen's Blood and Triple Triad use Card Hall. The eight Atlas regions unlock progressively, and infrastructure progression must be completable offline. ART-1 event/aftermath placeholder illustrations do not enable unfinished event game mechanics.

To upgrade, stop BOTH services and back up live code and databases. Deploy the included `Bot/` and `Web/` source files, preserving private `.env`/config, hosted and Bot SQLite databases, backups, overlay runtime state, and live persistence. Replace the deployed `Web/frontend/dist` directory as a whole with the included Vite output: do not merge old hashed chunks. Copying only changed files into the running build is not the correct deployment procedure.

Do not overwrite production databases or secret environment files. The full release contains no live database, session secrets, or tokens. It includes `Web/frontend/public` and a fully assembled compiled `Web/frontend/dist`; npm rebuild is not required for hosts using prebuilt output. `Web/Dockerfile.prebuilt` deploys the compiled frontend. Source-building hosts may use their established `npm ci` / `npm run build` procedure.

Technical baseline: Bot local schema 27, hosted sync schema 1, Portal Action protocol 39. The abandoned Living World 1A/1B and v1.9.4.4 Accessibility branch are NOT implementation baselines. Follow Bot/README_FIRST.txt and Web/HOSTING_GUIDE.md for historical setup details. This release addendum supersedes their outdated Card Hall/Triple Triad placement descriptions.

Automated Windows staging checks: frontend 908/908, Bot 1013/1013, hosted Web 215/215, compiled verifier PASS, and disposable Bot-to-hosted-Portal discovery PASS. Checked compiled JS/CSS and all 1,156 static source files against the returned manifest. Static HTTP smoke confirmed the Vite entrypoint and several key assets return HTTP 200. This is an assembled full package, **not evidence of a live production deployment**. Browser visual QA could not be completed in the assistant's isolated environment because Chromium navigation was administratively blocked. After deployment, manually check desktop and mobile layouts, sign-in, Card Hall, Atlas, Emporium, and representative offline progression before accepting production sign-off.

---

## Historical baseline instructions (v1.9.7)

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

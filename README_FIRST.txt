Crystal Guild v1.9.0 Alpha 13 — Trading Post QoL
Matching Bot/Web: 1.9.0-trading-post-qol-alpha13
Bot schema 25 | hosted sync 1 | Portal Action protocol 39

# Crystal Guild Alpha 13 — ONE-ZIP HANDOFF

**Extract the ZIP once.** Everything is already arranged in the correct folders:

```
Crystal_Guild_Alpha13/
  Bot/                    Matching local engine and migrations
  Web/                    Matching hosted Portal service and React frontend
    frontend/public/      Complete public assets (954 files)
  START_HERE.md
  RELEASE_NOTES.md
  TRADING_POST_ALPHA13_VALIDATION.md
  SOURCE_SHA256.txt
```

1. Back up both your live Bot database and hosted Portal store, environment variables, OAuth/session secrets and data mounts **before** deployment. Do not overwrite live data with the extracted source.
2. Deploy the matching Alpha 13 Bot and Web together. The Bot auto-migrates from schema 24 to 25 with a verified backup; the hosted sync schema stays at 1 and both Portal Action protocol versions are now **39**.
3. From `Web/frontend/`, run `npm ci`, then `npm run build`. The archive contains source and assets but **no prebuilt `dist`**; the configured Vite packages need npm registry access. Use the source-building Dockerfile and your existing staging/deployment workflow.
4. On staging, test watch/unwatch including a page refresh, search for items without listings, seller inventory quantities, completed-sale history, price comparisons after three sales, and quick relist when both inventory and listing fee are available. Confirm rejection when inventory is missing; verify Camp, mobile combat and existing Trading Post buy/cancel still work.
5. If reverting code, restore the corresponding schema-24 pre-migration backup too. **Do not run an older Bot against an already-migrated schema-25 database.**

There are no automated market transactions or new economic fees in this update.

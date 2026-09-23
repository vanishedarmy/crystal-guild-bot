# Upgrade to v1.9.0 Alpha 10 — Records & Moments

**Direct incremental patch baseline:** v1.9.0 Alpha 9 — Player Language Hotfix 1, with matching Bot/Web source. If your live release differs, use the Alpha 10 Complete or matching Web/Bot source archives instead of applying the patch onto an unknown build.

1. Stop the Bot and Web. Back up the actual live SQLite database, `.env`, Twitch token store, `overlay/state.json` and all hosted secrets and mounted persistent volumes. Verify that backups can be restored.
2. For the small patch, overlay its `Bot/` and `Web/` paths onto that **exact** Language Hotfix 1 baseline. For a complete install, deploy the matching full Alpha 10 Bot and Web trees. Do not replace the old live DB or your environment files with packaged examples.
3. Install Web/frontend dependencies using the deployment's package manager from `package.json`; run `npm run build` in a network-enabled, dependency-installed build environment. This source package intentionally omits `node_modules` and generated `dist`.
4. Run Bot/hosted regression checks, then restart the hosted Web/API and the Bot. Existing local schema 22 automatically upgrades to schema 23 and generates a verified `pre_schema_23_*` backup on Bot startup. Older schema versions migrate through their normal sequential steps.
5. Confirm both services report `1.9.0-records-moments-alpha10`, local schema 23, hosted sync 1 and Portal Action protocol 37. Verify the main profile, Records, Moments (owned and secret entries), Titles, Hall of Trophies and Player Guide in desktop and mobile browsers.
6. Test one long-existing account with proven Cactpot/purchase history and a brand-new account. No other historical Moments may be inferred. Confirm all 16 separate WebP art paths load and no secret metadata leaks in the relevant per-player API responses.
7. If anything fails before replacing production, restore the matched old Bot/Web and **their** pre-migration database together. Never run an old schema-22 Bot against a live schema-23 DB.

Historical upgrade note: legacy releases migrate in order (including local schema 17 → 18 during Merc Recruitment and the automatic `pre_schema_21` backup during the seasonal event upgrade) before reaching schema 23. These steps retain the previously verified data-preservation behavior.

No economy rebalance, player wipe, new hosted sync version or Portal write action. Halloween remains disabled unless manually enabled.

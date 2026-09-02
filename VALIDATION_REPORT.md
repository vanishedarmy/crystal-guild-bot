# Validation Report — Crystal Guild v1.7.0 Moogle Retainer

**Result: PASS**

## Release contract

- Bot runtime: `1.7.0`
- Web runtime: `1.7.0`
- Frontend asset revision: `1.7.0-final`
- Local database schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **31**
- Twitch command prefix: `!`

## Automated regression

- Bot: **668 / 668 PASS**
- Frontend: **554 / 554 PASS**
- Hosted Web/API: **63 / 63 PASS**
- Bot Python parse: **117 / 117 PASS**
- Web Python parse: **15 / 15 PASS**
- JS/MJS syntax: **202 / 202 PASS**
- CSS structural checks: **8 / 8 PASS**
- WebP decode: **843 / 843 PASS**
- Public PNG count: **0**

## Final release checks

- Production identity is centralized and no active runtime/frontend identity uses a pre-release suffix.
- The non-destructive database backup/restore recovery drill passes under schema 15.
- Existing Retainer Service, Moogle Emporium Annex, Gold Saucer, raids, dungeons, expeditions, Fellowship, inventory, item-use, and Portal action regression suites remain green.
- Render startup-backup low-space protection remains enabled.
- Hosted artwork remains streamed without unbounded in-process byte caching and supports ETag revalidation.
- The source-only Web archive does not include installed `node_modules`; no local Vite production build is claimed.

No database migration or player reset is required from the immediately prior schema-15 v1.7.0 candidate baseline.

## Package hygiene checks

- No pre-release-named manifest/report files remain at the Bot or Web package root.
- No generated `reports/`, Python bytecode/cache, `node_modules`, live database, token database, exact `.env`, or runtime checkpoint state is included.
- Current setup, maintenance, migration, stress-test, and control-panel surfaces identify the release as v1.7.0 Moogle Retainer.
- `pyproject.toml` reports project version `1.7.0`.

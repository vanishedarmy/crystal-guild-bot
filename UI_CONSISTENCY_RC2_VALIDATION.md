# Crystal Guild v1.8.0 RC2 — Validation Report

RC2 validates the Portal-wide UI consistency pass against the sealed RC1 Complete baseline.

## Completed validation

- Frontend Node regression suite: **652/652 PASS**.
- Hosted Web/API Python suite: **78/78 PASS**.
- Bot Python suite: **733/733 PASS**.
- Direct static media-reference audit: **159 references checked, 0 missing**. One template-generated region path is dynamic and remains covered by the existing region/artwork regression suite.
- Python compileall: **PASS** for Bot and hosted Web modules.
- JSON parse audit: **PASS** for Bot data and Player Guide metadata.
- No Merc gameplay, Hunt Seal economy, schema, sync, or Portal protocol changes.

## UI consistency coverage

- The sixteen Adventurer Profile destinations render as two balanced 8-item rows on wide desktop.
- Compact desktop/tablet uses a balanced 4-column grid, avoiding orphan navigation rows.
- At 720px and below the desktop tab grid is replaced by the compact section selector.
- Shared layout guardrails allow panels, grids, titles, badges, and controls to shrink without forcing horizontal viewport overflow.
- Shared media containment keeps images, figures, video, canvas, and feature artwork inside their authored parent frames.
- Existing mobile, Fellowship, Guide, Gold Saucer, Merc Service, accessibility, and artwork-routing regressions remain green.

## Release contract

- Runtime/frontend: `1.8.0-merc-rc2`
- Local database schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- No player reset or migration.

The frontend source archive intentionally does not ship `node_modules`; the source/regression suite is authoritative in this workspace, while deployment installs the pinned Vite/React dependencies from `package.json`.

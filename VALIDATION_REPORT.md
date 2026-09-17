# Crystal Guild v1.8.0 Final — Validation Report

The Final pass promotes the sealed RC3 feature set without gameplay expansion and verifies the production release identity, compatibility contract, source integrity, and packaged assets.

## Automated validation

- Frontend Node regression suite: **656/656 PASS**.
- Hosted Web/API Python suite: **78/78 PASS**.
- Bot Python suite: **733/733 PASS**.
- Python compileall: **PASS** for Bot and hosted Web modules.
- JSON integrity: **31/31 JSON files parsed successfully**.
- Static media-reference audit: **159/159 direct static references present; 0 broken direct static references**.
- Final release identity is synchronized across Bot runtime, hosted API, frontend version/cache revision, Guide metadata, package metadata, and release tests.

## Final release scope

- No Merc Service balance changes from RC3.
- No Hunt Seal economy changes from RC3.
- No Hero effect or mission-eligibility changes from RC3.
- No Portal navigation/refresh behavior changes beyond the already-tested RC3 implementation.
- No local database schema, hosted sync schema, or Portal Action protocol change.

## Release contract

- Runtime/frontend: `1.8.0-merc-final`
- Frontend package: `1.8.0`
- Local database schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- Final-specific migration: **none**
- Player reset: **none**

## Build environment note

The extracted shipping source does not include installed `node_modules`, so `npm run build` cannot invoke the Vite executable in this workspace (`vite: not found`). As with the RC line, the production bundle command is not used as a release gate here; frontend source/unit/regression coverage is complete and the direct static-media audit confirms referenced packaged assets are present.

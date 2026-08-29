# Validation Report — Crystal Guild v1.2.0 Expeditions Beta 4

## Automated suites
- Bot Python unittest suite: **443 / 443 PASS**
- Hosted Web/API Python suite: **47 / 47 PASS**
- Frontend Node regression suite: **324 / 324 PASS**
- Python compile sweep: **PASS**
- JS/JSX source parse sweep: **PASS**

## Beta 4 hardening coverage
- Active persistent Expedition blocks direct Long Rest refresh.
- Long Rest daemon sweep skips active persistent runs.
- Twitch stream-start roster refresh skips active persistent runs and remains once-per-stream idempotent.
- Expedition state/cache/Journal survive full Database + Engine restart.
- Forced Portal replay-receipt failure rolls back an Expedition stage mutation.
- Forced replay-receipt failure during Expedition completion rolls back cache banking, rewards, Hunt Seals, result persistence, and run deletion.
- Retrying the same completed Portal action returns the stored result without duplicating progression/rewards.
- Representative schema-7 player progression migrates to schema 8 with verified pre-schema-8 backup.
- Player Guide metadata matches authoritative 60/30 Venture and 90/60 Raid timing defaults.
- Existing simulated Twitch outage, acknowledgement-loss, token failure, reconnect/runtime checkpoint, database-integrity, and synthetic stress regressions remain passing.

## Compatibility
- Bot runtime `1.2.0-expeditions-b4`
- Hosted Web runtime `1.2.0-expeditions-beta4`
- Frontend revision `1.2.0-expeditions-b4`
- Local DB schema **8**
- Hosted sync schema **1**
- Portal Action protocol **20**
- No player reset or new environment variable

## Production bundle note
The clean shipping Web source intentionally does not vendor `node_modules`; a local Vite production bundle is therefore not part of this release-environment validation. Hosted deployment installs the pinned dependencies normally. Source-level Node regressions, JS/JSX parsing, hosted Python tests, and package reproduction provide the release checks here.

## Patch/package scope
- Beta 1 Bot → Beta 4 Bot: **13 changed/new files, 0 deleted**; final Bot tree **136 files**.
- Beta 3 Web → Beta 4 Web: **27 changed/new files, 0 deleted**; final Web tree **794 files**.
- Direct patch reproduction is verified against clean Beta 1 Bot / Beta 3 Web baselines before release.
- Runtime/private-artifact hygiene excludes live `.env`, token stores, SQLite runtime files, logs, Python bytecode/cache directories, and `node_modules`; documented `.env.example` templates remain included.

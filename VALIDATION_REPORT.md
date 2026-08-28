# Validation Report — Crystal Guild v1.2.0 Expeditions Alpha 3

## Automated suites
- Bot regression suite: **426 / 426 passed**.
- Hosted Web/API suite: **47 / 47 passed**.
- Frontend Node regression suite: **304 / 304 passed**.
- Python compilation checks: **PASS**.
- Changed JSX / JavaScript parse checks using the installed TypeScript parser: **PASS**.

## Alpha 3 regression coverage
- Atlas overall progress and cartography rank derive from existing schema-8 regional records.
- Per-region Legendary unlock requires 100% Mastery plus at least one Regional Boss clear.
- Legendary launch uses the existing `EXPEDITION_START` action with depth `legendary`.
- Legendary boss final stage is guaranteed.
- Legendary boss HP scales to 125% and enemy pressure to 115%.
- Legendary contract reward multiplier is 25% above the normal regional contract and base travel is 20% longer.
- Guaranteed Regional Boss materials are doubled on Legendary victory.
- All five mastered regions unlock **No Blank Spots Left** and **Master Cartographer**.
- Adventure Board state remains below the established **16 KiB** compact action/state envelope.
- Alpha 2 regional milestones, normal Regional Boss Contracts, Region Mastery, H3 scenic backdrops, collapsible Board/Travel/Hunt sections, and Player Guide content remain covered by the passing regression suite.

## Production bundle note
A local Vite production bundle was not executed because this source release does not package `node_modules` and the local Vite binary is unavailable. Source-level frontend regression tests and JSX parsing are clean.

## Compatibility
- Local DB schema **8** — unchanged.
- Hosted sync schema **1** — unchanged.
- Portal Action protocol **20** — unchanged.
- No player reset or database migration.

## Packaging validation
- Full Bot ZIP integrity: **PASS**.
- Full Web ZIP integrity: **PASS**.
- A2 → A3 Bot patch exact reproduction: **PASS — 13 changed/new files, 0 deleted**.
- A2H3 → A3 Web patch exact reproduction: **PASS — 26 changed/new files, 0 deleted**.
- Runtime/secret hygiene scan: **PASS**; no live `.env`, token stores, databases, logs, Python bytecode/cache directories, or `node_modules` are packaged.

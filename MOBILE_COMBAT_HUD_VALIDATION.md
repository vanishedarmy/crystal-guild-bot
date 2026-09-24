# Alpha 11 — Mobile Combat HUD validation

## Scope
- Reused the previously implemented Alpha 6 quick HUD across Solo Ventures, Dungeons, Expeditions, live Ventures, Raids and World Events.
- Replaced its nested sticky placement with a body-level, mobile-only viewport overlay, measured HUD height and safe-area-aware page spacing.
- Portaled only the selected mobile Ability/Item panel above the HUD, retained the full desktop decks, and added keyboard Escape, dialog labels and reduced-motion support.
- Preserved all existing authoritative combat callbacks; no player database, game balance, item rules or Portal Action contract changes.

## Automated evidence
- New Alpha 11 focused frontend tests: 4/4 passing. Earlier mobile HUD/drawer tests: 10/10 passing.
- Existing broad frontend suite: 809 tests, 753 passing and 56 failing. On the **unmodified Alpha 10 baseline**, the same historical suite had 805 tests, 740 passing and 65 failing. Every Alpha 11 failure also occurred in Alpha 10; no new regression-test failures relative to that baseline. Remaining failures include obsolete release-identity expectations and older artwork/UI assumptions.
- Changed JavaScript and JSX files: 7/7 pass TypeScript JSX parse diagnostics. CSS passes PostCSS syntax parsing.
- Bot release-contract checks: 8/8 passing. Web hosted-portal regression checks: 29/29 passing.

## Deployment blocker / staging gate
A fresh Vite production bundle could not be built inside this sandbox because Alpha 10 carried Windows-only native Rolldown/Lightning CSS node_modules and npm registry resolution was unavailable. The earlier `frontend/dist` must not be shipped as Alpha 11. Build from the pinned lockfile (`npm ci && npm run build`) in the deployment environment after adding the separately supplied public folder. Confirm a manual mobile browser walkthrough at 320px, 375px, 390px and 760px, mobile safe-area insets and landscape.

# Crystal Guild v1.9.0 Alpha 9 — Bestiary Discovery Validation

Baseline: v1.9.0 Alpha 8 Halloween Individual Artwork Hotfix 3. Local database schema: **22**. Hosted sync schema: **1**. Portal Action protocol: **37**.

## Release gates

- Bot unittest regression suite: **835/835 passed** (including eight new historical-migration, isolation, lock, threshold and idempotency tests).
- Hosted Web/API unittest suite: **81/81 passed**.
- Frontend source/history Node suite: **723/778 passed**. The **55 remaining failures are identical by name to the 55 existing Step 5 baseline failures**, with no new failure names; they are not counted as passing.
- Bestiary artwork audit: **169/169 required image files valid and decodable** (112 core + 37 bosses + 10 World Event variants + five seasonal unlocked + five seasonal locked). Five new Expedition-boss WebPs are 512×768.
- Direct frontend static-asset references: **192/192 present**.
- Schema migration: simulated pre-existing schema 21 to schema 22, including automatic verified backup and preservation of historical defeats and archived seasonal progress, passed.
- Bot masteries and research points: once-only per `(player_id,monster_id)`, isolation between players, and no rewards for external encounter records, passed.
- Old Bestiary history and seasonal edition-scoped records are not reset.

## Not covered by this source validation

The source package intentionally excludes `node_modules`; a real Vite production bundle and a deployed-browser walkthrough were not run in this workspace. Install pinned dependencies and run `npm run build` in the deployment environment and validate the Portal on staging before replacing a live installation. Existing frontend test failures remain unresolved. No material-drop bonus was enabled.

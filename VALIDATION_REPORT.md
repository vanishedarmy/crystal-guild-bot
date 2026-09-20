# Crystal Guild v1.9.0 Alpha 1 — Moogle Trading Post Validation

Validation target: runtime `1.9.0-trading-post-alpha1`, local schema **19**, hosted sync schema **1**, and Portal Action protocol **36**.

## Automated results

- Bot regression suite: **757 / 757 passed**.
- Web/hosted Python suite: **80 / 80 passed**.
- Dedicated Trading Post coverage includes construction gating, locked/open state, listing fees, fixed-price purchase settlement, seller tax/payout, replay safety, self-purchase rejection, cancellation returns, expiry returns, protected relics, equipped-last-copy protection, and hosted payload validation.
- Python package compile checks passed for Bot and Web.
- JavaScript syntax checks passed for `api/auth.js`, `version.js`, and `whatsNewData.js`.
- JSX parser checks passed for the modified `MoogleEmporium.jsx` and `FellowshipPage.jsx`.
- Project JSON parse validation passed.

## Frontend build-environment note

The source archive does not contain `node_modules` or a package lock, and dependency installation was not available to completion in this isolated build environment, so a Vite production bundle could not be executed here. This is an environment/dependency-availability limitation rather than a detected source parse error. The modified JavaScript/JSX passed the syntax/parser checks above. Normal deployment should install the dependencies declared in `frontend/package.json` before running the Vite build.

## Migration and safety

Schema 18 → 19 is additive and uses the existing verified pre-migration backup path (`pre_schema_19_*.db`). No player reset is required. Trading Post mutations remain Bot-authoritative and use the existing replay-safe Portal action pipeline.

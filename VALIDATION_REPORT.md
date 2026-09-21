# Crystal Guild v1.9.0 Alpha 5 — Title Status Hardening Validation

Validation target: runtime/frontend `1.9.0-title-status-hardening-alpha5`, local schema **19**, hosted sync schema **1**, Portal Action protocol **36**.

## Automated results
- Bot full regression suite: **772 / 772 passed**.
- Focused Bot Title/Achievement hardening suite: **21 / 21 passed**.
- Hosted/Web Python suite: **80 / 80 passed**.
- Focused Alpha 3 + Alpha 4 + Alpha 5 frontend checks: **12 / 12 passed**.
- Full frontend history suite: **654 / 711 passed**. The remaining **57** failures are the same inherited historical release-name and legacy PNG-policy assertions present in the Alpha 4 baseline (**651 / 708**, also 57 failures). Alpha 5 adds three passing frontend tests and introduces **zero new full-suite failure names**.
- Python source compilation: **passed** for Bot and Web packages.
- Game-data validation: **0 errors**.

## Alpha 5 hardening coverage
- Existing players are proactively reconciled against the current achievement catalog on Bot startup.
- In-process hosted profile sync reconciles the requested player before building a snapshot.
- An achievement already stored as unlocked repairs a missing reward-Title row automatically and idempotently.
- Achievement dependencies resolve to a fixed point in one reconciliation cycle rather than depending on catalog order or a later gameplay trigger.
- Already-earned achievements remain visually **100% complete** even if a reversible current value later falls below the original threshold.
- The Portal progress evaluator now mirrors additional Bot requirement families, including Expedition-region progress.
- Secret Titles and secret achievement conditions remain concealed until earned.
- Existing Title requirements and Gold Saucer/economy values are unchanged.

## Compatibility
No database migration, hosted sync bump, Portal Action protocol bump, economy rebalance, Gold Saucer payout change, Title requirement change, or player reset is required.

## Frontend build-environment note
The source snapshot does not include installed frontend `node_modules`, so a production Vite bundle was not rebuilt inside this isolated workspace. The Node source-contract/history suites ran directly and the new Alpha 5 checks pass. Normal deployment remains responsible for installing the pinned package dependencies before the Vite production build.

# Gold Saucer RC1 Release Audit — Crystal Guild v1.6.0

RC1 is the release-candidate freeze for the complete five-attraction Gold Saucer feature set. It intentionally introduces no new attraction, MGP rebalance, schema migration, or Portal action.

Runtime `1.6.0-gold-saucer-rc1`; local DB schema **13**; hosted sync **1**; Portal Action protocol **29**; prefix `!`; MGP canonical.

The only gameplay hardening in RC1 binds persistent Monster Toss and Triple Triad daily entries to the UTC day on which the entry is started/paid for. Active same-day sessions count immediately; sessions completed after midnight retain their original start-day history timestamp.

Release gates: **636/636 Bot**, **521/521 frontend**, **56/56 hosted Web/API**, Bot Python **111/111**, Web Python **12/12**, plain JS/MJS **190/190**, CSS **8/8**, public artwork **800/800 WebP decode**, **0 PNG**.

The source-only Web package does not contain installed `node_modules`; a local Vite production build is therefore not claimed (`vite: not found`).

Packaging must exclude live databases, `.env`, token/secrets, caches, `__pycache__`, logs, and runtime overlay state.

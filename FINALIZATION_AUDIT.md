# Gold Saucer RC2 Release Audit — Crystal Guild v1.6.0

RC2 is the final balance candidate for the complete five-attraction Gold Saucer feature set. It introduces no new attraction, schema migration, Portal action, player reset, or non-Saucer progression change.

The release audit found one economy outlier in RC1: Mini Cactpot's inherited payout scale overwhelmed Crystal Guild's MGP Prize Counter. RC2 rescales only that table, keeps the 10 MGP daily ticket and 1,000 MGP jackpot, and records net win/draw/loss outcomes. All other attraction economics remain frozen.

Runtime `1.6.0-gold-saucer-rc2`; local DB schema **13**; hosted sync **1**; Portal Action protocol **29**; prefix `!`; MGP canonical.

Release gates: **641/641 Bot**, **522/522 frontend**, **56/56 hosted Web/API**, Bot Python **112/112**, Web Python **12/12**, plain JS/MJS **191/191**, CSS **8/8**, public artwork **800/800 WebP decode**, **0 PNG**.

The source-only Web package does not contain installed project `node_modules`; a local Vite production build is therefore not claimed.

Packaging excludes live databases, `.env`, token/secrets, caches, `__pycache__`, logs, and runtime overlay state.

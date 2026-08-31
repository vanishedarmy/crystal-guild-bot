# Crystal Guild v1.6.0 — Gold Saucer Alpha 1 Validation Report

## Result
**PASS**

## Regression suites
- Bot: **607 / 607 PASS**.
- Frontend: **472 / 472 PASS**.
- Hosted Web/API: **49 / 49 PASS**.

## Gold Saucer Alpha 1 coverage
- Dedicated Gold Saucer Portal tab: PASS.
- Separate Saucer Point economy; ordinary Gil is never wagered: PASS.
- One-time **500 SP** welcome purse: exactly once.
- Daily **50 SP** floor allowance beginning after the welcome day: exactly once per UTC day.
- Persistent Mini Cactpot ticket/reveals/line resolution: PASS.
- Replay-safe Crystal Slots debit/payout: PASS.
- Cosmetic-only Prize Counter purchases: atomic, replay-safe, and Title-system backed.
- Recent Saucer ledger and personal records: PASS.
- Streamer `!saucergrant` / `!saucerreset`: PASS.
- Monster Toss, Chocobo Racing, and Triple Triad remain disabled/Coming Soon: PASS.

## Source validation
- Python source parse: **113 / 113 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **216 / 216 PASS**.
- Plain JS/MJS Node syntax: **174 / 174 PASS**.
- `portal.css` PostCSS parse: **0 errors**.

## GameData and artwork
- **18 Jobs / 18 Relics / 435 items / 37 bosses / 4 Dungeons / 94 Titles**.
- Public artwork: **0 PNG / 665 WebP**.
- WebP decode: **665 / 665 PASS**.
- Refreshed Relic artwork family: **54 / 54** WebP assets present under `relic-weapons-v2`.

## Upgrade / recovery drill
A genuine v1.5.1 schema-10 database was created with the prior runtime and opened under Alpha 1:
- automatic verified pre-migration backup created under `backups/pre_schema_11_*.db`;
- schema advanced **10 → 11**;
- validation hero remained **Lv.17 / 4,321 Gil**;
- SQLite `quick_check`: **ok**;
- foreign-key violations: **0**;
- Gold Saucer tables: **3 / 3 present**.

## Frontend production build gate
`npm run build` was explicitly attempted. The source-only container does not contain the pinned local Vite executable (`sh: vite: not found`, exit 127), so this report does **not** claim a local Vite production-build pass. The complete frontend regression/parser/syntax/CSS gates above are green.

## Compatibility contract
- Runtime: `1.6.0-gold-saucer-a1`
- Local DB schema: **11**
- Hosted sync schema: **1**
- Portal Action protocol: **26**
- Twitch prefix: **`!`**
- No player reset, OAuth reauthorization, hosted sync migration, or new required environment variable.

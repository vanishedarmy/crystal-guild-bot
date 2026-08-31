# Crystal Guild v1.6.0 — Gold Saucer Alpha 2 Validation Report

## Result
**PASS**

## Automated suites
- Bot regression suite: **615 / 615 PASS**.
- Frontend Node regression suite: **481 / 481 PASS**.
- Hosted Web/API suite: **51 / 51 PASS**.

## Source / asset validation
- Python source parse across Bot + Web: **116 / 116 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **217 / 217 PASS**.
- Plain JS/MJS Node syntax: **177 / 177 PASS**.
- CSS parse: **8 / 8 PASS**.
- Public artwork: **0 PNG / 675 WebP**; **675 / 675 WebP decode PASS**.
- GameData: **18 Jobs / 18 Relics / 435 items / 37 bosses / 4 Dungeons / 96 Titles / 0 validation errors**.

## Gold Saucer Alpha 2 coverage
- Monster Toss is the third playable Gold Saucer attraction.
- Entry cost is **20 SP**; each game has **5 throws** and a maximum of **3 games per UTC day**.
- Each throw chooses one of four targets and one of three throw styles; target/style combinations trade hit chance against score.
- Active game ID, throw index, score, and throw history persist across Portal refreshes, reconnects, and Bot restarts.
- Duplicate action IDs replay the committed Monster Toss start/throw result and do not debit, throw, or pay twice.
- Fifth throw settles a bounded SP reward exactly once and records the completed game in the existing Gold Saucer ledger.
- Personal records include Monster Toss games, best score, hits/throws, hit accuracy, and best payout.
- Prize Counter adds **Toss Tactician** and **Pot Shot Pro** as cosmetic-only Titles.
- Mini Cactpot, Crystal Slots, daily SP recovery, H1 scenic artwork, and H2 UX/records behavior remain green.

## Upgrade / recovery
A genuine **v1.6.0 Alpha 1 Hotfix 2 schema-11** database was created with the prior runtime and then opened under Alpha 2:
- schema advanced **11 → 12**;
- a verified `pre_schema_12_*` backup was created automatically;
- validation hero remained **Lv.17 / 4,321 Gil**;
- foreign-key validation remained clean.

Schema 12 is additive and adds only persistent active Monster Toss state.

## Production frontend build gate
`npm run build` was explicitly attempted. This source-only environment does not contain the pinned local Vite executable (`vite: not found`, exit 127), so this report does **not** claim a local Vite production-build pass. The complete frontend regression/parser/syntax/CSS gates above are green.

## Compatibility contract
- Runtime: `1.6.0-gold-saucer-a2`
- Local DB schema: **12**
- Hosted sync schema: **1**
- Portal Action protocol: **27**
- Twitch prefix: **`!`**
- No player reset, OAuth/environment change, new required environment variable, normal Gil economy change, combat progression change, Mini Cactpot payout change, or Crystal Slots payout change.

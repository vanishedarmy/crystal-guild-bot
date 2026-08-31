# Crystal Guild v1.5.0 — Trails & Raids Validation Report

## Production validation
- Bot regression suite: **598 / 598 PASS**.
- Frontend regression suite: **458 / 458 PASS**.
- Hosted Web/API suite: **47 / 47 PASS**.
- Python compile sweep: **109 / 109 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **212 / 212 PASS**.
- Plain Node JS/MJS syntax sweep: **171 / 171 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 validation errors**.
- Public artwork: **0 PNG / 578 WebP**; **578 / 578 WebP decode PASS**.
- Static WebP literal-token audit: **403 / 403 resolve**.

## RC1 → production upgrade/recovery drill
- Genuine RC1 schema-10 database reopened under runtime `1.5.0-trails-raids`: **PASS**.
- No migration triggered; highest schema migration remains **10**.
- Test hero preserved exactly at **Lv.17 / 4,321 Gil**.
- SQLite `quick_check`: **ok**; foreign-key violations: **0**.
- Non-destructive backup/reopen preserved schema and player state: **PASS**.

## Production visual integration
- Active Hunt scenic WebP route: **PASS**.
- Trial & Raid Board collapsed scenic state: **PASS**.
- Trial & Raid Board open scenic state: **PASS**.
- Public tree remains PNG-free: **PASS**.

## Contract
- Bot/Web/frontend runtime: `1.5.0-trails-raids`.
- Local DB schema: **10**.
- Hosted sync schema: **1**.
- Portal Action protocol: **25**.
- Twitch prefix: `!`.
- No player reset, database migration, OAuth/environment change, reward rebalance, or new Portal combat action.

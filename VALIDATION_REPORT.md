# Validation Report — Crystal Guild v1.7.0 — Retainer Service Alpha 1

## Automated release gates

- Bot regression suite: **649 / 649 PASS**
- Retainer focused suite: **8 / 8 PASS**
- Local DB schema: **14**
- Hosted sync: **1**
- Portal Action protocol: **30**
- Command prefix: `!`
- Gold Saucer / MGP economy: unchanged from v1.6.0 production

## Retainer coverage

Alpha 1 regression coverage verifies one personal Retainer, one active assignment at a time, Gil deduction at dispatch, reward commitment before departure, rank-gated procurement routes, crafting-material-only pools, restart persistence, exact Portal worker payload handling, and exactly-once collection.

- Bot Python AST parse: **114 / 114 PASS**

## Upgrade safety

Schema 13 upgrades sequentially to schema 14. A verified `pre_schema_14_*.db` backup is created before the structural migration. Existing players, progression, inventory, Guild state, and Gold Saucer state are preserved.

Contract: runtime `1.7.0-retainer-a1`, schema **14**, hosted sync **1**, Portal protocol **30**.

Migration drill: **PASS** — a real v1.6.0 schema-13 test database preserved level 17, 4,321 Gil, 17 Iron Ore, and 777 MGP through schema 14; the `pre_schema_14_*.db` backup passed SQLite `quick_check`.

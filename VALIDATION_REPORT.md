# Crystal Guild v1.5.0 — Trails & Raids Alpha 1 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **539 / 539 PASS**.
- Frontend Node regression suite: **404 / 404 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Alpha 1 coverage
- Ifrit — Inferno Crucible scripted Trial flow is regression-covered end to end.
- Incinerate, Radiant Plume, Infernal Nails, and weakened/empowered Hellfire resolve authoritatively.
- `attacks_per_round = 0` continues to suppress boss retaliation in existing fixtures/admin simulations.
- Adventure Board and OBS overlay consume sanitized public mechanic/contribution state only; Twitch IDs and internal target IDs are not exposed.
- Weighted contribution covers damage, healing, and mitigation.
- Existing raid rounds, revives, Limit Breaks, Summons, phases, enrages, persistence, and recovery behavior remain green.
- Existing v1.4 Dungeons remain frozen and unchanged.

## Source / asset validation
- Python compile sweep: **99 / 99 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **200 / 200 PASS**.
- Plain JS/MJS `node --check`: **159 / 159 PASS**.
- Active quoted literal image-route audit: **150 / 150 PASS**; **0 missing**.
- Public artwork: **0 PNG / 576 WebP**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.

## Upgrade / recovery drill
- Real v1.4.0 schema-10 database reopened under Alpha 1 without a migration or migration backup: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- SQLite quick-check, foreign keys, WAL/busy-timeout runtime pragmas, and non-destructive backup/restore recovery drill: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a1`.
- Local DB schema **10**, hosted sync **1**, Portal protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment change, or new environment variable.

## Packaging verification
- v1.4.0 → Alpha 1 Bot patch: **34 changed/new files, 0 deletions**; final Bot tree **153 files**.
- v1.4.0 → Alpha 1 Web patch: **58 changed/new files, 0 deletions**; final Web tree **828 files**.
- Individual Bot/Web patch helpers and paired updater reconstruct the exact final shipping trees: **PASS**.
- Complete archive contains the exact final Bot/Web trees: **PASS**.
- All **6 / 6** release ZIPs pass CRC/integrity checks.
- Runtime/private-artifact hygiene: **0 violations**.
- SHA-256 verification: **PASS**.

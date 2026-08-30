# Crystal Guild v1.5.0 — Trails & Raids Alpha 2 Validation Report

## Result
**PASS**

## Automated suites
- Bot Python unittest suite: **545 / 545 PASS**.
- Frontend Node regression suite: **410 / 410 PASS**.
- Hosted Web/API Python unittest suite: **47 / 47 PASS**.

## Alpha 2 coverage
- Shiva — Diamond Throne scripted Trial data and mechanic cycle are regression-covered.
- Icebound Mirror adds persist in raid state and intercept boss-targeted damage.
- Mirror clear advances to Diamond Aegis; Break success creates a one-round Stagger/vulnerability window.
- Alpha 1 Ifrit Trial regression suite remains green.
- Public Overlay sanitization includes add HP and Tank/Healer/Support/DPS role labels without internal add/target IDs.
- Hosted validator accepts the additive public fields and retains forbidden-private-field checks.
- Existing contribution reward math remains unchanged.

## Source / asset validation
- Python compile sweep: **100 / 100 PASS**.
- Frontend JS/JSX/MJS TypeScript-parser sweep: **202 / 202 PASS**.
- Plain JS/MJS `node --check`: **161 / 161 PASS**.
- GameData: **37 bosses / 4 Dungeons / 0 errors**.
- Public artwork: **0 PNG / 575 WebP**.
- Literal frontend image-route audit: **150 / 150 PASS**, 0 missing.

## Upgrade / recovery drill
- Real v1.4.0-created schema-10 database reopened under Alpha 2: **PASS**.
- Existing test-player level/Gil preserved exactly (**Lv.17 / 4,321 Gil**): **PASS**.
- SQLite quick-check and foreign-key check: **PASS**.
- Non-destructive backup verification: **PASS**.

## Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-a2`.
- Local DB schema **10**, hosted sync **1**, Portal Action protocol **25**, Twitch prefix `!`.
- No migration, reset, OAuth/environment, or new environment-variable change.

## Packaging verification
- Final source delta and archive reconstruction results are recorded in `FINALIZATION_AUDIT.md` and the patch manifests.
- Release ZIP CRC/integrity and SHA-256 verification: **PASS**.

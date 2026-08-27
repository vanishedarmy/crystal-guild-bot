# Crystal Guild v1.1.19 — Retro Phase III RC1 Validation Report

## Automated validation
- Bot unittest suite: **392 / 392 PASS**.
- Frontend Node regression suite: **283 / 283 PASS**.
- Hosted Portal/API unittest suite: **46 / 46 PASS**.
- Bot + hosted Web Python compile sweep: **PASS**.
- Finalization static audit: **PASS — 0 errors / 0 warnings**.
- Explicit `/retro-phase-*` artwork routes checked: **147**, missing: **0**.
- Bot patch reconstruction from the Chocobo Portrait baseline: **0 differences**.
- Web patch reconstruction from iii13: **0 differences**.

## RC1 visual pass
Four optimized **1440×810 PNG** scenic backgrounds are packaged and routed:
- Camp / Recovery
- Blacksmith
- Chocobo Stable
- Moogle Emporium

The scenic layers use readability gradients, reduced mobile opacity, and `prefers-contrast: more` safeguards. Camp art is shared by both Adventure Board Camp and Inventory Recovery.

## Progression / balance audit
- All monster drop item IDs resolve and all drop probabilities are valid.
- Every region encounter ID resolves.
- Every region retains at least three listed encounters within its minimum-level +10 safety band.
- All six Fellowship facility materials have at least three monster sources, at least one source at Lv.11 or below, and a practical early drop rate.
- Shop catalog density remains populated across Lv.1–10, 11–20, 21–30, 31–40, and 41–50.

See `FINALIZATION_AUDIT.md` for the detailed source tables.

## Frontend production-build note
The shipping source tree intentionally contains no `node_modules`. The local RC workspace therefore could not execute `vite build` because the Vite executable is not installed in the clean package tree. The complete Node regression suite passes against the shipping source; normal hosted deployment installs the pinned dependencies before building.

## Compatibility
- Bot runtime: `1.1.19-retro-phase-iii-rc1`
- Hosted Web runtime: `1.1.19-retro-phase-iii-rc1`
- Frontend asset revision: `1.1.19-retro-phase-iii14-rc1`
- Local DB schema: **6**
- Hosted sync schema: **1**
- Portal Action protocol: **15**
- Twitch prefix: `!`
- Player reset: **none**
- OAuth change: **none**
- New environment variables: **none**

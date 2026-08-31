# Crystal Guild v1.5.0 — Trails & Raids Release Audit

## Frozen production contract
- Runtime: `1.5.0-trails-raids`.
- Local DB schema **10** / hosted sync **1** / Portal Action protocol **25** / Twitch prefix `!`.
- Seven scripted flagship Trials and four production Dungeons remain content/reward frozen from RC1.
- Beta 2 exactly-once settlement, Beta 3 authoritative combat revision/timer hardening, and RC1 exact readiness remain intact.

## Final visual additions
- `/trails-raids/hunt-active.webp` for active timed Hunts.
- `/trails-raids/trial-board-collapsed.webp` for the collapsed Trial & Raid Board.
- `/trails-raids/trial-board-open.webp` for the open Trial & Raid Board.
- All generated source PNGs were converted into shipping WebP assets; public package contains **0 PNG**.

## Validation
- **598/598 Bot**, **458/458 frontend**, **47/47 hosted Web/API**.
- **109/109 Python compile**, **212/212 JS/JSX/MJS parser**, **171/171 Node syntax**.
- **37 bosses / 4 Dungeons / 0 GameData errors**.
- **578/578 WebP decode**, **403/403 static WebP literal tokens resolve**.
- RC1 → stable schema-10 upgrade/recovery drill: **PASS**, Lv.17 / 4,321 Gil preserved.

## Source delta from RC1
- Bot: **32 changed/new, 0 deleted → 163 files**.
- Web: **59 changed/new, 0 deleted → 842 files**.

No migration, reset, OAuth/environment change, new environment variable, Trial/reward/economy change, or new Portal combat mutation is introduced.

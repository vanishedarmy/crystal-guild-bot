# Crystal Guild v1.8.2 — Elite Mercs Finalization Audit

**Decision: PASS.** v1.8.2 expands the permanent Hero Merc Registry with six premium late-game contracts while preserving the v1.8.1 recruitment, save, Dungeon, and live-stream-control foundations.

## Release contract

- Visible release: **v1.8.2 — Elite Mercs**
- Runtime/frontend: `1.8.2-elite-mercs`
- Frontend package: `1.8.2`
- Local database schema: **18** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Portal Action protocol: **35** (unchanged)
- No new migration from v1.8.1 and no player reset.

## Elite Merc scope

The founding six and v1.8.1 expansion six remain intact. v1.8.2 adds **Lightning, Sephiroth, Rikku, Y’shtola, Noctis, and Cid** as Elite contracts, increasing the registry from 12 to 18 Heroes.

Each Elite Hero has the three established visual states:

- **Locked** — silhouette, not yet recruited.
- **Unavailable** — permanently recruited but currently hired/deployed.
- **Available** — permanently recruited and ready to hire.

Elite contracts use higher permanent recruitment requirements and higher Hunt Seal deployment fees in exchange for substantially stronger damage, recovery, tactical support, or gathering effects.

## Validation gate

- Bot unit/regression suite: **748 / 748 passed**.
- Hosted Web/API suite: **78 / 78 passed**.
- Frontend unit/regression suite: **685 / 685 passed**.
- Python compilation: **PASS**.
- JSON parse validation: **33 / 33 passed**.
- Elite Merc artwork: **18 / 18 present**, standardized to **660 × 880 WebP**, all below 400 KB.
- Active release identity scan: no stale `1.8.1-merc-recruitment` runtime identity remains in active Bot/Web version code.

The frontend distribution remains source-based, matching the existing Crystal Guild Web packages. The local validation environment did not contain installed Vite dependencies, so a separate prebuilt `dist/` bundle is not included.

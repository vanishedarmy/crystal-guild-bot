# v1.9.8 — Airship Expedition

The Crystal Guild Airship is now the Fellowship's shared unlock for individual remote Expeditions. The old 24–48-hour passive mission **launches are retired**; any mission already in flight can finish and settle using its original persisted rules, and mission history and construction/upgrades remain intact.

- Three Airship-only regions: **The Shattered Sky Isles** (Lv.25+, Crystal Core 0), **The Aetherstorm Expanse** (Lv.35+, Core 1), and **The Forgotten Dominion** (Lv.45+, Core 2). The original five Chocobo regions are unchanged.
- Three new regional bosses and three sky-exclusive salvage materials, with persistent regional exploration, milestones and boss contracts.
- Per-player Airship Expeditions reuse the regular Expedition persistence, routing, combat and rewards; a Chocobo is not required for flying. Multiple members may travel independently.
- Airship upgrades: Hull lowers hazards and improves rescue retention; Engine shortens travel; Cargo increases gathered materials; Survey improves rare-event odds and exploration gains; Crystal Core gates distant regions. Tiers are copied when a flight launches so mid-flight guild upgrades cannot change its conditions.
- Airship-specific events: aerial ambushes, aetherstorms, emergency landings and floating ruins.
- Twitch chat: `!airshipregions`, `!airshipexpedition <region_id> [scout|journey|deep|boss|legendary]`, `!airshipstage`, `!airshiproute [safe|unknown|deep]`, `!airshipcamp`, `!airshipreturn`, `!airshipattack`, `!airshipdefend`, `!airshipretreat`. Existing `!airship` reports Guild construction and unlocked destinations. `!airshipmission` is disabled.
- Portal Expedition Board has separate Chocobo and Guild Airship routes. Fellowship page focuses on upgrades and remote regions, while prior mission history stays visible.
- No database migration required; persistent schema remains **27**, hosted sync schema **1**, Portal Action protocol **39**.
- **v1.9.7 Quick Gear Twitch chat commands remain present** in the full Bot.

**Deployment:** Always back up live Bot/Web databases, volumes and configuration before updating. Merge `Bot/` and `Web/` source patch into the existing tree; keep all image assets and secrets unchanged. Restart Bot, and rebuild Web/frontend through the source-build Dockerfile or normal `npm ci && npm run build`. The static v1.9.7 `frontend/dist` is not a v1.9.8 UI build; do not deploy with `Dockerfile.prebuilt` until the new bundle has been compiled. Do not wipe either database.

---

# v1.9.7 — Queen’s Blood

Queen’s Blood joins Crystal Guild in its own Card Hall, separate from Gold Saucer and Triple Triad.

- **48 illustrated cards:** 16 foundation cards, 16 heroes, and 16 summons and villains. All six approved batches are included, with the final Cactuar, Cloud, Zidane, FFVII Remake Leviathan, and reference-pose Sephiroth revisions. Lightweight 320×480 display copies keep browsing fast; the 1024×1536 lossless originals remain available in the art viewer. Portraits retain their full frame; collection and selected-card views open larger artwork dialogs.
- **Solo progression:** guided tutorial, practice matches, 14 circuit opponents, guaranteed first-win rewards, and three saved 15-card deck slots. Every card can be obtained solo. PvP, raids, and live streams are not progression gates.
- **Live casual invitations:** 10 minutes to accept, 3 minutes for both opening hands, and 90 seconds per turn. Visible turn indicators and a server-based countdown accompany automatic refresh and reconnect handling. Closing the page does not pause a live clock.
- **Correspondence duels:** 48 hours to accept, 24 hours for both opening hands, and 48 hours per turn. Both modes save every action. Missing an opening deadline cancels the game without a result; missing a turn deadline is a forfeit. Live and correspondence records are shown separately.
- **Reliable match state:** deck snapshots at acceptance, private hands, revision checks, duplicate-request protection, authoritative deadlines, and saved-match compatibility.
- **Compact presentation:** dark readable surfaces, illustrated hands and board cards, compact collection rows, full placement/effect previews, and wrapping controls on desktop and mobile.

## Rules and scope

The three-lane territory game uses original Crystal Guild cards and the established Guild rules implementation inspired by Queen’s Blood. Its 15-card decks, opening exchange, turn draws, lane scoring, replacement, destruction, ongoing effects, thresholds, and status-count abilities are explained in the Card Hall’s How to play section. The release does not claim exact conformance to every FFVII Rebirth interaction. Persisted rule identifiers retain their historical names so old matches can still be resumed.

There is no ranked ladder, public matchmaking queue, spectator mode, wagering, or automated defense-deck mode in this release. Live play uses private invitations and periodic state refresh. Timers are enforced by the hosted server; after a restart, overdue turns are settled when the duel is next read or acted on. Both modes need the Portal online; the Bot may be offline.

## Installation and verification

Use `START_HERE.md`. Both service folders and the production frontend are included. No npm rebuild is required when using the prebuilt output. Keep your existing Bot and hosted Web databases and private configuration.

The validation report distinguishes the Queen’s Blood release checks from inherited failures in the historical test suites. Automated game simulations are termination checks, not evidence of human win rates or exhaustive competitive balance. No live deployment or real-player transactions were performed.

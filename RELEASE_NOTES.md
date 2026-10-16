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

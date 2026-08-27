# Crystal Guild v1.1.19 — Retro Phase III / Release Candidate 1

RC1 finalizes Retro Phase III. It retains persistent player-selectable Chocobo portraits and Facility Supply Balance, adds release-wide integrity/balance auditing, and removes superseded release-tree debris before the v1.2 Expeditions branch.

Runtime `1.1.19-retro-phase-iii-rc1h6` · local DB schema **7** · hosted sync schema **1** · hosted sync compatibility `1.1.15-wayfarer` · Portal Action protocol **17** · Twitch prefix `!`.


Latest Hunt timing: C 15m · B 30m · A 2h · S 5h. Hunts resolve autonomously with no round-by-round chat input.

## RC1 Hotfix 6 — Persistent Adventure Results
Adds a durable per-player Adventure Board result inbox. Portal Solo Venture outcomes and Portal-origin timed Hunt results persist across page changes, time away, and Bot restarts until the player confirms the individual card. Hotfix 5 Streamer Controls and LIVE-only notable Portal announcements remain intact. Deploy with the matching Web build because local DB schema 7 and Portal Action protocol 17 are required.

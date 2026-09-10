# Crystal Guild v1.7.1 — Resynthesis Alpha 2 Hotfix 5 — HTTP Response Efficiency

This hotfix reduces unnecessary HTTP response volume and repeated payload transfer while preserving live Portal behavior.

## Response-efficiency changes
- Bot Portal action claims use server long polling (up to 20 seconds) instead of repeated empty 3-second responses.
- Browser action completion waits use a single-action long-poll endpoint instead of repeatedly downloading action history.
- Idle Bot sync heartbeat is manifest-first: unchanged Fellowship and Overlay snapshots are not retransmitted unless the hosted mirror reports them missing.
- Sync heartbeat moves to 60 seconds; hosted stale tolerance moves to 150 seconds so one delayed heartbeat does not falsely mark the Bot offline.
- Dynamic JSON reads use ETags and return HTTP 304 with an empty body when unchanged.
- SSE is the primary live update signal. Health, Favorites, Raid, Adventure Board, and authentication HTTP timers are fallback/recovery paths.
- SSE keepalive moves to 20 seconds with a 50-second client freshness window.
- Auth fallback is 120 seconds while visible, with focus/page-return throttling.
- Equipment Favorites fallback is 120 seconds while live revisions/focus remain immediate.
- Raid Board fallback is 60 seconds for overlay state and 120 seconds for records.
- The standalone Raid Overlay stops recurring JSON polling while SSE is healthy and uses a 60-second recovery fallback only when the stream is stale.
- Adventure Board fallback is 30 seconds for active encounter/Expedition/Dungeon paths and 60 seconds for timed Hunts; exact gameplay deadlines still trigger immediate refreshes.
- Unclaimable orphan actions do not cause rapid long-poll response loops.

## Compatibility
Full Rest & Combat Continuity, authoritative cross-device Gear Favorites, Treasure Seekers Solo progress, Rally 100/0, Solo 80/20, Weapon + Armor Best Use, the reverted visual design, and button-fit corrections remain intact. Runtime stays `1.7.1-resynthesis-a2h5`; local schema **16**, hosted sync **1**, Portal protocol **33**. No migration or player reset.

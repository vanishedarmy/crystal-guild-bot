# Crystal Guild v1.1.18 — Passive Recovery Hotfix

Adds automatic Long Rest recovery and a once-per-stream roster refresh.

## Long Rest
- An intentional Twitch command or Portal gameplay mutation records player activity.
- If eight hours pass without another intentional action, the background game daemon automatically restores full HP and current-Job MP/AP and clears ordinary Camp state, normally within one minute of the threshold.
- Passive Portal state polling does not reset the inactivity timer.
- Existing players begin a fresh Long Rest window on their first intentional action after upgrading.

## Stream Start Refresh
- Every registered hero is fully refreshed when Twitch reports a new LIVE stream session.
- Twitch `started_at` is persisted as the stream-session idempotency key, preventing repeated refreshes during reconnects or status polling.

## Compatibility
- Runtime: `1.1.18-recovery-h1`
- DB schema: 5 unchanged
- Hosted sync schema: 1 unchanged
- Portal Action protocol: 14 unchanged
- Twitch prefix: `!` unchanged

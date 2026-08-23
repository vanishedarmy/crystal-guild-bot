# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 1 Validation

## Scope

Bot-only stream-presence gating for Twitch live-show gameplay.

## Automated validation performed

- Stream-status LIVE detection and cache behavior: PASS
- OFFLINE detection from empty Twitch stream result: PASS
- Stale/failed Twitch probe fails closed to UNKNOWN: PASS
- Twitch adapter source coverage for Rally Venture, Rally join, Active Hunt, battle actions, and raid actions: PASS
- Portal Solo Venture / Portal Challenge Hunt remain outside the Twitch gate: PASS
- Release contract and DB recovery/stress guardrails: PASS
- Python source compile/AST validation: PASS

The full TwitchIO-dependent Bot regression suite could not be executed in this sandbox because TwitchIO is not installed in the system Python environment. The new functionality has no new third-party dependency; production continues to use the existing `twitchio==3.2.2` requirement.

## Compatibility

- Runtime: `1.1.14-cloud-continuity-h1`
- Hosted sync version: `1.1.14-cloud-continuity` unchanged
- DB schema: 4 unchanged
- Hosted sync schema: 1 unchanged
- Portal Action protocol: 12 unchanged
- Twitch prefix: `!` unchanged
- Player reset: none
- Database migration: none
- Web redeploy: none

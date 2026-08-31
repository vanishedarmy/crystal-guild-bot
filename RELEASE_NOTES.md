# Crystal Guild v1.5.0 — Trails & Raids RC1

## Release-Candidate Hardening & Feature Freeze

RC1 freezes the seven flagship Trials and the Beta 1–3 progression/reliability model for release-candidate validation. It does not add a boss, currency, reward rebalance, database table, Portal combat mutation, or new player command.

### Exact readiness ownership
- The live **Round Readiness** count and the internal all-actions-ready decision now use the same ownership rule as round resolution: an action must belong to the exact active Raid run and the upcoming round.
- A stale action stamp from an earlier round or different Raid no longer makes the Board falsely report that player as ready.
- This closes the final presentation/decision gap left after Beta 3 introduced exact run/round action stamps.

### Corrupt/stale checkpoint resilience
- A malformed restored `raid_round` stamp now fails closed instead of raising during round resolution.
- Invalid or stale stamped actions safely fall back to the normal automatic Attack for that round.
- The one unstamped queued action restored from a pre-Beta-3 checkpoint is still honored once for upgrade compatibility.

### Release-candidate cleanup
- Current Bot/Web/frontend identity advances to `1.5.0-trails-raids-rc1`.
- Player-facing What's New and Player Guide receive an RC1 feature-freeze/readiness note.
- The Bot control-panel banner and current deployment/package metadata are refreshed to the RC1 identity and Beta 3 baseline.
- Historical Alpha/Beta changelog entries remain engineering history.

### Frozen systems carried forward
- Seven scripted Trials: Ifrit, Shiva, Ramuh, Titan, Garuda, Leviathan, Bahamut.
- Trial Chronicle and repeat-clear mastery.
- Beta 2 exact-run bounded settlement receipts.
- Beta 3 authoritative combat revisions, cross-connection action merge, and exact timer-tick stale-state protection.
- Roomy collapsible Trial & Raid Board, Last Trial Result, contribution details, and Round Readiness.
- All four v1.4 production Dungeons and their existing stale-state/replay protections.

### Compatibility
- Bot/Web/frontend runtime: `1.5.0-trails-raids-rc1`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth/environment changes: **none**
- New environment variables: **none**

Deploy matching RC1 Web + Bot together.

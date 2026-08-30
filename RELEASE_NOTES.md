# Crystal Guild v1.4.0 — Dungeons & Delves RC1

## Release Candidate 1

RC1 is a release-cleanup and deployment-readiness build on the feature-frozen Beta 3 Dungeon system. It introduces no new Dungeon, reward layer, currency, combat tuning, or progression change.

### Release hardening carried forward
- Four Dungeons remain authoritative and unchanged.
- Every Dungeon mutation remains bound to exact run ID + chamber ID + persisted revision.
- Authoritative state reads remain serialized behind SQLite write intent, preventing separate connections from spending one rendered state twice.
- Duplicate delivery of the same action ID remains idempotent and returns the committed receipt.
- Dungeon runs, route effects, Cache state, records, and revisions remain restart/reconnect safe.

### RC1 cleanup
- Runtime/Web/frontend identities advance to `1.4.0-dungeons-rc1` for release-candidate cache/version clarity.
- Python project metadata now reports v1.4.0 rather than the stale v1.1.19 package version.
- The generated `overlay/state.json` runtime artifact is no longer shipped and is explicitly ignored.
- Cloud/full setup documentation is refreshed to the current schema/protocol/runtime baseline.
- Release packages are reconstructed from Beta 3 using the actual patch helpers and checked for private/runtime artifacts.

### Compatibility
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth/environment changes: **none**
- Gameplay/economy/balance changes: **none**

Deploy RC1 Web and Bot together so runtime and frontend identities remain aligned.

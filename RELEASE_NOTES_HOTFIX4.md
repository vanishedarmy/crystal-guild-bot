# Crystal Guild v1.1.19 Retro Phase III RC1 Hotfix 4 — Dynamic Camp

Camp is now stream-aware in the authoritative Bot runtime.

- Twitch LIVE: 15-minute base Camp timer.
- Twitch OFFLINE: 1-hour base Camp timer.
- Unknown/unconfirmed Twitch state uses the OFFLINE timer.
- Existing Fellowship/Infirmary Camp-time reductions still apply.
- Twitch `!rest` / `!camp` resolves current stream presence before starting a new Camp.
- Portal `START_REST` and Adventure Board Camp state use the same authoritative Twitch presence probe.
- Existing camps keep their already-recorded absolute completion timestamp; only newly started camps use the new rule.

Compatibility:
- Bot runtime: `1.1.19-retro-phase-iii-rc1h4`.
- Portal Action protocol: 15 unchanged.
- Hosted sync compatibility: unchanged.
- Database schema: unchanged.
- No player reset, migration, OAuth reauthorization, or new required environment variable.

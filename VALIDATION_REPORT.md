# Passive Recovery Hotfix — Bot Validation

- Long Rest threshold: exactly 8 hours.
- Long Rest restores HP plus current-Job MP/AP and clears ordinary Camp state.
- Twitch commands count as activity before gameplay validation.
- Portal gameplay mutations count as activity; passive Portal state polling does not.
- New LIVE Twitch sessions refresh all players exactly once per `started_at` value.
- DB schema remains 5; Portal Action protocol remains 14.
- Automated Bot suite: **384/384 PASS**

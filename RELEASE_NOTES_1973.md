# Crystal Guild v1.9.97.3 — Lurk Mode

Adds opt-in, persistence-backed participation in stream Ventures, World Events and Raids.

- `!lurkmode on`, `!lurkmode off`, and `!lurkmode status`. The `!lurk` command is reserved for the separate stream command and is not registered by Crystal Guild.
- The Stream Activities tab provides Enable/Disable Lurk Mode buttons and current status, via authenticated `SET_LURK_MODE` action (protocol version stays 39).
- Lurk players only auto-join an **open rally with at least one manual participant**. No automatic events start; empty World Events pass; solo Hunts, Dungeons, Ascension Trials, Expeditions and other solo activities are excluded. Normal restrictions (Job, alive, level, activity, cooldown, rally end) apply through the existing join methods.
- If a player explicitly queues a command for the round, that action always wins. Turning off automation stops new joins and future automated turns without ejecting players already in battle.
- When a turn has no manual input, the planner favors basic Attack, reserves at least 35% MP/AP after skills, prefers emergency support heals when critical, and Defends when near KO. High-cost buffs, empty-resource casts and routine expensive abilities are avoided.
- Non-rare restorative items are limited to two per battle, at least two items kept in inventory, only when healing is meaningful, and never bought automatically. The planner never spends Elixir, Megalixir or Phoenix Down.
- Automatic `!healparty` is allowed once total per group battle, up to tier 3, only with at least three living characters and multiple seriously wounded allies, and only if the contributing hero has twenty times the chosen tier's Gil price. Manually used Mist follows existing per-player rules.
- All opt-in preferences are stored in existing SQLite `runtime_state`; no migration required. Battle state persists through existing checkpoints. No other player's character data is exposed.
- Previous Elite Hunts, World Event exclusivity, artwork, Guild Town, Ascension Trials and Raid display hotfix remain included.

## Installation

1. Stop Bot and Web and back up persistent databases, runtime state, `.env` and existing artwork.
2. Extract the combined ZIP into the parent folder that already contains `Bot/` and `Web/`, merging matching files. Alternatively, merge **both** Bot and Web ZIPs; do not install both methods.
3. Never delete your existing `Web/frontend/public` art collection: this is a merge package, not a replacement for unrelated historical files.
4. Deploy/restart Bot. In `Web/frontend`, run `npm ci --include=dev` if dependencies are absent and `npm run build` before publishing Web.
5. Test `!lurkmode on`, start a live Venture/Raid with a manual participant, verify Lurk players join and act conservatively; test `!lurkmode off`, empty World Event expiry, level gates and Portal toggle. Try it in staging before a live stream.

## Verification boundaries

- Automated Bot and frontend-focused tests verify opt-in persistence, autojoin guards, safe auto-actions, Mist cost gating, Portal action/state wiring and basic regression behavior.
- Production frontend compilation, real OAuth Portal actions, live Twitch join timing and multi-process deployment must be tested on your hosting environment.

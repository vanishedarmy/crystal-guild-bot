# Crystal Guild v1.9.97.4 — Relic Portal Awakening

The Portal Relic Arsenal now supports authenticated RELIC_AWAKEN actions on Classic and Ultimate Relic lines. The same authoritative Bot `awaken_relic` operation used by Twitch `!awaken` validates the selected Job, quest state, stage requirements and materials, and grants the stage reward.

Portal requests use a fresh per-action idempotency key. The Bot records the replay receipt in the same SQLite transaction as the stage advancement so lost acknowledgements cannot spend twice or skip stages. Existing player weapons, saves and quests remain unchanged.

The Relic cards and the detail dialog show `Awaken Stage` when a stage is ready. The user reviews the exact Gil, Hunt Seals and materials cost before confirming. The Portal awaits the action result and refreshes the player snapshot.

No database migration or new item art required. Deploy matching Bot and Web source, preserve runtime DB/configuration and public assets, then rebuild the frontend. Test a ready Classic Relic and an Ultimate Relic with a staging player.

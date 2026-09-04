# Upgrade to v1.7.1 Resynthesis Alpha 2 Hotfix 2

This is a **Bot-only Job Quest unlock repair**. Deploy the Hotfix 2 Bot over v1.7.1 Resynthesis Alpha 2 Hotfix 1. The existing Alpha 2 Web build remains compatible and does not need to change.

Preserve the live database, Twitch token database, persistent storage, and environment secrets. No database migration is required; schema remains **15** and Portal protocol remains **32**.

After restart, confirm `!cgversion` reports `1.7.1-resynthesis-a2h2`. Open the Jobs tab or use `!job` / `!quests` on a player who already satisfies a Job Quest. The quest should reconcile once and the associated Job should become available without repeating prior milestones.
